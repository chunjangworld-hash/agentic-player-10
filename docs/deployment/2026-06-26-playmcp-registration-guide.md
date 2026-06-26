# PlayMCP in KC 등록 가이드 — 효도비서 + 선물고민러

> 작성: 2026-06-26 / 대상: 비개발자(사용자) 단독 진행 가능 / 등록 데드라인: **2026-07-10 (안전 버퍼)**, **2026-07-14 (마지노선)**

---

## 0. 사전 조건 확인 (이미 완료)

| 항목 | 상태 |
|---|---|
| GitHub repo 공개 | ✅ Public — `chunjangworld-hash/agentic-player-10` |
| Dockerfile 2종 | ✅ `Dockerfile.hyodo`, `Dockerfile.gift_curator` |
| 로컬 Docker build·실행 | ✅ HTTP 406 + `mcp-session-id` 정상 |
| 대표 이미지 | ✅ `assets/images/mascots/*.png` 2장 |
| 외부 API 키 | 🟠 Naver, Tavily 키는 사용자가 별도 발급 보관 (`.env`) |

---

## 1. phase-2.3 → main 머지 (PR #3)

PlayMCP는 **main 브랜치 기준** 빌드 권장. 안정.

1. 브라우저로 https://github.com/chunjangworld-hash/agentic-player-10/pull/new/phase-2.3 접속
2. PR 제목: `Phase 2.3 — Docker 빌드 + Tool description 다듬기 (외주 #4·#5 통합)`
3. 본문: commit 메시지 자동 채워짐 (그대로 OK)
4. `Create pull request`
5. `Squash and merge` → `Delete branch`

머지 완료되면 `main` HEAD에 Dockerfile이 포함됨.

---

## 2. PlayMCP in KC 등록

### 2.1. 접속

https://playmcp.kakaocloud.io 접속 → 카카오 계정 로그인.

### 2.2. 효도비서 등록

`+ 새 MCP 서버 등록` 클릭 → **Git 소스 빌드 방식** 선택.

| 필드 | 입력값 |
|---|---|
| MCP 서버 이름 | `hyodo-secretary` (PlayMCP 노출명과 무관, KC 내부 표시용) |
| 설명 | `효도비서 — KakaoTalk 부모 안부·사기 차단 도우미` |
| Git URL | `https://github.com/chunjangworld-hash/agentic-player-10.git` |
| 브랜치 | `main` |
| Dockerfile 경로 | `Dockerfile.hyodo` |
| PAT | (비워둠 — Public repo) |

**환경변수** (UI에서 추가):

| Key | Value | 비고 |
|---|---|---|
| `FASTMCP_HOST` | `0.0.0.0` | 컨테이너 내 바인딩 |
| `FASTMCP_PORT` | `8000` | (또는 KC가 지정한 포트) |
| `LOG_LEVEL` | `INFO` | |

→ Hyodo는 **외부 API 안 쓰므로 NAVER/TAVILY 키 불필요**.

`등록하기` 클릭 → Status `Starting` (1~3분) → `Active` 되면 ✅.

### 2.3. 선물고민러 등록

같은 방식으로 한 번 더:

| 필드 | 입력값 |
|---|---|
| MCP 서버 이름 | `gift-curator` |
| 설명 | `선물고민러 — 광고 없는 진짜 선물 큐레이션` |
| Git URL | `https://github.com/chunjangworld-hash/agentic-player-10.git` |
| 브랜치 | `main` |
| Dockerfile 경로 | `Dockerfile.gift_curator` |
| PAT | (비워둠) |

**환경변수**:

| Key | Value |
|---|---|
| `FASTMCP_HOST` | `0.0.0.0` |
| `FASTMCP_PORT` | `8001` |
| `LOG_LEVEL` | `INFO` |
| `NAVER_CLIENT_ID` | (네이버 개발자센터에서 발급한 값) |
| `NAVER_CLIENT_SECRET` | (네이버 개발자센터에서 발급한 값) |
| `TAVILY_API_KEY` | (Tavily 가입 후 받은 키) |

→ `등록하기` → Status `Active` 대기.

### 2.4. Endpoint URL 복사

각 서버가 Active 되면 상세 페이지에서 **Endpoint URL** 복사 — 두 개 보관:

- 효도비서 Endpoint: `https://<random>-hyodo.kc-mcp.kakaocloud.io/mcp` (예상 패턴)
- 선물고민러 Endpoint: `https://<random>-gift.kc-mcp.kakaocloud.io/mcp` (예상 패턴)

---

## 3. PlayMCP 마켓 임시 등록 + 자체 테스트

### 3.1. 임시 등록

PlayMCP 마켓 (별도 URL — 가이드 보고 확인) → `+ MCP 등록` 또는 `+ 새 MCP 신청`.

| 필드 | 효도비서 | 선물고민러 |
|---|---|---|
| MCP Server Name | `hyodo_secretary` (영문, A-Za-z0-9_-, 128자 이하, "kakao" 금지) | `gift_curator` |
| 노출 이름 | `효도비서` | `선물고민러` |
| 설명 | (영문 권장, 마케팅 카피 — 별도 작성) | (영문 권장) |
| 대표 이미지 | `assets/images/mascots/hyodo_secretary.png` 업로드 | `assets/images/mascots/gift_curator.png` 업로드 |
| Endpoint URL | (위에서 복사한 KC URL) | (위에서 복사한 KC URL) |

**임시 등록** 상태로 저장.

### 3.2. AI 채팅 자체 테스트

PlayMCP FAQ 따라:
1. 임시 등록 → MCP 상세 미리보기 진입
2. "AI 채팅에 적용" 클릭
3. **본인 카카오톡** 가서 ChatGPT 챗봇과 대화
4. 시나리오 dry-run:
   - "효도비서로 부모님께 안부 한 줄 만들어줘"
   - "선물고민러로 친구 생일 선물 골라줘"
5. 10개 Tool 모두 호출되는지 + 응답 정상인지 확인

### 3.3. 문제 발견 시 수정

- 코드 수정 → git push (main에) → PlayMCP가 자동 재빌드 (방식 A는 자동 재빌드 옵션 있음 — UI에서 확인)
- 또는 PlayMCP 등록 페이지에서 "재빌드" 버튼

---

## 4. 정식 심사 신청

자체 테스트 통과 후:
1. PlayMCP 마켓에서 "정식 심사 신청" 버튼
2. 영업일 기준 7일 (평균 1~2일) 심사
3. 보완 요청 시 수정 → 재신청

**데드라인 역산**:
- 정식 등록 데드라인 안전 버퍼: 2026-07-10
- 심사 7일 가정 → 신청 데드라인: **2026-07-03**
- 자체 테스트 + 디버깅 1주 가정 → 등록 시작 데드라인: **2026-06-27** (내일!)

→ **오늘 PR 머지 + 내일 등록 시작이 안전 페이스**.

---

## 5. 트러블슈팅 체크리스트

| 증상 | 점검 |
|---|---|
| KC Status가 `Starting` → `Failed` | Dockerfile 빌드 실패. KC 로그 확인 |
| Status `Active`인데 `/mcp` 응답 없음 | 환경변수 `FASTMCP_HOST=0.0.0.0` 확인 (필수!) |
| Hyodo가 `NAVER_CLIENT_ID` 에러 | (이제 옵셔널이라 발생 안 함. 발생 시 phase-2.3 머지 누락 의심) |
| 카톡 챗봇이 Tool을 호출 안 함 | Tool description의 "Use this when ..." 트리거 명확성 점검 (외주 #4 결과 OK) |
| 응답이 길어서 잘림 | `ResponseBuilder` 한계 22,000자 (안전 버퍼). 더 짧게 조정 |

---

## 6. 등록 후 메모리 갱신 권장

```
- [Reference: KC Endpoint URLs](reference_kc_endpoints.md) — 효도비서/선물고민러 Endpoint
- [Project: PlayMCP 등록 진행](project_playmcp_registration.md) — 심사 신청일, 보완 사항 추적
```

---

## 7. 관련 파일

- [docs/handoff/2026-06-23.md](../handoff/2026-06-23.md) — Phase 2.3 진입 핸드오프
- [docs/outsourcing/2026-06-26-task5-dockerfile.md](../outsourcing/2026-06-26-task5-dockerfile.md) — Dockerfile 외주 프롬프트
- [Dockerfile.hyodo](../../Dockerfile.hyodo), [Dockerfile.gift_curator](../../Dockerfile.gift_curator)
