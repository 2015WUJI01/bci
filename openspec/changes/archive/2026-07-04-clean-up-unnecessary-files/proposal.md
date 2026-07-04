# Clean Up Unnecessary Files

## What

Remove legacy/dead code and outdated documentation from the repository that is no longer relevant to the active development. Before deletion, capture the legacy architecture knowledge in a summary document.

## Why

The project has completed a full rewrite from Python+FastAPI+SQLite+vanillaJS to Go+chi+GORM+MySQL+React+TypeScript (see `docs/REFACTORING_ROADMAP.md`). The old code (`backend/`, `frontend/`) is:

1. **Dead code** — no longer built, deployed, or maintained
2. **Reference only** — originally kept as design reference, but the design docs (`docs/ARCHITECTURE.md`, `docs/AI_TRADER_DESIGN.md`, `docs/UI_STYLE_GUIDE.md`, etc.) now serve that role
3. **Confusing** — new contributors see two sets of code and may not know which is active
4. **Outdated** — `docs/DEPLOY.md` describes an nginx-based deployment that contradicts the current Vite + Go static file approach
5. **Orphaned** — `requirements.txt` references Python packages for a system that no longer exists

The rewrite roadmap's P8.4 ("收尾") already schedules this cleanup. This change executes it early and, before deleting, preserves the architectural knowledge of the legacy system in a single document.

## Scope

### Delete

| Path | Reason |
|------|--------|
| `backend/` | Legacy Python FastAPI backend — all API endpoints and engine logic have been rewritten in Go |
| `frontend/` | Legacy vanilla JS frontend — rewritten in React 18 + TypeScript |
| `requirements.txt` | Root-level Python requirements for legacy backend (already gitignored) |
| `docs/DEPLOY.md` | Deployment doc describing nginx + separate directory layout that contradicts current Vite proxy dev flow |

### Preserve in summary doc before deletion

- Legacy architecture overview (Python FastAPI + SQLAlchemy + SQLite + vanillaJS)
- Key file inventory per directory
- What each component did
- Migration decisions (why bcrypt > SHA-256, why GORM > SQLAlchemy, why chi > FastAPI, why React > vanillaJS)
- Color convention rationale (Chinese red-up/green-down)

### Not in scope

- `simulate_v2.py` — still used for P8 numerical validation
- `docs/` design docs — actively maintained and referenced by the new codebase
- `jjs-server/` and `jjs-web/` — active development code
