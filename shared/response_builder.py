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

    def build(
        self,
        sections: Iterable[tuple[str, int]],
        *,
        mandatory_footer: str | None = None,
    ) -> str:
        """
        mandatory_footer: 약관·법적 의무 표기 (예: '네이버 검색 기반').
                          본문이 truncate돼도 항상 마지막에 부착됨.
                          max_chars 안에 footer 자리가 미리 확보됨.
        """
        footer_text = f"\n\n{mandatory_footer}" if mandatory_footer else ""
        # 본문이 사용할 수 있는 한도 = 전체 한도 - footer - truncation marker 여유
        body_budget = self._max - len(footer_text)
        if body_budget < 0:
            raise ResponseTooLargeError(
                f"mandatory_footer({len(footer_text)}) > max_chars({self._max})"
            )

        sorted_secs = sorted(sections, key=lambda s: s[1])

        out: list[str] = []
        current_len = 0
        truncated = False

        for content, _priority in sorted_secs:
            piece = content + "\n\n"
            if current_len + len(piece) > body_budget:
                truncated = True
                break
            out.append(piece)
            current_len += len(piece)

        result = "".join(out).rstrip()
        if truncated:
            # truncation marker도 body_budget 안에 들어가야 안전
            if len(result) + len(self.TRUNCATION_MARKER) > body_budget:
                # marker가 들어갈 자리도 없으면 본문 더 줄임
                result = result[: max(0, body_budget - len(self.TRUNCATION_MARKER))].rstrip()
            result += self.TRUNCATION_MARKER

        result += footer_text

        if len(result) > self._max + len(self.TRUNCATION_MARKER):
            logger.warning("response_too_large", extra={"length": len(result)})
            raise ResponseTooLargeError(f"Response {len(result)} > {self._max}")

        return result
