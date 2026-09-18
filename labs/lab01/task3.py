import csv
import hashlib
import json
import os
import sys
from datetime import datetime


class ValidationError(Exception):
    pass

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from shared.student import VARIANT_NUMBER

PERSONAL_SALT = f"{VARIANT_NUMBER:05d}"
MIN_LEN_PASSWORD = 14

def generate_hash(password: str, salt: str = "00000") -> str:
    if not password or not salt:
        raise ValueError("Введіть пароль і сіль")
    if len(password) < MIN_LEN_PASSWORD:
        raise ValidationError("Пароль закороткий")
    
    data = (password + salt).encode('utf-8')
    return hashlib.sha3_256(data).hexdigest()


users_to_register = (
    ("admin1", "qwerty123_Secure!"),
    ("user1", "jqklfq_TooShort"), 
    ("user2", "oaksjdalskjf123!3"),
    ("admin2", "askjdlkjf02193_!"),
    ("user3", "kjdhkasfkqqwf345"),
    ("user4", "guest_password_123!"),
    ("moderator", "mod_secure_pass!@#"),
    ("user5", "test_acc_pass2026"),
    ("user6", "dev_ops_secret!1"),
    ("analyst", "data_analyst_2026!")
)

def create_user(username, password):
    generated_hash = generate_hash(password, salt=PERSONAL_SALT)
    return (username, generated_hash)

def create_users(users_list):
    os.makedirs("labs/lab01/data/", exist_ok=True)
    path = "labs/lab01/data/users.csv"
    try:
        with open(path, mode="w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(["username", "password_hash"])
            for username, password in users_list:
                try:
                    data = create_user(username, password)
                    writer.writerow(data)
                except (ValueError, ValidationError) as e:
                    print(f"Помилка створення {username}: {e}")
    except (PermissionError, IOError) as e:
        print(f"Помилка доступу до файлу: {e}")

def read_db():
    users_db = []
    path = "labs/lab01/data/users.csv"
    try:
        with open(path, mode="r", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            for row in reader:
                users_db.append(row)
        
        print("\nВміст бази даних:")
        for user in users_db:
            print(f"Користувач: {user['username']}, Хеш: {user['password_hash'][:15]}...")
    except FileNotFoundError:
        print("База даних не знайдена.")
    except (PermissionError, IOError) as e:
        print(f"Помилка читання файлу бази даних: {e}")
    return users_db


def log_event(func):
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        username = args[0] if args else kwargs.get("username", "unknown")
        
        log_entry = {
            "event": "login",
            "user": username,
            "result": "success" if result else "failure",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "args": args,
            "kwargs": kwargs
        }
        
        os.makedirs("labs/lab01/data", exist_ok=True)
        try:
            with open("labs/lab01/data/log.json", mode="a", encoding="utf-8") as file:
                file.write(json.dumps(log_entry) + "\n")
        except (PermissionError, IOError) as e:
            print(f"Помилка запису логу: {e}")
            
        return result
    return wrapper

@log_event
def login(username: str, password: str) -> bool:
    if not username or not password:
        raise ValueError("Логін або пароль порожні")
    
    try:
        expected_hash = generate_hash(password, salt=PERSONAL_SALT)
        users_db = read_db()
        for user in users_db:
            if user["username"] == username and user["password_hash"] == expected_hash:
                return True
    except (ValueError, ValidationError):
        return False
    except Exception as e:
        print(f"Системна помилка під час авторизації: {e}")
        return False
    return False

def task3():
    create_users(users_to_register)

    print("\nВхід user2 (правильний пароль):", login("user2", "oaksjdalskjf123!3"))
    print("\nВхід user2 (неправильний пароль):", login("user2", "wrong_password"))

if __name__ == "__main__":
    task3()