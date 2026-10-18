"""Тесты палитры символов (см. FS §3.3)."""

from __future__ import annotations

from ui.symbol_palette import SymbolPalette


def test_symbol_palette_emits_insert(qtbot) -> None:
    palette = SymbolPalette()
    qtbot.addWidget(palette)
    received: list[str] = []
    palette.symbolInserted.connect(received.append)
    palette.insert_symbol(r"\alpha")
    assert received == [r"\alpha"]


def test_symbol_palette_tabs(qtbot) -> None:
    palette = SymbolPalette()
    qtbot.addWidget(palette)
    assert palette._tabs.count() >= 4


def test_filter_enables_tabs(qtbot) -> None:
    palette = SymbolPalette()
    qtbot.addWidget(palette)
    palette._filter("alpha")
    # хотя бы одна вкладка остаётся доступной
    assert any(palette._tabs.isTabEnabled(i) for i in range(palette._tabs.count()))