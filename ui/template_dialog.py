"""Диалог выбора шаблона документа (см. FS §7.1, TZ У-01).

Отображает доступные шаблоны из assets/templates с описанием структуры
и создаёт новый документ на основе выбранного шаблона.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from core.document import Document, Section
from services.paths import resource_path

TEMPLATE_METADATA: dict[str, dict[str, str]] = {
    "article.sdoc": {
        "title": "Научная статья",
        "icon": "📄",
        "description": (
            "Классическая структура исследовательской научной статьи: "
            "Введение, Методология, Результаты и Выводы. "
            "Включает библиографию по ГОСТ и блоки для формул."
        ),
    },
    "thesis.sdoc": {
        "title": "Диссертация",
        "icon": "🎓",
        "description": (
            "Шаблон диссертационной работы или выпускной квалификационной работы (ВКР). "
            "Разбит на главы, содержит аннотацию, оглавление и список литературы."
        ),
    },
    "report.sdoc": {
        "title": "Научно-технический отчёт",
        "icon": "📊",
        "description": (
            "Отчёт о выполнении научно-исследовательской работы (НИР). "
            "Оформление соответствует требованиям ГОСТ 7.32."
        ),
    },
    "lecture.sdoc": {
        "title": "Лекция / Конспект",
        "icon": "📚",
        "description": (
            "Учебные материалы, конспект лекции или семинара с выделением определений, "
            "теорем, формул и примеров."
        ),
    },
    "review.sdoc": {
        "title": "Рецензия / Отзыв",
        "icon": "📝",
        "description": (
            "Отзыв или экспертная рецензия на научную статью или диссертацию "
            "с оценкой актуальности, новизны и критическими замечаниями."
        ),
    },
}


class TemplateDialog(QDialog):
    """Диалог создания документа на основе встроенных шаблонов."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Создать документ из шаблона")
        self.resize(650, 420)
        self.templates_dir = resource_path("assets/templates")
        self._selected_path: Path | None = None

        self._list_widget = QListWidget()
        self._list_widget.currentRowChanged.connect(self._on_template_selected)

        self._info_browser = QTextBrowser()
        self._info_browser.setOpenExternalLinks(False)

        self._build_ui()
        self._load_templates()

    def exec(self) -> int:
        return super().exec()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)

        title_lbl = QLabel("Выберите шаблон для создания нового документа:")
        title_lbl.setStyleSheet("font-weight: bold; font-size: 11pt;")
        layout.addWidget(title_lbl)

        content_layout = QHBoxLayout()

        self._list_widget.setFixedWidth(240)
        content_layout.addWidget(self._list_widget)
        content_layout.addWidget(self._info_browser, 1)

        layout.addLayout(content_layout, 1)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self.btn_ok = buttons.button(QDialogButtonBox.StandardButton.Ok)
        if self.btn_ok:
            self.btn_ok.setText("Создать")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _load_templates(self) -> None:
        self._list_widget.clear()
        if not self.templates_dir.is_dir():
            return

        files = sorted(self.templates_dir.glob("*.sdoc"))
        for file_path in files:
            meta = TEMPLATE_METADATA.get(
                file_path.name,
                {"title": file_path.stem.capitalize(), "icon": "📄", "description": ""},
            )
            item = QListWidgetItem(f"{meta['icon']} {meta['title']}")
            item.setData(Qt.ItemDataRole.UserRole, str(file_path))
            self._list_widget.addItem(item)

        if self._list_widget.count() > 0:
            self._list_widget.setCurrentRow(0)

    def _on_template_selected(self, row: int) -> None:
        item = self._list_widget.item(row)
        if not item:
            self._selected_path = None
            self._info_browser.clear()
            return

        path_str = item.data(Qt.ItemDataRole.UserRole)
        self._selected_path = Path(path_str) if path_str else None
        if not self._selected_path or not self._selected_path.is_file():
            return

        meta = TEMPLATE_METADATA.get(self._selected_path.name, {})
        title = meta.get("title", self._selected_path.stem)
        desc = meta.get("description", "Пользовательский шаблон.")

        sections_info = []
        try:
            doc = Document.from_file(self._selected_path)
            for block in doc.body:
                if isinstance(block, Section):
                    sections_info.append(f"• {block.heading}")
        except Exception:  # noqa: BLE001
            sections_info = ["(Не удалось прочитать разделы)"]

        sec_html = (
            "<br>".join(sections_info)
            if sections_info
            else "<i>Нет предварительных разделов</i>"
        )
        html = f"""
        <h3 style="margin-top:0;">{title}</h3>
        <p>{desc}</p>
        <hr>
        <b>Структура документа:</b><br>
        {sec_html}
        """
        self._info_browser.setHtml(html)

    def get_selected_template_path(self) -> Path | None:
        """Вернуть путь к выбранному шаблону или None."""
        return self._selected_path
