"""Главное окно приложения (см. FS §3.1, §4.7).

Этап 2: меню/тулбар с actions, live-preview (ADR-0014), автосохранение
(ADR-0003), темы и настройки (FS §10.1).
"""

from __future__ import annotations

import math
import os
from pathlib import Path

from PySide6.QtCore import QEvent, Qt, QTimer
from PySide6.QtGui import (
    QAction,
    QCloseEvent,
    QColor,
    QIcon,
    QKeySequence,
    QPainter,
    QPixmap,
)
from PySide6.QtWidgets import (
    QDialog,
    QDockWidget,
    QFileDialog,
    QInputDialog,
    QLabel,
    QMainWindow,
    QMessageBox,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from core import __version__
from core.document import Document
from core.markdown import document_to_md, md_to_document
from services.autostore import AutoStore
from services.logger import AppLogger
from services.paths import resource_path
from services.settings import Settings
from ui.editor_widget import EditorWidget
from ui.find_replace_dialog import FindReplaceDialog
from ui.navigation_panel import NavigationPanel
from ui.preview_widget import PreviewWidget

STYLES_DIR = resource_path("assets/styles")
PREVIEW_DEBOUNCE_MS = 300

# Unicode-глифы для иконок кнопок (TODO §7 / UI).
_GLYPHS: dict[str, str] = {
    "new": "✚",
    "new_template": "📋",
    "open": "📂",
    "open_md": "📄",
    "save": "💾",
    "save_as": "📥",
    "print": "🖨",
    "export": "⇩",
    "export_md": "⬇",
    "bib": "📚",
    "quit": "✕",
    "undo": "↩",
    "redo": "↪",
    "find": "🔍",
    "replace": "🔁",
    "bold": "𝐁",
    "italic": "𝐼",
    "underline": "U",
    "subscript": "x₂",
    "superscript": "x²",
    "quote": "❞",
    "heading1": "H1",
    "heading2": "H2",
    "heading3": "H3",
    "bullet_list": "•",
    "number_list": "1.",
    "align_left": "L",
    "align_center": "C",
    "align_right": "R",
    "align_justify": "J",
    "light": "☀",
    "dark": "☾",
    "formula": "∑",
    "symbol": "Ω",
    "table": "▦",
    "reference": "⛓",
    "citation": "[1]",
    "stats": "📊",
    "zoom_in": "+",
    "zoom_out": "−",
}

_ICON_CACHE: dict[str, QIcon] = {}


def _make_icon(glyph: str) -> QIcon:
    """Собрать QIcon из Unicode-символа (рендер на прозрачный QPixmap)."""
    if glyph not in _ICON_CACHE:
        pixmap = QPixmap(24, 24)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        font = painter.font()
        font.setPixelSize(17)
        painter.setFont(font)
        painter.setPen(QColor("#333333"))
        painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, glyph)
        painter.end()
        _ICON_CACHE[glyph] = QIcon(pixmap)
    return _ICON_CACHE[glyph]


class MainWindow(QMainWindow):
    """Главное окно Scientific Cat."""

    def __init__(self, logger: AppLogger | None = None) -> None:
        super().__init__()
        self._logger = logger or AppLogger()
        self.settings = Settings()
        self.document = Document.new()
        self.current_path: str | None = None

        self.setWindowTitle(f"Scientific Cat {__version__}")
        self.setWindowIcon(QIcon(str(resource_path("assets/icons/icon.png"))))
        self.resize(1500, 950)
        self.setMinimumSize(1000, 650)
        self._zoom = 100

        # В headless/offscreen (CI, тесты) QtWebEngine падает при завершении
        # после рендера превью — живое превью включается только при реальном дисплее.
        self._headless = os.environ.get("QT_QPA_PLATFORM") == "offscreen"

        self.editor = EditorWidget()
        self.editor.formulaEditRequested.connect(self.on_edit_formula)
        self.editor.viewport().installEventFilter(self)
        self.preview = QWidget() if self._headless else PreviewWidget()
        self.autostore = AutoStore(
            self.document,
            interval=int(self.settings.get("auto_save_interval", 300)),
            document_provider=self._sync_document_from_editor,
            recovery_path=self.settings.path.parent / "Untitled.sdoc.recover",
            error_handler=self._on_autosave_error,
        )

        self._preview_timer = QTimer()
        self._preview_timer.setSingleShot(True)
        self._preview_timer.setInterval(PREVIEW_DEBOUNCE_MS)
        self._preview_timer.timeout.connect(self._render_preview)

        self._setup_ui()
        self._apply_theme(self.settings.get("theme", "light"))
        if not self._headless:
            self.editor.textChanged.connect(self._schedule_preview)
        self.editor.textChanged.connect(self._update_navigation)
        self.editor.textChanged.connect(self._update_status)
        self.editor.cursorPositionChanged.connect(self._update_status)
        self._find_dialog: FindReplaceDialog | None = None

        self.autostore.start()
        self._offer_recovery()
        self._logger.info("Главное окно создано")

    # ---------- UI ----------

    def _setup_ui(self) -> None:
        splitter = QSplitter(Qt.Orientation.Horizontal)
        editor_pane = QWidget()
        editor_layout = QVBoxLayout(editor_pane)
        editor_layout.setContentsMargins(0, 0, 0, 0)
        editor_title = QLabel(
            "Документ  ·  формулы отображаются как карточки; двойной щелчок — изменить"
        )
        editor_title.setObjectName("PaneTitle")
        editor_layout.addWidget(editor_title)
        editor_layout.addWidget(self.editor, 1)

        preview_pane = QWidget()
        preview_layout = QVBoxLayout(preview_pane)
        preview_layout.setContentsMargins(0, 0, 0, 0)
        preview_title = QLabel("Предпросмотр")
        preview_title.setObjectName("PaneTitle")
        preview_layout.addWidget(preview_title)
        preview_layout.addWidget(self.preview, 1)

        splitter.addWidget(editor_pane)
        splitter.addWidget(preview_pane)
        splitter.setSizes([800, 700])
        self.setCentralWidget(splitter)

        self.navigation = NavigationPanel()
        self.navigation.heading_activated.connect(self.editor.go_to_block)
        dock = QDockWidget("Оглавление", self)
        dock.setObjectName("NavigationDock")
        dock.setWidget(self.navigation)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, dock)

        self.menubar = self.menuBar()
        self.toolbar = self.addToolBar("Основные")
        self.toolbar.setIconSize(QPixmap(24, 24).size())
        self.toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)

        # Увеличенный базовый масштаб — текст и формулы крупнее и лучше видны.
        self.editor.set_zoom(1.1)
        self._zoom = 110

        self._create_menus()
        self._build_status_bar()
        self._update_status()

    def _create_menus(self) -> None:
        self._create_file_menu()
        self._create_edit_menu()
        self._create_format_menu()
        self._create_table_menu()
        self._create_insert_menu()
        self._create_view_menu()
        self._create_tools_menu()
        self._create_help_menu()

    def _create_file_menu(self) -> None:
        menu_file = self.menubar.addMenu("&Файл")
        self.act_new = self._add(menu_file, "&Новый", "Ctrl+N", self.on_new, "new")
        self.act_new_template = self._add(
            menu_file,
            "Создать из &шаблона...",
            "Ctrl+Shift+N",
            self.on_new_from_template,
            "new_template",
        )
        self.act_open = self._add(menu_file, "&Открыть...", "Ctrl+O", self.on_open, "open")
        self.act_open_md = self._add(
            menu_file, "Открыть Markdown...", None, self.on_open_md, "open_md"
        )
        self.menu_recent = menu_file.addMenu("Недавние &документы")
        self._update_recent_files_menu()

        menu_file.addSeparator()
        self.act_save = self._add(menu_file, "&Сохранить", "Ctrl+S", self.on_save, "save")
        self.act_save_as = self._add(
            menu_file, "Сохранить &как...", "Ctrl+Shift+S", self.on_save_as, "save_as"
        )
        menu_file.addSeparator()
        self.act_print = self._add(menu_file, "&Печать...", "Ctrl+P", self.on_print, "print")
        self.act_print_preview = self._add(
            menu_file,
            "Предварительный просмотр печати...",
            None,
            self.on_print_preview,
            add_to_toolbar=False,
        )
        menu_file.addSeparator()
        self.act_export = self._add(menu_file, "Экспорт...", "Ctrl+E", self.on_export, "export")
        self.act_export_md = self._add(
            menu_file, "Экспорт Markdown", None, self.on_export_md, "export_md"
        )
        menu_file.addSeparator()
        self.act_import_bib = self._add(
            menu_file, "Импорт BibTeX...", None, self.on_import_bib, "bib"
        )
        menu_file.addSeparator()
        self.act_quit = self._add(menu_file, "&Выход", "Alt+F4", self.close, "quit")

    def _create_edit_menu(self) -> None:
        menu_edit = self.menubar.addMenu("&Правка")
        self.act_undo = self._add(menu_edit, "&Отменить", "Ctrl+Z", self.editor.undo, "undo")
        self.act_redo = self._add(menu_edit, "&Повторить", "Ctrl+Y", self.editor.redo, "redo")
        menu_edit.addSeparator()
        self.act_find = self._add(
            menu_edit, "&Найти...", "Ctrl+F", lambda: self._open_find(False), "find"
        )
        self.act_replace = self._add(
            menu_edit, "&Заменить...", "Ctrl+H", lambda: self._open_find(True), "replace"
        )
        menu_edit.addSeparator()
        self.act_bold = self._add(menu_edit, "Жирный", "Ctrl+B", self.editor.make_bold, "bold")
        self.act_italic = self._add(
            menu_edit, "Курсив", "Ctrl+I", self.editor.make_italic, "italic"
        )
        self.act_underline = self._add(
            menu_edit, "Подчёркнутый", "Ctrl+U", self.editor.make_underline, "underline"
        )

    def _create_table_menu(self) -> None:
        menu_table = self.menubar.addMenu("&Таблица")
        self.act_insert_table_menu = self._add(
            menu_table,
            "Вставить таблицу...",
            "Ctrl+Shift+T",
            self.on_insert_table,
            "table",
            add_to_toolbar=False,
        )
        menu_table.addSeparator()
        self._add(
            menu_table,
            "Добавить строку выше",
            None,
            self.editor.add_table_row_above,
            add_to_toolbar=False,
        )
        self._add(
            menu_table,
            "Добавить строку ниже",
            None,
            self.editor.add_table_row_below,
            add_to_toolbar=False,
        )
        self._add(
            menu_table,
            "Удалить строку",
            None,
            self.editor.remove_table_row,
            add_to_toolbar=False,
        )
        menu_table.addSeparator()
        self._add(
            menu_table,
            "Добавить столбец слева",
            None,
            self.editor.add_table_col_left,
            add_to_toolbar=False,
        )
        self._add(
            menu_table,
            "Добавить столбец справа",
            None,
            self.editor.add_table_col_right,
            add_to_toolbar=False,
        )
        self._add(
            menu_table,
            "Удалить столбец",
            None,
            self.editor.remove_table_col,
            add_to_toolbar=False,
        )
        menu_table.addSeparator()
        self._add(
            menu_table,
            "Удалить таблицу",
            None,
            self.editor.delete_current_table,
            add_to_toolbar=False,
        )

    def _create_insert_menu(self) -> None:
        menu_insert = self.menubar.addMenu("&Вставка")
        self.act_formula = self._add(
            menu_insert, "&Формула", "Ctrl+M", self.on_insert_formula, "formula"
        )
        self.act_symbol = self._add(
            menu_insert, "&Символ...", "Ctrl+Shift+U", self.on_open_symbol_palette, "symbol"
        )
        self.act_table = self._add(
            menu_insert,
            "&Таблица...",
            None,
            self.on_insert_table,
            "table",
            add_to_toolbar=False,
        )
        self.act_reference = self._add(
            menu_insert,
            "Перекрёстная ссылка...",
            "Ctrl+Shift+R",
            self.on_insert_reference,
            "reference",
        )
        self.act_citation = self._add(
            menu_insert,
            "Цитата...",
            "Ctrl+Shift+C",
            self.on_insert_citation,
            "citation",
        )
        self.act_bib_manager = self._add(
            menu_insert,
            "Управление литературой...",
            "Ctrl+Shift+B",
            self.on_open_bib_manager,
            "bib",
        )

    def _create_view_menu(self) -> None:
        menu_view = self.menubar.addMenu("&Вид")
        self.act_light = self._add(
            menu_view, "Светлая тема", None, lambda: self._apply_theme("light"), "light"
        )
        self.act_dark = self._add(
            menu_view, "Тёмная тема", None, lambda: self._apply_theme("dark"), "dark"
        )
        menu_view.addSeparator()
        self.act_zoom_in = self._add(menu_view, "Увеличить", "Ctrl+=", self.zoom_in, "zoom_in")
        self.act_zoom_out = self._add(menu_view, "Уменьшить", "Ctrl+-", self.zoom_out, "zoom_out")
        self.act_zoom_reset = self._add(menu_view, "Масштаб 100%", "Ctrl+0", self.zoom_reset)

    def _create_tools_menu(self) -> None:
        menu_tools = self.menubar.addMenu("&Сервис")
        self.act_stats = self._add(
            menu_tools, "Статистика документа...", "Ctrl+Shift+I", self.on_show_statistics, "stats"
        )
        self.act_bib_tools = self._add(
            menu_tools,
            "Менеджер библиографии...",
            None,
            self.on_open_bib_manager,
            add_to_toolbar=False,
        )

    def _create_help_menu(self) -> None:
        menu_help = self.menubar.addMenu("&Справка")
        self.act_help = self._add(
            menu_help,
            "&Помощь",
            "F1",
            self.on_help,
            add_to_toolbar=False,
        )
        self.act_about = self._add(
            menu_help,
            "&О программе",
            None,
            self.on_about,
            add_to_toolbar=False,
        )

    def _create_format_menu(self) -> None:
        menu_format = self.menubar.addMenu("Фор&мат")
        menu_headings = menu_format.addMenu("Заголовок")
        self.act_heading_normal = self._add(
            menu_headings,
            "Обычный текст",
            "Ctrl+Alt+0",
            lambda: self.editor.set_heading(0),
            add_to_toolbar=False,
        )
        self.act_headings = []
        for level in range(1, 7):
            action = self._add(
                menu_headings,
                f"Заголовок {level}",
                f"Ctrl+Alt+{level}",
                lambda checked=False, value=level: self.editor.set_heading(value),
                f"heading{level}" if level <= 3 else None,
                add_to_toolbar=level <= 3,
            )
            self.act_headings.append(action)
        menu_format.addSeparator()
        self.act_subscript = self._add(
            menu_format,
            "Нижний индекс",
            "Ctrl+,",
            self.editor.make_subscript,
            "subscript",
        )
        self.act_superscript = self._add(
            menu_format,
            "Верхний индекс",
            "Ctrl+.",
            self.editor.make_superscript,
            "superscript",
        )
        menu_format.addSeparator()
        self.act_blockquote = self._add(
            menu_format,
            "Блочная цитата",
            "Ctrl+Shift+Q",
            self.editor.toggle_blockquote,
            "quote",
        )
        menu_env = menu_format.addMenu("Научное окружение")
        for env_name in ("Теорема", "Лемма", "Определение", "Доказательство", "Замечание"):
            action = menu_env.addAction(env_name)
            action.triggered.connect(
                lambda _=False, name=env_name: self.editor.insert_environment(name)
            )
        menu_format.addSeparator()
        self.act_bullet_list = self._add(
            menu_format,
            "Маркированный список",
            "Ctrl+Shift+8",
            self.editor.toggle_bullet_list,
            "bullet_list",
        )
        self.act_number_list = self._add(
            menu_format,
            "Нумерованный список",
            "Ctrl+Shift+7",
            self.editor.toggle_numbered_list,
            "number_list",
        )
        menu_alignment = menu_format.addMenu("Выравнивание")
        self.act_align_left = self._add(
            menu_alignment,
            "По левому краю",
            "Ctrl+L",
            lambda: self.editor.set_alignment(Qt.AlignmentFlag.AlignLeft),
            "align_left",
        )
        self.act_align_center = self._add(
            menu_alignment,
            "По центру",
            "Ctrl+Shift+E",
            lambda: self.editor.set_alignment(Qt.AlignmentFlag.AlignHCenter),
            "align_center",
        )
        self.act_align_right = self._add(
            menu_alignment,
            "По правому краю",
            "Ctrl+R",
            lambda: self.editor.set_alignment(Qt.AlignmentFlag.AlignRight),
            "align_right",
        )
        self.act_align_justify = self._add(
            menu_alignment,
            "По ширине",
            "Ctrl+J",
            lambda: self.editor.set_alignment(Qt.AlignmentFlag.AlignJustify),
            "align_justify",
        )

    def _add(  # noqa: PLR0913
        self,
        menu,
        text: str,
        shortcut: str | None,
        slot,
        glyph: str | None = None,
        *,
        add_to_toolbar: bool = True,
    ) -> QAction:
        action = QAction(text, self)
        if glyph:
            action.setIcon(_make_icon(_GLYPHS.get(glyph, glyph)))
            action.setToolTip(text)
        if shortcut:
            action.setShortcut(QKeySequence(shortcut))
        action.triggered.connect(slot)
        menu.addAction(action)
        if add_to_toolbar:
            self.toolbar.addAction(action)
        return action

    # ---------- Строка состояния (UI) ----------

    def _build_status_bar(self) -> None:
        sb = self.statusBar()
        self._lbl_words = QLabel("Слов: 0")
        self._lbl_formulas = QLabel("Формул: 0")
        self._lbl_cursor = QLabel("Стр:1 Кл:1")
        self._lbl_zoom = QLabel("Зум: 100%")
        self._lbl_pages = QLabel("Страниц: 1")
        self._lbl_encoding = QLabel("UTF-8")
        self._lbl_theme = QLabel("Светлая")
        for label in (
            self._lbl_words,
            self._lbl_formulas,
            self._lbl_cursor,
            self._lbl_zoom,
            self._lbl_pages,
            self._lbl_encoding,
            self._lbl_theme,
        ):
            label.setMargin(4)
            sb.addPermanentWidget(label)

    def _update_status(self) -> None:
        text = self.editor.toPlainText()
        words = len(text.split())
        formulas = len(self.editor.extract_formulas())
        cursor = self.editor.textCursor()
        line = cursor.blockNumber() + 1
        column = cursor.positionInBlock() + 1
        pages = max(1, math.ceil(words / 300))
        theme = self.settings.get("theme", "light")
        self._lbl_words.setText(f"Слов: {words}")
        self._lbl_formulas.setText(f"Формул: {formulas}")
        self._lbl_cursor.setText(f"Стр:{line} Кл:{column}")
        self._lbl_zoom.setText(f"Зум: {self._zoom}%")
        self._lbl_pages.setText(f"Страниц: ~{pages}")
        self._lbl_encoding.setText("UTF-8")
        self._lbl_theme.setText("Светлая" if theme == "light" else "Тёмная")

    # ---------- Масштаб (UI) ----------

    def zoom_in(self) -> None:
        self._zoom = min(300, self._zoom + 10)
        self.editor.set_zoom(self._zoom / 100.0)
        self._update_status()

    def zoom_out(self) -> None:
        self._zoom = max(50, self._zoom - 10)
        self.editor.set_zoom(self._zoom / 100.0)
        self._update_status()

    def zoom_reset(self) -> None:
        self._zoom = 100
        self.editor.set_zoom(1.0)
        self._update_status()

    def eventFilter(self, obj, event) -> bool:
        # Ctrl + колесо мыши — масштабирование редактора
        if (
            obj is self.editor.viewport()
            and event.type() == QEvent.Type.Wheel
            and event.modifiers() & Qt.KeyboardModifier.ControlModifier
        ):
            if event.angleDelta().y() > 0:
                self.zoom_in()
            else:
                self.zoom_out()
            return True
        return super().eventFilter(obj, event)

    # ---------- Тема ----------

    def _apply_theme(self, theme: str) -> None:
        css_file = STYLES_DIR / f"{theme}.qss"
        if css_file.is_file():
            self.setStyleSheet(css_file.read_text(encoding="utf-8"))
        self.settings.set("theme", theme)
        self.settings.save()
        self._update_status()

    # ---------- Навигация (TODO §5.2) ----------

    def _update_navigation(self) -> None:
        self.navigation.set_headings(self.editor.extract_headings())

    # ---------- Поиск и замена (TODO §5.3) ----------

    def _open_find(self, replace_mode: bool) -> None:
        if self._find_dialog is None:
            self._find_dialog = FindReplaceDialog(self.editor, self, replace_mode=replace_mode)
            self._find_dialog.finished.connect(self._on_find_closed)
        self._find_dialog.show()
        self._find_dialog.raise_()
        self._find_dialog.activateWindow()

    def _on_find_closed(self, _code: int) -> None:
        self._find_dialog = None

    # ---------- Live preview (ADR-0014) ----------

    def _schedule_preview(self) -> None:
        self._preview_timer.start()

    def _render_preview(self) -> None:
        self.preview.render_document(self._sync_document_from_editor())

    def document_from_editor(self) -> Document:
        """Совместимый публичный метод: актуальная модель редактора."""
        return self._sync_document_from_editor()

    def _sync_document_from_editor(self) -> Document:
        """Синхронизировать rich-text редактора с единственной моделью документа."""
        self.document = self.editor.to_model(self.document)
        if hasattr(self, "autostore"):
            self.autostore.set_document(self.document, self.current_path)
        return self.document

    # ---------- Действия ----------

    def on_new(self) -> None:
        if not self._confirm_discard_changes():
            return
        self.document = Document.new()
        self.current_path = None
        self.editor.clear()
        self.editor.document().setModified(False)
        self.autostore.set_document(self.document)
        self.setWindowTitle("Scientific Cat — Untitled.sdoc")
        self._logger.info("Создан новый документ")

    def on_new_from_template(self) -> None:
        """Создать новый документ на основе выбранного шаблона."""
        if not self._confirm_discard_changes():
            return
        from ui.template_dialog import TemplateDialog  # noqa: PLC0415

        dialog = TemplateDialog(self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        template_path = dialog.get_selected_template_path()
        if not template_path:
            return
        try:
            self.document = Document.from_file(template_path)
            self.current_path = None
            self.editor.load_model(self.document)
            self.editor.document().setModified(True)
            self.autostore.set_document(self.document)
            self.setWindowTitle(
                f"Scientific Cat — {self.document.title or 'Новый документ'}"
            )
            if not self._headless:
                self._render_preview()
            self._logger.info(f"Создан документ из шаблона: {template_path.name}")
            self.statusBar().showMessage(
                f"Создан документ из шаблона {template_path.name}", 3000
            )
        except Exception as exc:  # noqa: BLE001
            self._show_error("Не удалось создать документ из шаблона", exc)

    def _update_recent_files_menu(self) -> None:
        """Обновить подменю недавних документов."""
        if not hasattr(self, "menu_recent"):
            return
        self.menu_recent.clear()
        recent_files = self.settings.get_recent_files()
        if not recent_files:
            act_empty = self.menu_recent.addAction("Нет недавних файлов")
            act_empty.setEnabled(False)
            return

        for path in recent_files:
            p = Path(path)
            act = self.menu_recent.addAction(f"{p.name} ({p.parent})")
            act.setToolTip(path)
            act.triggered.connect(
                lambda _=False, file_path=path: self._open_recent_file(file_path)
            )

        self.menu_recent.addSeparator()
        self.menu_recent.addAction(
            "Очистить список недавних", self._on_clear_recent_files
        )

    def _open_recent_file(self, path: str) -> None:
        if not self._confirm_discard_changes():
            return
        self._load_document(path)

    def _on_clear_recent_files(self) -> None:
        self.settings.clear_recent_files()
        self._update_recent_files_menu()

    def on_open(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Открыть .sdoc", "", "SDoc (*.sdoc)")
        if not path:
            return
        if not self._confirm_discard_changes():
            return
        self._load_document(path)

    def on_open_md(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Открыть Markdown", "", "Markdown (*.md)")
        if not path:
            return
        if not self._confirm_discard_changes():
            return
        try:
            self.document = md_to_document(Path(path).read_text(encoding="utf-8"))
            self.current_path = None
            self.editor.load_model(self.document)
            self.autostore.set_document(self.document)
            self.setWindowTitle(f"Scientific Cat — {Path(path).name}")
        except (OSError, ValueError) as exc:
            self._show_error("Не удалось открыть Markdown", exc)

    def on_save(self) -> bool:
        if self.current_path:
            return self._save_document(self.current_path)
        return self.on_save_as()

    def on_save_as(self) -> bool:
        path, _ = QFileDialog.getSaveFileName(self, "Сохранить .sdoc", "", "SDoc (*.sdoc)")
        if not path:
            return False
        if not path.lower().endswith(".sdoc"):
            path += ".sdoc"
        if self._save_document(path):
            self.current_path = path
            self.autostore.set_document(self.document, path)
            self.setWindowTitle(f"Scientific Cat — {Path(path).name}")
            return True
        return False

    def _save_document(self, path: str) -> bool:
        try:
            self._sync_document_from_editor().save(path)
        except (OSError, ValueError) as exc:
            self._show_error("Не удалось сохранить документ", exc)
            return False
        self.editor.document().setModified(False)
        self.autostore.discard_recovery()
        self.settings.add_recent_file(path)
        self._update_recent_files_menu()
        self._logger.info(f"Документ сохранён: {path}")
        self.statusBar().showMessage("Документ сохранён", 3000)
        return True

    def on_print(self) -> None:
        """Печать документа на принтере."""
        from PySide6.QtPrintSupport import QPrintDialog, QPrinter  # noqa: PLC0415

        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        dialog = QPrintDialog(printer, self)
        dialog.setWindowTitle("Печать документа")
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.editor.print_(printer)
            self.statusBar().showMessage("Документ отправлен на печать", 3000)

    def on_print_preview(self) -> None:
        """Предварительный просмотр печати."""
        from PySide6.QtPrintSupport import QPrinter, QPrintPreviewDialog  # noqa: PLC0415

        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        preview = QPrintPreviewDialog(printer, self)
        preview.setWindowTitle("Предварительный просмотр печати")
        preview.paintRequested.connect(self.editor.print_)
        preview.exec()

    def on_export(self) -> None:
        from core.exporter import Exporter  # noqa: PLC0415
        from ui.export_dialog import ExportDialog  # noqa: PLC0415

        dialog = ExportDialog(self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        path = dialog.get_path()
        if not path:
            return
        try:
            exporter = Exporter(self._sync_document_from_editor())
            fmt = dialog.get_format()
            dpi = dialog.get_dpi()
            if fmt == "PDF":
                exporter.export_pdf(path, dpi=dpi)
            elif fmt == "DOCX":
                exporter.export_docx(path, dpi=dpi)
            elif fmt == "HTML":
                exporter.export_html(path)
            else:
                exporter.export_latex(path)
        except (OSError, RuntimeError, ValueError) as exc:
            self._show_error("Не удалось экспортировать документ", exc)
            return
        self.statusBar().showMessage("Экспорт завершён", 3000)

    def on_export_md(self) -> None:
        path, _ = QFileDialog.getSaveFileName(self, "Экспорт Markdown", "", "Markdown (*.md)")
        if not path:
            return
        try:
            Path(path).write_text(
                document_to_md(self._sync_document_from_editor()),
                encoding="utf-8",
            )
        except OSError as exc:
            self._show_error("Не удалось экспортировать Markdown", exc)

    def on_import_bib(self) -> None:
        from core.bibliography import BibManager  # noqa: PLC0415

        path, _ = QFileDialog.getOpenFileName(self, "Импорт BibTeX", "", "BibTeX (*.bib)")
        if not path:
            return
        manager = BibManager(bibliography=self.document.bibliography)
        count = manager.import_bibtex(Path(path).read_text(encoding="utf-8"))
        self.statusBar().showMessage(f"Импортировано записей: {count}")
        if not self._headless:
            self._schedule_preview()

    def on_insert_formula(self) -> None:
        from ui.formula_dialog import FormulaDialog  # noqa: PLC0415

        dialog = FormulaDialog(self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        latex = dialog.get_latex()
        if not latex.strip():
            return
        from core.formula import Formula  # noqa: PLC0415

        formula = Formula(latex, formula_type=dialog.get_formula_type())
        self.editor.insert_formula(
            latex,
            number=len(self.editor.extract_formulas()) + 1,
            ftype=dialog.get_formula_type(),
            formula_id=formula.id,
        )
        self._logger.info(f"Вставлена формула: {latex}")

    def on_insert_table(self) -> None:
        """Запросить размер/подпись и вставить таблицу в редактор."""
        rows, accepted = QInputDialog.getInt(
            self,
            "Вставка таблицы",
            "Количество строк:",
            2,
            1,
            100,
        )
        if not accepted:
            return
        columns, accepted = QInputDialog.getInt(
            self,
            "Вставка таблицы",
            "Количество столбцов:",
            2,
            1,
            30,
        )
        if not accepted:
            return
        caption, accepted = QInputDialog.getText(
            self,
            "Вставка таблицы",
            "Подпись (необязательно):",
        )
        if not accepted:
            return
        self.editor.insert_table(rows, columns, caption.strip())
        self.statusBar().showMessage("Таблица вставлена", 3000)

    def on_edit_formula(
        self,
        position: int,
        latex: str,
        formula_type: str,
        _formula_id: str,
        _number: int,
    ) -> None:
        """Открыть редактор существующей формулы по двойному щелчку."""
        from ui.formula_dialog import FormulaDialog  # noqa: PLC0415

        dialog = FormulaDialog(self)
        dialog.setWindowTitle("Изменить формулу")
        dialog.set_formula(latex, formula_type)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        updated_latex = dialog.get_latex().strip()
        if not updated_latex:
            return
        if self.editor.replace_formula_at(
            position,
            updated_latex,
            dialog.get_formula_type(),
        ):
            self.statusBar().showMessage("Формула обновлена", 3000)
            self._logger.info(f"Формула изменена: {updated_latex}")

    def on_insert_reference(self) -> None:
        """Выбрать формулу и вставить стабильную перекрёстную ссылку."""
        self._sync_document_from_editor()
        records = self.editor.extract_formula_records()
        if not records:
            self.statusBar().showMessage("В документе нет формул для ссылки")
            return
        labels = [f"Уравнение ({number}): {latex}" for _, number, latex in records]
        selected, accepted = QInputDialog.getItem(
            self,
            "Перекрёстная ссылка",
            "Формула:",
            labels,
            len(labels) - 1,
            False,
        )
        if not accepted:
            return
        index = labels.index(selected)
        formula_id, number, _latex = records[index]
        self.editor.insert_reference(formula_id, number)
        self.statusBar().showMessage("Вставлена перекрёстная ссылка")
        self._logger.info(f"Вставлена перекрёстная ссылка на формулу {number}")

    def on_insert_citation(self) -> None:
        """Выбрать запись библиографии и вставить связанную цитату."""
        entries = self.document.bibliography.entries
        if not entries:
            self.statusBar().showMessage("Сначала импортируйте файл BibTeX")
            return
        labels = [
            f"[{number}] {entry.author or entry.title or entry.key}"
            for number, entry in enumerate(entries, start=1)
        ]
        selected, accepted = QInputDialog.getItem(
            self,
            "Вставка цитаты",
            "Источник:",
            labels,
            0,
            False,
        )
        if not accepted:
            return
        index = labels.index(selected)
        self.editor.insert_citation(entries[index].key, index + 1)
        self.statusBar().showMessage(f"Вставлена цитата [{index + 1}]")

    def on_open_symbol_palette(self) -> None:
        """Открыть палитру символов для быстрой вставки в текст."""
        if not hasattr(self, "_symbol_dialog") or self._symbol_dialog is None:
            from ui.symbol_palette import SymbolPickerDialog  # noqa: PLC0415

            self._symbol_dialog = SymbolPickerDialog(self)
            self._symbol_dialog.symbolInserted.connect(self.editor.insertPlainText)
        self._symbol_dialog.show()
        self._symbol_dialog.raise_()
        self._symbol_dialog.activateWindow()

    def on_open_bib_manager(self) -> None:
        """Открыть визуальный менеджер библиографии."""
        from ui.bib_dialog import BibManagerDialog  # noqa: PLC0415

        dialog = BibManagerDialog(self.document.bibliography, self)
        dialog.exec()
        if not self._headless:
            self._schedule_preview()
        self._update_status()

    def on_show_statistics(self) -> None:
        """Показать детальную статистику документа."""
        from ui.stats_dialog import DocumentStatsDialog  # noqa: PLC0415

        self._sync_document_from_editor()
        dialog = DocumentStatsDialog(self.editor, self.document, self)
        dialog.exec()

    def on_help(self) -> None:
        from ui.help_dialogs import HelpDialog  # noqa: PLC0415

        HelpDialog(self).exec()

    def on_about(self) -> None:
        from ui.help_dialogs import AboutDialog  # noqa: PLC0415

        AboutDialog(self).exec()

    def _load_document(self, path: str) -> None:
        try:
            document = Document.from_file(path)
        except (OSError, ValueError) as exc:
            self._show_error("Не удалось открыть документ", exc)
            return
        self.document = document
        self.current_path = path
        self.editor.load_model(document)
        self.autostore.set_document(document, path)
        self.settings.add_recent_file(path)
        self._update_recent_files_menu()
        self.setWindowTitle(f"Scientific Cat — {Path(path).name}")
        if not self._headless:
            self._render_preview()
        self._logger.info(f"Документ открыт: {path}")

    def _confirm_discard_changes(self) -> bool:
        """Разрешить разрушительное действие только после Save/Discard."""
        if not self.editor.document().isModified() or self._headless:
            return True
        answer = QMessageBox.warning(
            self,
            "Несохранённые изменения",
            "Документ изменён. Сохранить изменения?",
            QMessageBox.StandardButton.Save
            | QMessageBox.StandardButton.Discard
            | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Save,
        )
        if answer == QMessageBox.StandardButton.Save:
            return self.on_save()
        return answer == QMessageBox.StandardButton.Discard

    def closeEvent(self, event: QCloseEvent) -> None:
        """Не закрывать окно, если пользователь отменил сохранение."""
        if not self._confirm_discard_changes():
            event.ignore()
            return
        self.autostore.stop()
        event.accept()

    def _offer_recovery(self) -> None:
        if self._headless or not self.autostore.has_recovery():
            return
        answer = QMessageBox.question(
            self,
            "Восстановление документа",
            "Найден документ автосохранения. Восстановить его?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes,
        )
        if answer != QMessageBox.StandardButton.Yes:
            self.autostore.discard_recovery()
            return
        try:
            self.document = self.autostore.load_recovery()
            self.current_path = None
            self.editor.load_model(self.document)
            self.autostore.set_document(self.document)
            self.setWindowTitle("Scientific Cat — восстановленный документ")
        except (OSError, ValueError) as exc:
            self.autostore.discard_recovery()
            self._show_error("Не удалось восстановить документ", exc)

    def _show_error(self, title: str, error: Exception) -> None:
        self._logger.error(f"{title}: {error}")
        if not self._headless:
            QMessageBox.critical(self, title, str(error))

    def _on_autosave_error(self, error: Exception) -> None:
        """Сообщить о сбое автосохранения без модального окна."""
        self._logger.error(f"Автосохранение не выполнено: {error}")
        self.statusBar().showMessage(
            "Автосохранение не выполнено — сохраните документ вручную",
            10000,
        )