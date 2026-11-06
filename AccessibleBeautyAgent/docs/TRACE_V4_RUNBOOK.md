# TRACE V4 Windows runbook

## Start

From `D:\AccessibleBeautyAgent`, run `powershell -ExecutionPolicy Bypass -File .\start-dev.ps1 -NoBrowser`. The script checks local ports; do not terminate an unknown process. Open `http://127.0.0.1:5173/`; API health is `http://127.0.0.1:8000/api/health`.

## Demo

Choose Voice, Visual or Text. Enter the café prompt, open Today's Look, confirm any section, then request a scoped change such as “我今天穿黑色连衣裙” or “我不想戴耳饰，也不想喷香水”. Compare exactly two materials. THREAD continues the existing makeup routine. ECHO and DOT require explicit camera consent; choose decline or clearly marked fictional demo when real capture is unsuitable. IMPRINT shows a candidate and requires explicit save/refuse.

## Verify

Use process-scoped mock provider environment variables, then run `python -m pytest --basetemp=work/v4-check -o addopts='' -q`. In `frontend`, run `npm test` and `npm run build`. Run `python scripts/validate_kb.py`. Do not alter `.env` for automated testing.

## Troubleshooting

If a page was open during Vite hot reload, reload once before judging an interaction. A stale plan returns 409; refresh restores the latest server version. If DeepSeek is unavailable, the explicit café demo falls back to curated local intent and text remains usable. TTS/ASR are browser capabilities; text input and visible replies are always the fallback. Vision uncertainty must result in retake/skip, never a guessed composition or left/right claim.

Stop only project-owned processes whose command line points to this checkout. Private backups are under `_backups`; do not commit or upload them.

## Realtime companion

Home Voice/Visual entry starts recognition in that click; direct `/voice` or `/explore` presents manual Start. Calls cycle Listening → Thinking → Speaking → Listening only after a final transcript and completed synthesis. Pause, Interrupt, End and text controls remain explicit. Switching between Voice and Visual keeps call state/session/step/plan; an ended or paused call requires manual restart/resume. Language switching pauses the call; resume uses the new language.

In Visual, Enable camera grants local preview only. Allow remote frames is a separate consent and needs an eligible blush/lip step. Configured service disclosure is visible. Remote samples are single images, at most every 2.5 seconds, with change gating, one request in flight and conservative failure/retake behavior. Close, Pause, End, page hide and route exit stop tracks and revoke consent. Preview alone has no automatic visual analysis.

Use all six process providers=`mock`, ALLOW_REMOTE_AI=`false` and PYTHONPATH=`backend;tests/regression` for isolated verification. Current commands/results and genuine NOT_TESTED limits are in TRACE_V4_TEST_REPORT.md. Do not change `.env` or imply that simulated results prove visual accuracy.

An ignored `frontend/work/realtime-proof.html` fixture, when present, is served by Vite at `/work/realtime-proof.html`. It imports the actual app and clearly substitutes recognition, silent synthesis and abstract canvas video. Buttons emit a final transcript, complete synthesis and toggle permission denial; the fixture status exposes starts/aborts/stops and track counts. It does not simulate actual hardware permission or intercept API requests. Serve only with the local mock backend; this helper is not a product route or deliverable.
