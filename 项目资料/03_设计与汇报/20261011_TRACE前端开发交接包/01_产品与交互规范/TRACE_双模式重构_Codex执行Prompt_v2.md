# TRACE Dual-Mode UX Refactor — Copy-Ready Codex Prompt V2

> 将以下正文直接发送给 **已经打开 `D:\AccessibleBeautyAgent` 的 Codex**。不要创建全新项目或覆盖数据库。

---

You are working inside the EXISTING TRACE / Accessible Beauty Agent repository at `D:\AccessibleBeautyAgent`.

This is a **targeted front-end UX and interaction architecture refactor**. The user's latest decision is to introduce a simple entry experience with two selectable modes: **Voice Companion** and **Visual Experience**. Both must connect to the EXISTING DeepSeek-backed Agent, knowledge base, camera tools, state machine, and consent-controlled memory. Our audience includes blind and low-vision people, but the experience must never require users to verify or disclose disability status in order to proceed.

Read the two original design documents supplied by the user if available:
- `听见你的美_AI_Coding网页生成Prompt_v1(1).md`
- `听见你的美_高保真网页UI动效设计规范_v1(1).md`

Also read the new `TRACE_双模式入口与无障碍体验规范_v2.md` if available. Treat V2 as the decision authority for page flow while preserving the original documents' aesthetic intent. The old documents' recommendation to use Next.js is NOT a migration request: this repo currently uses **React 19, Vite 7, TypeScript and FastAPI**. Preserve that stack.

## MANDATORY PRE-FLIGHT

1. Inspect `frontend/package.json`, `frontend/src/App.tsx`, `frontend/src/state/routes.ts`, `frontend/src/pages/`, `frontend/src/realtime/voice.ts`, `frontend/src/accessibility/useSpeech.ts`, `frontend/src/vision/camera.ts`, and the backend Agent endpoint contracts.
2. Report the currently implemented pages and whether the real DeepSeek text/vision/ASR/TTS providers are connected or MOCK. Do not claim something works merely because a class or component exists.
3. Make a git commit or recoverable backup of the current working state; protect `.env`, any API keys, user images, and the `_incoming` folder from accidental commit.
4. Preserve all existing functionality and routes. Do not automatically import, verify or overwrite any DRAFT KB records.
5. Show the smallest change plan, then implement it and run tests. Do not stop after just writing a plan.

## PRODUCT DECISION 1 — ENTRY MODE, NOT DISABILITY VERIFICATION

Replace the root user-facing landing with a minimal accessible Entry Page:

Brand: `TRACE / 听见你的美`
Tagline: `Beauty, translated across senses.`
Headline: `美，可以从听见开始。`
Question: `今天，你希望我怎样陪你？`

Provide two equally available routes:

**Voice Companion / 语音陪伴**  
Subtext: `用声音告诉我你的想法，我会一步一步陪你完成。`

**Visual Experience / 视觉探索**  
Subtext: `探索妆容、造型与属于你的美学体验。`

Additional unobtrusive controls:
- `文字开始` — text-only alternative
- `使用说明`
- `切换语言`

No mandatory self-reported diagnosis; no storage of sensitive disability identity. If the user spontaneously indicates a visual-accessibility preference, apply the preference to interaction presentation only unless they separately and explicitly consent to save it. Provide a mode switch throughout the session, preserving state.

IMPORTANT: Page load alone must NOT turn on the microphone or camera, nor assume audible autoplay is permitted. Show a screen-reader-accessible entry immediately. Offer a clear `开启语音介绍` button that, after an actual user gesture, plays an optional spoken introduction. An explicit mic button may then start ASR after browser consent. Allow voice commands `语音陪伴`, `视觉探索`, `文字开始` when ASR is available. Always provide click/keyboard alternatives.

## PRODUCT DECISION 2 — VOICE COMPANION IS THE PRIMARY ACCESSIBLE TASK SURFACE

New `/voice` page (or minimal backwards-compatible equivalent):
- Minimal navigation; accessible, uncluttered one-screen voice-first layout.
- Large Talk button; textual and spoken states: IDLE / LISTENING / THINKING / SPEAKING / PAUSED / ERROR / CONSENT.
- Display the latest Agent message as large readable text.
- Buttons: `按下说话`, `重复`, `慢一点`, `下一步`, `为什么`, `帮我看看`, `停止`, and an accessible text-input fallback.
- Optional full conversation transcript; current look and routine step always understandable.
- Keep original Agent `send()`, `start()`, session ID, state machine, and TTS/ASR providers. DO NOT duplicate Agent state or build a second chat service.
- Manage audio concurrency: stop prior TTS when user begins speaking; cancel mic capture on page switch/stop; do not leave camera stream running.
- Support explicit mode switch to Visual Experience without losing the active session.
- Do not default to patronizing language or artificially slow speech; allow user-controlled speed and verbosity.
- Keep the latest instruction available via semantic live region without duplicate announcements when a screen reader and app TTS are both in use. User can disable app auto-read.

First dialogue example (for testing, not hard-coded as the only response):

User: `今晚有一个 dinner，我想正式一点，但不要显得太成熟。`
Agent: returns current intent/Look recommendation grounded in existing verified knowledge.
User: `一步一步教我。`
Agent: THREAD gives one actionable step at a time by default, can answer `为什么`, `重复`, `慢一点`, `下一步`.

## PRODUCT DECISION 3 — VISUAL EXPERIENCE RETAINS ORIGINAL ART DIRECTION

New `/explore` page, built by reusing/refactoring current Home, Story, Look, Pair, DOT and Memory pages. Preserve the original artistic feel:
- Ivory, warm white, Oat, Blush Mist, Espresso, muted rose-brown.
- Editorial asymmetry, substantial whitespace, luxury-beauty sensibility, soft perfume/air/voice-inspired particles.
- Tasteful typography using available font fallbacks; performance-conscious CSS transitions.
- Brand storytelling and optional scroll-trigger reveals, ONLY after accessible core works.
- User-visible navigation: Explore Looks, Talk to TRACE, DOT Read, PAIR Compare, THREAD Guide, ECHO Check, IMPRINT Memory.
- Demo scenario: Dinner / Soft Formal. Do not show DRAFT references/products as verified real recommendations.
- Visual mode must still be keyboard navigable, screen-reader compatible and usable at larger text sizes.
- Do not install GSAP, Three.js, Lenis, React Three Fiber or migrate to Next.js just because the old spec lists them. If a new dependency is needed, justify and check bundle cost; start with native React/CSS.
- No random fake Braille characters; decorative 2x3 dot geometry must be hidden from screen readers; any actual Braille text must be verified.

## PRODUCT DECISION 4 — CAMERA, FACE TRACKING AND AGENT ARE SHARED

ECHO uses the current consent-driven `CameraCheck` and camera capture utilities, not a second camera stack.

Flow:
`THREAD suggests check` → `User agrees to current use` → `getUserMedia` → `quality/head pose/face gate` → `capture three still frames upon request` → `vision provider` → `structured status` → `ECHO observation` → `TTS and on-screen result` → `repeat / retry / skip / next`.

A user must be able to refuse camera and still complete THREAD. No camera permission may be presumed from mode choice. Respect actual server/provider behavior and distinguish simulated outputs from real-image analysis.

Do not claim continuous motion capture, precise real-time blush symmetry, professional-grade color measurement, or guaranteed lip boundary estimation. For the current MVP, the demonstrated visual task is `blush_presence`: `NO_BLUSH | LEFT_ONLY | RIGHT_ONLY | BOTH | UNCERTAIN`. Treat LEFT/RIGHT as the USER'S sides even when the preview is mirrored. Insufficient evidence → `UNCERTAIN` + actionable retry or skip, not a fabricated corrective instruction.

If a real vision provider is not available/verified, present clearly labeled MOCK output; do not silently merge mock with production UI. Verify the remote provider's actual supported model name and image request format from provider docs/config rather than relying on past assumptions.

DOT reading remains a separate optional camera task for packages, labels and visible screens; it is NOT unrestricted system-wide screen scraping.

## PRODUCT DECISION 5 — SHARED STATE & NAVIGATION

Propose a small, typed state distinction:
- `experienceMode: 'voice' | 'visual' | null`
- `audioState: 'idle' | 'listening' | 'thinking' | 'speaking' | 'paused' | 'error'`
- existing `session`, `step`, `selectedLook`, and permission flags stay in their existing owners.

Use React state and existing route helpers, not new global state machinery unless technically necessary. Browser Back/Forward, bookmark paths, refresh and old `/session`, `/dot`, `/pair`, `/camera`, `/memory`, `/story`, `/demo`, `/admin/*` must remain functional. `main.tsx` admin split must remain intact.

Switching modes must not automatically:
- start a new session
- clear conversation history
- remove user preferences
- open camera or mic
- overwrite KB

When leaving voice/makeup check, release active streams and pause current TTS where appropriate.

## ACCESSIBILITY / PRIVACY ACCEPTANCE CONTRACT

1. Keyboard-only and screen reader can choose an experience mode with meaningful names.
2. The entry does not ask users to prove blindness or severity.
3. First-visit voice introduction starts only after user action, with a silent/text alternative.
4. Mic denial, ASR unavailability, TTS failure, camera denial, timeout and invalid vision JSON all have usable, clear fallback states.
5. Focus order makes sense; headings are semantic; controls have 44–48px+ practical hit targets; sufficient contrast and zoom behavior; important states have accessible text.
6. Respect `prefers-reduced-motion`; never put essential controls behind visual-only motion or hover.
7. Opt-in camera/memory permissions remain separate. Sensitive camera data must not leak into logs or client local storage.
8. On remote image analysis, privacy disclosure must accurately state that the picture is transmitted to the configured provider; do not claim fully on-device processing without evidence.
9. Development-only mock controls and raw confidence are not shown as ordinary UI.
10. Text/voice instructions follow the existing evidence-grounded policy; do not infer disability, emotion, appearance value or attractiveness from video.

## ENGINEERING ACCEPTANCE / TESTS

Add tests or manual reproducible checks that verify:

- Entry: Voice / Visual / Text all navigate correctly, mode select available with keyboard.
- Voice: session survives switching to Explore and back; progress is preserved.
- Voice: command handlers repeat, next, slow, why, stop behave correctly, especially during loading.
- Voice: mic denied -> typed input works. TTS disabled -> content remains visible and announced appropriately.
- Camera: no stream opens before explicit check authorization; decline keeps workflow usable; stop unmount releases camera.
- Vision: mocked results are always visibly disclosed; UNCERTAIN forbids confident corrective advice.
- Existing read, pair, memory, debug and admin routes are not broken.
- Regression: run current backend and frontend tests + frontend build; report actual counts/results, not assumed ones.
- Cross-device status: explicitly distinguish **NOT TESTED** from PASS for Windows, Android, iOS, macOS.

## STAGED EXECUTION — DO NOT POLISH BEFORE IT WORKS

Phase A / P0 (implement first):
1. Git backup/checkpoint.
2. Entry route and mode choices.
3. Voice Companion page bound to existing Agent, text and voice utilities.
4. Persistent mode switch with shared session.
5. Camera consent / stream cleanup / TTS integration.
6. Core access/error fallback tests and build.

Phase B / P1 (only if P0 passes):
7. Move/reuse existing home presentation in `/explore`.
8. Apply original high-fidelity editorial style only to Visual Experience, keep Voice fast and minimal.
9. Centralize bilingual copy and refine responsive design.
10. Add short 60–90 second Judge Demo journey, with explicit mocked-vs-real labels.

Phase C / P2 (later, not critical path):
11. Advanced particles/scroll effects, polished transitions, additional looks/products.
12. Additional face/hand tracking research features only after separate feasibility validation.

## REQUIRED FINAL REPORT

Return in Chinese:
- Which files changed and why.
- Old vs new route map.
- The exact Entry → Voice and Entry → Visual journeys.
- What shares the same backend/session.
- Which text/vision/audio capabilities are confirmed REAL and which remain MOCK / NOT TESTED.
- The real commands you executed, test results, and any failures.
- How to start the existing project in Windows without disrupting already-running servers.
- User steps to verify the two entry modes and a Dinner/Soft Formal demo.
- Any privacy/accessibility issue requiring user approval.
- What was deliberately deferred to protect the stable MVP.

Final priority: **a reliable voice-first experience for people who prefer non-visual interaction, a refined editorial interface for exploratory users, and a shared trusted Agent beneath both.**

