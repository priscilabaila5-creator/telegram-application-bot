from typing import Any
import time

from app.config import load_settings
from app.flow import ApplicationFlow, Session, start_action
from app.storage import JsonStore
from app.telegram_api import TelegramAPI


class ApplicationBot:
    def __init__(self, api: TelegramAPI, store: JsonStore, admin_ids: set[int], target_chat_id: int):
        self.api = api
        self.store = store
        self.admin_ids = set(admin_ids)
        self.allowed_users = store.load_users(admin_ids)
        self.sessions = store.load_sessions()
        self.target_chat_id = target_chat_id
        self.flow = ApplicationFlow()

    def handle_update(self, update: dict[str, Any]) -> None:
        if "message" in update:
            self._handle_message(update["message"])
        elif "callback_query" in update:
            self._handle_callback(update["callback_query"])

    def _handle_message(self, message: dict[str, Any]) -> None:
        user_id = int(message["from"]["id"])
        chat_id = int(message["chat"]["id"])
        text = str(message.get("text", ""))

        if not self._is_allowed(user_id):
            self.api.send_message(chat_id, "доступ ограничен")
            return

        if text.startswith("/start"):
            self.sessions.pop(str(user_id), None)
            self.store.save_sessions(self.sessions)
            self._reply(chat_id, start_action())
            return
        if text.startswith("/adduser"):
            self._add_user(user_id, chat_id, text)
            return
        if text.startswith("/users"):
            self._list_users(user_id, chat_id)
            return

        if str(user_id) not in self.sessions:
            self._reply(chat_id, start_action())
            return

        session = Session.from_dict(self.sessions.get(str(user_id)))
        session, action = self.flow.message(session, text)
        self._save_session(user_id, session, action.reset_session)
        self._reply(chat_id, action)

    def _handle_callback(self, callback: dict[str, Any]) -> None:
        self.api.answer_callback_query(callback["id"])
        user_id = int(callback["from"]["id"])
        message = callback["message"]
        chat_id = int(message["chat"]["id"])

        if not self._is_allowed(user_id):
            self.api.send_message(chat_id, "доступ ограничен")
            return

        session = Session.from_dict(self.sessions.get(str(user_id)))
        session, action = self.flow.callback(session, str(callback.get("data", "")))
        self._save_session(user_id, session, action.reset_session)
        self._reply(chat_id, action)

    def _add_user(self, user_id: int, chat_id: int, text: str) -> None:
        if user_id not in self.admin_ids:
            self.api.send_message(chat_id, "Команда доступна только админам.")
            return
        parts = text.split()
        if len(parts) != 2 or not parts[1].isdigit():
            self.api.send_message(chat_id, "Используйте: /adduser <id>")
            return
        new_user_id = int(parts[1])
        self.allowed_users.add(new_user_id)
        self.store.save_users(self.allowed_users)
        self.api.send_message(chat_id, f"Пользователь {new_user_id} добавлен.")

    def _list_users(self, user_id: int, chat_id: int) -> None:
        if user_id not in self.admin_ids:
            self.api.send_message(chat_id, "Команда доступна только админам.")
            return
        users = ", ".join(str(item) for item in sorted(self.allowed_users))
        self.api.send_message(chat_id, f"Белый список: {users}")

    def _is_allowed(self, user_id: int) -> bool:
        return user_id in self.allowed_users

    def _save_session(self, user_id: int, session: Session, reset: bool) -> None:
        key = str(user_id)
        if reset:
            self.sessions.pop(key, None)
        else:
            self.sessions[key] = session.to_dict()
        self.store.save_sessions(self.sessions)

    def _reply(self, chat_id: int, action) -> None:
        if action.send_to_target:
            self.api.send_message(self.target_chat_id, action.send_to_target)
        self.api.send_message(chat_id, action.text, action.keyboard)


def main() -> None:
    settings = load_settings()
    api = TelegramAPI(settings.bot_token)
    store = JsonStore(settings.data_dir)
    bot = ApplicationBot(api, store, settings.admin_ids, settings.target_chat_id)
    offset = None
    while True:
        try:
            for update in api.get_updates(offset=offset):
                offset = int(update["update_id"]) + 1
                bot.handle_update(update)
        except Exception as exc:
            print(f"Polling error: {exc}")
            time.sleep(3)


if __name__ == "__main__":
    main()
