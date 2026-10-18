"""Тесты форматирования редактора (TZ Т-01..Т-05)."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QTextCursor

from core.document import (
    BibEntry,
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
from ui.editor_widget import EditorWidget


def _select_all(widget: EditorWidget) -> None:
    cursor = widget.textCursor()
    cursor.select(cursor.SelectionType.Document)
    widget.setTextCursor(cursor)


def _inline_signature(items) -> tuple:
    return tuple(
        (
            "formula",
            item.id,
            item.type,
            item.latex,
        )
        if isinstance(item, Formula)
        else (
            "run",
            item.text,
            item.style,
            item.bold,
            item.italic,
            item.underline,
            item.subscript,
            item.superscript,
            item.reference_target,
            item.citation_key,
        )
        for item in items
    )


def _block_signature(block) -> tuple:
    if isinstance(block, Section):
        return (
            "section",
            block.id,
            block.heading,
            block.level,
            tuple(_block_signature(child) for child in block.children),
        )
    if isinstance(block, Paragraph):
        return (
            "paragraph",
            block.id,
            block.align,
            _inline_signature(block.inline_content()),
        )
    if isinstance(block, Formula):
        return ("formula", block.id, block.type, block.latex)
    if isinstance(block, ListBlock):
        return (
            "list",
            block.id,
            block.list_type,
            tuple(item.text for item in block.items),
        )
    assert isinstance(block, Table)
    return (
        "table",
        block.id,
        block.cols,
        block.rows,
        block.caption,
        block.align,
        tuple(
            tuple(
                (
                    cell.colspan,
                    cell.rowspan,
                    cell.align,
                    _inline_signature(cell.inline_content()),
                )
                for cell in row.cells
            )
            for row in block.rows_data
        ),
    )


def test_make_bold(qtbot) -> None:
    widget = EditorWidget()
    qtbot.addWidget(widget)
    widget.setPlainText("bold")
    _select_all(widget)
    widget.make_bold()
    assert widget.currentCharFormat().fontWeight() == QFont.Weight.Bold


def test_make_italic(qtbot) -> None:
    widget = EditorWidget()
    qtbot.addWidget(widget)
    widget.setPlainText("italic")
    _select_all(widget)
    widget.make_italic()
    assert widget.currentCharFormat().fontItalic() is True


def test_make_underline(qtbot) -> None:
    widget = EditorWidget()
    qtbot.addWidget(widget)
    widget.setPlainText("under")
    _select_all(widget)
    widget.make_underline()
    assert widget.currentCharFormat().fontUnderline() is True


def test_insert_and_extract_formula(qtbot) -> None:
    widget = EditorWidget()
    qtbot.addWidget(widget)
    widget.insertPlainText("до ")
    widget.insert_formula("E = mc^2", number=1)
    widget.insertPlainText(" после")
    assert widget.extract_formulas() == ["E = mc^2"]


def test_display_formula_is_a_separate_model_block(qtbot, monkeypatch) -> None:
    monkeypatch.setattr("ui.editor_widget._render_latex", lambda latex: None)
    widget = EditorWidget()
    qtbot.addWidget(widget)
    widget.insertPlainText("До формулы")
    widget.insert_formula(
        "x^2",
        formula_id="eq-display",
        ftype="display",
    )
    widget.insertPlainText("После формулы")

    model = widget.to_model()

    assert [type(block).__name__ for block in model.body] == [
        "Paragraph",
        "Formula",
        "Paragraph",
    ]
    assert isinstance(model.body[1], Formula)
    assert model.body[1].id == "eq-display"
    assert model.body[1].type == "display"


def test_inserted_table_caption_and_generated_ids_stay_stable(qtbot) -> None:
    widget = EditorWidget()
    qtbot.addWidget(widget)
    widget.insertPlainText("Введение")
    widget.insert_table(2, 3, "Данные опыта")

    first = widget.to_model()
    second = widget.to_model(first)

    first_ids = [block.id for block in first.body]
    second_ids = [block.id for block in second.body]
    assert first_ids == second_ids
    table = next(block for block in second.body if isinstance(block, Table))
    assert table.rows == 2
    assert table.cols == 3
    assert table.caption == "Данные опыта"


def test_set_heading_no_crash(qtbot) -> None:
    widget = EditorWidget()
    qtbot.addWidget(widget)
    widget.setPlainText("Заголовок")
    widget.set_heading(1)
    widget.set_alignment(Qt.AlignmentFlag.AlignCenter)
    widget.toggle_bullet_list()
    assert widget.toPlainText() == "Заголовок"


def test_editor_model_roundtrip_preserves_text_formula_order(qtbot, monkeypatch) -> None:
    monkeypatch.setattr("ui.editor_widget._render_latex", lambda latex: None)
    source = Document.new()
    paragraph = Paragraph(id="p001")
    before = Run(text="до ")
    formula = Formula("E=mc^2", number=3, formula_id="eq000001")
    after = Run(text=" после", bold=True)
    paragraph.runs.extend([before, after])
    paragraph.formulas.append(formula)
    paragraph.content.extend([before, formula, after])
    source.body.append(paragraph)

    widget = EditorWidget()
    qtbot.addWidget(widget)
    widget.load_model(source)
    restored = widget.to_model(source)

    restored_paragraph = restored.body[0]
    assert isinstance(restored_paragraph, Paragraph)
    assert [
        item.latex if isinstance(item, Formula) else item.text
        for item in restored_paragraph.inline_content()
    ] == ["до ", "E=mc^2", " после"]
    assert restored_paragraph.formulas[0].number == 1
    assert restored_paragraph.formulas[0].id == "eq000001"
    assert restored_paragraph.runs[1].bold is True


def test_editor_model_roundtrip_preserves_headings(qtbot) -> None:
    source = Document.new()
    source.body.append(Section(id="sec001", heading="Введение", level=2))

    widget = EditorWidget()
    qtbot.addWidget(widget)
    widget.load_model(source)
    restored = widget.to_model(source)

    assert isinstance(restored.body[0], Section)
    assert restored.body[0].heading == "Введение"
    assert restored.body[0].level == 2


def test_editor_model_roundtrip_preserves_table(qtbot, monkeypatch) -> None:
    monkeypatch.setattr("ui.editor_widget._render_latex", lambda latex: None)
    source = Document.new()
    formula = Formula("x+y", formula_id="eq000003")
    formula_cell = Cell(formulas=[formula], content=[formula])
    source.body.append(
        Table(
            id="tbl001",
            cols=2,
            rows=1,
            rows_data=[
                Row(
                    cells=[
                        Cell(runs=[Run("Текст")], content=[Run("Текст")]),
                        formula_cell,
                    ]
                )
            ],
        )
    )

    widget = EditorWidget()
    qtbot.addWidget(widget)
    widget.load_model(source)
    restored = widget.to_model(source)

    assert len(restored.body) == 1
    restored_table = restored.body[0]
    assert isinstance(restored_table, Table)
    assert restored_table.rows == 1
    assert restored_table.cols == 2
    assert restored_table.rows_data[0].cells[0].runs[0].text == "Текст"
    assert restored_table.rows_data[0].cells[1].formulas[0].latex == "x+y"


def test_editor_roundtrip_preserves_structure_captions_and_ids(
    qtbot, monkeypatch
) -> None:
    monkeypatch.setattr("ui.editor_widget._render_latex", lambda latex: None)
    source = Document.new()
    display_formula = Formula(
        r"\int_0^1 x\,dx",
        formula_type="display",
        formula_id="eq-stable",
    )
    nested_table = Table(
        id="table-stable",
        cols=1,
        rows=1,
        caption="Экспериментальные данные",
        rows_data=[Row(cells=[Cell(runs=[Run("42")], content=[Run("42")])])],
    )
    nested = Section(
        id="section-nested",
        heading="Метод",
        level=2,
        children=[display_formula, nested_table],
    )
    source.body.extend(
        [
            Section(
                id="section-root",
                heading="Исследование",
                level=1,
                children=[
                    Paragraph(
                        id="paragraph-child",
                        runs=[Run("Внутри раздела")],
                        content=[Run("Внутри раздела")],
                    ),
                    nested,
                ],
            ),
            Paragraph(
                id="paragraph-root",
                runs=[Run("После раздела")],
                content=[Run("После раздела")],
            ),
            ListBlock(
                id="list-stable",
                list_type="ordered",
                items=[ListItem("Первый")],
            ),
        ]
    )

    widget = EditorWidget()
    qtbot.addWidget(widget)
    widget.load_model(source)
    restored = widget.to_model(source)

    assert [block.id for block in restored.body] == [
        "section-root",
        "paragraph-root",
        "list-stable",
    ]
    restored_root = restored.body[0]
    assert isinstance(restored_root, Section)
    assert [block.id for block in restored_root.children] == [
        "paragraph-child",
        "section-nested",
    ]
    restored_nested = restored_root.children[1]
    assert isinstance(restored_nested, Section)
    assert isinstance(restored_nested.children[0], Formula)
    assert restored_nested.children[0].id == "eq-stable"
    assert restored_nested.children[0].type == "display"
    restored_table = restored_nested.children[1]
    assert isinstance(restored_table, Table)
    assert restored_table.id == "table-stable"
    assert restored_table.caption == "Экспериментальные данные"


def test_all_sdoc_fixtures_survive_editor_roundtrip(
    qtbot, fixtures_dir, monkeypatch
) -> None:
    monkeypatch.setattr("ui.editor_widget._render_latex", lambda latex: None)
    widget = EditorWidget()
    qtbot.addWidget(widget)

    for fixture in sorted(fixtures_dir.glob("*.sdoc")):
        source = Document.from_file(fixture)
        widget.load_model(source)
        restored = widget.to_model(source)
        assert tuple(_block_signature(block) for block in restored.body) == tuple(
            _block_signature(block) for block in source.body
        ), fixture.name


def test_subscript_and_superscript_survive_model_roundtrip(qtbot) -> None:
    widget = EditorWidget()
    qtbot.addWidget(widget)
    widget.setPlainText("индекс")
    _select_all(widget)
    widget.make_subscript()

    model = widget.to_model()
    paragraph = model.body[0]
    assert isinstance(paragraph, Paragraph)
    assert paragraph.runs[0].subscript is True

    widget.load_model(model)
    restored = widget.to_model()
    restored_paragraph = restored.body[0]
    assert isinstance(restored_paragraph, Paragraph)
    assert restored_paragraph.runs[0].subscript is True


def test_real_qt_list_converts_to_model(qtbot) -> None:
    widget = EditorWidget()
    qtbot.addWidget(widget)
    widget.setPlainText("Первый")
    widget.toggle_numbered_list()

    model = widget.to_model()

    assert isinstance(model.body[0], ListBlock)
    assert model.body[0].list_type == "ordered"
    assert model.body[0].items[0].text == "Первый"


def test_formula_reference_renumbers_after_formula_removal(qtbot, monkeypatch) -> None:
    monkeypatch.setattr("ui.editor_widget._render_latex", lambda latex: None)
    source = Document.new()
    first = Formula("a", formula_id="eq000001")
    second = Formula("b", formula_id="eq000002")
    reference = Run("см. уравнение (2)", reference_target=second.id)
    paragraph = Paragraph(
        id="p001",
        formulas=[first, second],
        runs=[reference],
        content=[first, second, reference],
    )
    source.body.append(paragraph)
    widget = EditorWidget()
    qtbot.addWidget(widget)
    widget.load_model(source)

    cursor = widget.textCursor()
    cursor.setPosition(0)
    cursor.setPosition(1, QTextCursor.MoveMode.KeepAnchor)
    cursor.removeSelectedText()
    restored = widget.to_model(source)

    restored_paragraph = restored.body[0]
    assert isinstance(restored_paragraph, Paragraph)
    assert restored_paragraph.formulas[0].id == second.id
    assert restored_paragraph.formulas[0].number == 1
    assert restored_paragraph.runs[0].text == "см. уравнение (1)"
    assert restored_paragraph.runs[0].reference_target == second.id


def test_citation_key_survives_editor_roundtrip(qtbot) -> None:
    source = Document.new()
    source.bibliography.entries.extend(
        [
            BibEntry(key="first", title="Первая"),
            BibEntry(key="second", title="Вторая"),
        ]
    )
    citation = Run("[2]", citation_key="second")
    source.body.append(Paragraph(id="p001", runs=[citation], content=[citation]))
    widget = EditorWidget()
    qtbot.addWidget(widget)
    widget.load_model(source)

    restored = widget.to_model(source)

    paragraph = restored.body[0]
    assert isinstance(paragraph, Paragraph)
    assert paragraph.runs[0].text == "[2]"
    assert paragraph.runs[0].citation_key == "second"