"""표준 로깅 설정 — JSON 친화적 포맷, 카카오클라우드 로그 수집 호환."""
from __future__ import annotations

import json
import logging
import sys
from typing import Any

from shared.config import get_settings


_RESERVED_RECORD_ATTRS = frozenset({
    "args", "asctime", "created", "exc_info", "exc_text", "filename",
    "funcName", "levelname", "levelno", "lineno", "message", "module",
    "msecs", "msg", "name", "pathname", "process", "processName",
    "relativeCreated", "stack_info", "thread", "threadName", "taskName",
})


class JsonFormatter(logging.Formatter):
    """간단한 JSON 포맷터. 카카오클라우드 로그 수집 친화."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "time": self.formatTime(record, datefmt="%Y-%m-%dT%H:%M:%S"),
        }
        for key, value in record.__dict__.items():
            if key not in _RESERVED_RECORD_ATTRS:
                payload[key] = value
        return json.dumps(payload, ensure_ascii=False)


def setup_logger(name: str) -> logging.Logger:
    """이름별 로거 생성. 같은 이름 호출 시 같은 객체 반환 (idempotent)."""
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    settings = get_settings()
    logger.setLevel(getattr(logging, settings.log_level.upper(), logging.INFO))

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    logger.addHandler(handler)
    logger.propagate = False

    return logger
