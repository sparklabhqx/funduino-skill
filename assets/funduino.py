#!/usr/bin/env python3
"""
funduino.py — reusable engine for "Funduino"-style educational electronics reels.

1080x1920 (9:16) vertical, 30 fps, no audio. Pipeline: pycairo draws each frame
onto an ARGB surface -> raw BGRA piped to ffmpeg (libx264).

House style (the NEW Funduino identity — see SKILL.md "The look"):
    - LIGHT studio-gradient bookends (title / hero / outro): a soft seamless grey
      backdrop with a floor shadow, exactly like the real Funduino product shots.
    - DARK charcoal "lab" canvas for the explanatory / animation scenes, with a
      faint dot grid and a single teal glow. White / teal line-art hero objects.
    - One accent only: TEAL (#538b82). Emphasis is teal, never a second colour.
    - NO burned-in captions: the reel renders no on-screen text; the lower fifth is
      left blank so the user can overlay their own subtitles. (caption() still exists
      below but is DEPRECATED — never called in episodes.)
    - NO on-screen logo: the funduino_logo() wordmark still exists in this engine but
      is DEPRECATED and never drawn in videos (brand rule — see SKILL.md "The look").

Run with a python3 that has pycairo. Fonts are loaded by file path via FreeType
(NOT fontconfig, which can silently mis-resolve display fonts to a system
fallback). Defaults are macOS system Arial faces (Rounded Bold reads like the
logo) so the skill is turnkey with no font install. Override with FUNDUINO_FONT_*
env vars (e.g. point DISPLAY at Poppins / Quicksand for a closer logo match).

Typical episode:
    import funduino as fn
    from funduino import *
    fn.DUR = 24.0
    BG_LIGHT, BG_DARK = make_background_light(), make_background_dark()
    def draw_frame(t): ...                      # compose scenes
    fn.render(draw_frame, "/path/out.mp4", dur=fn.DUR)
"""
import cairo, math, random, subprocess, ctypes, os

# ── canvas ─────────────────────────────────────────────────────────────────────
W, H = 1080, 1920
FPS  = 30
DUR  = 24.0          # episodes set this (scene_alpha reads it); also passed to render()

# ── palette (sampled from the Funduino logo + brand colour band) ────────────────
PAPER   = (0.957, 0.957, 0.945)   # #f4f4f1  off-white (light bg base)
PAPER_D = (0.800, 0.804, 0.804)   # darker grey for the studio gradient floor
INK     = (0.141, 0.141, 0.141)   # #242424  charcoal "lab" canvas
INK2    = (0.110, 0.110, 0.110)   # #1c1c1c  charcoal vignette edge
DARK    = (0.227, 0.227, 0.227)   # #3a3a3a  the wordmark "Fun" grey / dark panels
TEAL    = (0.325, 0.545, 0.510)   # #538b82  THE accent — keywords, line-art accent
TEAL_D  = (0.231, 0.408, 0.380)   # #3b6861  deeper teal (shadows / blocks)
TEAL_L  = (0.451, 0.671, 0.635)   # #73aba2  lighter teal (glow / hovers)
WHITE   = (0.969, 0.973, 0.969)   # #f7f8f7  line-art / captions on dark
SMOKE   = (0.620, 0.635, 0.631)   # muted grey for secondary labels
BLACK   = (0.086, 0.086, 0.086)   # #161616  caption text on light / outlines

# ── colour ROLES — use these, not the raw palette names above ───────────────────
# The house canvas is BRIGHT in every scene (make_background_light throughout), but
# the engine's line-art defaults are still white-on-dark from the retired two-canvas
# era. On a light canvas an unspecified WHITE stroke is invisible, so pass a role to
# every draw call. Two-tone teal: dark carries structure + emphasis, mid carries
# accents + secondary labels, neutral grey is the only "inactive" state.
LINE  = TEAL_D    # structure line-art             (dark canvas used WHITE)
ACC   = TEAL      # accent / current / pings       (unchanged)
LABEL = TEAL_D    # primary, emphasised label      (dark canvas used TEAL)
MUTED = TEAL      # secondary label                (dark canvas used SMOKE)
GHOST = DARK      # inactive graphics at low alpha (dark canvas used SMOKE)
# "Active" must read DARKER + FATTER, never brighter — mid-teal recedes on off-white.

# ── fonts: load .ttf/.otf directly via FreeType (bypass fontconfig) ─────────────
# Defaults are macOS system faces (always present). Roles:
#   DISPLAY = rounded heavy face for the wordmark, headline blocks, big numerals
#             (Arial Rounded Bold reads like the Funduino logo)
#   ITALIC  = bold italic for the "duino" half of the wordmark + emphasis
#   BODY    = bold sans for captions / labels (umlauts ä ö ü ß all supported)
_MAC = "/System/Library/Fonts/Supplemental"
DISPLAY = os.environ.get("FUNDUINO_FONT_DISPLAY", f"{_MAC}/Arial Rounded Bold.ttf")
ITALIC  = os.environ.get("FUNDUINO_FONT_ITALIC",  f"{_MAC}/Arial Bold Italic.ttf")
BODY    = os.environ.get("FUNDUINO_FONT_BODY",    f"{_MAC}/Arial Bold.ttf")

def _find(cands):
    for p in cands:
        if os.path.exists(p): return p
    return cands[0]
_ft    = ctypes.CDLL(_find(["/opt/homebrew/lib/libfreetype.6.dylib",
                            "/usr/local/lib/libfreetype.6.dylib",
                            "/usr/lib/x86_64-linux-gnu/libfreetype.so.6",
                            "libfreetype.so.6", "libfreetype.6.dylib"]))
_cairo = ctypes.CDLL(_find(["/opt/homebrew/lib/libcairo.2.dylib",
                            "/usr/local/lib/libcairo.2.dylib",
                            "/usr/lib/x86_64-linux-gnu/libcairo.so.2",
                            "libcairo.so.2", "libcairo.2.dylib"]))
_ftlib = ctypes.c_void_p()
if _ft.FT_Init_FreeType(ctypes.byref(_ftlib)) != 0:
    raise RuntimeError("FT_Init_FreeType failed")
_cairo.cairo_ft_font_face_create_for_ft_face.restype  = ctypes.c_void_p
_cairo.cairo_ft_font_face_create_for_ft_face.argtypes = [ctypes.c_void_p, ctypes.c_int]
_cairo.cairo_set_font_face.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
class _PycairoContext(ctypes.Structure):
    _fields_ = [("PyObject_HEAD", ctypes.c_byte * object.__basicsize__),
                ("ctx", ctypes.c_void_p), ("base", ctypes.c_void_p)]
_face_cache = {}
def _face(path):
    if path not in _face_cache:
        if not os.path.exists(path):
            raise FileNotFoundError(
                f"Funduino font not found:\n  {path}\n"
                "Set FUNDUINO_FONT_DISPLAY / FUNDUINO_FONT_ITALIC / FUNDUINO_FONT_BODY "
                "to .ttf/.otf file paths. Defaults are macOS Arial faces. See SKILL.md.")
        ftf = ctypes.c_void_p()
        if _ft.FT_New_Face(_ftlib, path.encode("utf-8"), 0, ctypes.byref(ftf)) != 0:
            raise RuntimeError("FT_New_Face failed (corrupt/unsupported font?): " + path)
        _face_cache[path] = _cairo.cairo_ft_font_face_create_for_ft_face(ftf, 0)
    return _face_cache[path]
def set_font_file(ctx, path):
    cctx = ctypes.cast(id(ctx), ctypes.POINTER(_PycairoContext)).contents.ctx
    _cairo.cairo_set_font_face(cctx, _face(path))

# ── easing / helpers ────────────────────────────────────────────────────────────
def clamp(v, lo=0.0, hi=1.0): return max(lo, min(hi, v))
def ease_out(t): return 1 - (1 - clamp(t))**3
def ease_in_out(t):
    t = clamp(t); return 4*t*t*t if t < 0.5 else 1 - (-2*t+2)**3/2
def ease_back(t):
    t = clamp(t); c1 = 1.70158; c3 = c1 + 1; u = t - 1
    return 1 + c3*u*u*u + c1*u*u
def pop_scale(t, start=0.6, over=1.07):
    """Scale factor for a 'snap-in': small -> overshoot `over` -> settle 1.0.
    Feed to block(..., scale=pop_scale(p)). An accent — use sparingly."""
    t = clamp(t)
    if t < 0.7: return start + (over-start)*ease_out(t/0.7)
    return over + (1-over)*ease_out((t-0.7)/0.3)
def scene_alpha(t, t0, t1, fade=0.28):
    """Dip-through-background fade: a scene fades in after t0 and out before t1, so
    adjacent scenes never sit double-opaque. Reads module-level DUR."""
    up   = 1.0 if t0 <= 0.0 else clamp((t - t0) / fade)
    down = 1.0 if t1 >= DUR else clamp((t1 - t) / fade)
    return clamp(min(up, down))
def enter(lt, delay, dur=0.55, dist=210):
    """(alpha, x-slide-offset) for a slick slide-in with overshoot. Subtract the
    offset from an element's x to make it slide in from the left."""
    al = clamp((lt - delay) / 0.28)
    sl = ease_back(clamp((lt - delay) / dur))
    return al, (1 - sl) * dist
def enter_dir(lt, delay, dir="left", dist=210, dur=0.55):
    """Accent variant of enter() -> (alpha, dx, dy, scale). Apply at (x+dx, y+dy)
    scaled by `scale`. dir in {left,right,up,down,pop}."""
    al  = clamp((lt - delay) / 0.28)
    sl  = ease_back(clamp((lt - delay) / dur))
    off = (1 - sl) * dist
    dx = dy = 0.0; sc = 1.0
    if   dir == "left":  dx = -off
    elif dir == "right": dx =  off
    elif dir == "up":    dy = -off
    elif dir == "down":  dy =  off
    elif dir == "pop":   sc = pop_scale(clamp((lt - delay) / dur))
    return al, dx, dy, sc
def S(c, rgb, a=1.0): c.set_source_rgba(*rgb, a)

# ── backgrounds (build once, reuse every frame) ─────────────────────────────────
def make_background_light():
    """Soft seamless grey studio backdrop + floor shadow — the Funduino product look."""
    sur = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H); c = cairo.Context(sur)
    # top-lit wall: light at the top, a touch darker low down
    g = cairo.LinearGradient(0, 0, 0, H)
    g.add_color_stop_rgb(0.0, *PAPER)
    g.add_color_stop_rgb(0.62, 0.918, 0.922, 0.918)
    g.add_color_stop_rgb(1.0, *PAPER_D)
    c.set_source(g); c.paint()
    # soft pool of light behind the hero
    rad = cairo.RadialGradient(W/2, H*0.40, H*0.05, W/2, H*0.40, H*0.55)
    rad.add_color_stop_rgba(0, 1, 1, 1, 0.55); rad.add_color_stop_rgba(1, 1, 1, 1, 0.0)
    c.set_source(rad); c.rectangle(0, 0, W, H); c.fill()
    # grounded floor shadow ellipse low-centre
    c.save(); c.translate(W/2, H*0.74); c.scale(1.0, 0.18)
    sh = cairo.RadialGradient(0, 0, 10, 0, 0, 520)
    sh.add_color_stop_rgba(0, 0, 0, 0, 0.16); sh.add_color_stop_rgba(1, 0, 0, 0, 0.0)
    c.set_source(sh); c.arc(0, 0, 520, 0, 2*math.pi); c.fill(); c.restore()
    sur.flush(); return sur

def make_background_dark():
    """LEGACY — the charcoal 'lab' canvas of the retired two-canvas era. Kept so the
    archived dark episodes still render; do NOT use it in a new episode (the house
    style is now make_background_light() throughout). See SKILL.md "The look"."""
    sur = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H); c = cairo.Context(sur)
    S(c, INK); c.paint()
    rad = cairo.RadialGradient(W/2, H*0.42, H*0.04, W/2, H*0.42, H*0.62)
    rad.add_color_stop_rgba(0, *TEAL, 0.16); rad.add_color_stop_rgba(1, *TEAL, 0.0)
    c.set_source(rad); c.rectangle(0, 0, W, H); c.fill()
    # dot grid
    S(c, WHITE, 0.05); step = 60
    y = step
    while y < H:
        x = step
        while x < W:
            c.arc(x, y, 1.7, 0, 2*math.pi); c.fill(); x += step
        y += step
    # vignette
    vg = cairo.RadialGradient(W/2, H/2, H*0.30, W/2, H/2, H*0.72)
    vg.add_color_stop_rgba(0, *INK2, 0.0); vg.add_color_stop_rgba(1, *INK2, 0.55)
    c.set_source(vg); c.rectangle(0, 0, W, H); c.fill()
    sur.flush(); return sur

# ── path / text primitives ──────────────────────────────────────────────────────
def rrect(c, x, y, w, h, r):
    r = min(r, w/2, h/2); c.new_path()
    c.arc(x+w-r, y+r, r, -math.pi/2, 0); c.arc(x+w-r, y+h-r, r, 0, math.pi/2)
    c.arc(x+r, y+h-r, r, math.pi/2, math.pi); c.arc(x+r, y+r, r, math.pi, 3*math.pi/2)
    c.close_path()

def _adv(c, s, track):
    return sum(c.text_extents(ch).x_advance + track for ch in s) - (track if s else 0)

def seg_w(c, s, size, font=DISPLAY, track=0.0):
    c.save(); set_font_file(c, font); c.set_font_size(size)
    w = _adv(c, s, track); c.restore(); return w

def text(c, s, x, y, size, rgb=WHITE, font=BODY, a=1.0, center=True, track=0.0):
    """Plain filled text, vertically centred on y. Advances by x_advance so spaces count."""
    c.save(); set_font_file(c, font); c.set_font_size(size)
    ex = c.text_extents(s); w = _adv(c, s, track)
    cx = (x - w/2) if center else x
    by = y - ex.height/2 - ex.y_bearing
    S(c, rgb, a)
    for ch in s:
        c.move_to(cx, by); c.show_text(ch); cx += c.text_extents(ch).x_advance + track
    c.restore()

def heavy(c, s, x, baseline, size, rgb, font=DISPLAY, a=1.0, track=2,
          outline=None, ow=0.0):
    """Heavy display text from left edge / baseline. Optional outline drawn first
    (the caption 'sticker' look). Returns the advance width."""
    c.save(); set_font_file(c, font); c.set_font_size(size)
    c.set_line_join(cairo.LINE_JOIN_ROUND); c.set_line_cap(cairo.LINE_CAP_ROUND)
    cx = x; c.new_path()
    for ch in s:
        c.move_to(cx, baseline); c.text_path(ch); cx += c.text_extents(ch).x_advance + track
    if outline is not None and ow > 0:
        S(c, outline, a); c.set_line_width(ow); c.stroke_preserve()
    S(c, rgb, a); c.fill(); c.restore()
    return cx - x - track

def block(c, s, cx, cy, size, blk=TEAL, a=1.0, txt=WHITE, font=DISPLAY,
          padx=34, pady=20, track=2, reveal=1.0, scale=1.0):
    """Chunky text on a rounded highlight block (a headline look). Default = teal
    block, white text. ACCENT: reveal<1 wipes the card open L->R; scale=pop_scale(p)
    snaps it in. Defaults reproduce a plain block. Returns (bw, bh)."""
    c.save(); set_font_file(c, font); c.set_font_size(size)
    caph = c.text_extents("HXjg").height; w = _adv(c, s, track); c.restore()
    bw, bh = w + 2*padx, caph + 2*pady
    c.save()
    if scale != 1.0:
        c.translate(cx, cy); c.scale(scale, scale); c.translate(-cx, -cy)
    rv = ease_out(clamp(reveal))
    if rv < 1.0:
        c.rectangle(cx-bw/2, cy-bh/2-6, bw*rv, bh+12); c.clip()
    S(c, blk, a); rrect(c, cx-bw/2, cy-bh/2, bw, bh, 16); c.fill()
    heavy(c, s, cx - w/2, cy + caph/2 - 2, size, txt, font=font, a=a, track=track)
    c.restore()
    return bw, bh

# ── the signature caption: ALL-CAPS rows, ONE keyword in teal, sticker outline ──
def _parse_caption(s):
    """'EIN RASPBERRY *PI*' -> [('EIN RASPBERRY ', False), ('PI', True)] tokens."""
    out, buf, hi = [], "", False
    for ch in s:
        if ch == "*":
            if buf: out.append((buf, hi)); buf = ""
            hi = not hi
        else:
            buf += ch
    if buf: out.append((buf, hi))
    return out

def caption(c, s, cx, cy, size=78, a=1.0, base=WHITE, hi=TEAL, font=DISPLAY,
            track=1, outline=BLACK, ow=10, upper=True, maxw=None):
    """The brand caption. Mark the key word with *asterisks* -> rendered in teal.
    Use '\\n' for a second line. White text + dark sticker outline on the dark canvas;
    pass base=BLACK, outline=PAPER, ow=0 for a clean look on the light canvas.
    Auto-shrinks `size` so the widest line fits `maxw` (default 92% width) — German
    captions are long, so never trust the requested size to fit."""
    if maxw is None: maxw = W*0.92
    lines = s.split("\n")
    # strip the * markers to measure raw line width, then shrink size to fit
    raw = [l.replace("*", "").upper() if upper else l.replace("*", "") for l in lines]
    widest = max((seg_w(c, r, size, font, track) for r in raw), default=0)
    if widest > maxw:
        sc = maxw / widest; size *= sc; ow *= sc
    c.save(); set_font_file(c, font); c.set_font_size(size)
    lh = c.text_extents("HXjg").height * 1.30
    c.restore()
    y0 = cy - lh*(len(lines)-1)/2
    for li, line in enumerate(lines):
        toks = _parse_caption(line.upper() if upper else line)
        total = sum(seg_w(c, t, size, font, track) for t, _ in toks)
        x = cx - total/2; by = y0 + li*lh
        for t, is_hi in toks:
            heavy(c, t, x, by + size*0.36, size, hi if is_hi else base,
                  font=font, a=a, track=track,
                  outline=outline if ow else None, ow=ow)
            x += seg_w(c, t, size, font, track)

# ── the Funduino wordmark (brand motif — allowed on title / outro) ──────────────
def board_icon(c, cx, cy, w, a=1.0, rgb=DARK, lw=4.0):
    """Line-art Arduino-style board: rounded outline, header pin rows top+bottom,
    a USB jack on the left edge, a chip + two round pads. Matches the logo glyph."""
    h = w*0.66; x, y = cx-w/2, cy-h/2
    c.save(); S(c, rgb, a)
    c.set_line_join(cairo.LINE_JOIN_ROUND); c.set_line_cap(cairo.LINE_CAP_ROUND)
    c.set_line_width(lw)
    rrect(c, x, y, w, h, h*0.16); c.stroke()
    # USB jack sticking out of the left edge
    jw, jh = w*0.12, h*0.30
    rrect(c, x-jw*0.7, cy-jh/2, jw, jh, 3); c.stroke()
    # header pin rows (small ticks) along top + bottom
    n = 12; m = w*0.10; pin = (w-2*m)/(n-1)
    for i in range(n):
        px = x+m+i*pin
        c.move_to(px, y+lw*1.4);     c.line_to(px, y+h*0.13)
        c.move_to(px, y+h-lw*1.4);   c.line_to(px, y+h-h*0.13)
    c.stroke()
    # central chip
    cw, ch = w*0.30, h*0.26
    rrect(c, cx-cw*0.15, cy-ch/2, cw, ch, 4); c.stroke()
    # two mounting pads
    for sx in (-0.36, 0.36):
        c.new_path(); c.arc(cx+sx*w, cy+h*0.18, w*0.035, 0, 2*math.pi); c.stroke()
    c.restore()

def funduino_logo(c, cx, cy, w=560, a=1.0, dark_on_light=True):
    """The wordmark: board icon + 'Fun' (grey) + 'duino' (teal italic).
    dark_on_light=True for the light bg; pass False on the dark canvas (whites out
    the 'Fun' half so it stays legible)."""
    fun_rgb = DARK if dark_on_light else WHITE
    size = w*0.205
    # measure the two words so we can centre icon+text as a unit
    wf = seg_w(c, "Fun", size, DISPLAY, 1)
    wd = seg_w(c, "duino", size, ITALIC, 1)
    icon_w = w*0.30; gap = w*0.045
    total = icon_w + gap + wf + wd
    x = cx - total/2
    board_icon(c, x + icon_w/2, cy, icon_w, a=a, rgb=fun_rgb, lw=max(3.5, w*0.008))
    bx = x + icon_w + gap; baseline = cy + size*0.36
    bx += heavy(c, "Fun",   bx, baseline, size, fun_rgb, font=DISPLAY, a=a, track=1) + 1
    heavy(c, "duino", bx, baseline, size, TEAL, font=ITALIC, a=a, track=1)

# ── generic component line-art (build topic art per episode; these are starters) ─
def chip(c, cx, cy, w, a=1.0, rgb=WHITE, lw=4.0, pins=4, label=None):
    """A black-box IC / module with pin legs both sides + a notch + dot-1 marker."""
    h = w*0.78; x, y = cx-w/2, cy-h/2
    c.save(); S(c, rgb, a); c.set_line_width(lw)
    c.set_line_join(cairo.LINE_JOIN_ROUND); c.set_line_cap(cairo.LINE_CAP_ROUND)
    rrect(c, x, y, w, h, 10); c.stroke()
    leg = w*0.16; gap = h/(pins+1)
    for i in range(pins):
        ly = y+gap*(i+1)
        c.move_to(x-leg, ly); c.line_to(x, ly)
        c.move_to(x+w, ly); c.line_to(x+w+leg, ly)
    c.stroke()
    c.new_path(); c.arc(x+w*0.18, y+h*0.18, w*0.05, 0, 2*math.pi); c.stroke()  # pin-1 dot
    c.restore()
    if label: text(c, label, cx, cy, w*0.16, rgb=rgb, font=DISPLAY, a=a, track=1)

def led(c, cx, cy, r, a=1.0, rgb=TEAL, lw=4.0, glow=0.0):
    """A round LED dome with two legs. glow in [0..1] lights the dome from the INSIDE —
    a filled core plus one tight rim following the dome, deliberately NOT a wide
    translucent halo: the old version filled a disc at 1.8-2.3x r, which bleeds into
    nearby text and reads as a grey smudge on the bright house canvas."""
    c.save()
    if glow > 0:
        S(c, rgb, a*0.34*glow)                       # lit core, inside the dome
        c.new_path(); c.arc(cx, cy, r*0.92, math.pi, 2*math.pi); c.close_path(); c.fill()
        S(c, rgb, a*0.40*glow); c.set_line_width(lw*0.7)   # tight rim, not a halo
        c.new_path(); c.arc(cx, cy, r*1.20, math.pi*1.04, 2*math.pi - math.pi*0.04)
        c.stroke()
    S(c, rgb, a); c.set_line_width(lw); c.set_line_cap(cairo.LINE_CAP_ROUND)
    c.new_path(); c.arc(cx, cy, r, math.pi, 2*math.pi); c.stroke()           # dome
    c.move_to(cx-r, cy); c.line_to(cx-r, cy+r*1.4); c.line_to(cx-r*0.4, cy+r*1.4)
    c.move_to(cx+r, cy); c.line_to(cx+r, cy+r*1.9); c.line_to(cx+r*0.4, cy+r*1.9)
    c.stroke(); c.restore()

def pin_header(c, cx, cy, n, pitch, a=1.0, rgb=WHITE, lw=3.0):
    """A row of header pins (small squares) — the gold standard breadboard motif."""
    c.save(); S(c, rgb, a); c.set_line_width(lw)
    x0 = cx - (n-1)*pitch/2
    for i in range(n):
        rrect(c, x0+i*pitch-pitch*0.18, cy-pitch*0.18, pitch*0.36, pitch*0.36, 2); c.stroke()
    c.restore()

# ── real 3D part: composite a pre-rendered STEP sprite (see SKILL "Add a 3D model") ─
def load_sprite(path):
    """Load an RGBA model render (from render3d.py) once, reuse it every frame."""
    return cairo.ImageSurface.create_from_png(path)

def draw_sprite(c, surf, cx, cy, vis_w, a=1.0, flip=False, vis=(0.5, 0.5, 1.0), pins=()):
    """Paint a pre-rendered 3D part `surf` centred at (cx,cy) so its VISIBLE model spans
    `vis_w` px — the clean way to drop a real CAD sensor into a scene instead of line-art.
    `vis`=(cx_frac, cy_frac, w_frac): the visible-model centre + width as fractions of the
    sprite (measure once — the transparent margin means you can't trust the raw image box).
    flip=True rotates it 180° (e.g. so a module stands on its pins). Returns each `pins`
    fraction (fx,fy) mapped to canvas coords so you can wire() to the actual pin tips.
    Keep cutaway/'what's inside' scenes line-art — a solid model can't show internals."""
    sw, sh = surf.get_width(), surf.get_height()
    vcx, vcy, vw = vis[0]*sw, vis[1]*sh, vis[2]*sw
    s = vis_w/vw
    c.save(); c.translate(cx, cy)
    if flip: c.rotate(math.pi)
    c.scale(s, s); c.translate(-vcx, -vcy)
    c.set_source_surface(surf, 0, 0); c.paint_with_alpha(clamp(a)); c.restore()
    sgn = -1 if flip else 1
    return [(cx+sgn*(fx*sw-vcx)*s, cy+sgn*(fy*sh-vcy)*s) for fx, fy in pins]

# ── signal / current flow along a path (works for any topic) ────────────────────
def _poly(pts):
    segs = [math.hypot(pts[i+1][0]-pts[i][0], pts[i+1][1]-pts[i][1]) for i in range(len(pts)-1)]
    return segs, sum(segs)
def _poly_pt(pts, segs, total, s):
    d = clamp(s)*total; acc = 0.0
    for i, sl in enumerate(segs):
        if acc+sl >= d or i == len(segs)-1:
            f = (d-acc)/sl if sl else 0.0
            return (pts[i][0]+(pts[i+1][0]-pts[i][0])*f, pts[i][1]+(pts[i+1][1]-pts[i][1])*f)
        acc += sl
    return pts[-1]
def wire(c, pts, rgb=WHITE, a=1.0, lw=4, dash=None, draw=1.0):
    """Draw a static path (a wire / PCB trace) through the given points.
    draw<1 strokes only the first fraction of the path's LENGTH — animate it
    (e.g. draw=ease_out(clamp(lt/0.6))) for a slick draw-on before the flow() dots."""
    d = clamp(draw)
    if d <= 0.001: return
    if d < 0.999:
        segs, total = _poly(pts)
        if total <= 0: return
        target, out, acc = total*d, [pts[0]], 0.0
        for i, sl in enumerate(segs):
            if acc+sl >= target:
                f = (target-acc)/sl if sl else 0.0
                out.append((pts[i][0]+(pts[i+1][0]-pts[i][0])*f,
                            pts[i][1]+(pts[i+1][1]-pts[i][1])*f))
                break
            out.append(pts[i+1]); acc += sl
        pts = out
    c.save(); S(c, rgb, a); c.set_line_width(lw)
    c.set_line_join(cairo.LINE_JOIN_ROUND); c.set_line_cap(cairo.LINE_CAP_ROUND)
    if dash: c.set_dash(dash)
    c.move_to(*pts[0])
    for p in pts[1:]: c.line_to(*p)
    c.stroke(); c.restore()

def ring_ping(c, cx, cy, p, r0=16, r1=80, rgb=TEAL, a=1.0, lw=4):
    """ACCENT — ONE expanding, fading ring: a 'detect' ping, a turn-on flash, a CTA
    pulse. p in [0..1] is the life of the ring (no-op outside); drive it with a
    clamp() for a one-shot or a (lt*rate)%1.0 for a repeating ping. Keep radii
    COMPACT (this replaces big translucent halos, it must not become one)."""
    p = clamp(p)
    if p <= 0.001 or p >= 0.999: return
    c.save(); S(c, rgb, a*(1.0-p)); c.set_line_width(lw*(1.0-0.45*p))
    c.new_path(); c.arc(cx, cy, r0+(r1-r0)*ease_out(p), 0, 2*math.pi); c.stroke()
    c.restore()

def scene_lift(lt, dist=26, dur=0.55):
    """Vertical settle for a scene entering: returns a +dy that starts `dist` low and
    eases to 0. Wrap a scene's art in c.save(); c.translate(0, scene_lift(lt)); ...
    c.restore() so it rises into place while scene_alpha fades it in."""
    return (1.0-ease_out(clamp(lt/dur)))*dist
def flow(c, pts, t, rgb=TEAL, a=1.0, n=5, speed=0.32, r=9, glow=True):
    """ACCENT — animated dots travelling a polyline: current, data bits, a signal.
    Pair with wire() for the trace. speed = laps/sec; dots fade near the ends."""
    segs, total = _poly(pts)
    if total <= 0: return
    for i in range(n):
        s = (t*speed + i/n) % 1.0
        x, y = _poly_pt(pts, segs, total, s)
        fade = clamp(s/0.06) * clamp((1-s)/0.06)
        if glow:
            S(c, rgb, a*fade*0.30); c.new_path(); c.arc(x, y, r*2.1, 0, 2*math.pi); c.fill()
        S(c, rgb, a*fade); c.new_path(); c.arc(x, y, r, 0, 2*math.pi); c.fill()

def roll_number(c, value, cx, cy, size, lt, dur=1.0, rgb=WHITE, suffix="", prefix="",
                decimals=0, font=DISPLAY, a=1.0, track=2):
    """ACCENT — count a number up 0 -> value over `dur`s (lt = local scene time),
    centred at (cx,cy). Reserve for the single most important spec in the video."""
    cur = value * ease_out(clamp(lt/dur))
    body = f"{cur:.{decimals}f}" if decimals else f"{int(round(cur))}"
    s = f"{prefix}{body}{suffix}"
    w = seg_w(c, s, size, font, track)
    heavy(c, s, cx - w/2, cy + size*0.36, size, rgb, font=font, a=a, track=track)
    return s

def marker(c, cx, cy, w, lt, rgb=TEAL, a=1.0, dur=0.45, thick=22):
    """ACCENT — a translucent teal highlighter swipe drawn on L->R behind a key term
    (call BEFORE the text). Highlight one key word once or twice per video."""
    p = ease_out(clamp(lt/dur))
    c.save(); S(c, rgb, a*0.40)
    c.set_line_width(thick); c.set_line_cap(cairo.LINE_CAP_ROUND)
    c.move_to(cx - w/2, cy); c.line_to(cx - w/2 + w*p, cy); c.stroke(); c.restore()

def progress_bar(c, t, a=1.0, rgb=TEAL):
    """Thin teal time-progress bar pinned to the very bottom (a tidy reels touch)."""
    p = clamp(t/DUR); c.save()
    S(c, WHITE, a*0.12); c.rectangle(0, H-8, W, 8); c.fill()
    S(c, rgb, a); c.rectangle(0, H-8, W*p, 8); c.fill(); c.restore()

# ── encode / probe ───────────────────────────────────────────────────────────────
def render(draw_frame, output, dur=None, fps=FPS, preset="medium", crf=18):
    """Pipe draw_frame(t)->ImageSurface frames to ffmpeg as a vertical mp4."""
    global DUR
    if dur is not None: DUR = dur
    nf = int(fps*DUR)
    os.makedirs(os.path.dirname(output) or ".", exist_ok=True)
    print(f"Rendering {nf} frames ({DUR}s @ {fps}fps) -> {output}")
    enc = subprocess.Popen(
        ["ffmpeg", "-y", "-f", "rawvideo", "-vcodec", "rawvideo",
         "-s", f"{W}x{H}", "-pix_fmt", "bgra", "-r", str(fps), "-i", "pipe:0",
         "-vcodec", "libx264", "-pix_fmt", "yuv420p", "-crf", str(crf),
         "-preset", preset, "-movflags", "+faststart", output],
        stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)
    for i in range(nf):
        if i % (fps*2) == 0: print(f"  {i//fps:>2}s / {int(DUR)}s")
        enc.stdin.write(bytes(draw_frame(i/fps).get_data()))
    enc.stdin.close()
    print("done" if enc.wait() == 0 else "FFMPEG FAILED")

def probe(draw_frame, times, outdir):
    """Dump still frames at given times for quick visual review."""
    os.makedirs(outdir, exist_ok=True)
    for tt in times:
        draw_frame(tt).write_to_png(f"{outdir}/probe_{tt}.png"); print("probe", tt)
