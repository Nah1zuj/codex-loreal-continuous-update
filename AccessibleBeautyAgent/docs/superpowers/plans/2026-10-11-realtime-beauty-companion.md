# TRACE Realtime Beauty Companion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a one-click continuous voice call and consent-gated video call experience with a soft-luxury postmodern interface, while keeping one Agent session and honest vision boundaries.

**Architecture:** A client-side call controller owns the ASR → Agent → TTS loop; a separate camera controller and throttled frame scheduler own media lifetime and analysis. Voice and Visual are presentation shells over the existing session, Full Look, consent state machine and `/api/vision/check` contract.

**Tech Stack:** React 19, TypeScript 5.9, Vite 7, Vitest 5, browser Web Speech APIs, browser MediaDevices/Canvas APIs, FastAPI/Pydantic, existing mock/DeepSeek provider adapters.

**Spec:** `docs/superpowers/specs/2026-10-11-realtime-beauty-companion-design.md`

## Global Constraints

- A single entry click starts microphone permission and listening; no second start button.
- Camera consent is separate from microphone consent; remote sampled-frame consent is separate from local camera preview.
- Sample at most once per configured 2–3 second interval and allow at most one vision request in flight.
- Never upload a video stream or persist audio, video frames or interim recognition results.
- Voice and Visual keep the same `session_id`, Today's Look, routine step and pending Memory candidate.
- A photo/video appearance cannot establish clothing composition, disability, health, true emotion or scent.
- All media stops on end call, page hide, route exit and component unmount.
- Text input remains available whenever ASR, TTS, camera, network or model access fails.
- Chinese and English render as separate complete locales; never show both languages simultaneously in normal product UI.
- Companion language may be contemplative and literary, but actionable guidance and safety boundaries always come first.
- Motion stays restrained and is removed under `prefers-reduced-motion`.
- Preserve all existing routes, admin flows and API contracts.

## Review Focus

- TTS output captured by ASR must not create an AI self-conversation; Task 2 tests the speaking/listening gate.
- A late ASR, chat or vision response after ending or switching sessions must be ignored; Tasks 2 and 4 test generation IDs.
- Permission denial must not cause repeated prompts or a blocked text experience; Tasks 3 and 5 test denied states.
- Background tabs and route changes must release every media track and timer; Tasks 3 and 5 test cleanup.
- Rapid frame changes or slow vision responses must not queue uploads; Task 4 tests throttle and single-flight behavior.

---

### Task 1: Speech provider events and interruption safety

**Files:**
- Modify: `frontend/src/realtime/voice.ts`
- Modify: `frontend/src/realtime/voice.test.ts`

**Interfaces:**
- Consumes: browser `SpeechRecognition`, `webkitSpeechRecognition`, `speechSynthesis`.
- Produces: `ContinuousRecognitionProvider.startCycle(handlers): void`, `stop(): void`, `abort(): void`, `available: boolean`; TTS completion callback in `BrowserTTSProvider.speak(text, slow, onEnd)`.

- [ ] **Step 1: Write failing provider tests** for a final transcript emitted once, abort ignoring late events, recognition error mapping, TTS completion, cancellation generation and absence of browser speech APIs.
- [ ] **Step 2: Run `npm test -- frontend/src/realtime/voice.test.ts`** and verify the new cases fail for missing continuous interfaces.
- [ ] **Step 3: Implement the minimal event-safe providers** using generation counters and explicit handler cleanup; do not implement application state here.
- [ ] **Step 4: Run the focused test** and expect all voice provider tests to pass.
- [ ] **Step 5: Commit** `frontend/src/realtime/voice.ts` and its test with message `Add event-safe continuous speech providers`.

### Task 2: Realtime call state machine

**Files:**
- Create: `frontend/src/realtime/callController.ts`
- Create: `frontend/src/realtime/callController.test.ts`
- Modify: `frontend/src/accessibility/useSpeech.ts`

**Interfaces:**
- Consumes: Task 1 providers and an injected `sendTranscript(text): Promise<string>` callback.
- Produces: `CallState = idle|requesting_permission|listening|thinking|speaking|paused|ended|error`; `RealtimeCallController.start()`, `pause()`, `resume()`, `interrupt()`, `end()` and `subscribe(listener)`.

- [ ] **Step 1: Write failing state-machine tests** for one-click start, transcript → thinking → speaking → listening, no listening during TTS, manual interruption, pause/resume, network error to text fallback, end ignoring late responses and no restart after `ended`.
- [ ] **Step 2: Run the focused Vitest file** and confirm failure because the controller is absent.
- [ ] **Step 3: Implement the controller** with injected providers, one active generation and no React dependency.
- [ ] **Step 4: Update `useSpeech`** to expose event-safe TTS state without creating duplicate providers during rerenders.
- [ ] **Step 5: Run both realtime test files** and expect PASS.
- [ ] **Step 6: Commit** with message `Add continuous voice call state machine`.

### Task 3: Camera stream lifetime and explicit consent

**Files:**
- Create: `frontend/src/realtime/cameraStream.ts`
- Create: `frontend/src/realtime/cameraStream.test.ts`
- Modify: `frontend/src/types/index.ts`

**Interfaces:**
- Consumes: `navigator.mediaDevices.getUserMedia` and a supplied `<video>` element.
- Produces: `CameraStreamController.requestPreview(video, facingMode): Promise<CameraState>`, `switchFacingMode()`, `stop()`; states `off|requesting|live|denied|unavailable|error`.

- [ ] **Step 1: Write failing tests** for exact video constraints, permission denial, unsupported browser, switching cameras, stopping all tracks, route/unmount cleanup and no automatic retry after denial.
- [ ] **Step 2: Run the focused test** and verify missing-module failure.
- [ ] **Step 3: Implement the controller** without persistence, frame upload or server calls.
- [ ] **Step 4: Run the focused test** and expect PASS.
- [ ] **Step 5: Commit** with message `Add consent-gated camera preview controller`.

### Task 4: Throttled frame analysis scheduler and API contract

**Files:**
- Create: `frontend/src/realtime/frameAnalysis.ts`
- Create: `frontend/src/realtime/frameAnalysis.test.ts`
- Modify: `frontend/src/api/client.ts`
- Modify: `backend/app/schemas/models.py`
- Modify: `backend/app/routes/api.py`
- Create: `tests/test_v4_video_analysis.py`

**Interfaces:**
- Consumes: live `<video>`, local canvas capture, existing `/api/vision/check`, session ID, task and explicit remote-frame consent.
- Produces: `FrameAnalysisScheduler.start(options)`, `analyzeNow(reason)`, `stop()`; server accepts a single sampled image and returns the existing bounded `VisionReply` with `capture_kind=video_sample` metadata.

- [ ] **Step 1: Write failing frontend tests** for 2500 ms minimum interval, single-flight behavior, manual immediate analysis, unchanged-frame skip, stop ignoring late results and remote consent false blocking API transmission.
- [ ] **Step 2: Write failing backend tests** proving camera consent is required, one sampled frame is accepted, no video blob/list is accepted, uncertainty survives unchanged and composition inference remains impossible.
- [ ] **Step 3: Run focused frontend/backend tests** and confirm failures at missing scheduler/schema behavior.
- [ ] **Step 4: Implement scheduler and additive request metadata** while reusing the current vision gate/provider and size limits.
- [ ] **Step 5: Run focused tests** and expect PASS.
- [ ] **Step 6: Commit** with message `Add throttled consented video frame analysis`.

### Task 5: Voice and video call React shells

**Files:**
- Create: `frontend/src/pages/VoiceCall.tsx`
- Create: `frontend/src/pages/VideoCall.tsx`
- Create: `frontend/src/components/CallControls.tsx`
- Create: `frontend/src/components/CallStatus.tsx`
- Create: `frontend/src/components/CallExperience.test.tsx`
- Modify: `frontend/src/App.tsx`
- Modify: `frontend/src/pages/Entry.tsx`
- Modify: `frontend/src/state/routes.ts`

**Interfaces:**
- Consumes: Tasks 2–4 controllers and existing `send`, `session`, `step`, `FullLook` data and navigation.
- Produces: one-click Voice entry; Video view with live mirror and editorial recommendation rail; mode switching without session replacement.

- [ ] **Step 1: Write failing React contract tests** for entry click invoking call start, only one microphone action, visible call states, pause/resume/end/text controls, separate camera and remote-analysis consent, denied permission fallback and stable session identity across shells.
- [ ] **Step 2: Run the component tests** and verify expected failures.
- [ ] **Step 3: Implement `VoiceCall` and shared controls**; remove the second voice-consent click and start recognition only from the entry user gesture.
- [ ] **Step 4: Implement `VideoCall` and recommendation rail**; camera preview starts only from its explicit control and remote analysis remains off until separately accepted.
- [ ] **Step 5: Integrate controllers into `App`** with refs, generation guards, page-visibility cleanup and the existing text form as fallback.
- [ ] **Step 6: Run component tests and full frontend tests** and expect PASS.
- [ ] **Step 7: Commit** with message `Build accessible voice and video call experiences`.

### Task 6: Soft-luxury postmodern visual system

**Files:**
- Create: `frontend/src/components/AmbientParticles.tsx`
- Create: `frontend/src/components/AmbientParticles.test.tsx`
- Modify: `frontend/src/content/Locale.tsx`
- Modify: `frontend/src/content/errors.ts`
- Modify: `frontend/src/style.css`
- Modify: `frontend/src/pages/VoiceCall.tsx`
- Modify: `frontend/src/pages/VideoCall.tsx`
- Modify: `prompts/policies/v4/accessibility_policy.md`
- Modify: `prompts/policies/v4/brand_copy_policy.md`
- Create: `tests/test_realtime_companion_language.py`

**Interfaces:**
- Consumes: call state from Task 2.
- Produces: semantic `data-call-state` styling; deterministic low-density particles; reduced-motion static rendering; clean `zh-CN` and `en` locales; versioned contemplative companion-language rules.

- [ ] **Step 1: Write failing structural tests** asserting decorative particles are hidden from accessibility APIs, use a bounded deterministic count, expose no interaction, and render a static reduced-motion mode.
- [ ] **Step 2: Run focused tests** and confirm the component is absent.
- [ ] **Step 3: Implement the ambient component** with CSS variables and no animation library or random render-time layout.
- [ ] **Step 4: Implement the visual system**: warm ivory/apricot/smoke-rose/cocoa/copper tokens, editorial typography, fog glows, mirror video surface, breathing state transitions, focus visibility, 44 px controls and narrow-screen stacking.
- [ ] **Step 5: Add `prefers-reduced-motion` rules** that remove particle travel, parallax and continuous transforms.
- [ ] **Step 6: Replace simultaneous bilingual rendering** with one complete active locale across navigation, calls, errors, consent text and Full Look; add tests that Chinese contains no English UI duplicate and English contains no Chinese UI duplicate.
- [ ] **Step 7: Add and test companion-language policy**: clear action first, at most one short reflective sentence, no author imitation, diagnosis, pity, invented inner state or decorative language in safety instructions.
- [ ] **Step 8: Run tests and production build** and expect PASS.
- [ ] **Step 9: Commit** with message `Create localized soft-luxury companion interface`.

### Task 7: End-to-end verification, privacy audit and handoff

**Files:**
- Modify: `docs/TRACE_V4_ACCESSIBILITY_AUDIT.md`
- Modify: `docs/TRACE_V4_TEST_REPORT.md`
- Modify: `docs/TRACE_V4_RUNBOOK.md`
- Create: `docs/TRACE_REALTIME_CALL_HANDOFF.md`

**Interfaces:**
- Consumes: complete Tasks 1–6.
- Produces: reproducible test evidence, screenshots and explicit hardware/provider status.

- [ ] **Step 1: Run full backend tests** with process-scoped mock providers and `ALLOW_REMOTE_AI=false`; record exact count and exit code.
- [ ] **Step 2: Run `npm test` and `npm run build`**; record exact counts and output.
- [ ] **Step 3: Use the in-app Browser** to validate page identity, no overlay, console health, one-click Voice transition, permission boundary without accepting unapproved hardware access, text fallback, Video consent controls, shared-session mode switch, desktop and narrow layout.
- [ ] **Step 4: Verify cleanup** using mocked tracks and browser navigation; confirm no stored frames/audio/interim text and no new storage keys.
- [ ] **Step 5: Audit copy and rendered UI** for identity screening, composition inference, remote-frame disclosure, DRAFT content labels, keyboard names and reduced motion.
- [ ] **Step 6: Update documents and save proof screenshots**; mark real microphone, audible TTS, camera and remote vision as TESTED only if actually exercised with permission.
- [ ] **Step 7: Run final `git diff --check`, tests, build and knowledge validation**; preserve unrelated user changes.
- [ ] **Step 8: Request one final whole-branch review, fix material issues, rerun affected checks and commit** with message `Verify realtime Beauty Companion experience`.
