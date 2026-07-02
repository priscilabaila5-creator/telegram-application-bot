import tempfile
import unittest
from pathlib import Path

from app.bot import ApplicationBot
from app.storage import JsonStore


class FakeApi:
    def __init__(self):
        self.messages = []
        self.callback_ids = []

    def send_message(self, chat_id, text, keyboard=None):
        self.messages.append({"chat_id": chat_id, "text": text, "keyboard": keyboard})

    def answer_callback_query(self, callback_query_id):
        self.callback_ids.append(callback_query_id)


def message(user_id, text, chat_id=None):
    return {"message": {"from": {"id": user_id}, "chat": {"id": chat_id or user_id}, "text": text}}


def callback(user_id, data, callback_id="cb", chat_id=None):
    return {
        "callback_query": {
            "id": callback_id,
            "from": {"id": user_id},
            "data": data,
            "message": {"chat": {"id": chat_id or user_id}},
        }
    }


class BotTest(unittest.TestCase):
    def make_bot(self, admin_ids={1}):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        api = FakeApi()
        bot = ApplicationBot(api, JsonStore(Path(tmp.name)), set(admin_ids), -100)
        return bot, api

    def test_unknown_user_is_blocked(self):
        bot, api = self.make_bot()
        bot.handle_update(message(99, "/start"))
        self.assertEqual(api.messages[-1]["text"], "доступ ограничен")

    def test_admin_adds_user_and_users_persist(self):
        bot, api = self.make_bot()
        bot.handle_update(message(1, "/adduser 2"))
        self.assertIn("2", api.messages[-1]["text"])
        bot.handle_update(message(1, "/users"))
        self.assertIn("1, 2", api.messages[-1]["text"])
        bot.handle_update(message(2, "/start"))
        self.assertNotEqual(api.messages[-1]["text"], "доступ ограничен")

    def test_admin_ids_are_merged_into_existing_users_file(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        store = JsonStore(Path(tmp.name))
        store.save_users({2})
        api = FakeApi()
        bot = ApplicationBot(api, store, {1}, -100)
        self.assertEqual(bot.allowed_users, {1, 2})

    def test_two_users_sessions_do_not_mix(self):
        bot, api = self.make_bot(admin_ids={1, 2})
        bot.handle_update(callback(1, "start_request"))
        bot.handle_update(callback(2, "start_request"))
        bot.handle_update(message(1, "Анна"))
        bot.handle_update(message(2, "Борис"))
        bot.handle_update(callback(1, "type:Сайт"))
        bot.handle_update(callback(2, "type:Бот"))
        self.assertEqual(bot.sessions["1"]["answers"]["request_type"], "Сайт")
        self.assertEqual(bot.sessions["2"]["answers"]["request_type"], "Бот")

    def test_completed_request_goes_to_target_chat(self):
        bot, api = self.make_bot()
        bot.handle_update(callback(1, "start_request"))
        bot.handle_update(message(1, "Анна"))
        bot.handle_update(callback(1, "type:Бот"))
        bot.handle_update(callback(1, "budget:до 50к"))
        bot.handle_update(message(1, "неделя"))
        bot.handle_update(message(1, "@anna"))
        bot.handle_update(callback(1, "send"))
        target_messages = [item for item in api.messages if item["chat_id"] == -100]
        self.assertEqual(len(target_messages), 1)
        self.assertIn("Контакт: @anna", target_messages[0]["text"])
        self.assertEqual(api.messages[-1]["text"], "Заявка принята")

    def test_text_without_start_button_does_not_start_request(self):
        bot, api = self.make_bot()
        bot.handle_update(message(1, "Анна"))
        self.assertEqual(api.messages[-1]["text"], "Привет! Я помогу оставить заявку.")
        self.assertNotIn("1", bot.sessions)

    def test_added_user_survives_bot_restart(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        store = JsonStore(Path(tmp.name))
        api = FakeApi()
        bot = ApplicationBot(api, store, {1}, -100)
        bot.handle_update(message(1, "/adduser 2"))

        restarted_bot = ApplicationBot(FakeApi(), store, {1}, -100)
        self.assertIn(2, restarted_bot.allowed_users)


if __name__ == "__main__":
    unittest.main()
