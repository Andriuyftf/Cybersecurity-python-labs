import hashlib
import hmac
import os
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

SALT_BYTES = 16
ITTERATIONS = 600_000
SESSION_TIMEOUT_SEC = 900

EMAIL_PATTERN = (
    r"[A-Za-z][A-Za-z0-9_]{2,63}@"
    r"[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?"
    r"(?:\.[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?)+"
)


class User:
    def __init__(
        self,
        username: str,
        email: str,
        role: str,
        active: bool = True,
    ) -> None:
        self.username = username
        self.email = email
        self.role = role
        self.active = active
        self.__password_hash: bytes = b""
        self.__password_salt: bytes = b""

    def set_password(self, password: str) -> None:
        salt = os.urandom(SALT_BYTES)
        password_hash = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt,
            ITTERATIONS,
        )
        self.__password_hash = password_hash
        self.__password_salt = salt

    def check_password(self, password: str) -> bool:
        if not self.__password_hash:
            return False

        candidate_hash = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            self.__password_salt,
            ITTERATIONS,
        )
        return hmac.compare_digest(self.__password_hash, candidate_hash)

    def deactivate(self) -> None:
        self.active = False

    def __str__(self) -> str:
        return (
            f"User(username={self.username}, email={self.email}, "
            f"role={self.role}, active={self.active})"
        )

    @property
    def email(self) -> str:
        return self._email

    @email.setter
    def email(self, value: str) -> None:
        if not isinstance(value, str) or re.fullmatch(EMAIL_PATTERN, value) is None:
            raise ValueError("Некоректний формат email")

        self._email = value


class Admin(User):
    def __init__(
        self,
        username: str,
        email: str,
        active: bool = True,
        permissions: set[str] | None = None,
    ) -> None:
        super().__init__(
            username=username,
            email=email,
            role="admin",
            active=active,
        )

        if permissions is None:
            self.permissions: set[str] = set()
        else:
            self.permissions = set(permissions)

    def grant_permission(self, permission: str) -> None:
        self.permissions.add(permission)

    def revoke_permission(self, permission: str) -> None:
        self.permissions.discard(permission)

    def has_permission(self, permission: str) -> bool:
        return permission in self.permissions

    def __str__(self) -> str:
        return (
            f"Admin(username={self.username}, email={self.email}, "
            f"role={self.role}, active={self.active}, "
            f"permissions={sorted(self.permissions)})"
        )


class Session:
    def __init__(self, ip: str) -> None:
        self.ip = ip
        now = datetime.now(timezone.utc)
        self.login_time: datetime = now
        self.last_activity: datetime = now

    def touch(self) -> None:
        self.last_activity = datetime.now(timezone.utc)

    def is_active(self, timeout_sec: int) -> bool:
        if timeout_sec <= 0:
            raise ValueError("timeout_sec має бути більшим за 0")

        now = datetime.now(timezone.utc)
        inactivity = now - self.last_activity
        return inactivity < timedelta(seconds=timeout_sec)


@dataclass
class AuditRecord:
    time: datetime
    username: str
    action: str


class AuditLog:
    def __init__(self) -> None:
        self.records: list[AuditRecord] = []

    def add_log(self, username: str, action: str) -> None:
        record = AuditRecord(
            time=datetime.now(timezone.utc),
            username=username,
            action=action,
        )
        self.records.append(record)

    def show_all(self) -> None:
        for record in self.records:
            print(f"{record.time.isoformat()} | {record.username} | {record.action}")


class UserAccount:
    def __init__(
        self,
        user: User,
        session: Session | None = None,
        audit_log: AuditLog | None = None,
    ) -> None:
        self["user"] = user
        self["session"] = session
        self["audit_log"] = AuditLog() if audit_log is None else audit_log

    def login(self, username: str, password: str, ip: str) -> bool:
        if (
            username != self.user.username
            or not self.user.active
            or not self.user.check_password(password)
        ):
            self.audit_log.add_log(username, "login_failure")
            return False

        self.session = Session(ip)
        self.session.touch()
        self.audit_log.add_log(username, "login_success")
        return True

    def is_authenticated(self) -> bool:
        if self.session is None:
            return False

        if not self.user.active or not self.session.is_active(SESSION_TIMEOUT_SEC):
            self.session = None
            return False

        return True

    def logout(self) -> None:
        self.session = None
        self.audit_log.add_log(self.user.username, "logout")

    def __getitem__(self, key: str) -> User | Session | AuditLog | None:
        if key not in ("user", "session", "audit_log"):
            raise KeyError(key)
        return getattr(self, key)

    def __setitem__(self, key: str, value: object) -> None:
        if key not in ("user", "session", "audit_log"):
            raise KeyError(key)

        allowed_types = {
            "user": User,
            "session": (Session, type(None)),
            "audit_log": AuditLog,
        }

        if not isinstance(value, allowed_types[key]):
            raise TypeError(f"Неправильний тип значення для '{key}'")

        setattr(self, key, value)

        if key == "user":
            self.session = None
