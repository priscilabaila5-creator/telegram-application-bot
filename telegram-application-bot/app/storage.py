import json
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any


class JsonStore:
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.users_path = self.data_dir / "users.json"
        self.sessions_path = self.data_dir / "sessions.json"

    def load_users(self, initial_admins: set[int]) -> set[int]:
        if not self.users_path.exists():
            self.save_users(initial_admins)
            return set(initial_admins)
        data = self._read_json(self.users_path, [])
        users = {int(item) for item in data}
        merged_users = users | set(initial_admins)
        if merged_users != users:
            self.save_users(merged_users)
        users = merged_users
        if not users:
            users = set(initial_admins)
            self.save_users(users)
        return users

    def save_users(self, users: set[int]) -> None:
        self._write_json(self.users_path, sorted(users))

    def load_sessions(self) -> dict[str, dict[str, Any]]:
        if not self.sessions_path.exists():
            return {}
        data = self._read_json(self.sessions_path, {})
        return data if isinstance(data, dict) else {}

    def save_sessions(self, sessions: dict[str, dict[str, Any]]) -> None:
        self._write_json(self.sessions_path, sessions)

    def _read_json(self, path: Path, default: Any) -> Any:
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return default

    def _write_json(self, path: Path, data: Any) -> None:
        with NamedTemporaryFile("w", encoding="utf-8", delete=False, dir=self.data_dir) as tmp:
            json.dump(data, tmp, ensure_ascii=False, indent=2)
            tmp_path = Path(tmp.name)
        tmp_path.replace(path)
