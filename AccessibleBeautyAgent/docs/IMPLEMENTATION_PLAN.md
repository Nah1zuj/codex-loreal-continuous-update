# Accessible Beauty Agent implementation plan

Goal: implement the supplied hackathon specification in a runnable Windows project, with no paid credentials required.
Spec: SPECIFICATION.txt (unaltered user brief).
Architecture: React/Vite TypeScript client, FastAPI services, SQLite consent-based memory, JSON knowledge and an in-process hybrid index. Tool results govern agent outputs. Mock providers are explicitly identified.

## Constraints and decisions
- All writes stay inside D:\AccessibleBeautyAgent; no Docker or databases requiring servers.
- Native inline execution per user's instruction to execute immediately. The supplied detailed spec replaces additional design approval rounds.
- Use OpenCV Haar face and eye landmarks as a dependency-stable local equivalent; pose/occlusion are coarse heuristics, not calibrated measurements.
- Hashed token embeddings are a deterministic lexical proxy, not learned semantic understanding. Remote embedding adapter supports actual semantic retrieval.
- Camera and memory consent cannot be inferred from free text or model output.
- Test invalid image, missing face, unknown IDs, revoked consent and out-of-order session actions.

## Tasks and checks
- [x] 1. Create base API, configuration and schema; health and validation tests.
- [x] 2. Create SAMPLE looks/routines/products/reference data; validate schema and dinner retrieval.
- [x] 3. Implement parent-child ingestion, hybrid search, filters and rerank interface; run RAG tests.
- [x] 4. Implement session transitions and tool harness; run command and full routine tests.
- [x] 5. Implement quality gate, providers and consensus; run gate bypass/confidence tests.
- [x] 6. Implement SQLite memory and feedback consent; run persistence and deletion tests.
- [x] 7. Build accessible frontend, consent camera capture, voice fallbacks and debug panel; typecheck/build and browser checks.
- [x] 8. Add startup/KB scripts and documentation; run complete regression suite and live API smoke checks.

## Progress ledger
Environment: Python 3.13.11, Node 24.13.0, npm 11.6.2; D: available; new isolated repository on implementation branch.
Remote providers will be implemented but remain unverified without credentials. Qwen realtime is a documented placeholder, browser push-to-talk/TTS is the tested fallback.
Native review: consent must remain strict boolean; failed gate blocks evaluator; mock marker survives confidence handling; deletion rebuilds profile; captured bytes excluded from trace. All covered by regression tests.
Verified: 32 backend + 4 frontend tests; frontend production build; 0 npm audit vulnerabilities; KB validate/index; live smoke and complete browser mock journey. Physical camera/mic and remote credentials are not tested.
Ruling: keep startup index rebuild rather than consuming an old snapshot, so manual KB edits cannot be silently stale. Costs one in-memory index build at startup.
Ruling: use isolated sample fixtures for regression after real KB replacement, preventing user knowledge edits from invalidating deterministic demo expectations.
Fresh reviewer: two P2 issues reproduced and fixed (old consent when creating new session; continue after pre-routine check). Regression suite 32 passed; browser verified prior session COMPLETE/camera_consent=false after New Session. Build/frontend tests passed after fixes.
