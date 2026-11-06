# Phase 2 — human-reviewed Beauty KB production

Spec: PHASE2_SPECIFICATION.txt. Extend existing modules; preserve Phase 1 agent/camera/memory behavior. Native inline execution per explicit user instruction. No redesign. All writes remain inside this repository. No Qwen or other remote AI calls in this phase; mock remains enabled, remote access disabled by default. Prepare configurable DeepSeek adapter for later.

## Tasks
- [x] Consolidate canonical schemas and backward-compatible normalization; controlled vocabulary JSON and source provenance. Tests: invalid Look, duplicate IDs, broken source/Look/routine links.
- [x] Add transactional local JSON repository, history/version checks, authoritative human verification and deprecation. Test protected overwrite and optimistic conflicts.
- [x] Replace raw JSON RAG with readable parent/child documents; verified-only production filtering across retrieval and agent tools; debugger channels and safe live rebuild. Test parent integrity and unchanged canonical files.
- [x] Add CSV/XLSX templates/import with row reports, preview/commit and no silent invalid-row loss. Test missing cells, formula values, duplicates and workbook roundtrip.
- [x] Extend existing reference analyzer, upload/review APIs, batch drafts and video-frame selection. Test no auto-verification, image upload/review and protected revisions.
- [x] Add internal /admin/knowledge, /admin/references, /admin/rag via reusable form and API components; preserve main app. Run build/browser flows.
- [x] Document non-engineer research workflow, editable files, UI/module boundaries and future DeepSeek configuration; run all existing/new tests and live checks.

## Decisions
Keep existing flat canonical JSON filenames to avoid duplicate knowledge stores. Add sources.json, data/config, raw/frames/drafts/history/indexes. Canonical models are centralized in schemas/knowledge.py; old rag/knowledge.py model names re-export aliases, not duplicates.
Default production agent and RAG exclude drafts/demo/deprecated knowledge. Developer mode permits demo, research mode permits unverified; admin can explicitly preview draft results. Review edits require version and human confirmation; automated analysis/import never replaces verified records.
Main CSS stays independent from admin CSS. Structured editor derives fields from one schema descriptor and expandable vocabulary; layout/labels/components are replaceable without changing data or orchestration.
