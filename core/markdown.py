"""Markdown импорт/экспорт (см. TZ Т-07, TODO Этап 2).

Импорт .md → Document через mistletoe (AST), экспорт Document → .md.
Формулы представляются как $latex$ (inline) / $$latex$$ (display).
"""

from __future__ import annotations

import secrets

import mistletoe
from mistletoe import block_token as bt

from core.document import (
    Cell,
    Document,
    Formula,
    ListBlock,
    ListItem,
    Paragraph,
    Row,
    Run,
    Section,
    Table,
)


def _gen_id(prefix: str) -> str:
    return prefix + secrets.token_hex(3)


# ---------- Импорт: .md → Document ----------


def md_to_document(md_text: str) -> Document:
    """Конвертация Markdown-текста в Document."""
    doc = Document()
    tree = mistletoe.Document(md_text)
    for child in tree.children:
        block = _block_to_model(child)
        if block is not None:
            doc.body.append(block)
    return doc


def _block_to_model(token):  # noqa: PLR0911
    if isinstance(token, bt.Heading):
        return Section(
            id=_gen_id("sec"),
            heading=_spans_to_md(token.children),
            level=token.level,
        )
    if isinstance(token, bt.Paragraph):
        return Paragraph(id=_gen_id("p"), runs=[Run(text=_spans_to_md(token.children))])
    if isinstance(token, bt.List):
        items: list[ListItem] = []
        for item in token.children:
            if isinstance(item, bt.ListItem):
                items.append(ListItem(text=_spans_to_md(item.children)))
        return ListBlock(
            id=_gen_id("list"),
            list_type="ordered" if token.start else "unordered",
            items=items,
        )
    if isinstance(token, bt.CodeFence):
        return Paragraph(
            id=_gen_id("p"),
            runs=[Run(text=token.content or "", style="Code")],
        )
    if isinstance(token, bt.Quote):
        return Paragraph(
            id=_gen_id("p"),
            runs=[Run(text=_spans_to_md(token.children), style="Quote")],
        )
    if isinstance(token, bt.Table):
        return _table_to_model(token)
    if isinstance(token, bt.ThematicBreak):
        return None
    return None


def _table_to_model(token) -> Table:
    cols = len(token.header)
    table = Table(id=_gen_id("tbl"), cols=cols, rows=0)
    header = Row(cells=[Cell(runs=[_cell_run(c)]) for c in token.header])
    table.rows_data.append(header)
    for row in token.rows:
        table.rows_data.append(Row(cells=[Cell(runs=[_cell_run(c)]) for c in row]))
    table.rows = len(table.rows_data)
    return table


def _cell_run(cell_token) -> Run:
    children = getattr(cell_token, "children", None)
    text = _spans_to_md(children) if children is not None else str(cell_token)
    return Run(text=text)


def _spans_to_md(spans) -> str:
    """Рекурсивный разбор спанов/блоков в Markdown-текст.

    Устойчив к именам классов mistletoe (на разных версиях имена
    спанов различаются) — используется type().__name__/getattr.
    """
    return "".join(_span_to_md(span) for span in spans).strip()


def _span_to_md(span) -> str:  # noqa: PLR0911
    name = type(span).__name__
    children = getattr(span, "children", None)
    content = getattr(span, "content", None)
    if name == "Strong":
        return f"**{_spans_to_md(children or [])}**"
    if name == "Emphasis":
        return f"*{_spans_to_md(children or [])}*"
    if name in ("CodeSpan", "InlineCode"):
        return f"`{content}`" if content else ""
    if name == "LineBreak":
        return " "
    if content is not None:
        return str(content)
    if children is not None:
        return _spans_to_md(children)
    return ""


# ---------- Экспорт: Document → .md ----------


def document_to_md(doc: Document) -> str:
    """Конвертация Document в Markdown-текст."""
    lines: list[str] = []
    if doc.title:
        lines.append(f"# {doc.title}")
    for block in doc.body:
        _block_to_md(block, lines)
    return "\n".join(lines)


def _block_to_md(block, lines: list[str]) -> None:
    if isinstance(block, Section):
        lines.append(f"{'#' * block.level} {block.heading}")
        for child in block.children:
            _block_to_md(child, lines)
    elif isinstance(block, Paragraph):
        parts: list[str] = []
        for item in block.inline_content():
            if isinstance(item, Run):
                parts.append(_run_to_md(item))
            else:
                delim = "$$" if item.type == "display" else "$"
                parts.append(f"{delim}{item.latex}{delim}")
        lines.append("".join(parts))
    elif isinstance(block, ListBlock):
        for i, item in enumerate(block.items, start=1):
            prefix = f"{i}. " if block.list_type == "ordered" else "- "
            lines.append(f"{prefix}{item.text}")
    elif isinstance(block, Table):
        _table_to_md(block, lines)
    elif isinstance(block, Formula):
        delim = "$$" if block.type == "display" else "$"
        lines.append(f"{delim}{block.latex}{delim}")


def _run_to_md(run: Run) -> str:
    text = run.text
    if run.subscript:
        text = f"<sub>{text}</sub>"
    elif run.superscript:
        text = f"<sup>{text}</sup>"
    if run.underline:
        text = f"<u>{text}</u>"
    if run.italic:
        text = f"*{text}*"
    if run.bold:
        text = f"**{text}**"
    return text


def _table_to_md(table: Table, lines: list[str]) -> None:
    if not table.rows_data:
        return
    header = table.rows_data[0]
    lines.append("| " + " | ".join(_cell_text(c) for c in header.cells) + " |")
    lines.append("| " + " | ".join("---" for _ in header.cells) + " |")
    for row in table.rows_data[1:]:
        lines.append("| " + " | ".join(_cell_text(c) for c in row.cells) + " |")


def _cell_text(cell: Cell) -> str:
    return " ".join(r.text for r in cell.runs).replace("|", "\\|")