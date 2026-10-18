"""Логирование приложения (см. FS §9.3, TZ §4.4).

Логи пишутся в %APPDATA%/ScientificCat/logs/YYYYMMDD.log и в консоль.
"""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path

from services.user_data import app_data_dir


def _base_dir() -> Path:
    return app_data_dir()


def _log_dir() -> Path:
    path = _base_dir() / "logs"
    path.mkdir(parents=True, exist_ok=True)
    return path


def crash_dump_dir() -> Path:
    """Каталог для crash-дампов (см. TODO §5.6)."""
    path = _base_dir() / "crashes"
    path.mkdir(parents=True, exist_ok=True)
    return path


def write_crash_dump(message: str) -> Path:
    """Записать текст ошибки в файл дампа, вернуть путь."""
    path = crash_dump_dir() / f"crash-{datetime.now().strftime('%Y%m%d-%H%M%S')}.log"
    path.write_text(message, encoding="utf-8")
    return path


class AppLogger:
    """Настраиваемый логгер с файловым и консольным обработчиками."""

    def __init__(self, name: str = "ScientificCat") -> None:
        self.logger = logging.getLogger(name)
        if self.logger.handlers:
            return  # уже настроен

        self.logger.setLevel(logging.DEBUG)

        log_file = _log_dir() / f"{datetime.now().strftime('%Y%m%d')}.log"
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)

        console = logging.StreamHandler()
        console.setLevel(logging.INFO)

        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        file_handler.setFormatter(formatter)
        console.setFormatter(formatter)

        self.logger.addHandler(file_handler)
        self.logger.addHandler(console)

    def debug(self, msg: str) -> None:
        self.logger.debug(msg)

    def info(self, msg: str) -> None:
        self.logger.info(msg)

    def warning(self, msg: str) -> None:
        self.logger.warning(msg)

    def error(self, msg: str) -> None:
        self.logger.error(msg)

    def critical(self, msg: str) -> None:
        self.logger.critical(msg)