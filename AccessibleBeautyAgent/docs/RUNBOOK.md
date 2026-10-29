# Windows demo runbook

1. `cd D:\AccessibleBeautyAgent`; run `powershell -ExecutionPolicy Bypass -File .\setup.ps1` once.
2. Confirm `.env` has MODEL_PROVIDER/VISION_PROVIDER/EMBEDDING_PROVIDER=mock and DEVELOPER_MODE=true.
3. `powershell -ExecutionPolicy Bypass -File .\start-dev.ps1`; leave terminal open. Frontend 5173, backend 8000, logs under work.
4. Start conversation; dinner sample → soft_formal. Start routine, next to blush, check, explicitly consent.
5. For a stable presentation use the **Developer mock controls**. Pick BOTH, LEFT_ONLY or UNCERTAIN. Explain aloud these are simulated. No camera is required for this route.
6. Continue lip and optional final step, submit preference feedback, review candidate, choose save or decline.
7. Hide developer panel before audience view if desired. Data remains visibly SAMPLE; simulated visuals remain visibly marked.

## Checks

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/health
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe scripts\validate_kb.py
.\.venv\Scripts\python.exe scripts\rebuild_index.py
```

Frontend: `cd frontend; npm.cmd test; npm.cmd run build`.

## Troubleshooting

- Port in use: stop your own previous startup terminal with Ctrl+C. Script does not kill unrelated processes.
- npm PowerShell policy error: use npm.cmd or the provided -ExecutionPolicy Bypass script invocation. No persistent system policy change is made.
- Stop both development servers before running setup again: Windows locks the running esbuild binary. The installer checks active ports and refuses before replacing dependencies.
- Camera not available: use localhost/HTTPS and grant browser permission yourself. Use deterministic demo without camera if browser/hardware is unsupported. The app never opens camera without its own consent and a user click.
- Gate rejects: ensure one face in frame, reasonable distance, even frontal lighting, clear eyes, steady camera. Eye/pose proxy may falsely reject; no evaluative result is returned on failure.
- Low confidence: retry under better conditions; do not treat UNCERTAIN as actionable correction.
- Voice missing/network failure: text and buttons work. TTS depends on installed browser voices. Browser recognition may require an online vendor service.
- Missing key / remote 503: check .env region URL and model, or restore mock providers and restart. No fake remote result is substituted.
- Invalid KB: run validate_kb and correct required fields/duplicate IDs/Look links. Keep human_verified=false on unreviewed reference drafts.
- Provider changed: restart backend. If embedding remote is selected, startup needs key and connectivity to build index.
- Memory unexpected: review the visible records in Beauty Memory; only confirm deletion of records you intend to remove. Profile is rebuilt after deletion.

The startup command is the supported way to own server lifecycle. If started individually, stop each terminal with Ctrl+C. Do not delete SQLite just to fix a startup problem; it contains saved user preferences.

## Phase 2 knowledge operations

Follow KNOWLEDGE_BASE_WORKFLOW.md for upload/review/import. Remote calls are blocked by ALLOW_REMOTE_AI=false; keep it false for this phase. Admin Rebuild refreshes live services; saving alone does not. Production mode excludes demos and drafts. Local uploads/reports/history are ignored by Git; back them up separately before moving the project.
