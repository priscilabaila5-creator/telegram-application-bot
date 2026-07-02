from dataclasses import dataclass
import os
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    bot_token: str
    target_chat_id: int
    admin_ids: set[int]
    data_dir: Path


def load_dotenv(path: Path = Path(".env")) -> None:
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def parse_ids(value: str) -> set[int]:
    result: set[int] = set()
    for part in value.split(","):
        part = part.strip()
        if part:
            result.add(int(part))
    return result


def load_settings() -> Settings:
    load_dotenv()
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    target = os.environ.get("TARGET_CHAT_ID", "").strip()
    admins = os.environ.get("ADMIN_IDS", "").strip()
    data_dir = Path(os.environ.get("DATA_DIR", "./data"))

    missing = []
    if not token:
        missing.append("TELEGRAM_BOT_TOKEN")
    if not target:
        missing.append("TARGET_CHAT_ID")
    if not admins:
        missing.append("ADMIN_IDS")
    if missing:
        raise RuntimeError("Missing required settings: " + ", ".join(missing))

    return Settings(
        bot_token=token,
        target_chat_id=int(target),
        admin_ids=parse_ids(admins),
        data_dir=data_dir,
    )
