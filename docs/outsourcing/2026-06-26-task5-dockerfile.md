# 외주 #5 — Dockerfile 2종 작성

**위임 대상**: GPT-5 (또는 Codex/Cursor) — 1회 호출, ~10분 작업
**목표**: PlayMCP in KakaoCloud 등록용 Dockerfile 2개 + `.dockerignore` 1개 작성
**산출물 형식**: 마크다운 코드블록 3개 (그대로 복붙 가능)
**예상 토큰**: 입력 ~3k, 출력 ~3k

---

## 🚀 외주 프롬프트 (이하 전부 복붙)

````
You are a senior Python/Docker engineer. I'm deploying two Python MCP (Model Context
Protocol) servers to "PlayMCP in KakaoCloud" — a managed container hosting platform
that builds Docker images directly from a public GitHub repo, runs them, and exposes
them as remote MCP endpoints over Streamable HTTP.

## Your task

Produce three files:
1. `Dockerfile.hyodo` (at repo root) — for the Hyodo Secretary MCP server
2. `Dockerfile.gift_curator` (at repo root) — for the Gift Curator MCP server
3. `.dockerignore` (at repo root) — shared

PlayMCP will use each Dockerfile separately when registering each service.

## Hard constraints (from PlayMCP guide)

1. **Architecture**: must build for `linux/amd64`. KC's runtime is amd64 only.
2. **Single port exposed per container**. The MCP server reads `FASTMCP_PORT` (env)
   and binds to `FASTMCP_HOST=0.0.0.0` inside the container.
3. **No host volumes / no host network** — KC mounts none.
4. **No persistent disk writes** — design as if root filesystem is read-only.
5. **Fast cold start** target: image build < 3 min, container ready < 5 sec.
6. **Image size** target: < 250 MB final stage.
7. **Health check**: KC pings `GET /` (Streamable HTTP returns 406 with `mcp-session-id`
   header — that IS the expected "alive" response; do NOT add a separate /health route).
   Just expose the port and let MCP handle it.
8. **Secrets**: KC injects environment variables at runtime (NAVER_CLIENT_ID,
   NAVER_CLIENT_SECRET, TAVILY_API_KEY, LOG_LEVEL, FASTMCP_PORT, FASTMCP_HOST).
   The Dockerfile must NOT bake `.env` into the image. The image MUST start gracefully
   even if some env vars are missing (relevant tools will surface a runtime error;
   server boot itself must succeed). Actually — Hyodo Secretary does not use Naver/
   Tavily, only Gift Curator does. So Hyodo can boot without any external API keys.
9. **Non-root user** for runtime (CIS hardening, KC review preference).
10. **Multi-stage build** preferred for size + reproducibility.

## Repository structure (monorepo, both services share `shared/`)

```
agentic-player-10/
├── pyproject.toml           # see below
├── shared/                  # used by BOTH services — must be included in both images
│   ├── __init__.py
│   ├── ad_filter.py
│   ├── config.py            # loads NAVER_CLIENT_ID, NAVER_CLIENT_SECRET, TAVILY_API_KEY from env
│   ├── http_client.py
│   ├── logging.py
│   ├── naver_search.py
│   ├── positive_signals.py
│   ├── response_builder.py
│   ├── safety_filter.py
│   └── tavily_search.py
├── servers/
│   ├── __init__.py
│   ├── hyodo/
│   │   ├── __init__.py
│   │   ├── server.py        # entrypoint: `python -m servers.hyodo.server`
│   │   ├── tools/           # 5 tools + data/
│   │   └── data/            # JSON files loaded at runtime (must ship in image)
│   └── gift_curator/
│       ├── __init__.py
│       ├── server.py        # entrypoint: `python -m servers.gift_curator.server`
│       ├── tools/           # 5 tools + data/
│       └── data/            # JSON files
└── tests/                   # NOT included in image
```

## `pyproject.toml` (exact contents)

```toml
[project]
name = "agentic-player-10"
version = "0.1.0"
description = "AGENTIC PLAYER 10 — Hyodo Secretary + Gift Curator MCP servers"
requires-python = ">=3.11"
dependencies = [
    "mcp[cli]>=1.2.0",
    "httpx>=0.27.0",
    "pydantic>=2.5.0",
    "python-dotenv>=1.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.23.0",
    "pytest-httpx>=0.30.0",
    "ruff>=0.5.0",
]

[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"

[tool.setuptools.packages.find]
where = ["."]
include = ["shared*", "servers*"]
```

## Server entry point (for context — both services follow the same pattern)

```python
# servers/hyodo/server.py
from mcp.server.fastmcp import FastMCP
import os

mcp = FastMCP(
    "Hyodo Secretary(효도비서)",
    instructions="...",
    port=int(os.environ.get("FASTMCP_PORT", 8000)),
    host=os.environ.get("FASTMCP_HOST", "127.0.0.1"),
)

from servers.hyodo.tools import register_all
register_all(mcp)

def main() -> None:
    mcp.run(transport="streamable-http")

if __name__ == "__main__":
    main()
```

Gift Curator is identical except default port is 8001 and module path is
`servers.gift_curator.server`.

## Design preferences

- **Base image**: `python:3.11-slim-bookworm` (or `python:3.11-slim`) — official slim is fine.
- **Package manager inside image**: plain `pip`. We don't need `uv` in the image
  (build speed is acceptable with pip for this dep set).
- **Build approach**: 2-stage. Stage 1 = wheel builder. Stage 2 = runtime.
- **No `.env` copy** — `.env` is git-ignored; runtime env comes from KC.
- **Hyodo image** should include ONLY `shared/` + `servers/__init__.py` +
  `servers/hyodo/`. NOT `servers/gift_curator/`. Same for Gift Curator (mirror).
  This keeps each image minimal and avoids leaking unrelated code/data.
- The Dockerfile must work when triggered from KC's "build from Git source" flow
  with `Dockerfile path` field pointing to `./Dockerfile.hyodo` (or `.gift_curator`).
- **EXPOSE the port** that the service binds. Hyodo: 8000. Gift Curator: 8001.
  KC maps the exposed port to its public endpoint.
- **No CMD override needed** — KC reads the Dockerfile's CMD.
- **HEALTHCHECK**: skip it (KC has its own probe; an in-image HEALTHCHECK can
  conflict with KC's probe semantics and slow startup).

## Output format

Return THREE fenced code blocks in this exact order, with the filename as the
language hint comment on the first line of each block:

```dockerfile
# Dockerfile.hyodo
... full file contents ...
```

```dockerfile
# Dockerfile.gift_curator
... full file contents ...
```

```gitignore
# .dockerignore
... full file contents ...
```

After the three code blocks, add a short "## Build & verify" section with the
exact local commands to:
1. Build each image for `linux/amd64`
2. Run each container locally with the required env vars
3. Send a probe to confirm it's serving (curl one-liner that should return
   HTTP 406 with the `mcp-session-id` header — that's success)
4. Estimated final image size for each

No additional prose. Begin now.
````

---

## 결과 받으면 본세션에서 할 일

1. 3개 코드블록을 각각 파일로 저장 (`Dockerfile.hyodo`, `Dockerfile.gift_curator`, `.dockerignore`)
2. 로컬에서 `docker build --platform linux/amd64 -f Dockerfile.hyodo -t hyodo:test .` 빌드 검증
3. 각 컨테이너 실행 후 `curl -i http://localhost:8000/` 응답 = `HTTP/1.1 406 Not Acceptable` + `mcp-session-id` 헤더 확인
4. 이미지 크기 측정 (목표 < 250 MB)
5. commit: `chore(deploy): Dockerfile 2종 + .dockerignore (외주 #5)`
6. → Phase 2.3 진입 (PlayMCP in KC 등록)
