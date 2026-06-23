# Phase 2.1 회고 (2026-06-23)

## 결과 한 줄
공유 인프라 8개 모듈 + 두 서버 골격 + 45개 테스트 통과. 두 서버 동시 실행 검증 완료. 4일 예상 → **약 반나절 완료**.

## 측정 가능한 성과
- **45 testcases · 100% pass · 0.64s** 전체 수행
- **8 shared modules**: config, logging, http_client, naver_search, tavily_search, ad_filter, positive_signals, response_builder
- **2 servers**: hyodo (port 8000), gift_curator (port 8001)
- **11 git commits** on `phase-2.1` 브랜치

## 가장 시간 많이 든 것 (오름차순)
1. **Task 1 환경 셋업** — Python 위치 추적, AnySign4PC 파일 연결 충돌, `.env.*` 패턴 버그
2. **Task 7.5 PositiveSignalScorer** — 사용자 도메인 인사이트(공정위 기준·뒷광고 방어)를 알고리즘으로 인코딩
3. **Task 11 포트 디버깅** — `FASTMCP_PORT` 환경변수 안 먹는 이슈

## 발견사항 (Phase 2.2 진입 전 반영 필요)

### FastMCP Settings 환경변수 동작 (잠재 버그)
- `model_config.env_prefix='FASTMCP_'` 선언 있지만 `FASTMCP_PORT=8001` 환경변수는 실제로 적용 안 됨
- 우회: 코드 안에서 `os.environ.get("FASTMCP_PORT", 기본값)` → `FastMCP(..., port=...)` kwarg 직접 전달
- 두 서버 디폴트 포트 다르게 분리(8000/8001)해 로컬 동시 실행 시 충돌 없음
- Docker/카카오클라우드 배포 시도 같은 kwarg 패턴 유지

### MCP 표준 응답 코드 의미
- 단순 GET → **HTTP 406** (Not Acceptable) + `mcp-session-id` 헤더 → 정상 동작. Streamable HTTP 프로토콜 클라이언트만 수락
- 일반 브라우저로는 접근 불가 — MCP Inspector, Claude Desktop, 카카오톡 챗봇 같은 MCP 클라이언트가 필요
- 이게 정확한 MCP 보안 모델

### 약관 안전망의 책임 위치
- `ResponseBuilder.mandatory_footer` 추가 — 약관 출처 표기를 호출자 부주의로부터 보호
- 다음 Phase에서 Tool 구현 시 `네이버 검색 기반`은 무조건 `mandatory_footer`로

### 양성 신호 스코어러 (F2 신설)
- F1(광고 제거)만으론 차별가치 부족 — F2(진짜 만족 점수)가 PlayMCP 심사 정책의 "LLM 단독 가능 기능 반려" 방어
- 삼각수 가중치(1→1, 2→3, 3→6, 4→10) + 약 신호 별도 트랙

## Phase 2.2 진입 전 외주 후보 (Claude 외부)
- **Tool별 e2e 시나리오 카드 30+개** (GPT) — 다양한 사용자 발화 시뮬레이션
- **Dockerfile 작성 검토** (GPT/Claude) — 멀티스테이지 빌드 표준 패턴
- **MCP Inspector로 두 서버 실측 검사** (사용자) — Phase 2.2 Tool 추가 후

## 다음 단계 (Phase 2.2)
효도비서 5개 Tool + 선물고민러 5개 Tool 구현. 각 Tool마다 TDD + annotations 5개 필수 + description 영문 작성.

Phase 2.2 계획 문서 작성은 Phase 2.1 인터페이스 확정 후 진행 (iterative-engineering 원칙 — Phase 2.1에서 발견된 시그니처 변경을 반영해야 정확).
