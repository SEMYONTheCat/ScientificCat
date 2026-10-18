"""Help and About dialogs for Scientific Cat."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QLabel,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from core import __version__
from services.paths import resource_path


class HelpDialog(QDialog):
    """Short built-in user guide."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Помощь — Scientific Cat")
        self.resize(700, 620)

        self.help_browser = QTextBrowser()
        self.help_browser.setOpenExternalLinks(False)
        self.help_browser.setHtml(_HELP_HTML)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addWidget(self.help_browser, 1)
        layout.addWidget(buttons)


class AboutDialog(QDialog):
    """Application information and dedication."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("О программе — Scientific Cat")
        self.resize(500, 680)

        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pixmap = QPixmap(str(resource_path("assets/icons/icon.png")))
        if not pixmap.isNull():
            self.image_label.setPixmap(
                pixmap.scaled(
                    400,
                    500,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )

        title = QLabel(f"<h2>Scientific Cat {__version__}</h2>")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.dedication_label = QLabel("Проект посвящён памяти кота Семёна")
        self.dedication_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.dedication_label.setWordWrap(True)
        dedication_font = self.dedication_label.font()
        dedication_font.setPointSize(13)
        dedication_font.setBold(True)
        self.dedication_label.setFont(dedication_font)

        description = QLabel(
            "Научный WYSIWYG-редактор с формулами LaTeX, "
            "открытым форматом .sdoc и экспортом документов."
        )
        description.setAlignment(Qt.AlignmentFlag.AlignCenter)
        description.setWordWrap(True)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addWidget(self.image_label, 1)
        layout.addWidget(title)
        layout.addWidget(self.dedication_label)
        layout.addWidget(description)
        layout.addWidget(buttons)


_HELP_HTML = """
<h1>Scientific Cat</h1>
<p>Редактор научных документов с формулами, оглавлением и экспортом.</p>

<h2>Основы работы</h2>
<ol>
  <li>Введите текст в центральной панели <b>Документ</b>.</li>
  <li>Сохраните документ через <b>Файл → Сохранить</b> (<b>Ctrl+S</b>).</li>
  <li>Правая панель автоматически показывает итоговый вид документа.</li>
</ol>

<h2>Оглавление</h2>
<p>
  Выделите строку и назначьте ей стиль через
  <b>Формат → Заголовок → H1–H6</b>. Заголовок автоматически появится
  слева. Щелчок по пункту оглавления перемещает курсор к разделу.
</p>

<h2>Формулы</h2>
<p>
  Нажмите <b>Ctrl+M</b> или выберите <b>Вставка → Формула</b>.
  Формула отображается в документе как карточка и рендерится справа.
  <b>Дважды щёлкните карточку формулы</b>, чтобы изменить её.
</p>

<h2>Форматирование</h2>
<ul>
  <li><b>Ctrl+B / Ctrl+I / Ctrl+U</b> — жирный, курсив, подчёркивание.</li>
  <li><b>Формат</b> — списки, выравнивание, верхние и нижние индексы.</li>
  <li><b>Ctrl+F / Ctrl+H</b> — поиск и замена.</li>
  <li><b>Ctrl+колесо</b> — масштаб центрального редактора.</li>
</ul>

<h2>Ссылки и библиография</h2>
<p>
  Импортируйте BibTeX через <b>Файл → Импорт BibTeX</b>, затем вставляйте
  цитаты через <b>Вставка → Цитата</b>. Перекрёстные ссылки на формулы
  добавляются через <b>Вставка → Перекрёстная ссылка</b> и автоматически
  перенумеровываются.
</p>

<h2>Экспорт</h2>
<p>
  Команда <b>Файл → Экспорт</b> создаёт PDF, DOCX, HTML или LaTeX.
  Для Markdown используйте отдельную команду экспорта в меню «Файл».
</p>
"""
