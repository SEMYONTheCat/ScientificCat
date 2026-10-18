"""Тесты диалога поиска и замены (TODO §5.3)."""

from __future__ import annotations

from ui.editor_widget import EditorWidget
from ui.find_replace_dialog import FindReplaceDialog


def test_find_next(qtbot) -> None:
    editor = EditorWidget()
    editor.setPlainText("hello world hello")
    dialog = FindReplaceDialog(editor)
    qtbot.addWidget(dialog)
    dialog.find_edit.setText("hello")
    dialog.find_next()
    assert editor.textCursor().selectedText() == "hello"


def test_find_no_result_does_not_crash(qtbot) -> None:
    editor = EditorWidget()
    editor.setPlainText("abc")
    dialog = FindReplaceDialog(editor)
    qtbot.addWidget(dialog)
    dialog.find_edit.setText("zzz")
    dialog.find_next()  # не должно быть исключений


def test_replace_one(qtbot) -> None:
    editor = EditorWidget()
    editor.setPlainText("cat and dog")
    dialog = FindReplaceDialog(editor)
    qtbot.addWidget(dialog)
    dialog.find_edit.setText("cat")
    dialog.replace_edit.setText("kitten")
    dialog.replace_one()
    assert "kitten and dog" in editor.toPlainText()


def test_replace_all(qtbot) -> None:
    editor = EditorWidget()
    editor.setPlainText("a b a c a")
    dialog = FindReplaceDialog(editor)
    qtbot.addWidget(dialog)
    dialog.find_edit.setText("a")
    dialog.replace_edit.setText("X")
    dialog.replace_all()
    assert editor.toPlainText() == "X b X c X"


def test_case_sensitive_flag(qtbot) -> None:
    editor = EditorWidget()
    editor.setPlainText("A a")
    dialog = FindReplaceDialog(editor)
    qtbot.addWidget(dialog)
    dialog.case_check.setChecked(True)
    dialog.find_edit.setText("a")
    dialog.find_next()
    assert editor.textCursor().selectedText() == "a"


def test_find_and_replace_inside_formula_preserves_formula_object(
    qtbot, monkeypatch
) -> None:
    monkeypatch.setattr("ui.editor_widget._render_latex", lambda latex: None)
    editor = EditorWidget()
    editor.insertPlainText("Перед ")
    editor.insert_formula(r"\alpha + \beta", formula_id="eq-search")
    dialog = FindReplaceDialog(editor)
    qtbot.addWidget(dialog)
    dialog.find_edit.setText(r"\beta")
    dialog.replace_edit.setText(r"\gamma")
    cursor = editor.textCursor()
    cursor.movePosition(cursor.MoveOperation.Start)
    editor.setTextCursor(cursor)

    dialog.find_next()
    assert editor.textCursor().selectedText() == "\ufffc"

    dialog.replace_one()
    assert editor.extract_formulas() == [r"\alpha + \gamma"]
    assert editor.extract_formula_records()[0][0] == "eq-search"