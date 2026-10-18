"""Диалог поиска и замены (см. TODO §5.3, FS §4.7).

Работает поверх `QTextEdit`: поиск/замена по тексту с учётом регистра
(опционально), включая фрагменты формул (LaTeX-текст объектов).
"""

from __future__ import annotations

from PySide6.QtGui import QTextDocument
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
)

from ui.editor_widget import EditorWidget


class FindReplaceDialog(QDialog):
    """Не-модальный диалог Ctrl+F / Ctrl+H."""

    def __init__(self, editor: EditorWidget, parent=None, replace_mode: bool = False) -> None:
        super().__init__(parent)
        self._editor = editor
        self.setWindowTitle("Поиск и замена")

        self.find_edit = QLineEdit()
        self.find_edit.setPlaceholderText("Найти…")
        self.replace_edit = QLineEdit()
        self.replace_edit.setPlaceholderText("Заменить на…")

        self.case_check = QCheckBox("Учитывать регистр")

        btn_find = QPushButton("Найти далее")
        btn_replace = QPushButton("Заменить")
        btn_replace_all = QPushButton("Заменить все")
        btn_close = QPushButton("Закрыть")

        btn_find.clicked.connect(self.find_next)
        btn_replace.clicked.connect(self.replace_one)
        btn_replace_all.clicked.connect(self.replace_all)
        btn_close.clicked.connect(self.close)

        find_row = QHBoxLayout()
        find_row.addWidget(QLabel("Найти:"))
        find_row.addWidget(self.find_edit)

        replace_row = QHBoxLayout()
        replace_row.addWidget(QLabel("Заменить:"))
        replace_row.addWidget(self.replace_edit)

        btns = QHBoxLayout()
        btns.addWidget(btn_find)
        btns.addWidget(btn_replace)
        btns.addWidget(btn_replace_all)
        btns.addWidget(btn_close)

        layout = QVBoxLayout()
        layout.addLayout(find_row)
        layout.addLayout(replace_row)
        layout.addWidget(self.case_check)
        layout.addLayout(btns)
        self.setLayout(layout)

        self.find_edit.returnPressed.connect(self.find_next)

        if replace_mode:
            self.replace_edit.setFocus()

    def _flags(self) -> QTextDocument.FindFlag:
        if self.case_check.isChecked():
            return QTextDocument.FindFlag.FindCaseSensitively
        return QTextDocument.FindFlag(0)

    def find_next(self) -> None:
        text = self.find_edit.text()
        if not text:
            return
        if not self._editor.find_content(text, self._flags()):
            # к началу документа (wrap-around)
            cursor = self._editor.textCursor()
            cursor.movePosition(cursor.MoveOperation.Start)
            self._editor.setTextCursor(cursor)
            self._editor.find_content(text, self._flags())

    def replace_one(self) -> None:
        if not self._editor.textCursor().hasSelection():
            self.find_next()
        if self._editor.textCursor().hasSelection():
            replaced_formula = self._editor.replace_formula_search_match(
                self.replace_edit.text(),
                case_sensitive=self.case_check.isChecked(),
            )
            if not replaced_formula:
                self._editor.textCursor().insertText(self.replace_edit.text())
        self.find_next()

    def replace_all(self) -> None:
        text = self.find_edit.text()
        if not text:
            return
        replacement = self.replace_edit.text()
        count = 0
        cursor = self._editor.textCursor()
        cursor.movePosition(cursor.MoveOperation.Start)
        self._editor.setTextCursor(cursor)
        while self._editor.find_content(text, self._flags()):
            replaced_formulas = self._editor.replace_formula_search_match(
                replacement,
                all_occurrences=True,
                case_sensitive=self.case_check.isChecked(),
            )
            if replaced_formulas:
                count += replaced_formulas
            else:
                self._editor.textCursor().insertText(replacement)
                count += 1
        self.setWindowTitle(f"Поиск и замена — заменено: {count}")