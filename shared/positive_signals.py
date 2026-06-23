"""F2 — 진짜 만족 후기일 가능성을 높이는 양성 신호 스코어링.

⚠️ 공정위 기준 — '비광고 확정' 도구가 아니라 *진짜 만족 가능성*을 점수화하는 보조 신호.
   AdFilter(F1)가 먼저 광고를 제거한 후, 남은 후보에 PositiveSignalScorer를 적용.

스코어링 철학:
  - 단일 강 신호 < 여러 카테고리의 조합 (사용자가 강조한 도메인 인사이트)
  - 같은 카테고리 안에서 키워드 여러 개 매치해도 카테고리 hit = 1 (스터핑 방어)
  - '내돈내산' 등 약 등급은 뒷광고의 방어 문구이기도 함 → 보조 신호로만 작동

수식:
  base = n_categories * (n_categories + 1) // 2  (삼각수: 1→1, 2→3, 3→6, 4→10)
  weak_bonus = min(weak_signal_count, 3) * 0.3
  score = base + weak_bonus
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from shared.logging import setup_logger

logger = setup_logger("positive_signals")

_DEFAULT_SIGNALS_PATH = (
    Path(__file__).resolve().parent.parent / "docs" / "data" / "positive_signals.json"
)


class PositiveSignalScorer:
    """양성 신호 스코어러 — F2."""

    def __init__(self, signals_path: Path | None = None) -> None:
        path = signals_path or _DEFAULT_SIGNALS_PATH
        with open(path, encoding="utf-8") as fp:
            data = json.load(fp)

        # _meta 제외하고 카테고리만
        self._by_category: dict[str, list[dict[str, str]]] = {
            cat: entries
            for cat, entries in data.items()
            if not cat.startswith("_") and isinstance(entries, list)
        }

    @staticmethod
    def _matches(keyword: str, text_lower: str) -> bool:
        """'+' 는 AND. 'A + B'는 A와 B 둘 다 substring으로 존재해야 매치."""
        if " + " in keyword:
            parts = [p.strip().lower() for p in keyword.split("+")]
            return all(p in text_lower for p in parts)
        return keyword.lower() in text_lower

    def score(self, text: str) -> dict[str, Any]:
        """텍스트의 양성 신호 점수."""
        if not text:
            return {"score": 0, "category_count": 0, "categories": [], "weak_signal_count": 0}

        text_lower = text.lower()
        categories_hit: set[str] = set()
        weak_count = 0

        for cat, entries in self._by_category.items():
            for entry in entries:
                kw = entry["keyword"]
                conf = entry.get("confidence", "약")
                if not self._matches(kw, text_lower):
                    continue
                if conf in ("강", "중"):
                    categories_hit.add(cat)
                    # 같은 카테고리는 한 번만 카운트 — 스터핑 방어
                    # 단 약 신호는 별도 카운트 위해 계속 순회
                else:  # 약
                    weak_count += 1

        n = len(categories_hit)
        base = n * (n + 1) // 2 if n > 0 else 0
        weak_bonus = round(min(weak_count, 3) * 0.3, 2)
        total = base + weak_bonus

        return {
            "score": total,
            "category_count": n,
            "categories": sorted(categories_hit),
            "weak_signal_count": weak_count,
        }

    def assess_items(self, items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """각 item에 _positive_score를 부착해 반환 (원본 보존, 새 dict)."""
        out = []
        for item in items:
            combined = " ".join(
                str(item.get(f, "")) for f in ("title", "description", "content", "snippet")
            )
            scored = dict(item)
            scored["_positive_score"] = self.score(combined)
            out.append(scored)
        logger.info("positive_signal_assessed", extra={"count": len(items)})
        return out
