"""의료/금융/사기 확정 표현에 자동 disclaimer 부착 또는 톤 약화.

⚠️ 외주 #2 시나리오 분석에서 발견된 공통 가드레일.
모든 Tool 응답이 통과해야 안전.
"""
from __future__ import annotations

import re

from shared.logging import setup_logger

logger = setup_logger("safety_filter")


class SafetyFilter:
    MEDICAL_PATTERNS = [
        r"낫(아|을)요?",
        r"나아요",  # "낫다"의 ㅅ불규칙 활용 (낫+아요 → 나아요)
        r"치료(됩니다|된다)",
        r"효과 확실",
        r"부작용 없(어요|음)",
    ]
    FINANCIAL_PATTERNS = [
        r"100% 안전",
        r"확실한 수익",
        r"손실 없",
    ]
    SCAM_CERTAINTY_PATTERNS = [
        r"100% 사기",
        r"확실히 사기",
    ]

    MEDICAL_DISCLAIMER = "\n\n_⚠️ 위 내용은 의료 진단·처방이 아닙니다. 정확한 판단은 의료진과 상담하세요._"
    FINANCIAL_DISCLAIMER = "\n\n_⚠️ 위 내용은 투자 권유가 아닙니다. 금융 의사결정은 본인 판단으로._"
    SCAM_SOFTENER = "\n\n_⚠️ 사기 판단은 참고용입니다. 실제 피해 발생 시 경찰(112)·KISA(118)에 신고하세요._"

    def apply(self, text: str) -> str:
        result = text
        if any(re.search(p, text) for p in self.MEDICAL_PATTERNS):
            result += self.MEDICAL_DISCLAIMER
            logger.info("safety_medical_disclaimer", extra={"length": len(text)})
        if any(re.search(p, text) for p in self.FINANCIAL_PATTERNS):
            result += self.FINANCIAL_DISCLAIMER
            logger.info("safety_financial_disclaimer", extra={"length": len(text)})
        if any(re.search(p, text) for p in self.SCAM_CERTAINTY_PATTERNS):
            result += self.SCAM_SOFTENER
            logger.info("safety_scam_softener", extra={"length": len(text)})
        return result
