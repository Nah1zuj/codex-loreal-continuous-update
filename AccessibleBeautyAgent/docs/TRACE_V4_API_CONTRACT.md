# TRACE V4 API contract

Existing compatible endpoints: GET health/session/profile; POST chat/look/search/products/search/products/compare/rag/search/routine/start/routine/advance/vision/gate/vision/check/reading/read/memory/feedback/realtime/connect; POST memory/{id}/edit; DELETE memory/{id}; admin research routes unchanged.

Additive Session fields: experience_mode voice|visual|text|null, todays_look FullLook|null. ChatRequest optional experience_mode. Existing actions/consent validated as before.

Implemented runtime endpoints: POST full-look/plan {session_id}; GET full-look/{session_id}; POST full-look/revise {session_id,user_request,target_sections?,constraints?,expected_version?}; POST full-look/confirm {session_id,sections,decision:confirm|skip,expected_version?}; POST full-look/memory-candidate {session_id,feedback}. Mutations return existing Reply plus plan and revision metadata, all use the same SessionStore lock.

GET materials returns results; POST materials/explain {material_ids:[1..2]} returns results and human-readable message. Plan confirmation is session-only, NEVER implicit durable memory. Candidate route requires a separate original memory consent action to persist.

Validation: strict enums, lengths and bounded lists; expected_version stale =>409; missing session=>404; completed sessions cannot mutate; camera busy disallows plan mutations; original consent schemas unchanged. MemoryCandidate adds material_preferences list[str], domain_preferences dict[str,list[str]], never health/disability labels.

Example scoped revision:

```json
{"session_id":"session-id","user_request":"我想淡一点","target_sections":["makeup"],"expected_version":2}
```

The response includes `changed_sections`, `unchanged_sections`, `reasons`, `version`, `plan`, `session`, `step` and a human-readable `message`. A target-domain mismatch is rejected before any section is changed.
