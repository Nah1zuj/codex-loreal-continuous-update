# TRACE V4 accessibility audit

2026-10-11. Incremental React frontend; existing warm bilingual TRACE system retained. No external assets or dependencies added.

## Implemented and tested with local frontend tests/build

- Home asks the preferred interaction, with three equally styled Voice, Visual and Text buttons. No medical/identity classification. `/voice`, `/explore`, `/full-look` added; all legacy routes retained. Browser navigation uses the existing history/popstate implementation.
- One App owns session, step and messages. Switching shells keeps them and sends a mode-only empty chat to the same session. Navigation does not start a new agent or invoke microphone/TTS.
- Only `trace.session_id` is stored in sessionStorage. Session, current step, last response and latest plan are fetched from the existing session API on refresh. No camera images, message text, credentials or consent flags stored in browser storage. Restore failure is announced and does not silently create a replacement session.
- Voice shell presents a large latest reply, live status, repeat/slower/detail/overview/next/why/stop/check actions and real text input. Speech uses the existing browser providers and explicit controls. Auto-read is initially unchecked. Stop remains available during a request. Existing camera consent boundaries remain intact.
- Full Look uses independent section actions and expected-version requests. Cards expose names, reasons, state and sources. Editing is text-based; confirmed/skipped state comes from the authoritative response. Material cards are readable in DOM order with individual TTS, two-choice comparison, sources and limitations.
- DOT adds product/garment label selection before consent. Camera still requires one-time permission and closes after capture. Composition is distinct from appearance, uncertain characters are displayed, and fictional demo labels are identified.
- Material/domain memory preferences render human-readable values. Memory candidate review still requires explicit save or refusal through IMPRINT.
- Technical tools are hidden from ordinary navigation; explicit developer URL flag and server developer_mode are required. Direct admin URLs remain operational.
- Existing focus handling, skip link and bilingual text retained. Added named controls, labeled inputs, warm contrast, responsive one-column grids, visible focus and reduced-motion rules.

## Actual verification

`npm.cmd test`: 6 files, 24 tests PASS（含 V4 入口、路由、材料/记忆展示和浏览器 TTS 生命周期）。
`npm.cmd run build`: TypeScript and Vite PASS; 67 transformed modules.

Tests cover entry alternatives, route compatibility, starting Full Look without a session, material composition warning, and human-readable memory candidates. These are structural contracts, not proof of assistive technology or real device behavior.

## Not tested by this frontend agent

本轮已用 Codex In-app Browser 在 Windows 本机验证入口、Voice → Visual 模式切换、六域计划、确认后局部修改和材料列表。真实麦克风、可听 TTS、摄像头权限、屏幕阅读器、Android/iOS、200% 缩放仍为 NOT_TESTED。未授权真人图没有发送到远端；不声明视觉或 OCR 准确率。

## Realtime accessibility/source audit — 2026-10-11

Current frontend verification is 12 test files / 104 tests PASS and TypeScript/Vite build PASS (77 modules). The previous 6-file/24-test totals are historical. Runtime dev dependency jsdom was added in Task 5; the older dependency statement applies only to V4.

The active language replaces authored product copy rather than presenting stacked bilingual labels. Catalogued local guidance and reviewed source text are localized; unknown external text retains the original with an explicit unavailable-translation notice. User-authored text remains original. Switching language pauses recognition and synthesis; it does not imply translation accuracy for arbitrary provider text.

Source audit: only existing `trace.session_id` uses browser storage. No new storage key, audio recorder, interim transcript persistence or camera-frame persistence exists in the realtime path. Frame capture and small comparison signature remain in RAM and are cleared on stop; backend visual traces record frame count/task/result, not pixels. This statement excludes the established developer reference-library upload feature. Recognition accepts final results only. Entry asks interaction preference without identity screening. Cosmetic appearance checks do not infer product composition.

Video local preview, microphone entry and remote frame permission are distinct gestures. Remote frames default off; no local visual model is claimed. Call pause/end, route exit, hidden page and camera close dispose tracks/scheduler and revoke active server consent. Mode changes preserve the shared call state after the browser-found restart fix; Text remains available. Browser native media error text can follow OS/browser language and is outside app copy.

Skip link, named navigation, labeled text input, visible focus and bounded aria-hidden particles remain in source. Reduced-motion CSS disables particle animation, transition and active-button transforms. Desktop video/guidance columns stack on narrow screens. DOM/source tests do not establish screen-reader quality, measured contrast, physical-device accessibility or 200% zoom; those remain NOT_TESTED pending direct evidence.

Final review correction: particles consume actual CallState and animate only while Listening/Thinking/Speaking; idle/off-route/paused/ended/error/permission states stay static. Six positions remain deterministic, aria-hidden and pointer-inert. Particle state/reduced-motion structural regression PASS; direct browser OS reduced-motion emulation remains NOT_TESTED.

Final coordinator keyboard/browser PASS: normal Tab focused Enable camera with visible solid outline; Home Enter navigated and focused the page announcer. Actual Speaking/Idle state attributes observed. Synthetic active speech survived mode change and completed into Listening; route Home disposed all synthetic tracks. Whole-branch review APPROVED. OS reduced motion, screen reader and physical hardware remain NOT_TESTED.
