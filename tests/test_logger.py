"""Тесты логирования и crash-дампов (TODO §5.6)."""

from __future__ import annotations

import logging

from services.logger import AppLogger, crash_dump_dir, write_crash_dump


def test_write_crash_dump(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("APPDATA", str(tmp_path))
    path = write_crash_dump("Traceback (most recent call last)...")
    assert path.exists()
    assert "Traceback" in path.read_text(encoding="utf-8")


def test_crash_dump_dir_created(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("APPDATA", str(tmp_path))
    directory = crash_dump_dir()
    assert directory.exists()


def test_app_logger_writes_file(tmp_path, monkeypatch, caplog) -> None:
    monkeypatch.setenv("APPDATA", str(tmp_path))
    app_logger = AppLogger("test_scientific_cat")
    with caplog.at_level(logging.DEBUG, logger="test_scientific_cat"):
        app_logger.info("привет")
        app_logger.error("ошибка")
    assert caplog.text != ""


def test_app_logger_reuses_handlers(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("APPDATA", str(tmp_path))
    a = AppLogger("test_reuse")
    handlers_a = a.logger.handlers
    b = AppLogger("test_reuse")
    assert b.logger.handlers == handlers_a