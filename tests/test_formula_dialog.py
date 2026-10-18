"""Тесты WYSIWYG-диалога формул (см. FS §3.2)."""

from __future__ import annotations

from ui.formula_dialog import FormulaDialog


def test_dialog_initial_state(qtbot) -> None:
    dialog = FormulaDialog()
    qtbot.addWidget(dialog)
    assert dialog.get_latex() == ""
    assert dialog.get_formula_type() == "inline"


def test_dialog_set_latex_and_type(qtbot) -> None:
    dialog = FormulaDialog()
    qtbot.addWidget(dialog)
    dialog.set_formula(r"\int_0^1 x dx", "display")
    assert dialog.get_latex() == r"\int_0^1 x dx"
    assert dialog.get_formula_type() == "display"


def test_dialog_insert_template_into_latex(qtbot) -> None:
    dialog = FormulaDialog()
    qtbot.addWidget(dialog)
    dialog.latex_input.setText("x + ")
    dialog.insert_symbol(r"\sqrt{}")
    assert dialog.get_latex() == "x + \\sqrt{}"


def test_dialog_validation_label(qtbot) -> None:
    dialog = FormulaDialog()
    qtbot.addWidget(dialog)
    dialog.latex_input.setText("E = mc^2")
    assert dialog.validation_label.text()  # "✓ OK" или аналог