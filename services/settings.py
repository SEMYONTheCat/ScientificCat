"""Настройки приложения user_settings.json (см. FS §10.1, TZ §2.5).

Хранится в %APPDATA%/ScientificCat/user_settings.json; при отсутствии —
значения по умолчанию.
"""

from __future__ import annotations

import contextlib
import json
from pathlib import Path
from typing import Any

from services.user_data import app_data_dir


def _settings_dir() -> Path:
    return app_data_dir()


DEFAULT_SETTINGS: dict[str, Any] = {
    "theme": "light",
    "language": "ru",
    "font_family": "Arial",
    "font_size": 12,
    "auto_save_interval": 300,
    "recent_files": [],
    "window": {"width": 1200, "height": 800, "splitter_ratio": 0.5},
    "export": {"default_format": "pdf", "pdf_dpi": 300},
}


class Settings:
    """Загрузка/сохранение настроек из user_settings.json."""

    def __init__(self, path: str | Path | None = None) -> None:
        self.path = Path(path) if path else _settings_dir() / "user_settings.json"
        self.data: dict[str, Any] = dict(DEFAULT_SETTINGS)
        self.data.update(self._load())

    def _load(self) -> dict[str, Any]:
        if not self.path.is_file():
            return {}
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
            return raw if isinstance(raw, dict) else {}
        except (json.JSONDecodeError, OSError):
            return {}

    def get(self, key: str, default: Any = None) -> Any:
        return self.data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self.data[key] = value

    def save(self) -> None:
        self.path.write_text(
            json.dumps(self.data, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    def add_recent_file(self, file_path: str | Path, max_items: int = 10) -> None:
        """Добавить путь в список недавних файлов (без дубликатов, в начало списка)."""
        clean_path = str(Path(file_path).resolve())
        recent: list[str] = [p for p in self.get("recent_files", []) if p != clean_path]
        recent.insert(0, clean_path)
        self.set("recent_files", recent[:max_items])
        with contextlib.suppress(OSError):
            self.save()

    def get_recent_files(self) -> list[str]:
        """Вернуть список существующих недавних файлов."""
        return [p for p in self.get("recent_files", []) if Path(p).is_file()]

    def clear_recent_files(self) -> None:
        """Очистить список недавних файлов."""
        self.set("recent_files", [])
        with contextlib.suppress(OSError):
            self.save()
