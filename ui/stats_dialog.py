"""Диалог детальной статистики документа (см. TZ §3.1, TODO v2.0 Фаза 8).

Подсчитывает слова, символы (с пробелами и без), число абзацев, формул,
таблиц, разделов и библиографических ссылок, а также расчётное время чтения.
"""

from __future__ import annotations

import math

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGroupBox,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from core.document import Document, Section, Table
from ui.editor_widget import EditorWidget


class DocumentStatsDialog(QDialog):
    """Окно подробной статистики открытого документа."""

    def __init__(
        self,
        editor: EditorWidget,
        document: Document,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Статистика документа")
        self.resize(420, 380)

        self.editor = editor
        self.document = document

        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)

        text = self.editor.toPlainText()
        words = len(text.split())
        chars_with_spaces = len(text)
        chars_without_spaces = len(text.replace(" ", "").replace("\n", "").replace("\t", ""))
        paragraphs = text.count("\n") + 1 if text else 0
        formulas = len(self.editor.extract_formulas())

        tables_count = sum(1 for b in self.document.body if isinstance(b, Table))
        sections_count = sum(1 for b in self.document.body if isinstance(b, Section))
        citations_count = len(self.document.bibliography.entries)

        est_pages = max(1, math.ceil(words / 300))
        reading_time_min = max(1, math.ceil(words / 200))

        # Группа: Текст
        group_text = QGroupBox("Текст и символы")
        form_text = QFormLayout(group_text)
        form_text.addRow("Слов:", QLabel(str(words)))
        form_text.addRow("Символов (с пробелами):", QLabel(str(chars_with_spaces)))
        form_text.addRow("Символов (без пробелов):", QLabel(str(chars_without_spaces)))
        form_text.addRow("Абзацев / строк:", QLabel(str(paragraphs)))
        layout.addWidget(group_text)

        # Группа: Элементы документа
        group_elements = QGroupBox("Элементы структуры")
        form_elem = QFormLayout(group_elements)
        form_elem.addRow("Формул:", QLabel(str(formulas)))
        form_elem.addRow("Таблиц:", QLabel(str(tables_count)))
        form_elem.addRow("Разделов (H1–H6):", QLabel(str(sections_count)))
        form_elem.addRow("Источников литературы:", QLabel(str(citations_count)))
        layout.addWidget(group_elements)

        # Группа: Оценки
        group_estimates = QGroupBox("Оценки объёма")
        form_est = QFormLayout(group_estimates)
        form_est.addRow("Страниц A4 (~300 слов/стр):", QLabel(f"~{est_pages}"))
        form_est.addRow("Время чтения (~200 слов/мин):", QLabel(f"~{reading_time_min} мин."))
        layout.addWidget(group_estimates)

        # Кнопка закрытия
        btn_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        btn_box.rejected.connect(self.accept)
        layout.addWidget(btn_box)
