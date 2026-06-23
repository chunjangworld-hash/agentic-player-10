"""광고/협찬 필터링 — F1 (명시 키워드) + F4 (다중 출처 교차 검증).

⚠️ False negative > False positive — 의심스러우면 제거.
LLM 분류는 호출 에이전트에 위임. 우리는 룰 기반만 — 빠르고 결정적.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from shared.logging import setup_logger

logger = setup_logger("ad_filter")

_DEFAULT_KEYWORDS_PATH = (
    Path(__file__).resolve().parent.parent / "docs" / "data" / "ad_keywords.json"
)


class AdFilter:
    """F1 키워드 매칭 + F4 다중 출처 검증.

    confidence 등급(강/중/약) 중 강+중만 사용. 약은 false positive 위험.
    """

    _USED_CATEGORIES = (
        "explicit_ad",
        "experience_team",
        "group_buy",
        "sponsorship_disclosure",
    )

    def __init__(self, keywords_path: Path | None = None) -> None:
        path = keywords_path or _DEFAULT_KEYWORDS_PATH
        with open(path, encoding="utf-8") as fp:
            data = json.load(fp)

        self._keywords: list[str] = []
        for category in self._USED_CATEGORIES:
            for entry in data.get(category, []):
                if entry.get("confidence") in ("강", "중"):
                    self._keywords.append(entry["keyword"])

    def is_ad(self, text: str) -> bool:
        """텍스트에 광고 키워드 매칭이 있는지 (대소문자 무시)."""
        if not text:
            return False
        lowered = text.lower()
        return any(kw.lower() in lowered for kw in self._keywords)

    def filter_items(self, items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """검색 결과 리스트에서 광고 항목 제거."""
        clean = []
        for item in items:
            combined = " ".join(
                str(item.get(f, "")) for f in ("title", "description", "content", "snippet")
            )
            if not self.is_ad(combined):
                clean.append(item)
        logger.info("ad_filter_applied", extra={"input": len(items), "output": len(clean)})
        return clean

    def aggregate_by_source(
        self, items: list[dict[str, Any]], keyword: str
    ) -> dict[str, Any]:
        """F4 — 같은 키워드가 여러 출처(도메인)에 등장 → 신뢰도 점수.

        trust_score = 고유 도메인 수. 단일 출처보다 다중 출처가 높음.
        sentiment 분리는 호출 에이전트(LLM) 담당 — 여기선 단순 mention 카운트.
        """
        domains: set[str] = set()
        mentions = 0
        lowered_kw = keyword.lower()
        for item in items:
            link = item.get("link") or item.get("url") or ""
            combined = " ".join(
                str(item.get(f, "")) for f in ("title", "description", "content")
            )
            if lowered_kw in combined.lower():
                mentions += 1
                if link:
                    domain = urlparse(link).netloc
                    if domain:
                        domains.add(domain)

        return {
            "unique_sources": len(domains),
            "total_mentions": mentions,
            "trust_score": len(domains),
            "domains": sorted(domains),
        }
