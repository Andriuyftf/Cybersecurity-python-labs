import random
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__),'../../')))
from shared.student import STUDENT_NAME, GROUP_NAME, VARIANT_NUMBER

passwords = ["Compli4nc3@Check", "weak", "Risk@Ass3ssment", "guest",
"Vulner4bility@Scan", "temp", "P3netration@Test", "demo", "S3curity@Audit",
"trial"]

criteria = {
"min_length": 8,
"require_digits": True,
"require_upper": True,
"require_special": True}

forbidden_passwords = {"weak", "guest", "temp", "demo", "trial", "password"}

def analyze_pas():

    randomdupl = random.choices(passwords, k=3)
    passwords.extend(randomdupl)
    
    print(f"{'Пароль':<25} | {'Статус'}")
    print("-" * 50)

    for pas in passwords:
        forbiden = pas in forbidden_passwords or len(pas) < criteria["min_length"]

        has_digit = any(c.isdigit() for c in pas)
        has_upper = any(c.isupper() for c in pas)
        has_lower = any(c.islower() for c in pas)
        has_spec = any(not c.isalnum() for c in pas)

        meets_all = has_digit and has_spec and has_upper and has_lower
        meets_some = (has_digit or has_upper or has_lower or has_spec) and not meets_all
        is_unique = passwords.count(pas) == 1

        if forbiden:
            status = "Заборонений"
        elif meets_all and len(pas) >= criteria["min_length"] + 4 and is_unique:
            status = "Дуже сильний"
        elif meets_all and len(pas) < criteria["min_length"] + 4:
            status = "Сильний"
        elif meets_some:
            status = "Середній"
        else:
            status = "Слабкий"

        print(f"{pas:<25} | {status}")

if __name__ == "__main__":
    analyze_pas()