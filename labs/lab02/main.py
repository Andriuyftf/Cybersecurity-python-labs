import argparse
from datetime import timedelta
from secrets import token_urlsafe

from .task1 import (
    SESSION_TIMEOUT_SEC,
    Admin,
    AuditLog,
    User,
    UserAccount,
)


def demo() -> None:
    user = User(
        "andrii",
        "andrii_13@example.com",
        "student",
    )

    password = token_urlsafe(24)
    user.set_password(password)

    audit = AuditLog()
    account = UserAccount(user=user, audit_log=audit)

    # Невдалий вхід.
    print(
        "Невдалий вхід:",
        account.login(
            user.username,
            password + "!",
            "192.168.1.10",
        ),
    )
    print(
        "Сесія після невдалого входу:",
        account["session"],
    )

    # Успішний вхід.
    print(
        "Успішний вхід:",
        account.login(
            user.username,
            password,
            "192.168.1.10",
        ),
    )
    print("Автентифіковано:", account.is_authenticated())

    # Зміна email із валідацією.
    user.email = "andrii_new@example.org"
    print("Новий email:", user.email)

    try:
        user.email = "incorrect-email"
    except ValueError as error:
        print("Помилка email:", error)

    # Права адміністратора.
    admin = Admin(
        "administrator",
        "administrator@example.com",
        permissions={"read_logs"},
    )

    admin.grant_permission("manage_users")
    print(
        "Право manage_users:",
        admin.has_permission("manage_users"),
    )

    admin.revoke_permission("read_logs")
    print(
        "Право read_logs:",
        admin.has_permission("read_logs"),
    )
    print(admin)

    # Доступ через спеціальні методи.
    print("Користувач через ключ:", account["user"])
    account["audit_log"] = audit

    try:
        account["session"] = "not a session"
    except TypeError as error:
        print("Помилка типу:", error)

    try:
        print(account["password_hash"])
    except KeyError as error:
        print("Невідомий ключ:", error)

    # Імітація таймауту без очікування 15 хвилин.
    if account.session is not None:
        account.session.last_activity -= timedelta(
            seconds=SESSION_TIMEOUT_SEC + 1,
        )

    print("Після таймауту:", account.is_authenticated())
    print("Сесія після таймауту:", account["session"])

    # Повторний вхід і явний вихід із системи.
    print(
        "Повторний вхід:",
        account.login(
            user.username,
            password,
            "192.168.1.10",
        ),
    )
    del password

    account.logout()
    print("Після logout:", account.is_authenticated())

    print("Журнал аудиту:")
    audit.show_all()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Лабораторна робота №2",
    )

    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
    )
    subparsers.add_parser(
        "demo",
        help="Демонстрація класів",
    )

    args = parser.parse_args()

    if args.command == "demo":
        demo()


if __name__ == "__main__":
    main()