# Legacy Architecture — Big Cat Investment v1

This document preserves the architecture of the original Big Cat Investment game before the full rewrite (v1 → v2). The legacy code (`backend/`, `frontend/`) was deleted after this summary was captured. For the current architecture, see `docs/ARCHITECTURE.md`.

## Project History

The original game was built as a single-developer project with Python + FastAPI + SQLite backend and a vanilla JS frontend. After months of development, the architecture showed signs of strain:

- **`backend/game_engine.py`**: 3370-line god module handling AI trading, order matching, company operations, quarterly settlement, market making, SEC regulation, leaderboards, and more—all in one file
- **No type safety**: Python dynamic types led to runtime errors in production
- **Global mutable state**: `gameState.js` on the frontend, `GlobalMarketState` dict on the backend—mutations scattered across files
- **SQLite single-file DB**: No concurrent write safety, no migrations
- **SHA-256 password hashing**: Custom salt + token scheme instead of bcrypt

The decision was made to do a **full rewrite** (not incremental refactor) as documented in `docs/REFACTORING_ROADMAP.md`. New code lives in `jjs-server/` (Go + chi + GORM + MySQL) and `jjs-web/` (React 18 + TypeScript + Vite).

---

## Legacy Backend (`backend/`)

**Stack**: Python 3.10+, FastAPI, SQLAlchemy (async), SQLite (aiosqlite)

**Total**: 5407 lines across 11 files

### File Inventory

| File | Lines | Purpose |
|------|-------|---------|
| `__init__.py` | 0 | Package marker |
| `config.py` | 25 | All game constants: starting cash, prices, fees, margins, tax rates |
| `database.py` | 22 | SQLAlchemy async engine + session factory + `init_db()` auto-create tables |
| `models.py` | 141 | SQLAlchemy ORM models: `User`, `Transaction`, `PlayerState`, `Holding`, `Company`, `CompanyQuarterly` |
| `schemas.py` | 117 | Pydantic request/response models: auth, market, company, WS messages |
| `industry_config.py` | 39 | 6 industry definitions with names, descriptions, base PE ratios, startup parameters |
| `company_engine.py` | 318 | v1 company lifecycle: create, quarterly settlement, cash actions, decisions |
| `game_engine.py` | 3370 | Monolithic engine: in-memory market state, AI bot trading (4 types), NPC/market maker, order matching, price tick loop, K-line aggregation, SEC regulator, forced liquidation, leaderboard, DB flush |
| `websocket_manager.py` | 94 | Room-based WebSocket connection manager with auto-reconnect support |
| `main.py` | 101 | FastAPI app factory: lifespan, CORS, router registration, static file serving middleware |
| `routers/__init__.py` | 0 | Package marker |
| `routers/auth.py` | 85 | Login/register endpoints, SHA-256 password hashing, token-based auth, `get_current_user` dependency |
| `routers/ws.py` | 141 | WebSocket upgrade endpoint, player state recovery from DB, WS message dispatch |
| `routers/market.py` | 480 | Market info, stock list, player portfolio, leaderboard, admin endpoints |
| `routers/company.py` | 474 | Company CRUD, quarterly reports, cash actions, admin management |

### Key Design Decisions (Legacy)

- **Auth**: SHA-256 with random 16-byte salt; 64-byte hex token stored in DB; passed via `x-auth-token` header
- **Engine**: All state in memory (`GlobalMarketState` dict) with periodic DB flushes every 30s via `DB_FLUSH_INTERVAL`
- **AI Bots**: 4 types running in separate asyncio tasks—`ai_trading_loop`, `npc_trading_loop`, `inst_trading_loop`, `hot_money_trading_loop`
- **Order Matching**: In-memory order book with FIFO queue per symbol, limit/market orders, no partial fill tracking in DB
- **K-lines**: 3 periods (1t, 4t, 20t) aggregated in memory, not stored in DB
- **SPA Fallback**: Custom ASGI middleware (`StaticFileMiddleware`) serves `frontend/` files with SPA fallback to `index.html`

---

## Legacy Frontend (`frontend/`)

**Stack**: Vanilla JavaScript, CSS 3, HTML 5 (no framework)

**Total**: 6542 lines across 10 files

### File Inventory

| File | Lines | Purpose |
|------|-------|---------|
| `index.html` | 535 | Single HTML page with all markup: auth forms, game panels, modals; SPA via `display:none` toggling |
| `css/style.css` | 2621 | Complete dark theme: CSS variables, 12+ panel layouts, responsive breakpoints, animations, Chinese red-up/green-down colors |
| `js/api.js` | 25 | Minimal fetch wrapper: `apiPost()` and `apiGet()` with auto-attached auth token |
| `js/auth.js` | 156 | Auth UI logic: tab switching, login/register handlers, lobby management |
| `js/gameState.js` | 38 | Global mutable state object: player info, stocks, holdings, orders, candles, UI state |
| `js/websocket.js` | 76 | WebSocket client: exponential backoff reconnect, `wsConnect(playerId)` with query param auth |
| `js/main.js` | 351 | WS message dispatch: price updates, portfolio updates, K-line rendering, order book, trade tape, UI refresh |
| `js/utils.js` | 45 | Helper functions: number formatting, element creation, DOM utilities |
| `js/ui/game.js` | 1847 | All game UI logic: stock info bar, trade form, portfolio table, order management, company panels, leaderboard, admin panel |
| `js/kline.js` | 1378 | Canvas-based K-line chart renderer: candlestick drawing, MA overlays, MACD/KDJ/RSI/BOLL indicators, crosshair, zooming |
| `js/lightweight-charts.js` | 7 | Placeholder/stub for TradingView library (not actually used) |

### Key Design Patterns (Legacy)

- **State**: Single global `gameState` object, mutated directly from WS handlers and UI callbacks—no immutability, no change detection
- **DOM**: Direct DOM manipulation (`innerHTML`, `createElement`, `classList`) with string-based IDs and global event handlers (`onclick=`)
- **Charts**: Hand-drawn Canvas 2D API with custom crosshair, indicator overlays (MACD, KDJ, RSI, BOLL), candle/volume rendering
- **Color Convention**: Chinese market style—red for price rise (阳线), green for price fall (阴线)
- **WS Auth**: Player ID passed as query parameter (`/ws?player_id=...`), no JWT

---

## Migration Decisions

| Layer | Legacy (v1) | New (v2) | Rationale |
|-------|-------------|----------|-----------|
| Language | Python 3.10 | Go 1.24 | Performance, native concurrency (goroutines), single-binary deploy |
| API Framework | FastAPI | chi v5 | Lighter, stdlib-compatible, no code generation |
| ORM | SQLAlchemy async | GORM | Go-standard, AutoMigrate, better MySQL support |
| Database | SQLite | MySQL 8.0+ | Production-grade, concurrent write safety, migrations |
| Auth | SHA-256 + salt + static tokens | bcrypt + JWT HS256 | Industry standard password hashing, expiring tokens |
| Engine State | In-memory dict + periodic flush | GORM DB-driven with tick goroutines | Crash safety, audit trail, no state loss |
| AI Traders | 4 types in asyncio tasks | 6 types in goroutines, v2 cigar-butt model | Simplified valuation model, configurable count |
| Frontend | Vanilla JS | React 18 + TypeScript | Type safety, component model, ecosystem |
| Charts | Canvas hand-drawn | lightweight-charts v5 | Professional-grade, maintainable, feature-rich |
| State Mgmt | Mutable global object | Zustand + TanStack Query | Predictable state, server cache, optimistic updates |
| Build | None (raw files) | Vite | HMR, TypeScript, CSS post-processing |
| Color Convention | Red-up / Green-down | Red-up / Green-down | Preserved (Chinese market) |

## Why Delete the Legacy Code

1. **Read-only reference is fragile** — without active builds/tests, legacy code inevitably drifts from reality
2. **Design docs document intent better** — `docs/AI_TRADER_DESIGN.md`, `docs/ARCHITECTURE.md`, `docs/UI_STYLE_GUIDE.md`, etc. explain the *why* behind decisions
3. **Newcomer confusion** — two stacks in one repo creates onboarding friction ("which code do I edit?")
4. **Git history preserves everything** — deleted files remain accessible via `git log` and `git show`

## Restoring Legacy Code

If needed, recover from git history:

```bash
# Find the last commit before deletion
git log --all -- backend/ frontend/

# Restore specific directories
git restore --source <commit-hash> -- backend/
git restore --source <commit-hash> -- frontend/
```
