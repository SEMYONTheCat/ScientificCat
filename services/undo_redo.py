"""Командный стек undo/redo на уровне модели (см. FS §9.2, ADR-0013).

Каждая операция над `Document` — класс-команда с методами `execute()` /
`undo()` / `redo()`. Стек оперирует актуальным состоянием модели, поэтому
откат всегда согласован с форматом `.sdoc` (в отличие от UI-стека из FS §9.2).
"""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Generic, TypeVar

from core.document import Block, Document, Paragraph, Run

MAX_HISTORY = 100

T = TypeVar("T")


def _new_id() -> str:
    return "id" + uuid.uuid4().hex[:8]


class Command(ABC, Generic[T]):
    """Абстрактная команда над моделью."""

    @abstractmethod
    def execute(self, model: T) -> None:
        """Применить команду к модели."""

    @abstractmethod
    def undo(self, model: T) -> None:
        """Инвертировать действие."""

    @abstractmethod
    def redo(self, model: T) -> None:
        """Повторить действие."""


@dataclass
class InsertParagraph(Command[Document]):
    """Вставить абзац с текстом в позицию body[index]."""

    index: int
    text: str = ""
    _para: Paragraph | None = field(default=None, init=False)

    def execute(self, model: Document) -> None:
        if self._para is None:
            self._para = Paragraph(id=_new_id(), runs=[Run(text=self.text)])
        pos = min(max(self.index, 0), len(model.body))
        model.body.insert(pos, self._para)

    def undo(self, model: Document) -> None:
        if self._para is not None:
            model.body = [b for b in model.body if b is not self._para]

    def redo(self, model: Document) -> None:
        self.execute(model)


@dataclass
class RemoveBlock(Command[Document]):
    """Удалить блок body[index] с возможностью восстановления."""

    index: int
    _block: Block | None = field(default=None, init=False)

    def execute(self, model: Document) -> None:
        if 0 <= self.index < len(model.body):
            self._block = model.body.pop(self.index)

    def undo(self, model: Document) -> None:
        if self._block is not None:
            model.body.insert(min(self.index, len(model.body)), self._block)

    def redo(self, model: Document) -> None:
        self.execute(model)


class UndoRedoStack:
    """Стек команд (MAX_HISTORY=100), синхронизированный с моделью."""

    def __init__(self, model: Document) -> None:
        self._model = model
        self._undo: list[Command[Document]] = []
        self._redo: list[Command[Document]] = []

    def execute(self, command: Command[Document]) -> None:
        """Применить команду и положить в undo-стек."""
        command.execute(self._model)
        self._undo.append(command)
        self._redo.clear()
        if len(self._undo) > MAX_HISTORY:
            self._undo.pop(0)

    def undo(self) -> bool:
        """Откатить последнюю команду. Возвращает True, если откат выполнен."""
        if not self._undo:
            return False
        command = self._undo.pop()
        command.undo(self._model)
        self._redo.append(command)
        return True

    def redo(self) -> bool:
        """Повторить последнюю отменённую команду."""
        if not self._redo:
            return False
        command = self._redo.pop()
        command.redo(self._model)
        self._undo.append(command)
        return True

    @property
    def can_undo(self) -> bool:
        return bool(self._undo)

    @property
    def can_redo(self) -> bool:
        return bool(self._redo)

    def clear(self) -> None:
        """Очистить оба стека (например, при открытии нового документа)."""
        self._undo.clear()
        self._redo.clear()