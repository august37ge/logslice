"""Tests for logslice.config."""

import json
import os
import pytest

from logslice.config import (
    ConfigError,
    LogSliceConfig,
    load_config,
    _validate,
)


def _write_config(tmp_path, data: dict) -> str:
    p = tmp_path / ".logslice.json"
    p.write_text(json.dumps(data), encoding="utf-8")
    return str(p)


def test_load_config_returns_defaults_when_no_file():
    cfg = load_config(path="/nonexistent/path/logslice.json")
    assert isinstance(cfg, LogSliceConfig)
    assert cfg.format == "plain"
    assert cfg.min_severity is None
    assert cfg.show_stats is False
    assert cfg.append is False


def test_load_config_reads_format(tmp_path):
    path = _write_config(tmp_path, {"format": "json"})
    cfg = load_config(path=path)
    assert cfg.format == "json"


def test_load_config_reads_all_known_fields(tmp_path):
    data = {
        "format": "colored",
        "min_severity": "WARNING",
        "output_file": "out.log",
        "append": True,
        "show_stats": True,
    }
    path = _write_config(tmp_path, data)
    cfg = load_config(path=path)
    assert cfg.format == "colored"
    assert cfg.min_severity == "WARNING"
    assert cfg.output_file == "out.log"
    assert cfg.append is True
    assert cfg.show_stats is True


def test_load_config_stores_unknown_keys_in_extra(tmp_path):
    path = _write_config(tmp_path, {"format": "plain", "my_custom_key": 42})
    cfg = load_config(path=path)
    assert cfg.extra == {"my_custom_key": 42}


def test_load_config_raises_on_invalid_json(tmp_path):
    p = tmp_path / ".logslice.json"
    p.write_text("{not valid json", encoding="utf-8")
    with pytest.raises(ConfigError, match="Cannot parse config file"):
        load_config(path=str(p))


def test_validate_raises_on_bad_format():
    with pytest.raises(ConfigError, match="Invalid format"):
        _validate({"format": "xml"})


def test_validate_raises_on_bad_severity():
    with pytest.raises(ConfigError, match="Invalid min_severity"):
        _validate({"min_severity": "VERBOSE"})


def test_validate_passes_for_valid_values():
    # Should not raise
    _validate({"format": "json", "min_severity": "ERROR"})


def test_load_config_raises_config_error_on_invalid_format_in_file(tmp_path):
    path = _write_config(tmp_path, {"format": "yaml"})
    with pytest.raises(ConfigError):
        load_config(path=path)


def test_load_config_no_path_no_default_file_returns_defaults(monkeypatch):
    """When no default config files exist, return default config."""
    monkeypatch.chdir(tmp := pytest.importorskip("tempfile").mkdtemp())
    cfg = load_config()
    assert cfg.format == "plain"
