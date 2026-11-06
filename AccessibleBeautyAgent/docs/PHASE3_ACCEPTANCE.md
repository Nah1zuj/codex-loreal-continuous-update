# TRACE Phase 3 acceptance and A–N delivery report

Date: 2026-10-07. Project: D:\AccessibleBeautyAgent. Phase 2 core preserved; additions do not replace Agent/RAG/reference administration.

## A. Previous identity

Accessible Beauty Agent / 无界体验家.

## B. New identity and naming

TRACE (conceptual Chinese name 迹). Beauty, translated across senses. / 让美的信息，在感官之间流动。

| Concept | Functional label | Descriptor |
|---|---|---|
| DOT | 读给我听 | Read the Surface |
| ECHO | 帮我看看 | Hear What Changed |
| THREAD | 陪我完成 | Follow Your Way |
| PAIR | 陪我选 | Compare What Matters |
| IMPRINT | 记住我的习惯 | Remember What You Choose |

## C. Pages

Home, App navigation/conversation, THREAD guidance, ECHO camera check and IMPRINT memory revised. DOT reading, PAIR two-option comparison, /story and /demo added. Admin retains existing research functions with TRACE identity. Browser routes are /dot, /echo, /thread, /pair, /imprint, /story, /demo.

## D. Components and configuration

TraceDotGrid, TraceMark, ModuleHeader, ThreadProgress and MemoryFacts. Central bilingual content in content/traceBrand.ts; humane public errors in content/errors.ts; locale provider; design tokens and separate TRACE styles. Plain React/CSS; no animation library, large background media or WebGL. UI design can be revised independently of the backend.

## E. Language changes

Technical page names replaced with functional Chinese names and English concept descriptors. Public memory JSON replaced by labeled facts and edit fields. Developer errors map to short recovery language; diagnostic detail stays in the optional developer panel. Vision copy describes observable states and uncertainty, without beauty scores or claims of symmetry. Product enumerations become readable labels. Existing Agent and knowledge data remain primarily Chinese; English UI does not imply full KB translation.

## F–G. Dot geometry and real Braille

Decorative two-column, three-row grids appear in the mark, hero, five module signs, progress and subtle waiting/listening indicators. Numbering 1 4 / 2 5 / 3 6. **None is claimed as real Braille.** No verified Braille strings were provided or displayed. Null unverified registry is intentionally unused. BRAILLE_USAGE_GUIDE explains expert verification before future display; no converter implemented.

## H. Accessibility

Decorative grids aria-hidden; explicit button names and functional descriptors; interactive grids require six named controls. Ordered progress with aria-current=step and text count. Live status and conversation announcement, skip link, page-change focus, visible focus outline, contrast-oriented warm palette, 18px body, large controls. Reduced-motion CSS disables animation/transition. Text remains available when speech is absent. Consent can be declined; errors/uncertainty do not force camera or memory use.

IAB tested at 390×844: no homepage horizontal overflow (innerWidth 390, scrollWidth 375); nav wraps and Chinese labels remain readable. Keyboard Tab from TRACE reaches Home with solid visible outline. Semantic SSR tests cover labels, grids, progress and memory preview. This is not a claim of complete WCAG compliance or assistive-technology certification. Reduced-motion rule is implemented/inspected; OS setting and real screen-reader testing remain to be done on target devices.

## I. Story

Separate /story: visual information → change the channel → TRACE → five tools → user agency → closing. “Beauty should not begin with sight. It should begin with you.” Story explicitly states research awaits verification and dot geometry is not tactile Braille. No literary passage or invented citation.

## J. Demo

/demo or /?demo=true starts a real Dinner Agent session and existing Soft Formal look. Development controls are hidden; ?demo=true survives subsequent module URLs. Refresh keeps mode/module but does not restore a transient Agent session; restart Dinner. PAIR uses existing comparison endpoint. ECHO simulation and DOT fixture are explicitly optional and labeled. No scripted fake chat transcript.

## K. Mock content

All providers remain mock and ALLOW_REMOTE_AI=false. Existing sample products/knowledge and synthetic reference are fictional/demo data. DOT fictional TRACE label demonstrates reading only; real images in mock mode return UNCERTAIN with unknown fields. Image confidence is not a validated measurement of accuracy. No Qwen or DeepSeek application request was sent. A generated visual concept is a design reference, not evidence about product or users.

## L. Research remaining

Every research/literary/Braille reference is **NEEDS SOURCE VERIFICATION** in CONCEPT_REFERENCES.md. Supply exact papers/pages and product sources, assess applicable claims, review canonical records before production RAG, then refine prompts and evaluate representative tasks. Real Braille needs language-specific expert review. Real media/provider output, nonvisual user testing and target hardware remain unverified.

## M. Verification, fixes and limitations

Backend: **65 tests passed** (including original regressions plus strict reading consent, disabled remote calls, production fixture refusal and memory edit consent/owner/profile update). Frontend: **17 tests passed**, TypeScript/Vite production build passed. Regression expectations updated only for explicitly revised uncertainty wording; protective behavior retained. Git whitespace check completed.

Browser: Home, DOT refusal → disabled capture, single-use fictional label result → camera off; actual Dinner selection → real product comparison → guidance; ECHO refusal → continue, allowed simulation → labeled result/camera off; steps skip → feedback → human memory candidate → decline → no saved preference; Chinese/English UI and /story. Memory edit ownership/save validation tested through HTTP API in isolated temporary test storage. Physical camera/microphone/online speech were not exercised. No production model accuracy or complete screen-reader compliance claimed.

Final independent review found two issues and confirmed fixes: demo entered from Home now sets/preserves mode; stale DOT camera failures cannot close a new stream or report into a new page. A development HMR createRoot warning was observed during source replacement; fresh document load was checked separately. No known failing test/build or unresolved review blocker remains. Production auth and durable session restoration remain future work, as before Phase 3.

## Design fidelity ledger

Both docs/design/trace-home-concept.png and trace-home-render.png inspected with view_image at the end.

| Reference feature | Rendered implementation / intentional adjustment |
|---|---|
| Warm off-white field, dark serif hero, brown CTA | Flat #F7F3EC/#292722/#805535 tokens; no raster texture shipped |
| Header TRACE with six small circles and horizontal nav | Same structure plus language toggle; mobile nav wraps |
| Two-line English hero and Chinese supporting statement | Same copy/order; smaller live type fits navigation and scalable viewports |
| Large right two-by-three alternating circles | Code-native filled/outline geometry with matching brown |
| Five ruled rows with concept, Chinese function, explanation and arrow | Same order and anatomy; labels are real accessible buttons |
| Fine vertical divisions and closing serif line | Preserved; usable product footer added below |
| IMPRINT/THREAD/ECHO patterns | Stable configured symbolic patterns; any generated pattern discrepancy is deliberate, no Braille translation claim |

Copy differences: only clarified product labels, honest mock disclosure, language toggle/footer and reachable live actions. Geometry comes from CSS, not a screenshot. Screenshot is a desktop acceptance artifact; mobile uses condensed geometry to preserve action space.

## N. Launch

```powershell
cd D:\AccessibleBeautyAgent
powershell -ExecutionPolicy Bypass -File .\start-dev.ps1
```

Open http://127.0.0.1:5173/demo. Backend API docs: http://127.0.0.1:8000/docs. Keep mock defaults for the current demonstration; see TRACE_DEMO_GUIDE.md for the sequence and limitations. No dependency reinstall is needed while servers are running.
