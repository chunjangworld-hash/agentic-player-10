"""사전 통합 스크립트 — v1 + GPT v2 + Gemini v2를 합치고 중복 제거.

사용: python scripts/merge_dictionaries.py
효과: docs/data/ad_keywords.json + positive_signals.json 갱신.
원칙: False positive 방어 — 두 소스 confidence가 다르면 더 보수적(낮은) 등급 채택.
"""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

# Windows console UTF-8 강제
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

CONF_ORDER = {"약": 1, "중": 2, "강": 3}


def more_conservative(a: str, b: str) -> str:
    return a if CONF_ORDER[a] <= CONF_ORDER[b] else b


def merge_category(*sources):
    merged: dict[str, str] = {}
    for src in sources:
        for entry in src:
            kw = entry["keyword"]
            conf = entry["confidence"]
            merged[kw] = more_conservative(merged[kw], conf) if kw in merged else conf
    return sorted(
        [{"keyword": k, "confidence": v} for k, v in merged.items()],
        key=lambda x: (-CONF_ORDER[x["confidence"]], x["keyword"]),
    )


# ────────────────────────── AD KEYWORDS ──────────────────────────
ad_v1 = json.loads(Path("docs/data/ad_keywords.json").read_text(encoding="utf-8"))

AD_GPT_V2 = {
    "explicit_ad": [
        {"keyword": "광고입니다", "confidence": "강"},
        {"keyword": "본 게시물은 광고입니다", "confidence": "강"},
        {"keyword": "광고 포함 게시물", "confidence": "강"},
        {"keyword": "유료 광고 콘텐츠", "confidence": "강"},
        {"keyword": "제휴 광고", "confidence": "강"},
        {"keyword": "협찬 광고", "confidence": "강"},
        {"keyword": "브랜드 콘텐츠", "confidence": "중"},
        {"keyword": "스폰서드", "confidence": "중"},
        {"keyword": "#sponsored", "confidence": "중"},
        {"keyword": "#스폰서드", "confidence": "중"},
        {"keyword": "paid partnership", "confidence": "중"},
    ],
    "experience_team": [
        {"keyword": "체험단 선정", "confidence": "강"},
        {"keyword": "리뷰어 선정", "confidence": "강"},
        {"keyword": "리뷰어 활동", "confidence": "강"},
        {"keyword": "서포터즈 활동", "confidence": "강"},
        {"keyword": "브랜드 앰버서더", "confidence": "강"},
        {"keyword": "앰버서더 활동", "confidence": "강"},
        {"keyword": "캠페인 참여", "confidence": "중"},
        {"keyword": "포스팅 미션", "confidence": "강"},
        {"keyword": "리뷰 미션", "confidence": "강"},
        {"keyword": "제품 체험 기회", "confidence": "중"},
        {"keyword": "체험권 제공", "confidence": "강"},
    ],
    "group_buy": [
        {"keyword": "공구 링크", "confidence": "강"},
        {"keyword": "공구가", "confidence": "강"},
        {"keyword": "공구 문의", "confidence": "중"},
        {"keyword": "공구방", "confidence": "중"},
        {"keyword": "오픈채팅 공구", "confidence": "강"},
        {"keyword": "댓글 공구", "confidence": "중"},
        {"keyword": "DM 공구", "confidence": "중"},
        {"keyword": "공구 참여", "confidence": "중"},
        {"keyword": "공구 마감 임박", "confidence": "중"},
        {"keyword": "프로필 링크에서 구매", "confidence": "중"},
        {"keyword": "오늘만 공구가", "confidence": "강"},
    ],
    "sponsorship_disclosure": [
        {"keyword": "제품을 제공받아 작성했습니다", "confidence": "강"},
        {"keyword": "서비스를 제공받아 작성했습니다", "confidence": "강"},
        {"keyword": "무상으로 제공받았습니다", "confidence": "강"},
        {"keyword": "무료 체험권을 제공받았습니다", "confidence": "강"},
        {"keyword": "제작비를 지원받았습니다", "confidence": "강"},
        {"keyword": "금전적 지원을 받았습니다", "confidence": "강"},
        {"keyword": "소정의 수수료를 지급받습니다", "confidence": "강"},
        {"keyword": "구매 시 수수료를 받을 수 있습니다", "confidence": "강"},
        {"keyword": "파트너스 활동을 통해 수수료를 제공받습니다", "confidence": "강"},
        {"keyword": "브랜드로부터 협찬을 받았습니다", "confidence": "강"},
        {"keyword": "업체 지원으로 작성했습니다", "confidence": "강"},
    ],
    "implicit_signals": [
        {"keyword": "본문 끝부분에만 광고 표기", "confidence": "중"},
        {"keyword": "해시태그 사이에 광고 표기 숨김", "confidence": "중"},
        {"keyword": "더보기 아래에 협찬 표시", "confidence": "중"},
        {"keyword": "영상 중간 짧은 협찬 자막만 노출", "confidence": "중"},
        {"keyword": "브랜드명 반복 언급", "confidence": "약"},
        {"keyword": "구매 링크가 댓글 고정", "confidence": "중"},
        {"keyword": "쿠폰코드와 구매 링크 동시 제공", "confidence": "강"},
        {"keyword": "동일 제품 새상품을 당근에 반복 등록", "confidence": "중"},
        {"keyword": "중고 플랫폼에서 판매자 상품 라인업이 과도하게 유사", "confidence": "중"},
        {"keyword": "사용 후기 없이 판매 링크만 강조", "confidence": "중"},
        {"keyword": "뒷광고 아님을 과하게 강조", "confidence": "약"},
    ],
}

AD_GEMINI_V2 = {
    "explicit_ad": [
        {"keyword": "#paidpartnership", "confidence": "강"},
        {"keyword": "#유료파트너십", "confidence": "강"},
        {"keyword": "Paid partnership", "confidence": "강"},
        {"keyword": "쿠팡 파트너스 활동의 일환", "confidence": "강"},
        {"keyword": "일정액의 수수료를 제공받습니다", "confidence": "강"},
        {"keyword": "제휴마케팅의 일환으로", "confidence": "강"},
        {"keyword": "#소정의수수료", "confidence": "강"},
        {"keyword": "이 영상은 유료 광고를 포함하고 있습니다", "confidence": "강"},
        {"keyword": "#브랜드협업", "confidence": "중"},
        {"keyword": "#PaidAd", "confidence": "강"},
    ],
    "experience_team": [
        {"keyword": "블로그체험단", "confidence": "중"},
        {"keyword": "인스타체험단", "confidence": "중"},
        {"keyword": "얼리버드 리뷰어", "confidence": "중"},
        {"keyword": "무상으로 지원받아 작성된", "confidence": "강"},
        {"keyword": "체험단에 선정되어", "confidence": "강"},
        {"keyword": "서비스를 무상 제공받았으나", "confidence": "강"},
        {"keyword": "품평단 참여", "confidence": "중"},
        {"keyword": "신제품 피드백용으로", "confidence": "중"},
        {"keyword": "리뷰이벤트 참여", "confidence": "중"},
    ],
    "group_buy": [
        {"keyword": "최저가 공구 오픈", "confidence": "강"},
        {"keyword": "프로필 링크트리 클릭", "confidence": "중"},
        {"keyword": "스토리 하이라이트에 링크", "confidence": "중"},
        {"keyword": "DM 주시면 링크", "confidence": "중"},
        {"keyword": "단독 특가 앵콜", "confidence": "중"},
        {"keyword": "공동구매 진행합니다", "confidence": "강"},
        {"keyword": "비밀댓글로 링크 공유", "confidence": "약"},
        {"keyword": "공구 마켓 오픈", "confidence": "강"},
        {"keyword": "한정 수량 마감 임박", "confidence": "약"},
    ],
    "sponsorship_disclosure": [
        {"keyword": "제작비 지원", "confidence": "강"},
        {"keyword": "업체로부터 제품 지원", "confidence": "강"},
        {"keyword": "브랜드 기프트로 제공받은", "confidence": "강"},
        {"keyword": "단순 협찬 제품입니다", "confidence": "강"},
        {"keyword": "콘텐츠 제작 협찬", "confidence": "강"},
        {"keyword": "대여 및 소정의 원고료", "confidence": "강"},
        {"keyword": "행사에 초청받아 제품을 제공", "confidence": "강"},
        {"keyword": "기프트로 받아서 써봄", "confidence": "중"},
        {"keyword": "브랜드 협찬을 받아", "confidence": "강"},
    ],
    "implicit_signals": [
        {"keyword": "뒷광고 아님", "confidence": "약"},
        {"keyword": "내돈내산은 아니고 친한 지인이", "confidence": "약"},
        {"keyword": "당근 이웃분들께만 공유하는 꿀팁", "confidence": "약"},
        {"keyword": "제가 아는 사장님이 직접", "confidence": "약"},
        {"keyword": "속는 셈 치고 샀는데", "confidence": "약"},
        {"keyword": "제품 정보는 프로필 링크에", "confidence": "중"},
        {"keyword": "협찬은 맞지만 솔직하게", "confidence": "중"},
        {"keyword": "댓글 달아주시면 좌표 공유", "confidence": "약"},
        {"keyword": "더보기란 링크 참조", "confidence": "중"},
        {"keyword": "소문듣고 찾아간 업체", "confidence": "약"},
    ],
}

AD_CATEGORIES = ["explicit_ad", "experience_team", "group_buy", "sponsorship_disclosure", "implicit_signals"]
merged_ad = {
    cat: merge_category(ad_v1.get(cat, []), AD_GPT_V2.get(cat, []), AD_GEMINI_V2.get(cat, []))
    for cat in AD_CATEGORIES
}
ad_total = sum(len(merged_ad[cat]) for cat in AD_CATEGORIES)

ad_v2_out = {
    "_meta": {
        "purpose": "광고/협찬/체험단 식별 키워드 마스터 목록. shared/ad_filter.py의 F1 룰셋에 사용.",
        "source": "v1 (2026-06-22 GPT) + v2 (2026-06-23 GPT-5 + Gemini 외주 합본, 중복 제거 + 보수적 등급 채택)",
        "version": "v2",
        "categories": 5,
        "total_keywords": ad_total,
        "confidence_levels": "강 / 중 / 약 — 강은 거의 확실한 광고 신호, 약은 보조 신호",
        "usage": "각 검색 결과 텍스트에 대해 모든 키워드를 검사. 매칭 시 confidence에 따라 가중치 부여 후 제거 결정",
        "philosophy": "False positive 방어 — 두 소스에서 confidence가 다르면 더 낮은(보수적) 등급 채택",
    },
    **merged_ad,
}

Path("docs/data/ad_keywords.json").write_text(
    json.dumps(ad_v2_out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
)
print(f"[ad_keywords] v2 작성 완료 - 총 {ad_total} 키워드")
for cat in AD_CATEGORIES:
    print(f"  {cat}: {len(merged_ad[cat])}")


# ────────────────────────── POSITIVE SIGNALS ──────────────────────────
pos_v1 = json.loads(Path("docs/data/positive_signals.json").read_text(encoding="utf-8"))

POS_GPT_V2 = {
    "purchase_proof": [
        {"keyword": "실물 영수증 같이 올립니다", "confidence": "강"},
        {"keyword": "카드 결제 문자 인증", "confidence": "강"},
        {"keyword": "구매일자 보이게 캡처", "confidence": "강"},
        {"keyword": "배송완료 내역 첨부", "confidence": "강"},
        {"keyword": "반품 기간 지나고 쓰는 후기", "confidence": "강"},
        {"keyword": "제 주문번호는 가렸어요", "confidence": "강"},
        {"keyword": "당근에서 직접 거래한 물건", "confidence": "중"},
        {"keyword": "중고로 사서 써봤어요", "confidence": "중"},
        {"keyword": "제가 쓰던 거 재구매했어요", "confidence": "강"},
        {"keyword": "가격 비교하다가 직접 샀어요", "confidence": "중"},
        {"keyword": "내돈내산 인증샷", "confidence": "중"},
    ],
    "third_party_reaction": [
        {"keyword": "엄마가 먼저 또 사달라고 하셨어요", "confidence": "강"},
        {"keyword": "아빠가 매일 쓰세요", "confidence": "강"},
        {"keyword": "부모님이 직접 고르신 제품", "confidence": "강"},
        {"keyword": "받으신 분이 바로 사용하셨어요", "confidence": "중"},
        {"keyword": "식구들이 다 한 번씩 써봤어요", "confidence": "중"},
        {"keyword": "친정엄마도 같은 걸로 사달라셨어요", "confidence": "강"},
        {"keyword": "시어머니가 부담스럽지 않다고 하셨어요", "confidence": "중"},
        {"keyword": "아이가 할머니 선물이라고 골랐어요", "confidence": "중"},
        {"keyword": "주변 어른들이 제품명을 물어보셨어요", "confidence": "중"},
        {"keyword": "부모님이 기존 것보다 편하다고 하셨어요", "confidence": "강"},
        {"keyword": "가족 단톡방에서 반응 좋았어요", "confidence": "중"},
    ],
    "repurchase_recommendation": [
        {"keyword": "이번에 같은 걸로 다시 샀어요", "confidence": "강"},
        {"keyword": "부모님 집에도 하나 더 보냈어요", "confidence": "강"},
        {"keyword": "다 쓰기도 전에 재주문했어요", "confidence": "강"},
        {"keyword": "계속 이 제품만 사요", "confidence": "중"},
        {"keyword": "명절마다 이걸로 정착했어요", "confidence": "강"},
        {"keyword": "다음 생신에도 이 브랜드로 할 듯", "confidence": "중"},
        {"keyword": "동생한테도 추천했어요", "confidence": "중"},
        {"keyword": "부모님 선물 리스트에 저장해뒀어요", "confidence": "중"},
        {"keyword": "여러 개 사서 나눠드렸어요", "confidence": "중"},
        {"keyword": "가격 오르기 전에 또 살 생각", "confidence": "중"},
        {"keyword": "재구매 의사 있어요", "confidence": "약"},
    ],
    "emotion_expression": [
        {"keyword": "기대보다 오래 쓰고 있어요", "confidence": "강"},
        {"keyword": "단점까지 감안해도 만족", "confidence": "강"},
        {"keyword": "돈값은 하는 것 같아요", "confidence": "중"},
        {"keyword": "광고처럼 보일까 봐 조심스럽지만", "confidence": "약"},
        {"keyword": "과장 없이 괜찮았어요", "confidence": "중"},
        {"keyword": "완벽하진 않은데 손이 자주 가요", "confidence": "강"},
        {"keyword": "처음엔 별로였는데 계속 쓰게 돼요", "confidence": "강"},
        {"keyword": "부담 없는 가격이라 만족", "confidence": "중"},
        {"keyword": "선물하고 민망하지 않았어요", "confidence": "중"},
        {"keyword": "찐으로 잘 샀다 싶어요", "confidence": "약"},
        {"keyword": "솔직후기입니다", "confidence": "약"},
    ],
    "daily_usage_pattern": [
        {"keyword": "세탁 여러 번 해보고 남겨요", "confidence": "강"},
        {"keyword": "한 계절 써본 후기", "confidence": "강"},
        {"keyword": "부모님 댁에 두고 계속 쓰는 중", "confidence": "강"},
        {"keyword": "매일 아침 사용 중", "confidence": "중"},
        {"keyword": "주말마다 꺼내 써요", "confidence": "중"},
        {"keyword": "장 보러 갈 때마다 들고 가요", "confidence": "중"},
        {"keyword": "병원 갈 때 챙겨가세요", "confidence": "중"},
        {"keyword": "여행 갈 때 꼭 챙겼어요", "confidence": "중"},
        {"keyword": "부엌에 놓고 계속 쓰세요", "confidence": "중"},
        {"keyword": "침대 옆에 두고 쓰는 중", "confidence": "중"},
        {"keyword": "사용감 생길 만큼 썼어요", "confidence": "강"},
    ],
}

POS_GEMINI_V2 = {
    "purchase_proof": [
        {"keyword": "영수증 첨부합니다", "confidence": "강"},
        {"keyword": "카드 내역 캡처", "confidence": "강"},
        {"keyword": "배송조회 화면 인증", "confidence": "강"},
        {"keyword": "예약 내역 인증", "confidence": "강"},
        {"keyword": "내돈내산 인증", "confidence": "약"},
        {"keyword": "찐후기", "confidence": "약"},
        {"keyword": "솔직후기", "confidence": "약"},
        {"keyword": "제 돈 주고 산 영수증", "confidence": "강"},
        {"keyword": "카카오 선물하기 주문 내역", "confidence": "강"},
        {"keyword": "쿠팡 로켓배송 구매내역", "confidence": "강"},
    ],
    "third_party_reaction": [
        {"keyword": "엄마 카톡 프로필 사진 바뀜", "confidence": "강"},
        {"keyword": "아빠가 동네방네 자랑하심", "confidence": "강"},
        {"keyword": "시어머니가 친구분들한테 자랑하셨대요", "confidence": "강"},
        {"keyword": "돈 아깝게 뭘 이런 걸 샀냐더니 매일 쓰심", "confidence": "강"},
        {"keyword": "남편이 자기도 사달라고 난리", "confidence": "중"},
        {"keyword": "친척들이 어디서 샀냐고 물어봄", "confidence": "중"},
        {"keyword": "엄마가 친구분들 공구해 달라고 난리심", "confidence": "강"},
        {"keyword": "부모님이 너무 고맙다고 카톡 오심", "confidence": "중"},
        {"keyword": "시댁 어르신들이 다들 칭찬하심", "confidence": "중"},
    ],
    "repurchase_recommendation": [
        {"keyword": "재구매만 벌써 세 번째", "confidence": "강"},
        {"keyword": "이번 명절에도 이걸로 고정", "confidence": "중"},
        {"keyword": "주변에 무조건 사라고 영업 중", "confidence": "약"},
        {"keyword": "지인 선물용으로 추가 구매함", "confidence": "강"},
        {"keyword": "쟁여두고 쓰는 템", "confidence": "중"},
        {"keyword": "다음 부모님 생신 때도 이거 할 듯", "confidence": "중"},
        {"keyword": "인생템 등극", "confidence": "약"},
        {"keyword": "돈이 안 아까운 제품", "confidence": "중"},
        {"keyword": "정착템 찾았네요", "confidence": "약"},
    ],
    "emotion_expression": [
        {"keyword": "엄마 우는 모습 보고 울컥함", "confidence": "강"},
        {"keyword": "효도한 것 같아 마음이 뿌듯", "confidence": "중"},
        {"keyword": "부모님 좋아하시는 모습 보니 눈물 남", "confidence": "중"},
        {"keyword": "돈 쓴 보람이 있네요", "confidence": "중"},
        {"keyword": "진짜 대대대만족", "confidence": "약"},
        {"keyword": "이 가격에 이 퀄리티라니 감동", "confidence": "약"},
        {"keyword": "안 샀으면 평생 후회할 뻔", "confidence": "약"},
        {"keyword": "마음이 뭉클하네요", "confidence": "중"},
    ],
    "daily_usage_pattern": [
        {"keyword": "매일 아침마다 쓰고 계심", "confidence": "강"},
        {"keyword": "침대 머리맡에 두고 주무심", "confidence": "강"},
        {"keyword": "외출할 때 무조건 챙겨 나가심", "confidence": "강"},
        {"keyword": "식탁 위에 항상 올려져 있음", "confidence": "강"},
        {"keyword": "벌써 한 통 다 비워감", "confidence": "강"},
        {"keyword": "매일 저녁 퇴근하고 가보면 쓰고 계심", "confidence": "강"},
        {"keyword": "닳고 닳아서 구멍 날 때까지", "confidence": "중"},
        {"keyword": "손에서 놓지를 않으시네요", "confidence": "중"},
        {"keyword": "일주일째 24시간 풀가동 중", "confidence": "중"},
    ],
}

POS_CATEGORIES = ["purchase_proof", "third_party_reaction", "repurchase_recommendation", "emotion_expression", "daily_usage_pattern"]
merged_pos = {
    cat: merge_category(pos_v1.get(cat, []), POS_GPT_V2.get(cat, []), POS_GEMINI_V2.get(cat, []))
    for cat in POS_CATEGORIES
}
pos_total = sum(len(merged_pos[cat]) for cat in POS_CATEGORIES)

pos_v2_out = {
    "_meta": {
        "purpose": "진짜 만족 후기일 가능성을 높이는 양성 신호 키워드. shared/positive_signals.py의 F2 룰셋에 사용.",
        "source": "v1 (2026-06-23 사용자 직접 작성) + v2 (2026-06-23 GPT-5 + Gemini 외주 합본, 중복 제거 + 보수적 등급 채택)",
        "version": "v2",
        "categories": 5,
        "total_keywords": pos_total,
        "confidence_levels": "강 / 중 / 약 — 강은 광고에서 사용 어려운 행동/증빙 표현, 약은 뒷광고도 사용하는 방어 문구",
        "philosophy": "단일 강 신호 < 조합. 구매증빙 + 장기사용 + 단점언급 + 재구매 동시 만족 = 가장 신뢰. '내돈내산' 같은 양날 키워드는 약 등급으로 단독 가중치 최소화.",
        "false_positive_defense": "두 외주 소스에서 confidence가 다르면 보수적(낮은) 등급 채택. 광고가 양성으로 오판될 위험 최소화.",
    },
    **merged_pos,
}

Path("docs/data/positive_signals.json").write_text(
    json.dumps(pos_v2_out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
)
print(f"\n[positive_signals] v2 작성 완료 - 총 {pos_total} 키워드")
for cat in POS_CATEGORIES:
    print(f"  {cat}: {len(merged_pos[cat])}")

# servers/gift_curator/data/ 사본 동기화
import shutil
shutil.copy("docs/data/ad_keywords.json", "servers/gift_curator/data/ad_keywords.json")
shutil.copy("docs/data/positive_signals.json", "servers/gift_curator/data/positive_signals.json")
print("\nservers/gift_curator/data/ 사본 동기화 완료")
