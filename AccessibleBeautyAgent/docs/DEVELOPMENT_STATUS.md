# Development status · 2026-10-06

## DONE

**IMPLEMENTED**
- Runnable React/Vite/TypeScript frontend and FastAPI/Pydantic/Uvicorn backend; Windows setup/start scripts, loopback listeners, readiness checks, health/OpenAPI.
- Explicit stage machine with legal transitions and routine state; one-step commands repeat/slow/why/skip/stop/check/stop-camera.
- Tool harness for profile, Look, products/comparison, routines, visual checks, feedback and consent-bound memory save/delete.
- Five canonical KB input types, schema and cross-link validation, parent-child hierarchy, local flat vector storage/snapshot, lexical+vector ranking, metadata filters and reranker interface.
- 3 looks, 3 routines and 12 sample products in interchangeable JSON; explicit SAMPLE tags. Immutable regression fixtures under data/demo/knowledge.
- getUserMedia camera adapter, explicit one-time consent, 0/250/500ms three-frame JPEG capture, resizing, unmirrored raw data, track cleanup and revocation.
- OpenCV face and eye-center landmark proxy gate, ROI lighting/blur, coarse face-size/pose/occlusion flags; failed gates block all makeup evaluation.
- Visual schemas, three-frame reliable majority and disagreement penalty, configured confidence thresholds and uncertainty language.
- SQLite episodic memory and derived profile memory, strict write consent and owner-scoped deletion; no image/audio persistence.
- Accessible semantic UI, large controls, focus styles, polite status, text/PTT/TTS adapters, memory screen and hideable Debug.
- Real Qwen HTTP adapters for intent, visual measurement, embedding and reference draft generation (credential tests pending).
- README, architecture/API/runbook/KB guides, validation/ingestion/rebuild/draft scripts.

**MOCKED**
- Language intention in default mode uses deterministic keyword rules.
- Visual presence in default mode is selectable deterministic simulation; every response explicitly labels simulated observations.
- MockEmbeddingProvider is a hashed bag-of-words proxy, not learned semantic retrieval.
- Reference analyzer default emits unknown values and unverified flags; current reference case does not represent analyzed real media.
- All demo products, Look content and reference data are SAMPLE, unverified and replaceable.

## WORKING

- Full mock journey: dinner → soft_formal → base/blush/lip steps → single-check consent → mock structured vision → continue → feedback → preview candidate → explicit save/decline.
- Live API smoke passed: backend health, frontend HTTP, dinner matching, scene-filtered RAG, structured mock vision, refused no-consent memory write, persisted-and-deleted disposable test memory.
- Backend: **32 tests passed**. Includes requested 8 acceptance cases plus real blank-image gate, normal-mode demo rejection, schema validation, state commands, low confidence, provider failure, metadata parent links and persistence/deletion.
- Frontend: **4 tests passed**, TypeScript and Vite production build passed. npm audit: **0 vulnerabilities**. pip check: no broken requirements.
- KB validation: 3 looks / 3 routines / 12 products / 1 reference / 41 parent-child documents. Local index snapshot generated.
- In-app browser: complete consent/save journey verified, app console errors absent; desktop 1280×900 and mobile 390×844 have no horizontal overflow. Camera off before consent and after simulated check verified.

## NOT IMPLEMENTED

**PLACEHOLDER**
- Qwen realtime voice/WebRTC transport: endpoint advertises unavailable realtime and working browser/text fallback.
- RemoteRerankerAdapter: callable transport interface exists; no chosen remote reranking endpoint.

**FUTURE / OUT OF P0**
- MediaPipe full face mesh and calibrated head-pose/occlusion estimation.
- Fine blush symmetry/gradient, millimeter lip boundaries, personalized face geometry.
- Production authentication, multiuser authorization, session TTL, durable multi-instance orchestration and deployment.
- Video full-stream AI analysis is not implemented; local selected-frame extraction and image batch drafts are implemented in Phase 2.
- Beauty scoring/emotion recognition are excluded from product scope.

## BLOCKED

- No Qwen API key was supplied, so real chat/vision/embedding/reference calls are **unverified**, despite implemented adapters. Local mock does not need a key.
- Physical camera/microphone capture and live speech recognition were not exercised. Browser UI flow and capture adapter unit checks passed; real hardware permissions remain user-controlled.
- No representative face or real Beauty KB was supplied; gate/model accuracy and knowledge correctness are not validated. OpenCV pose/occlusion flags are explicitly coarse heuristics.

## NEXT

1. Replace the five files in data/knowledge according to KNOWLEDGE_BASE_GUIDE; review sources and mark references verified only after manual review.
2. When authorized, configure DeepSeek separately for chat/vision and validate real outputs; remote AI is disabled for now.
3. Test camera and browser speech on the demo laptop; retain text and simulation fallback for presentation.
4. Add calibrated landmarks/realtime/reranking behind existing interfaces if the hackathon schedule permits.

No known failing test or build remains. No API keys are in source control. Dependencies are locked; generated work/index/memory files are ignored.

Final independent review found and resolved two state issues: new-session creation now stops the previous backend session and revokes its consent; continuing after a pre-routine check starts the first routine step. The latter has a RED→GREEN regression, the former was verified through the browser and old-session HTTP state.
Windows setup now refuses active development ports before replacing dependencies; stop servers before reinstalling to avoid esbuild file locking. Complete setup was rerun successfully after repair.

## Phase 2 verification (2026-10-07)

Backend 59 tests and frontend 7 tests passed; production build passed. Seven-sheet XLSX roundtrip accepted all 7 rows, no rejected rows. Live browser verified admin pages, XLSX preview, synthetic demo upload → mock draft → light_medium edit → signed review → protected reanalysis → rebuild 42 docs → Dinner retrieval with Soft Formal and reviewed demo reference. Real media interpretation remains unverified; synthetic reference is marked demo_data=true and excluded from production. Later review/QA details are recorded in PHASE2_ACCEPTANCE.md.

## Phase 3 TRACE (2026-10-07)

DONE: TRACE identity and five bilingual functional modules; Home redesign, centralized copy/tokens and reusable dot/progress/memory components; DOT single-use consent + explicit mock/uncertain reading endpoint; PAIR existing API two-option comparison; IMPRINT editable owned memory; separate Story and real Dinner Demo, persistent demo URL flag. Public errors are human-readable; admin/Agent/RAG schemas and existing APIs retained. Decorative geometry is never described as real Braille.

Verification: backend 65 passed, frontend 17 passed, TypeScript/Vite build passed, desktop/mobile/keyboard and real mock Dinner browser flows checked. Independent final review fixes confirmed. Full A–N report and limitations: PHASE3_ACCEPTANCE.md. Research and Braille sources: NEEDS SOURCE VERIFICATION. No remote model calls. English UI prepared; KB/Agent primarily Chinese. Actual hardware/screen-reader/reduced-motion OS behavior and model accuracy await target-device testing. In-progress sessions remain transient across refresh; restart Dinner.

Next: supply verified papers and product evidence, refine prompts from bounded source-backed claims, populate reviewed production knowledge, authorize/configure and validate DeepSeek when ready, then test with target users and presentation hardware. Knowledge current canonical file count is six (including accessibility_guidance), superseding the early five-file instruction above.
