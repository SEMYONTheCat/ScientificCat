"""Тесты модели Formula (см. FS §4.2, ADR-0003)."""

from __future__ import annotations

import pytest

from core.formula import Formula


class TestFormula:
    def test_generate_id_prefix(self) -> None:
        f = Formula(latex="a + b")
        assert f.id.startswith("eq")
        assert len(f.id) >= 5

    def test_default_type_inline(self) -> None:
        f = Formula(latex="x")
        assert f.type == "inline"

    def test_validate_valid(self) -> None:
        assert Formula(latex="x^2 + y^2 = z^2").validate() is True

    def test_validate_matrix(self) -> None:
        # матрица не должна давать ложную ошибку (в отличие от sympy)
        assert Formula(r"\begin{pmatrix}1&2\\3&4\end{pmatrix}").validate() is True

    def test_validate_returns_bool_without_crash(self) -> None:
        for latex in (r"\frac{", "x^ + ", r"\int_0^\infty dx", "E = mc^2"):
            result = Formula(latex=latex).validate()
            assert isinstance(result, bool)

    @pytest.mark.parametrize("ftype", ["inline", "display"])
    def test_formula_type_roundtrip(self, ftype: str) -> None:
        f = Formula(latex="E=mc^2", formula_type=ftype)  # type: ignore[arg-type]
        assert f.type == ftype