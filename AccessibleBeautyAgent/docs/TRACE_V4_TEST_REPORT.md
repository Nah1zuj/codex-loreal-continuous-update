# TRACE V4 test report

Date: 2026-10-11. Host: Windows, local project. Automated tests forced all providers to mock and `ALLOW_REMOTE_AI=false`; they did not consume the configured text API or upload images.

| Check | Result | Evidence |
|---|---|---|
| Backend regression | PASS | `python -m pytest --basetemp=work/v4-release -o addopts='' -q`: 82 passed in 17.17s |
| Frontend tests | PASS | `npm test`: 6 files, 24 tests |
| Frontend production build | PASS | `npm run build`: TypeScript clean, 67 modules transformed |
| Knowledge validation | PASS | 3 looks, 3 routines, 8 reference cases, 12 products, 12 guidance, 18 sources |
| Runtime policy registry | PASS | health reports v4 plus hashes for all six files |
| `.env` preservation | PASS | SHA-256 equals Phase0 backup; contents were not printed |
| Browser page/interaction | PASS | localhost Entry, Voice café flow, mode switch, Full Look, confirm makeup, black-dress scoped edit, 8 material cards |

Regression coverage includes stale versions, scope mismatch without mutation, same-session mode changes, explicit memory consent/refusal, camera refusal, local material comparison, garment-label uncertainty, provider prompt injection of policies, old routes and prior tests. Review regressions specifically cover old responses, skincare/makeup target scopes and uncertain/negative photo composition language.

Live status is truthful: DeepSeek text provider is configured and ready; V4 automated tests used mock. Vision, reading, embeddings and reference providers are mock. No real image, microphone, audible TTS, camera permission, screen reader or phone was exercised. MediaPipe package/model and a consented Gold Set are absent, so landmark and accuracy claims are NOT_TESTED / EXPERIMENTAL_NOT_READY.

The 14 requested scenarios are represented as: 1–5 and 7–8, 10–12, 14 implemented/tested through unit/API/browser checks; 6 only mock/uncertain fallback tested; 9 real garment photo NOT_TESTED (contract tested); 13 desktop DOM/reduced-motion/build tested while device/screen-reader/large-zoom remain NOT_TESTED.

## Realtime companion verification update — 2026-10-11

Supersedes the V4 totals above for this branch. Reviewed baseline HEAD `2180f38`; three browser-found frontend corrections remain under final review (mode switches preserve ended/paused calls; desktop video and guidance occupy adjacent columns).

| Check | Status | Exact evidence |
|---|---|---|
| Backend, all six providers mock, remote AI disabled | PASS | `D:\AccessibleBeautyAgent\.venv\Scripts\python.exe -m pytest --basetemp=work/task7-check -o addopts='' -q`: 100 passed in 27.52s, exit 0 |
| Frontend final regression | PASS | `npm --prefix frontend test`: 12 files, 104 tests, exit 0, 7.69s |
| Production build | PASS | TypeScript + Vite, 77 modules, 4.28s, exit 0 |
| Knowledge validation | PASS | LOOK 3, ROUTINE 3, REFERENCE_CASE 2, PRODUCT 12, ACCESSIBILITY_GUIDANCE 1, SOURCE 1; exit 0 |
| Whitespace/diff check | PASS | `git diff --check`, exit 0 |
| Real microphone / ASR / audible synthesis / physical camera | NOT_TESTED | No real permission accepted; synthetic fixture is separately labeled |
| Remote visual correctness / model training / real OCR | NOT_TESTED | Local simulated providers and generated test pixels cannot establish accuracy |
| Screen reader / mobile hardware / measured contrast | NOT_TESTED | DOM and CSS checks are limited structural evidence |

Backend command used process-scoped MODEL_PROVIDER, VISION_PROVIDER, READING_PROVIDER, REFERENCE_PROVIDER, EMBEDDING_PROVIDER and RERANKER_PROVIDER=`mock`, ALLOW_REMOTE_AI=`false`, PYTHONPATH=`backend;tests/regression`; `.env` was not changed or printed. Historical V4 configured-provider statements above do not describe this verification process.

TDD follow-up: ended Voice-to-Visual regression failed (1 failed/15 passed) because recognition restarted; restricting initial gesture start to Home made it pass. Stage/rail DOM regression failed (1 failed/16 passed) before grouping preview and consent controls into the left stage. Final full suite includes both regressions. Browser evidence and remaining limitations are recorded in TRACE_REALTIME_CALL_HANDOFF.md.

Actual local-browser synthetic lifecycle: PASS (manual final transcript, silent synthesis completion, one local abstract canvas track disposed on End, denied microphone/camera keep text fallback, remote frames remain off). Normal local browser English café flow and locale switching: PASS, coordinator observed no overflow at 390/1440px. These are local UI observations with mock backend; real hardware and remote accuracy remain NOT_TESTED. Preserved active-TTS navigation regression also passed; final frontend total is 104 tests.

Final coordinator review APPROVED, no remaining material issues. Browser synthetic active speech survived Video→Voice without increasing cancellation count (13), completion resumed recognition (4→5), End/mode switch kept starts at 5, and Home disposed all created tracks (2/2). Keyboard focus/navigation PASS. Home Chinese/English screenshot paths and exact limitations are in TRACE_REALTIME_CALL_HANDOFF.md.
