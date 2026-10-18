"""Тесты командного стека undo/redo (см. ADR-0013)."""

from __future__ import annotations

from core.document import Document, Paragraph, Run, Section
from services.undo_redo import (
    MAX_HISTORY,
    InsertParagraph,
    RemoveBlock,
    UndoRedoStack,
)


def _para_text(doc: Document, index: int) -> str:
    block = doc.body[index]
    assert isinstance(block, Paragraph)
    return "".join(r.text for r in block.runs)


class TestInsertParagraph:
    def test_insert_and_undo(self) -> None:
        doc = Document.new()
        stack = UndoRedoStack(doc)

        stack.execute(InsertParagraph(0, "первый"))
        stack.execute(InsertParagraph(1, "второй"))

        assert len(doc.body) == 2
        assert _para_text(doc, 0) == "первый"
        assert _para_text(doc, 1) == "второй"
        assert stack.can_undo

        assert stack.undo() is True
        assert len(doc.body) == 1
        assert _para_text(doc, 0) == "первый"

        assert stack.undo() is True
        assert doc.body == []
        assert not stack.can_undo
        assert stack.can_redo

        assert stack.undo() is False  # нечего откатывать

    def test_redo_restores(self) -> None:
        doc = Document.new()
        stack = UndoRedoStack(doc)
        stack.execute(InsertParagraph(0, "текст"))
        stack.undo()
        stack.redo()
        assert _para_text(doc, 0) == "текст"

    def test_new_command_clears_redo(self) -> None:
        doc = Document.new()
        stack = UndoRedoStack(doc)
        stack.execute(InsertParagraph(0, "а"))
        stack.undo()
        stack.execute(InsertParagraph(0, "б"))
        assert not stack.can_redo


class TestRemoveBlock:
    def test_remove_and_undo(self) -> None:
        doc = Document.new()
        doc.body.append(Paragraph(id="p1", runs=[Run(text="x")]))
        stack = UndoRedoStack(doc)
        stack.execute(RemoveBlock(0))
        assert doc.body == []
        stack.undo()
        assert len(doc.body) == 1
        stack.redo()
        assert doc.body == []

    def test_remove_out_of_range(self) -> None:
        doc = Document.new()
        stack = UndoRedoStack(doc)
        stack.execute(RemoveBlock(5))
        assert doc.body == []
        # команда лежит в стеке, откат безопасен (ничего не меняет)
        stack.undo()
        assert doc.body == []


class TestHistoryLimit:
    def test_history_capped(self) -> None:
        doc = Document.new()
        stack = UndoRedoStack(doc)
        for i in range(MAX_HISTORY + 10):
            stack.execute(InsertParagraph(0, str(i)))
        assert len(doc.body) == MAX_HISTORY + 10
        # undo-стек ограничен MAX_HISTORY
        undo_count = 0
        while stack.undo():
            undo_count += 1
        assert undo_count == MAX_HISTORY


class TestSectionBlocks:
    def test_remove_section(self) -> None:
        doc = Document.new()
        doc.body.append(Section(id="s1", heading="Раздел"))
        stack = UndoRedoStack(doc)
        stack.execute(RemoveBlock(0))
        assert doc.body == []
        stack.undo()
        assert isinstance(doc.body[0], Section)