"""Тесты автосохранения (см. FS §9.1, ADR-0003)."""

from __future__ import annotations

import pytest

from core.document import Document
from core.xml_serializer import XMLSerializer
from services.autostore import AutoStore


def test_autostore_saves_document(qtbot, tmp_path) -> None:
    doc = Document.new()
    doc.title = "Test"
    out = tmp_path / "doc.sdoc"
    store = AutoStore(doc, save_path=str(out), interval=60)
    store._auto_save()
    assert out.is_file()


def test_autostore_recovery_when_no_path(qtbot, tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    doc = Document.new()
    doc.title = "Recover"
    store = AutoStore(doc, save_path=None)
    store._auto_save()
    assert (tmp_path / "Untitled.sdoc.recover").is_file()


def test_autostore_start_stop(qtbot) -> None:
    doc = Document.new()
    store = AutoStore(doc, save_path=None, interval=1)
    store.start()
    assert store.timer.isActive()
    store.stop()
    assert not store.timer.isActive()


def test_autostore_uses_latest_document_and_custom_recovery(qtbot, tmp_path) -> None:
    original = Document.new()
    latest = Document.new()
    latest.title = "Latest editor state"
    recovery = tmp_path / "recovery" / "Untitled.sdoc.recover"
    store = AutoStore(
        original,
        document_provider=lambda: latest,
        recovery_path=recovery,
    )

    store._auto_save()

    assert store.has_recovery()
    assert store.load_recovery().title == "Latest editor state"
    store.discard_recovery()
    assert not store.has_recovery()


def test_atomic_save_keeps_previous_file_when_replace_fails(
    tmp_path, monkeypatch
) -> None:
    output = tmp_path / "document.sdoc"
    output.write_text("previous valid content", encoding="utf-8")
    document = Document.new()
    document.title = "New content"

    def fail_replace(_source, _target) -> None:
        raise OSError("disk failure")

    monkeypatch.setattr("core.xml_serializer.os.replace", fail_replace)
    with pytest.raises(OSError, match="disk failure"):
        XMLSerializer(document, str(output)).serialize()

    assert output.read_text(encoding="utf-8") == "previous valid content"
    assert list(tmp_path.glob("*.tmp")) == []


def test_autostore_reports_errors_without_raising(qtbot, tmp_path, monkeypatch) -> None:
    errors: list[Exception] = []
    document = Document.new()

    def fail_save(_self, _path) -> None:
        raise OSError("read-only destination")

    monkeypatch.setattr(Document, "save", fail_save)
    store = AutoStore(
        document,
        save_path=str(tmp_path / "document.sdoc"),
        error_handler=errors.append,
    )

    store._auto_save()

    assert isinstance(store.last_error, OSError)
    assert errors == [store.last_error]