


users = {
"ai_security_expert": {
    "role": "ai_security",
    "clearance": 4,
    "department": "AI Security",
    "active": True},

"ml_engineer": {
    "role": "ml_engineer",
    "clearance": 3,
    "department": "Machine Learning",
    "active": True},

"data_engineer": {
    "role": "data_engineer",
    "clearance": 2,
    "department":"Data Engineering",
    "active": True},

"research_assistant": {
    "role": "researcher",
    "clearance": 2,
    "department": "Research",
    "active": True},

"training_bot": {
    "role": "bot_account",
    "clearance": 1,
    "department": "Automation",
    "active": False}
}
resources = [("ai_models", 4), ("training_datasets", 3), ("data_pipelines", 2),
("research_notebooks", 2), ("model_artifacts", 4), ("synthetic_data", 1),
("adversarial_tests", 3), ("model_registry", 4), ("feature_stores", 2),
("public_models", 1)]
security_levels = ("Open Source", "Internal Research", "Proprietary", "TradeSecret")
blocked_users = {"training_bot", "model_theft", "data_poisoning_acc"}

def task2():
    print("ресурси системи:")
    for res_name, res_level in resources:
        print(f"- {res_name}: {security_levels[res_level - 1]}")
    
    print("\nрезультати перевірки доступу:")
    user_test = list(users.keys())
    
    for username in user_test:
        for res_name, res_level in resources:
            user_data = users.get(username)
            
            if not user_data:
                result = "DENY (User not found)"
            elif username in blocked_users:
                result = "DENY (User is blocked)"
            elif not user_data.get("active"):
                result = "DENY (Account inactive)"
            elif user_data.get("clearance") >= res_level:
                result = "ALLOW"
            else:
                result = "DENY (Insufficient clearance)"
            
            print(f"user=[{username}] resource=[{res_name}] -> {result}")

if __name__ == "__main__":
    task2()