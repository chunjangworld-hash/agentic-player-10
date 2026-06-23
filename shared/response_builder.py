"""Tool 응답 마크다운 빌드 + 24k 한계 검사.

PlayMCP 규칙: Response 24,000자 초과 시 에러 → 심사 반려.
우리는 22,000자 안전 한계 (2k 버퍼).
"""
from __future__ import annotations

from typing import Iterable

from shared.config import get_settings
from shared.logging import setup_logger

logger = setup_logger("response_builder")


class ResponseTooLargeError(Exception):
    """ResponseBuilder가 안전하게 truncate하지 못하고 한계 초과 시 발생."""


class ResponseBuilder:
    """우선순위 기반 마크다운 빌더.

    sections: [(content, priority), ...]
    - priority 숫자가 작을수록 중요. 정렬 후 위에서부터 채움.
    - 한계 초과 시 큰 priority(덜 중요)부터 잘림.
    - 잘리면 TRUNCATION_MARKER 자동 삽입.
    """

    TRUNCATION_MARKER = "\n\n_...(이하 생략. 더 자세한 정보가 필요하면 다른 Tool 호출)_"

    def __init__(self, max_chars: int | None = None) -> None:
        self._max = max_chars or get_settings().response_max_chars

    def build(self, sections: Iterable[tuple[str, int]]) -> str:
        sorted_secs = sorted(sections, key=lambda s: s[1])

        out: list[str] = []
        current_len = 0
        truncated = False

        for content, _priority in sorted_secs:
            piece = content + "\n\n"
            if current_len + len(piece) > self._max:
                truncated = True
                break
            out.append(piece)
            current_len += len(piece)

        result = "".join(out).rstrip()
        if truncated:
            result += self.TRUNCATION_MARKER

        if len(result) > self._max + len(self.TRUNCATION_MARKER):
            logger.warning("response_too_large", extra={"length": len(result)})
            raise ResponseTooLargeError(f"Response {len(result)} > {self._max}")

        return result
