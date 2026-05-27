# Vatican source archive

A forensic copy of the official Vatican source for *Magnifica Humanitas*,
preserved here so the reader's edition in this repository can be
re-verified against authoritative ground truth at any time.

## What's in here

| File | Captured with | Size | Notes |
|---|---|---|---|
| `magnifica-humanitas.html` | `curl` (User-Agent: Chrome 131 on macOS) | ~395 KB | Raw HTML exactly as served by `vatican.va`, including the original `MsoNormal` paragraph classes and `_ftn1..224` anchors. |
| `magnifica-humanitas.firecrawl.md` | Firecrawl MCP scraper | ~371 KB | Independent clean markdown extraction of the same page, useful for diffing. |
| `magnifica-humanitas.firecrawl.html` | Firecrawl MCP scraper | ~442 KB | Firecrawl's rendered HTML (after its own normalisation). |

## Provenance

- **Source URL** — <https://www.vatican.va/content/leo-xiv/en/encyclicals/documents/20260515-magnifica-humanitas.html>
- **Captured** — 2026-05-26 (the day after I imported the original Vatican PDF into the repository).
- **HTTP status** — 200 OK; the page is served without authentication and is part of the Vatican's public encyclical archive.

## Cross-verification at capture time

All three sources independently contain the same structural content as
this repository's parsed `build/magnifica.json`:

| Measure | curl HTML | Firecrawl MD | `build/magnifica.json` |
|---|---|---|---|
| Numbered paragraphs (1–245, contiguous) | 245 ✓ | 245 ✓ | 245 ✓ |
| Footnote anchors `_ftn1..224` | 224 ✓ | — | 224 ✓ |

## Why this folder exists

The text embedded in `index.html` and `build/magnifica.json` is derived
through a chain of transformations (vatican.va HTML → Firecrawl
markdown → `build/parse_encyclical.py` → JSON → reader HTML), each of
which could introduce a defect. Keeping a captured copy of the source
HTML lets anyone re-run that verification with a single diff if the
text in the reader ever appears to disagree with what the Vatican
publishes today. It also fixes a single canonical reference point
should `vatican.va` reorganise its URLs, take the page down for an
update, or correct an *errata* later — all of which have historical
precedent for papal documents.

## Copyright

These files reproduce the official English-language text of an
encyclical letter of His Holiness Pope Leo XIV. © Dicastery for
Communication — Libreria Editrice Vaticana. They are kept here for
private study and reference. The authoritative source remains the
Vatican website linked above.
