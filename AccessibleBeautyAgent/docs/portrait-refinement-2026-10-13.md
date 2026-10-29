# TRACE - Portrait refinement and reference comparison / 2026-10-13

Status: implemented portrait refinement, visually checked on four routes. The strict reference reconstruction gate is PARTIAL, not a pixel-perfect pass.

## Scope and preservation
Latest user emphasis: facial proportions and a less ordinary sculpture. Retain the previously confirmed centered home copy, upper-left five apples, feature row and rear decorative particles. No API, camera consent, voice workflow, RAG, memory/calendar, hardware, authentication or routing changes. No private images or microphone data collected. No keys read or changed.

## Source changes
- frontend/src/visual/refinePortrait.ts: bounded sculptural deformation on the normalized, attributed default anatomical mesh. Narrow front jaw up to18%, reduce lateral nose width locally up to20%, soften brow/eye surfaces, refine chin/cheek/lip projection, narrow neck locally up to7.5%. Recompute surface normals and bounds. Original connectivity remains. Custom /models/ replacement assets bypass these model-specific deformations.
- frontend/src/visual/refinePortrait.test.ts: finite normals/positions, jaw and lip changes, preserved back-of-head vertices and connectivity.
- frontend/src/visual/SculptureScene.tsx: two wire subdivisions desktop, one on initial mobile; normal-directed surface offset avoids self-occlusion; depth-only prepass removes back-surface cheek silhouettes; matte pearl/rose material, restrained emission, softer key/rim lighting; hero yaw -0.95rad and pitch -0.30rad; weighted surface sampling, mostly subpixel grains and2% larger highlights.
- frontend/src/visual/sculptureField.ts and sculptureField.test.ts: adaptive high295000 / medium88000 / low16800 allocation, seeded fields. Actual low16799 because satellite subdivision uses integer thirds. High295000 verified in browser.

Source model remains Lee Perry-Smith CC BY3.0 with existing visible attribution. The in-memory sculpture is a derivative, not an original human scan or the current user's face. Original anatomical model is not replaced by a sphere/mask. The reference's source mesh is unavailable.

## Reference measurements and iterations
Authoritative reference1536x1024. Divider aty552: home/voice target768x552, makeup/full-look768x471. Real IAB captures753x541 /753x462, excluding scrollbar and with capture scaling. Comparisons retain native image sizes, do not invent matching scores.

Main pre-change differences: coarse computational grid; opaque/rigid surface; broad jaw and heavy brow; dark self-overlap at cheek; no selectively bright surface particles. Reference portrait is a different refined closed-eye anatomy.

1. TRACE_PORTRAIT_ITERATION_1.jpg - finer topology, lighter matte/transparency. Rejected excessive surface washout.
2. TRACE_PORTRAIT_ITERATION_2.jpg - weighted contour grains, smaller particle sizes, stronger base definition. A sampler API mismatch was caught and repaired using the installed setWeightAttribute API; corrected screenshot saved.
3. TRACE_PORTRAIT_ITERATION_3.jpg - profile camera calibration and normal-directed wire offsets. Still showed transparent overlap, so refinement continued.
4. Final - depth prepass, explicit surface/wire ordering, face-proportion deformation and calibrated pearl material. Independent eyelid patches were tried, but side-view seams remained; patches were removed. Final screenshots contain only the connected sculpted mesh, not floating eyelid components.

Final native screenshots: TRACE_PORTRAIT_HOME_FINAL.jpg, TRACE_PORTRAIT_VOICE_FINAL.jpg, TRACE_PORTRAIT_MAKEUP_FINAL.jpg, TRACE_PORTRAIT_FULL_LOOK_FINAL.jpg. Comparison images: TRACE_PORTRAIT_COMPARE_home.png, _voice.png, _makeup.png, _full-look.png. TRACE_PORTRAIT_HOME_OVERLAY.png is a50% diagnostic overlay at the common crop, not a similarity score. TRACE_PORTRAIT_DESKTOP_FINAL.jpg is a1366x900 viewport check.

## Actual high-budget layers
|Layer|Count|
|---|---:|
|Apple|100000|
|Slice|25000|
|Plume|65000|
|Human surface|45000|
|Ambient|20000|
|Burst|10000|
|Ribbon|10000|
|Orbit|5000|
|Highlights|5000|
|Satellite apples total|8001|
|Fragment|1999|
|Total|295000|

The allocation differs from the suggested groups to retain the existing five-form apple composition. Apple shape and placement retained; a new apple asset was not rebuilt in this portrait-focused refinement.

## Validation
PASS: frontend158 tests /31files, full backend187 tests, KB LOOK3/ROUTINE3/REFERENCE_CASE2/PRODUCT12/ACCESSIBILITY_GUIDANCE73/SOURCE3, final tsc/Vite build121modules, diff check.
PASS browser: four route renders; licensed derivative metadata loaded; high295000 points; pause/static time0; motion restored; mobile375 client/scroll360, no horizontal overflow; four home feature boxes retain y779.5 at1366x900. No new camera/mic permissions requested.
Performance: intermediate short contiguous sample59.4fps/16.8ms with295000 points. Final run reported insufficient-contiguous-samples; no valid final sustained60fps claim. Performance remains adaptive. Final lazy3D chunk657.35KB warning remains.
NOT_TESTED: final long-run/filming-device FPS, OS screenreader, native reduced-motion preference, real microphone playback energy, new real camera analysis/remote calls, physical hardware. These product paths were not changed; regression tests passed.

## Remaining fidelity gaps / not visually complete
- Different source anatomy remains visible: reference eyelid shape, jaw silhouette, lip and nose microtopology are not reproduced exactly. Full closed-eye topology NOT_IMPLEMENTED; add-on patch experiment rejected.
- Home centered copy/upper-left five apples and saturated trails reflect subsequent user-approved direction, so composition differs substantially from the old four-panel reference. No global layout reversal in this portrait pass.
- Empty conversation/profile/FullLook show truthful current user state, not copied reference example turns or invented recommendations/85% scores.
- Fine grid and material improve the computational surface, but neither exact2-6px line spacing nor full photometric correspondence has been measured at every face region.
- Browser capture quality/scaling limits forensic pixel matching. No SSIM or invented numerical fidelity score.

No visual accuracy, training or real Digital Twin identity claims. This is a visible geometric/material refinement; the entire strict reference reconstruction remains PARTIAL.
