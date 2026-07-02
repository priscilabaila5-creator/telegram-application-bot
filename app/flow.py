from dataclasses import dataclass, field
from typing import Any


REQUEST_TYPES = ["Сайт", "Бот", "Другое"]
BUDGETS = ["до 50к", "50–150к", "150к+"]
REQUIRED_FIELDS = ["name", "request_type", "budget", "deadline", "contact"]


@dataclass
class BotAction:
    text: str
    keyboard: list[list[dict[str, str]]] | None = None
    send_to_target: str | None = None
    reset_session: bool = False


@dataclass
class Session:
    step: str = "name"
    answers: dict[str, str] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> "Session":
        if not data:
            return cls()
        return cls(step=str(data.get("step", "name")), answers=dict(data.get("answers", {})))

    def to_dict(self) -> dict[str, Any]:
        return {"step": self.step, "answers": self.answers}


def button(text: str, data: str) -> dict[str, str]:
    return {"text": text, "callback_data": data}


def start_action() -> BotAction:
    return BotAction(
        text="Привет! Я помогу оставить заявку.",
        keyboard=[[button("Оставить заявку", "start_request")]],
        reset_session=True,
    )


def first_question() -> BotAction:
    return BotAction(text="Как вас зовут?")


def format_card(answers: dict[str, str]) -> str:
    return (
        "Заявка\n"
        f"Имя: {answers.get('name', '-')}\n"
        f"Что нужно: {answers.get('request_type', '-')}\n"
        f"Бюджет: {answers.get('budget', '-')}\n"
        f"Срок: {answers.get('deadline', '-')}\n"
        f"Контакт: {answers.get('contact', '-')}"
    )


def is_complete(answers: dict[str, str]) -> bool:
    return all(answers.get(field, "").strip() for field in REQUIRED_FIELDS)


class ApplicationFlow:
    def start(self) -> tuple[Session, BotAction]:
        return Session(), start_action()

    def callback(self, session: Session, data: str) -> tuple[Session, BotAction]:
        if data == "start_request":
            return Session(), first_question()
        if data == "restart":
            return Session(), first_question()
        if data == "send":
            if session.step != "confirm" or not is_complete(session.answers):
                return session, BotAction(
                    text="Сначала заполните заявку.",
                    keyboard=[[button("Оставить заявку", "start_request")]],
                )
            card = format_card(session.answers)
            return Session(), BotAction(
                text="Заявка принята",
                send_to_target=card,
                reset_session=True,
            )
        if data.startswith("type:"):
            value = data.removeprefix("type:")
            if session.step != "request_type" or value not in REQUEST_TYPES:
                return session, self._ask_request_type()
            session.answers["request_type"] = value
            session.step = "budget"
            return session, self._ask_budget()
        if data.startswith("budget:"):
            value = data.removeprefix("budget:")
            if session.step != "budget" or value not in BUDGETS:
                return session, self._ask_budget()
            session.answers["budget"] = value
            session.step = "deadline"
            return session, BotAction(text="В какие сроки нужно сделать?")
        return session, BotAction(text="Не понял выбор, попробуйте еще раз.")

    def message(self, session: Session, text: str) -> tuple[Session, BotAction]:
        value = text.strip()
        if not value:
            return session, BotAction(text="Пришлите, пожалуйста, текстом.")

        if session.step == "name":
            session.answers["name"] = value
            session.step = "request_type"
            return session, self._ask_request_type()
        if session.step == "request_type":
            return session, self._ask_request_type("Выберите вариант кнопкой: Сайт, Бот или Другое.")
        if session.step == "budget":
            return session, self._ask_budget("Выберите бюджет кнопкой.")
        if session.step == "deadline":
            session.answers["deadline"] = value
            session.step = "contact"
            return session, BotAction(text="Оставьте контакт для связи.")
        if session.step == "contact":
            session.answers["contact"] = value
            session.step = "confirm"
            return session, BotAction(
                text=format_card(session.answers),
                keyboard=[[button("Отправить", "send")], [button("Заполнить заново", "restart")]],
            )
        if session.step == "confirm":
            return session, BotAction(
                text="Проверьте карточку и нажмите кнопку.",
                keyboard=[[button("Отправить", "send")], [button("Заполнить заново", "restart")]],
            )
        return Session(), first_question()

    def _ask_request_type(self, text: str = "Что нужно?") -> BotAction:
        return BotAction(
            text=text,
            keyboard=[[button(item, f"type:{item}") for item in REQUEST_TYPES]],
        )

    def _ask_budget(self, text: str = "Какой бюджет?") -> BotAction:
        return BotAction(
            text=text,
            keyboard=[
                [button("до 50к", "budget:до 50к")],
                [button("50–150к", "budget:50–150к")],
                [button("150к+", "budget:150к+")],
            ],
        )
