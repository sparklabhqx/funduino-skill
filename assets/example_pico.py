#!/usr/bin/env python3
"""
Worked Funduino episode — "Der Raspberry Pi Pico" (~24s, German).
The script + caption chunking are reconstructed from the real Funduino reel.
Copy this file per topic and edit the CONFIG + the scene bodies in draw_frame().

Run with SYSTEM python3 (has pycairo):
    python3 example_pico.py            # render mp4
    python3 example_pico.py probe      # dump one still per scene into out/
Keep funduino.py in the same folder (the script adds its own folder to sys.path).
"""
import os, sys, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import funduino as fn
from funduino import *          # palette + helpers (TEAL, block, caption, led, ...)

# ── CONFIG ───────────────────────────────────────────────────────────────────
PROJECT = os.path.dirname(os.path.abspath(__file__))   # self-contained
OUTPUT  = f"{PROJECT}/out/pico.mp4"
fn.DUR  = 24.0

BG_LIGHT = make_background_light()     # THE canvas — every scene, no dark, no crossfade
CAP_Y    = int(H*0.80)     # lower-fifth zone left BLANK for the user's own subtitles
HERO_Y   = int(H*0.42)
# ONE transform shrinks every scene's art around the hero point (the background stays
# full-frame). KEEP THIS AT 0.60 — art sized "right" on a desktop reads far too big in
# a phone-sized reel; the user has sent 0.86 back as "too big". Sparse is the style.
CONTENT_SCALE = 0.60

def draw_frame(t):
    sur = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H); c = cairo.Context(sur)
    c.set_source_surface(BG_LIGHT, 0, 0); c.paint()   # bright canvas throughout
    # NOTE: every stroke below passes a colour ROLE (LINE / ACC / LABEL / MUTED / GHOST).
    # The engine's rgb= defaults are WHITE from the retired dark canvas and would be
    # invisible here. "Active" goes DARKER + fatter, never brighter.

    c.save()                               # ── global content scale (wraps ALL scenes)
    c.translate(W/2, HERO_Y); c.scale(CONTENT_SCALE, CONTENT_SCALE)
    c.translate(-W/2, -HERO_Y)

    # SCENE 1 — title (board hero — NO logo) ------------------------------
    if t < 4.5:
        a = scene_alpha(t, 0.0, 4.2)
        bob = math.sin(t*2.2)*8
        board_icon(c, W/2, HERO_Y+bob, w=560, a=a*ease_out((t-0.2)/0.7), rgb=LINE, lw=6)
        # subtitle (user overlays own): "DER RASPBERRY PI *PICO*"  — engine draws nothing here

    # SCENE 2 — a small microcontroller (the RP2040 chip) -------------------
    if 4.0 < t < 9.0:
        a = scene_alpha(t, 4.2, 8.6); lt = t-4.2
        chip(c, W/2, HERO_Y, w=420, a=a, rgb=LINE, lw=6, pins=5, label="RP2040")
        # teal pads breathing around the chip
        for ang in range(0, 360, 45):
            r = 300 + math.sin(lt*3+ang)*6
            x = W/2+math.cos(math.radians(ang))*r; y = HERO_Y+math.sin(math.radians(ang))*r*0.7
            S(c, ACC, a*0.5); c.new_path(); c.arc(x, y, 6, 0, 2*math.pi); c.fill()
        # subtitle (user overlays own): "EIN KLEINER *MIKROCONTROLLER*"

    # SCENE 3 — starts your code instantly, no OS (flow into the chip) ------
    if 8.4 < t < 13.6:
        a = scene_alpha(t, 8.6, 13.2); lt = t-8.6
        chip(c, W/2, HERO_Y, w=300, a=a, rgb=LINE, lw=5, pins=4, label="RP2040")
        path = [(150, HERO_Y), (W/2-170, HERO_Y)]
        wire(c, path, rgb=LINE, a=a*0.55, lw=4)
        flow(c, path, lt, rgb=ACC, a=a, n=4, speed=0.6, r=10, glow=False)
        ab, dxb = enter(lt, 0.1)
        block(c, "KEIN BETRIEBSSYSTEM", W/2 - dxb, HERO_Y+260, 50, blk=TEAL_D, a=a*ab)
        # subtitle (user overlays own): "STARTET DEINEN *CODE* SOFORT"

    # SCENE 4 — drives sensors / an audio-reactive LED (pulsing LED) --------
    if 13.0 < t < 18.2:
        a = scene_alpha(t, 13.2, 17.8); lt = t-13.2
        chip(c, 320, HERO_Y+40, w=210, a=a, rgb=LINE, lw=5, pins=3, label="PICO")
        pulse = (math.sin(lt*7)*0.5+0.5)        # "reacts to music"
        path = [(420, HERO_Y+40), (W-360, HERO_Y-20)]
        wire(c, path, rgb=LINE, a=a*0.55, lw=4)
        flow(c, path, lt, rgb=ACC, a=a, n=3, speed=0.7, r=8, glow=False)
        led(c, W-300, HERO_Y-40, r=70, a=a, rgb=LINE, lw=7, glow=pulse)
        # little equaliser bars under the LED
        for i in range(5):
            bh = 26 + abs(math.sin(lt*6+i))*70
            S(c, ACC, a*0.8); rrect(c, W-340+i*32, HERO_Y+130-bh, 18, bh, 5); c.fill()
        # subtitle (user overlays own): "EINE LED DIE AUF *MUSIK* REAGIERT"

    # SCENE 5 — outro (CTA — NO logo) -------------------------------------
    if t > 17.6:
        a = scene_alpha(t, 17.8, fn.DUR)
        a1, dx1 = enter(t-17.8, 0.10); a2, dx2 = enter(t-17.8, 0.24)
        block(c, "BOARD FÜR SCHNELLE", W/2 - dx1, HERO_Y+40, 64, blk=TEAL_D, a=a*a1)
        block(c, "DIY-IDEEN", W/2 - dx2, HERO_Y+190, 64, blk=TEAL, a=a*a2)
        # subtitle (user overlays own): "ABONNIERE UNSEREN *KANAL*"

    c.restore()                            # ── end global content scale
    progress_bar(c, t, a=0.9)              # (bar stays full-width — outside the scale)
    sur.flush(); return sur

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "probe":
        probe(draw_frame, (1.8, 6.4, 10.8, 15.4, 21.0), f"{PROJECT}/out")
    else:
        fn.render(draw_frame, OUTPUT, dur=fn.DUR)
