# TRACE V4 implementation log

## Phase0
Backup verified; user changes preserved. ZIP listings confirm specifications only. Backend isolated mock 65 PASS, frontend18 PASS/buildPASS. Corrected initial audit command removing pytest basetemp (fixture path errors) rather than changing application constraints. Checkpoint contains docs/ignore only; user canonical edits remain unstaged.

## Phase1 — shared session and three entry modes

Added equal Voice / Visual / Text entry choices, `/voice`, `/explore` and `/full-look`, while retaining every legacy route. All modes use one session and one Agent; a refresh restores the server-owned current step and latest plan. Browser microphone and TTS remain user-triggered. Frontend structural and rendered checks passed.

## Phase2 — six-domain Today's Look

Added strict FullLook schemas and session-scoped plan/revise/confirm endpoints. Six sections are skincare, makeup, hair, outfit, accessories and fragrance. Expected-version checks reject stale edits; scoped edits preserve confirmed sections. A review-found bug was fixed so skincare/makeup edits include a target domain and makeup edits retain the selected look/routine link.

## Phase3 — material and garment-label boundaries

Added eight DRAFT material entries with source links and text/TTS comparison. Fiber and structure are distinct. DOT garment mode only reports visible label text; low confidence or uncertain characters clears composition. A regression test proves photo-like, negative and uncertain cotton wording cannot become confirmed cotton composition.

## Phase4 — evidence, products and assets

Registered 9 primary research sources (mostly abstract-level), 4 official-group product candidates and 27 candidate image hashes. All product/material records remain DRAFT; all candidate images have unknown rights and are prohibited from public use. No source was promoted into production RAG automatically.

## Phase5 — runtime policies

Six versioned v4 policy files are loaded at runtime and exposed by safe name/version/hash metadata in health. Provider-path tests prove the text and visual/reading prompts consume them. Camera and memory consent remain code-enforced state transitions.

## Phase6 — regression and handoff

Fresh isolated verification: backend 82 PASS; frontend 24 PASS; TypeScript/Vite build PASS; knowledge validation PASS. Browser verified Entry → Voice café prompt → shared Visual session → Full Look → confirm makeup → change only outfit. `.env` hash matches the Phase0 backup. MediaPipe is EXPERIMENTAL_NOT_READY because neither the package nor a local `.task` model is present; this does not block the text-first MVP.
