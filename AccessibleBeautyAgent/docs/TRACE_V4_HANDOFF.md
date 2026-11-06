# TRACE V4 handoff

Branch: `trace-v4-full-look`. Start from `start-dev.ps1 -NoBrowser`, then open `http://127.0.0.1:5173/`. The demo path is Entry → Voice → café prompt → Today's Look → THREAD/ECHO optional → local section edits → IMPRINT consent.

Core implementation lives in `backend/app/full_look`, `backend/app/policies`, `backend/app/routes/full_look.py`, `frontend/src/pages/Entry.tsx` and `frontend/src/pages/FullLook.tsx`. Existing canonical knowledge changes and the user's two root scripts were deliberately preserved rather than folded into V4 commits. Do not rerun `trace_stage_softformal.py --commit` blindly.

Review boundaries: material/product/source candidates are DRAFT; image assets have unknown rights; research is mainly abstract-level; no visual accuracy metric exists. Before production, conduct human content review, consented device/accessibility testing and a separate privacy-reviewed vision evaluation.

Rollback uses the Phase0 snapshot path recorded locally in `work/v4_backup_path.txt`. It includes a consistent SQLite backup. Never publish that private backup or `.env`.
