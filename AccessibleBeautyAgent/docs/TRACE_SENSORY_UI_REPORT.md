# TRACE 2.0 sensory UI — acceptance report

Date: 2026-10-12. Branch: `trace-v5-realtime`.

Phase 4 functional delivery preceded this visual work. This change adds an original procedural digital sculpture, warm wireframe, distinct point particles, apple-to-face morph, section-owned scenes, editorial Full Look annotations and bilingual key headings/navigation. Existing voice controller, text API, makeup workflow, memory, journal consent, camera controls, reading settings and routes remain available. The palette reference disclosure and its official source links are retained.

The sculpture is a generic illustrative face, not a scan or an accurate digital twin of the user. Makeup region previews change only visual pose/overlay; they do not advance the actual coaching step or make a visual judgment. No model training took place. No real person image or frame was transmitted. Configuration secrets were not read, printed or changed.

## Automated checks

| Check | Result | Evidence / limit |
|---|---|---|
| Complete backend regression | PASS | 158 tests, exit 0, fresh `--basetemp=work/ui-regression-fresh-20261012`. Backend source unchanged in this UI task. |
| Frontend regression | PASS | 20 files / 134 tests; deterministic geometry, particle budgets, pointer clamps, language display and preview without API mutation included. |
| TypeScript + Vite build | PASS with warning | 106 modules. Lazy 3D chunk exceeds Vite's 500 KB warning threshold. This warning is retained. |
| Knowledge validation | PASS | 3 LOOK, 3 ROUTINE, 2 REFERENCE_CASE, 12 PRODUCT, 73 ACCESSIBILITY_GUIDANCE, 3 SOURCE. |
| Whitespace / diff check | PASS | Checked before commit. |

Observed earlier failures are not omitted: the first backend run using the old temporary directory had 157 passes and one SQLite `database disk image is malformed` failure in the privacy frame test. A new isolated temporary directory passed all 158. The corruption cause is not established. An intermediate frontend run had 133 passes and one failure because renaming the journal removed its clear “Makeup calendar” caption; the functional bilingual calendar caption was restored and subsequent complete runs passed. Development HMR had temporary import/effect errors while new files were being assembled; final reloads rendered the scenes, and no later errors appeared in the captured console history.

## Browser checks

| Check | Result | Evidence / limit |
|---|---|---|
| Home, Voice, Makeup, Full Look | PASS | Real app routes rendered WebGL sculpture/points, usable text controls and existing entry points. No physical call was started for this visual check. |
| Section-owned backgrounds | PASS | DOM positions are `absolute` inside page/section containers. At home scroll 630 px, Hero background top moved from 115 to -515 px. At scroll 2856 px, the Hero canvas was unmounted and later scenes were present. |
| Pause motion | PASS | Keyboard/action controls retained; active visible canvas reports `data-motion=static` and preserves the sculpture. Offscreen scenes stop/unmount rather than using a viewport-fixed global canvas. |
| Language display | PASS | Default bilingual key headings/navigation. Chinese First removes heading translations; English First sets document language to English and the checked main content contained no Chinese. Recognition locale behavior retains regression coverage. |
| Narrow screen | PASS | 375 px viewport, no horizontal page overflow, compact header and text-first stacking. Viewport override reset afterward. |
| Region preview | PASS | Blush selects a slow 3/4 pose; lips select front. Buttons expose pressed state. Regression verifies preview invokes no coaching API. |
| Full Look truthfulness | PASS | Six domains display waiting text without a real plan. Existing planning, material dictionary, edit/confirm/skip controls remain. No fabricated profile or outfit result. |
| Reading settings | PASS | Mouse toggles separately apply large 24 px body text and high contrast; restore controls work. An overlapping narrow dropdown discovered during QA was corrected to 220 px with 70 px button spacing. |
| Keyboard / accessibility tree | PASS, limited | Headings, native controls, visible focus and text fallback inspected. This is not a real screen-reader certification. |
| Desktop performance | OBSERVED, limited | One browser window reported approximately 60 fps during a short measurement. Adaptive degradation is implemented; this is not a hardware-wide performance guarantee. |

Screenshots are supplied with the chat: `trace-ui-home.png`, `trace-ui-voice.png`, `trace-ui-makeup.png`, `trace-ui-full-look.png`, `trace-ui-mobile.png`. The home proof shows paused motion for a clear sculpture view. Decorative art is marked hidden from assistive technology; meaningful workflow information remains in text.

## NOT_TESTED and remaining risks

- Physical microphone recognition, audible TTS, camera, real screen reader and OS-level reduced-motion setting in this UI acceptance. Existing controller regression tests cover denial, switching and cleanup but are not physical hardware evidence.
- Real makeup recognition accuracy or calibration. Remote visual inference remains unavailable/Mock; generic art is not evidence of successful face analysis.
- Replacing `/models/human.glb` with a licensed production model. Default original geometry needs no asset. Arbitrary GLB anatomy, first-mesh point sampling and overlay registration require asset-specific QA.
- Low-end GPU / long-duration heat, battery, memory and universal 60 fps. Mobile uses at most about 4,830 scene particles initially; desktop about 22,280, with offscreen release, DPR caps and adaptive main-particle reduction.
- Lighthouse and production deployment. No score was fabricated. The lazy Three chunk is approximately 682.5 KB / 182.6 KB gzip; the main chunk approximately 441.4 KB / 151.3 KB gzip. Actual final Vite output remains authoritative.
- Phase 4's pending expert review of original tutorial drafts, real visual validation and production privacy limitations still apply. This UI task does not resolve them.

Repository/license selection and local model replacement instructions: [TRACE_SENSORY_UI.md](TRACE_SENSORY_UI.md). Exact observed GitHub metadata: [UI_REPOSITORIES.json](UI_REPOSITORIES.json). Previous functional status: [PHASE4_ENGINEERING_REPORT.md](PHASE4_ENGINEERING_REPORT.md).

Implementation commit: `0c9b2df7a07be3e8bd4a43e7b4f84c29dd767ba4`.
