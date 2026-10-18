"""Виджет текстового редактора (см. FS §4.9, ADR-0001).

Формулы вставляются как inline-объекты (QTextObjectInterface); LaTeX
сохраняется в QTextCharFormat и извлекается без потерь (round-trip).
"""

from __future__ import annotations

import copy
import re
import secrets

from PySide6.QtCore import QPoint, QRectF, QSizeF, Qt, Signal
from PySide6.QtGui import (
    QColor,
    QContextMenuEvent,
    QFont,
    QFontMetricsF,
    QImage,
    QKeyEvent,
    QMouseEvent,
    QPainter,
    QPen,
    QPyTextObject,
    QTextBlockFormat,
    QTextCharFormat,
    QTextCursor,
    QTextDocument,
    QTextFormat,
    QTextListFormat,
    QTextTable,
)
from PySide6.QtWidgets import QMenu, QTextEdit

from core.document import (
    Cell,
    Document,
    ListBlock,
    ListItem,
    Paragraph,
    Row,
    Run,
    Section,
    Table,
)
from core.formula import Formula

FORMULA_OBJECT_TYPE = QTextFormat.UserObject + 1
FORMULA_LATEX_PROP = QTextFormat.UserProperty + 1
FORMULA_TYPE_PROP = QTextFormat.UserProperty + 2
FORMULA_NUMBER_PROP = QTextFormat.UserProperty + 3
HEADING_LEVEL_PROP = QTextFormat.UserProperty + 4
FORMULA_IMAGE_PROP = QTextFormat.UserProperty + 5
FORMULA_ID_PROP = QTextFormat.UserProperty + 6
REFERENCE_TARGET_PROP = QTextFormat.UserProperty + 7
CITATION_KEY_PROP = QTextFormat.UserProperty + 8
MODEL_ID_PROP = QTextFormat.UserProperty + 9
BLOCK_KIND_PROP = QTextFormat.UserProperty + 10
TABLE_CAPTION_PROP = QTextFormat.UserProperty + 11
PARENT_SECTION_PROP = QTextFormat.UserProperty + 12
RUN_STYLE_PROP = QTextFormat.UserProperty + 13
ROOT_SECTION_MARKER = "__document_root__"

# WYSIWYG-рендер формул прямо в редакторе (ADR-0002).
# LaTeX → PNG через matplotlib (опциональный бэкенд); DISPLAY_SCALE приводит
# пиксели к логическим единицам QTextEdit. fontsize/scale подобраны так,
# чтобы формулы отображались крупно и были хорошо видны.
_FORMULA_DPI = 144
_FORMULA_SCALE = _FORMULA_DPI / 120.0
_RENDER_FONTSIZE = 18
_RENDER_CACHE: dict[str, tuple[QImage, QSizeF]] = {}


def _render_latex(latex: str) -> tuple[QImage, QSizeF] | None:
    """LaTeX → QImage + отображаемый размер (с кэшем).

    Возвращает None, если matplotlib недоступен или рендер не удался —
    тогда используется плейсхолдер (см. FormulaObject.drawObject).
    """
    cached = _RENDER_CACHE.get(latex)
    if cached is not None:
        return cached
    try:
        import io  # noqa: PLC0415 - опциональный ленивый импорт

        import matplotlib.pyplot as plt  # noqa: PLC0415 - опциональный бэкенд
    except ImportError:
        return None
    try:
        fig = plt.figure(figsize=(0.01, 0.01), dpi=_FORMULA_DPI)
        fig.patch.set_alpha(0)
        fig.text(
            0,
            0,
            f"${latex}$",
            ha="left",
            va="bottom",
            fontsize=_RENDER_FONTSIZE,
        )
        buf = io.BytesIO()
        fig.savefig(
            buf,
            format="png",
            dpi=_FORMULA_DPI,
            bbox_inches="tight",
            transparent=True,
            pad_inches=0.01,
        )
        plt.close(fig)
        image = QImage.fromData(buf.getvalue())
        if image.isNull():
            return None
        result = (image, QSizeF(image.width() / _FORMULA_SCALE, image.height() / _FORMULA_SCALE))
        _RENDER_CACHE[latex] = result
        return result
    except Exception:  # noqa: BLE001 - любой сбой рендера -> плейсхолдер
        plt.close("all")
        return None


class FormulaObject(QPyTextObject):
    """Отрисовка объекта-формулы и его размера.

    WYSIWYG-рендер (ADR-0002): если в char-формате есть отрендеренное
    изображение — рисуем его; иначе — плейсхолдер с LaTeX-текстом.
    """

    def intrinsicSize(
        self,
        document,
        _position_in_document: int,
        fmt: QTextFormat,
    ) -> QSizeF:
        metrics = QFontMetricsF(document.defaultFont())
        image = fmt.property(FORMULA_IMAGE_PROP)
        number = int(fmt.property(FORMULA_NUMBER_PROP) or 0)
        number_width = metrics.horizontalAdvance(f"({number})") + 10 if number else 0
        if isinstance(image, QImage) and not image.isNull():
            return QSizeF(
                image.width() / _FORMULA_SCALE + number_width + 12,
                max(image.height() / _FORMULA_SCALE + 6, 24),
            )
        latex = fmt.property(FORMULA_LATEX_PROP) or ""
        return QSizeF(
            metrics.horizontalAdvance(str(latex)) + number_width + 20,
            metrics.height() + 6,
        )

    def drawObject(
        self,
        painter: QPainter,
        rect: QRectF,
        _document,
        _position_in_document: int,
        fmt: QTextFormat,
    ) -> None:
        latex = str(fmt.property(FORMULA_LATEX_PROP) or "")
        number = int(fmt.property(FORMULA_NUMBER_PROP) or 0)
        image = fmt.property(FORMULA_IMAGE_PROP)
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setPen(QPen(QColor("#8c959f"), 1))
        painter.setBrush(QColor("#ffffff"))
        painter.drawRoundedRect(rect.adjusted(0.5, 0.5, -0.5, -0.5), 3, 3)

        number_width = painter.fontMetrics().horizontalAdvance(f"({number})") + 6 if number else 0
        content_rect = rect.adjusted(5, 2, -(5 + number_width), -2)
        if isinstance(image, QImage) and not image.isNull():
            target = content_rect.toRect()
            scaled = image.scaled(
                target.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            image_y = target.top() + max(0, (target.height() - scaled.height()) // 2)
            painter.drawImage(target.left(), image_y, scaled)
        else:
            painter.setPen(QColor("#1f2328"))
            painter.drawText(
                content_rect,
                Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
                latex,
            )
        if number:
            painter.setPen(QColor("#57606a"))
            painter.drawText(
                rect.adjusted(5, 2, -5, -2),
                Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight,
                f"({number})",
            )
        painter.restore()


class EditorWidget(QTextEdit):
    """Редактор с поддержкой объектов-формул."""

    formulaEditRequested = Signal(int, str, str, str, int)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setAcceptRichText(True)
        self.setPlaceholderText(
            "Начните вводить текст. Используйте H1-H6 для оглавления и Ctrl+M для формул."
        )
        self._register_formula_object()
        self._base_font_size = self.font().pointSizeF() or 12.0
        self._formula_search_match: tuple[int, str, int, int] | None = None

    def set_zoom(self, factor: float) -> None:
        """Масштаб текста редактора (1.0 = 100%), пересчёт базового шрифта."""
        font = QFont(self.font().family(), self._base_font_size * factor)
        self.setFont(font)

    def _register_formula_object(self) -> None:
        layout = self.document().documentLayout()
        self._formula_handler = FormulaObject(self)
        layout.registerHandler(FORMULA_OBJECT_TYPE, self._formula_handler)

    def _reset_cursor_to_body(self, cursor: QTextCursor) -> None:
        block_fmt = QTextBlockFormat()
        block_fmt.setProperty(HEADING_LEVEL_PROP, 0)
        block_fmt.setAlignment(Qt.AlignmentFlag.AlignLeft)
        cursor.setBlockFormat(block_fmt)

        char_fmt = QTextCharFormat()
        char_fmt.setFontPointSize(self._base_font_size)
        char_fmt.setFontWeight(QFont.Weight.Normal)
        char_fmt.setFontItalic(False)
        char_fmt.setFontUnderline(False)
        char_fmt.setVerticalAlignment(QTextCharFormat.VerticalAlignment.AlignNormal)
        cursor.setCharFormat(char_fmt)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        is_new_paragraph = event.key() in (
            Qt.Key.Key_Return,
            Qt.Key.Key_Enter,
        ) and not (event.modifiers() & Qt.KeyboardModifier.ShiftModifier)
        current_level = int(
            self.textCursor().blockFormat().property(HEADING_LEVEL_PROP) or 0
        )
        super().keyPressEvent(event)
        if is_new_paragraph and current_level:
            cursor = self.textCursor()
            self._reset_cursor_to_body(cursor)
            self.setTextCursor(cursor)

    def insert_formula(
        self,
        latex: str,
        number: int = 0,
        ftype: str = "inline",
        formula_id: str = "",
    ) -> None:
        """Вставка формулы в текущую позицию курсора (с WYSIWYG-рендером)."""
        cursor = self.textCursor()
        if int(cursor.blockFormat().property(HEADING_LEVEL_PROP) or 0):
            cursor.movePosition(QTextCursor.MoveOperation.EndOfBlock)
            cursor.insertBlock()
            self._reset_cursor_to_body(cursor)
        if ftype == "display":
            if cursor.block().text():
                cursor.movePosition(QTextCursor.MoveOperation.EndOfBlock)
                cursor.insertBlock()
                self._reset_cursor_to_body(cursor)
            block_fmt = cursor.blockFormat()
            block_fmt.setProperty(BLOCK_KIND_PROP, "formula")
            block_fmt.setAlignment(Qt.AlignmentFlag.AlignHCenter)
            cursor.setBlockFormat(block_fmt)
        self._insert_formula(cursor, latex, number, ftype, formula_id)
        if ftype == "display":
            cursor.insertBlock()
            self._reset_cursor_to_body(cursor)
        self.setTextCursor(cursor)

    def replace_formula_at(self, position: int, latex: str, ftype: str) -> bool:
        """Заменить формулу в указанной позиции, сохранив ID и номер."""
        formula = self._formula_at(position)
        if formula is None:
            return False
        object_position, fmt = formula
        cursor = QTextCursor(self.document())
        cursor.setPosition(object_position)
        cursor.setPosition(
            object_position + 1,
            QTextCursor.MoveMode.KeepAnchor,
        )
        formula_id = str(fmt.property(FORMULA_ID_PROP) or "")
        number = int(fmt.property(FORMULA_NUMBER_PROP) or 0)
        cursor.removeSelectedText()
        self._insert_formula(cursor, latex, number, ftype, formula_id)
        block = cursor.block()
        if block.text() == "\ufffc":
            block_fmt = cursor.blockFormat()
            block_fmt.setProperty(
                BLOCK_KIND_PROP,
                "formula" if ftype == "display" else "paragraph",
            )
            block_fmt.setAlignment(
                Qt.AlignmentFlag.AlignHCenter
                if ftype == "display"
                else Qt.AlignmentFlag.AlignLeft
            )
            cursor.setBlockFormat(block_fmt)
        self.setTextCursor(cursor)
        return True

    def _formula_at(self, position: int) -> tuple[int, QTextCharFormat] | None:
        for object_position in (position, position - 1):
            if object_position < 0 or object_position >= self.document().characterCount() - 1:
                continue
            cursor = QTextCursor(self.document())
            cursor.setPosition(object_position)
            cursor.setPosition(
                object_position + 1,
                QTextCursor.MoveMode.KeepAnchor,
            )
            fmt = cursor.charFormat()
            if fmt.objectType() == FORMULA_OBJECT_TYPE:
                return object_position, fmt
        return None

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        cursor = self.cursorForPosition(event.position().toPoint())
        formula = self._formula_at(cursor.position())
        if formula is None:
            super().mouseDoubleClickEvent(event)
            return
        position, fmt = formula
        self.formulaEditRequested.emit(
            position,
            str(fmt.property(FORMULA_LATEX_PROP) or ""),
            str(fmt.property(FORMULA_TYPE_PROP) or "inline"),
            str(fmt.property(FORMULA_ID_PROP) or ""),
            int(fmt.property(FORMULA_NUMBER_PROP) or 0),
        )
        event.accept()

    def create_context_menu(self, pos: QPoint | None = None) -> QMenu:
        """Построить контекстное меню: стандартные действия + операции с таблицами и формулами."""
        menu = self.createStandardContextMenu()
        table = self.current_table()
        if table is not None:
            menu.addSeparator()
            table_menu = menu.addMenu("Таблица")
            table_menu.addAction("Добавить строку выше", self.add_table_row_above)
            table_menu.addAction("Добавить строку ниже", self.add_table_row_below)
            act_del_row = table_menu.addAction("Удалить строку", self.remove_table_row)
            act_del_row.setEnabled(table.rows() > 1)
            table_menu.addSeparator()
            table_menu.addAction("Добавить столбец слева", self.add_table_col_left)
            table_menu.addAction("Добавить столбец справа", self.add_table_col_right)
            act_del_col = table_menu.addAction("Удалить столбец", self.remove_table_col)
            act_del_col.setEnabled(table.columns() > 1)
            table_menu.addSeparator()
            table_menu.addAction("Удалить таблицу", self.delete_current_table)

        if pos is not None:
            click_pos = self.cursorForPosition(pos).position()
            formula = self._formula_at(click_pos)
            if formula is not None:
                menu.addSeparator()
                fpos, fmt = formula
                latex = str(fmt.property(FORMULA_LATEX_PROP) or "")
                ftype = str(fmt.property(FORMULA_TYPE_PROP) or "inline")
                fid = str(fmt.property(FORMULA_ID_PROP) or "")
                fnum = int(fmt.property(FORMULA_NUMBER_PROP) or 0)
                menu.addAction(
                    "Изменить формулу...",
                    lambda p=fpos, lx=latex, ft=ftype, fi=fid, fn=fnum: (
                        self.formulaEditRequested.emit(p, lx, ft, fi, fn)
                    ),
                )
        return menu

    def contextMenuEvent(self, event: QContextMenuEvent) -> None:
        """Отобразить контекстное меню."""
        menu = self.create_context_menu(event.pos())
        menu.exec(event.globalPos())

    def _insert_formula(
        self,
        cursor: QTextCursor,
        latex: str,
        number: int = 0,
        ftype: str = "inline",
        formula_id: str = "",
    ) -> None:
        """Вставить формулу указанным курсором."""
        fmt = QTextCharFormat()
        fmt.setObjectType(FORMULA_OBJECT_TYPE)
        fmt.setProperty(FORMULA_LATEX_PROP, latex)
        fmt.setProperty(FORMULA_TYPE_PROP, ftype)
        fmt.setProperty(FORMULA_NUMBER_PROP, number)
        fmt.setProperty(FORMULA_ID_PROP, formula_id)
        rendered = _render_latex(latex)
        if rendered is not None:
            fmt.setProperty(FORMULA_IMAGE_PROP, rendered[0])
        cursor.insertText("\ufffc", fmt)

    def insert_reference(self, target_id: str, number: int) -> None:
        """Вставить стабильную ссылку на формулу."""
        fmt = QTextCharFormat()
        fmt.setProperty(REFERENCE_TARGET_PROP, target_id)
        cursor = self.textCursor()
        cursor.insertText(f"см. уравнение ({number})", fmt)
        self.setTextCursor(cursor)

    def insert_citation(self, citation_key: str, number: int) -> None:
        """Вставить цитату, связанную с ключом BibTeX."""
        fmt = QTextCharFormat()
        fmt.setProperty(CITATION_KEY_PROP, citation_key)
        cursor = self.textCursor()
        cursor.insertText(f"[{number}]", fmt)
        self.setTextCursor(cursor)

    def insert_table(self, rows: int, columns: int, caption: str = "") -> None:
        """Вставить редактируемую таблицу и сохранить её метаданные."""
        rows = max(1, rows)
        columns = max(1, columns)
        cursor = self.textCursor()
        current_block_fmt = cursor.blockFormat()
        parent_section = str(current_block_fmt.property(PARENT_SECTION_PROP) or "")
        heading_level = int(current_block_fmt.property(HEADING_LEVEL_PROP) or 0)
        if heading_level:
            parent_section = str(current_block_fmt.property(MODEL_ID_PROP) or "")
        current_table = cursor.currentTable()
        if current_table is not None:
            cursor.setPosition(current_table.lastCursorPosition().position())
            cursor.movePosition(QTextCursor.MoveOperation.NextBlock)
        elif cursor.block().text():
            cursor.movePosition(QTextCursor.MoveOperation.EndOfBlock)
            cursor.insertBlock()
            self._reset_cursor_to_body(cursor)

        table = cursor.insertTable(rows, columns)
        table_fmt = table.format()
        table_fmt.setProperty(MODEL_ID_PROP, f"tbl{secrets.token_hex(4)}")
        table_fmt.setProperty(TABLE_CAPTION_PROP, caption)
        if parent_section:
            table_fmt.setProperty(PARENT_SECTION_PROP, parent_section)
        table_fmt.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        table.setFormat(table_fmt)
        self.setTextCursor(table.cellAt(0, 0).firstCursorPosition())

    def current_table(self) -> QTextTable | None:
        """Вернуть текущую таблицу под курсором или None."""
        return self.textCursor().currentTable()

    def add_table_row_above(self) -> bool:
        """Добавить строку выше текущей ячейки."""
        table = self.current_table()
        if table is None:
            return False
        cell = table.cellAt(self.textCursor())
        row = cell.row()
        table.insertRows(row, 1)
        return True

    def add_table_row_below(self) -> bool:
        """Добавить строку ниже текущей ячейки."""
        table = self.current_table()
        if table is None:
            return False
        cell = table.cellAt(self.textCursor())
        row = cell.row()
        table.insertRows(row + 1, 1)
        return True

    def remove_table_row(self) -> bool:
        """Удалить текущую строку таблицы."""
        table = self.current_table()
        if table is None or table.rows() <= 1:
            return False
        cell = table.cellAt(self.textCursor())
        table.removeRows(cell.row(), 1)
        return True

    def add_table_col_left(self) -> bool:
        """Добавить столбец слева от текущей ячейки."""
        table = self.current_table()
        if table is None:
            return False
        cell = table.cellAt(self.textCursor())
        col = cell.column()
        table.insertColumns(col, 1)
        return True

    def add_table_col_right(self) -> bool:
        """Добавить столбец справа от текущей ячейки."""
        table = self.current_table()
        if table is None:
            return False
        cell = table.cellAt(self.textCursor())
        col = cell.column()
        table.insertColumns(col + 1, 1)
        return True

    def remove_table_col(self) -> bool:
        """Удалить текущий столбец таблицы."""
        table = self.current_table()
        if table is None or table.columns() <= 1:
            return False
        cell = table.cellAt(self.textCursor())
        table.removeColumns(cell.column(), 1)
        return True

    def delete_current_table(self) -> bool:
        """Удалить текущую таблицу целиком."""
        table = self.current_table()
        if table is None:
            return False
        start = table.firstPosition() - 1
        end = table.lastPosition() + 1
        cur = self.textCursor()
        cur.setPosition(max(0, start))
        cur.setPosition(
            min(self.document().characterCount() - 1, end),
            QTextCursor.MoveMode.KeepAnchor,
        )
        cur.removeSelectedText()
        return True

    def toggle_blockquote(self) -> None:
        """Переключить оформление текущего абзаца как блочной цитаты."""
        cursor = self.textCursor()
        block_fmt = cursor.blockFormat()
        current_indent = block_fmt.indent()
        if current_indent > 0:
            block_fmt.setIndent(0)
            block_fmt.setLeftMargin(0)
            block_fmt.setProperty(RUN_STYLE_PROP, "Body")
        else:
            block_fmt.setIndent(1)
            block_fmt.setLeftMargin(28)
            block_fmt.setProperty(RUN_STYLE_PROP, "Quote")
        cursor.setBlockFormat(block_fmt)

    def insert_environment(self, env_type: str = "Теорема", title: str = "") -> None:
        """Вставить научное окружение (Теорема, Лемма, Определение, Доказательство и др.)."""
        cursor = self.textCursor()
        if cursor.block().text().strip():
            cursor.movePosition(QTextCursor.MoveOperation.EndOfBlock)
            cursor.insertBlock()
        header = f"[{env_type.upper()}" + (f" ({title})" if title else "") + "]"
        block_fmt = QTextBlockFormat()
        block_fmt.setLeftMargin(20)
        block_fmt.setProperty(RUN_STYLE_PROP, f"Env_{env_type}")
        cursor.setBlockFormat(block_fmt)

        char_fmt = QTextCharFormat()
        char_fmt.setFontWeight(QFont.Weight.Bold)
        cursor.insertText(header + " ", char_fmt)

        body_fmt = QTextCharFormat()
        body_fmt.setFontItalic(env_type.lower() != "доказательство")
        cursor.insertText("Текст утверждения...", body_fmt)

    def find_content(
        self,
        text: str,
        flags: QTextDocument.FindFlag | None = None,
    ) -> bool:
        """Найти обычный текст или LaTeX внутри формулы по порядку документа."""
        if not text:
            return False
        if flags is None:
            flags = QTextDocument.FindFlag(0)
        self._formula_search_match = None
        start_position = self.textCursor().selectionEnd()
        text_match = self.document().find(text, start_position, flags)
        text_position = (
            text_match.selectionStart()
            if not text_match.isNull()
            else self.document().characterCount()
        )
        case_sensitive = bool(flags & QTextDocument.FindFlag.FindCaseSensitively)
        needle = text if case_sensitive else text.casefold()
        formula_match: tuple[int, str, int, int] | None = None

        block = self.document().findBlock(start_position)
        while block.isValid() and formula_match is None:
            fragment_it = block.begin()
            while not fragment_it.atEnd():
                fragment = fragment_it.fragment()
                fmt = fragment.charFormat()
                if (
                    fragment.position() >= start_position
                    and fmt.objectType() == FORMULA_OBJECT_TYPE
                ):
                    latex = str(fmt.property(FORMULA_LATEX_PROP) or "")
                    haystack = latex if case_sensitive else latex.casefold()
                    match_start = haystack.find(needle)
                    if match_start >= 0:
                        formula_match = (
                            fragment.position(),
                            text,
                            match_start,
                            len(text),
                        )
                        break
                fragment_it += 1
            block = block.next()

        if formula_match is not None and formula_match[0] <= text_position:
            position = formula_match[0]
            cursor = QTextCursor(self.document())
            cursor.setPosition(position)
            cursor.setPosition(position + 1, QTextCursor.MoveMode.KeepAnchor)
            self.setTextCursor(cursor)
            self.ensureCursorVisible()
            self._formula_search_match = formula_match
            return True
        if not text_match.isNull():
            self.setTextCursor(text_match)
            self.ensureCursorVisible()
            return True
        return False

    def replace_formula_search_match(
        self,
        replacement: str,
        *,
        all_occurrences: bool = False,
        case_sensitive: bool = False,
    ) -> int:
        """Заменить найденный LaTeX-фрагмент, не разрушая объект формулы."""
        match = self._formula_search_match
        if match is None:
            return 0
        position, query, match_start, match_length = match
        formula = self._formula_at(position)
        self._formula_search_match = None
        if formula is None:
            return 0
        _, fmt = formula
        latex = str(fmt.property(FORMULA_LATEX_PROP) or "")
        if all_occurrences:
            expression = re.compile(
                re.escape(query),
                0 if case_sensitive else re.IGNORECASE,
            )
            updated, count = expression.subn(lambda _match: replacement, latex)
        else:
            updated = latex[:match_start] + replacement + latex[match_start + match_length :]
            count = 1
        if count and self.replace_formula_at(
            position,
            updated,
            str(fmt.property(FORMULA_TYPE_PROP) or "inline"),
        ):
            return count
        return 0

    def extract_formula_records(self) -> list[tuple[str, int, str]]:
        """Вернуть формулы как (id, номер, LaTeX) в порядке документа."""
        records: list[tuple[str, int, str]] = []
        block = self.document().begin()
        while block.isValid():
            fragment_it = block.begin()
            while not fragment_it.atEnd():
                fragment = fragment_it.fragment()
                fmt = fragment.charFormat()
                if fmt.objectType() == FORMULA_OBJECT_TYPE:
                    records.append(
                        (
                            str(fmt.property(FORMULA_ID_PROP) or ""),
                            int(fmt.property(FORMULA_NUMBER_PROP) or 0),
                            str(fmt.property(FORMULA_LATEX_PROP) or ""),
                        )
                    )
                fragment_it += 1
            block = block.next()
        return records

    def renumber_inline_objects(  # noqa: PLR0915
        self,
        citation_numbers: dict[str, int] | None = None,
    ) -> None:
        """Обновить номера формул, перекрёстных ссылок и цитат."""
        formulas: list[tuple[int, int, QTextCharFormat, str, int]] = []
        formula_numbers: dict[str, int] = {}
        block = self.document().begin()
        number = 0
        while block.isValid():
            fragment_it = block.begin()
            while not fragment_it.atEnd():
                fragment = fragment_it.fragment()
                fmt = fragment.charFormat()
                if fmt.objectType() == FORMULA_OBJECT_TYPE:
                    number += 1
                    formula_id = str(fmt.property(FORMULA_ID_PROP) or "")
                    if not formula_id:
                        formula_id = Formula("").id
                    formula_numbers[formula_id] = number
                    formulas.append(
                        (fragment.position(), fragment.length(), fmt, formula_id, number)
                    )
                fragment_it += 1
            block = block.next()

        for position, length, old_fmt, formula_id, formula_number in formulas:
            if (
                old_fmt.property(FORMULA_ID_PROP) == formula_id
                and old_fmt.property(FORMULA_NUMBER_PROP) == formula_number
            ):
                continue
            fmt = QTextCharFormat(old_fmt)
            fmt.setProperty(FORMULA_ID_PROP, formula_id)
            fmt.setProperty(FORMULA_NUMBER_PROP, formula_number)
            cursor = QTextCursor(self.document())
            cursor.setPosition(position)
            cursor.setPosition(
                position + length,
                QTextCursor.MoveMode.KeepAnchor,
            )
            cursor.setCharFormat(fmt)

        replacements: list[tuple[int, int, str, QTextCharFormat]] = []
        block = self.document().begin()
        while block.isValid():
            fragment_it = block.begin()
            while not fragment_it.atEnd():
                fragment = fragment_it.fragment()
                fmt = fragment.charFormat()
                target = str(fmt.property(REFERENCE_TARGET_PROP) or "")
                citation_key = str(fmt.property(CITATION_KEY_PROP) or "")
                replacement = ""
                if target:
                    target_number = formula_numbers.get(target)
                    label = str(target_number) if target_number is not None else "???"
                    replacement = f"см. уравнение ({label})"
                elif citation_key:
                    citation_number = (citation_numbers or {}).get(citation_key)
                    label = str(citation_number) if citation_number is not None else "?"
                    replacement = f"[{label}]"
                if replacement and replacement != fragment.text():
                    replacements.append(
                        (fragment.position(), fragment.length(), replacement, fmt)
                    )
                fragment_it += 1
            block = block.next()

        for position, length, replacement, fmt in reversed(replacements):
            cursor = QTextCursor(self.document())
            cursor.setPosition(position)
            cursor.setPosition(
                position + length,
                QTextCursor.MoveMode.KeepAnchor,
            )
            cursor.insertText(replacement, fmt)

    # ---------- Синхронизация с моделью Document ----------

    def to_model(  # noqa: PLR0912, PLR0915
        self, base_document: Document | None = None
    ) -> Document:
        """Собрать Document из фактического rich-text содержимого редактора."""
        citation_numbers = {
            entry.key: number
            for number, entry in enumerate(
                base_document.bibliography.entries if base_document else [],
                start=1,
            )
        }
        self.renumber_inline_objects(citation_numbers)
        model = copy.deepcopy(base_document) if base_document is not None else Document.new()
        model.body = []
        paragraph_number = 0
        section_number = 0
        list_number = 0
        table_number = 0
        active_list_index = -1
        active_list: ListBlock | None = None
        section_stack: list[Section] = []
        sections_by_id: dict[str, Section] = {}
        used_ids: set[str] = set()

        def model_id(fmt: QTextFormat, prefix: str, sequence: int) -> str:
            stored = str(fmt.property(MODEL_ID_PROP) or "")
            if stored and stored not in used_ids:
                used_ids.add(stored)
                return stored
            suffix = sequence
            candidate = f"{prefix}{suffix:04d}"
            while candidate in used_ids:
                suffix += 1
                candidate = f"{prefix}{suffix:04d}"
            used_ids.add(candidate)
            fmt.setProperty(MODEL_ID_PROP, candidate)
            return candidate

        def append_block(
            model_block,
            parent_id: str = "",
            *,
            has_parent_metadata: bool = False,
        ) -> None:
            nonlocal section_stack
            explicit_parent = sections_by_id.get(parent_id)
            if isinstance(model_block, Section):
                if has_parent_metadata:
                    target = explicit_parent.children if explicit_parent else model.body
                else:
                    while section_stack and section_stack[-1].level >= model_block.level:
                        section_stack.pop()
                    target = section_stack[-1].children if section_stack else model.body
                target.append(model_block)
                sections_by_id[model_block.id] = model_block
                while section_stack and section_stack[-1].level >= model_block.level:
                    section_stack.pop()
                section_stack.append(model_block)
                return
            if has_parent_metadata:
                target = explicit_parent.children if explicit_parent else model.body
            else:
                target = section_stack[-1].children if section_stack else model.body
            target.append(model_block)

        block = self.document().begin()
        while block.isValid():
            qt_table = QTextCursor(block).currentTable()
            if qt_table is not None:
                active_list = None
                active_list_index = -1
                table_number += 1
                table_fmt = qt_table.format()
                table_id = model_id(table_fmt, "tbl", table_number)
                qt_table.setFormat(table_fmt)
                table = Table(
                    id=table_id,
                    cols=qt_table.columns(),
                    rows=qt_table.rows(),
                    caption=str(table_fmt.property(TABLE_CAPTION_PROP) or ""),
                    align=self._alignment_name(table_fmt.alignment()),
                )
                for row_number in range(qt_table.rows()):
                    row = Row()
                    for column_number in range(qt_table.columns()):
                        qt_cell = qt_table.cellAt(row_number, column_number)
                        cell = Cell()
                        cell_block = qt_cell.firstCursorPosition().block()
                        cell_end = qt_cell.lastCursorPosition().position()
                        while cell_block.isValid() and cell_block.position() < cell_end:
                            fragment_it = cell_block.begin()
                            while not fragment_it.atEnd():
                                fragment = fragment_it.fragment()
                                fmt = fragment.charFormat()
                                if fmt.objectType() == FORMULA_OBJECT_TYPE:
                                    formula = self._formula_from_format(fmt)
                                    cell.formulas.append(formula)
                                    cell.content.append(formula)
                                elif fragment.text():
                                    run = self._run_from_fragment(fragment)
                                    cell.runs.append(run)
                                    cell.content.append(run)
                                fragment_it += 1
                            cell_block = cell_block.next()
                        row.cells.append(cell)
                    table.rows_data.append(row)
                append_block(
                    table,
                    str(table_fmt.property(PARENT_SECTION_PROP) or ""),
                    has_parent_metadata=table_fmt.hasProperty(PARENT_SECTION_PROP),
                )
                table_index = qt_table.objectIndex()
                block = block.next()
                while block.isValid():
                    current_table = QTextCursor(block).currentTable()
                    if current_table is None or current_table.objectIndex() != table_index:
                        break
                    block = block.next()
                continue

            text_list = block.textList()
            if text_list is not None:
                object_index = text_list.objectIndex()
                if active_list is None or active_list_index != object_index:
                    list_number += 1
                    list_fmt = text_list.format()
                    style = list_fmt.style()
                    list_id = model_id(list_fmt, "list", list_number)
                    text_list.setFormat(list_fmt)
                    active_list = ListBlock(
                        id=list_id,
                        list_type=(
                            "ordered"
                            if style
                            in (
                                QTextListFormat.Style.ListDecimal,
                                QTextListFormat.Style.ListLowerAlpha,
                                QTextListFormat.Style.ListUpperAlpha,
                            )
                            else "unordered"
                        ),
                    )
                    append_block(
                        active_list,
                        str(list_fmt.property(PARENT_SECTION_PROP) or ""),
                        has_parent_metadata=list_fmt.hasProperty(PARENT_SECTION_PROP),
                    )
                    active_list_index = object_index
                active_list.items.append(ListItem(text=block.text()))
                block = block.next()
                continue

            active_list = None
            active_list_index = -1
            level = int(block.blockFormat().property(HEADING_LEVEL_PROP) or 0)
            if 1 <= level <= 6:
                section_number += 1
                block_fmt = block.blockFormat()
                section_id = model_id(block_fmt, "sec", section_number)
                QTextCursor(block).setBlockFormat(block_fmt)
                append_block(
                    Section(
                        id=section_id,
                        heading=self._block_semantic_text(block),
                        level=level,
                    ),
                    str(block_fmt.property(PARENT_SECTION_PROP) or ""),
                    has_parent_metadata=block_fmt.hasProperty(PARENT_SECTION_PROP),
                )
                block = block.next()
                continue

            block_kind = str(block.blockFormat().property(BLOCK_KIND_PROP) or "")
            text_without_objects = block.text().replace("\ufffc", "").strip()
            if block_kind == "formula" and not text_without_objects:
                fragment_it = block.begin()
                while not fragment_it.atEnd():
                    fragment = fragment_it.fragment()
                    fmt = fragment.charFormat()
                    if fmt.objectType() == FORMULA_OBJECT_TYPE:
                        append_block(
                            self._formula_from_format(fmt),
                            str(
                                block.blockFormat().property(PARENT_SECTION_PROP)
                                or ""
                            ),
                            has_parent_metadata=block.blockFormat().hasProperty(
                                PARENT_SECTION_PROP
                            ),
                        )
                    fragment_it += 1
                block = block.next()
                continue

            paragraph_number += 1
            block_fmt = block.blockFormat()
            paragraph_id = model_id(block_fmt, "p", paragraph_number)
            QTextCursor(block).setBlockFormat(block_fmt)
            paragraph = Paragraph(
                id=paragraph_id,
                align=self._alignment_name(block_fmt.alignment()),
            )
            fragment_it = block.begin()
            while not fragment_it.atEnd():
                fragment = fragment_it.fragment()
                fmt = fragment.charFormat()
                if fmt.objectType() == FORMULA_OBJECT_TYPE:
                    formula = self._formula_from_format(fmt)
                    paragraph.formulas.append(formula)
                    paragraph.content.append(formula)
                elif fragment.text():
                    run = self._run_from_fragment(fragment)
                    paragraph.runs.append(run)
                    paragraph.content.append(run)
                fragment_it += 1
            if paragraph.content or block.text():
                append_block(
                    paragraph,
                    str(block.blockFormat().property(PARENT_SECTION_PROP) or ""),
                    has_parent_metadata=block.blockFormat().hasProperty(
                        PARENT_SECTION_PROP
                    ),
                )
            block = block.next()
        from core.references import ReferenceResolver  # noqa: PLC0415

        resolver = ReferenceResolver(model)
        resolver.number_sections()
        resolver.number_formulas()
        return model

    @staticmethod
    def _formula_from_format(fmt: QTextCharFormat) -> Formula:
        return Formula(
            latex=str(fmt.property(FORMULA_LATEX_PROP) or ""),
            formula_type=(
                "display" if fmt.property(FORMULA_TYPE_PROP) == "display" else "inline"
            ),
            number=int(fmt.property(FORMULA_NUMBER_PROP) or 0),
            formula_id=str(fmt.property(FORMULA_ID_PROP) or "") or None,
        )

    @staticmethod
    def _run_from_fragment(fragment) -> Run:
        fmt = fragment.charFormat()
        has_vertical_alignment = fmt.hasProperty(
            QTextFormat.Property.TextVerticalAlignment
        )
        return Run(
            text=fragment.text(),
            style=str(fmt.property(RUN_STYLE_PROP) or "Body"),
            bold=(
                fmt.fontWeight() >= QFont.Weight.Bold
                if fmt.hasProperty(QTextFormat.Property.FontWeight)
                else None
            ),
            italic=(
                fmt.fontItalic()
                if fmt.hasProperty(QTextFormat.Property.FontItalic)
                else None
            ),
            underline=(
                fmt.fontUnderline()
                if fmt.hasProperty(QTextFormat.Property.FontUnderline)
                else None
            ),
            subscript=(
                fmt.verticalAlignment()
                == QTextCharFormat.VerticalAlignment.AlignSubScript
                if has_vertical_alignment
                else None
            ),
            superscript=(
                fmt.verticalAlignment()
                == QTextCharFormat.VerticalAlignment.AlignSuperScript
                if has_vertical_alignment
                else None
            ),
            reference_target=str(fmt.property(REFERENCE_TARGET_PROP) or "") or None,
            citation_key=str(fmt.property(CITATION_KEY_PROP) or "") or None,
        )

    @staticmethod
    def _insert_run(cursor: QTextCursor, item: Run) -> None:
        """Вставить Run, сохранив tri-state форматирование и связи."""
        fmt = QTextCharFormat()
        fmt.setProperty(RUN_STYLE_PROP, item.style)
        if item.bold is not None:
            fmt.setFontWeight(QFont.Weight.Bold if item.bold else QFont.Weight.Normal)
        if item.italic is not None:
            fmt.setFontItalic(item.italic)
        if item.underline is not None:
            fmt.setFontUnderline(item.underline)
        if item.subscript is not None or item.superscript is not None:
            if item.subscript:
                vertical = QTextCharFormat.VerticalAlignment.AlignSubScript
            elif item.superscript:
                vertical = QTextCharFormat.VerticalAlignment.AlignSuperScript
            else:
                vertical = QTextCharFormat.VerticalAlignment.AlignNormal
            fmt.setVerticalAlignment(vertical)
        if item.reference_target:
            fmt.setProperty(REFERENCE_TARGET_PROP, item.reference_target)
        if item.citation_key:
            fmt.setProperty(CITATION_KEY_PROP, item.citation_key)
        cursor.insertText(item.text, fmt)

    def load_model(self, model: Document) -> None:  # noqa: PLR0915
        """Отобразить Document в редакторе без потери текста и формул."""
        self.clear()
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.Start)
        first_block = True

        def begin_block() -> None:
            nonlocal first_block
            if first_block:
                first_block = False
            else:
                cursor.insertBlock()
            self._reset_cursor_to_body(cursor)

        def render_block(  # noqa: PLR0912, PLR0915
            block,
            parent_section_id: str = "",
        ) -> None:
            if isinstance(block, Section):
                begin_block()
                block_fmt = QTextBlockFormat()
                block_fmt.setProperty(HEADING_LEVEL_PROP, block.level)
                block_fmt.setProperty(MODEL_ID_PROP, block.id)
                block_fmt.setProperty(BLOCK_KIND_PROP, "section")
                block_fmt.setProperty(
                    PARENT_SECTION_PROP,
                    parent_section_id or ROOT_SECTION_MARKER,
                )
                cursor.mergeBlockFormat(block_fmt)
                heading_fmt = QTextCharFormat()
                heading_fmt.setFontPointSize(max(12, 20 - block.level * 2))
                heading_fmt.setFontWeight(QFont.Weight.Bold)
                cursor.insertText(block.heading, heading_fmt)
                for child in block.children:
                    render_block(child, block.id)
                return
            if isinstance(block, Paragraph):
                begin_block()
                block_fmt = QTextBlockFormat()
                block_fmt.setAlignment(self._qt_alignment(block.align))
                block_fmt.setProperty(MODEL_ID_PROP, block.id)
                block_fmt.setProperty(BLOCK_KIND_PROP, "paragraph")
                block_fmt.setProperty(
                    PARENT_SECTION_PROP,
                    parent_section_id or ROOT_SECTION_MARKER,
                )
                cursor.mergeBlockFormat(block_fmt)
                for item in block.inline_content():
                    if isinstance(item, Run):
                        self._insert_run(cursor, item)
                    else:
                        self._insert_formula(
                            cursor,
                            item.latex,
                            item.number,
                            item.type,
                            item.id,
                        )
                return
            if isinstance(block, Formula):
                begin_block()
                block_fmt = QTextBlockFormat()
                block_fmt.setAlignment(Qt.AlignmentFlag.AlignHCenter)
                block_fmt.setProperty(MODEL_ID_PROP, block.id)
                block_fmt.setProperty(BLOCK_KIND_PROP, "formula")
                block_fmt.setProperty(
                    PARENT_SECTION_PROP,
                    parent_section_id or ROOT_SECTION_MARKER,
                )
                cursor.mergeBlockFormat(block_fmt)
                self._insert_formula(cursor, block.latex, block.number, block.type, block.id)
                return
            if isinstance(block, ListBlock):
                qt_list = None
                for item in block.items:
                    begin_block()
                    cursor.insertText(item.text)
                    if qt_list is None:
                        list_fmt = QTextListFormat()
                        list_fmt.setStyle(
                            QTextListFormat.Style.ListDecimal
                            if block.list_type == "ordered"
                            else QTextListFormat.Style.ListDisc
                        )
                        list_fmt.setProperty(MODEL_ID_PROP, block.id)
                        list_fmt.setProperty(
                            PARENT_SECTION_PROP,
                            parent_section_id or ROOT_SECTION_MARKER,
                        )
                        qt_list = cursor.createList(list_fmt)
                    else:
                        qt_list.add(cursor.block())
                return
            if isinstance(block, Table):
                begin_block()
                rows = max(block.rows, len(block.rows_data), 1)
                columns = max(block.cols, 1)
                qt_table = cursor.insertTable(rows, columns)
                table_fmt = qt_table.format()
                table_fmt.setProperty(MODEL_ID_PROP, block.id)
                table_fmt.setProperty(TABLE_CAPTION_PROP, block.caption)
                table_fmt.setProperty(
                    PARENT_SECTION_PROP,
                    parent_section_id or ROOT_SECTION_MARKER,
                )
                table_fmt.setAlignment(self._qt_alignment(block.align))
                qt_table.setFormat(table_fmt)
                for row_number, row in enumerate(block.rows_data[:rows]):
                    for column_number, cell in enumerate(row.cells[:columns]):
                        cell_cursor = qt_table.cellAt(
                            row_number, column_number
                        ).firstCursorPosition()
                        for item in cell.inline_content():
                            if isinstance(item, Run):
                                self._insert_run(cell_cursor, item)
                            else:
                                self._insert_formula(
                                    cell_cursor,
                                    item.latex,
                                    item.number,
                                    item.type,
                                    item.id,
                                )
                cursor.setPosition(qt_table.lastCursorPosition().position())
                cursor.movePosition(QTextCursor.MoveOperation.NextBlock)

        cursor.beginEditBlock()
        for body_block in model.body:
            render_block(body_block)
        cursor.endEditBlock()
        self.setTextCursor(cursor)
        self.document().setModified(False)

    @staticmethod
    def _alignment_name(alignment: Qt.AlignmentFlag) -> str:
        if alignment & Qt.AlignmentFlag.AlignHCenter:
            return "center"
        if alignment & Qt.AlignmentFlag.AlignRight:
            return "right"
        if alignment & Qt.AlignmentFlag.AlignJustify:
            return "justify"
        return "left"

    @staticmethod
    def _qt_alignment(alignment: str) -> Qt.AlignmentFlag:
        return {
            "center": Qt.AlignmentFlag.AlignHCenter,
            "right": Qt.AlignmentFlag.AlignRight,
            "justify": Qt.AlignmentFlag.AlignJustify,
        }.get(alignment, Qt.AlignmentFlag.AlignLeft)

    @staticmethod
    def _block_semantic_text(block) -> str:
        """Текст блока без служебного символа OBJ; формулы показаны как LaTeX."""
        parts: list[str] = []
        fragment_it = block.begin()
        while not fragment_it.atEnd():
            fragment = fragment_it.fragment()
            fmt = fragment.charFormat()
            if fmt.objectType() == FORMULA_OBJECT_TYPE:
                parts.append(f"⟨{fmt.property(FORMULA_LATEX_PROP) or 'формула'}⟩")
            else:
                parts.append(fragment.text().replace("\ufffc", ""))
            fragment_it += 1
        return "".join(parts)

    # ---------- Форматирование (TZ Т-01..Т-05) ----------

    def _toggle_char_format(self, prop, value, normal) -> None:
        fmt = QTextCharFormat()
        current = self.currentCharFormat().property(prop)
        fmt.setProperty(prop, normal if current == value else value)
        self.mergeCurrentCharFormat(fmt)

    def make_bold(self) -> None:
        cur = self.currentCharFormat().fontWeight()
        target = QFont.Weight.Normal if cur == QFont.Weight.Bold else QFont.Weight.Bold
        fmt = QTextCharFormat()
        fmt.setFontWeight(target)
        self.mergeCurrentCharFormat(fmt)

    def make_italic(self) -> None:
        fmt = QTextCharFormat()
        fmt.setFontItalic(not self.currentCharFormat().fontItalic())
        self.mergeCurrentCharFormat(fmt)

    def make_underline(self) -> None:
        fmt = QTextCharFormat()
        fmt.setFontUnderline(not self.currentCharFormat().fontUnderline())
        self.mergeCurrentCharFormat(fmt)

    def make_subscript(self) -> None:
        fmt = QTextCharFormat()
        current = self.currentCharFormat().verticalAlignment()
        fmt.setVerticalAlignment(
            QTextCharFormat.VerticalAlignment.AlignNormal
            if current == QTextCharFormat.VerticalAlignment.AlignSubScript
            else QTextCharFormat.VerticalAlignment.AlignSubScript
        )
        self.mergeCurrentCharFormat(fmt)

    def make_superscript(self) -> None:
        fmt = QTextCharFormat()
        current = self.currentCharFormat().verticalAlignment()
        fmt.setVerticalAlignment(
            QTextCharFormat.VerticalAlignment.AlignNormal
            if current == QTextCharFormat.VerticalAlignment.AlignSuperScript
            else QTextCharFormat.VerticalAlignment.AlignSuperScript
        )
        self.mergeCurrentCharFormat(fmt)

    def set_heading(self, level: int) -> None:
        """Переключить H1-H6 для выбранных блоков; 0 означает обычный текст."""
        cursor = self.textCursor()
        current_level = int(cursor.blockFormat().property(HEADING_LEVEL_PROP) or 0)
        target_level = 0 if level == current_level else level
        if not 1 <= target_level <= 6:
            target_level = 0

        block_fmt = QTextBlockFormat()
        block_fmt.setProperty(HEADING_LEVEL_PROP, target_level)
        cursor.mergeBlockFormat(block_fmt)

        char_fmt = QTextCharFormat()
        if target_level:
            size = max(12, 20 - target_level * 2)
            char_fmt.setFontPointSize(size)
            char_fmt.setFontWeight(QFont.Weight.Bold)
        else:
            char_fmt.setFontPointSize(self._base_font_size)
            char_fmt.setFontWeight(QFont.Weight.Normal)

        text_cursor = QTextCursor(cursor)
        if not text_cursor.hasSelection():
            text_cursor.select(QTextCursor.SelectionType.BlockUnderCursor)
        text_cursor.mergeCharFormat(char_fmt)
        self.setTextCursor(cursor)

    def set_alignment(self, align) -> None:
        """Выравнивание блока: Qt.AlignmentFlag (Left/Center/Right/Justify)."""
        block_fmt = QTextBlockFormat()
        block_fmt.setAlignment(align)
        cursor = self.textCursor()
        cursor.mergeBlockFormat(block_fmt)

    def _toggle_list(self, ordered: bool) -> None:
        cursor = self.textCursor()
        list_fmt = QTextListFormat()
        list_fmt.setIndent(1)
        list_fmt.setStyle(
            QTextListFormat.Style.ListDecimal
            if ordered
            else QTextListFormat.Style.ListDisc
        )
        cursor.createList(list_fmt)

    def toggle_bullet_list(self) -> None:
        self._toggle_list(ordered=False)

    def toggle_numbered_list(self) -> None:
        self._toggle_list(ordered=True)

    def extract_headings(self) -> list[tuple[int, str, int]]:
        """Заголовки H1–H6 как (уровень, текст, номер блока) — для навигации."""
        result: list[tuple[int, str, int]] = []
        block = self.document().begin()
        while block.isValid():
            level = int(block.blockFormat().property(HEADING_LEVEL_PROP) or 0)
            if 1 <= level <= 6:
                result.append(
                    (level, self._block_semantic_text(block), block.blockNumber())
                )
            block = block.next()
        return result

    def go_to_block(self, block_number: int) -> None:
        """Переместить курсор в блок с заданным номером (панель навигации)."""
        block = self.document().findBlockByNumber(block_number)
        if block.isValid():
            self.setTextCursor(QTextCursor(block))
            self.setFocus()

    def extract_formulas(self) -> list[str]:
        """Извлечение LaTeX всех формул документа в порядке следования."""
        latex_list: list[str] = []
        block = self.document().begin()
        while block.isValid():
            it = block.begin()
            while not it.atEnd():
                fragment = it.fragment()
                if fragment.charFormat().objectType() == FORMULA_OBJECT_TYPE:
                    latex_list.append(
                        str(fragment.charFormat().property(FORMULA_LATEX_PROP))
                    )
                it += 1
            block = block.next()
        return latex_list