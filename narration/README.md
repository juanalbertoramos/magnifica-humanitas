# Magnifica Humanitas — Narration Kit

Everything you need to turn the encyclical into a high-quality ~4-hour audio
narration, ready for whichever text‑to‑speech tool you choose. The finished
audio drops straight into the reader (`magnifica-humanitas.html`).

> **About the voice:** there is **no tool that produces Pope Leo XIV's real
> voice**, and cloning a living person's voice without consent violates every
> reputable provider's terms. Pick a dignified, professional narrator voice
> (an older, measured male voice suits the text well).

## The numbers
- **~232,000 characters · ~37,000 words · ≈ 4.1 hours** of finished audio.
- Per chapter (characters): Introduction 17K · Ch. 1 37K · Ch. 2 39K · Ch. 3 37K · Ch. 4 47K · Ch. 5 38K · Conclusion 17K.
- Footnote reference markers are **removed** from all narration text.

## What's in here
| Folder / file | Use it for |
|---|---|
| `plain/00..06-*.txt` | One clean text file per chapter. Best for **ElevenLabs**, **Play.ht/WellSaid/Murf**, local models, or human proofreading. |
| `plain/magnifica-full.txt` | The whole encyclical as one file (e.g. ElevenLabs Studio, Azure batch). |
| `ssml/00..06-*.ssml` + `magnifica-full.ssml` | SSML with reverent pacing (`rate 92%`), paragraph/section pauses, and `<sub>` pronunciation for Latin. Best for **Azure**, **Google Cloud TTS**, **Amazon Polly**. |
| `tts-chunks/chunk-###.txt` | 74 chunks ≤ 3,800 chars, **already respelled** (Latin + "A.I.") so they need **no lexicon**. Best for **OpenAI TTS** and any char‑limited / dictionary‑less engine. `manifest.json` maps each chunk → chapter. |
| `lexicon/pronunciation-guide.md` | Human‑readable say‑it‑like table. |
| `lexicon/aliases.json` | Term → respelling map (for substitution pipelines). |
| `lexicon/lexicon.pls` | W3C PLS lexicon (IPA) for Azure/engines that accept a lexicon file. |
| `assemble.sh` | ffmpeg: normalize + concatenate the 7 chapter MP3s into one chaptered audiobook at `../audio/magnifica-narration.mp3`. |

Normalizations already applied to `plain/` and `tts-chunks/`: papal Roman
numerals → words ("Leo XIII" → "Leo the Thirteenth"), `cf.` → "see",
`i.e.` → "that is". SSML keeps the original spelling but adds `<sub>` hints.

---

## Pick your pipeline

### A. ElevenLabs (best naturalness) — use `plain/`
1. Project/Studio → paste `plain/magnifica-full.txt` (or add 7 chapter files).
2. Settings → **Pronunciation Dictionary**: add the entries from
   `lexicon/aliases.json` (alias/phonetic form), or just trust the respellings.
3. Choose one voice; keep **Stability ~50, Similarity ~75** for consistency.
4. Export MP3 per chapter into `narration/out/` (see naming in `assemble.sh`).

```python
# minimal per-chunk example (API)
from elevenlabs import ElevenLabs
c = ElevenLabs(api_key="...")
text = open("plain/00-introduction.txt").read()
audio = c.text_to_speech.convert(voice_id="<voice>", model_id="eleven_multilingual_v2", text=text)
open("out/00-introduction.mp3","wb").write(b"".join(audio))
```

### B. Azure AI Speech (great for book-length, SSML) — use `ssml/` + `lexicon.pls`
Azure's **Batch synthesis / Long Audio** API is built for this length.
```bash
# upload lexicon.pls somewhere Azure can read, reference it in SSML via:
#   <lexicon uri="https://.../lexicon.pls"/>
az cognitiveservices ... # or the Batch Synthesis REST API with ssml/magnifica-full.ssml
```
Pick a neural voice (e.g. a calm `en-US` or `en-GB` male). SSML pauses are already in place.

### C. Google Cloud TTS (Chirp 3 HD / Studio) — use `ssml/`
```bash
gcloud ml speech ... # or REST: synthesize per chapter from ssml/0X-*.ssml
```
Google reads the `<sub>`, `<break>`, `<prosody>` tags. For names not covered,
add them to the SSML the same way.

### D. OpenAI TTS / any char-limited engine — use `tts-chunks/`
No lexicon needed (already respelled, ≤3,800 chars).
```python
from openai import OpenAI
import glob, json
client = OpenAI()
for ch in sorted(glob.glob("tts-chunks/chunk-*.txt")):
    text = open(ch).read()
    with client.audio.speech.with_streaming_response.create(
        model="gpt-4o-mini-tts", voice="onyx", input=text) as r:
        r.stream_to_file(ch.replace("tts-chunks","out").replace(".txt",".mp3"))
# then concatenate the chunk MP3s per chapter using manifest.json
```

### E. Local / free / private — Kokoro, Coqui XTTS-v2, or Piper
Feed `plain/` (or `tts-chunks/` if your model has tight limits). Example (Piper):
```bash
cat plain/00-introduction.txt | piper -m en_US-ryan-high.onnx -f out/00-introduction.wav
```

---

## Assemble the final audiobook
```bash
# after you have out/00..06-*.mp3
./assemble.sh        # -> ../audio/magnifica-narration.mp3 (normalized, chaptered)
```
Then open `magnifica-humanitas.html` — the **Read aloud** player detects
`audio/magnifica-narration.mp3` automatically and uses it instead of the
device voice.

## Rough cost (verify current rates)
- Cloud premium neural (Azure/Google/Polly): ~**$3–$20** for 232K chars.
- OpenAI TTS: a few dollars.
- ElevenLabs ultra-realistic: higher (tens of dollars of credits) — top quality.
- Local models: **free** + compute time.
