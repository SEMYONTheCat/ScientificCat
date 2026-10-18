"""Палитра символов (см. FS §3.3, TZ Фр-03).

Вкладки: Греческие, Математические, Кириллица, Спецсимволы + поле поиска.
Вставляет LaTeX-код через сигнал symbolInserted.
"""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QDialog,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QRadioButton,
    QScrollArea,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from core.formula_templates import (
    CYRILLIC_LETTERS,
    GREEK_SYMBOLS,
    MATH_SYMBOLS,
    SPECIAL_SYMBOLS,
)


class SymbolPalette(QWidget):
    """Палитра символов с поиском и вставкой LaTeX."""

    symbolInserted = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._search = QLineEdit()
        self._search.setPlaceholderText("Поиск символа...")
        self._search.textChanged.connect(self._filter)

        self._tabs = QTabWidget()
        self._tab_symbols: dict[int, list[tuple[str, str]]] = {}

        self._tabs.addTab(self._build_tab(GREEK_SYMBOLS), "Греческие")
        self._tabs.addTab(self._build_tab(MATH_SYMBOLS), "Математические")
        self._tabs.addTab(self._build_cyrillic_tab(), "Кириллица")
        self._tabs.addTab(self._build_tab(SPECIAL_SYMBOLS), "Спецсимволы")

        layout = QVBoxLayout(self)
        layout.addWidget(self._search)
        layout.addWidget(self._tabs)

    # ---------- Построение ----------

    def _build_tab(self, symbols: list[tuple[str, str]]) -> QWidget:
        container = QWidget()
        grid = QGridLayout(container)
        for index, (display, latex) in enumerate(symbols):
            button = QPushButton(display)
            button.setFixedSize(40, 32)
            button.clicked.connect(lambda _=False, ltx=latex: self.symbolInserted.emit(ltx))
            grid.addWidget(button, index // 8, index % 8)
        self._tab_symbols[self._tabs.count()] = list(symbols)
        return self._wrap_scroll(container)

    def _build_cyrillic_tab(self) -> QWidget:
        container = QWidget()
        grid = QGridLayout(container)
        for index, letter in enumerate(CYRILLIC_LETTERS):
            button = QPushButton(letter)
            button.setFixedSize(32, 32)
            button.clicked.connect(lambda _=False, ltr=letter: self.symbolInserted.emit(ltr))
            grid.addWidget(button, index // 16, index % 16)
        self._tab_symbols[self._tabs.count()] = [(c, c) for c in CYRILLIC_LETTERS]
        return self._wrap_scroll(container)

    def _wrap_scroll(self, content: QWidget) -> QWidget:
        scroll = QScrollArea()
        scroll.setWidget(content)
        scroll.setWidgetResizable(True)
        return scroll

    # ---------- Поведение ----------

    def insert_symbol(self, latex: str) -> None:
        self.symbolInserted.emit(latex)

    def _filter(self, text: str) -> None:
        query = text.strip().lower()
        for index, symbols in self._tab_symbols.items():
            matches = any(
                query in display.lower() or query in latex.lower()
                for display, latex in symbols
            )
            self._tabs.setTabEnabled(index, matches or not query)


class SymbolPickerDialog(QDialog):
    """Автономное диалоговое окно палитры символов для вставки в редактор."""

    symbolInserted = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Палитра символов")
        self.resize(540, 400)

        self.palette = SymbolPalette(self)
        self.radio_unicode = QRadioButton("Символ (Unicode)")
        self.radio_latex = QRadioButton("LaTeX-код")
        self.radio_unicode.setChecked(True)

        mode_layout = QHBoxLayout()
        mode_layout.addWidget(QLabel("Режим вставки:"))
        mode_layout.addWidget(self.radio_unicode)
        mode_layout.addWidget(self.radio_latex)
        mode_layout.addStretch()

        layout = QVBoxLayout(self)
        layout.addLayout(mode_layout)
        layout.addWidget(self.palette, 1)

        self.palette.symbolInserted.connect(self._on_palette_symbol)

    def _on_palette_symbol(self, latex: str) -> None:
        if self.radio_latex.isChecked():
            self.symbolInserted.emit(latex)
        else:
            display = self._find_display(latex)
            self.symbolInserted.emit(display)

    @staticmethod
    def _find_display(latex: str) -> str:
        for sym_list in (GREEK_SYMBOLS, MATH_SYMBOLS, SPECIAL_SYMBOLS):
            for disp, ltx in sym_list:
                if ltx == latex:
                    return disp
        return latex