"""Парсер XML → Document (.sdoc), см. FS §4.3, ADR-0004.

Выполняет валидацию по схеме assets/schema/sdoc-v1.0.xsd (lxml.XMLSchema),
затем разбирает элементы в модель core.document.
"""

from __future__ import annotations

import contextlib

import lxml.etree as ET

from core.document import (
    BibEntry,
    Bibliography,
    Cell,
    Document,
    Font,
    ListBlock,
    ListItem,
    NamedObject,
    Paragraph,
    ParagraphStyle,
    Resource,
    Row,
    Run,
    Section,
    Styles,
    Table,
)
from core.formula import Formula, FormulaType
from services.paths import resource_path

NS = "https://scientificcat.dev/sdoc/1.0"
SCHEMA_PATH = resource_path("assets/schema/sdoc-v1.0.xsd")


def _local(tag: str) -> str:
    """Локальное имя тега (без namespace)."""
    return tag.rsplit("}", 1)[-1]


class XMLParser:
    """Парсер формата .sdoc."""

    def __init__(self, xml_path: str) -> None:
        self.path = xml_path
        self.tree: ET._ElementTree | None = None
        self.document = Document()
        self._schema: ET.XMLSchema | None = None

    def parse(self) -> Document:
        """Полный парсинг XML → Document (с валидацией по XSD)."""
        self.tree = ET.parse(self.path)
        self._validate_schema()
        root = self.tree.getroot()
        self.document = Document()
        self._parse_metadata(root)
        self._parse_styles(root)
        self._parse_body(root)
        self._parse_bibliography(root)
        self._parse_named_objects(root)
        self._parse_resources(root)
        return self.document

    # ---------- Валидация ----------

    def _load_schema(self) -> ET.XMLSchema:
        if self._schema is None:
            if not SCHEMA_PATH.is_file():
                raise FileNotFoundError(f"XSD-схема не найдена: {SCHEMA_PATH}")
            self._schema = ET.XMLSchema(ET.parse(str(SCHEMA_PATH)))
        return self._schema

    def _validate_schema(self) -> bool:
        schema = self._load_schema()
        assert self.tree is not None
        if not schema.validate(self.tree):
            raise ValueError(f"Невалидный .sdoc: {schema.error_log}")
        return True

    # ---------- Разбор ----------

    def _find(self, root: ET._Element, tag: str) -> ET._Element | None:
        return root.find(f"{{{NS}}}{tag}")

    def _findall(self, root: ET._Element, tag: str) -> list[ET._Element]:
        return root.findall(f"{{{NS}}}{tag}")

    def _parse_metadata(self, root: ET._Element) -> None:
        meta = self._find(root, "metadata")
        if meta is None:
            return
        doc = self.document
        doc.title = self._text(meta, "title")
        doc.author = self._text(meta, "author")
        doc.keywords = self._text(meta, "keywords")
        doc.template = self._text(meta, "template")
        doc.language = self._text(meta, "language") or doc.language

    def _parse_styles(self, root: ET._Element) -> None:
        styles_el = self._find(root, "styles")
        if styles_el is None:
            return
        styles = Styles.default()
        for font_el in self._findall(styles_el, "font"):
            styles.fonts[font_el.get("name", "Main")] = Font(
                name=font_el.get("name", "Main"),
                family=font_el.get("family", "Arial"),
                size=int(font_el.get("size", "12")),
                unit=font_el.get("unit", "pt"),
            )
        for style_el in self._findall(styles_el, "style"):
            styles.styles[style_el.get("name", "Body")] = ParagraphStyle(
                name=style_el.get("name", "Body"),
                font=style_el.get("font", "Main"),
                size=int(style_el.get("size", "12")),
                bold=style_el.get("bold", "false") == "true",
                italic=style_el.get("italic", "false") == "true",
                underline=style_el.get("underline", "false") == "true",
                align=style_el.get("align", "justify"),
            )
        margin = self._find(styles_el, "margin")
        if margin is not None:
            styles.margin_top = margin.get("top", styles.margin_top)
            styles.margin_bottom = margin.get("bottom", styles.margin_bottom)
            styles.margin_left = margin.get("left", styles.margin_left)
            styles.margin_right = margin.get("right", styles.margin_right)
        ls = self._find(styles_el, "line_spacing")
        if ls is not None and ls.text:
            with contextlib.suppress(ValueError):
                styles.line_spacing = float(ls.text)
        self.document.styles = styles

    def _parse_body(self, root: ET._Element) -> None:
        body = self._find(root, "body")
        if body is None:
            return
        for child in body:
            name = _local(child.tag)
            if name == "section":
                self.document.body.append(self._parse_section(child))
            elif name == "paragraph":
                self.document.body.append(self._parse_paragraph(child))
            elif name == "formula":
                self.document.body.append(self._parse_formula(child))
            elif name == "list":
                self.document.body.append(self._parse_list(child))
            elif name == "table":
                self.document.body.append(self._parse_table(child))

    def _parse_section(self, el: ET._Element) -> Section:
        section = Section(id=el.get("id", ""), number=el.get("number", ""))
        heading = self._find(el, "heading")
        if heading is not None:
            section.heading = heading.text or ""
            section.level = int(heading.get("level", "1"))
        for child in el:
            name = _local(child.tag)
            if name == "section":
                section.children.append(self._parse_section(child))
            elif name == "paragraph":
                section.children.append(self._parse_paragraph(child))
            elif name == "formula":
                section.children.append(self._parse_formula(child))
            elif name == "list":
                section.children.append(self._parse_list(child))
            elif name == "table":
                section.children.append(self._parse_table(child))
        return section

    def _parse_paragraph(self, el: ET._Element) -> Paragraph:
        p = Paragraph(id=el.get("id", ""), align=el.get("align", "justify"))
        for child in el:
            name = _local(child.tag)
            if name == "run":
                run = self._parse_run(child)
                p.runs.append(run)
                p.content.append(run)
            elif name == "formula":
                formula = self._parse_formula(child)
                p.formulas.append(formula)
                p.content.append(formula)
        return p

    def _parse_run(self, el: ET._Element) -> Run:
        return Run(
            text=el.get("text", el.text or ""),
            style=el.get("style", "Body"),
            bold=self._optional_bool(el, "bold"),
            italic=self._optional_bool(el, "italic"),
            underline=self._optional_bool(el, "underline"),
            subscript=self._optional_bool(el, "subscript"),
            superscript=self._optional_bool(el, "superscript"),
            reference_target=el.get("reference"),
            citation_key=el.get("citation-key"),
        )

    def _parse_formula(self, el: ET._Element) -> Formula:
        formula_type: FormulaType = (
            "display" if el.get("type") == "display" else "inline"
        )
        return Formula(
            latex=el.get("latex", ""),
            formula_type=formula_type,
            number=int(el.get("number", "0")),
            formula_id=el.get("id"),
        )

    def _parse_list(self, el: ET._Element) -> ListBlock:
        block = ListBlock(
            id=el.get("id", ""),
            list_type=el.get("type", "unordered"),
        )
        for item in self._findall(el, "item"):
            block.items.append(ListItem(text=item.text or ""))
        return block

    def _parse_table(self, el: ET._Element) -> Table:
        table = Table(
            id=el.get("id", ""),
            cols=int(el.get("cols", "0")),
            rows=int(el.get("rows", "0")),
            align=el.get("align", "center"),
        )
        caption = self._find(el, "caption")
        if caption is not None:
            table.caption = caption.text or ""
        for row_el in self._findall(el, "row"):
            row = Row()
            for cell_el in self._findall(row_el, "cell"):
                cell = Cell(
                    colspan=int(cell_el.get("colspan", "1")),
                    rowspan=int(cell_el.get("rowspan", "1")),
                    align=cell_el.get("align", "center"),
                )
                for child in cell_el:
                    name = _local(child.tag)
                    if name == "run":
                        run = self._parse_run(child)
                        cell.runs.append(run)
                        cell.content.append(run)
                    elif name == "formula":
                        formula = self._parse_formula(child)
                        cell.formulas.append(formula)
                        cell.content.append(formula)
                row.cells.append(cell)
            table.rows_data.append(row)
        return table

    def _parse_bibliography(self, root: ET._Element) -> None:
        bib_el = self._find(root, "bibliography")
        if bib_el is None:
            return
        bib = Bibliography(style=bib_el.get("style", "GOST"))
        for citation in self._findall(bib_el, "citation"):
            entry = BibEntry(
                key=citation.get("key", ""),
                entry_type=citation.get("type", "article"),
                title=self._text(citation, "title"),
                author=self._text(citation, "author"),
                journal=self._text(citation, "journal"),
                booktitle=self._text(citation, "booktitle"),
                year=self._text(citation, "year"),
                volume=self._text(citation, "volume"),
                number=self._text(citation, "number"),
                pages=self._text(citation, "pages"),
                publisher=self._text(citation, "publisher"),
                address=self._text(citation, "address"),
                doi=self._text(citation, "doi"),
                url=self._text(citation, "url"),
            )
            bib.entries.append(entry)
        self.document.bibliography = bib

    def _parse_named_objects(self, root: ET._Element) -> None:
        no_el = self._find(root, "named-objects")
        if no_el is None:
            return
        for obj in self._findall(no_el, "object"):
            named = NamedObject(
                id=obj.get("id", ""),
                obj_type=obj.get("type", ""),
                label=obj.get("label", ""),
            )
            self.document.named_objects[named.id] = named

    def _parse_resources(self, root: ET._Element) -> None:
        res_el = self._find(root, "resources")
        if res_el is None:
            return
        for r in self._findall(res_el, "resource"):
            resource = Resource(
                id=r.get("id", ""),
                res_type=r.get("type", "image"),
                format=r.get("format", "png"),
                data=(r.text or "").strip(),
            )
            self.document.resources[resource.id] = resource

    @staticmethod
    def _text(parent: ET._Element, tag: str) -> str:
        el = parent.find(f"{{{NS}}}{tag}")
        return el.text or "" if el is not None else ""

    @staticmethod
    def _optional_bool(element: ET._Element, attribute: str) -> bool | None:
        value = element.get(attribute)
        if value is None:
            return None
        return value == "true"