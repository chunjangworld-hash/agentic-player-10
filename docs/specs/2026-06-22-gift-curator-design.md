# Gift Curator (선물고민러) — Design Spec

**작성일**: 2026-06-22
**MCP 서비스명**: `Gift Curator(선물고민러)`
**Tool 개수**: 5개
**상위 문서**: [2026-06-22-architecture-overview.md](./2026-06-22-architecture-overview.md)

---

## 1. 개요

### 1.1 한 줄 요약

광고·협찬으로 오염되지 않은 외부 후기를 큐레이션해, 사용자가 받는 사람에게 진짜로 어울리는 카카오 선물하기 키워드/가격대/메시지 카드를 제안. 카카오 선물하기 MCP의 `SearchGift`/`GetTrendingGiftRanking`/`GetRecentGiftOrderHistory`와 자연스럽게 연계.

### 1.2 차별점 (PlayMCP 심사 정당화)

| 차별 요소 | LLM 단독 불가 이유 |
|---|---|
| **광고 필터링 (F1+F4 룰 기반)** | 협찬/체험단/공동구매 패턴을 룰 기반으로 사전 제거 (LLM 일반 웹 검색은 광고 구분 X) |
| **카카오 선물하기 카탈로그 통합** | `SearchGift` 호출용 query/minPrice/maxPrice/customTags 생성 (카카오 MCP만 가능) |
| **사용자 최근 선물 자동 회피** | `GetRecentGiftOrderHistory` 결과 활용 (사용자 카카오 데이터, LLM 접근 불가) |
| **트렌드 차별화 시그널** | `GetTrendingGiftRanking` 비교로 "남들 다 사는 것 vs 특별한 선택" 명시 |
| **외부 후기 집계 + 신뢰도 점수** | 네이버 블로그/카페·Tavily 다중 출처 + F4 교차 검증 (LLM 단독 검색은 신뢰도 평가 X) |
| **응답 시간 100ms 보장** | LLM 호출 없이 외부 API + 룰 기반만 |

### 1.3 타깃 사용자

- **1차**: 20~40대 카카오톡 사용자
- **사용 시나리오 범위**: 효도 선물 / 친구·연인 / 사회생활 / 축의 / 사과·위로
- **사용 빈도**: 행사·계기마다 (월 1~2회 평균)

### 1.4 첫 화면 — 자유 입력 + 가이드 예시

```
┌─────────────────────────────────────────┐
│ 🎁 선물고민러                              │
│ 광고 없는 진짜 추천만 골라드려요              │
│                                          │
│ 누구에게 선물할까요?                        │
│ ┌──────────────────────────────────┐    │
│ │ 자유롭게 적어주세요               │    │
│ └──────────────────────────────────┘    │
│                                          │
│ 💡 이렇게 적어보세요:                       │
│   • "엄마 환갑 20만 원 이내"                │
│   • "친구 결혼 축의금 외 작은 선물 5만"      │
│   • "팀장님 승진 축하 5만 원대"             │
│                                          │
│ 💬 이미 후보 있으세요? "OO 어때?" 평가도 가능 │
└─────────────────────────────────────────┘
```

---

## 2. 사용자 시나리오

### 시나리오 G1 — 메인 큐레이션 (가장 자주)

```
사용자: "엄마 환갑 20만 원 이내. 등산 시작하셨고 허리 조금 안 좋음"
  ↓
[선물고민러: curate_gifts 호출]
  → 입력 파싱: 관계=엄마, 행사=환갑, 예산=~20만, 컨텍스트=등산+허리
  → 네이버 검색 ("60대 엄마 환갑 선물 등산"), Tavily 보강
  → F1+F4 광고 필터 (협찬·체험단·공동구매 제거)
  → 외부 후기 집계 + 신뢰도 점수
  → 후보 3개 (실용/감성/특별 톤 분리) + SearchGift 파라미터 + 광고X 검증 정보
  ↓
[호출 에이전트: 마크다운 결과 → 자녀에게 자연어 추천]
[에이전트가 SearchGift 자동 호출 — 카카오 도구함이 조율]
  → 사용자 화면에 실제 제품 카드 표시
  ↓
사용자: 마음에 드는 거 선택 → 카카오 선물하기 앱에서 구매
```

### 시나리오 G2 — 자문 모드

```
사용자: "엄마 환갑인데 마사지건 13만 원 어때?"
  ↓
[선물고민러: evaluate_gift_idea 호출]
  → 사용자가 가져온 후보(마사지건)에 대한 외부 후기 검색
  → F1+F4 필터링
  → 가격 적정성 데이터 (60대 환갑 선물 일반 가격대 비교)
  → 적합도/강점/약점 시그널
  → 대안 후보 1~2개
  ↓
[호출 에이전트: 종합 평가 + 자연어 의견]
```

### 시나리오 G3 — 재추천

```
사용자: "방금 추천 너무 비싸, 다른 거"
  ↓
[선물고민러: refine_recommendation 호출 with feedback="너무 비쌈"]
  → feedback 파싱 → 새 예산대로 재검색
  → 다른 카테고리/가격대 후보 3개
  ↓
[에이전트가 결과 전달]
```

### 시나리오 G4 — 메시지 카드 단독

```
사용자: "이미 선물 정했는데 메시지만 좀 써줘. 엄마 환갑, 핸드크림"
  ↓
[선물고민러: compose_gift_message 호출]
  → 관계+행사+선물 종합 → 메시지 템플릿 (정중/캐주얼)
  ↓
[에이전트가 최종 메시지 다듬어 사용자에게]
```

### 시나리오 G5 — 광고X 검증 단독 (차별점 단독 노출)

```
사용자: "수면 안마기 광고 없는 진짜 후기만 보여줘"
  ↓
[선물고민러: find_real_recommendations 호출 with keyword="수면 안마기"]
  → 네이버/Tavily 검색
  → F1+F4 광고 필터링 (협찬·체험단·공동구매 제거)
  → 통과한 출처만 정제해서 반환 (URL + 발췌 + 광고 표시 없음 확인)
  ↓
[에이전트가 결과를 사용자에게 깔끔히 정리]
```

이 Tool 자체가 **"광고 없는 큐레이션"이라는 우리 핵심 차별점을 사용자/심사위원에게 단독 노출**합니다. Tool 목록에서 보면 바로 인지됨.

---

## 3. Tool 명세

### Tool 1: `curate_gifts` (메인)

**Name**: `curate_gifts`

**Description**:
```
Gift Curator(선물고민러). Generate curated gift candidates for the user's
recipient based on relationship, occasion, budget, and recipient context.
Combines Naver Blog/Cafe and Tavily web search results, filters out ads
and sponsored content using rule-based detection (#광고/#협찬/체험단/공동구매
keyword matching + multi-source cross-validation), and returns 3 candidates
in distinct tones (practical / emotional / special). Each candidate includes
SearchGift-compatible parameters (query, minPrice, maxPrice, customTags),
non-ad source attribution, reasoning that links input signals to the
recommendation, suggested message card draft, and trend comparison.
Does not call LLM internally - the calling agent should pass each candidate's
query/price params to the Kakao Gift MCP's SearchGift tool for catalog
retrieval. Use this as the primary gift recommendation tool.
```

**inputSchema**:
```python
class CurateGiftsInput(BaseModel):
    recipient_brief: str = Field(
        ...,
        description="One-line recipient + occasion context in Korean. E.g., '엄마 환갑 20만 원 이내 등산 시작 허리 안 좋음'",
        max_length=500,
    )
    budget_max: int | None = Field(None, ge=1000, description="Max budget in KRW. If omitted, parsed from recipient_brief.")
    avoid_categories: list[str] | None = Field(
        None,
        description="Categories to avoid (negative signal). E.g., ['향수', '건강식품']",
        max_length=10,
    )
    recent_gifts_hint: list[str] | None = Field(
        None,
        description="Previously gifted items to avoid duplication. Calling agent should populate this from Kakao Gift MCP's GetRecentGiftOrderHistory if available.",
        max_length=5,
    )
```

**annotations**:
```python
{
    "title": "광고 없는 선물 후보 큐레이션",
    "readOnlyHint": True,
    "destructiveHint": False,
    "openWorldHint": True,         # 네이버/Tavily 외부 호출
    "idempotentHint": False,       # 검색 결과는 시점에 따라 변동
}
```

**Output** (~2,000자 예상):

```markdown
## 🎁 선물 후보 — 엄마 환갑 (~20만 원)

> 광고/협찬/체험단 제거 후 신뢰도 ★★★ 후보 3개

---

### ① 💎 감성형 — 수면 안마기 (10~15만 원대)

**왜 이 후보?** (입력 시그널 → 추론)
- 허리 부담 + 등산 후 회복 → 가벼운 마사지 케어
- 환갑 = 본인을 위한 시간 = 자기 돌봄 카테고리

**카카오 선물하기 검색 파라미터** (에이전트가 SearchGift에 전달)
```json
{
  "query": "수면 안마기",
  "minPrice": 100000,
  "maxPrice": 180000,
  "customTags": ["효도", "건강"]
}
```

**광고 X 검증** (F1+F4 필터 통과)
- 출처 3곳에서 칭찬: 맘카페 2곳, 블로그 1곳
- 협찬 표시: 없음 ✅
- 신뢰도: ★★★ (다중 출처 일관)

**메시지 카드 초안**
"엄마, 환갑 진심으로 축하해요. 무리하지 마시고 푹 쉬세요."

---

### ② 🌿 실용형 — 가벼운 등산 백 (9~12만 원대)

**왜 이 후보?**
- "등산 시작" 명시적 신호 → 등산 장비
- "허리 안 좋음" → 가벼운 백 (무거운 가전 X)

**카카오 선물하기 검색 파라미터**
```json
{
  "query": "가벼운 등산 백팩",
  "minPrice": 90000,
  "maxPrice": 120000,
  "customTags": ["등산", "아웃도어"]
}
```

**광고 X 검증**
- 출처 2곳: 등산 전문 블로그
- 신뢰도: ★★

**메시지 카드 초안**
"엄마, 환갑 축하해요. 등산 다니실 때 가볍게 메세요."

---

### ③ ✨ 특별형 — 프리미엄 여행 가이드북 + 한라산 패키지 (15~20만 원대)

**왜 이 후보?**
- 환갑 = 새 챕터 → 특별한 경험
- 등산 관심 → 한라산 같은 상징적 산행

**카카오 선물하기 검색 파라미터**
```json
{
  "query": "여행 패키지 한라산",
  "minPrice": 150000,
  "maxPrice": 200000,
  "customTags": ["여행", "특별한날"]
}
```

**광고 X 검증**
- 출처 2곳: 여행 블로그
- 신뢰도: ★★

---

## ⚠️ 피해야 할 것
- 무거운 가전 (허리 부담)
- 향수 류 (avoid_categories에 명시되었거나 기본 회피)
- 너무 형식적인 정장/구두

## 📊 트렌드 비교
60대 여성 인기 1위 (`GetTrendingGiftRanking` 기준)는 보통 "비타민/홍삼"이지만,
위 3개 후보는 더 개인화된 선택. 일반 추천과 차별화됨.

## 💬 다른 방향 원하시면
"이거 너무 비싸요" / "취향 다른 것" / "전혀 다른 카테고리" 등을 알려주시면
refine_recommendation으로 새 방향 찾아드려요.

## 호출 에이전트에게
1. 각 후보의 `query`/`minPrice`/`maxPrice`/`customTags`를 카카오 선물하기 MCP의
   `SearchGift`에 전달해 실제 카탈로그 제품을 받아 사용자에게 카드로 보여주세요.
2. 사용자가 "작년에 뭐 드렸는지 기억나" 같은 경우 `GetRecentGiftOrderHistory`
   결과를 다음 `curate_gifts` 호출의 `recent_gifts_hint`에 넣어주세요.
3. 사용자가 "남들 인기 비교"를 원하면 `GetTrendingGiftRanking` 호출 후
   우리 후보와 함께 보여주세요.
```

**응답 시간 예산**:
- 캐시 적중: <100ms
- 캐시 미스 (네이버 + Tavily 2회 호출): <2,500ms (p99 3,000ms 내)

**관련 데이터**:
- `shared/ad_filter.py` — F1 광고 키워드 목록 + F4 다중 출처 집계
- `servers/gift_curator/data/relationship_tone_map.json` — 관계별 톤 가이드

---

### Tool 2: `evaluate_gift_idea` (자문 모드)

**Name**: `evaluate_gift_idea`

**Description**:
```
Gift Curator(선물고민러). Evaluate a user-provided gift idea against the
recipient context. Searches external reviews of the proposed item, filters
out ads (F1+F4), assesses price-appropriateness for the relationship/occasion,
and suggests 1-2 alternative candidates. Returns structured signals
(external review summary, price context, strengths/weaknesses, alternatives)
for the calling agent to synthesize a final judgment. Does not call LLM
internally. Use this when the user already has a candidate in mind and
wants a second opinion (자문 모드).
```

**inputSchema**:
```python
class EvaluateGiftIdeaInput(BaseModel):
    gift_idea: str = Field(
        ...,
        description="The gift candidate the user is considering. E.g., '마사지건', '발렌타인 초콜릿 세트'",
        max_length=200,
    )
    recipient_brief: str = Field(
        ...,
        description="Recipient + occasion + budget context.",
        max_length=500,
    )
    user_budget: int | None = Field(None, ge=1000, description="Actual budget if specified separately.")
```

**annotations**:
```python
{
    "title": "선물 아이디어 평가 (자문)",
    "readOnlyHint": True,
    "destructiveHint": False,
    "openWorldHint": True,
    "idempotentHint": False,
}
```

**Output** (~1,500자 예상):

```markdown
## 💭 평가 — 마사지건 (엄마 환갑, 약 13만 원)

### 외부 후기 시그널 (광고 제거 후)
- 출처 4곳: 맘카페 2 + 블로그 2
- 긍정 패턴: "무릎/어깨 부담 줄음", "조용한 모델 추천"
- 부정 패턴: "허리에는 부담될 수 있음", "무거운 모델은 노인에게 불편"
- 협찬 표시 없음: ✅
- 신뢰도: ★★★

### 가격 적정성
- 환갑 선물 일반 가격대: 10~25만 원 (한국 사회 일반 기준)
- 마사지건 13만 원: **적정** ✅
- 자녀-부모 환갑 평균: 15만 원 ± 5만 (참고)

### 이 사람에게 강점
- 등산 후 회복 도구로 자연스러움
- 자녀가 챙긴다는 메시지 ↑

### 이 사람에게 약점
- "허리 안 좋음" 시그널과 충돌 가능성 (강도 잘못 쓰면 역효과)
- → 가벼운 모델 (mini 시리즈) 선택 필수

### 대안 후보 (혹시 다른 방향)
1. **수면 안마기** (10~15만, 안전성 ↑)
2. **저진동 마사지볼** (5~8만, 가벼움 + 부담 없음)

## 호출 에이전트에게
사용자에게 "마사지건 13만 원은 적정하지만, 강도 약한 모델 추천,
대안으로 수면 안마기도 좋다"는 톤으로 안내해주세요.
```

**응답 시간 예산**: <2,500ms (캐시 미스 시)

---

### Tool 3: `refine_recommendation` (재추천)

**Name**: `refine_recommendation`

**Description**:
```
Gift Curator(선물고민러). Generate new gift candidates based on user feedback
on previous recommendations. Parses feedback signals (price too high/low,
wrong category, wrong style, etc.) from natural language hints provided by
the calling agent, then searches in a different direction. Returns 3 new
candidates in the same format as curate_gifts. Does not call LLM internally
- the calling agent is responsible for parsing the user's free-form feedback
into the structured input. Use this when the user reacts to a previous
curate_gifts output with negative or directional feedback.
```

**inputSchema**:
```python
class RefineRecommendationInput(BaseModel):
    previous_keywords: list[str] = Field(
        ...,
        description="Keywords from previous curate_gifts output to avoid.",
        max_length=10,
    )
    feedback_direction: Literal[
        "cheaper", "more_expensive", "different_category",
        "more_practical", "more_emotional", "more_special",
        "less_serious", "more_serious", "smaller", "bigger",
    ] = Field(
        ...,
        description="Parsed feedback direction. Calling agent translates user's natural language to this.",
    )
    recipient_brief: str = Field(..., max_length=500)
    new_budget_max: int | None = Field(None, ge=1000)
```

**annotations**:
```python
{
    "title": "선물 재추천 (피드백 반영)",
    "readOnlyHint": True,
    "destructiveHint": False,
    "openWorldHint": True,
    "idempotentHint": False,
}
```

**Output**: `curate_gifts`와 동일 형식, 단 "이전 추천 회피" + "방향 전환 이유" 명시.

**응답 시간 예산**: <2,500ms

---

### Tool 4: `compose_gift_message` (메시지 카드)

**Name**: `compose_gift_message`

**Description**:
```
Gift Curator(선물고민러). Generate message card templates to accompany a gift,
tailored to the relationship, occasion, and chosen gift. Returns 2-3 template
variants in different tones (formal/casual/heartfelt) along with a tone
selection guide. Does not call LLM internally - uses pre-curated Korean
message templates organized by relationship type and occasion. Use this when
the user has decided on a gift and needs help writing the accompanying message.
```

**inputSchema**:
```python
class ComposeGiftMessageInput(BaseModel):
    gift_name: str = Field(..., max_length=100)
    recipient_relationship: Literal[
        "parent", "sibling", "friend", "colleague",
        "boss", "client", "lover", "in_law", "child", "other"
    ]
    occasion: str = Field(..., description="E.g., '환갑', '결혼', '승진', '집들이'", max_length=100)
    tone_preference: Literal["formal", "casual", "heartfelt"] | None = Field(None)
```

**annotations**:
```python
{
    "title": "선물 메시지 카드 초안",
    "readOnlyHint": True,
    "destructiveHint": False,
    "openWorldHint": False,
    "idempotentHint": True,
}
```

**Output** (~500자):

```markdown
## 💌 메시지 카드 초안 — 엄마 환갑 (핸드크림)

### 정중 톤
"엄마, 환갑 진심으로 축하드려요. 손 매일 거치시는데 부드럽게 챙기세요."

### 따뜻한 톤 ⭐ (이 관계에 추천)
"엄마, 환갑 축하해요. 매일 쓰시는 손, 늘 고마워요. 자주 발라주세요."

### 캐주얼 톤
"엄마, 환갑 축하 🎉 손 챙기시라고요!"

### 톤 가이드
부모님 + 환갑 = **따뜻한 톤** 추천. 너무 격식 차리면 어색, 너무 캐주얼하면 가벼움.

## 호출 에이전트에게
사용자가 톤 선호 명시했으면 그 톤만 보여주고, 안 했으면 추천 톤 강조해 보여주세요.
```

**응답 시간 예산**: <30ms (정적 템플릿)

**관련 데이터**:
- `servers/gift_curator/data/message_templates.json` — 관계 × 행사 × 톤 매트릭스

---

### Tool 5: `find_real_recommendations` (광고X 검증 단독)

**Name**: `find_real_recommendations`

**Description**:
```
Gift Curator(선물고민러). Search external reviews for a specific keyword
and return only non-ad sources. Applies F1 (explicit ad keyword matching:
#광고/#협찬/체험단/공동구매/리뷰단/원고료/제공받은/협찬받은) and F4
(multi-source cross-validation: items endorsed in multiple independent
sources get higher trust scores). Returns up to N filtered sources with
URL, excerpt, and ad-filter verification. This is the standalone version
of the ad-filtering capability used internally by curate_gifts. Use this
when the user explicitly wants to see "real reviews" of a specific keyword
without full curation. Does not call LLM internally.
```

**inputSchema**:
```python
class FindRealRecommendationsInput(BaseModel):
    keyword: str = Field(..., max_length=100, description="Search keyword in Korean")
    max_results: int = Field(5, ge=1, le=10)
    source_preference: Literal["all", "blog", "cafe", "global"] = Field("all")
```

**annotations**:
```python
{
    "title": "광고 없는 진짜 후기 찾기",
    "readOnlyHint": True,
    "destructiveHint": False,
    "openWorldHint": True,
    "idempotentHint": False,
}
```

**Output** (~1,500자):

```markdown
## 🔍 "수면 안마기" — 광고 없는 후기 5건

### 검색 + 필터링 결과
- 네이버 블로그/카페 검색: 30건
- Tavily 글로벌 보강: 10건
- **F1 키워드 필터 통과**: 25건 (협찬·체험단·공동구매 제거)
- **F4 다중 출처 교차 검증**: 12건 → 상위 5건 선별

---

### 1. ★★★ "수면 안마기 3개월 사용 후기" (블로그)
- URL: https://blog.naver.com/.../...
- 발췌: "노부모님 드렸는데 무릎 마사지에 자주 쓰신다고 함..."
- 광고 표시: 없음 ✅
- 신뢰: 다른 후기와 일관

### 2. ★★★ "엄마 환갑 선물 후기" (맘카페)
- URL: https://cafe.naver.com/.../...
- 발췌: "처음엔 비싸다 했는데 실제로 매일 쓰시더라..."
- 광고 표시: 없음 ✅

### 3. ★★ "수면 안마기 추천 정리" (블로그)
- URL: https://blog.naver.com/.../...
- 발췌: "Z 브랜드가 조용해서 좋음. 노인에게 추천..."
- 광고 표시: 없음 ✅
- 신뢰: 약간 광고 톤이지만 협찬 표시 없음

### 4. ★★ "수면용 안마기 비교" (블로그)
- URL: ...
- 발췌: "...실사용 3가지 비교..."

### 5. ★★ "선물용 마사지 가전" (네이버 카페)
- URL: ...
- 발췌: "...만족도 정리..."

## 필터링 통계
- 협찬 표시 제거: 5건
- 시드 리뷰 패턴 제외: 8건
- 단일 출처 (다중 검증 실패): 12건

## 호출 에이전트에게
사용자에게 위 후기 5건을 깔끔히 정리해서 보여주세요.
"광고 없는 진짜 후기"라는 점을 강조하면 우리 차별점이 잘 전달됩니다.
```

**응답 시간 예산**: <2,500ms (캐시 미스 시)

---

## 4. 데이터 흐름 — 카카오 선물하기 MCP와의 협력

### 표준 흐름 (G1)

```
사용자: "엄마 환갑 20만 원"
  ↓
호출 에이전트가 우리 curate_gifts 호출
  ↓
우리 결과: 후보 3개 + 각각 SearchGift 파라미터
  ↓
호출 에이전트가 각 후보를 카카오 선물하기 MCP의 SearchGift에 자동 전달
  ↓
카카오가 실제 카탈로그 제품 반환
  ↓
사용자 화면: 우리 큐레이션 + 카카오 제품 카드 통합 표시
  ↓
사용자가 마음에 드는 거 클릭 → 카카오 선물하기 앱에서 구매
```

### 중복 회피 흐름

```
사용자: "엄마 선물"
  ↓
호출 에이전트가 GetRecentGiftOrderHistory 호출 → 최근 3건 받음
  ↓
호출 에이전트가 curate_gifts 호출 시 recent_gifts_hint에 그 3건 전달
  ↓
우리는 그 키워드 회피해서 큐레이션
```

### 트렌드 비교 흐름

```
사용자: "60대 여성 인기 선물 vs 특별한 선택 비교"
  ↓
호출 에이전트가 GetTrendingGiftRanking + 우리 curate_gifts 병렬 호출
  ↓
두 결과를 사용자에게 비교 표시
```

---

## 5. 광고 / 결제 정책

- **광고 노출 0** — 우리 Tool 출력에 협찬·광고·구매 유도 없음
- **결제 유도** — 카카오 선물하기 앱으로의 자연 연결만, "구매하세요" 같은 강요 X
- **외부 링크** — 후기 출처 URL만, 쇼핑몰 직링크 X

---

## 6. 에러 처리

| 상황 | 우리 응답 |
|---|---|
| 네이버 API timeout | 부분 결과 + "후기 일부 못 가져왔어요" |
| 네이버 API rate limit | "현재 조회량이 많아요, 잠시 후 다시 시도" |
| 광고 필터 후 결과 0건 | "조건에 맞는 광고 없는 후기를 못 찾았어요. 다른 키워드 시도" |
| recipient_brief 너무 모호 | "받는 분 정보 한 줄 더 알려주세요 (예: '엄마 60대 환갑 20만')" |
| 가격대 추출 실패 | "예산 범위 알려주시면 더 정확해요" |

---

## 7. 테스트 전략

### 단위 테스트
- F1 광고 키워드 매칭: 9개 키워드 모두 정확 감지
- F4 다중 출처 집계: 같은 키워드 N개 출처 → 정확한 점수
- 응답 크기 검증: 최대 출력 시나리오에서도 <24k
- 응답 시간 (캐시 적중): <100ms

### 통합 테스트
- 실제 네이버 + Tavily 호출 → 응답 형식 검증
- 5분 캐싱 정상 작동
- 동시 외부 호출 제한 (semaphore) 작동

### 시나리오 dry-run
- G1: "엄마 환갑 20만" → 후보 3개 합리성 평가
- G2: 사용자 후보 평가 정확도
- G5: 광고 X 검증 정확도 (시드 리뷰 감지 비율)

---

## 8. 미해결 이슈

| # | 이슈 | 결정 시점 / 담당 |
|---|---|---|
| ~~G_U1~~ | ~~광고 키워드 마스터 목록~~ | **✅ 2026-06-22 완료** — `docs/data/ad_keywords.json` (35개) |
| ~~G_U2~~ | ~~message_templates.json~~ | **✅ 2026-06-22 작성** — `docs/data/message_templates.json` (30개 핵심 조합 + fallback 전략. 300개 가능 조합 중 빈번한 것만, 호출 에이전트가 보강) |
| ~~G_U3~~ | ~~relationship_tone_map.json~~ | **✅ 2026-06-22 작성** — `docs/data/relationship_tone_map.json` (10개 관계 × 톤/호칭/예시 표현/주의사항) |
| G_U4 | Tavily country boost 파라미터 (`country=south korea`) 적절성 | Phase 2.2 — 실제 호출해보고 결정 |
| G_U5 | 네이버 검색 결과 시드 리뷰 감지 패턴 (현재 F1만, F4는 출처 다양성) | Phase 2.2 — 실제 결과 보면서 룰 추가 |
| G_U6 | recent_gifts_hint 활용 시 어떤 정보(키워드/카테고리/가격)를 받을지 | Phase 2.2 — SearchGift 응답 구조 확인 후 |

---

## 9. 검토 체크리스트

- [ ] 5개 Tool 분담이 합리적인가
- [ ] 카카오 선물하기 MCP와의 협력 패턴이 명확한가
- [ ] curate_gifts 출력 마크다운 형식이 24k 안에 안전하게 들어가는가
- [ ] F1+F4 룰 기반 광고 필터가 진짜 차별점이 되는가
- [ ] find_real_recommendations Tool이 차별점 단독 노출에 효과적인가
- [ ] 응답 시간 예산이 현실적인가
- [ ] 누락된 시나리오/Tool이 있는가
