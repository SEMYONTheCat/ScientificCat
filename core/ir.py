"""Промежуточное представление (IR) для экспорта и превью (ADR-0006/0014).

IR — нейтральный слой между Document и целевым форматом/рендером.
Формулы в IR хранятся как LaTeX-исходник; рендер в SVG/PNG выполняется
в самом экспортёре (см. ADR-0006).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from core.bibliography import BibManager
from core.document import (
    Block,
    Document,
    InlineContent,
    ListBlock,
    Paragraph,
    Run,
    Section,
    Table,
)


@dataclass
class IRText:
    text: str
    style: str = "Body"
    bold: bool = False
    italic: bool = False
    underline: bool = False
    subscript: bool = False
    superscript: bool = False


@dataclass
class IRFormula:
    latex: str
    display: bool = False
    number: int = 0


IRParagraphItem = IRText | IRFormula


@dataclass
class IRParagraph:
    items: list[IRParagraphItem] = field(default_factory=list)
    align: str = "justify"


@dataclass
class IRHeading:
    level: int
    text: str


@dataclass
class IRList:
    ordered: bool
    items: list[str] = field(default_factory=list)


@dataclass
class IRTable:
    caption: str
    rows: list[list[IRTableCell]] = field(default_factory=list)
    align: str = "center"


@dataclass
class IRTableCell:
    items: list[IRParagraphItem] = field(default_factory=list)


IRBlock = IRParagraph | IRHeading | IRFormula | IRList | IRTable


def document_to_ir(doc: Document) -> list[IRBlock]:
    """Конвертация Document → список блоков IR."""
    blocks: list[IRBlock] = []
    for block in doc.body:
        blocks.extend(_block_to_ir(block, doc))
    if doc.bibliography.entries:
        blocks.append(IRHeading(level=1, text="Список литературы"))
        for number, entry in enumerate(doc.bibliography.entries, start=1):
            blocks.append(
                IRParagraph(
                    items=[
                        IRText(
                            BibManager.format_entry(
                                entry,
                                doc.bibliography.style,
                                number,
                            )
                        )
                    ]
                )
            )
    return blocks


def _block_to_ir(block: Block, doc: Document) -> list[IRBlock]:
    if isinstance(block, Section):
        result: list[IRBlock] = []
        if block.heading:
            result.append(IRHeading(level=block.level, text=block.heading))
        for child in block.children:
            result.extend(_block_to_ir(child, doc))
        return result
    if isinstance(block, Paragraph):
        return [
            IRParagraph(
                items=_inline_to_ir(block.inline_content(), doc),
                align=block.align,
            )
        ]
    if isinstance(block, ListBlock):
        return [IRList(ordered=block.list_type == "ordered", items=[i.text for i in block.items])]
    if isinstance(block, Table):
        rows = [
            [
                IRTableCell(items=_inline_to_ir(cell.inline_content(), doc))
                for cell in row.cells
            ]
            for row in block.rows_data
        ]
        return [IRTable(caption=block.caption, rows=rows, align=block.align)]
    # Formula (display-блок верхнего уровня)
    return [
        IRFormula(
            latex=block.latex,
            display=block.type == "display",
            number=block.number,
        )
    ]


def _inline_to_ir(
    items: list[InlineContent],
    doc: Document,
) -> list[IRParagraphItem]:
    result: list[IRParagraphItem] = []
    for item in items:
        if isinstance(item, Run):
            if item.text:
                style = doc.styles.styles.get(item.style)
                result.append(
                    IRText(
                        text=item.text,
                        style=item.style,
                        bold=item.bold if item.bold is not None else bool(style and style.bold),
                        italic=(
                            item.italic
                            if item.italic is not None
                            else bool(style and style.italic)
                        ),
                        underline=(
                            item.underline
                            if item.underline is not None
                            else bool(style and style.underline)
                        ),
                        subscript=bool(item.subscript),
                        superscript=bool(item.superscript),
                    )
                )
        else:
            result.append(
                IRFormula(
                    latex=item.latex,
                    display=item.type == "display",
                    number=item.number,
                )
            )
    return result