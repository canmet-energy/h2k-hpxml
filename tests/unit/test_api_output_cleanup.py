"""Tests for output file handling in api.py."""

from h2k_hpxml.api import _convert_h2k_file_to_hpxml
from h2k_hpxml.api import _write_text_atomically


def test_write_text_atomically_creates_file(tmp_path):
    target = tmp_path / "house" / "house.xml"
    _write_text_atomically(str(target), "<xml/>")

    assert target.read_text(encoding="utf-8") == "<xml/>"


def test_write_text_atomically_overwrites_existing_file(tmp_path):
    target = tmp_path / "house" / "house.xml"
    target.parent.mkdir(parents=True)
    target.write_text("<old/>", encoding="utf-8")

    _write_text_atomically(str(target), "<new/>")

    assert target.read_text(encoding="utf-8") == "<new/>"


def test_convert_h2k_file_overwrites_without_deleting_directory(tmp_path, monkeypatch):
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    house_dir = output_dir / "WizardHouse"
    house_dir.mkdir()
    existing_xml = house_dir / "WizardHouse.xml"
    existing_xml.write_text("<old/>", encoding="utf-8")
    marker = house_dir / "keep-me.txt"
    marker.write_text("stay", encoding="utf-8")

    h2k_file = tmp_path / "WizardHouse.h2k"
    h2k_file.write_text('<?xml version="1.0"?><House></House>', encoding="utf-8")

    monkeypatch.setattr(
        "h2k_hpxml.api._h2ktohpxml",
        lambda _content, _config=None: "<new-hpxml/>",
    )

    result = _convert_h2k_file_to_hpxml(str(h2k_file), str(output_dir))

    assert result == str(existing_xml)
    assert existing_xml.read_text(encoding="utf-8") == "<new-hpxml/>"
    assert marker.read_text(encoding="utf-8") == "stay"
