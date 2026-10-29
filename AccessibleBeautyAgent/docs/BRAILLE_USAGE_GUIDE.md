# TRACE Braille usage guide

The six-position grid is decorative visual geometry inspired by the two-column, three-row cell. Position numbering is 1 4 / 2 5 / 3 6. Neither TRACE's mark nor the five module patterns spell their names in Braille. Screens cannot supply tactile access; dots do not replace text, audio, semantic HTML or user testing.

There is currently **no real Braille text displayed**. `verifiedBrailleStrings` contains null, unverified placeholders; it is not rendered. Do not create a Unicode converter or describe decorative patterns as translations.

Before real Braille is introduced: obtain a qualified language-specific transcription, record the exact source/standard and language, obtain expert or Braille-reader review, record reviewer and date, then set verified=true with the reviewed string and source. English contracted/uncontracted and Chinese Braille require separate review. Status: **NEEDS SOURCE VERIFICATION**.

Decorative grids have aria-hidden=true. Interactive grids require an explicit group name and six named controls. State is expressed in text and semantic progress, never dots/color alone. Reduced-motion disables dot animation. Module labels always include a clear functional description.
