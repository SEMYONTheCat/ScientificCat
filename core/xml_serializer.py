"""Сериализатор Document → XML (.sdoc), см. FS §4.3, ADR-0004.

Формирует XML в пространстве имён https://scientificcat.dev/sdoc/1.0
в соответствии со схемой assets/schema/sdoc-v1.0.xsd.
"""

from __future__ import annotations

import datetime
import os
import tempfile
from pathlib import Path

import lxml.etree as ET

from core.document import (
    Block,
    Document,
    ListBlock,
    Paragraph,
    Run,
    Section,
    Table,
)
from core.formula import Formula

NS = "https://scientificcat.dev/sdoc/1.0"
W = "{" + NS + "}"


def _tag(name: str) -> str:
    return W + name


class XMLSerializer:
    """Сериализатор Document → XML."""

    def __init__(self, document: Document, output_path: str) -> None:
        self.document = document
        self.output_path = output_path
        self.root: ET._Element | None = None

    def serialize(self) -> str:
        """Построить XML и атомарно заменить целевой файл."""
        data = self.to_bytes()
        target = Path(self.output_path)
        temporary: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="wb",
                dir=target.parent,
                prefix=f".{target.name}.",
                suffix=".tmp",
                delete=False,
            ) as stream:
                temporary = Path(stream.name)
                stream.write(data)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, target)
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)
        return data.decode("utf-8")

    def to_string(self) -> str:
        return self.to_bytes().decode("utf-8")

    def to_bytes(self) -> bytes:
        self.root = self._build()
        return ET.tostring(
            self.root,
            pretty_print=True,
            xml_declaration=True,
            encoding="UTF-8",
        )

    # ---------- Построение ----------

    def _build(self) -> ET._Element:
        now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        root = ET.Element(_tag("sdoc"), nsmap={"sdoc": NS})
        root.set("version", "1.0")
        root.set("generator", "ScientificCat/1.0")
        root.set("created", now)
        root.set("modified", now)
        root.append(self._metadata())
        root.append(self._styles())
        root.append(self._body())
        root.append(self._bibliography())
        root.append(self._named_objects())
        root.append(self._resources())
        return root

    def _metadata(self) -> ET._Element:
        meta = ET.Element(_tag("metadata"))
        if self.document.title:
            ET.SubElement(meta, _tag("title")).text = self.document.title
        if self.document.author:
            ET.SubElement(meta, _tag("author")).text = self.document.author
        if self.document.keywords:
            ET.SubElement(meta, _tag("keywords")).text = self.document.keywords
        if self.document.template:
            ET.SubElement(meta, _tag("template")).text = self.document.template
        ET.SubElement(meta, _tag("language")).text = self.document.language
        return meta

    def _styles(self) -> ET._Element:
        styles = ET.Element(_tag("styles"))
        for font in self.document.styles.fonts.values():
            f = ET.SubElement(styles, _tag("font"))
            f.set("name", font.name)
            f.set("family", font.family)
            f.set("size", str(font.size))
            f.set("unit", font.unit)
        for style in self.document.styles.styles.values():
            s = ET.SubElement(styles, _tag("style"))
            s.set("name", style.name)
            s.set("font", style.font)
            s.set("size", str(style.size))
            s.set("bold", "true" if style.bold else "false")
            s.set("italic", "true" if style.italic else "false")
            s.set("underline", "true" if style.underline else "false")
            s.set("align", style.align)
        margin = ET.SubElement(styles, _tag("margin"))
        margin.set("top", self.document.styles.margin_top)
        margin.set("bottom", self.document.styles.margin_bottom)
        margin.set("left", self.document.styles.margin_left)
        margin.set("right", self.document.styles.margin_right)
        ls = ET.SubElement(styles, _tag("line_spacing"))
        ls.set("unit", "pt")
        ls.text = str(self.document.styles.line_spacing)
        return styles

    def _body(self) -> ET._Element:
        body = ET.Element(_tag("body"))
        for block in self.document.body:
            body.append(self._body_block(block))
        return body

    def _body_block(self, block: Block) -> ET._Element:
        if isinstance(block, Section):
            return self._section(block)
        if isinstance(block, Paragraph):
            return self._paragraph(block)
        if isinstance(block, ListBlock):
            return self._list(block)
        if isinstance(block, Table):
            return self._table(block)
        return self._formula(block)

    def _section(self, section: Section) -> ET._Element:
        el = ET.Element(_tag("section"))
        el.set("id", section.id)
        if section.number:
            el.set("number", section.number)
        if section.heading:
            h = ET.SubElement(el, _tag("heading"))
            h.set("level", str(section.level))
            h.text = section.heading
        for child in section.children:
            el.append(self._body_block(child))
        return el

    def _paragraph(self, p: Paragraph) -> ET._Element:
        el = ET.Element(_tag("paragraph"))
        el.set("id", p.id)
        el.set("align", p.align)
        for item in p.inline_content():
            el.append(self._run(item) if isinstance(item, Run) else self._formula(item))
        return el

    def _run(self, run: Run) -> ET._Element:
        el = ET.Element(_tag("run"))
        el.set("text", run.text)
        el.set("style", run.style)
        if run.bold is not None:
            el.set("bold", "true" if run.bold else "false")
        if run.italic is not None:
            el.set("italic", "true" if run.italic else "false")
        if run.underline is not None:
            el.set("underline", "true" if run.underline else "false")
        if run.subscript is not None:
            el.set("subscript", "true" if run.subscript else "false")
        if run.superscript is not None:
            el.set("superscript", "true" if run.superscript else "false")
        if run.reference_target:
            el.set("reference", run.reference_target)
        if run.citation_key:
            el.set("citation-key", run.citation_key)
        return el

    def _formula(self, formula: Formula) -> ET._Element:
        el = ET.Element(_tag("formula"))
        el.set("id", formula.id)
        el.set("type", formula.type)
        el.set("latex", formula.latex)
        if formula.number:
            el.set("number", str(formula.number))
        return el

    def _list(self, block: ListBlock) -> ET._Element:
        el = ET.Element(_tag("list"))
        el.set("id", block.id)
        el.set("type", block.list_type)
        for item in block.items:
            it = ET.SubElement(el, _tag("item"))
            it.text = item.text
        return el

    def _table(self, table: Table) -> ET._Element:
        el = ET.Element(_tag("table"))
        el.set("id", table.id)
        el.set("cols", str(table.cols))
        el.set("rows", str(table.rows))
        el.set("align", table.align)
        if table.caption:
            ET.SubElement(el, _tag("caption")).text = table.caption
        for row in table.rows_data:
            row_el = ET.SubElement(el, _tag("row"))
            for cell in row.cells:
                cell_el = ET.SubElement(row_el, _tag("cell"))
                cell_el.set("colspan", str(cell.colspan))
                cell_el.set("rowspan", str(cell.rowspan))
                cell_el.set("align", cell.align)
                for item in cell.inline_content():
                    cell_el.append(
                        self._run(item) if isinstance(item, Run) else self._formula(item)
                    )
        return el

    def _bibliography(self) -> ET._Element:
        bib = ET.Element(_tag("bibliography"))
        bib.set("style", self.document.bibliography.style)
        for entry in self.document.bibliography.entries:
            c = ET.SubElement(bib, _tag("citation"))
            c.set("id", "ref" + entry.key[:5] or entry.key)
            c.set("key", entry.key)
            c.set("type", entry.entry_type)
            for fname in (
                "title", "author", "journal", "booktitle", "year",
                "volume", "number", "pages", "publisher", "address", "doi",
            ):
                val = getattr(entry, fname)
                if val:
                    ET.SubElement(c, _tag(fname)).text = val
            if entry.url:
                ET.SubElement(c, _tag("url")).text = entry.url
        return bib

    def _named_objects(self) -> ET._Element:
        no = ET.Element(_tag("named-objects"))
        for obj in self.document.named_objects.values():
            o = ET.SubElement(no, _tag("object"))
            o.set("id", obj.id)
            o.set("type", obj.obj_type)
            o.set("label", obj.label)
        return no

    def _resources(self) -> ET._Element:
        res = ET.Element(_tag("resources"))
        for resource in self.document.resources.values():
            r = ET.SubElement(res, _tag("resource"))
            r.set("id", resource.id)
            r.set("type", resource.res_type)
            r.set("format", resource.format)
            r.text = resource.data
        return res