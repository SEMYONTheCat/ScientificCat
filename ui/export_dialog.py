"""Диалог экспорта документа (см. TZ §2.4, ADR-0006).

Выбор формата (PDF/DOCX/HTML/LaTeX), DPI для PNG, путь сохранения.
"""

from __future__ import annotations

from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

FORMAT_FILTERS = {
    "PDF": "PDF (*.pdf)",
    "DOCX": "Word (*.docx)",
    "HTML": "HTML (*.html)",
    "LaTeX": "LaTeX (*.tex)",
}


class ExportDialog(QDialog):
    """Диалог выбора формата экспорта и параметров."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Экспорт документа")
        self.resize(480, 200)

        self.format_combo = QComboBox()
        for name in FORMAT_FILTERS:
            self.format_combo.addItem(name)
        self.format_combo.currentTextChanged.connect(self._on_format_changed)

        self.dpi_spin = QSpinBox()
        self.dpi_spin.setRange(72, 600)
        self.dpi_spin.setValue(300)

        self.path_edit = QLineEdit()
        browse = QPushButton("Обзор...")
        browse.clicked.connect(self._browse)

        path_row = QHBoxLayout()
        path_row.addWidget(self.path_edit, 1)
        path_row.addWidget(browse)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Формат:"))
        layout.addWidget(self.format_combo)
        layout.addWidget(QLabel("DPI (для формул в DOCX/PDF):"))
        layout.addWidget(self.dpi_spin)
        layout.addWidget(QLabel("Файл:"))
        layout.addLayout(path_row)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self._on_format_changed(self.format_combo.currentText())

    def _browse(self) -> None:
        fmt = self.format_combo.currentText()
        path, _ = QFileDialog.getSaveFileName(
            self, "Сохранить как", "", FORMAT_FILTERS.get(fmt, "")
        )
        if path:
            self.path_edit.setText(path)

    def _on_format_changed(self, fmt: str) -> None:
        self.dpi_spin.setEnabled(fmt in ("DOCX", "PDF"))

    # ---------- Результат ----------

    def get_format(self) -> str:
        return self.format_combo.currentText()

    def get_dpi(self) -> int:
        return self.dpi_spin.value()

    def get_path(self) -> str | None:
        return self.path_edit.text().strip() or None