"""Разрешение путей к ресурсам (обычный запуск vs PyInstaller frozen).

При сборке onefile/onedir PyInstaller распаковывает бандл в `sys._MEIPASS`;
все обращения к `assets/`, `icons/` и т.п. должны идти через `resource_path`.
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def resource_path(relative: str) -> Path:
    """Вернуть абсолютный путь к ресурсу (учитывает frozen-режим PyInstaller)."""
    if getattr(sys, "frozen", False):
        base = Path(getattr(sys, "_MEIPASS", PROJECT_ROOT))
        return base / relative
    return PROJECT_ROOT / relative