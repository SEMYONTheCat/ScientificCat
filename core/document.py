"""Модель документа (см. FS §4.1, ADR-0005).

Ядро не зависит от UI. Пагинация (get_page_count) не входит в API ядра —
номер страницы считается в UI по фактическому рендеру (ADR-0005).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Union

from core.formula import Formula

AlignType = str  # "left" | "center" | "right" | "justify"


# ---------- Стили ----------


@dataclass
class Font:
    name: str = "Main"
    family: str = "Arial"
    size: int = 12
    unit: str = "pt"


@dataclass
class ParagraphStyle:
    name: str = "Body"
    font: str = "Main"
    size: int = 12
    bold: bool = False
    italic: bool = False
    underline: bool = False
    align: AlignType = "justify"


@dataclass
class Styles:
    fonts: dict[str, Font] = field(default_factory=dict)
    styles: dict[str, ParagraphStyle] = field(default_factory=dict)
    margin_top: str = "20mm"
    margin_bottom: str = "20mm"
    margin_left: str = "30mm"
    margin_right: str = "20mm"
    line_spacing: float = 20.0
    language: str = "ru"

    @classmethod
    def default(cls) -> Styles:
        fonts = {
            "Main": Font("Main", "Arial", 12),
            "Formula": Font("Formula", "Computer Modern", 14),
        }
        styles = {
            "Body": ParagraphStyle("Body", "Main", 12, align="justify"),
            "Heading1": ParagraphStyle("Heading1", "Main", 16, bold=True),
            "Heading2": ParagraphStyle("Heading2", "Main", 14, bold=True),
        }
        return cls(fonts=fonts, styles=styles)


# ---------- Содержимое ----------


@dataclass
class Run:
    text: str = ""
    style: str = "Body"
    bold: bool | None = None
    italic: bool | None = None
    underline: bool | None = None
    subscript: bool | None = None
    superscript: bool | None = None
    reference_target: str | None = None
    citation_key: str | None = None


InlineContent = Run | Formula


@dataclass
class ListItem:
    text: str = ""


@dataclass
class ListBlock:
    id: str
    list_type: str = "unordered"  # ordered | unordered
    items: list[ListItem] = field(default_factory=list)


@dataclass
class Cell:
    runs: list[Run] = field(default_factory=list)
    formulas: list[Formula] = field(default_factory=list)
    content: list[InlineContent] = field(default_factory=list)
    colspan: int = 1
    rowspan: int = 1
    align: AlignType = "center"

    def inline_content(self) -> list[InlineContent]:
        """Вернуть текст и формулы в исходном порядке."""
        return self.content or [*self.runs, *self.formulas]


@dataclass
class Row:
    cells: list[Cell] = field(default_factory=list)


@dataclass
class Table:
    id: str
    cols: int
    rows: int
    caption: str = ""
    align: AlignType = "center"
    rows_data: list[Row] = field(default_factory=list)


@dataclass
class Paragraph:
    id: str
    align: AlignType = "justify"
    runs: list[Run] = field(default_factory=list)
    formulas: list[Formula] = field(default_factory=list)
    content: list[InlineContent] = field(default_factory=list)

    def inline_content(self) -> list[InlineContent]:
        """Вернуть текст и формулы в исходном порядке."""
        return self.content or [*self.runs, *self.formulas]


@dataclass
class Section:
    id: str
    number: str = ""
    heading: str = ""
    level: int = 1
    children: list[Block] = field(default_factory=list)


# Блок тела документа (секции, параграфы, формулы, списки, таблицы)
Block = Union["Section", "Paragraph", "Formula", "ListBlock", "Table"]


# ---------- Библиография ----------


@dataclass
class BibEntry:
    key: str
    entry_type: str = "article"
    title: str = ""
    author: str = ""
    journal: str = ""
    booktitle: str = ""
    year: str = ""
    volume: str = ""
    number: str = ""
    pages: str = ""
    publisher: str = ""
    address: str = ""
    doi: str = ""
    url: str = ""


@dataclass
class Bibliography:
    style: str = "GOST"
    entries: list[BibEntry] = field(default_factory=list)


@dataclass
class NamedObject:
    id: str
    obj_type: str
    label: str


@dataclass
class Resource:
    id: str
    res_type: str = "image"
    format: str = "png"
    data: str = ""


# ---------- Документ ----------


class Document:
    """Модель научного документа."""

    def __init__(self) -> None:
        self.title: str = ""
        self.author: str = ""
        self.keywords: str = ""
        self.template: str = ""
        self.language: str = "ru"
        self.styles: Styles = Styles.default()
        self.body: list[Block] = []
        self.bibliography: Bibliography = Bibliography()
        self.named_objects: dict[str, NamedObject] = {}
        self.resources: dict[str, Resource] = {}

    @property
    def sections(self) -> list[Section]:
        """Разделы верхнего уровня (для совместимости с FS §4.1)."""
        return [b for b in self.body if isinstance(b, Section)]

    # --- Создание и загрузка ---

    @classmethod
    def new(cls) -> Document:
        return cls()

    @classmethod
    def from_file(cls, path: str | Path) -> Document:
        """Загрузка документа из .sdoc (через XMLParser)."""
        from core.xml_parser import XMLParser  # noqa: PLC0415 - избегаем циклического импорта

        return XMLParser(str(path)).parse()

    # --- Сохранение ---

    def save(self, path: str | Path) -> None:
        """Сохранение документа в .sdoc (через XMLSerializer)."""
        from core.xml_serializer import XMLSerializer  # noqa: PLC0415

        XMLSerializer(self, str(path)).serialize()

    # --- Вспомогательное ---

    def get_word_count(self) -> int:
        """Количество слов в тексте документа (грубая оценка)."""
        return sum(self._count_block(block) for block in self.body)

    def _count_block(self, block: Block) -> int:
        if isinstance(block, Section):
            total = _words(block.heading)
            for child in block.children:
                total += self._count_block(child)
            return total
        if isinstance(block, Paragraph):
            return _words(" ".join(r.text for r in block.runs))
        if isinstance(block, ListBlock):
            return _words(" ".join(i.text for i in block.items))
        if isinstance(block, Table):
            total = 0
            for row in block.rows_data:
                for cell in row.cells:
                    total += _words(" ".join(r.text for r in cell.runs))
            return total
        return 0


def _words(text: str) -> int:
    return len(text.split())