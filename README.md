# funduino — Claude-Code-Skill

Ein **Claude-Code-Skill**, der komplette vertikale Kurzvideos (1080×1920, 30 fps) im
**Funduino-Hausstil** erzeugt: deutsche Elektronik-Erklärvideos für TikTok / Reels /
Shorts, gezeichnet Bild für Bild mit **pycairo** und encodiert mit **ffmpeg**.

Der Skill kann zwei Dinge — meistens beides hintereinander:

1. **Skript schreiben** — ein kurzes deutsches Voiceover (2–4 Sätze, Du-Form) plus die
   Untertitel-Cues in Großbuchstaben.
2. **Video rendern** — der animierte Reel dazu. **Ohne eingebrannten Text**: die
   Untertitel legst du selbst in deinem Schnittprogramm drüber.

> **Kurzfassung für Eilige:** Skill nach `~/.claude/skills/funduino/` kopieren,
> `brew install cairo freetype ffmpeg`, `pip install pycairo`, dann in Claude Code
> „Mach mir eine Funduino-Folge über den HC-SR04" sagen. Alles Weitere steht unten.

---

## Inhalt

1. [Was dabei herauskommt](#1-was-dabei-herauskommt)
2. [Installation](#2-installation)
3. [Benutzung mit Claude Code](#3-benutzung-mit-claude-code)
4. [Der Arbeitsablauf im Detail](#4-der-arbeitsablauf-im-detail)
5. [Die Skript-Formel (6 Beats)](#5-die-skript-formel-6-beats)
6. [Der Look — Hausstil-Regeln](#6-der-look--hausstil-regeln)
7. [Die Engine: `funduino.py`](#7-die-engine-funduinopy)
8. [Eine neue Folge von Hand bauen](#8-eine-neue-folge-von-hand-bauen)
9. [Echte 3D-Bauteile aus STEP-Dateien](#9-echte-3d-bauteile-aus-step-dateien)
10. [Stolperfallen](#10-stolperfallen)
11. [Dateien in diesem Repo](#11-dateien-in-diesem-repo)
12. [Auf die eigene Marke umbauen](#12-auf-die-eigene-marke-umbauen)

---

## 1. Was dabei herauskommt

Ein `.mp4`, 1080×1920, 30 fps, **ohne Ton** und **ohne eingebrannte Untertitel**.
Typische Länge: 20–28 Sekunden, aufgeteilt in 5–6 Szenen.

Der Stil ist bewusst eng gefasst — das ist der Sinn eines Hausstils:

- **Eine einzige helle Leinwand** in jeder Szene: eine weiche Studiowand in Off-White
  mit Bodenschatten, so wie ein Produktfoto. Kein dunkler Hintergrund, keine Überblendung
  zwischen hell und dunkel.
- **Eine einzige Akzentfarbe: Petrol `#538b82`**, in zwei Tönen. Keine zweite Farbe.
- **Line-Art**: Boards, Sensoren, Kabel als dünne Linien gezeichnet — oder ein echtes
  3D-Bauteil, gerendert aus einer STEP-Datei.
- **Viel Weißraum.** Die Grafik ist absichtlich klein (60 % Skalierung), damit unten
  Platz für deine Untertitel bleibt.
- **Kein Logo, kein Schriftzug** im Bild.

Parallel entsteht ein Textblock mit dem gesprochenen Voiceover und den Untertitel-Cues,
den du selbst einsprichst (oder durch eine TTS jagst) und als Untertitel überlagerst.

---

## 2. Installation

### 2.1 Den Skill installieren

Claude Code lädt Skills aus `~/.claude/skills/<name>/`. Der Ordnername muss zum
`name:` im Frontmatter von `SKILL.md` passen — also **`funduino`**, nicht
`funduino-skill`:

```bash
git clone https://github.com/sparklabhqx/funduino-skill.git ~/.claude/skills/funduino
```

Oder, wenn du das Repo schon woanders liegen hast:

```bash
mkdir -p ~/.claude/skills
cp -R /pfad/zu/funduino-skill ~/.claude/skills/funduino
```

Danach Claude Code neu starten. Der Skill taucht als `/funduino` in der Skill-Liste auf.

### 2.2 Abhängigkeiten

Für das Rendern der Videos:

```bash
# macOS
brew install cairo freetype ffmpeg
python3 -m pip install pycairo       # alternativ: brew install py3cairo

# Debian / Ubuntu
sudo apt install libcairo2 libcairo2-dev libfreetype6 ffmpeg python3-pip
python3 -m pip install pycairo
```

Prüfen, ob es sitzt:

```bash
python3 -c "import cairo; print(cairo.version)"
ffmpeg -version | head -1
```

### 2.3 Schriften

Out of the box nutzt die Engine **macOS-Systemschriften** (Arial Rounded Bold, Arial
Bold Italic, Arial Bold) — auf einem Mac musst du also nichts installieren.

Auf Linux, oder wenn du näher an den Funduino-Look willst, installier eine runde
geometrische Schrift (Poppins, Quicksand, Baloo 2) und zeig der Engine per
Umgebungsvariable den **Dateipfad**:

```bash
export FUNDUINO_FONT_DISPLAY=/pfad/Poppins-Bold.ttf
export FUNDUINO_FONT_ITALIC=/pfad/Poppins-BoldItalic.ttf
export FUNDUINO_FONT_BODY=/pfad/Poppins-SemiBold.ttf
```

Die Schriften werden bewusst **per Dateipfad über FreeType** geladen, nie über
fontconfig — fontconfig löst Display-Schnitte still und heimlich falsch auf und du
bekommst dann klammheimlich die falsche Schrift ins Video gerendert.

### 2.4 Optional: 3D-Rendering

Nur nötig, wenn du echte Bauteile aus STEP-Dateien rendern willst (siehe
[Abschnitt 9](#9-echte-3d-bauteile-aus-step-dateien)). Das braucht ein **eigenes venv**,
getrennt vom System-Python:

```bash
python3 -m venv ~/.venvs/funduino3d
~/.venvs/funduino3d/bin/pip install cascadio trimesh numpy pillow
```

> **Wichtig auf dem Mac:** Leg dieses venv **nicht** in einen iCloud-synchronisierten
> Ordner (also nicht unter `~/Documents` oder `~/Desktop`). iCloud lagert die Dateien
> aus, und dann hängt jeder Aufruf bei 0 % CPU, ohne Fehlermeldung.

---

## 3. Benutzung mit Claude Code

Der Skill greift automatisch, wenn du so etwas sagst:

- „Mach mir eine Funduino-Folge über den HC-SR04 Ultraschallsensor."
- „Schreib nur das Skript für eine Folge über Pull-up-Widerstände."
- „Noch eine Funduino-Episode, diesmal über den DHT11."
- `/funduino Fotowiderstand`

Du kannst auch explizit nur einen der beiden Teile anfordern:

| Was du willst | Was du sagst |
|---|---|
| Nur den Text | „Nur das Skript, noch kein Video." |
| Nur das Video zu einem fertigen Text | „Hier ist mein Skript — bau das Video dazu." |
| Beides | „Folge über X" (Standard) |

### Das Umschreib-Gate

Der Skill zeigt dir **immer zuerst den Voiceover-Entwurf** und wartet, bis du ihn
umschreibst oder freigibst. Erst danach rendert er. Das ist Absicht: Du sprichst die
Reels selbst ein, also muss die Formulierung deine sein. Rendere nie auf Basis des
ersten KI-Entwurfs — die Szenenlängen hängen an den Textblöcken, und wenn der Text
sich danach ändert, musst du alles neu timen.

---

## 4. Der Arbeitsablauf im Detail

```
 1. Thema wählen
       ↓
 2. Skript schreiben (6 Beats)  ──→  DIR ZEIGEN, du schreibst um  ←── Pflicht-Gate
       ↓
 3. Untertitel-Cues neu aufteilen, passend zu deinem Text
       ↓
 4. Episoden-Datei bauen (Szenen in draw_frame)
       ↓
 5. python3 <thema>.py probe   →  ein Standbild pro Szene in out/
       ↓
 6. Die PNGs ansehen und prüfen  ←── Pflicht, jedes Mal
       ↓
 7. python3 <thema>.py          →  das fertige mp4
       ↓
 8. Du: Voiceover aufnehmen, Untertitel drüberlegen, schneiden
```

### Was beim Prüfen in Schritt 6 zu kontrollieren ist

- **Das untere Fünftel ist leer** (ab ca. `y = H*0.78`). Da kommen deine Untertitel hin.
- **Genau ein Blickfang pro Szene.** Nicht zwei gleich große Objekte.
- **Nichts ist ausgewaschen.** Jeder Strich braucht eine Farbrolle; ein vergessenes
  `rgb=` rendert weiß auf hellem Grund — also unsichtbar.
- **Nichts überlappt**, Beschriftungen bleiben über der Untertitel-Zone.
- **Kurze Ereignisse extra prüfen.** Ein Probe-Bild aus der Szenenmitte verpasst einen
  einmaligen Moment (ein Kontakt schließt, ein Trigger feuert) komplett. Rechne aus,
  in welchen Frames das Ereignis liegt, und probe gezielt diese Zeitpunkte.

Einzelbilder aus einem fertigen Video ziehen:

```bash
ffmpeg -i out/thema.mp4 -vf fps=1 /tmp/f_%02d.png
```

---

## 5. Die Skript-Formel (6 Beats)

Jede Folge ist ein **20–28 Sekunden langes deutsches Voiceover**, zerlegt in kurze
Untertitel-Cues zu je 2–4 Wörtern. Der Ton ist locker, **Du-Form**, freundlich-nerdig —
als würdest du einem Kumpel ein Bauteil erklären. Kein Füllmaterial, kein „in diesem
Video". Der Haken sitzt in den ersten 1,5 Sekunden.

| # | Beat | Aufgabe | Länge |
|---|---|---|---|
| 1 | **HOOK** | Benenne es in einem Satz. „Das ist ein …" | ~2 s |
| 2 | **EINORDNUNG** | Verorte es gegen etwas Bekanntes. „Kein X, aber …" | ~3 s |
| 3 | **KERN** | Der eine Mechanismus. Der Lehrmoment. | ~6 s |
| 4 | **DETAIL** | Eine konkrete Zahl oder ein zweiter Fakt (kHz, V, Ω) | ~4 s |
| 5 | **PROJEKT** | Was du damit wirklich bauen kannst — die Belohnung | ~5 s |
| 6 | **CTA** | Immer derselbe Satz (siehe unten) | ~3 s |

Für eine sehr kurze Folge darfst du Beat 2 oder 5 streichen. Die anderen nicht.

### Untertitel-Cues

- **GROSSBUCHSTABEN**, 2–4 Wörter pro Block, ein Block pro Szene.
- **Genau ein Schlüsselwort** pro Block in `*Sternchen*` — das ist das Wort, das du in
  deinen eigenen Untertiteln petrol einfärben kannst. Nimm das bedeutungstragende Wort.
- Umlaute und ß richtig schreiben (Ä Ö Ü ß).
- Die Blöcke sind der gesprochene Satz, an natürlichen Pausen getrennt — hintereinander
  gelesen ergeben sie wieder den vollen Text.

### Sprachregeln (nicht verhandelbar)

- **Niemals das Wort „Arduino".** Sag **„UNO"** oder **„UNO board"** für das Board und
  **„Mikrocontroller"** für den Chip allgemein — im Voiceover, in den Cues *und* in den
  Beschriftungen in der Grafik.
- **Der Call-to-Action ist fix.** Beat 6 lautet immer wörtlich:
  - Voiceover: „Wenn du mehr über Elektronik lernen willst, dann abonniere unseren Kanal!"
  - Cue: `ABONNIERE UNSEREN *KANAL*`
  - Nie ein Website-CTA.
- **Halte das Leseniveau niedrig.** Ein Gedanke pro Satz, kurze Hauptsätze. Stapel nicht
  Nebensatz, Doppelpunkt und Anführungszeichen in eine Zeile. Tausch harte Komposita
  gegen Alltagswörter: `Sekundenbruchteil` → `ganz kurz`, `Erschütterung` → `Stoß`,
  `wie empfindlich er sein soll` → `wie viel er merken soll`. Lieber das zweite Beispiel
  streichen als einen Beat verlängern. Der CTA ist der einzige Satz, der einen Nebensatz
  haben darf.
- **Prüf auch die Grafik.** Eine Beschriftung wie `ERSCHÜTTERUNGEN` holt genau das harte
  Wort zurück, das du gerade aus dem Text geworfen hast.

### Ausgefülltes Beispiel (die Pico-Folge)

```
TITEL:  Der Raspberry Pi Pico
DAUER:  24 s

VOICEOVER:
  Das ist der Raspberry Pi Pico — ein kleiner Mikrocontroller.
  Kein ESP32, aber viel einfacher aufgebaut.
  Im Herzen sitzt der RP2040-Chip: er startet deinen Code sofort, ganz ohne Betriebssystem.
  Du programmierst ihn in C oder MicroPython.
  Damit steuerst du Sensoren, Displays oder LEDs an — zum Beispiel eine LED, die auf Musik reagiert.
  Wenn du mehr über Elektronik lernen willst, dann abonniere unseren Kanal!

UNTERTITEL-CUES:
  S1  "DER RASPBERRY PI *PICO*"
  S2  "EIN KLEINER *MIKROCONTROLLER*"
  S3  "STARTET DEINEN *CODE* SOFORT"
  S4  "EINE LED DIE AUF *MUSIK* REAGIERT"
  S5  "BOARD FÜR SCHNELLE *DIY*-IDEEN"
  S6  "ABONNIERE UNSEREN *KANAL*"
```

Die vollständige Vorlage liegt in [`assets/SCRIPT_TEMPLATE.md`](assets/SCRIPT_TEMPLATE.md).

---

## 6. Der Look — Hausstil-Regeln

Das sind keine Geschmacksfragen, sondern Korrekturen aus echten Durchläufen. Wer sie
überspringt, macht genau den Fehler, den sie verhindern sollen.

### 6.1 Die neun harten Regeln

1. **Erst das Skript freigeben lassen**, dann bauen und rendern.
2. **Kein Logo, kein Schriftzug** — `funduino_logo()` in keiner Szene aufrufen.
3. **Keine eingebrannten Untertitel** — `caption()` nie aufrufen. Das untere Fünftel
   (`y ≳ H*0.78`) bleibt leer. Die Cues schreibst du trotzdem — als Textdatei für dich.
4. **Nie das Wort „Arduino"** — weder im Text noch in den Grafik-Beschriftungen.
5. **Fixer CTA** am Ende, immer derselbe Satz.
6. **Echte Schaltungen zeichnen.** Ein analoger 2-Pin-Sensor ist ein Spannungsteiler:
   5 V → Sensor → Knoten → Pulldown-Widerstand → GND, Knoten → Analogpin. **Alle** Pins
   anschließen. Kabel landen auf **Header-Pins**, nie auf der USB-Buchse — dreh das Board
   um 90°, wenn die Buchse zur Verkabelung zeigt.
7. **Kleine, saubere Grafik.** `CONTENT_SCALE = 0.60`, nicht 0.75–0.86. Kompakte
   Leuchteffekte, keine großen durchscheinenden Schleier. Ein Lichtstrahl endet **an**
   der Oberfläche des Ziels, nie dahinter.
8. **Die Leinwand ist in jeder Szene hell.** `make_background_light()` durchgehend, kein
   dunkler Hintergrund, keine Überblendung. Jedem Strich eine Farbrolle geben.
   „Aktiv" heißt **dunkler und dicker**, niemals heller. `flow()` braucht `glow=False`.
9. **Jedes Mal visuell prüfen** — die Probe-PNGs wirklich ansehen.

### 6.2 Farbrollen

Die Engine-Defaults stammen noch von der alten dunklen Leinwand und sind `WHITE`. Ein
weggelassenes `rgb=` rendert damit **unsichtbar** auf dem hellen Grund. Übergib deshalb
jedem Zeichenaufruf eine Rolle:

| Rolle | Wert | Wofür |
|---|---|---|
| `LINE` | `TEAL_D` | Struktur-Line-Art — Boards, Kabel, Umrisse, Schnittansichten |
| `ACC` | `TEAL` | Akzente: Strom-Punkte, Pings, Callout-Ringe, Füllungen |
| `LABEL` | `TEAL_D` | Die primäre, betonte Beschriftung; Hero-Zahlen |
| `MUTED` | `TEAL` | Sekundäre Beschriftungen (Pin-Namen, Einheiten) |
| `GHOST` | `DARK` | Inaktive Grafik, immer mit niedriger Deckkraft (~0,3) |

Ausnahme: `block()` braucht nichts — eine gefüllte Petrol-Karte mit weißer Schrift liest
sich auf jedem Untergrund.

Rohe Palette: `TEAL TEAL_D TEAL_L PAPER DARK INK WHITE SMOKE BLACK`. Davon sind
`WHITE`, `SMOKE` und `INK` Altlasten der dunklen Leinwand; auf hell benutzt du direkt
nur noch `BLACK` (Kontaktschatten) und `PAPER`.

### 6.3 Bewegung

- Hereinfahren mit leichtem Überschwingen (`enter()`, `ease_back`), sanftes Wippen.
- Strom/Signal als Punkte auf einer Leitung (`flow()` auf `wire()`): erst die Leitung
  zeichnen lassen (`wire(draw=…)`, pro Kabel versetzt), **dann** die Punkte starten.
- Szenenwechsel über ein Abtauchen in den Hintergrund (`scene_alpha()`), jede Szene
  setzt sich mit `scene_lift()` klein nach.
- Line-Art-Objekte zeichnen sich über einen Clip-Wisch auf; Fächer und Bögen **wachsen**
  nach außen (Radius bzw. Winkel animieren); die Hero-Zahl kommt mit `pop_scale()` rein
  und zählt dabei hoch.
- `ring_ping()` markiert die Story-Momente (Erkennungs-Ping, Einschalt-Blitz,
  CTA-Puls). Auf hell mit `LINE` und `lw=6`, sonst verschwindet er beim Ausblenden.
- Auf der Titelkarte: `pop_scale()`-Auftritt plus Mikro-Schwingen über einem kleinen
  Kontaktschatten (`BLACK` bei ~0,14), der das Wippen beantwortet.

---

## 7. Die Engine: `funduino.py`

Alles Wiederverwendbare steckt in `assets/funduino.py` (Canvas 1080×1920, 30 fps).

### Leinwand und Rahmen

| Funktion | Zweck |
|---|---|
| `make_background_light()` | **Die** Leinwand. Einmal bauen, jeden Frame zeichnen. |
| `make_background_dark()` | Altlast — nur für archivierte alte Folgen, nie für eine neue. |
| `render(draw_frame, output, dur)` | Rendert das mp4 (libx264, crf 18). |
| `probe(draw_frame, times, outdir)` | Ein Standbild pro Zeitpunkt als PNG. |

### Bauteile

| Funktion | Zweck |
|---|---|
| `board_icon(c, cx, cy, w, …)` | Line-Art-Board (z. B. ein UNO). Kein Logo — nur eine Platinenform. |
| `chip(c, cx, cy, w, …, pins=, label=)` | IC / Modul |
| `led(c, cx, cy, r, …, glow=0..1)` | LED; `glow` leuchtet die Kuppel **von innen** aus |
| `pin_header(c, cx, cy, n, pitch, …)` | Stiftleiste |
| `wire(c, pts, …, draw=)` | Leiterbahn; `draw < 1` zeichnet nur den ersten Teil der Länge |
| `flow(c, pts, t, …, glow=False)` | Punkte, die auf der Leitung wandern (Strom / Daten) |
| `marker(…)` | Durchscheinender Petrol-Textmarker hinter einem Begriff |
| `progress_bar(c, t)` | Dünner Fortschrittsbalken |

### Text

| Funktion | Zweck |
|---|---|
| `block(c, text, cx, cy, size, blk=, txt=)` | Kräftiger Text auf abgerundeter Karte |
| `text(…)` | Normale Beschriftung |
| `heavy(…)` | Roher Display-Text |
| `roll_number(value, …, suffix=)` | Zahl von 0 hochzählen — **eine** Hero-Zahl pro Video |
| `caption(…)` | **Veraltet — nicht aufrufen.** Videos bekommen keinen eingebrannten Text. |
| `funduino_logo(…)` | **Veraltet — nicht aufrufen.** Kein Logo im Bild. |

### Animation und Timing

| Funktion | Zweck |
|---|---|
| `scene_alpha(t, t0, t1)` | Deckkraft einer Szene inkl. Ein-/Ausblenden |
| `scene_lift(lt)` | Kleines vertikales Setzen beim Szeneneinstieg |
| `enter(lt, delay)` | Liefert `(alpha, dx)` für ein Element, das hereinfährt |
| `ring_ping(c, cx, cy, p, r0=, r1=)` | Ein expandierender, verblassender Ring |
| `ease_out`, `ease_back`, `ease_in_out`, `pop_scale`, `clamp` | Kurven-Helfer |

### 3D-Sprites

| Funktion | Zweck |
|---|---|
| `load_sprite(path)` | PNG mit Transparenz laden (aus `render3d.py`) |
| `draw_sprite(c, surf, cx, cy, vis_w, flip=, vis=, pins=)` | Sprite setzen; gibt die Pin-Spitzen in Leinwand-Koordinaten zurück |

---

## 8. Eine neue Folge von Hand bauen

Du brauchst Claude Code dafür nicht zwingend — die Engine ist ein normales Python-Modul.

### Schritt 1 — Projektordner anlegen

```bash
mkdir -p ~/Documents/Funduino_Video_GEN
cp ~/.claude/skills/funduino/assets/funduino.py     ~/Documents/Funduino_Video_GEN/
cp ~/.claude/skills/funduino/assets/example_pico.py ~/Documents/Funduino_Video_GEN/ultraschall.py
```

Die Episoden-Datei hängt ihren eigenen Ordner an `sys.path` und leitet alle Pfade aus
ihrem eigenen Ort ab — ein Projekt ist also in sich geschlossen und verschiebbar.

### Schritt 2 — CONFIG anpassen

```python
PROJECT = os.path.dirname(os.path.abspath(__file__))
OUTPUT  = f"{PROJECT}/out/ultraschall.mp4"
fn.DUR  = 24.0                  # Gesamtlänge in Sekunden

BG_LIGHT = make_background_light()
CAP_Y    = int(H*0.80)          # diese Zone bleibt LEER
HERO_Y   = int(H*0.42)
CONTENT_SCALE = 0.60            # NICHT hochdrehen
```

### Schritt 3 — Szenen schreiben

Struktur behalten, Inhalte austauschen:

- **Szene 1** — nur der Held (Board, Chip oder 3D-Sprite). Kein Logo, kein Text unten.
- **Szenen 2 … N-1** — je ein Held, optional eine `block()`-Beschriftung **oben** im
  Heldenbereich, `flow()` für Strom/Signal, `led(glow=…)` oder `roll_number()` für einen
  Kennwert.
- **Szene N** — CTA-Grafik (z. B. ein Petrol-Abo-Button). Kein Logo, kein Text unten.

Alle Szenen sitzen auf **derselben** hellen Leinwand; die Trennung entsteht durch die
`scene_alpha()`-Abtaucher und `scene_lift()`, nicht durch einen Hintergrundwechsel.

```python
# SZENE 3 — startet den Code sofort, kein Betriebssystem
if 8.4 < t < 13.6:
    a = scene_alpha(t, 8.6, 13.2); lt = t - 8.6
    chip(c, W/2, HERO_Y, w=300, a=a, rgb=LINE, lw=5, pins=4, label="RP2040")
    path = [(150, HERO_Y), (W/2-170, HERO_Y)]
    wire(c, path, rgb=LINE, a=a*0.55, lw=4)
    flow(c, path, lt, rgb=ACC, a=a, n=4, speed=0.6, r=10, glow=False)
    ab, dxb = enter(lt, 0.1)
    block(c, "KEIN BETRIEBSSYSTEM", W/2 - dxb, HERO_Y+260, 50, blk=TEAL_D, a=a*ab)
    # Untertitel (legst du selbst drüber): "STARTET DEINEN *CODE* SOFORT"
```

Zwei Dinge, die in **jedem** Zeichenaufruf stehen müssen:

- die Szenen-Deckkraft `a` — sonst blendet das Element bei den Übergängen nicht mit aus;
- eine Farbrolle `rgb=` — sonst ist es weiß auf weiß.

Den Untertitel-Cue lässt du als `# Kommentar` in der Szene stehen. Er wird nicht
gezeichnet, aber so steht beim Schneiden dran, was an dieser Stelle eingeblendet gehört.

### Schritt 4 — Prüfen und rendern

```bash
cd ~/Documents/Funduino_Video_GEN
python3 ultraschall.py probe     # ein Standbild pro Szene nach out/
python3 ultraschall.py           # das fertige mp4
```

Die Probe-Zeitpunkte stehen unten in der Datei — setz sie auf die Mitte jeder Szene
(und zusätzlich auf kurze Einzelereignisse):

```python
if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "probe":
        probe(draw_frame, (1.8, 6.4, 10.8, 15.4, 21.0), f"{PROJECT}/out")
    else:
        fn.render(draw_frame, OUTPUT, dur=fn.DUR)
```

---

## 9. Echte 3D-Bauteile aus STEP-Dateien

Wenn du eine CAD-Datei des Bauteils hast (oder die Line-Art zu blass wirkt), kannst du
das **echte Bauteil** rendern und einsetzen. `assets/render3d.py` ist ein reiner
CPU-Renderer STEP → glb → Bild, ohne Blender und ohne GPU.

Das gilt nur für Szenen mit massiven Objekten. Eine Schnittansicht („was ist da drin")
bleibt Line-Art — ein Volumenmodell kann nun mal kein Innenleben zeigen. Und wenn du den
Sensor in einer Szene austauschst, tausch ihn in **allen** Massiv-Szenen aus, sonst
springt das Video.

```bash
V=~/.venvs/funduino3d/bin/python

# 1) Winkel suchen: rendert ein Raster verschiedener Ansichten
$V render3d.py --step teil.step --glb model/m.glb --mode grid
#    → ang_*.png ansehen, einen Yaw wählen, der Bauteil UND Pins zeigt

# 2) Das Hero-Bild rendern (transparentes RGBA-PNG)
$V render3d.py --glb model/m.glb --mode hero --out model/hero.png \
     --yaw 26 --pitch 24 --res 1500 --down 1000
```

**Danach einmal ausmessen** — das Sprite hat transparenten Rand, die rohe Bildbox ist
also falsch:

- PNG laden, Bounding-Box der deckenden Pixel nehmen → `vis=(cx_frac, cy_frac, w_frac)`.
- Die deckenden Spalten im oberen Bereich clustern → die Pin-Spitzen als Bruchteile.
- Beide Werte fest in die Episode schreiben. Sie sind auflösungsunabhängig.

In der Episode:

```python
SPR = load_sprite(f"{PROJECT}/model/hero.png")

pins = draw_sprite(c, SPR, W/2, HERO_Y, vis_w=460, a=a,
                   flip=True,                     # 180° — Modul steht auf seinen Pins
                   vis=(0.50, 0.48, 0.86),        # gemessen
                   pins=[(0.32, 0.12), (0.50, 0.12), (0.68, 0.12)])
# pins zurück in Leinwand-Koordinaten → direkt als wire()-Endpunkte benutzen
```

Verdrahte **jeden** Pin des Moduls zum Ziel, nicht nur einen. Bei einem blanken
analogen 2-Pin-Sensor (LDR, NTC, FSR) zeichnest du den echten **Spannungsteiler**:
5 V → Sensor → Knoten → Pulldown-Widerstand → GND, und vom Knoten zum Analogpin.

### Farben aus dem STEP retten

STEP-Farben überleben die glb-Konvertierung oft (SolidWorks-Exporte tun das). Dann
match nicht die Geometrie, um umzufärben, sondern den exakten Material-`baseColorFactor`
in einem kleinen `load_world`-Wrapper. Typische Korrekturen: ein braun-schwarz
ankommendes WROOM-Schild → Silber (215, 218, 222); eine lila USB-Hülse → neutrales
Silber; eine reinschwarze Platine auf (26, 28, 32) anheben, damit sich ihre Flächen noch
voneinander trennen.

Sprites müssen für die helle Leinwand **nicht** umgefärbt werden — ein echtes Bauteil
bringt seine eigenen Materialfarben mit und ist damit das einzige Element, das der
Hausstil nicht anfasst. Trotzdem die Probe ansehen: ein fast weißes Bauteil oder eine
helle Platine verliert vor dem hellen Hintergrund die Kante. Dann mit dunklerem
Lötstopplack neu rendern (`--pcb`).

### Line-Art nachträglich durch ein Sprite ersetzen

- Die gemessene `vis`-Box enthält auch die herausstehenden Header-Pins, die Platine
  darin ist also kleiner als das alte Line-Art-Board. Setz `vis_w` auf die alte
  Line-Art-Breite **× ~1,1**, dann behält die Platine ihre Größe und die vorhandenen
  Kabelenden landen weiter auf der Header-Kante.
- Verdrahte nur dort, wo Pins im Render wirklich **sichtbar** sind: ein Modul verdeckt
  seine Seite der Stiftleiste schon mal komplett. Dann verschiebst du den Ankerpunkt zu
  den sichtbaren Ringen, statt die alte Koordinate zu behalten.
- Überlagerte Markierungen (ein Riss, ein Ping-Ziel) brauchen die **hellen** Flächen des
  Sprites — ein dunkelpetrol Strich verschwindet auf einer schwarzen Platine.
- Liegendes Board: `draw_sprite` in `translate / rotate(-π/2) / translate` einpacken.
  Ein andockender USB-Stecker muss den **echten** Anschluss treffen und muss eventuell
  gespiegelt werden (`scale(-1, 1)`), damit die Metallhülse zum Bauteil zeigt.

---

## 10. Stolperfallen

**„Aktiv" darf nicht „heller" heißen.** Das ist die große Falle der hellen Leinwand. Auf
dem alten dunklen Hintergrund ging ein aktives Element von Weiß nach Petrol, also nach
*heller*. Färbt man das naiv für hell um, dreht es sich um: Mittel-Petrol auf Off-White
hat **weniger** Kontrast als Dunkel-Petrol — das aktive Element tritt also zurück und der
Story-Moment verpufft. Auf hell wird ein aktivierendes Element **dunkler und dicker**:
volle Deckkraft `LINE` bei ~1,6-facher Linienbreite, während die ruhenden Striche bei
~0,78 Deckkraft und 0,85-facher Breite bleiben, dazu ein gefüllter `LINE`-Punkt und ein
`ring_ping`. Bei Balken und Diagrammen arbeitest du stattdessen mit Farbe gegen Grau: der
auslösende Balken ist `LABEL`, die ruhigen sind `GHOST` bei ~0,3 Deckkraft — das
*Erscheinen von Farbe* ist dann das Signal.

**`flow()` braucht `glow=False`.** Der Glow-Durchgang malt hinter jedem Punkt eine
Scheibe mit `r*2,1` bei 0,30 Deckkraft. Auf Anthrazit unsichtbar, auf Off-White ein
blasser grüner Schmier — genau der große durchscheinende Schleier, den dieser Stil
verbietet. Glow aus; und wenn die Punkte vorher absichtlich gedimmt waren, ihre
Deckkraft um ~0,1 anheben, um die verlorene Masse auszugleichen.

**Leuchteffekte kompakt halten.** Eine große durchscheinende Scheibe hinter einem Symbol
(Sonne, LED) blutet in den Text daneben. Gib jedem Symbol Luft; ein enger Ring mit
kurzen Strahlen liest sich sauberer.

**Ein Lichtstrahl endet an der Oberfläche.** Er geht nicht durch das Bauteil hindurch —
lass die Welle an der zugewandten Kante auslaufen (Amplitude dort auf 0).

**Mechanismen als Mini-Geschichte erzählen, nicht als Ingenieursdiagramm.** Eine Person,
die durch zwei beschriftete Erfassungsfelder läuft — Füllung und Beschriftung wachen auf,
solange die Wärme drin ist, Blitz plus `ring_ping` beim Auslösen — schlägt jede abstrakte
Differenzkurve. Wenn eine Szene ein Oszilloskop braucht, um Sinn zu ergeben, inszenier
sie neu mit dem Ding, das tatsächlich handelt.

**Der richtige Python-Interpreter.** Episoden und `funduino.py` laufen mit dem
**System-Python3** (der pycairo hat). Das separate 3D-venv ist **nur** für
`render3d.py`. Niemals mischen.

**Nicht gegen die Skalierung ankämpfen.** Wenn eine Szene bei 0.60 leer wirkt — das ist
der Hausstil. Vergrößere die Grafik nicht als Ausgleich. Die Leere ist genau der Platz,
in den die Untertitel und der Blick gehen.

---

## 11. Dateien in diesem Repo

```
SKILL.md                    Die Anweisungen, die Claude Code lädt (Hausstil, Regeln, Workflow)
README.md                   Diese Anleitung
assets/
  funduino.py               Die Engine: Palette, Leinwand, Bauteile, Animation, Renderer (525 Zeilen)
  example_pico.py           Vollständige Beispielfolge — kopieren als Start für ein neues Thema
  SCRIPT_TEMPLATE.md        Die 6-Beat-Skriptformel + ausgefülltes Beispiel
  render3d.py               STEP → glb → PNG-Renderer für echte 3D-Bauteile (reine CPU)
```

`SKILL.md` ist für das Modell geschrieben, `README.md` für dich. Inhaltlich decken sie
dasselbe ab — wenn du eine Regel änderst, ändere sie in beiden.

---

## 12. Auf die eigene Marke umbauen

Der Stil steckt an wenigen Stellen, du musst die Engine nicht anfassen:

| Was | Wo |
|---|---|
| Akzentfarbe | `TEAL`, `TEAL_D`, `TEAL_L` oben in `funduino.py` |
| Hintergrund | `make_background_light()` in `funduino.py` |
| Schriften | Die drei `FUNDUINO_FONT_*`-Umgebungsvariablen |
| Sprache, CTA, Tonfall | `SKILL.md` und `assets/SCRIPT_TEMPLATE.md` |
| Format / Framerate | `W`, `H`, `FPS` in `funduino.py` |

Wenn du mehrere Marken parallel fährst, kopier den ganzen Skill-Ordner unter neuem Namen
nach `~/.claude/skills/<marke>/` und pass `name:` und `description:` im Frontmatter von
`SKILL.md` an. Die `description:` ist das, woran Claude Code entscheidet, wann der Skill
greift — schreib dort klar hinein, wodurch sich deine Marke von den anderen unterscheidet,
sonst erwischt du im Zweifel den falschen Skill.
