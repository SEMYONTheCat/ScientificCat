"""Тесты разрешения путей к ресурсам (обычный и frozen-режим, TODO §6.1)."""

from __future__ import annotations

import sys

from main import frozen_smoke_test
from services.paths import resource_path
from services.user_data import app_data_dir


def test_resource_path_normal() -> None:
    assert (resource_path("assets/styles") / "light.qss").is_file()


def test_resource_path_frozen(monkeypatch, tmp_path) -> None:
    target = tmp_path / "assets" / "styles"
    target.mkdir(parents=True)
    (target / "light.qss").write_text("", encoding="utf-8")

    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "_MEIPASS", str(tmp_path), raising=False)

    assert (resource_path("assets/styles") / "light.qss").is_file()


def test_user_data_path_uses_xdg_on_linux(monkeypatch, tmp_path) -> None:
    monkeypatch.delenv("APPDATA", raising=False)
    monkeypatch.delenv("SCIENTIFIC_CAT_DATA_DIR", raising=False)
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
    monkeypatch.setattr(sys, "platform", "linux")

    assert app_data_dir() == tmp_path / "ScientificCat"


def test_source_tree_passes_frozen_smoke_contract() -> None:
    assert frozen_smoke_test() == 0