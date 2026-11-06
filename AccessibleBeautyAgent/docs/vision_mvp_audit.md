# Vision MVP audit — 2026-10-12

Actual baseline executed on this branch: backend **158 PASS**, fresh `work/vision-mvp-baseline-20261012`; frontend **20 files / 134 PASS**. The older 130/127 counts are historical. Previous UI report records an old temporary SQLite corruption failure; this fresh baseline passed. Repository began clean at `63e7475`.

Working: real DeepSeek text client and SSE, persistent authoritative makeup plan/events, controller commands, browser recognition/TTS fallback, frame capture/timestamps, local camera permissions/cleanup, reviewed-confirmation journal storage and existing TRACE 2.0 identity.

Existing vision: official local MediaPipe IMAGE model plus OpenCV. Blank-frame native inference was previously verified, but no real-person accuracy benchmark exists. Current analyzer performs Haar gating before landmarks, measures small LAB patches, always returns UNCERTAIN and requires a separately consented RAM baseline for comparison. Image services outside this local path remain Mock. Default preview is not analysis.

Gaps: landmark-based quality gates; explicit interpretable cheek metrics; same-session recent observation history; target-specific conservative lip feedback; adaptive authorized keyframes; visible live-analysis states; automatic result application for panel/continuous checks; contextual camera panel inside `/voice`; evaluation schemas and scripts. Existing UI navigates to `/explore` for camera commands, preserving session but disrupting page continuity.

Credentials: no secrets inspected. Earlier authorization permits the application's normal loading of existing DeepSeek text configuration. No new visual credential needed for local inference; no third-party image upload authorized. Local model/runtime installation is audited separately. Expert-reviewed corrective curriculum is unavailable, so draft tips must not be relabeled reviewed.

Hardware-dependent: physical microphone, audible speaker, camera permission/preview, true landmark localization, actual complexion/light variation and before/after makeup. None counted PASS without execution. Native model absence, network errors and uncertain inputs must remain explicit failures/unavailable states. No training or labeled evaluation data supplied; no accuracy figures may be claimed.

Implementation priority: local frame → pretrained geometry → quality gates → conservative numerical observation/recheck → same-session conversational feedback → focused UI → evaluation infrastructure. Preserve existing business rules, routes, Story, particles and confirmed data.
