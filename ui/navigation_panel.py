"""Боковая панель навигации по заголовкам (см. FS §4.7, TODO §5.2).

Оглавление из заголовков H1–H6; клик переводит курсор к разделу.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QListWidget, QListWidgetItem


class NavigationPanel(QListWidget):
    """Список заголовков документа; emits heading_activated(blockNumber)."""

    heading_activated = Signal(int)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Оглавление")
        self.setWordWrap(True)
        self.setToolTip("Оглавление строится из строк со стилями H1-H6.")
        self.itemClicked.connect(self._on_item_clicked)
        self.set_headings([])

    def set_headings(self, headings: list[tuple[int, str, int]]) -> None:
        """Заполнить панель: (level, text, block_number)."""
        self.clear()
        if not headings:
            item = QListWidgetItem(
                "Заголовков пока нет.\n"
                "Выделите строку и выберите Формат → Заголовок (H1–H6)."
            )
            item.setFlags(Qt.ItemFlag.NoItemFlags)
            item.setToolTip("После назначения H1-H6 здесь появится оглавление.")
            self.addItem(item)
            return
        for level, text, block_number in headings:
            item = QListWidgetItem(("    " * (level - 1)) + text)
            item.setData(Qt.ItemDataRole.UserRole, block_number)
            self.addItem(item)

    def _on_item_clicked(self, item: QListWidgetItem) -> None:
        block_number = item.data(Qt.ItemDataRole.UserRole)
        if block_number is not None:
            self.heading_activated.emit(int(block_number))