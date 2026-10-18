"""WYSIWYG-диалог вставки формул (см. FS §3.2, TZ Фр-01..Фр-08).

Шаблоны, LaTeX-ввод с live-валидацией, превью KaTeX, палитра символов,
выбор Inline/Display, кнопки OK/Cancel.
"""

from __future__ import annotations

import json
import os

from PySide6.QtCore import Qt, QUrl
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QRadioButton,
    QVBoxLayout,
    QWidget,
)

from core.formula_engine import FormulaEngine
from core.formula_templates import FORMULA_TEMPLATES
from services.paths import resource_path
from ui.symbol_palette import SymbolPalette

KATEX_DIR = resource_path("assets/katex")


class FormulaDialog(QDialog):
    """Диалог конструктора формул."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Formula Editor")
        self.resize(780, 540)

        self.engine = FormulaEngine()
        self.latex_input = QLineEdit()
        self.latex_input.textChanged.connect(self._on_latex_changed)
        self.validation_label = QLabel()

        self.radio_inline = QRadioButton("Inline (в тексте)")
        self.radio_display = QRadioButton("Display (блок)")
        self.radio_inline.setChecked(True)

        self.symbol_palette = SymbolPalette()
        self.symbol_palette.symbolInserted.connect(self.insert_symbol)

        self.preview = self._create_preview()

        self._build_ui()
        self._on_latex_changed()

    # ---------- Построение ----------

    def _create_preview(self) -> QWidget:
        if os.environ.get("QT_QPA_PLATFORM") == "offscreen":
            label = QLabel("(превью недоступно в headless-режиме)")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setMinimumHeight(120)
            return label
        from PySide6.QtWebEngineWidgets import QWebEngineView  # noqa: PLC0415

        return QWebEngineView()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)

        # Панель шаблонов
        templates_bar = QWidget()
        tl = QHBoxLayout(templates_bar)
        tl.setContentsMargins(0, 0, 0, 0)
        for name, latex in FORMULA_TEMPLATES.items():
            btn = QPushButton(name)
            btn.clicked.connect(lambda _=False, ltx=latex: self.insert_symbol(ltx))
            tl.addWidget(btn)
        tl.addStretch()
        layout.addWidget(templates_bar)

        # Поле ввода + валидация
        latex_layout = QHBoxLayout()
        latex_layout.addWidget(QLabel("LaTeX:"))
        latex_layout.addWidget(self.latex_input, 1)
        layout.addLayout(latex_layout)
        layout.addWidget(self.validation_label)

        # Превью
        preview_group = QGroupBox("Live Preview")
        preview_layout = QVBoxLayout(preview_group)
        preview_layout.addWidget(self.preview)
        layout.addWidget(preview_group, 1)

        # Палитра символов
        palette_group = QGroupBox("Символы")
        palette_layout = QVBoxLayout(palette_group)
        palette_layout.addWidget(self.symbol_palette)
        layout.addWidget(palette_group, 1)

        # Тип формулы
        type_group = QGroupBox("Тип формулы")
        type_layout = QHBoxLayout(type_group)
        type_layout.addWidget(self.radio_inline)
        type_layout.addWidget(self.radio_display)
        layout.addWidget(type_group)

        # Кнопки
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    # ---------- Поведение ----------

    def insert_symbol(self, latex: str) -> None:
        cursor = self.latex_input.cursorPosition()
        text = self.latex_input.text()
        self.latex_input.setText(text[:cursor] + latex + text[cursor:])
        self.latex_input.setCursorPosition(cursor + len(latex))
        self._on_latex_changed()

    def _on_latex_changed(self) -> None:
        latex = self.latex_input.text()
        if not latex.strip():
            self.validation_label.setText("")
            self._render_preview("")
            return
        ok, msg = self.engine.validate_latex(latex)
        if ok:
            self.validation_label.setText("✓ OK")
            self.validation_label.setStyleSheet("color: green;")
        else:
            self.validation_label.setText(f"✗ {msg[:80]}")
            self.validation_label.setStyleSheet("color: red;")
        self._render_preview(latex)

    def _render_preview(self, latex: str) -> None:
        if isinstance(self.preview, QLabel):
            self.preview.setText(latex or "(пусто)")
            return
        html = _PREVIEW_TEMPLATE.format(latex=json.dumps(latex))
        self.preview.setHtml(html, QUrl.fromLocalFile(str(KATEX_DIR) + "/"))

    # ---------- Результат ----------

    def set_formula(self, latex: str, formula_type: str = "inline") -> None:
        """Заполнить диалог существующей формулой для редактирования."""
        self.latex_input.setText(latex)
        self.radio_display.setChecked(formula_type == "display")
        self.radio_inline.setChecked(formula_type != "display")
        self.latex_input.setFocus()
        self.latex_input.selectAll()

    def get_latex(self) -> str:
        return self.latex_input.text()

    def get_formula_type(self) -> str:
        return "inline" if self.radio_inline.isChecked() else "display"


_PREVIEW_TEMPLATE = """<!DOCTYPE html>
<html><head><meta charset="utf-8">
<link rel="stylesheet" href="katex.min.css">
<script src="katex.min.js"></script>
</head><body>
<div id="formula"></div>
<script>
  katex.render({latex} || ' ', document.getElementById('formula'),
               {{throwOnError: false, displayMode: false}});
</script>
</body></html>"""