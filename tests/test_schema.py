"""Проверка целостности формата .sdoc: валидация фикстур против XSD-схемы.

См. ADR-0004 (XSD — источник истины) и ADR-0007 (фикстуры .sdoc).
"""

from __future__ import annotations

from pathlib import Path

import lxml.etree as ET

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SCHEMA_PATH = PROJECT_ROOT / "assets" / "schema" / "sdoc-v1.0.xsd"
FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"


def _load_schema() -> ET.XMLSchema:
    assert SCHEMA_PATH.is_file(), f"XSD-схема не найдена: {SCHEMA_PATH}"
    return ET.XMLSchema(ET.parse(str(SCHEMA_PATH)))


def _all_fixtures() -> list[Path]:
    fixtures = sorted(FIXTURES_DIR.glob("*.sdoc"))
    assert fixtures, f"Фикстуры не найдены в {FIXTURES_DIR}"
    return fixtures


def test_fixtures_exist() -> None:
    """Проверка, что эталонные фикстуры на месте (ADR-0007)."""
    names = {p.name for p in _all_fixtures()}
    for expected in (
        "minimal.sdoc",
        "cyrillic.sdoc",
        "formulas.sdoc",
        "table.sdoc",
        "bibliography.sdoc",
        "resources.sdoc",
    ):
        assert expected in names, f"Отсутствует фикстура {expected}"


def test_all_fixtures_valid_against_schema() -> None:
    """Каждая фикстура валидна относительно sdoc-v1.0.xsd."""
    schema = _load_schema()
    for path in _all_fixtures():
        doc = ET.parse(str(path))
        assert schema.validate(doc), (
            f"{path.name} невалиден: "
            f"{schema.error_log.last_error.message if schema.error_log else 'неизвестная ошибка'}"
        )


def test_schema_loads_without_warnings() -> None:
    """Схема парсится без фатальных предупреждений."""
    _load_schema()