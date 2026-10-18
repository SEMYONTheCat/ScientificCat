"""Визуальный менеджер библиографии (см. FS §4.6, TZ §2.6, TODO v2.0 Фаза 3).

Позволяет просматривать, фильтровать, добавлять, редактировать и удалять
записи BibTeX, переключать стиль цитирования (ГОСТ/APA/IEEE), а также
импортировать и экспортировать файлы .bib.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from core.bibliography import BibManager, entries_to_bibtex, parse_bibtex
from core.document import BibEntry, Bibliography


class BibEntryEditDialog(QDialog):
    """Диалог добавления или редактирования одной записи BibTeX."""

    def __init__(
        self,
        entry: BibEntry | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Редактирование записи библиографии" if entry else "Новая запись")
        self.resize(500, 460)

        self.key_edit = QLineEdit(entry.key if entry else "")
        self.type_combo = QComboBox()
        self.type_combo.addItems([
            "article",
            "book",
            "inproceedings",
            "phdthesis",
            "techreport",
            "misc",
        ])
        if entry and entry.entry_type:
            idx = self.type_combo.findText(entry.entry_type.lower())
            if idx >= 0:
                self.type_combo.setCurrentIndex(idx)

        self.title_edit = QLineEdit(entry.title if entry else "")
        self.author_edit = QLineEdit(entry.author if entry else "")
        self.journal_edit = QLineEdit(entry.journal if entry else "")
        self.year_edit = QLineEdit(entry.year if entry else "")
        self.volume_edit = QLineEdit(entry.volume if entry else "")
        self.number_edit = QLineEdit(entry.number if entry else "")
        self.pages_edit = QLineEdit(entry.pages if entry else "")
        self.publisher_edit = QLineEdit(entry.publisher if entry else "")
        self.doi_edit = QLineEdit(entry.doi if entry else "")
        self.url_edit = QLineEdit(entry.url if entry else "")

        layout = QVBoxLayout(self)
        form = QFormLayout()
        form.addRow("BibTeX Key *:", self.key_edit)
        form.addRow("Тип:", self.type_combo)
        form.addRow("Название:", self.title_edit)
        form.addRow("Автор(ы):", self.author_edit)
        form.addRow("Журнал / Книга:", self.journal_edit)
        form.addRow("Год:", self.year_edit)
        form.addRow("Том:", self.volume_edit)
        form.addRow("Номер / Выпуск:", self.number_edit)
        form.addRow("Страницы:", self.pages_edit)
        form.addRow("Издательство:", self.publisher_edit)
        form.addRow("DOI:", self.doi_edit)
        form.addRow("URL:", self.url_edit)
        layout.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._validate_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _validate_and_accept(self) -> None:
        if not self.key_edit.text().strip():
            QMessageBox.warning(self, "Ошибка", "Ключ (Key) обязателен для заполнения.")
            return
        self.accept()

    def exec(self) -> int:
        return super().exec()

    def get_entry(self) -> BibEntry:
        """Получить сформированный объект BibEntry."""
        return BibEntry(
            key=self.key_edit.text().strip(),
            entry_type=self.type_combo.currentText(),
            title=self.title_edit.text().strip(),
            author=self.author_edit.text().strip(),
            journal=self.journal_edit.text().strip(),
            year=self.year_edit.text().strip(),
            volume=self.volume_edit.text().strip(),
            number=self.number_edit.text().strip(),
            pages=self.pages_edit.text().strip(),
            publisher=self.publisher_edit.text().strip(),
            doi=self.doi_edit.text().strip(),
            url=self.url_edit.text().strip(),
        )


class BibManagerDialog(QDialog):
    """Полнофункциональный диалог управления библиографией документа."""

    def __init__(
        self,
        bibliography: Bibliography,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.bibliography = bibliography
        self.setWindowTitle("Менеджер библиографии (BibTeX)")
        self.resize(850, 560)

        self._search_edit = QLineEdit()
        self._search_edit.setPlaceholderText("Поиск по автору, названию, ключу или году...")
        self._search_edit.textChanged.connect(self._refresh_table)

        self._style_combo = QComboBox()
        self._style_combo.addItems(["GOST", "APA", "IEEE"])
        idx = self._style_combo.findText(self.bibliography.style)
        if idx >= 0:
            self._style_combo.setCurrentIndex(idx)
        self._style_combo.currentTextChanged.connect(self._on_style_changed)

        self._table = QTableWidget()
        self._table.setColumnCount(6)
        self._table.setHorizontalHeaderLabels([
            "№",
            "Ключ",
            "Тип",
            "Автор",
            "Название",
            "Год",
        ])
        header = self._table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self._table.itemSelectionChanged.connect(self._on_selection_changed)
        self._table.doubleClicked.connect(self.on_edit_entry)

        self._preview_browser = QTextBrowser()
        self._preview_browser.setMaximumHeight(80)

        self._build_ui()
        self._refresh_table()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)

        top_row = QHBoxLayout()
        top_row.addWidget(QLabel("Поиск:"))
        top_row.addWidget(self._search_edit, 1)
        top_row.addWidget(QLabel("Стиль оформления:"))
        top_row.addWidget(self._style_combo)
        layout.addLayout(top_row)

        middle_layout = QHBoxLayout()
        middle_layout.addWidget(self._table, 1)

        side_buttons = QVBoxLayout()
        btn_add = QPushButton("Добавить...")
        btn_add.clicked.connect(self.on_add_entry)
        side_buttons.addWidget(btn_add)

        btn_edit = QPushButton("Изменить...")
        btn_edit.clicked.connect(self.on_edit_entry)
        side_buttons.addWidget(btn_edit)

        btn_delete = QPushButton("Удалить")
        btn_delete.clicked.connect(self.on_delete_entry)
        side_buttons.addWidget(btn_delete)

        side_buttons.addSpacing(16)

        btn_import = QPushButton("Импорт .bib...")
        btn_import.clicked.connect(self.on_import_bib)
        side_buttons.addWidget(btn_import)

        btn_export = QPushButton("Экспорт .bib...")
        btn_export.clicked.connect(self.on_export_bib)
        side_buttons.addWidget(btn_export)

        side_buttons.addStretch()
        middle_layout.addLayout(side_buttons)

        layout.addLayout(middle_layout, 1)

        preview_group = QGroupBox("Предпросмотр ссылки в списке литературы")
        preview_layout = QVBoxLayout(preview_group)
        preview_layout.addWidget(self._preview_browser)
        layout.addWidget(preview_group)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.accept)
        layout.addWidget(buttons)

    def _on_style_changed(self, style: str) -> None:
        self.bibliography.style = style
        self._update_preview()

    def _filtered_entries(self) -> list[tuple[int, BibEntry]]:
        query = self._search_edit.text().strip().lower()
        results: list[tuple[int, BibEntry]] = []
        for number, entry in enumerate(self.bibliography.entries, start=1):
            if not query:
                results.append((number, entry))
                continue
            haystack = (
                f"{entry.key} {entry.author} {entry.title} {entry.year} {entry.journal}".lower()
            )
            if query in haystack:
                results.append((number, entry))
        return results

    def _refresh_table(self) -> None:
        filtered = self._filtered_entries()
        self._table.setRowCount(len(filtered))
        for row, (num, entry) in enumerate(filtered):
            item_num = QTableWidgetItem(str(num))
            item_num.setData(Qt.ItemDataRole.UserRole, entry.key)
            self._table.setItem(row, 0, item_num)
            self._table.setItem(row, 1, QTableWidgetItem(entry.key))
            self._table.setItem(row, 2, QTableWidgetItem(entry.entry_type))
            self._table.setItem(row, 3, QTableWidgetItem(entry.author))
            self._table.setItem(row, 4, QTableWidgetItem(entry.title))
            self._table.setItem(row, 5, QTableWidgetItem(entry.year))
        if len(filtered) > 0 and self._table.currentRow() < 0:
            self._table.selectRow(0)
        self._update_preview()

    def _selected_entry(self) -> tuple[int, BibEntry] | None:
        row = self._table.currentRow()
        if row < 0:
            return None
        item = self._table.item(row, 0)
        if not item:
            return None
        key = item.data(Qt.ItemDataRole.UserRole)
        for num, entry in enumerate(self.bibliography.entries, start=1):
            if entry.key == key:
                return num, entry
        return None

    def _on_selection_changed(self) -> None:
        self._update_preview()

    def _update_preview(self) -> None:
        selected = self._selected_entry()
        if not selected:
            self._preview_browser.setText("(Выберите запись для предпросмотра)")
            return
        num, entry = selected
        formatted = BibManager.format_entry(entry, self.bibliography.style, num)
        self._preview_browser.setText(formatted)

    def on_add_entry(self) -> None:
        """Добавить новую запись библиографии через форму."""
        dialog = BibEntryEditDialog(parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_entry = dialog.get_entry()
            # Проверка уникальности ключа
            if any(e.key == new_entry.key for e in self.bibliography.entries):
                QMessageBox.warning(
                    self, "Ошибка", f"Запись с ключом '{new_entry.key}' уже существует."
                )
                return
            self.bibliography.entries.append(new_entry)
            self._refresh_table()

    def on_edit_entry(self) -> None:
        """Отредактировать выбранную запись библиографии."""
        selected = self._selected_entry()
        if not selected:
            return
        _num, entry = selected
        dialog = BibEntryEditDialog(entry=entry, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            updated = dialog.get_entry()
            # Обновить поля
            entry.key = updated.key
            entry.entry_type = updated.entry_type
            entry.title = updated.title
            entry.author = updated.author
            entry.journal = updated.journal
            entry.year = updated.year
            entry.volume = updated.volume
            entry.number = updated.number
            entry.pages = updated.pages
            entry.publisher = updated.publisher
            entry.doi = updated.doi
            entry.url = updated.url
            self._refresh_table()

    def on_delete_entry(self) -> None:
        """Удалить выбранную запись."""
        selected = self._selected_entry()
        if not selected:
            return
        _num, entry = selected
        ans = QMessageBox.question(
            self,
            "Удаление записи",
            f"Удалить запись '{entry.key}' ({entry.title or 'без названия'})?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if ans == QMessageBox.StandardButton.Yes:
            self.bibliography.entries = [e for e in self.bibliography.entries if e.key != entry.key]
            self._refresh_table()

    def on_import_bib(self) -> None:
        """Импортировать записи из стороннего файла BibTeX."""
        path, _ = QFileDialog.getOpenFileName(self, "Импорт BibTeX", "", "BibTeX (*.bib)")
        if not path:
            return
        try:
            content = Path(path).read_text(encoding="utf-8")
            entries = parse_bibtex(content)
            added = 0
            for entry in entries:
                if not any(e.key == entry.key for e in self.bibliography.entries):
                    self.bibliography.entries.append(entry)
                    added += 1
            QMessageBox.information(
                self,
                "Импорт завершён",
                f"Импортировано записей: {added} (пропущено дубликатов: {len(entries) - added})",
            )
            self._refresh_table()
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "Ошибка импорта", f"Не удалось прочитать файл: {exc}")

    def on_export_bib(self) -> None:
        """Экспортировать текущие записи в файл .bib."""
        if not self.bibliography.entries:
            QMessageBox.information(self, "Экспорт", "Список литературы пуст.")
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Экспорт BibTeX", "references.bib", "BibTeX (*.bib)"
        )
        if not path:
            return
        try:
            bibtex_text = entries_to_bibtex(self.bibliography.entries)
            Path(path).write_text(bibtex_text, encoding="utf-8")
            QMessageBox.information(
                self,
                "Экспорт",
                f"Успешно сохранено записей: {len(self.bibliography.entries)}.",
            )
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "Ошибка экспорта", f"Не удалось записать файл: {exc}")
