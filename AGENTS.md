# AGENTS.md — 大猫投资 (Big Cat Investment)

## Architecture: legacy vs new

- **Legacy (do not modify)**: `backend/` (Python+FastAPI+SQLite) and `frontend/` (vanilla JS). These are dead code for reference only.
- **New backend**: `jjs-server/` — Go 1.24, chi router, GORM+MySQL, JWT+bcrypt.
- **New frontend**: `jjs-web/` — React 18 + TypeScript + Vite + Tailwind CSS + Zustand + TanStack Query/Router.
- **Rewrite plan**: `docs/REFACTORING_ROADMAP.md` — 8 phases. Currently at P2 start (lean Company skeleton, auth works).

## Development commands

All commands run from the package subdirectory, not from repo root.

### jjs-server (Go backend)

```bash
# Run (requires MySQL and config.json with mysql_dsn)
go run ./cmd/server
# Build binary
go build -o bin/jjs-server ./cmd/server
# Run built binary (reads bin/config.json by default)
./bin/jjs-server
```

### jjs-web (React frontend)

```bash
# Install (must use pnpm, not npm/yarn)
pnpm install
pnpm dev          # :5173, proxies /api and /ws to :8080
pnpm build        # outputs to dist/
pnpm typecheck    # runs tsc --noEmit on both tsconfig files
pnpm lint         # eslint .
```

**Verification order**: `pnpm typecheck` first, then `pnpm lint`. Both must pass before considering frontend work complete.

### Full-stack dev flow

1. Start MySQL (must be running)
2. Create `jjs-server/config.json` with `mysql_dsn` pointing at your DB (gitignored, see `bin/config.json` for format)
3. `go run ./cmd/server` in `jjs-server/`
4. `pnpm dev` in `jjs-web/`
5. Open http://localhost:5173 (Vite proxies API calls to Go at :8080)

## Configuration (jjs-server)

Config is loaded by merging env vars (`MYSQL_DSN`, `JWT_SECRET`, `PORT`, etc.) with `config.json` (file values override env). Default config path is `config.json` relative to the binary's working directory.

Game constants (tick intervals, prices, tax rates, etc.) are hardcoded in `internal/config/config.go` — these are ported from legacy `backend/config.py`.

## Key conventions

- **Package manager**: pnpm only for `jjs-web`. The repo has a `pnpm-workspace.yaml` but no root `package.json`.
- **Go module name**: `jjs-server` (matches directory name, not a full import path).
- **Auth**: bcrypt for passwords, JWT HS256 for tokens. Legacy code used SHA-256 — never copy that pattern.
- **UI color convention**: Chinese-style red for price rise, green for fall (opposite of Western convention). See `docs/UI_STYLE_GUIDE.md` for the full design token mapping that is reflected in `tailwind.config.ts`.
- **Passwords**: `MinPasswordLen = 3` (intentionally low for game, not a mistake).
- **No tests exist yet** — test infrastructure is P8 in the roadmap. There are no test commands to run.
- **No CI, no pre-commit hooks, no Makefile** — everything is manual for now.

## Directory boundaries

```
.
├── backend/          # LEGACY — reference only, do not modify
├── frontend/         # LEGACY — reference only, do not modify
├── docs/             # Design docs & rewrite roadmap
├── jjs-server/       # NEW Go backend — active development
│   ├── bin/          # Built binary + runtime config
│   ├── cmd/server/   # Entrypoint
│   ├── internal/     # config, domain, store, handler, middleware
│   └── web/          # Target for frontend build output (SPA serving)
├── jjs-web/          # NEW React frontend — active development
│   └── src/          # api/, stores/, pages/, components/, types/
├── simulate_v2.py    # Monte Carlo validation for v2 economics
└── stock_game.db     # Legacy SQLite DB (gitignored, not used by new code)
```

## Non-obvious gotchas

- The Go server serves SPA fallback from `web/` directory (`internal/middleware/static.go`). To deploy frontend: build `jjs-web` with `pnpm build`, then copy `dist/` contents into `jjs-server/web/`.
- `jjs-server/config.json` is gitignored. You must create it manually for local dev. Look at `bin/config.json` for the real-world format (contains production DB credentials — do not commit).
- `stock_game.db` is gitignored and belongs to the legacy Python backend. The new Go backend uses MySQL exclusively.
- Legacy `game_engine.py` is a 3370-line god module — the rewrite intentionally splits this into separate Go packages.
