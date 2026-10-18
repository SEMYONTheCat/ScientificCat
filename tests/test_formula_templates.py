"""Тесты шаблонов формул и наборов символов (TZ Фр-02/Фр-03)."""

from __future__ import annotations

from core.formula_templates import (
    CYRILLIC_LETTERS,
    FORMULA_TEMPLATES,
    GREEK_SYMBOLS,
    MATH_SYMBOLS,
)


def test_templates_present() -> None:
    assert "Дробь" in FORMULA_TEMPLATES
    assert "Матрица" in FORMULA_TEMPLATES
    assert all(t for t in FORMULA_TEMPLATES.values())


def test_greek_symbols_have_latex() -> None:
    assert ("α", r"\alpha") in GREEK_SYMBOLS
    assert all(latex.startswith("\\") for _, latex in GREEK_SYMBOLS)


def test_math_symbols_have_latex() -> None:
    assert ("∞", r"\infty") in MATH_SYMBOLS
    assert all(latex for _, latex in MATH_SYMBOLS)


def test_cyrillic_letters_present() -> None:
    assert "А" in CYRILLIC_LETTERS
    assert "я" in CYRILLIC_LETTERS