"""Автосохранение документа (см. FS §9.1, ADR-0003).

Работает в GUI-потоке через QTimer (никаких фоновых потоков для
обращения к документу — устранён thread-safety-дефект из спеки).
При несохранённом документе пишет recovery-файл для crash-recovery.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from PySide6.QtCore import QTimer

from core.document import Document
from core.xml_serializer import XMLSerializer


class AutoStore:
    """Автосохранение с интервалом из настроек (по умолчанию 300 с)."""

    DEFAULT_INTERVAL = 300  # секунд

    def __init__(  # noqa: PLR0913
        self,
        document: Document,
        *,
        save_path: str | None = None,
        interval: int = DEFAULT_INTERVAL,
        document_provider: Callable[[], Document] | None = None,
        recovery_path: str | Path | None = None,
        error_handler: Callable[[Exception], None] | None = None,
    ) -> None:
        self.document = document
        self.save_path = save_path
        self.document_provider = document_provider
        self.error_handler = error_handler
        self.last_error: Exception | None = None
        self.recovery_path = (
            Path(recovery_path) if recovery_path else Path("Untitled.sdoc.recover")
        )
        self.timer = QTimer()
        self.timer.setInterval(interval * 1000)
        self.timer.timeout.connect(self._auto_save)

    def start(self) -> None:
        self.timer.start()

    def stop(self) -> None:
        self.timer.stop()

    def set_interval(self, seconds: int) -> None:
        self.timer.setInterval(seconds * 1000)

    def set_document(self, document: Document, save_path: str | None = None) -> None:
        """Обновить документ и путь после New/Open/Save As."""
        self.document = document
        self.save_path = save_path

    def has_recovery(self) -> bool:
        return self.recovery_path.is_file()

    def load_recovery(self) -> Document:
        return Document.from_file(self.recovery_path)

    def discard_recovery(self) -> None:
        self.recovery_path.unlink(missing_ok=True)

    def _auto_save(self) -> None:
        """Сохранить документ или записать recovery-файл."""
        try:
            if self.document_provider is not None:
                self.document = self.document_provider()
            if self.save_path:
                self.document.save(self.save_path)
                self.discard_recovery()
                self.last_error = None
                return
            self.recovery_path.parent.mkdir(parents=True, exist_ok=True)
            XMLSerializer(self.document, str(self.recovery_path)).serialize()
            self.last_error = None
        except (OSError, RuntimeError, ValueError) as exc:
            self.last_error = exc
            if self.error_handler is not None:
                self.error_handler(exc)