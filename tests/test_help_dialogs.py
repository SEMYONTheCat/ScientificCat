"""Tests for the built-in Help and About dialogs."""

from __future__ import annotations

from ui.help_dialogs import AboutDialog, HelpDialog


def test_help_dialog_contains_core_workflows(qtbot) -> None:
    dialog = HelpDialog()
    qtbot.addWidget(dialog)
    text = dialog.help_browser.toPlainText()

    assert "Оглавление" in text
    assert "Ctrl+M" in text
    assert "Дважды щёлкните" in text
    assert "Экспорт" in text


def test_about_dialog_contains_cat_image_and_dedication(qtbot) -> None:
    dialog = AboutDialog()
    qtbot.addWidget(dialog)

    pixmap = dialog.image_label.pixmap()
    assert pixmap is not None
    assert not pixmap.isNull()
    assert dialog.dedication_label.text() == "Проект посвящён памяти кота Семёна"
