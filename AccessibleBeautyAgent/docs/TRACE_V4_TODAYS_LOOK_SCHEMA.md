# TRACE V4 Today's Look schema

`Session.todays_look` is the authoritative, session-scoped plan. It contains `plan_id`, `session_id`, scene, candidate impression, `review_status=DEMO_CURATED`, monotonically increasing `version`, uncertainties, confirmed sections and six required sections.

Each section has `state` (`proposed | confirmed | skipped`), optional suggestions, material IDs and optional makeup `look_id` / `routine_id`. Suggestions include bilingual names, reason, source references, review status and `user_override`. The required domains are `skincare`, `makeup`, `hair`, `outfit`, `accessories`, `fragrance`.

Revision requests may include `target_sections`, per-domain constraints and `expected_version`. Only changed sections are replaced; previously confirmed unrelated sections remain byte-for-byte stable. A stale version returns HTTP 409. A scope mismatch also returns 409 before mutation. Confirming a section changes only the current session and never writes durable memory.

Materials use stable IDs and `kind=fiber|structure`. Cotton, linen, wool, silk, polyester and viscose are fibers; satin and knit are structures. `verification_status=DRAFT` is displayed. Composition may come from a readable garment label, official product data or an explicit user statement. A photo appearance, uncertain statement or negative statement must keep composition unknown.

Durable preferences are proposed through `/api/full-look/memory-candidate`, shown in IMPRINT, and saved only by a separate original `memory_consent=true` action.
