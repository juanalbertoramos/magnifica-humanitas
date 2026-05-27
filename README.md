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
- Read-aloud via a 4-hour narration (`audio/magnifica-narration.mp3`,
  bm_george voice, embedded chapter markers). The reader auto-detects
  the file and falls back to the browser's built-in voices if it's not
  present.
- Keyboard navigation: `t` TOC · `/` search · `n` notes · `l` listen ·
  `b` bookmark · `j` / `k` paragraph nav · `Esc` close.

## Contents of this repository

```
index.html                     The reader (self-contained HTML + embedded JSON).
magnifica-humanitas.pdf        Official Vatican PDF, linked from the cover.
audio/magnifica-narration.mp3  4-hour narration with chapter markers
                               (Kokoro / bm_george, 32 kbps mono).
images/                        Cover portrait and one tasteful easter-egg image.
narration/                     Audiobook source kit — plain, SSML, and
                               per-chunk respelled text for any TTS pipeline,
                               plus an ffmpeg assemble script.
build/                         Reproducible build tooling — parser, narration
                               generator, reader template, the Kokoro render
                               pipeline (render_kokoro.py with IPA overrides
                               for ecclesiastical Latin), and the canonical
                               structured JSON (build/magnifica.json).
vatican-source/                Captured copies of the official Vatican HTML
                               for forensic provenance — see its README.
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

## Re-rendering the audiobook

The shipped narration was rendered with [Kokoro](https://github.com/hexgrad/kokoro)
via `kokoro-onnx` (no GPU required). To re-render in place — for
example after correcting a Latin term in `build/render_kokoro.py`'s
`IPA_OVERRIDES`:

```bash
python3 -m venv .venv-kokoro
.venv-kokoro/bin/pip install kokoro-onnx soundfile
mkdir -p models && curl -L -o models/kokoro-v1.0.onnx \
  https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx
curl -L -o models/voices-v1.0.bin \
  https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin
.venv-kokoro/bin/python build/render_kokoro.py             # renders all 7 chapters into narration/out/
narration/assemble.sh                                       # concat + 32k mono → audio/magnifica-narration.mp3
```

To use a different TTS engine instead (ElevenLabs, Azure, Google,
OpenAI, Piper, etc.), feed it `narration/plain/*.txt` (or the SSML
variants under `narration/ssml/`, or the pre-respelled chunks under
`narration/tts-chunks/`). See `narration/README.md` for engine-specific
examples and cost ballparks. Then:

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
