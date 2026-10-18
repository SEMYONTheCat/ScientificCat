"""Модель математической формулы (см. FS §4.2, ADR-0003).

Formula — модель данных (без рендеринга); рендер/валидация — в
core/formula_engine.py.
"""

from __future__ import annotations

import secrets
from typing import Literal

from pylatexenc.latex2text import LatexNodes2Text

FormulaType = Literal["inline", "display"]


class Formula:
    """Модель математической формулы."""

    def __init__(
        self,
        latex: str,
        formula_type: FormulaType = "inline",
        number: int = 0,
        formula_id: str | None = None,
    ) -> None:
        self.latex = latex
        self.type: FormulaType = formula_type
        self.number = number
        self.id = formula_id or self._generate_id()

    @staticmethod
    def _generate_id() -> str:
        """Генерация ID формата eq + 6 hex (см. FS §2.2, §5.1)."""
        return "eq" + secrets.token_hex(3)

    def validate(self) -> bool:
        """Синтаксическая проверка через pylatexenc (быстрый проход).

        Авторитетная проверка полноты формулы — KaTeX (см. ADR-0003),
        выполняется в FormulaEngine, где доступен рендер.
        """
        try:
            LatexNodes2Text().latex_to_text(self.latex)
            return True
        except Exception:
            return False

    def __repr__(self) -> str:  # pragma: no cover - отладочное
        return f"Formula({self.type}, {self.latex!r}, #{self.number})"