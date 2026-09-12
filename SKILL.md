---
name: funduino
description: >-
  Produce a vertical (1080x1920) short-form German educational electronics reel in
  the "Funduino" house style — an all-light theme: the clean studio-grey product-shot
  canvas in EVERY scene (no on-screen logo/wordmark), all art in two-tone teal
  line-art. The reel burns in NO captions — the user adds their own
  subtitles later. Frame-by-frame pycairo ->
  ffmpeg, turnkey macOS fonts. ALSO writes the short German voiceover + subtitle-cue
  script in the Funduino voice. Use whenever the user wants a Funduino reel, a
  /funduino video or script, a German Arduino/electronics-explainer short (sensors,
  boards, components, "was ist ein X") in the teal Funduino brand, a TikTok/Reels/
  Shorts in this clean studio look, or says "make another Funduino episode". Sibling
  of schematik-video and /reel; pick this one for the teal Funduino brand + German.
---

# Funduino Video

Make one vertical German educational electronics reel in the **Funduino** house
style — and/or write its script. Each frame is drawn with **pycairo** and piped as
raw BGRA to **ffmpeg** (libx264), 1080×1920, 30 fps, no audio. Everything reusable
lives in `assets/funduino.py`; copy `assets/example_pico.py` as the start of a new
topic. The German voiceover + subtitle-cue script is generated from the formula in
`assets/SCRIPT_TEMPLATE.md`.

**This skill does two things** — do whichever the user asks (often both):
1. **Script** — a short German VO + chunked teal-keyword subtitle cues (see "Write the script").
2. **Video** — the animated reel rendered from that script (it carries NO on-screen text).

## Hard rules — every episode (real corrections; do NOT repeat them)

Quick checklist; the sections below have the detail. Skipping any of these is the mistake.
1. **Gate the script on a rewrite FIRST** — show the VO draft, get the user's wording, THEN build/render. Never render off your own first draft.
2. **No on-screen logo / wordmark** — never call `funduino_logo()` in any scene.
3. **No burned-in captions** — never call `caption()`; leave the lower fifth (`y ≳ H*0.78`) empty for the user's OWN subtitles. You still WRITE the chunked cues in the script.
4. **Never the word "Arduino"** — say **UNO** / **UNO board** / **Mikrocontroller** (in the VO, the cues, AND the art labels).
5. **Fixed CTA** — always end on »Wenn du mehr über Elektronik lernen willst, dann abonniere unseren Kanal!« (cue `ABONNIERE UNSEREN *KANAL*`).
6. **Wire real circuits** — a 2-pin analog sensor is a voltage divider (5V → sensor → node → pull-down R → GND, node → analog pin); connect ALL pins; land wires on **header pins**, never the USB jack (rotate the board 90° if the jack faces the wiring).
7. **Small & clean art** — lots of negative space (global `CONTENT_SCALE = 0.60`, NOT 0.75–0.86: the user has sent art back as "too big"); compact glows (no big translucent halos); a light **beam stops AT the target's surface**, never through it.
8. **The canvas is BRIGHT in every scene** — `make_background_light()` throughout, no dark canvas, no crossfade. Colour every stroke with a role (`LINE ACC LABEL MUTED GHOST`); an unspecified `WHITE` default is invisible. "Active" reads **darker + fatter**, never brighter, and `flow()` needs `glow=False`.
9. **Verify visually every time** — read the probe PNGs: lower fifth empty, no washed-out strokes, one focal element, nothing overlaps.

## Working directory

Pick a project folder (anywhere — e.g. `~/Documents/Funduino_Video_GEN/`) and copy
`assets/funduino.py` + your episode `.py` into it. The episode adds its own folder to
`sys.path` and derives all paths from its own location, so a project is self-contained
and movable. Render with a **python3 that has pycairo**.

## Setup

Turnkey on macOS — the brand fonts default to system **Arial** faces (Rounded Bold
reads like the Funduino logo), so nothing to install beyond:
1. `brew install cairo freetype ffmpeg` (Linux: `libcairo2`, `libfreetype6`, `ffmpeg`).
2. `python3 -m pip install pycairo` (or `brew install py3cairo`).
3. *(optional, closer logo match)* install a rounded geometric face (Poppins,
   Quicksand, Baloo 2) and point the engine at it:
   `FUNDUINO_FONT_DISPLAY=/path/Poppins-Bold.ttf`,
   `FUNDUINO_FONT_ITALIC=/path/Poppins-BoldItalic.ttf`,
   `FUNDUINO_FONT_BODY=/path/Poppins-SemiBold.ttf`. Fonts load by file path via
   FreeType (never fontconfig, which silently mis-resolves display faces).

## The look (non-negotiable house style)

- **One canvas, all light.** EVERY scene — title, explainers, outro — paints
  `make_background_light()` (a soft seamless studio wall + grounded floor shadow,
  exactly the real Funduino product-shot look). One line, every frame:
  `c.set_source_surface(BG_LIGHT, 0, 0); c.paint()`. There is **no dark canvas and no
  crossfade** — do not build `BG_DARK`, do not write a `df = clamp(...)` line.
  (`make_background_dark()` survives in the engine only so the archived dark episodes
  still render. The 19 episodes before Aug 2026 use the retired two-canvas look;
  `balance_spoon.py` and `vibration_light.py` are the all-light references.)
- **One accent only: TEAL `#538b82`** — in two tones, because a bright canvas inverts
  the contrast logic. Never a second colour, never italics-for-emphasis (italics are
  reserved for the "duino" wordmark). **Pass a role to every draw call:**

  | role | value | use |
  |---|---|---|
  | `LINE`  | `TEAL_D` | structure line-art — boards, wires, outlines, cutaways |
  | `ACC`   | `TEAL`   | accents: current dots, pings, callout rings, fills |
  | `LABEL` | `TEAL_D` | the primary / emphasised label, hero numbers |
  | `MUTED` | `TEAL`   | secondary labels (pin names, units, sub-captions) |
  | `GHOST` | `DARK`   | inactive graphics, always at low alpha (~0.3) |

  The engine's own defaults are still `WHITE` (white-on-dark) — an omitted `rgb=`
  therefore renders **invisible** on the studio canvas. `block()` is the exception
  that needs nothing: a filled teal card with white text reads on any ground.
- **No on-screen logo — ever.** Do NOT call `funduino_logo()` or otherwise draw the
  "Fun duino" wordmark in any scene. The brand carries through the studio-grey look,
  the single teal accent and the caption alone — keep the title/outro clean. (Plain
  `board_icon()` line-art is still fine as a *component*, e.g. an UNO in a wiring
  scene — that's a board drawing, not the wordmark.)
- **No burned-in text in the lower fifth.** The reel renders NO on-screen captions —
  the user overlays their own subtitles afterwards, so the lower fifth (`y ≳ H*0.78`,
  around `CAP_Y ≈ H*0.80`) must stay empty. You still WRITE the chunked caption text in
  the script (it's the user's subtitle source) — it just isn't drawn. Keep every
  in-scene label/block (specs, pin names) up in the hero area, clear of that zone.
- **Hero per scene** = ONE focal object: a board (`board_icon()`), a module/IC
  (`chip()`), an LED (`led()`), pins (`pin_header()`), topic-specific line-art you draw,
  or a **real 3D part rendered from a STEP file** (`draw_sprite()` — see "Add a 3D
  model"). Dark-teal (`LINE`) strokes, mid-teal accents, generous negative space.
- **Motion:** slide-in with overshoot (`enter()`, `ease_back`), gentle bob, current /
  signal `flow()` along a `wire()` — draw the wire ON first (`wire(draw=…)`, staggered
  per wire), THEN start the dots. Dip-through-background scene transitions
  (`scene_alpha()`), each scene settling in with a small `scene_lift()`. Line-art
  heroes draw on via a clip sweep; fans/arcs GROW outward (animate radius / sweep
  angle); the hero number `pop_scale()`s in while it rolls. One-shot `ring_ping()`
  accents mark the story beats (detect-ping, turn-on flash, CTA pulse) — on light,
  give a ping `LINE` and `lw=6` so it stays legible as it fades. On the title card
  give the hero a `pop_scale()` entrance + micro-sway over a small contact shadow
  (`BLACK` at ~0.14) that answers the bob. A thin teal `progress_bar()` is a tidy touch.
- **Language: German, "du"-form, casual.** Subtitle cues are ALL-CAPS with umlauts
  (Ä Ö Ü ß) — written for the user to overlay, not rendered on screen.
- **Keep the reading level LOW** (a real correction — a draft came back as "too
  complicated and intricated sentences"). One idea per sentence; short main clauses;
  avoid stacking a subclause, a colon and quotes into one line. The fixed CTA is the
  only sentence allowed a subordinate clause. Swap hard compounds for everyday words
  (`Sekundenbruchteil`→`ganz kurz`, `Erschütterung`→`Stoß`, `wie empfindlich er sein
  soll`→`wie viel er merken soll`). Cut the second example rather than lengthen a beat.
  Check the ART too: an in-scene label like `ERSCHÜTTERUNGEN` re-imports the hard word
  the VO just dropped.
- **Never say "Arduino"** in the VO or captions (brand rule, every episode). Say
  **"UNO board"** (or just **"UNO"**) for the board, or **"Mikrocontroller"** for the
  generic part. Labels in the art use "UNO" too. (The `board_icon()` glyph is fine — it's
  just a board shape, not the word.)
- **Fixed CTA — beat 6, every episode.** The reel always ends on the same line:
  »**Wenn du mehr über Elektronik lernen willst, dann abonniere unseren Kanal!**« →
  caption `ABONNIERE UNSEREN *KANAL*`. Never a website CTA.

## Write the script

Read `assets/SCRIPT_TEMPLATE.md` and follow the **6-beat formula** (Hook → Einordnung
→ Kern → Detail → Wofür/Projekt → CTA). Deliverable for a "just the script" request:
the **VO** (2–4 German sentences, du-form) plus the **SUBTITLE CUES** (chunked, ALL-CAPS,
one `*keyword*` each, in playback order, ending on the **fixed subscribe CTA** —
`ABONNIERE UNSEREN *KANAL*`, see the language rules above). These chunks are what the
user overlays as their OWN subtitles — the video never burns them in. When you also
build the video, each chunk just sets one scene's timing/length; render nothing in the
lower fifth (keep the cue as a `# comment` in the scene for reference).

**ALWAYS gate the script on a rewrite.** When you have a first-draft VO, STOP and show
it to the user, then ask them to rewrite it (or approve it) before you build/render
anything. The user voices these reels, so the wording is theirs — never render off your
own first draft. Once they reply with their rewrite, re-chunk the captions to match it
and continue. (If they only asked for the script, just deliver the draft and the offer.)

## Build a new episode

1. `cp assets/example_pico.py <project>/<topic>.py` (keep `funduino.py` in that folder).
2. Edit the CONFIG block: `OUTPUT`, `fn.DUR`. Leave `CONTENT_SCALE` at **0.60** — the
   template already wraps every scene in that transform (see the size rule below).
3. Write the script (above) and **get the user's rewrite/approval BEFORE rendering** —
   do not skip this gate. Then rewrite the scene bodies in `draw_frame(t)`,
   keeping the structure:
   - **Scene 1:** hero (`board_icon`/`chip`/3D sprite) only. No logo, no caption.
   - **Scenes 2..N-1:** one hero each; optional `block()` / `text()` sub-label up in
     the hero area, `flow()` for signal/current, `led(glow=…)` / equaliser bars /
     `roll_number()` for a spec. No bottom caption.
   - **Scene N:** CTA art (e.g. a teal play/subscribe button). No logo, no caption.
   - Every scene sits on the SAME light canvas — the separation between them comes from
     `scene_alpha()` dips and `scene_lift()`, not from a background change.
   - Leave the lower fifth EMPTY in every scene (the user adds subtitles there); keep the
     per-scene subtitle cue as a `# comment` for reference.
   - Gate each scene with `scene_alpha(t, t0, t1)` and pass its `a` to EVERY draw call so
     dips stay clean. Pass a colour role to every draw call too (see the table above).
4. Probe, then render:
   - `python3 <topic>.py probe`  → one still per scene in `out/`
   - `python3 <topic>.py`        → the mp4
5. **Verify visually (always):** Read the probe PNGs (or `ffmpeg -i out/<topic>.mp4 -vf
   fps=1 /tmp/f_%02d.png`). Confirm the lower fifth is clear (NO burned-in text) for the
   user's subtitles, one focal element per scene, in-scene labels stay above the subtitle
   zone, and **nothing is washed out** — every stroke got a role, no `WHITE` leftovers,
   no pale `flow()` halos. A scene-midpoint probe can miss a one-shot beat entirely: if
   the story turns on a brief event (a contact closing, a trigger firing), compute WHICH
   frames it occupies and probe those, or you will verify a frame where it isn't there.

## Key building blocks (in `funduino.py`)

- `make_background_light()` — THE canvas; build once, paint every frame.
  (`make_background_dark()` is legacy — archived episodes only, never a new one.)
- `funduino_logo()` — exists in the engine but is **deprecated: never call it** (no logo).
- `board_icon(c, cx, cy, w, ...)` — line-art board for components (e.g. an UNO). Not the logo.
- `caption(...)` — the old signature-caption renderer; **deprecated — do NOT call it**
  (videos render no on-screen text; the user overlays their own subtitles).
- `block(c, text, cx, cy, size, blk=TEAL, txt=WHITE)` — chunky text on a rounded block.
- `text(...)` — plain labels (advances by x_advance so spaces render). `heavy(...)` — raw display text.
- `chip()`, `led(glow=)`, `pin_header()` — generic component line-art (extend per topic).
  `led(glow=0..1)` lights the dome from the INSIDE (filled core + tight rim); it used to
  fill a disc at 1.8–2.3× r, which smudged on light — do not reintroduce a wide halo.
- `load_sprite(path)` + `draw_sprite(c, surf, cx, cy, vis_w, flip=, vis=, pins=)` — drop a
  **real 3D part** (a STEP render) into a scene; returns pin tips in canvas coords. See
  "Add a 3D model" below.
- `wire(c, pts, draw=)` + `flow(c, pts, t, glow=False)` — a trace + dots travelling it
  (current/data/signal). `draw`<1 strokes only the first fraction of the path's LENGTH —
  animate it (staggered per wire) for a draw-on, and gate the `flow()` until laid.
  **Always pass `glow=False`** on the light canvas (see Gotchas).
- `ring_ping(c, cx, cy, p, r0=, r1=)` — ONE expanding, fading ring: a detect-ping, a
  turn-on flash, a CTA pulse. Drive `p` with `clamp()` (one-shot) or `(lt*rate)%1.0`
  (repeating). Keep radii compact — it REPLACES big halos, it must not become one.
- `scene_lift(lt)` — small vertical settle on scene entry: wrap the scene's art in
  `c.save(); c.translate(0, scene_lift(lt)); … c.restore()` alongside `scene_alpha`.
- `roll_number(value, …, suffix=)` — count a spec up from 0 (one hero number per video).
- `marker(...)` — translucent teal highlighter behind a key term. `progress_bar(t)`.
- `enter(lt, delay)`→(alpha, dx); `scene_alpha(t,t0,t1)`; `ease_out/ease_back/pop_scale/clamp`.
- `render(draw_frame, output, dur)`; `probe(draw_frame, times, outdir)`.
- Roles (use these): `LINE ACC LABEL MUTED GHOST`. Raw palette: `TEAL TEAL_D TEAL_L
  PAPER DARK INK WHITE SMOKE BLACK` — `WHITE`/`SMOKE`/`INK` are for the legacy dark
  canvas; on light only `BLACK` (contact shadows) and `PAPER` still apply directly.
  Fonts: `DISPLAY ITALIC BODY`.

## Add a 3D model (STEP / .stp file)

When the user supplies a CAD part (or the line-art hero looks too plain), render the
**real component** from its STEP file and composite it instead of the line-art. Keep
this for solid-object scenes only — a cutaway / "what's inside" scene must stay line-art
(a solid model can't show internals). If you swap the sensor in one scene, swap it in
ALL the solid-object scenes so the video stays consistent.

`assets/render3d.py` is a pure-CPU STEP→glb→rasterizer (no Blender/GPU). Steps:
1. One-time venv — put it OUTSIDE iCloud-synced paths (a venv inside
   `~/Documents` gets evicted and every run then hangs at 0% CPU):
   `python3 -m venv ~/.venvs/<project>3d` then
   `~/.venvs/<project>3d/bin/pip install cascadio trimesh numpy pillow`.
2. Pick an angle: `.venv3d/bin/python render3d.py --step part.step --glb model/m.glb --mode grid`
   → look at `ang_*.png`, choose a yaw that shows the part (and its pins) clearly.
3. Render a hero: `… --glb model/m.glb --mode hero --out model/hero.png --yaw 26 --pitch 24
   --res 1500 --down 1000` (transparent RGBA PNG).
4. **Measure once** (the sprite has transparent margin, so the raw image box is wrong):
   load the PNG, take the opaque-pixel bbox for `vis=(cx_frac, cy_frac, w_frac)`, and cluster
   the opaque columns in the top region for the pin-tip fractions. Hardcode both — they're
   resolution-independent.
5. In the episode: `SPR = load_sprite("model/hero.png")`, then per scene
   `pins = draw_sprite(c, SPR, cx, cy, vis_w, a=a, flip=True, vis=(...), pins=[(...),...])`.
   Use the returned `pins` as `wire()` endpoints — connect **every** pin of the module to the
   target (e.g. all 3 of a KY-015), not just one. `flip=True` rotates 180° so a module
   stands on its pins. For a **bare 2-pin analog sensor** (LDR, NTC, FSR…) draw the real
   **voltage divider**, not a single wire: 5V → sensor → node → pull-down resistor → GND,
   with the node tapping the analog pin (e.g. `A0`). Both sensor pins must be in the circuit
   (`resistor_box(..., vertical=True)` returns its two terminals for wiring — see `ldr.py`).
   Land board wires on a **header pin**, never the USB jack — rotate `board_icon()` 90°
   (wrap it in `translate/rotate(π/2)/translate`) if the jack faces the wiring.

The render caches as a surface, so compositing is one fast `paint` per frame — full-length
renders stay quick. Worked example lives in `~/Documents/explainer_funduino/dht_sensor.py`
(KY-015 DHT11 module).

**STEP colours often survive the glb conversion** (SolidWorks assembly
exports do). Then don't match geometry to recolour — match the exact material
`baseColorFactor` in a small `load_world` wrapper (see
`~/Documents/explainer_funduino/model_esp/render_esp.py`): e.g. a WROOM shield
that arrives brown-black -> silver (215,218,222), a lavender USB shell -> neutral
silver, a pure-black PCB lifted to (26,28,32) so its faces still separate.

**Upgrading an existing episode's line-art hero to a sprite** (done for
pi_vs_esp + esp_voltage, 2026-09-12) — the traps:
- The measured `vis` bbox includes protruding header pins, so the PCB inside it
  is smaller than the line-art board was. Pass `vis_w` = old line-art `w` × ~1.1
  and the PCB keeps its size — existing wire endpoints then still land on the
  header edge.
- Land wires only where pins/rings are actually VISIBLE in the render: a module
  can occludes its side of the header (no gold rings beside the can), so move
  anchors into ring territory instead of keeping the old line-art coordinate.
- Overlay marks (a crack, a ping target) need the sprite's LIGHT areas — a
  dark-teal stroke vanishes on a black PCB; anchor it on the silver can.
- Lying board: wrap `draw_sprite` in `translate/rotate(-π/2)/translate`. Docking
  props (a USB plug) must meet the REAL connector — find its position by mapping
  the image-fraction offset through flip+rotation — and may need mirroring
  (`scale(-1,1)`) so the plug's metal shell faces the part.
- Keep the old line-art def if other episodes borrowed it (grep first); note
  "Video v2" in the episode's `<topic>_script.txt`. VO/cues stay unchanged, so
  nothing needs re-recording.

Sprites need **no recolouring** for the light canvas — a real part carries its own
material colours, so it is the one element the theme doesn't touch (the SW-420's
black-and-brass switch actually reads better on studio grey than it did on charcoal).
Still check the probe: a part that is nearly white, or a pale PCB, can lose its edge
against the backdrop — if so re-render it with a darker soldermask via `--pcb`.

## Gotchas

- Run episodes + `funduino.py` with **system python3** (must have pycairo). Use the
  **separate 3D venv** (`~/.venvs/<project>3d`) only for `render3d.py` (STEP
  rendering) — never mix the two.
- Pass scene alpha `a` into EVERY draw call, or elements won't fade at transitions.
- **No burned-in text** — never call `caption()`; leave the lower fifth (`y ≳ H*0.78`)
  empty for the user's own subtitles, and keep in-scene labels above that zone.
- **Never draw the logo/wordmark** — no `funduino_logo()` in any scene (brand rule).
- Keep it minimal/clean: one focal element per scene, lots of negative space. Teal is
  the only accent — resist adding a second colour.
- Explain a mechanism as a **literal mini-story**, not an engineer's plot (real
  correction): a walker crossing two labelled detection fields — fill + label wake
  while the heat is inside, flash + `ring_ping()` on the switch — beats an abstract
  differential/oscilloscope trace. If a scene needs a scope to make sense, restage it
  with the person/object actually doing the thing.
- **"Active" cannot mean brighter** (the big light-canvas trap, a real correction). On
  the retired dark canvas a thing lighting up went white→teal, i.e. brighter. Recolour
  that naively for light and it inverts: mid-teal on off-white has LESS contrast than
  dark teal, so the lit element *recedes* and the story beat vanishes. On light, an
  activating element goes **darker and fatter**: full-alpha `LINE` at ~1.6× line width
  against resting strokes held at ~0.78 alpha / 0.85×, plus a filled `LINE` dot and a
  `ring_ping`. For bar/graph states use colour-vs-grey instead: the triggering bar is
  `LABEL`, the quiet ones are `GHOST` at ~0.3 alpha, so *colour appearing* is the signal.
  Worked example: `vibration_light.py` `spring_capsule()` (contact) + scene 6 (threshold).
- **`flow()` needs `glow=False` on light.** Its glow pass paints an `r*2.1` disc at 0.30
  alpha behind each dot — invisible on charcoal, but a pale green smudge on off-white,
  and exactly the "big translucent halo" this style bans. Kill the glow and, if the dots
  were deliberately dimmed, lift their alpha ~0.1 to compensate for the lost mass.
- Keep glows/halos **compact** — a big translucent disc behind an icon (sun, LED) bleeds
  into nearby text. Give each icon clear space; a tight ring + short rays reads cleaner.
- A light **beam/ray hitting a component must stop at its surface**, not pass through it —
  end the wave/line at the part's near edge (taper its amplitude to 0 there). See `ldr.py`
  scene 3 (`light_wave()` from the sun to the LDR's sun-facing edge).
- Keep hero art **compact** — lots of negative space beats full-bleed. Scaling every
  scene's art around the hero point (one transform wrapping the scenes in `draw_frame`,
  like `ldr.py`'s `CONTENT_SCALE`) shrinks them all at once and leaves more room for the
  user's subtitles. **Set it to ~0.60** — a real correction: 0.86 was built once and the
  user came back with "too big, make it 70 percent", i.e. 0.86 × 0.70 ≈ 0.60. Art that
  looks right at full size in the editor reads far too big in a phone-sized reel. If a
  scene looks sparse at 0.60, that is the house style — do NOT compensate by enlarging
  the art; the emptiness is where the subtitles and the eye go.
- This is the **German Funduino** brand. For the warm graph-paper English "Schematik"
  look use `schematik-video`; for the black/white `/reel` look use that command.
