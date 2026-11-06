# API

Base: http://127.0.0.1:8000/api. Interactive and machine-readable schema at `/docs` and `/openapi.json`.

| Route | Request | Response |
|---|---|---|
| GET /health | — | component booleans, modes, developer_mode, remote_ready |
| POST /chat | message, optional session_id, user_id=demo, action=message/camera_consent/memory_consent, consent boolean | message, session, step, mode |
| GET /session/{session_id} | — | explicit session state, history and trace |
| POST /look/search | scene, desired_impression[], avoid[], preferences{} | results with look and score |
| POST /products/search | look_id, scene, preferences{} | scored sourced products with unavailable-field language |
| POST /products/compare | JSON array of product IDs | descriptions; unknown info explicitly unavailable |
| POST /routine/start | session_id, optional routine_id | message, session, step |
| POST /routine/advance | session_id | next step or FEEDBACK |
| POST /vision/gate | session_id, images[] | gate flags and per-frame details; requires consent |
| POST /vision/check | session_id, task, exactly 3 images (or explicit demo=true) | gate, gates, visual or null, message, session, step |
| POST /rag/search | query, filters{}, limit 1..50 | query, source-backed documents with scores/metadata, embedding_mode |
| GET /profile/{user_id} | — | derived profile and persisted episodes |
| POST /memory | user_id, candidate{}, explicit_consent real boolean | memory_id, timestamp, saved |
| DELETE /memory/{memory_id} | query user_id, explicit_consent=true | deleted; ownership checked |
| POST /feedback | user_id, session_id, feedback | candidate, persisted=false; requires FEEDBACK |
| POST /realtime/connect | session_id | provider capabilities; realtime=false fallback |

Camera flow: chat “check this” → CAMERA_CONSENT; post dedicated camera_consent action with consent=true → VISION_GATE. Only then can gate/check accept image data. Checks close consent automatically after one burst. Request and consent again for retries.

```json
{"session_id":"returned-id","message":"","action":"camera_consent","consent":true}
```

Mock visual request (only mock + developer mode):

```json
{"session_id":"returned-id","task":"blush_presence","images":[],"demo":true,"mock_status":"BOTH"}
```

Blush statuses: NO_BLUSH / LEFT_ONLY / RIGHT_ONLY / BOTH / UNCERTAIN. Lip: NOT_APPLIED / APPLIED / OBVIOUS_OVERFLOW / UNCERTAIN. Simulated results are tagged. Images accept JPEG/PNG base64 or data URL, max 3MB encoded per frame and 32–2048px dimensions. Frontend shrinks to ≤1024px. Empty/non-three bursts rejected except developer demo.

RAG:

```json
{"query":"dinner blush","filters":{"scene":"dinner","look_id":"soft_formal","makeup_area":"blush"},"limit":5}
```

Memory candidate fields: feedback (required), context, preferred_finish[], preferred_saturation (low/medium_low/medium/high or null), avoid[]. JSON `"true"` is rejected for write consent. Timestamp is UTC ISO8601; UI renders local time.

Status codes: 403 missing consent/disabled demo; 404 unknown session/routine/memory; 409 illegal state/input/service schema; 422 Pydantic/invalid image; 503 unavailable remote provider. Do not treat gate failure with visual=null as a makeup observation. These endpoints are for trusted loopback development; user IDs are not authentication.

## Phase 2 internal admin (/api/admin)

ADMIN_ENABLED=false rejects admin access; this local MVP has no account auth. Model requests require ALLOW_REMOTE_AI=true. Health includes allow_remote_ai/reference_provider/research_mode.

| Method/path | Body or response |
|---|---|
| GET /dashboard, /vocabulary, /schemas | canonical counts/records/indexed_versions; configured labels; Pydantic JSON schemas |
| GET /records/{kind} | records and stable id_field; six canonical kinds |
| POST /records/{kind} | record, expected_version, reviewed strict boolean, reviewer; saved version/history; reviewed requires reviewer |
| POST /records/{kind}/{id}/deprecate | expected_version; soft deprecation |
| POST /references/upload | filename, look_id, base64 image, optional demo_data; RAW record/source/image |
| POST /references/{id}/analyze | expected_version; unverified draft or protected suggested_revision |
| GET /reference-media/{id} | reference image restricted to local media directory |
| POST /import | filename .csv/.xlsx, base64 file, optional CSV type, commit=false; row errors/warnings/staged records |
| POST /validate | {}; PASS/WARNING/ERROR with row/field messages |
| POST /rebuild | optional type/look_id; atomic full refresh; scope counts and smoke |
| POST /smoke | {}; dinner retrieval smoke status/results |
| POST /rag/search | query, filters, limit; parsed_filters/policy and semantic/lexical/merged/reranked/final results |

Stale versions return 409; protected edits/disabled remote/admin return 403; missing records/media 404. Schema errors include field detail. Saving knowledge requires rebuild to activate it for ongoing agent sessions. Import only creates drafts, never overwrites IDs.

## TRACE additive endpoints (Phase 3)

POST `/api/reading/read`: `{image?: dataURL, demo: boolean, explicit_consent: boolean}`. Strict boolean consent required; missing/false is denied. Normal mode requires a validated image; one resized JPEG is passed to the provider without persistence. Mock real images return UNCERTAIN, demo labels return clearly fictional simulated data and require developer_mode. Remote reading also requires ALLOW_REMOTE_AI and a supported vision model. Result: status/summary/shade/instructions/full_text/confidence/simulated. Unknown fields null.

POST `/api/memory/{memory_id}/edit`: existing MemoryRequest `{user_id,candidate,explicit_consent}`. Strict consent, same candidate validation as save, update scoped to memory_id AND user_id; missing or other owner 404, refusal 403. Preserves record ID and rebuilds derived preferences through existing profile aggregation. Existing contracts remain available. The MVP still uses local user IDs rather than production authentication.
