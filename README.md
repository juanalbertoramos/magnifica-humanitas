# Magnifica Humanitas — Reader's Edition

A single-file, offline, study-ready HTML reader for Pope Leo XIV's first
encyclical, *Magnifica Humanitas* (15 May 2026, "On Safeguarding the
Human Person in the Time of Artificial Intelligence").

**Read it:** <https://juanalbertoramos.github.io/magnifica-humanitas/>

The reader is one HTML file. Open it in a browser, or download it and
double-click to read fully offline. No server, no build step, no
network dependency once loaded.

## Features

- The complete official English text (245 paragraphs, 224 footnotes) embedded.
- Three themes — ivory (white-and-gold), sepia, night.
- Footnote popovers, full-text search, scrollspy table of contents,
  resume-where-you-left-off.
- Private notes, highlights and bookmarks (stored in your browser's
  localStorage; never leaves your device).
- Markdown export of your notes; JSON backup / import.
- Read-aloud via the browser's Web Speech API. If a narrated MP3 is
  ever dropped at `audio/magnifica-narration.mp3`, the reader picks it
  up automatically.
- Keyboard navigation: `t` TOC · `/` search · `n` notes · `l` listen ·
  `b` bookmark · `j` / `k` paragraph nav · `Esc` close.

## Contents of this repository

```
index.html               The reader (self-contained HTML + embedded JSON).
magnifica-humanitas.pdf  Official Vatican PDF, linked from the cover.
images/                  Cover portrait and one tasteful easter-egg image.
narration/               Audiobook source kit — plain, SSML, and
                         per-chunk respelled text for any TTS pipeline,
                         plus an ffmpeg assemble script.
build/                   Reproducible build tooling — parser, narration
                         generator, reader template, and the canonical
                         structured JSON (build/magnifica.json).
```

## Rebuilding the reader after editing text or template

```bash
python3 -c "import json; t=open('build/reader_template.html').read(); \
d=json.load(open('build/magnifica.json')); \
open('index.html','w').write(t.replace('__DOC_JSON__', \
json.dumps(d,ensure_ascii=False,separators=(',',':')).replace('</','<\\/')))"
```

Regenerate the narration kit after a text change:

```bash
python3 build/gen_narration.py
```

## Producing the audiobook

Pick any TTS engine and feed it `narration/plain/*.txt` (or the SSML
variants under `narration/ssml/`, or the pre-respelled chunks under
`narration/tts-chunks/`). See `narration/README.md` for engine-specific
examples (ElevenLabs, Azure, Google, OpenAI, local Kokoro/Piper) and
cost ballparks. Then:

```bash
cd narration && ./assemble.sh   # produces ../audio/magnifica-narration.mp3
```

The reader auto-detects that file and switches its read-aloud control
to a real narration.

## Credits and licence

The official text of *Magnifica Humanitas* is © Dicastery for
Communication — Libreria Editrice Vaticana, and remains the property of
the Holy See. This repository contains the official English edition
unmodified, together with a reader, build tooling, and a narration kit
that are released into the public domain to support unhurried study.

The official text and translations are also available at
<https://www.vatican.va/content/leo-xiv/en/encyclicals/documents/20260515-magnifica-humanitas.html>.
