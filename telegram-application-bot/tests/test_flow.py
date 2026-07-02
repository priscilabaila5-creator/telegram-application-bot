import unittest

from app.flow import ApplicationFlow, Session


class FlowTest(unittest.TestCase):
    def test_full_request_flow(self):
        flow = ApplicationFlow()
        session = Session()

        session, action = flow.message(session, "Анна")
        self.assertEqual(session.step, "request_type")
        self.assertEqual(action.text, "Что нужно?")

        session, action = flow.callback(session, "type:Бот")
        self.assertEqual(session.step, "budget")
        self.assertEqual(action.text, "Какой бюджет?")

        session, action = flow.callback(session, "budget:50–150к")
        self.assertEqual(session.step, "deadline")

        session, action = flow.message(session, "2 недели")
        self.assertEqual(session.step, "contact")

        session, action = flow.message(session, "@anna")
        self.assertEqual(session.step, "confirm")
        self.assertIn("Имя: Анна", action.text)
        self.assertIn("Что нужно: Бот", action.text)
        self.assertIn("Бюджет: 50–150к", action.text)
        self.assertIn("Срок: 2 недели", action.text)
        self.assertIn("Контакт: @anna", action.text)

        session, action = flow.callback(session, "send")
        self.assertEqual(action.text, "Заявка принята")
        self.assertIn("Имя: Анна", action.send_to_target)
        self.assertTrue(action.reset_session)

    def test_text_instead_of_buttons_is_reasked(self):
        flow = ApplicationFlow()
        session = Session(step="request_type", answers={"name": "Иван"})
        session, action = flow.message(session, "хочу сайт")
        self.assertEqual(session.step, "request_type")
        self.assertIn("Выберите вариант кнопкой", action.text)

        session = Session(step="budget", answers={"name": "Иван", "request_type": "Сайт"})
        session, action = flow.message(session, "дешево")
        self.assertEqual(session.step, "budget")
        self.assertIn("Выберите бюджет кнопкой", action.text)

    def test_restart_starts_from_beginning(self):
        flow = ApplicationFlow()
        session = Session(step="confirm", answers={"name": "Олег"})
        session, action = flow.callback(session, "restart")
        self.assertEqual(session.step, "name")
        self.assertEqual(session.answers, {})
        self.assertEqual(action.text, "Как вас зовут?")

    def test_stale_send_button_does_not_submit_empty_card(self):
        flow = ApplicationFlow()
        session, action = flow.callback(Session(), "send")
        self.assertEqual(session.step, "name")
        self.assertIsNone(action.send_to_target)
        self.assertEqual(action.text, "Сначала заполните заявку.")


if __name__ == "__main__":
    unittest.main()
