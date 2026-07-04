# Tasks — Legacy Cleanup & Documentation

## Task 1: Create legacy architecture summary doc ✅

Write `docs/LEGACY_ARCHITECTURE.md` covering:
- Project history and why the rewrite happened
- Legacy backend architecture (Python FastAPI + SQLAlchemy + SQLite)
  - File-by-file inventory with what each file does
  - Engine design (god module `game_engine.py`, 3370 lines)
  - Auth design (SHA-256 + salt + static tokens)
  - WS message formats
- Legacy frontend architecture (vanilla JS)
  - File-by-file inventory
  - State management pattern (mutable global `gameState`)
  - Chart implementation (Canvas hand-drawn K-line)
  - CSS dark theme and color convention
- Migration decisions table (legacy vs new, with rationale for each)
- Why delete after documenting

**Reference**: `openspec/changes/clean-up-unnecessary-files/design.md` Phase 1 section

## Task 2: Delete legacy directories ✅

```bash
git rm -r backend/
git rm -r frontend/
```

- Remove all tracked files in `backend/` (14 files) ✅
- Remove all tracked files in `frontend/` (12 files) ✅
- Verify no broken references in new code (should not import from legacy) ✅

## Task 3: Remove root-level legacy files ✅

```bash
git rm requirements.txt
git rm docs/DEPLOY.md
```

- `requirements.txt` — Python dependency file (already gitignored, but tracked) ✅
- `docs/DEPLOY.md` — deployment doc describing deprecated nginx architecture ✅

## Task 4: Update `.gitignore` ✅

Remove legacy-specific entries:
- `requirements.txt` — no longer tracked ✅
- `backend/requirements.txt` — directory deleted ✅
- `backend/admin_trade.py` — directory deleted ✅
- `qr_share.png` — legacy artifact ✅
- `stock_game.db` — SQLite DB (keep `.db` glob if desired) ✅

Keep generically useful patterns.

## Task 5: Update reference index in roadmap ✅

In `docs/REFACTORING_ROADMAP.md`, update the "旧代码参考索引" section:
- Replace individual file references (e.g., `backend/config.py`, `backend/models.py`) with a single link to `docs/LEGACY_ARCHITECTURE.md` ✅
- Mark P8.4 cleanup subtask as completed (✅) ✅

## Task 6: Verify nothing is broken ✅

- `git status` — confirm only intended files are staged ✅
- `git diff --stat` — review scale of changes ✅
- Read through `docs/LEGACY_ARCHITECTURE.md` for accuracy ✅
- Confirm `jjs-server/` and `jjs-web/` build/run normally (optional smoke test)
