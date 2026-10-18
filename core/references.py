"""Перекрёстные ссылки и авто-нумерация (см. FS §2.3, ADR-0011).

`ReferenceResolver` — единый сервис на уровне `Document`:
- авто-нумерация разделов (1, 1.1, 1.1.1…) и формул (сквозная);
- регистрация именованных объектов в `named_objects`;
- разрешение ссылок «уравнение (2)» / «таблица 1» для превью и экспортёров.
"""

from __future__ import annotations

import uuid

from core.document import Block, Document, NamedObject, Paragraph, Section, Table
from core.formula import Formula

_OBJ_TYPE_LABELS = {
    "formula": "уравнение",
    "equation": "уравнение",
    "table": "таблица",
    "figure": "рисунок",
}


class ReferenceResolver:
    """Сервис авто-нумерации и разрешения перекрёстных ссылок."""

    def __init__(self, document: Document) -> None:
        self.document = document

    # --- Регистрация и разрешение ссылок (ADR-0011 п.1, п.3) ---

    def register(self, obj_type: str, label: str = "") -> str:
        """Зарегистрировать именованный объект, вернуть его id."""
        ref_id = "ref" + uuid.uuid4().hex[:8]
        self.document.named_objects[ref_id] = NamedObject(
            id=ref_id, obj_type=obj_type, label=label
        )
        return ref_id

    def resolve(self, ref_id: str) -> str:
        """Вернуть отрендеренную подпись ссылки (напр. «уравнение (2)»)."""
        obj = self.document.named_objects.get(ref_id)
        if obj is None:
            return "???"
        type_word = _OBJ_TYPE_LABELS.get(obj.obj_type, obj.obj_type)
        return f"{type_word} ({obj.label})" if obj.label else type_word

    # --- Авто-нумерация (ADR-0011 п.4) ---

    def number_sections(self) -> None:
        """Нумерация разделов по вложенности: 1, 1.1, 1.1.1…"""
        counters: list[int] = []
        for block in self.document.body:
            self._number_section(block, counters)

    def _number_section(self, block: Block, counters: list[int]) -> None:
        if not isinstance(block, Section):
            return
        level = block.level
        while len(counters) < level:
            counters.append(0)
        del counters[level:]
        counters[level - 1] += 1
        block.number = ".".join(str(c) for c in counters)
        for child in block.children:
            self._number_section(child, counters)

    def number_formulas(self) -> None:
        """Сквозная нумерация формул по порядку появления."""
        self.document.named_objects = {
            object_id: named
            for object_id, named in self.document.named_objects.items()
            if named.obj_type not in {"formula", "equation"}
        }
        counter = 0
        for block in self.document.body:
            counter = self._number_formula_block(block, counter)

    def _number_formula_block(self, block: Block, counter: int) -> int:
        if isinstance(block, Formula):
            counter += 1
            block.number = counter
            self._index_formula(block)
        elif isinstance(block, Paragraph):
            for formula in block.formulas:
                counter += 1
                formula.number = counter
                self._index_formula(formula)
        elif isinstance(block, Section):
            for child in block.children:
                counter = self._number_formula_block(child, counter)
        elif isinstance(block, Table):
            for row in block.rows_data:
                for cell in row.cells:
                    for formula in cell.formulas:
                        counter += 1
                        formula.number = counter
                        self._index_formula(formula)
        return counter

    def _index_formula(self, formula: Formula) -> None:
        self.document.named_objects[formula.id] = NamedObject(
            id=formula.id,
            obj_type="equation",
            label=str(formula.number),
        )