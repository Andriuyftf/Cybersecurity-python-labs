import argparse
from datetime import timedelta

from . import task2
from .task1 import SESSION_TIMEOUT_SEC, Admin, AuditLog, User, UserAccount


def demo():
    user = User("andrii", "andrii@example.test", "user")
    user.set_password("Lab13Password!")
    audit = AuditLog()
    account = UserAccount(user, audit_log=audit)

    print("Користувач")
    print(account["user"])

    print("\nПеревірка входу")
    failed_login = account.login("andrii", "wrong", "192.0.2.10")
    print("Невдалий вхід:", failed_login)
    successful_login = account.login("andrii", "Lab13Password!", "192.0.2.10")
    print("Успішний вхід:", successful_login)
    authenticated = account.is_authenticated()
    print("Користувач авторизований:", authenticated)

    print("\nЗміна email")
    user.email = "andrii_new@example.test"
    print("Новий email:", user.email)
    try:
        user.email = "incorrect-email"
    except ValueError as error:
        print("Помилка:", error)
    print("Email після невдалої зміни:", user.email)

    print("\nПрава адміністратора")
    admin = Admin("admin", "admin@example.test")
    admin.grant_permission("read_logs")
    admin.grant_permission("manage_users")
    print(admin)
    print("Право read_logs:", admin.has_permission("read_logs"))
    admin.revoke_permission("read_logs")
    print("Право read_logs після відкликання:", admin.has_permission("read_logs"))
    print(admin)

    print("\nЗавершення сеансу за таймаутом")
    account["session"].last_activity -= timedelta(seconds=SESSION_TIMEOUT_SEC + 1)
    authenticated = account.is_authenticated()
    print("Авторизація після таймауту:", authenticated)

    print("\nВихід із системи")
    successful_login = account.login("andrii", "Lab13Password!", "192.0.2.10")
    print("Повторний вхід:", successful_login)
    account.logout()
    authenticated = account.is_authenticated()
    print("Авторизація після виходу:", authenticated)

    print("\nЖурнал аудиту")
    audit.show_all()


def main():
    parser = argparse.ArgumentParser(description="Лабораторна робота 2")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("demo")
    commands.add_parser("analyze", add_help=False)
    args, remaining = parser.parse_known_args()

    if args.command == "demo":
        if remaining:
            parser.error("Команда demo не приймає додаткових аргументів")
        demo()
        return 0

    if args.command == "analyze":
        return task2.main(remaining)


if __name__ == "__main__":
    raise SystemExit(main())
