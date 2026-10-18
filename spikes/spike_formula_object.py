"""Спайк A (ADR-0001): inline-формула как QTextObjectInterface.

Проверяет осуществимость:
  1) вставки формулы как объекта-заменителя U+FFFC в QTextDocument;
  2) хранения LaTeX/type/number в QTextCharFormat (setProperty);
  3) извлечения LaTeX обратно из документа (lossless round-trip).

Запуск headless (проверка round-trip):
    set QT_QPA_PLATFORM=offscreen & .venv\\Scripts\\python.exe spikes\\spike_formula_object.py
Запуск с окном:
    .venv\\Scripts\\python.exe spikes\\spike_formula_object.py --show
"""

from __future__ import annotations

import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QObject, QRectF, QSizeF, Qt
from PySide6.QtGui import QColor, QPainter, QTextCharFormat, QTextFormat
from PySide6.QtWidgets import QApplication, QTextEdit
from PySide6.QtGui import QAbstractTextDocumentLayout, QTextObjectInterface

# --- Идентификаторы (будут вынесены в core/ при реализации) ---
FORMULA_OBJECT_TYPE = QTextFormat.UserObject + 1
FORMULA_LATEX_PROP = QTextFormat.UserProperty + 1
FORMULA_TYPE_PROP = QTextFormat.UserProperty + 2
FORMULA_NUMBER_PROP = QTextFormat.UserProperty + 3


class FormulaObject(QObject, QTextObjectInterface):
    """Отрисовка объекта-формулы и вычисление его размера.

    На этапе спайка рисуем LaTeX как плейсхолдер; при реализации
    (ADR-0002) здесь будет рендер KaTeX в SVG.

    QObject требуется, т.к. registerHandler принимает QObject.
    """

    def intrinsicSize(self, fmt: QTextFormat, painter: QPainter) -> QSizeF:
        latex = fmt.property(FORMULA_LATEX_PROP)
        metrics = painter.fontMetrics()
        return QSizeF(metrics.horizontalAdvance(latex) + 12, metrics.height() + 8)

    def drawObject(
        self,
        painter: QPainter,
        rect: QRectF,
        fmt: QTextFormat,
        context: "QAbstractTextDocumentLayout.PaintContext",
    ) -> None:
        latex = fmt.property(FORMULA_LATEX_PROP)
        number = fmt.property(FORMULA_NUMBER_PROP)
        painter.save()
        painter.setPen(QColor("#1a7f37"))
        painter.drawRoundedRect(rect, 3, 3)
        painter.drawText(rect.adjusted(6, 4, 6, -4), Qt.AlignLeft, str(latex))
        if number:
            painter.drawText(
                rect.adjusted(6, 4, -6, -4),
                Qt.AlignRight,
                f"({number})",
            )
        painter.restore()


class FormulaEditor(QTextEdit):
    """Редактор с поддержкой объектов-формул (спайк)."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setAcceptRichText(True)
        self._register_handler()

    def _register_handler(self) -> None:
        layout = self.document().documentLayout()
        layout.registerHandler(FORMULA_OBJECT_TYPE, FormulaObject(self))

    def insert_formula(self, latex: str, number: int = 0, ftype: str = "inline") -> None:
        cursor = self.textCursor()
        fmt = QTextCharFormat()
        fmt.setObjectType(FORMULA_OBJECT_TYPE)
        fmt.setProperty(FORMULA_LATEX_PROP, latex)
        fmt.setProperty(FORMULA_TYPE_PROP, ftype)
        fmt.setProperty(FORMULA_NUMBER_PROP, number)
        cursor.insertText("\ufffc", fmt)


def extract_formulas(editor: QTextEdit) -> list[str]:
    """Извлечь LaTeX всех формул из документа в порядке следования."""
    latex_list: list[str] = []
    block = editor.document().begin()
    while block.isValid():
        it = block.begin()
        while not it.atEnd():
            frag = it.fragment()
            if frag.charFormat().objectType() == FORMULA_OBJECT_TYPE:
                latex_list.append(str(frag.charFormat().property(FORMULA_LATEX_PROP)))
            it += 1
        block = block.next()
    return latex_list


def run_roundtrip() -> bool:
    app = QApplication.instance() or QApplication(sys.argv)
    editor = FormulaEditor()

    formulas = [
        ("E = mc^2", 1),
        (r"\int_0^\infty e^{-x} dx = 1", 2),
        (r"\frac{a+b}{c-d}", 3),
    ]

    editor.insertPlainText("Текст: ")
    for latex, num in formulas:
        editor.insert_formula(latex, num)
        editor.insertPlainText(" и ")

    extracted = extract_formulas(editor)
    expected = [latex for latex, _ in formulas]

    print("Вставлено:", expected)
    print("Извлечено:", extracted)

    ok = extracted == expected
    print("Round-trip:", "OK" if ok else "FAIL")
    return ok


def main() -> int:
    show = "--show" in sys.argv
    ok = run_roundtrip()
    if show:
        app = QApplication.instance() or QApplication(sys.argv)
        editor = FormulaEditor()
        editor.setWindowTitle("Spike A — Formula Object")
        editor.resize(700, 200)
        editor.insertPlainText("Формула ")
        editor.insert_formula("E = mc^2", 1)
        editor.insertPlainText(" в тексте.")
        editor.show()
        app.exec()
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())