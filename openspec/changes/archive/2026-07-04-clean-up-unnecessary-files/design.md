# Design — Legacy Cleanup & Documentation

## Overview

Two-phase approach: (1) document, then (2) delete.

## Phase 1: Create Legacy Architecture Summary

Create `docs/LEGACY_ARCHITECTURE.md` (the new file intentionally lives alongside the other active docs) that captures:

### Legacy Backend (`backend/`)

| Aspect | Detail |
|--------|--------|
| Framework | Python FastAPI + SQLAlchemy ORM + SQLite (aiosqlite async) |
| Auth | SHA-256 password hashing with random salt, static token-based sessions |
| Engine | `game_engine.py` (~3370 lines, single god module) — company operations, market making, order matching, quarterly settlement |
| Industry | `industry_config.py` — 6 industry definitions with base parameters |
| Company | `company_engine.py` — v1 company lifecycle (no v2 features like AP/board/R&D) |
| DB | SQLite via `stock_game.db`, single-file, no migrations |
| WS | `websocket_manager.py` — simple connection manager + `schemas.py` message types |
| Routes | FastAPI routers in `routers/` — auth, market, company, ws |
| Config | `config.py` — all magic numbers and game constants |

### Legacy Frontend (`frontend/`)

| Aspect | Detail |
|--------|--------|
| Stack | Vanilla JavaScript, CSS, HTML (no framework) |
| Auth | `auth.js` — login/register form logic |
| Game UI | `ui/game.js` — all game interface logic (company panel, trade form, etc.) |
| Charts | `kline.js` — Canvas-based K-line chart (hand-drawn, no library) |
| Data | `gameState.js` — global state object, mutation-heavy |
| Network | `api.js` — fetch wrapper, `websocket.js` — WS client with heartbeat |
| Styling | `css/style.css` — 2621 lines, dark theme, Chinese red-up/green-down color convention |
| Entry | `index.html` — single HTML file with all markup, SPA-style page switching via display:none |

### Migration Decisions

| Decision | Legacy | New | Rationale |
|----------|--------|-----|-----------|
| Language | Python | Go 1.24 | Performance, goroutine concurrency, single binary deploy |
| API framework | FastAPI | chi v5 | Lightweight, closer to stdlib, no codegen |
| ORM | SQLAlchemy | GORM | AutoMigrate, better Go ecosystem fit |
| DB | SQLite | MySQL 8.0+ | Production reliability, concurrent writes |
| Auth | SHA-256 + salt | bcrypt + JWT HS256 | Industry standard for password hashing |
| Frontend | Vanilla JS | React 18 + TS | Type safety, component model, ecosystem |
| Charts | Canvas hand-drawn | lightweight-charts v5 | Professional-grade, fewer bugs |
| State | Mutable global object | Zustand + TanStack Query | Predictable state management |
| Color | Red-up/Green-down | Red-up/Green-down | Preserved from legacy (Chinese convention) |

### Why Delete Instead of Keeping

1. **Read-only reference is fragile** — without active builds/tests, legacy code inevitably diverges from reality
2. **Design docs are better references** — `docs/AI_TRADER_DESIGN.md`, `docs/ARCHITECTURE.md`, `docs/UI_STYLE_GUIDE.md` document intent, not just implementation
3. **Newcomer confusion** — two stacks in one repo creates onboarding friction
4. **Git history preserves everything** — deleted files remain accessible via `git log` and `git show`

## Phase 2: Delete Files

After the summary doc is committed, remove:

```
backend/          → rm -rf
frontend/         → rm -rf
requirements.txt  → rm (already gitignored)
docs/DEPLOY.md    → rm
```

### `.gitignore` Changes

Remove legacy-specific entries that no longer apply:
- `requirements.txt` — no Python deps to ignore
- `backend/requirements.txt` — same
- `backend/admin_trade.py` — no Python admin scripts
- `qr_share.png` — legacy artifact
- `stock_game.db` — SQLite DB no longer exists (the `.db` glob still catches others)

Keep generically useful ones: `__pycache__/`, `*.pyc`, `*.log`, `node_modules/`, `dist/`, etc.

### Update Roadmap Reference Index

In `docs/REFACTORING_ROADMAP.md`:
- Update "旧代码参考索引" (legacy code reference index) section to point to `docs/LEGACY_ARCHITECTURE.md` instead of individual legacy files
- Remove or mark as done the P8.4 subtask about cleanup

## Rollback Plan

If for any reason the legacy code is needed again:
- `git log --all -- backend/frontend` to find the last commit before deletion
- `git restore --source <commit> -- backend/` to recover specific files
- Or check `docs/LEGACY_ARCHITECTURE.md` for the architectural summary
