# Hyodo Secretary (효도비서) — Design Spec

**작성일**: 2026-06-22
**MCP 서비스명**: `Hyodo Secretary(효도비서)`
**Tool 개수**: 5개
**상위 문서**: [2026-06-22-architecture-overview.md](./2026-06-22-architecture-overview.md)

---

## 1. 개요

### 1.1 한 줄 요약

부모님과 멀리 사는 자녀를 위한 카카오톡 도우미. **부모님께 안부 보내기**(매주 1~3회)와 **부모님이 받은 의심 메시지의 사기 판단**(월 2~5회), 두 가지 효도 시나리오를 한 도구에서 처리.

### 1.2 차별점 (PlayMCP 심사 정당화)

| 차별 요소 | LLM 단독 불가 이유 |
|---|---|
| **부모-자녀 관계 컨텍스트 통합** | 같은 부모 정보를 안부·사기판단·기념일 챙김에 일관 활용 (단일 LLM 호출로 불가능) |
| **시즌/시사 시그널 통합** | 계절/공휴일/뉴스 기반 안부 톤 조정 (정적 LLM 지식 외 시즌 데이터 필요) |
| **사기 패턴 룰 매칭 + 사례 DB** | 한국 보이스피싱/스미싱 최신 패턴 룰 기반 매칭 (LLM의 generic 판단보다 정확) |
| **카카오 나챗방 MCP 자연 연계** | 결과를 사용자 본인 카톡에 저장 (카카오 생태계 내장 MCP 활용) |
| **응답 시간 100ms 보장** | 외부 LLM 호출 없는 빠른 데이터 조회 |

### 1.3 타깃 사용자

- **1차**: 20~40대 자녀 (디지털 네이티브, 카카오톡 도구함 사용 의지 ↑)
- **부모님**: 40대 후반~60대 후반 (카톡 활발, 의심 메시지 자주 수신)
- **사용 디바이스**: 자녀의 카카오톡

### 1.4 첫 화면 — 듀얼 카드

도구함에서 효도비서 진입 시:

```
┌─────────────────────────────────────────┐
│ 🌿 효도비서                                │
│ 부모님과의 거리, AI가 좁혀드릴게요             │
│                                          │
│ ┌─────────────────┐ ┌─────────────────┐  │
│ │  📨 안부 한 줄     │ │  🚨 사기 의심톡     │  │
│ │  부모님께 보낼     │ │  엄마/아빠 받은     │  │
│ │  메시지 만들기     │ │  카톡 확인하기     │  │
│ └─────────────────┘ └─────────────────┘  │
│                                          │
│ 📅 이번 달 챙길 일 보기  💾 결과 저장하기      │
└─────────────────────────────────────────┘
```

---

## 2. 사용자 시나리오

### 시나리오 S1 — 안부 한 줄 (주 1~3회)

```
자녀: "오늘 엄마한테 안부 보내고 싶어. 엄마 60대 허리 안 좋으심"
  ↓
[효도비서: compose_anbu 호출]
  → 부모 컨텍스트 파싱 (관계=엄마, 연령=60대, 건강=허리)
  → 시즌 컨텍스트 (현재 6월말 = 장마/더위)
  → 톤: warm_polite (기본)
  → 메시지 템플릿 후보 + 시즌 키워드 반환
  ↓
[호출 에이전트(GPT/Claude): 위 데이터로 최종 메시지 생성]
  → 자녀: "엄마, 비 많이 오는데 허리 더 안 좋으시진 않으세요? ..."
  ↓
자녀: "이거 좋다, 나챗방에 저장해줘"
  ↓
[효도비서: save_to_memo_chat → 호출 에이전트가 MemoChat MCP 호출]
```

### 시나리오 S2 — 사기 판단 (월 2~5회)

```
자녀: "엄마가 이런 카톡 받았다는데 사기야? '국민은행 대출 승인됐습니다 https://kookmin1n.com/auth'"
  ↓
[효도비서: check_suspicious_message 호출]
  → 위험 신호 추출:
     - URL: kookmin1n.com (오타 의심 - 국민은행 진짜 도메인 X)
     - 키워드: "대출 승인" + 사전 본인 인증 없이 카톡으로 옴
     - 매칭 사기 유형: 대출 사기 (전형적 패턴)
  → 위험도: 매우 높음
  → 권장 대응: 절대 클릭 X, 부모님께 전달 권고
  ↓
[호출 에이전트: 종합 판단 + 자연어 설명]
  → 자녀: "100% 사기예요. 부모님께 절대 클릭 X 안내 필요해요."
  ↓
자녀: "엄마한테 보낼 경고 메시지 만들어줘"
  ↓
[효도비서: compose_parent_warning 호출]
  → 60대 친화 경고 템플릿 + 단계별 안내
  → 호출 에이전트가 자녀가 부모님께 보낼 최종 문구 생성
```

### 시나리오 S3 — 챙길 일 (월 1~2회, 보너스)

```
자녀: "이번 달 엄마/아빠 챙길 일 있어?"
  ↓
[효도비서: find_upcoming_events 호출]
  → 시즌 이벤트: 어버이날(지남), 다음=추석(D-X), 환절기(D-7)
  → 부모 기념일: (parent_brief에 명시되어 있다면) 환갑 D-Y, 생신 D-Z
  ↓
[호출 에이전트가 추천 액션 생성]
```

---

## 3. Tool 명세

### Tool 1: `compose_anbu`

**Name**: `compose_anbu`

**Description (영문 + 국문 병기, 1024자 이내)**:
```
Hyodo Secretary(효도비서). Compose context data for a short greeting message
to the user's parent based on parent profile, current season, weather, and
recent news context. Returns structured data (parent profile breakdown,
seasonal keywords, recommended tone, message templates) for the calling
agent to synthesize the final greeting message in Korean. Does not call LLM
internally - the calling agent (Kakao Tools GPT/Claude) handles the final
message generation. Use this when the user wants to send a daily/weekly
check-in message to their parent.
```

**inputSchema** (Pydantic):
```python
class ComposeAnbuInput(BaseModel):
    parent_brief: str = Field(
        ...,
        description="One-line parent context in Korean. E.g., '엄마 60대 허리 안 좋음 등산 시작'",
        max_length=500,
    )
    occasion: str | None = Field(
        None,
        description="Special occasion if any. E.g., '비 오는 날', '추석 직전'",
        max_length=200,
    )
    tone: Literal["warm_polite", "brief", "playful"] = Field(
        "warm_polite",
        description="Output tone preference",
    )
    image_base64: str | None = Field(
        None,
        description="[Forward compat] Reserved for future Kakao Talk image support.",
    )
```

**annotations**:
```python
{
    "title": "안부 한 줄 만들기",
    "readOnlyHint": True,         # 외부 상태 변경 X
    "destructiveHint": False,     # 파괴적 작업 X
    "openWorldHint": False,       # 외부 API 호출 X (시즌 데이터는 정적)
    "idempotentHint": False,      # 같은 input + 다른 날짜 = 다른 시즌 결과
}
```

**Output (마크다운)**:

```markdown
## 부모님 프로필 (추출됨)
- 관계: 엄마
- 연령대: 60대
- 건강 이슈: 허리 부담
- 최근 활동: 등산 시작
- 관심사 키워드: 등산 (parent_brief에서 추출)

## 시즌 컨텍스트 (정적, seasonal_keywords.json)
- 현재: 6월 말 (장마 시작)
- 다음 절기: 하지 (D+3)
- 이번 달 안부 화제: 장마, 관절 통증, 우산
- 효도 이벤트: 다음 큰 이벤트 = 추석 (D-90, 음력 8/15)

## 트렌드 화제 후보 (호출 에이전트가 시점별 구체화)
부모님 관심사 매칭 카테고리:
- 🥾 취미·라이프스타일 (등산) — 자녀가 자연스럽게 안부 가능
- 🍲 음식·요리 화제 (장마철 보양식, 삼복 등)
- 🏥 사회 안전·생활 이슈 (장마철 안전, 미끄러움)

선택적 추가 카테고리 (parent_brief에 시그널 있을 시):
- 💰 경제·생활 화제 (주식·부동산 — 관심사일 때만)
- ⚾ 스포츠 이벤트 (월드컵/올림픽/야구 — 팬일 때만)
- 📺 엔터·문화 화제 (드라마/트로트 — 시청 시그널 있을 때)

⚠️ **회피 카테고리**: 정치 (선거 시기 외엔 X)

## 추천 톤
- warm_polite (정중하면서 따뜻함)

## 메시지 템플릿 후보 (자녀가 부모님께 보낼 한 줄)
**시즌 기반**
1. "엄마, 장마 시작인데 허리 더 안 좋으시진 않으세요?"
2. "엄마, 등산 다녀오셨어요? 무리하지 마시고요."

**트렌드 기반** (에이전트가 현재 시점 화제 채움)
3. "엄마, 요즘 [현재 시점 등산 관련 트렌드] 어떠세요?"
4. "엄마, 요즘 [현재 화제] 보세요? 어떻게 보세요?"

## 호출 에이전트에게
1. 시즌 기반 템플릿 + 트렌드 카테고리 중 1~2개를 자연스럽게 결합
2. 트렌드 카테고리는 본인(에이전트)의 최신 지식으로 구체 화제 채우기
3. 정치 화제는 선거 시기 외엔 회피
4. 정확한 수치(주가 등) 단정 금지 → '~다는데' 톤으로
5. 톤: 정중함 + 따뜻함
```

**응답 시간 예산**: <50ms (외부 API 호출 X, 정적 데이터 + 룰 기반)

**관련 데이터** (`servers/hyodo/data/`):
- `seasonal_keywords.json` — 월별 시즌 키워드 (계절/공휴일/안부 화제/건강 주의)
- `trending_topic_categories.json` — 시점-독립 트렌드 카테고리 (경제/스포츠/엔터/음식/안전/가족/취미/정치)
- `tone_templates.json` — 톤별 메시지 템플릿

---

### Tool 2: `check_suspicious_message`

**Name**: `check_suspicious_message`

**Description**:
```
Hyodo Secretary(효도비서). Analyze a Korean message (typed text, OCR result,
or natural-language description) to detect scam/phishing/smishing patterns.
Returns structured risk signals (suspicious URLs, suspicious keywords,
matched scam types, recommended user actions) for the calling agent to make
a final judgment and explain to the user. Does not call LLM internally - uses
rule-based pattern matching against a curated database of Korean scam
patterns. Use this when the user shares a suspicious KakaoTalk message
(usually one their parent received).
```

**inputSchema**:
```python
class CheckSuspiciousMessageInput(BaseModel):
    message_text: str = Field(
        ...,
        description="The suspicious message in Korean. Can be: full message copy, OCR extraction, or natural-language description.",
        max_length=3000,
    )
    sender_info: str | None = Field(
        None,
        description="Sender info if available. E.g., '+82 10-1234-5678', 'kakao_id_xxx'",
        max_length=200,
    )
    image_base64: str | None = Field(
        None,
        description="[Forward compat] Reserved for future Kakao Talk image support.",
    )
```

**annotations**:
```python
{
    "title": "의심 메시지 사기 판단",
    "readOnlyHint": True,
    "destructiveHint": False,
    "openWorldHint": False,       # 룰 기반, 외부 호출 X
    "idempotentHint": True,        # 같은 message_text = 같은 결과
}
```

**Output**:

```markdown
## 위험도 판정
**매우 높음 (95% 사기 가능성)**

## 발견된 위험 신호
- 🔗 의심 URL: `kookmin1n.com`
  - 오타 도메인 (진짜 국민은행: kbstar.com)
  - 단축 URL 가능성
- 💬 의심 키워드:
  - "대출 승인" + 본인 인증 없는 카톡 통보 패턴
  - 시간 압박 표현 ("즉시", "오늘 안")
- 📞 발신 정보: (sender_info가 있으면 평가)

## 매칭된 사기 유형
- 대출 사기 (한국 보이스피싱 사례 DB 매칭)
- 유사 신고 사례: 한국인터넷진흥원(KISA) 다수 신고

## 권장 대응 단계
1. **절대 링크 클릭 X**
2. 부모님께 즉시 전달 → 클릭 안 했는지 확인
3. 만약 클릭/정보 입력했다면:
   - 즉시 해당 계정 비밀번호 변경
   - 카드/계좌 거래 정지 요청 (1577-0001)
   - 경찰 사이버범죄 신고 (118)

## 호출 에이전트에게
위 신호들을 종합해 자녀에게 명확하고 침착한 어조로 사기 가능성과
즉시 해야 할 행동을 설명해주세요. 부모님께 보낼 경고 메시지가
필요하면 compose_parent_warning Tool을 추가 호출하세요.
```

**응답 시간 예산**: <100ms (정적 사기 패턴 DB + 룰 매칭만)

**관련 데이터**:
- `servers/hyodo/data/scam_patterns.json` — 사기 유형별 패턴 (URL/키워드/구조)
- `servers/hyodo/data/legit_domains.json` — 정상 한국 금융기관 도메인 목록 (오타 감지용)

---

### Tool 3: `compose_parent_warning`

**Name**: `compose_parent_warning`

**Description**:
```
Hyodo Secretary(효도비서). Generate a parent-friendly warning message template
about a detected scam, suitable for the user to forward to their parent.
Returns structured templates (warning in elderly-friendly Korean, step-by-step
action guide, suggested follow-up channels) tailored to the parent's age/profile.
Does not call LLM internally - uses pre-curated elderly-friendly templates.
Use this after check_suspicious_message returns a high-risk verdict and the
user wants help warning their parent.
```

**inputSchema**:
```python
class ComposeParentWarningInput(BaseModel):
    scam_type: str = Field(
        ...,
        description="Scam type from check_suspicious_message output. E.g., '대출 사기', '택배 사칭'",
    )
    parent_brief: str | None = Field(
        None,
        description="Parent context for tone adjustment.",
        max_length=500,
    )
    urgency: Literal["low", "medium", "high"] = Field("medium")
```

**annotations**:
```python
{
    "title": "부모님께 보낼 경고 메시지",
    "readOnlyHint": True,
    "destructiveHint": False,
    "openWorldHint": False,
    "idempotentHint": True,
}
```

**Output**:

```markdown
## 부모님께 보낼 경고 메시지 템플릿

### 안내 메시지 (자녀가 부모님께 보낼 카톡)
"엄마/아빠, 방금 받으신 OO 메시지는 사기예요.
절대 링크 누르지 마시고, 답장도 하지 마세요.
저한테 캡쳐로 보내주세요 — 제가 확인해드릴게요."

### 부모님이 해야 할 행동
1. 메시지 안에 있는 링크/번호 절대 누르지 마세요
2. 만약 이미 눌렀다면:
   - 자녀(나)에게 즉시 전화
   - 카드/통장 정지: 1577-0001
3. 사기 신고: 118번 또는 사이버범죄신고센터

### 알아두실 안전 수칙
- 은행/공공기관은 카톡으로 절대 대출/환급 안내 안 함
- 의심되면 무조건 자녀에게 먼저 확인
- 비밀번호·계좌번호·OTP는 어떤 경우에도 카톡으로 보내지 X

## 호출 에이전트에게
위 템플릿을 부모님 친화 어조로 다듬어 자녀에게 보여주세요.
긴 설명보다 짧고 분명한 표현 우선. 사기 유형별 핵심 한 줄 강조.
```

**응답 시간 예산**: <30ms (정적 템플릿 조회)

**관련 데이터**:
- `servers/hyodo/data/parent_warning_templates.json` — 사기 유형별 × 긴급도별 템플릿

---

### Tool 4: `find_upcoming_events`

**Name**: `find_upcoming_events`

**Description**:
```
Hyodo Secretary(효도비서). Find upcoming events to check on the user's parent
within a given time window. Combines seasonal events (Korean public holidays,
seasonal health risks, climate transitions) with personal events extracted
from parent_brief (birthdays, anniversaries, milestones). Returns structured
event list with recommended check-in actions. Does not call LLM internally -
uses static calendar data + simple text extraction. Use this when the user
wants to plan parent care for the upcoming weeks.
```

**inputSchema**:
```python
class FindUpcomingEventsInput(BaseModel):
    parent_brief: str = Field(
        ...,
        description="Parent context including any known dates. E.g., '엄마 60대 생신 8월 15일'",
        max_length=500,
    )
    upcoming_days: int = Field(60, ge=7, le=365, description="Look-ahead window in days")
```

**annotations**:
```python
{
    "title": "부모님 챙길 일 찾기",
    "readOnlyHint": True,
    "destructiveHint": False,
    "openWorldHint": False,
    "idempotentHint": False,        # 오늘 날짜에 따라 결과 다름
}
```

**Output**:

```markdown
## 다가오는 챙길 일 (앞으로 60일)

### D-3 — 하지 (절기)
- 카테고리: 시즌 안부
- 추천 행동: "낮 길어진 만큼 일찍 일어나시지 않으세요?" 안부 한 줄

### D-7 — 장마 시작
- 카테고리: 건강 주의
- 추천 행동: 무릎/허리 통증 안부 + 우산/우비 챙김 확인

### D-32 — 광복절 (공휴일)
- 카테고리: 명절 인사
- 추천 행동: 짧은 인사 한 줄 + 방문 가능 여부 논의

### D-54 — 엄마 생신 (8/15)
- 카테고리: 개인 기념일
- 추천 행동: 선물 준비 (선물고민러 Tool 활용 권장), 사전 안부

## 호출 에이전트에게
위 이벤트들을 보고 자녀에게 "지금부터 챙기면 좋을 일"을
우선순위 순으로 정리해주세요. 선물 추천이 필요하면 사용자에게
선물고민러 도구 사용을 안내해주세요.
```

**응답 시간 예산**: <50ms (정적 데이터 + 날짜 계산)

**관련 데이터**:
- `servers/hyodo/data/seasonal_events.json` — 24절기, 한국 공휴일, 환절기/장마/한파
- `servers/hyodo/data/health_seasonal_risks.json` — 시즌별 건강 주의 사항

---

### Tool 5: `save_to_memo_chat`

**Name**: `save_to_memo_chat`

**Description**:
```
Hyodo Secretary(효도비서). Format a Hyodo Secretary result (greeting message,
scam warning, event reminder) into a clean text block ready for saving to
the user's KakaoTalk MemoChat (나와의 채팅방). Returns the formatted text only.
Does not call MemoChat MCP directly - the calling agent should pass this
output to MemoChat MCP's MemoChat tool. Use this when the user explicitly
wants to save a Hyodo Secretary result for later reference.
```

**inputSchema**:
```python
class SaveToMemoChatInput(BaseModel):
    content: str = Field(
        ...,
        description="The content to format and save.",
        max_length=5000,
    )
    category: Literal["anbu", "warning", "event", "general"] = Field("general")
    label: str | None = Field(None, description="Optional label, e.g., '엄마 환갑 D-30'")
```

**annotations**:
```python
{
    "title": "결과를 나챗방에 저장",
    "readOnlyHint": True,             # 우리는 단지 포맷팅만, 저장 X
    "destructiveHint": False,
    "openWorldHint": False,
    "idempotentHint": True,
}
```

**Output**:

```markdown
## MemoChat에 저장할 텍스트 (호출 에이전트가 MemoChat MCP로 전달)

---

📌 효도비서 — [카테고리: 안부] | [라벨: 엄마 6월 안부]
📅 2026-06-22

[원본 content가 여기에]

---

## 호출 에이전트에게
위 텍스트 블록을 카카오톡 나챗방 MCP의 MemoChat tool에 message
파라미터로 전달해주세요. 우리 효도비서는 직접 MemoChat을 호출하지 않습니다.
```

**응답 시간 예산**: <10ms (텍스트 포맷팅만)

---

## 4. 데이터 흐름 — 호출 에이전트와의 협력

### 패턴 A: 단일 Tool 호출 + 에이전트 종합

```
사용자 자연어 입력
  ↓
호출 에이전트가 의도 파악 → 우리 Tool 1개 호출 (구조화된 input 전달)
  ↓
우리 Tool: 빠른 데이터 조회 (<100ms) → 마크다운 응답 반환
  ↓
호출 에이전트가 마크다운 컨텍스트를 보고 자연어 응답 생성
  ↓
사용자에게 친근한 한국어 답변 전달
```

### 패턴 B: 다중 Tool 체이닝 (사기 판단 → 경고 메시지)

```
사용자: "이거 사기야? 엄마한테 경고 보내야 돼"
  ↓
에이전트: check_suspicious_message 호출 → 사기 판정
  ↓
에이전트: 같은 응답 내에 compose_parent_warning 호출 → 경고 템플릿
  ↓
에이전트: 두 결과 종합 → 자녀에게 한 번에 응답
```

### 패턴 C: 외부 카카오 MCP와의 협력

```
사용자: "결과 나챗방에 저장"
  ↓
에이전트: save_to_memo_chat 호출 → 포맷팅된 텍스트
  ↓
에이전트: MemoChat MCP의 MemoChat tool 호출 (우리 Tool 출력을 message로)
  ↓
사용자 본인 나챗방에 저장 완료
```

---

## 5. 광고 / 결제 정책

- 효도비서는 **광고 노출 0** (PlayMCP 요구사항 충족)
- **결제 유도 0** (모든 기능 무료)
- 외부 링크는 공공 신고 채널(KISA 118, 보이스피싱 1577-0001)만 안내

---

## 6. 에러 처리

| 상황 | 우리 응답 |
|---|---|
| input 길이 초과 | "메시지가 너무 길어요. 핵심만 다시 입력해주세요" |
| parent_brief 너무 모호 | "부모님 정보를 한 줄로 알려주시면 더 정확해요 (예: '엄마 60대 허리')" |
| 사기 판단 결과 모호 | "위험 신호가 약합니다. 더 정확한 판단이 필요하면 부모님께 추가 정보를 물어봐주세요" |
| save_to_memo_chat content 비어있음 | "저장할 내용을 알려주세요" |
| 시즌 데이터 미존재 (이론상 X) | 정적 데이터라 발생 안 함 |

---

## 7. 테스트 전략

### 단위 테스트 (Phase 2)
- 각 Tool마다 pytest
- 주요 사기 패턴 (대출/택배/공공기관 사칭) → 정확한 위험도 판정 검증
- 시즌 컨텍스트 → 월별 정확한 절기/이벤트 반환 검증
- 응답 크기 <24k, 응답 시간 <100ms

### 시나리오 dry-run (Phase 2.3)
- S1: "오늘 엄마한테 안부" 흐름 end-to-end
- S2: 실제 보이스피싱 메시지 샘플 10개 → 정확한 판정률 측정
- S3: 다음 60일 챙길 일 출력 합리성 확인

### MCP Inspector (Phase 2.3)
- 5개 Tool 모두 정상 호출 + 응답 검증
- annotations 5개 명시 확인
- inputSchema validation 작동 확인

---

## 8. 미해결 이슈 (Phase 2 시작 전)

| # | 이슈 | 결정 시점 / 담당 |
|---|---|---|
| ~~H1~~ | ~~사기 패턴 DB 초기 수집~~ | **✅ 2026-06-22 완료** — `docs/data/scam_patterns.json` (18개 유형, KISA/경찰청/금감원 2025-2026 기반) |
| ~~H2~~ | ~~seasonal_keywords.json 초기 데이터~~ | **✅ 2026-06-22 초안 작성** — `docs/data/seasonal_keywords.json` (12개월 × 키워드/이벤트/안부 화제/건강 주의) **+ `docs/data/trending_topic_categories.json` (시점-독립 트렌드 카테고리 8개: 경제/스포츠/엔터/음식/안전/가족/취미/정치)** |
| ~~H3~~ | ~~parent_warning_templates.json~~ | **✅ 2026-06-22 작성** — `docs/data/parent_warning_templates.json` (Top 8 사기 유형 × medium/high 긴급도 = 16개 템플릿 + 신고 채널 + 보편 안전수칙) |
| H4 | image_base64 옵셔널 필드의 정확한 spec (현재는 placeholder) | 카카오톡 이미지 지원 시작 시점 |

---

## 9. 검토 체크리스트

- [ ] 5개 Tool 분담이 합리적인가 (너무 잘게 쪼개진 건 아닌가)
- [ ] 각 Tool의 description이 LLM에게 명확하게 호출 시점을 전달하는가
- [ ] 출력 마크다운 형식이 호출 에이전트가 자연어 응답으로 변환하기 쉬운가
- [ ] 응답 시간 예산이 현실적인가 (<100ms)
- [ ] 사기 판단의 False negative 위험 대응이 충분한가
- [ ] 누락된 시나리오가 있는가
