"""Тесты панели навигации и извлечения заголовков (TODO §5.2)."""

from __future__ import annotations

from PySide6.QtCore import Qt

from core.document import Document, Paragraph, Run, Section
from core.formula import Formula
from ui.editor_widget import EditorWidget
from ui.navigation_panel import NavigationPanel


def _editor_with_headings() -> EditorWidget:
    editor = EditorWidget()
    editor.clear()
    editor.insertPlainText("Введение")
    editor.set_heading(1)
    editor.textCursor().insertBlock()
    editor.insertPlainText("обычный текст")
    editor.set_heading(0)
    editor.textCursor().insertBlock()
    editor.insertPlainText("Методы")
    editor.set_heading(1)
    editor.textCursor().insertBlock()
    editor.insertPlainText("Подход")
    editor.set_heading(2)
    return editor


def test_extract_headings(qtbot) -> None:
    editor = _editor_with_headings()
    qtbot.addWidget(editor)
    headings = editor.extract_headings()
    assert [(lvl, t) for lvl, t, _ in headings] == [
        (1, "Введение"),
        (1, "Методы"),
        (2, "Подход"),
    ]


def test_panel_set_headings(qtbot) -> None:
    panel = NavigationPanel()
    qtbot.addWidget(panel)
    editor = _editor_with_headings()
    qtbot.addWidget(editor)
    panel.set_headings(editor.extract_headings())
    assert panel.count() == 3


def test_panel_empty(qtbot) -> None:
    panel = NavigationPanel()
    qtbot.addWidget(panel)
    panel.set_headings([])
    assert panel.count() == 1
    assert "H1" in panel.item(0).text()
    assert not panel.item(0).flags()


def test_go_to_block(qtbot) -> None:
    editor = _editor_with_headings()
    qtbot.addWidget(editor)
    editor.go_to_block(0)
    assert editor.textCursor().blockNumber() == 0
    # «Подход» — heading 2 (4-й блок)
    editor.go_to_block(3)
    assert editor.textCursor().block().text() == "Подход"


def test_enter_after_heading_starts_normal_paragraph(qtbot) -> None:
    editor = EditorWidget()
    qtbot.addWidget(editor)
    editor.setPlainText("Заголовок")
    editor.set_heading(1)
    editor.moveCursor(editor.textCursor().MoveOperation.End)

    qtbot.keyClick(editor, Qt.Key.Key_Return)
    qtbot.keyClicks(editor, "body text")

    assert [(level, text) for level, text, _ in editor.extract_headings()] == [
        (1, "Заголовок")
    ]
    assert editor.document().findBlockByNumber(1).text() == "body text"


def test_same_heading_action_toggles_back_to_body(qtbot) -> None:
    editor = EditorWidget()
    qtbot.addWidget(editor)
    editor.setPlainText("Не заголовок")

    editor.set_heading(1)
    assert editor.extract_headings()
    editor.set_heading(1)

    assert editor.extract_headings() == []


def test_loading_document_does_not_leak_heading_style(qtbot, monkeypatch) -> None:
    monkeypatch.setattr("ui.editor_widget._render_latex", lambda latex: None)
    document = Document.new()
    document.body.append(Section(id="sec001", heading="Привет!", level=1))
    formula = Formula(r"\alpha=\beta+\gamma", formula_id="eq000001")
    text = Run("первая формула: ")
    document.body.append(
        Paragraph(
            id="p001",
            runs=[text],
            formulas=[formula],
            content=[text, formula],
        )
    )
    document.body.append(Section(id="sec002", heading="Заголовок1", level=1))
    editor = EditorWidget()
    qtbot.addWidget(editor)

    editor.load_model(document)

    assert [(level, text) for level, text, _ in editor.extract_headings()] == [
        (1, "Привет!"),
        (1, "Заголовок1"),
    ]
    assert editor.extract_formulas() == [r"\alpha=\beta+\gamma"]


def test_formula_inserted_from_heading_moves_to_body_block(qtbot, monkeypatch) -> None:
    monkeypatch.setattr("ui.editor_widget._render_latex", lambda latex: None)
    editor = EditorWidget()
    qtbot.addWidget(editor)
    editor.setPlainText("Раздел")
    editor.set_heading(1)

    editor.insert_formula("x^2", formula_id="eq000002")

    assert editor.document().blockCount() == 2
    assert editor.extract_headings() == [(1, "Раздел", 0)]
    assert editor.extract_formulas() == ["x^2"]