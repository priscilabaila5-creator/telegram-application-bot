import json
import time
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen


class TelegramAPI:
    def __init__(self, token: str):
        self.base_url = f"https://api.telegram.org/bot{token}"

    def get_updates(self, offset: int | None = None, timeout: int = 25) -> list[dict[str, Any]]:
        params: dict[str, Any] = {"timeout": timeout, "allowed_updates": json.dumps(["message", "callback_query"])}
        if offset is not None:
            params["offset"] = offset
        data = self._request("getUpdates", params)
        return data.get("result", [])

    def send_message(self, chat_id: int, text: str, keyboard: list[list[dict[str, str]]] | None = None) -> None:
        payload: dict[str, Any] = {"chat_id": chat_id, "text": text}
        if keyboard:
            payload["reply_markup"] = json.dumps({"inline_keyboard": keyboard})
        self._request("sendMessage", payload)

    def answer_callback_query(self, callback_query_id: str) -> None:
        self._request("answerCallbackQuery", {"callback_query_id": callback_query_id})

    def _request(self, method: str, payload: dict[str, Any]) -> dict[str, Any]:
        body = urlencode(payload).encode("utf-8")
        request = Request(f"{self.base_url}/{method}", data=body, method="POST")
        last_error: Exception | None = None
        for _ in range(3):
            try:
                with urlopen(request, timeout=35) as response:
                    data = json.loads(response.read().decode("utf-8"))
                if not data.get("ok"):
                    raise RuntimeError(f"Telegram API error: {data}")
                return data
            except Exception as exc:
                last_error = exc
                time.sleep(1)
        raise RuntimeError(f"Telegram request failed: {last_error}")
