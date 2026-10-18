"""Общие fixtures для тестов Scientific Cat."""

from __future__ import annotations

from pathlib import Path

import pytest

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"


@pytest.fixture
def fixtures_dir() -> Path:
    """Каталог с эталонными .sdoc-фикстурами."""
    return FIXTURES_DIR