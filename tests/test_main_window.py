"""Смоук-тест главного окна (см. ADR-0001, Фаза 4.5)."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import QMessageBox

from core import __version__
from core.document import BibEntry, Document, Paragraph
from ui.main_window import MainWindow


def test_main_window_opens(qtbot) -> None:
    window = MainWindow()
    qtbot.addWidget(window)
    window.show()
    assert window.windowTitle() == f"Scientific Cat {__version__}"
    assert window.editor is not None
    assert window.preview is not None


def test_editor_insert_and_extract_formula(qtbot) -> None:
    window = MainWindow()
    qtbot.addWidget(window)
    window.editor.insertPlainText("Текст: ")
    window.editor.insert_formula("E = mc^2", number=1)
    window.editor.insertPlainText(" и ")

    extracted = window.editor.extract_formulas()
    assert extracted == ["E = mc^2"]


def test_status_bar_and_zoom(qtbot) -> None:
    window = MainWindow()
    qtbot.addWidget(window)
    window.show()

    # Строка состояния содержит информативные виджеты
    assert window._lbl_words.text() == "Слов: 0"
    assert window._lbl_formulas.text() == "Формул: 0"
    assert "Зум" in window._lbl_zoom.text()

    # Ввод текста обновляет счётчик слов
    window.editor.setPlainText("один два три")
    assert window._lbl_words.text() == "Слов: 3"

    # Масштабирование
    zoom_before = window._zoom
    window.zoom_in()
    assert window._zoom == zoom_before + 10
    window.zoom_out()
    assert window._zoom == zoom_before
    window.zoom_reset()
    assert window._zoom == 100


def test_toolbar_has_icons(qtbot) -> None:
    window = MainWindow()
    qtbot.addWidget(window)
    window.show()
    assert not window.act_formula.icon().isNull()
    assert not window.act_save.icon().isNull()
    assert not window.act_headings[0].icon().isNull()
    assert not window.act_bullet_list.icon().isNull()
    assert not window.act_citation.icon().isNull()
    assert window.act_subscript.shortcut().toString()
    assert window.act_help.shortcut().toString() == "F1"
    assert window.act_about.text() == "&О программе"
    assert window.act_open.text() == "&Открыть..."


def test_save_uses_current_editor_content(qtbot, tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr("ui.editor_widget._render_latex", lambda latex: None)
    window = MainWindow()
    qtbot.addWidget(window)
    window.editor.insertPlainText("Текст ")
    window.editor.insert_formula("x^2", number=1, formula_id="eq000001")
    window.editor.insertPlainText(" после формулы")
    output = tmp_path / "edited.sdoc"

    assert window._save_document(str(output)) is True

    loaded = Document.from_file(output)
    assert len(loaded.body) == 1
    paragraph = loaded.body[0]
    assert isinstance(paragraph, Paragraph)
    assert [type(item).__name__ for item in paragraph.inline_content()] == [
        "Run",
        "Formula",
        "Run",
    ]
    assert "".join(run.text for run in paragraph.runs) == "Текст  после формулы"
    assert paragraph.formulas[0].latex == "x^2"


def test_open_loads_formula_back_into_editor(qtbot, tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr("ui.editor_widget._render_latex", lambda latex: None)
    source = tmp_path / "source.sdoc"
    creator = MainWindow()
    qtbot.addWidget(creator)
    creator.editor.insertPlainText("Формула: ")
    creator.editor.insert_formula("a+b", number=1, formula_id="eq000002")
    assert creator._save_document(str(source)) is True

    window = MainWindow()
    qtbot.addWidget(window)
    window._load_document(str(source))

    assert window.editor.extract_formulas() == ["a+b"]
    assert window.current_path == str(source)


def test_insert_reference_uses_stable_formula_id(qtbot, monkeypatch) -> None:
    monkeypatch.setattr("ui.editor_widget._render_latex", lambda latex: None)
    monkeypatch.setattr(
        "ui.main_window.QInputDialog.getItem",
        lambda *args, **kwargs: (args[3][0], True),
    )
    window = MainWindow()
    qtbot.addWidget(window)
    window.editor.insert_formula("x+y", formula_id="eq000010")

    window.on_insert_reference()
    model = window.document_from_editor()

    paragraph = model.body[0]
    assert isinstance(paragraph, Paragraph)
    assert paragraph.runs[0].reference_target == "eq000010"
    assert paragraph.runs[0].text == "см. уравнение (1)"


def test_insert_citation_preserves_bibtex_key(qtbot, monkeypatch) -> None:
    monkeypatch.setattr(
        "ui.main_window.QInputDialog.getItem",
        lambda *args, **kwargs: (args[3][0], True),
    )
    window = MainWindow()
    qtbot.addWidget(window)
    window.document.bibliography.entries.append(
        BibEntry(key="einstein1905", author="Эйнштейн")
    )

    window.on_insert_citation()
    model = window.document_from_editor()

    paragraph = model.body[0]
    assert isinstance(paragraph, Paragraph)
    assert paragraph.runs[0].citation_key == "einstein1905"
    assert paragraph.runs[0].text == "[1]"


def test_new_is_cancelled_when_document_has_unsaved_changes(
    qtbot, monkeypatch
) -> None:
    monkeypatch.setattr(
        "ui.main_window.QMessageBox.warning",
        lambda *args, **kwargs: QMessageBox.StandardButton.Cancel,
    )
    window = MainWindow()
    qtbot.addWidget(window)
    window._headless = False
    window.editor.insertPlainText("Не потерять")

    window.on_new()

    assert window.editor.toPlainText() == "Не потерять"
    assert window.editor.document().isModified()
    window._headless = True