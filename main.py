"""Точка входа Scientific Cat.

Запуск:
    python main.py
"""

from __future__ import annotations

import sys
import traceback

from PySide6.QtWidgets import QApplication

from services.logger import AppLogger, write_crash_dump
from services.paths import resource_path
from ui.main_window import MainWindow


def install_excepthook(logger: AppLogger) -> None:
    """Перехват необработанных исключений: лог + crash-дамп (TODO §5.6)."""

    def handler(exc_type, exc_value, exc_tb) -> None:
        details = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
        logger.error(details)
        try:
            path = write_crash_dump(details)
            logger.info(f"Crash-dump сохранён: {path}")
        except OSError:
            logger.error("Не удалось сохранить crash-dump")

    sys.excepthook = handler


def main() -> int:
    if "--smoke-test" in sys.argv:
        return frozen_smoke_test()
    logger = AppLogger()
    logger.info("Scientific Cat запуск")
    install_excepthook(logger)

    app = QApplication(sys.argv)
    window = MainWindow(logger=logger)
    window.show()

    return app.exec()


def frozen_smoke_test() -> int:
    """Проверить импорты, модель и ресурсы собранного приложения."""
    from core.document import Document  # noqa: PLC0415
    from core.xml_serializer import XMLSerializer  # noqa: PLC0415

    required = (
        "assets/schema/sdoc-v1.0.xsd",
        "assets/styles/light.qss",
        "assets/katex/katex.min.js",
        "assets/icons/icon.png",
    )
    missing = [relative for relative in required if not resource_path(relative).is_file()]
    if missing:
        print(f"Missing bundled resources: {', '.join(missing)}", file=sys.stderr)
        return 2
    XMLSerializer(Document.new(), "").to_bytes()
    return 0


if __name__ == "__main__":
    sys.exit(main())