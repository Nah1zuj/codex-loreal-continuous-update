# Architecture and trust boundaries

React/Vite TypeScript UI uses a same-origin `/api` proxy to the loopback FastAPI server. Browser push-to-talk and TTS are optional; text chat is the universal fallback. No paid API is needed for default startup.

## Session and agent

`agent/state.py` defines legal edges for INIT → ONBOARDING → INTENT → CLARIFY / LOOK_SELECTED → GUIDE, optional CHECK_REQUESTED → CAMERA_CONSENT → VISION_GATE → VISION_CHECK → VERIFY, then FEEDBACK → MEMORY_CONSENT → COMPLETE. `SessionStore.transition` rejects illegal edges. A stop event can reach COMPLETE from any state. Per-process lock serializes mutation. Sessions are transient, not production accounts.

`AgentHarness` exposes profile, Look, product, comparison, routine, visual, feedback, memory proposal/save/delete tools. Text providers parse intention only. The deterministic Harness uses retrieved tool data to compose concise Chinese replies. `last_tool_call` and the latest 30 trace entries stay in process; image bytes are excluded. RAG retrieved source documents are included in session/debug.

Dedicated camera_consent / memory_consent action with Pydantic StrictBool is required. Model or arbitrary conversational “yes” cannot give consent. Explicit API writes require a real JSON boolean. The UI presents candidates before saving. Feedback/proposal is transient until confirmed.

## Knowledge and retrieval

Canonical records in data/knowledge are schema validated. Parent-child IDs link overall Look, techniques, routines/steps, references and products. JSON records can be replaced without altering orchestration.

HybridRetriever combines BM25-like token scores (55%) and cosine vector scores (45%). MockEmbeddingProvider is a stable SHA256-hashed bag of words with 256 dimensions; it is a lexical proxy, not learned semantics. RemoteEmbeddingProvider calls the configured embeddings endpoint in batches. Metadata filters execute before ranking. Optional remote reranker requires transport injection; default is a stable score sort.

The local vector index is a small in-memory flat list, with an exportable JSON snapshot. Startup rebuilds from canonical records to avoid stale KB. This is appropriate for a small hackathon KB; larger collections should replace the flat vector storage behind the same retrieval response.

Product weights live in settings/env. Empty claims and absent/null fields produce “信息不可用”. Sample catalogs are explicitly marked fictional. Look suggestions use data-defined scene/impression/avoid and saved preference fit.

## Camera and vision

Camera is off by default. Once backend consent is recorded, a separate user action calls getUserMedia. Preview is mirrored via CSS, raw uploaded pixels are not mirrored; prompt uses anatomical left/right. Capture is a burst at roughly 0/250/500ms, JPEG quality .8, longest edge ≤1024; no continuous video upload. Tracks close after capture, stop, navigation and component cleanup. Capture cancellation prevents later frames being uploaded.

LocalFaceGate uses OpenCV Haar face detection and eye centers as a coarse local landmark equivalent. It checks exactly one face, face area, eye alignment proxy, face ROI brightness/clipping/contrast and blur. Pose/occlusion scores are heuristics, not calibrated probabilities. Eye glasses, frontal angle and skin/lighting differences can cause false rejects; no clinical or demographic accuracy claim is made.

Every real frame must pass the gate before any makeup provider is called. Only explicitly developer-enabled mock demo bypasses real image input with a visibly simulated gate. Three VisualResult schemas validate allowed blush/lip statuses; reliable majority must contain ≥2 votes, quality not poor and confidence ≥CONFIDENCE_MIN. Disagreement penalizes average winning confidence by .15 per nonwinning frame. No majority or adjusted low confidence yields UNCERTAIN. Average/adjusted confidence is not a scientific calibration metric.

Confidence ≥.80 uses high-confidence phrasing, .60–.79 explicitly says moderate, <.60 says cannot reliably judge and asks retry. Thresholds are in Settings. No automatic fine-grained corrections are generated. Mock output always carries simulated=true and accessible simulation wording.

## Memory

SQLite rows store a validated candidate and UTC timestamp only after explicit consent. Episodic records are the source of truth; profile lists union across current rows, latest nonnull saturation wins. Deleting a row for its user reconstructs profile and removes that row's contribution. SQL is parameterized. No images/recordings are written. Profile is personalized in retrieval.

## Remote interfaces and boundaries

QwenClient uses httpx, configured base URL/models/key, request timeout and JSON-schema validation. Provider HTTP failures return 503 and never synthesize remote observations. Visual errors revoke camera consent and require retry consent. Key stays server-side; error output omits upstream response bodies. Remote adapters have not been credential-verified.

Browser voice fallback is implemented. Qwen realtime provider returns PLACEHOLDER and fallback capability names; remote reranking is an extension interface. Fine symmetry, gradient scoring, millimeter lip boundaries, personalized geometry, emotion and beauty scoring are future/excluded.

Local development has no auth. Bind loopback only. A process lock and unbounded transient session dictionary are acceptable for the local MVP; production needs auth, quotas, TTL and per-session async locks.

## Phase 2 extension

Canonical schemas → validated KnowledgeRepository → readable document_builder → HybridRetriever. One repository owns all six canonical JSON types; existing services reuse it via KnowledgeStore. Admin saves use optimistic version checks and append previous versions to history; import stages cross-linked drafts. Reference upload commits Source+RAW together; analysis cannot replace human-reviewed truth. Persist index before atomically swapping active agent services. Reranker only reorders original permitted candidates. Admin routes and lazy React admin UI are isolated from the main interaction flow. RemoteModelClient gates DeepSeek/Qwen behind ALLOW_REMOTE_AI=false by default.
