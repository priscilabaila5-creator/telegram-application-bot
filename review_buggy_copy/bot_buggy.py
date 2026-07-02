class BuggyBot:
    def __init__(self, target_chat_id, admin_ids):
        self.target_chat_id = target_chat_id
        self.admin_ids = set(admin_ids)
        self.allowed_users = set(admin_ids)
        self.session = {"step": "name", "answers": {}}

    def add_user(self, current_user_id, new_user_id):
        if current_user_id not in self.allowed_users:
            return "доступ ограничен"
        self.allowed_users.add(new_user_id)
        return f"Пользователь {new_user_id} добавлен."

    def handle_budget_text(self, text):
        self.session["answers"]["budget"] = text
        self.session["step"] = "deadline"
        return "В какие сроки нужно сделать?"

    def send_request(self):
        return "Заявка принята"
