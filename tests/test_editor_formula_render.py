"""Тесты WYSIWYG-рендера формул в редакторе (TODO §7, ADR-0002).

Рендер тестируется через monkeypatch `_render_latex`, чтобы не зависеть
от установленного matplotlib: проверяем, что изображение сохраняется в
char-формат и что intrinsicSize/drawObject его используют.
"""

from __future__ import annotations

from PySide6.QtCore import QRectF, QSizeF
from PySide6.QtGui import QImage, QPainter

from ui.editor_widget import (
    FORMULA_IMAGE_PROP,
    FORMULA_LATEX_PROP,
    FORMULA_OBJECT_TYPE,
    EditorWidget,
    FormulaObject,
    _render_latex,
)


def _formula_char_format(editor: EditorWidget, latex: str):
    block = editor.document().begin()
    while block.isValid():
        it = block.begin()
        while not it.atEnd():
            fragment = it.fragment()
            fmt = fragment.charFormat()
            if (
                fmt.objectType() == FORMULA_OBJECT_TYPE
                and fmt.property(FORMULA_LATEX_PROP) == latex
            ):
                return fmt
            it += 1
        block = block.next()
    return None


def test_insert_stores_rendered_image(qtbot, monkeypatch) -> None:
    image = QImage(64, 32, QImage.Format.Format_RGB32)
    image.fill(0)
    monkeypatch.setattr(
        "ui.editor_widget._render_latex", lambda latex: (image, QSizeF(42.67, 21.33))
    )
    editor = EditorWidget()
    qtbot.addWidget(editor)
    editor.insert_formula("E = mc^2")

    cf = _formula_char_format(editor, "E = mc^2")
    assert cf is not None
    stored = cf.property(FORMULA_IMAGE_PROP)
    assert isinstance(stored, QImage) and not stored.isNull()


def test_real_formula_render_has_compact_canvas() -> None:
    result = _render_latex("E=mc^2")

    assert result is not None
    image, _size = result
    assert image.width() < 300
    assert image.height() < 100


def test_formula_handler_is_registered_with_document_layout(qtbot) -> None:
    editor = EditorWidget()
    qtbot.addWidget(editor)

    handler = editor.document().documentLayout().handlerForObject(FORMULA_OBJECT_TYPE)

    assert handler is editor._formula_handler


def test_fallback_placeholder_without_render(qtbot, monkeypatch) -> None:
    monkeypatch.setattr("ui.editor_widget._render_latex", lambda latex: None)
    editor = EditorWidget()
    qtbot.addWidget(editor)
    editor.insert_formula("x^2")

    cf = _formula_char_format(editor, "x^2")
    assert cf is not None
    assert not isinstance(cf.property(FORMULA_IMAGE_PROP), QImage)


def test_intrinsic_size_and_draw_use_image(qtbot, monkeypatch) -> None:
    image = QImage(64, 32, QImage.Format.Format_RGB32)
    image.fill(0)
    monkeypatch.setattr(
        "ui.editor_widget._render_latex", lambda latex: (image, QSizeF(42.67, 21.33))
    )
    editor = EditorWidget()
    qtbot.addWidget(editor)
    editor.insert_formula("a+b")

    cf = _formula_char_format(editor, "a+b")
    assert cf is not None

    obj = FormulaObject(editor)
    canvas = QImage(400, 200, QImage.Format.Format_RGB32)
    painter = QPainter(canvas)
    size = obj.intrinsicSize(editor.document(), 0, cf)
    obj.drawObject(painter, QRectF(0, 0, 200, 60), editor.document(), 0, cf)
    painter.end()
    assert size.width() > 0 and size.height() > 0


def test_replace_formula_preserves_object_identity(qtbot, monkeypatch) -> None:
    monkeypatch.setattr("ui.editor_widget._render_latex", lambda latex: None)
    editor = EditorWidget()
    qtbot.addWidget(editor)
    editor.insert_formula(
        "x^2",
        number=4,
        ftype="inline",
        formula_id="eq000123",
    )

    assert editor.replace_formula_at(0, r"\frac{a}{b}", "display") is True

    records = editor.extract_formula_records()
    assert records == [("eq000123", 4, r"\frac{a}{b}")]