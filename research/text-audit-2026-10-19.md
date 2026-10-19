# Text audit (Oct 19, 2026)

A measure-only audit of every piece of on-screen text, against the standard OP Hiker's chat learned the hard way (its audit found about 80% of its labels subtly blurred). Morg ticked every fix in the hub ("Sharp text: the fixes"). Stage 1 is on `daily`. Stages 2 and 3 are below.

## The standard (from OP Scout's spec for OP Hiker, decision 125)
- Pixel fonts look right only at a whole number of device pixels per font pixel. A size between device pixels gets resampled, so strokes drop or double.
- Never shrink the lettering. The remedies, in order: write it shorter, use a shorter form, or a box built to wrap.
- Every line fits its box on every supported phone, and an overrun is a bug.
- Two-line text breaks into balanced lines, never one long line and an orphan.
- No visible font swap when the fonts load. Every character is in its font.

## Findings
1. **Pixelify Sans (about 90% of the text) can’t be crisp at any size as Google serves it.** Its grid is 11 pixels to the em, but its outlines overhang the grid by about 0.1 px, its advances are whole pixels plus 0.44, and its kerning, ascent (0.92 em) and descent (0.28 em) are off the grid. The game’s weights 500, 600 and 700 come from a variable font that sits further off still. Gray pixels: 17% or more at 3×, 27–53% at 2×. A static weight-400 copy snapped to the grid, kerning off, measured 3.7% at 3× and 0% at 2× at 11 px. Crisp sizes are multiples of 11/dpr: 11, 14.67, 18.33, 22 at 3×, and 11, 16.5, 22, 27.5 at 2×.
2. **Fake bold on every Press Start 2P label without its own weight** (the body is 600, the font has only 400): Next, PICK A CARD, the countdown, the GOLAZO! shout, the beta message and the lock’s title. Fixed in stage 1.
3. **Press Start 2P sizes off its grid.** It is 8 pixels to the em, so crisp sizes are multiples of 8/dpr (4 px at 2×, 8/3 at 3×). The 0.8em digit rule made 12.8, 13.6 and 14.4 px and so on. In the score “11/15” the slash stood taller than the digits. Fixed in stage 1.
4. **Hooks shrink instead of fitting.** At 320×568@2, 145 deals (91 distinct hooks) shrank, down to 10.5 px, and 24 ran under the yellow or red corner card. At 402×874@3, 48 deals (33 hooks), down to 14 px, none under the card. Every shrink comes from one word too wide for the tile, never from needing three lines. Corner-card overlap fixed in stage 1 with 14 px side padding on yellow and red tiles (which shrinks a few hooks further for now, down to 9 px at 320).
5. **No balanced wrapping** on two-line hooks, means lines (517 of 868 two-line means at 320 had a last line under 35% of the first) or the slogan. Fixed in stage 1 with `text-wrap: balance`.
6. **Tight labels:** “Start over from #1” wrapped at 375 (now “Start over”). The slogan wrapped at 320–340 on tall screens (now balanced). One sentence clips by 5 px at 320–328 on short screens after answering: ligamx:45, the Lapuente card (“in 1994–95 and 1995–96”), still to shorten.
7. **Font loading:** the Google Fonts stylesheet blocks first paint, and a slow font file shows SF fallbacks, then swaps. The end screen’s score and grid jump 37–43 px when fonts arrive. Yellowtail is requested but unused.
8. **No glyph gaps:** every character on cards and labels is in the served subsets.
9. **The sign’s dot pitch** wasn’t a whole number of device pixels. Fixed in stage 1.

The caveat: measured in headless Chromium on Linux, not Safari on an iPhone. The grid arithmetic and the fake bold apply in any browser, but the exact gray percentages will differ.

## The plan
1. **Stage 1 (done, on `daily`):** crisp Press Start 2P sizes (`round(nearest, X, var(--ps))`), `font-synthesis: none`, balanced lines, corner-card clearance, Start over, the subheading on one line, the sign’s dots.
2. **Stage 2:** a cleaned copy of Pixelify Sans under a new name (OFL): outlines snapped to its 11-unit grid, whole-pixel advances, kerning off, ascent and descent on the grid, WOFF2 subset, one regular weight or a true two-pixel bold (never interpolated). Both fonts self-hosted in docs/fonts with `font-display: block` and preloads, the Google link removed, sw.js caching them. Every Pixelify size becomes `round(nearest, X, var(--px))` with `--px` = 11/dpr. The hook shrink steps between crisp sizes only. Started Oct 19 night by an agent in the session scratchpad. If that work was lost, start it again from this plan and the audit’s prototype approach (snap every point, strip kerning, static instance).
3. **Stage 3:** list the hooks that still don’t fit at the stage-2 sizes on the smallest phone, send them to the editor to shorten (each change goes back through all three reviewers), then remove hook shrinking. Shorten the Lapuente card the same way.
