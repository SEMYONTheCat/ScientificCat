"""Кроссплатформенные пути для изменяемых данных приложения."""

from __future__ import annotations

import os
import sys
from pathlib import Path


def app_data_dir() -> Path:
    """Вернуть пользовательский каталог Scientific Cat и создать его."""
    explicit = os.getenv("SCIENTIFIC_CAT_DATA_DIR")
    if explicit:
        base = Path(explicit)
    elif appdata := os.getenv("APPDATA"):
        base = Path(appdata) / "ScientificCat"
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support" / "ScientificCat"
    elif xdg_data := os.getenv("XDG_DATA_HOME"):
        base = Path(xdg_data) / "ScientificCat"
    else:
        base = Path.home() / ".local" / "share" / "ScientificCat"
    base.mkdir(parents=True, exist_ok=True)
    return base
