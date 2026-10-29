# TRACE sensory visual system

2026-10-12. Branch `trace-v5-realtime`. This visual layer follows the completed Phase 4 coaching implementation. It changes presentation, not coaching, consent, persistence or API contracts.

## Design audit and preservation

The previous interface used an apple photograph, viewport-fixed particle fields, a million-particle allocation and several competing rose backgrounds. The retained identity is cream paper, warm red, serif typography, original apple symbols, calm pacing and accessibility controls. The new layer uses original procedural face geometry, ivory matte sculpture, fine warm wireframe and individually rendered particles. No portrait photographs or externally sourced human models are introduced.

All existing routes remain: `/`, `/voice`, `/speak`, `/explore`, `/video`, `/thread`, `/echo`, `/full-look`, `/imprint`, `/dot`, `/pair`, `/story`, `/demo` and admin. Navigation, voice controller, session recovery, streaming replies, camera consent, local checks, confirmed memory, journal calendar, product comparisons and material library remain attached to their existing handlers.

The latest brief explicitly replaces the earlier monolingual default with bilingual primary headings and navigation. Language display supports Chinese first, Bilingual and English first. Recognition and speech locale still use the existing locale mechanism; changing locale still pauses active recognition. Consent and guidance remain explicit functional prose.

## Implementation

- `SectionBackground`: section-owned, absolute-inset light/art containers, lazy scene loading through visibility observation. Offscreen scenes unmount and dispose GPU resources. No mounted art uses viewport-fixed positioning.
- `SculptureScene`: Three.js scene, original parametric head, neutral neck/bust, fine wireframe, GPU shader points, original irregular fruit, particle bridge, optional local model loader. No skin texture or user-face scan.
- `DigitalHuman`, `WireframeHuman`, `PointCloudHuman`, `AppleParticleSymbol`, `ParticleMorph`, `FaceRegionOverlay`: named scene builders exported by the scene module. These are Three.js object builders, not standalone JSX widgets.
- `VoiceOrb`, `BeautyProfile`, `MakeupDigitalTwin`, `FullLookAnnotations`, `ParticleBackground`, `AccessibilityControls`, `BilingualHeading`: React presentation components using existing session state.
- Hero: apple/face morph; following sections show wireframe, generic makeup regions and bust. Story sections own their scenes. Mouse rotation contributions clamp to X ±2°, Y ±5°. Base editorial poses are independent of that small pointer contribution.
- Voice states: idle particles drift loosely; listening gathers; thinking softly pulses the apple; speaking expands particles. Optional local RMS measurement still uses the existing consented meter and stops when hidden, reduced or unmounted. AI playback animation indicates state, not measured output volume.
- Region preview selects base, blush, eyes, lips or finish. Blush turns to three-quarter, lips to front. Preview does not call the API, advance the workflow or fabricate observations. Real step updates reset preview to the current step.
- Full Look labels reflect actual suggestions or display “awaiting your choice”; skipped sections remain skipped. Skincare is preserved alongside makeup, hair, outfit, accessories and fragrance.
- Headings use local Noto Serif SC subsets; English uses locally packaged Cormorant Garamond (OFL). Existing system sans body fonts remain available.

## Performance and accessibility

Desktop face target: 20,000 points, plus at most 2,280 ancillary points. Mobile: 3,500 face points plus at most 1,330 ancillary points. Counts stay below 30,000 and 5,000 respectively. Two consecutive three-second samples below 42fps halve the face draw range and reduce device pixel ratio. Default DPR caps: desktop 1.5, mobile 1. No post-processing pipeline.

Motion uses shader uniforms and Three.js objects without React state changes per frame. IntersectionObserver and visibility handling pause/unmount offscreen work. Reduced motion or the motion toggle draws a static sculpture and cancels the animation frame loop. Decorative visuals are aria-hidden and never receive input focus. Existing skip link, focus rings, reading controls, status announcements, transcript input and speech controls remain.

The renderer is in a lazy chunk. Network/import/WebGL failures fall back to an original static illustration, while product controls remain available. The illustration is not a personal digital twin or calibrated measurement.

## Open-source research

Used the connected GitHub plugin search tools for all seven requested queries. There is no separately installed “GitHub Skill” file in the supplied skill catalog. Public repository metadata was retrieved through the GitHub connector after unauthenticated REST requests encountered rate limiting. See `UI_REPOSITORIES.json` for exact observations on 2026-10-12.

| Repository | License | Stars | Last push UTC | Fit and difficulty |
|---|---|---:|---|---|
| [mrdoob/three.js](https://github.com/mrdoob/three.js) | MIT | 116285 | 2026-10-12 | Selected. Mature renderer, Points/BufferGeometry, GLTFLoader, MeshSurfaceSampler. Moderate custom scene work. |
| [pmndrs/react-three-fiber](https://github.com/pmndrs/react-three-fiber) | MIT | 32903 | 2026-10-12 | Strong React alternative; version 9 pairs with React 19. Additional renderer abstraction unnecessary for these isolated scene leaves. Moderate. |
| [pmndrs/drei](https://github.com/pmndrs/drei) | MIT | 9927 | 2026-10-05 | Maintained R3F helpers. Not installed because R3F is not used. Low to moderate with R3F. |
| [darkroomengineering/lenis](https://github.com/darkroomengineering/lenis) | MIT | 16452 | 2026-10-02 | Mature smooth scroll. Not installed; preserve native scrolling, focus movement and reading behavior. Low, with integration costs. |
| [14islands/r3f-scroll-rig](https://github.com/14islands/r3f-scroll-rig) | MIT | 980 | 2025-12-17 | DOM/3D scroll synchronization, but extra R3F/scroll architecture. Higher retrofit cost; not used. |
| [MisterPrada/morph-particles](https://github.com/MisterPrada/morph-particles) | No license found | 285 | 2025-05-16 | Relevant conceptual search result, but no permissive license found. No code/model copied. Higher integration and rights uncertainty. |

Queries: `react three fiber point cloud`; `threejs particle morph`; `three.js human wireframe`; `react three fiber shader particles`; `threejs gltf point cloud`; `GSAP ScrollTrigger Three.js`; `Lenis React Three Fiber`. Some narrow queries produced no repository results; the maintained parent projects above provide the underlying capabilities. Search demos are not dependencies.

Registry package unpacked sizes: Three 0.186.1 20,443,256 bytes; Fiber 9.8.1 2,378,458; drei 10.7.9 1,753,692; Lenis 1.3.26 457,528; Motion 14.1.0 757,064. These are package installation sizes, **not browser bundle sizes**. Unselected packages were not installed or benchmarked in this app. Actual selected browser chunks are measured by the Vite build in the acceptance report.

[GSAP](https://github.com/greensock/GSAP) was already present and remains in use for entry motion, subtle CTA interaction and section scroll progression. Its package uses its own standard license; it is not presented as MIT/Apache. No Lenis, R3F, drei, Motion or postprocessing dependency is added. React/Vite/TypeScript and native CSS remain the project stack.

## Replacing the original sculpture

Default geometry is original code in `frontend/src/visual/geometry.ts`. To use an owned or permissively licensed local head/bust model, place it at `frontend/public/models/human.glb` and add `<meta name="trace-human-model" content="/models/human.glb">` to `frontend/index.html`, or pass `modelUrl="/models/human.glb"` to the scene. The loader accepts the local `/models/` path, centers/scales the model and uses matte material. No external model is fetched by default. Replacement GLB rendering and point sampling still need asset-specific visual QA. The generic makeup overlays are not automatic landmark registration to an arbitrary replacement model.

## Limits carried forward

No real-person frames were uploaded, and no recordings were saved. No keys or `.env` content were inspected or changed. Phase 4 text coaching remains connected by the existing authorized launcher; local visual checks remain uncalibrated and remote vision remains Mock. The UI does not turn mock checks into real observations. Knowledge review and actual makeup accuracy are separate work, not model training achieved by this redesign.
