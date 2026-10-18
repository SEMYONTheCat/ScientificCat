"""Тесты настроек user_settings.json (см. FS §10.1)."""

from __future__ import annotations

from services.settings import Settings


def test_settings_defaults(tmp_path) -> None:
    settings = Settings(path=tmp_path / "settings.json")
    assert settings.get("theme") == "light"
    assert settings.get("auto_save_interval") == 300


def test_settings_save_and_load(tmp_path) -> None:
    path = tmp_path / "settings.json"
    settings = Settings(path=path)
    settings.set("theme", "dark")
    settings.set("auto_save_interval", 60)
    settings.save()

    loaded = Settings(path=path)
    assert loaded.get("theme") == "dark"
    assert loaded.get("auto_save_interval") == 60


def test_settings_corrupt_file_uses_defaults(tmp_path) -> None:
    path = tmp_path / "settings.json"
    path.write_text("{ not valid json", encoding="utf-8")
    settings = Settings(path=path)
    assert settings.get("theme") == "light"