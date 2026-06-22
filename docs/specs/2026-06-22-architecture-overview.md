# Architecture Overview — AGENTIC PLAYER 10 출품작

**작성일**: 2026-06-22
**대상**: 효도비서 (Hyodo Secretary) MCP + 선물고민러 (Gift Curator) MCP 공동 아키텍처
**예선 마감**: 2026-07-14

---

## 1. 프로젝트 정의

카카오 AGENTIC PLAYER 10 공모전 출품을 위한 **2개의 독립 MCP 서버**:

| MCP | 한 줄 요약 | 핵심 차별점 |
|---|---|---|
| **Hyodo Secretary (효도비서)** | 부모님과 멀리 사는 자녀를 위한 카카오톡 도우미 (안부 + 사기 판단 통합) | 두 가지 효도 시나리오를 한 도구에서, 부모-자녀 관계 컨텍스트 통합 |
| **Gift Curator (선물고민러)** | 광고 없는 진짜 칭찬받은 선물을 카카오톡에서 큐레이션 | 카카오 선물하기 MCP (`SearchGift`/`GetTrendingGiftRanking`/`GetRecentGiftOrderHistory`)와 외부 후기 검색을 통합한 메타 큐레이션 레이어 |

**공통 사용자**: 20~40대 카카오톡 사용자.
**공통 톤**: 정중함 + 따뜻함, 자존감 보호.
**공통 차별 전략**: 카카오 생태계 내부 MCP와의 자연스러운 조율 + Stateless 운영.

---

## 2. 아키텍처 핵심 원칙

### 2.1 The MCP Role Boundary

> **우리 MCP Tool = 빠른 데이터 조회/포맷팅 (손과 발)**
> **호출 에이전트 (Kakao Tools의 GPT/Claude) = 자연어 추론/생성 (뇌)**

이 분리는 두 가지 PlayMCP 제약을 동시에 만족시킵니다:

| 제약 | 우리 대응 |
|---|---|
| 평균 응답 100ms / p99 3,000ms | 우리 Tool은 LLM 호출 없이 외부 API + 룰 기반만 → 100ms 안에 응답 |
| LLM 단독으로 가능한 기능은 반려 | 우리 Tool은 카카오 자체 MCP 통합 + 외부 데이터 종합 → LLM 단독 불가능 입증 |

### 2.2 Stateless 원칙

- 서버는 사용자별 세션/프로필을 저장하지 않음
- 사용자 컨텍스트는 매 호출마다 input으로 받음 (자유 자연어)
- 영구 보관이 필요하면 사용자가 카카오 나챗방 MCP의 `MemoChat`으로 저장 (반자동)
- 개인정보 처리 책임 회피 + 인증 시스템 불필요 + 본인 카카오톡에 데이터 소유권

### 2.3 Forward Compatibility

- Tool input schema에 미래 확장 필드를 **옵셔널로** 미리 정의
- 예: `text: string` (필수) + `image_base64?: string` (현재 미지원, 향후 카카오톡이 이미지 지원 시 자동 활성화)
- 카카오톡/PlayMCP 스펙이 진화할 가능성을 가정한 보수적 설계

---

## 3. 시스템 구조

### 3.1 모노레포 디렉토리

```
agentic-player-10/
├── .gitignore
├── README.md
├── CLAUDE.md                      # 협업 지침
├── pyproject.toml                 # Python 프로젝트 메타데이터 + 공통 의존성
├── docs/
│   └── specs/                     # 설계 문서들
├── shared/                        # 두 서버 공유 코드
│   ├── __init__.py
│   ├── config.py                  # 환경 변수 로딩, 설정
│   ├── logging.py                 # 표준 로거 설정
│   ├── http_client.py             # httpx 래퍼 (재시도, 타임아웃, 캐싱)
│   ├── naver_search.py            # 네이버 검색 API 클라이언트
│   ├── tavily_search.py           # Tavily API 클라이언트
│   ├── ad_filter.py               # 광고 필터링 (F1 키워드 + F4 다중 출처)
│   ├── markdown_utils.py          # 응답 포맷팅 (마크다운 템플릿)
│   └── response_builder.py        # 응답 구조화 + 24k 제한 검사
└── servers/
    ├── hyodo/
    │   ├── Dockerfile             # PlayMCP in KC 등록용
    │   ├── server.py              # MCP 서버 진입점
    │   ├── tools/
    │   │   ├── __init__.py
    │   │   ├── compose_anbu.py
    │   │   ├── check_suspicious_message.py
    │   │   ├── compose_parent_warning.py
    │   │   ├── find_upcoming_events.py
    │   │   └── save_to_memo_chat.py
    │   └── data/                  # 정적 데이터 (사기 패턴 룰, 계절 키워드 등)
    └── gift_curator/
        ├── Dockerfile
        ├── server.py
        ├── tools/
        │   ├── __init__.py
        │   ├── curate_gifts.py
        │   ├── evaluate_gift_idea.py
        │   ├── refine_recommendation.py
        │   ├── compose_gift_message.py
        │   └── find_real_recommendations.py
        └── data/                  # 정적 데이터 (광고 키워드 목록 등)
```

### 3.2 기술 스택 (확정)

| 영역 | 선택 | 근거 |
|---|---|---|
| **언어** | Python 3.11+ | MCP Python SDK 안정성, 카카오 생태계 친화 |
| **MCP SDK** | **FastMCP** (`mcp[fastmcp]`) | 공식 SDK 위에 빌드된 데코레이터 기반 wrapper. 비개발자 친화적. Tool 정의·annotations·schema 자동 생성 |
| **HTTP** | `httpx` (async) | 비동기 외부 API 호출, retry 지원 |
| **검증** | `pydantic` v2 | Tool input schema 자동 생성 + 검증 |
| **컨테이너** | Docker (`python:3.11-slim`) | PlayMCP in KC 등록 요구사항. linux/amd64 빌드 |
| **로깅** | 표준 `logging` + JSON 포맷 | 카카오클라우드 로그 수집 호환 |

### 3.3 외부 의존성

| 출처 | 사용 처 | 인증 | 무료 한도 | 비고 |
|---|---|---|---|---|
| **네이버 검색 API** | 선물고민러 (블로그/카페 후기) | Client ID/Secret (헤더) | 25,000회/일 | 한국어 후기 핵심 출처 |
| **Tavily API** | 선물고민러 (글로벌 검색 백업) | API Key | 1,000 credits/월 | 검색 + Country 부스팅 |
| **카카오 선물하기 MCP** | 선물고민러 (간접 — 사용자가 도구함에 추가 시 자동 연계) | Kakao Tools 내장 | - | `SearchGift`, `GetTrendingGiftRanking`, `GetRecentGiftOrderHistory` |
| **카카오 나챗방 MCP** | 효도비서 + 선물고민러 (간접 — 결과 저장 위임) | Kakao Tools 내장 | - | `MemoChat` (쓰기 전용) |

**중요**: 카카오 자체 MCP들은 **우리 서버에서 직접 호출하지 않음**. AI 에이전트가 사용자의 자연어 요청을 보고 우리 MCP와 카카오 MCP를 함께 조율함. 우리는 SearchGift 호출에 필요한 키워드/가격대를 출력하면 됨.

---

## 4. 공유 컴포넌트 명세

### 4.1 `shared/config.py`

환경 변수 로딩, 설정 객체.

```python
@dataclass(frozen=True)
class Settings:
    naver_client_id: str
    naver_client_secret: str
    tavily_api_key: str
    log_level: str = "INFO"
    naver_max_per_query: int = 10
    tavily_max_results: int = 5
    response_max_chars: int = 22000  # 24k 한계, 2k 버퍼
```

`.env` 파일에서 로딩 (Python `os.environ`).

### 4.2 `shared/http_client.py`

비동기 httpx 클라이언트 + 재시도 + 타임아웃 + **서비스별 캐싱 정책**.

```python
class HttpClient:
    async def get(url, headers, params, *, timeout=5.0, cache_ttl=0) -> dict
    # cache_ttl=0 (기본): 캐싱 안 함
    # cache_ttl>0: 해당 초만큼 캐시
```

- **타임아웃**: 5초 (외부 API 응답 안 오면 우리 Tool 응답속도 초과)
- **재시도**: 1회만 (지연 누적 방지)
- **캐싱 정책 — 서비스별 분리**:
  - **네이버 검색 API**: ❌ **캐싱 안 함** (약관 7.3 위반 위험 — API 결과 무단 복제·저장 금지 조항)
  - **Tavily API**: ✅ 5분 LRU 캐싱 (Tavily 약관 별도, 검색 API 캐싱 일반 허용)
  - **동시 호출 보호**: 같은 query 30초 미만 in-flight deduplication (양쪽 모두)
- 자세한 내용: `docs/data/naver_search_api_compliance.md`

### 4.3 `shared/ad_filter.py`

광고 필터링 (F1 키워드 + F4 다중 출처).

```python
AD_KEYWORDS = ["#광고", "#협찬", "유료광고포함", "체험단", "공동구매",
               "리뷰단", "원고료", "제공받은", "협찬받은"]

def is_ad_by_keyword(text: str) -> bool: ...
def aggregate_by_source(items: list) -> list:
    """같은 키워드를 여러 출처에서 칭찬 → 신뢰도 점수 부여"""
```

LLM 분류는 우리 안 함. 룰 기반 + 호출 에이전트에게 후보+메타데이터 위임.

### 4.4 `shared/response_builder.py`

Tool 응답 구조화 + 24k 제한 검사.

```python
def build_markdown_response(payload: dict, *, max_chars: int = 22000) -> str:
    """렌더링 후 길이 검사. 초과 시 후보 수 줄이거나 truncate + 'more' 안내"""
```

### 4.5 `shared/logging.py`

표준 logging, JSON 포맷 (카카오클라우드 로그 수집).

```python
logger = setup_logger("hyodo")  # or "gift_curator"
logger.info("tool_call", extra={"tool": "compose_anbu", "duration_ms": 42})
```

---

## 5. MCP 표준 준수

### 5.1 Protocol

- **MCP spec 버전**: 2025-11-25 (최대 지원 버전)
- **전송**: Streamable HTTP (필수)
- **상태**: Stateless (no session)
- **인증**: 없음 (1차 MVP) — 필요 시 미래에 OAuth 추가

### 5.2 Tool 정의 (FastMCP 패턴)

```python
from mcp.server.fastmcp import FastMCP
from pydantic import Field

mcp = FastMCP("Hyodo Secretary(효도비서)")

@mcp.tool(
    name="compose_anbu",
    description="Hyodo Secretary(효도비서). Compose context data for a short greeting message to the user's parent based on parent profile, season, and recent news. Returns structured context for the calling agent to synthesize the final message. Does not call LLM internally.",
    annotations={
        "title": "안부 한 줄 만들기",
        "readOnlyHint": True,
        "destructiveHint": False,
        "openWorldHint": False,
        "idempotentHint": False,
    }
)
def compose_anbu(
    parent_brief: str = Field(..., description="One-line parent context, e.g., '엄마 60대 허리 안 좋음 등산 시작'"),
    tone: str = Field("warm_polite", description="Output tone: warm_polite | brief | playful"),
) -> str:
    ...
```

### 5.3 Tool description 작성 원칙

- **영문 우선** + MCP 서비스명 영문/국문 병기 (`Hyodo Secretary(효도비서)`)
- **1,024자 이내** (너무 길면 다른 Tool 호출에도 영향)
- **명확한 호출 시점** 명시 ("when the user wants to send a daily greeting to their parent")
- **호출 에이전트에게 후속 액션 힌트** 포함 ("Returns structured data for the agent to synthesize the final message")

### 5.4 Tool result 원칙

- **마크다운 텍스트** 우선 (raw JSON 지양)
- **24,000자 미만** 엄수 (24k 초과 시 에러 → 반려)
- 후보가 많으면 상위 N개로 자르고 "더 보기" 안내
- 외부 API 응답은 절대 그대로 반환하지 않음 (정제 후 반환)

---

## 6. 성능 전략

### 6.1 응답 시간 예산 (Tool당)

| 단계 | 예상 시간 |
|---|---|
| Tool 진입 + input 검증 | <5ms |
| 네이버 API 호출 (캐싱 X, 매번 호출) | <1,500ms |
| Tavily API 호출 (캐시 적중) | <10ms |
| Tavily API 호출 (캐시 미스) | <1,500ms |
| 룰 기반 광고 필터 | <50ms |
| 응답 포맷팅 (마크다운) | <20ms |
| **외부 호출 없는 Tool 합 (compose_anbu, find_upcoming_events 등)** | **<100ms** ✅ |
| **외부 호출 있는 Tool 합 (curate_gifts, find_real_recommendations 등, p99)** | **<2,500ms** ✅ (3,000 이내) |

**평균 100ms** 목표는 외부 호출 없는 Tool 7개의 평균으로 끌어내림. 외부 호출 있는 3개 Tool은 p99 3,000ms 충족이 핵심.

### 6.2 캐싱 전략 (서비스별 분리)

- **네이버 검색 API**: 캐싱 ❌ (약관 위반 회피)
- **Tavily API**: 같은 키워드 5분 in-memory LRU 캐싱
- **동시 호출 보호**: 양쪽 모두 30초 in-flight deduplication
- 사용자별 캐시는 안 함 (Stateless 원칙)
- 카카오 자체 MCP 호출은 우리가 안 함 → 카카오가 알아서

### 6.4 출처 표기 (네이버 API 약관 요구)

`curate_gifts` / `find_real_recommendations` 응답 마크다운 끝에:

```markdown
---
🔍 출처: 네이버 검색 API + Tavily
```

(BI 가이드의 네이버 로고 사용은 Phase 3에서 검토)

### 6.3 동시성 / 외부 API 호출 제한

- `asyncio.Semaphore`로 동시 외부 호출 5개로 제한 (네이버 API 부하 방지)
- 외부 API timeout 5초 (Tool 응답 시간 보호)

---

## 7. 보안 & 개인정보

| 항목 | 우리 처리 |
|---|---|
| 주민번호/카드/계좌/여권 등 | **절대 요구·반환 안 함** (심사 반려 사유) |
| 사용자 입력 (부모 정보 등) | Stateless — 처리 후 즉시 폐기, 저장 X |
| 외부 API 응답 | 캐시 (5분 in-memory) 외 영구 저장 X |
| 광고 노출 유도 | 절대 금지 (심사 반려 사유) |
| 의료/금융 자문 | 회피 (사기 판단은 일반 정보 안내로 한정) |

---

## 8. 배포 & 운영

### 8.1 PlayMCP in KC 등록 방식

- **Git 소스 빌드** (방식 A) 선택
- GitHub public repo `agentic-player-10` 하나
- 각 서버는 Dockerfile 경로로 구분:
  - Hyodo: Git URL + Dockerfile 경로 `servers/hyodo/Dockerfile`
  - Gift Curator: 같은 Git URL + Dockerfile 경로 `servers/gift_curator/Dockerfile`

### 8.2 Dockerfile 패턴

```dockerfile
# servers/hyodo/Dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY pyproject.toml ./
COPY shared/ ./shared/
COPY servers/hyodo/ ./servers/hyodo/
RUN pip install --no-cache-dir -e .
ENV PYTHONUNBUFFERED=1
EXPOSE 8000
CMD ["python", "-m", "servers.hyodo.server"]
```

- linux/amd64 빌드 필수 (PlayMCP in KC 요구사항)
- Apple Silicon Mac은 `docker build --platform linux/amd64 .`

### 8.3 환경 변수 (`.env`, gitignore됨)

```bash
NAVER_CLIENT_ID=xxx
NAVER_CLIENT_SECRET=xxx
TAVILY_API_KEY=tvly-dev-xxx
LOG_LEVEL=INFO
```

PlayMCP in KC 등록 시 환경 변수 설정 화면에서 입력.

### 8.4 일정 (Phase 2 + 3)

| Phase | 기간 | 마일스톤 |
|---|---|---|
| Phase 2.1 | 6/23 ~ 6/26 | 공유 컴포넌트 구현 + FastMCP 기본 서버 셋업 |
| Phase 2.2 | 6/27 ~ 7/3 | 효도비서 + 선물고민러 Tool 구현 |
| Phase 2.3 | 7/4 ~ 7/8 | MCP Inspector 통과 + Docker 빌드 + 카카오클라우드 배포 |
| Phase 3.1 | 7/9 ~ 7/11 | PlayMCP 등록 + 대표 이미지 + 등록 카피 |
| Phase 3.2 | 7/12 ~ 7/14 | 실제 카카오톡 도구함 dry-run + 응모 |

**등록 데드라인: 7/10** (심사 1~7일 + 보완 요청 대응 버퍼 확보)

---

## 9. 테스트 전략

### 9.1 단위 테스트 (Phase 2)

- 각 Tool마다 pytest 단위 테스트
- 외부 API는 `pytest-httpx`로 mock
- 응답 크기 < 24k 검증
- 응답 시간 < 3,000ms 검증 (단위 테스트 환경에서)

### 9.2 통합 테스트 (Phase 2.3)

- 실제 네이버/Tavily API 호출
- 응답 형식 (마크다운) 검증
- 캐싱 동작 확인

### 9.3 MCP Inspector (Phase 2.3)

- `npx @modelcontextprotocol/inspector`
- 모든 Tool에 대해 정상 호출 + 응답 검증
- annotations 5개 모두 명시 확인

### 9.4 카카오톡 dry-run (Phase 3.2)

- 실제 카카오톡 도구함에 등록 후
- 자녀 페르소나로 모든 핵심 시나리오 수동 시연
- 응답 자연스러움 + 카드 UI 가독성 평가

---

## 10. 에러 처리

| 상황 | 우리 응답 |
|---|---|
| 외부 API timeout | 부분 결과 + "일부 데이터 조회 실패, 다시 시도해주세요" 안내 |
| 외부 API rate limit | "현재 조회량이 많습니다, 잠시 후 다시 시도해주세요" |
| 사용자 입력 부족 | "더 정확한 추천을 위해 OO 알려주시면 좋아요" follow-up 권고 |
| 인증 만료 (미래 OAuth 시) | HTTP 401 Unauthorized 반환 (PlayMCP 요구사항) |
| 내부 예외 | 사용자에게 일반 에러 메시지 + 로그에 상세 기록 |

**원칙**: 절대로 raw API 에러나 stack trace를 사용자에게 노출 X. 항상 친근한 한국어 메시지.

---

## 11. 미해결 이슈 (Phase 2 시작 전 결정)

| # | 이슈 | 결정 시점 |
|---|---|---|
| ~~U1~~ | ~~FastMCP 버전~~ | **✅ 2026-06-22 확정** — 공식 MCP Python SDK 내장 `mcp.server.fastmcp` 사용 (`pip install "mcp[cli]>=1.2.0"`). 별도 fastmcp 패키지는 PlayMCP 호환성 미보장으로 회피 |
| ~~U2~~ | ~~네이버 검색 API 약관 정독~~ | **✅ 2026-06-22 완료** — `docs/data/naver_search_api_compliance.md` |
| ~~U3~~ | ~~Tool input 글자 길이 제한~~ | **✅ 2026-06-22 확정** — 짧은 컨텍스트 500자, 긴 메시지 3,000자, 짧은 답변 200자, 콘텐츠 5,000자 (이미 design doc Tool 명세에 반영) |
| ~~U4~~ | ~~광고 키워드 목록 확정~~ | **✅ 2026-06-22 완료** — `docs/data/ad_keywords.json` (35개) |
| ~~U5~~ | ~~대표 이미지 디자인 방향~~ | **✅ 2026-06-22 방향 결정** — `docs/design/visual_identity.md` (효도비서=다람쥐 따뜻한 자연 톤, 선물고민러=토끼 카카오 노랑+발랄). 실제 이미지 제작은 Phase 3.1 |

---

## 12. 관련 문서

- `2026-06-22-hyodo-secretary-design.md` (작성 예정) — 효도비서 5개 Tool 풀 명세
- `2026-06-22-gift_curator-design.md` (작성 예정) — 선물고민러 5개 Tool 풀 명세
- `CLAUDE.md` — 사용자 협업 지침
- 메모리 `reference_playmcp_*` — PlayMCP 공식 가이드 요약

---

## 검토 체크리스트 (이 문서)

- [ ] 모노레포 구조가 본인 의도와 일치하는가
- [ ] FastMCP 선택에 동의하는가 (대안: 공식 MCP SDK 직접 사용)
- [ ] LLM 위임 원칙이 명확한가
- [ ] 응답 시간 예산이 현실적인가
- [ ] 일정 (Phase 2 ~ 7/14)이 무리 없는가
- [ ] 누락된 영역이 있는가
