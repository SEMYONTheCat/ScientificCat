"""Тесты новых возможностей: таблицы, шаблоны, BibTeX, палитра, статистика, недавние файлы."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import QDialog

from core.bibliography import BibManager, entries_to_bibtex
from core.document import BibEntry, Bibliography, Document, Table
from services.settings import Settings
from ui.bib_dialog import BibEntryEditDialog, BibManagerDialog
from ui.editor_widget import EditorWidget
from ui.main_window import MainWindow
from ui.stats_dialog import DocumentStatsDialog
from ui.symbol_palette import SymbolPickerDialog
from ui.template_dialog import TemplateDialog


def test_table_operations(qtbot) -> None:
    """Проверка добавления/удаления строк и столбцов и удаления таблицы."""
    editor = EditorWidget()
    qtbot.addWidget(editor)

    editor.insert_table(2, 2, caption="Таблица 1")
    table = editor.current_table()
    assert table is not None
    assert table.rows() == 2
    assert table.columns() == 2

    # Добавить строку ниже
    assert editor.add_table_row_below() is True
    assert table.rows() == 3

    # Добавить строку выше
    assert editor.add_table_row_above() is True
    assert table.rows() == 4

    # Удалить строку
    assert editor.remove_table_row() is True
    assert table.rows() == 3

    # Добавить столбец справа
    assert editor.add_table_col_right() is True
    assert table.columns() == 3

    # Добавить столбец слева
    assert editor.add_table_col_left() is True
    assert table.columns() == 4

    # Удалить столбец
    assert editor.remove_table_col() is True
    assert table.columns() == 3

    # Проверка сохранения в модель Document
    doc = editor.to_model()
    tables = [b for b in doc.body if isinstance(b, Table)]
    assert len(tables) == 1
    assert tables[0].rows == 3
    assert tables[0].cols == 3
    assert tables[0].caption == "Таблица 1"

    # Удалить таблицу целиком
    assert editor.delete_current_table() is True
    assert editor.current_table() is None


def test_table_context_menu_event(qtbot) -> None:
    """Контекстное меню строится и содержит действия для таблицы."""
    editor = EditorWidget()
    qtbot.addWidget(editor)
    editor.insert_table(2, 2)

    menu = editor.create_context_menu(editor.rect().center())
    assert menu is not None
    submenus = [a.menu() for a in menu.actions() if a.menu() is not None]
    table_menus = [m for m in submenus if m.title() == "Таблица"]
    assert len(table_menus) == 1
    table_menu = table_menus[0]
    action_texts = [a.text() for a in table_menu.actions()]
    assert "Добавить строку выше" in action_texts
    assert "Добавить строку ниже" in action_texts
    assert "Удалить строку" in action_texts
    assert "Добавить столбец слева" in action_texts
    assert "Добавить столбец справа" in action_texts
    assert "Удалить столбец" in action_texts
    assert "Удалить таблицу" in action_texts


def test_template_dialog(qtbot) -> None:
    """Проверка диалога выбора шаблона документа."""
    dialog = TemplateDialog()
    qtbot.addWidget(dialog)

    assert dialog._list_widget.count() >= 5
    path = dialog.get_selected_template_path()
    assert path is not None
    assert path.is_file()
    assert path.suffix == ".sdoc"

    # Переключение на другой шаблон
    dialog._list_widget.setCurrentRow(1)
    path2 = dialog.get_selected_template_path()
    assert path2 is not None
    assert path2 != path


def test_bibtex_export_and_manager(qtbot, tmp_path: Path, monkeypatch) -> None:
    """Проверка сериализации BibTeX и работы BibManagerDialog."""
    entries = [
        BibEntry(
            key="knuth1984",
            entry_type="article",
            title="Literate Programming",
            author="Donald E. Knuth",
            journal="The Computer Journal",
            year="1984",
        ),
        BibEntry(
            key="lamport1994",
            entry_type="book",
            title="LaTeX: A Document Preparation System",
            author="Leslie Lamport",
            year="1994",
        ),
    ]

    # Экспорт в BibTeX
    bib_text = entries_to_bibtex(entries)
    assert "@article{knuth1984," in bib_text
    assert "Donald E. Knuth" in bib_text
    assert "@book{lamport1994," in bib_text

    bib = Bibliography(style="GOST", entries=entries)
    manager = BibManager(bib)
    assert "Donald E. Knuth" in manager.export_bibtex()

    dialog = BibManagerDialog(bib)
    qtbot.addWidget(dialog)
    assert dialog._table.rowCount() == 2

    # Фильтрация
    dialog._search_edit.setText("Knuth")
    assert dialog._table.rowCount() == 1
    dialog._search_edit.clear()
    assert dialog._table.rowCount() == 2

    # Смена стиля
    dialog._style_combo.setCurrentText("IEEE")
    assert bib.style == "IEEE"

    # Добавление новой записи через мок
    new_entry = BibEntry(key="turing1936", title="Computable Numbers", author="A. Turing")
    monkeypatch.setattr(BibEntryEditDialog, "exec", lambda self: QDialog.DialogCode.Accepted)
    monkeypatch.setattr(BibEntryEditDialog, "get_entry", lambda self: new_entry)

    dialog.on_add_entry()
    assert len(bib.entries) == 3
    assert any(e.key == "turing1936" for e in bib.entries)

    # Экспорт в файл
    export_file = tmp_path / "refs.bib"
    monkeypatch.setattr(
        "PySide6.QtWidgets.QFileDialog.getSaveFileName",
        lambda *args, **kwargs: (str(export_file), "BibTeX (*.bib)"),
    )
    monkeypatch.setattr("PySide6.QtWidgets.QMessageBox.information", lambda *args, **kwargs: None)
    monkeypatch.setattr("PySide6.QtWidgets.QMessageBox.warning", lambda *args, **kwargs: None)
    monkeypatch.setattr("PySide6.QtWidgets.QMessageBox.question", lambda *args, **kwargs: None)
    dialog.on_export_bib()
    assert export_file.is_file()
    assert "turing1936" in export_file.read_text(encoding="utf-8")


def test_symbol_picker_dialog(qtbot) -> None:
    """Проверка автономной палитры символов в Unicode и LaTeX режимах."""
    dialog = SymbolPickerDialog()
    qtbot.addWidget(dialog)

    received_symbols: list[str] = []
    dialog.symbolInserted.connect(received_symbols.append)

    # По умолчанию режим Unicode
    assert dialog.radio_unicode.isChecked()
    dialog._on_palette_symbol(r"\alpha")
    assert len(received_symbols) == 1
    assert received_symbols[0] == "α"

    # Переключение в LaTeX
    dialog.radio_latex.setChecked(True)
    dialog._on_palette_symbol(r"\beta")
    assert len(received_symbols) == 2
    assert received_symbols[1] == r"\beta"


def test_recent_files_in_settings(tmp_path: Path) -> None:
    """Проверка сохранения и ограничения недавних файлов в Settings."""
    settings_file = tmp_path / "test_settings.json"
    settings = Settings(settings_file)

    f1 = tmp_path / "doc1.sdoc"
    f2 = tmp_path / "doc2.sdoc"
    f3 = tmp_path / "doc3.sdoc"
    for f in (f1, f2, f3):
        f.touch()

    settings.add_recent_file(f1)
    settings.add_recent_file(f2)
    assert settings.get_recent_files() == [str(f2.resolve()), str(f1.resolve())]

    # Добавление f1 снова перемещает его в начало
    settings.add_recent_file(f1)
    assert settings.get_recent_files() == [str(f1.resolve()), str(f2.resolve())]

    # Очистка
    settings.clear_recent_files()
    assert settings.get_recent_files() == []


def test_document_stats_dialog(qtbot) -> None:
    """Проверка корректности подсчёта статистики документа."""
    editor = EditorWidget()
    qtbot.addWidget(editor)
    editor.setPlainText("Раз два три четыре пять.")
    editor.insert_formula("E=mc^2")

    doc = Document.new()
    doc.bibliography.entries.append(BibEntry(key="ref1", title="Sample"))

    dialog = DocumentStatsDialog(editor, doc)
    qtbot.addWidget(dialog)

    text = editor.toPlainText()
    assert len(text.split()) >= 5
    assert len(editor.extract_formulas()) == 1


def test_editor_blockquote_and_environments(qtbot) -> None:
    """Проверка форматирования блочных цитат и научных окружений."""
    editor = EditorWidget()
    qtbot.addWidget(editor)

    editor.setPlainText("Текст параграфа")
    editor.toggle_blockquote()
    assert editor.textCursor().blockFormat().indent() == 1

    editor.toggle_blockquote()
    assert editor.textCursor().blockFormat().indent() == 0

    editor.insert_environment("Теорема", "Пифагора")
    assert "ТЕОРЕМА (Пифагора)" in editor.toPlainText()


def test_main_window_new_from_template(qtbot, monkeypatch) -> None:
    """Создание документа из шаблона обновляет редактор и заголовок."""
    template_path = Path("assets/templates/article.sdoc").resolve()
    monkeypatch.setattr(
        TemplateDialog,
        "get_selected_template_path",
        lambda self: template_path,
    )
    monkeypatch.setattr(TemplateDialog, "exec", lambda self: QDialog.DialogCode.Accepted)

    window = MainWindow()
    qtbot.addWidget(window)
    window._headless = True

    window.on_new_from_template()
    editor_text = window.editor.toPlainText()
    assert "Название статьи" in editor_text or "Введение" in editor_text
    assert "Название статьи" in window.windowTitle()
