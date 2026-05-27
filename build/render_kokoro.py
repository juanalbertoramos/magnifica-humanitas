#!/usr/bin/env python3
"""Render a chapter of the encyclical with Kokoro-onnx, using IPA-direct overrides
for words and phrases where espeak-ng's English defaults are wrong.

Workflow per chapter:
  1. Read plain text from narration/plain/<chapter>.txt
  2. espeak-phonemise via kokoro.tokenizer.phonemize()
  3. Apply IPA_OVERRIDES (espeak's wrong IPA → desired ecclesiastical IPA)
  4. Synthesise audio with is_phonemes=True
  5. Write narration/out/<chapter>.mp3
"""

from __future__ import annotations
import argparse, os, subprocess, sys, time
from pathlib import Path

# espeak's actual IPA  →  ecclesiastical / corrected IPA
IPA_OVERRIDES: dict[str, str] = {
    # Latin pontifical/encyclical phrases — Italian-school Latin
    "ɹɪɹˈʌm nˈəʊvəɹəm":           "ˈreːrum noˈvaːrum",   # Rerum Novarum / rerum novarum
    "ɹˈɛz nˈəʊvə":                "ˈrɛs ˈnɔvɛ",          # res novae
    "kˈɔːpəs":                    "ˈkɔrpus",             # corpus
    # (more to be added as future chapters surface them — see gen_narration.py RESPELL list)
}


def render(chapter_slug: str, voice: str, lang: str, speed: float, out_dir: Path, repo: Path) -> Path:
    from kokoro_onnx import Kokoro
    import soundfile as sf

    text_path = repo / "narration" / "plain" / f"{chapter_slug}.txt"
    text = text_path.read_text()

    k = Kokoro(str(repo / "models" / "kokoro-v1.0.onnx"),
               str(repo / "models" / "voices-v1.0.bin"))

    ipa = k.tokenizer.phonemize(text, lang=lang)
    n_subs = 0
    for src, dst in IPA_OVERRIDES.items():
        if src in ipa:
            ipa = ipa.replace(src, dst)
            n_subs += 1
    print(f"[{chapter_slug}] {len(text):>6} chars text → {len(ipa):>6} phonemes  ({n_subs} IPA overrides)")

    t0 = time.time()
    samples, sr = k.create(ipa, voice=voice, lang=lang, speed=speed, is_phonemes=True)
    audio_s = len(samples) / sr
    elapsed = time.time() - t0
    print(f"[{chapter_slug}] rendered {audio_s/60:.1f} min audio in {elapsed/60:.1f} min compute (RTF {elapsed/audio_s:.2f})")

    out_dir.mkdir(parents=True, exist_ok=True)
    wav = out_dir / f"{chapter_slug}.wav"
    mp3 = out_dir / f"{chapter_slug}.mp3"
    sf.write(str(wav), samples, sr)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(wav),
                    "-codec:a", "libmp3lame", "-q:a", "3", str(mp3)], check=True)
    wav.unlink()
    return mp3


CHAPTERS = ["00-introduction", "01-chapter-one", "02-chapter-two", "03-chapter-three",
            "04-chapter-four", "05-chapter-five", "06-conclusion"]


def main():
    p = argparse.ArgumentParser()
    p.add_argument("chapter", nargs="?", default=None,
                   help="chapter slug to render (e.g. 00-introduction). Default: all 7 chapters.")
    p.add_argument("--voice", default="bm_george")
    p.add_argument("--lang",  default="en-gb")
    p.add_argument("--speed", type=float, default=0.95)
    args = p.parse_args()

    repo = Path(__file__).resolve().parent.parent
    out  = repo / "narration" / "out"

    targets = [args.chapter] if args.chapter else CHAPTERS
    for slug in targets:
        if slug not in CHAPTERS:
            print(f"unknown chapter: {slug}", file=sys.stderr); sys.exit(1)
        render(slug, args.voice, args.lang, args.speed, out, repo)


if __name__ == "__main__":
    main()
