# TRACE V4 implementation plan

Goal: Shared Agent with three entry choices, six-domain incremental Today's Look, material text/voice, preserved makeup/consent workflows.
Architecture: Extend existing Session/ChatRequest/MemoryCandidate; FullLookService operates on same session under existing lock. Presentation modes share App state and session ID. Versioned policy registry feeds intent/visual/reading and constrains deterministic planner.
Spec: user supplied TRACE Harness V4 (2026-10-11). Continuous execution Phase0–6 authorized; no phase approval needed.
Constraints: writes inside project; preserve .env and dirty data; no automatic verified promotion or private media upload; no heavy dependency/framework migration.
Review: stale revision versions; confirmed sections untouched; camera/memory consent independent; unknown material composition never inferred; unavailable provider fallback honest.

- [x] Phase0: read inputs, data/SQLite/source backup, network-isolated original tests, baseline/API audit, checkpoint.
- [ ] Phase1: Entry/Voice/Explore/Text shared session and media release; frontend tests/build; checkpoint.
- [ ] Phase2: schemas full_look.py, full_look/service.py, routes/full_look.py; Session fields; cafe integration in harness; new API contract tests RED→GREEN; frontend six-domain UI; checkpoint.
- [ ] Phase3: overview/detailed/fallback controls; per-check camera handling and existing Gate preserved; safe return to Full Look; regression and checkpoint.
- [ ] Phase4: eight-material local dictionary/API/PAIR, garment DOT strict unknown percentages, scoped revision and explicit material memory; tests/checkpoint.
- [ ] Phase5: source/evidence/product/asset candidate audit, six runtime policy files + registry linked in harness/providers/reading/vision; regression evidence, no production auto-review; checkpoint.
- [ ] Phase6: capability levels, optional isolated landmarker experiment if possible, final end-to-end/API/browser/mobile tests, docs/runbook/handoff, fresh review, checkpoint.

Backend test command keeps pytest's project-local --basetemp and all remote providers disabled via process environment. Real provider smoke separate; do not send user photos. Final tests report actual counts, not historical baseline.
