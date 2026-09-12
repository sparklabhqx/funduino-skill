# Funduino script formula

Every Funduino reel is a **20–28 s German voiceover** cut into **short ALL-CAPS subtitle
cues** (2–4 words each), with **one keyword per chunk** you may emphasise. The voice is
casual, "du"-form, friendly-nerdy — like explaining a part to a mate. No filler, no
"in diesem Video". Hook in the first 1.5 s, end on the fixed subscribe CTA. These chunks
are SUBTITLE CUES the user overlays themselves — the rendered video has no on-screen text.

This formula is reverse-engineered from the real reels (Pico, LED, Widerstand,
Piezo, Ultraschall, CAN-Bus, …). Follow the **6 beats** — most episodes use all six;
drop beat 2 or 5 for a very short one.

| # | Beat | Job | Length |
|---|------|-----|--------|
| 1 | **HOOK / WAS IST DAS** | Name it in one line. "Das ist ein …" / "Ein …" | ~2 s |
| 2 | **EINORDNUNG** | Position vs. something known. "Kein X, aber …" / "Ähnlich wie …, nur …" | ~3 s |
| 3 | **KERN / WIE FUNKTIONIERT'S** | The one mechanism or key fact. The teaching moment. | ~6 s |
| 4 | **DETAIL / SPEC** | A concrete number or second fact (kHz, V, Ω, „kein Betriebssystem") | ~4 s |
| 5 | **WOFÜR / PROJEKT** | A real thing you can build with it (the payoff) | ~5 s |
| 6 | **CTA** (fixed) | **Always** end on: „Wenn du mehr über Elektronik lernen willst, dann abonniere unseren Kanal!" | ~3 s |

## Subtitle cues (you write them; the user overlays them — nothing is burned in)

- **ALL CAPS**, 2–4 words per chunk, one chunk per scene/beat.
- Exactly **one keyword per chunk** wrapped in `*asterisks*` — marks the word the user
  may style teal in their own subtitles. Pick the word that carries the meaning (the
  noun, the number, the verb that matters).
- Chunks are the spoken line **broken at natural pauses** — read in order they form
  the full sentences. Keep each chunk short (one comfortable subtitle line).
- German umlauts/ß are fine — write them properly (Ä Ö Ü ß).

## Brand language (every episode — non-negotiable)

- **Never the word „Arduino".** Use **„UNO board"** / **„UNO"** for the board, or
  **„Mikrocontroller"** for the generic chip — in the VO *and* the captions/labels.
- **The CTA is fixed.** Beat 6 is always the same line, never a website CTA:
  - VO: „Wenn du mehr über Elektronik lernen willst, dann abonniere unseren Kanal!"
  - caption: `ABONNIERE UNSEREN *KANAL*`

## Fill-in template

```
TITLE:   <topic, e.g. "Der HC-SR04 Ultraschallsensor">
DUR:     <22–26> s
VO (the full spoken script, 2–4 sentences, du-form German):
  <1 HOOK sentence> <2 EINORDNUNG> <3 KERN> <4 DETAIL> <5 PROJEKT> <6 CTA>

SUBTITLE CUES (chunked, one *keyword* each, in playback order — user overlays; engine draws nothing):
  S1 (light/title):  "<HOOK chunk>"            e.g.  "DAS IST EIN *ULTRASCHALL*"
  S2 (dark):         "<EINORDNUNG chunk>"      e.g.  "WIE DEINE *FLEDERMAUS*"
  S3 (dark):         "<KERN chunk>"            e.g.  "ER SENDET EINEN *PULS*"
  S4 (dark):         "<DETAIL chunk>"          e.g.  "40 *KHZ* — ZU HOCH FÜRS OHR"
  S5 (dark):         "<PROJEKT chunk>"         e.g.  "MISST *ABSTAND* AUF DEN MM"
  S6 (light/outro):  "ABONNIERE UNSEREN *KANAL*"      (fixed CTA — always exactly this)
```

## Worked example (the Pico reel, transcribed from the original)

```
TITLE:  Der Raspberry Pi Pico
DUR:    24 s
VO:
  Das ist der Raspberry Pi Pico — ein kleiner Mikrocontroller.
  Kein ESP32, aber viel einfacher aufgebaut.
  Im Herzen sitzt der RP2040-Chip: er startet deinen Code sofort, ganz ohne Betriebssystem.
  Du programmierst ihn in C oder MicroPython.
  Damit steuerst du Sensoren, Displays oder LEDs an — zum Beispiel eine LED, die auf Musik reagiert.
  Wenn du mehr über Elektronik lernen willst, dann abonniere unseren Kanal!

SUBTITLE CUES:
  S1  "DER RASPBERRY PI *PICO*"
  S2  "EIN KLEINER\n*MIKROCONTROLLER*"
  S3  "STARTET DEINEN *CODE* SOFORT"   +block "KEIN BETRIEBSSYSTEM"
  S4  "EINE LED DIE AUF *MUSIK* REAGIERT"
  S5  "BOARD FÜR SCHNELLE *DIY*-IDEEN"
  S6  "ABONNIERE UNSEREN *KANAL*"
```

When the user asks for "just the script", deliver the **VO + SUBTITLE CUES** block above.
When they want the video too, map S1→Scene 1 … S6→Scene N for **timing only** — the
engine renders no text. The cues are what the user overlays as subtitles afterwards; the
VO is what they record (or feed to TTS).
