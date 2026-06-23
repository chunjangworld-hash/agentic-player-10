import json
import logging

import pytest

from shared.logging import setup_logger


@pytest.fixture(autouse=True)
def _clear_settings_cache():
    from shared.config import get_settings
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_setup_logger_returns_logger():
    logger = setup_logger("test_service")
    assert isinstance(logger, logging.Logger)
    assert logger.name == "test_service"


def test_logger_uses_configured_level(monkeypatch):
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")
    from shared.config import get_settings
    get_settings.cache_clear()

    logger = setup_logger("test_service_debug")
    assert logger.level == logging.DEBUG


def test_logger_outputs_json_format(capsys):
    # propagate=False 로거라 caplog 대신 실제 stdout 검사. JSON 포맷 자체를 검증.
    logger = setup_logger("test_service_json")
    logger.info("test_message", extra={"tool": "compose_anbu", "duration_ms": 42})

    captured = capsys.readouterr()
    payload = json.loads(captured.out.strip().splitlines()[-1])
    assert payload["message"] == "test_message"
    assert payload["level"] == "INFO"
    assert payload["logger"] == "test_service_json"
    assert payload["tool"] == "compose_anbu"
    assert payload["duration_ms"] == 42
    assert "time" in payload
