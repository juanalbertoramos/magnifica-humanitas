#!/usr/bin/env bash
# Assemble per-chapter narration MP3s into one normalized audiobook file
# with chapter markers, ready for the reader's audio player.
#
# Usage:
#   1) Synthesize 7 files into ./out/ named:
#        00-introduction.mp3 01-chapter-one.mp3 ... 06-conclusion.mp3
#   2) ./assemble.sh
#   3) Output -> ../audio/magnifica-narration.mp3  (the reader auto-detects this)
#
# Requires ffmpeg.
set -euo pipefail
cd "$(dirname "$0")"
IN=out
OUTDIR=../audio
FINAL="$OUTDIR/magnifica-narration.mp3"
mkdir -p "$OUTDIR" tmp

declare -a TITLES=("Introduction" "Chapter One — A Dynamic Approach Faithful to the Gospel" \
  "Chapter Two — Foundations and Principles of the Social Doctrine" \
  "Chapter Three — Technology and Dominance" \
  "Chapter Four — Safeguarding Humanity: Truth, Work, Freedom" \
  "Chapter Five — The Culture of Power and the Civilization of Love" \
  "Conclusion")
SLUGS=(00-introduction 01-chapter-one 02-chapter-two 03-chapter-three 04-chapter-four 05-chapter-five 06-conclusion)

# 1. loudness-normalize each chapter to spoken-word standard (-16 LUFS)
: > tmp/concat.txt
for s in "${SLUGS[@]}"; do
  [ -f "$IN/$s.mp3" ] || { echo "missing $IN/$s.mp3"; exit 1; }
  ffmpeg -y -i "$IN/$s.mp3" -af loudnorm=I=-16:TP=-1.5:LRA=11 -ar 44100 "tmp/$s.norm.mp3"
  echo "file 'tmp/$s.norm.mp3'" >> tmp/concat.txt
done

# 2. build ffmetadata with chapter markers (uses normalized durations)
echo ";FFMETADATA1" > tmp/meta.txt
echo "title=Magnifica Humanitas — Pope Leo XIV" >> tmp/meta.txt
echo "artist=Pope Leo XIV" >> tmp/meta.txt
echo "album=Magnifica Humanitas (Reader's Edition narration)" >> tmp/meta.txt
start=0
for i in "${!SLUGS[@]}"; do
  dur=$(ffprobe -v quiet -of csv=p=0 -show_entries format=duration "tmp/${SLUGS[$i]}.norm.mp3")
  ms=$(printf '%.0f' "$(echo "$dur*1000" | bc -l)")
  end=$((start+ms))
  { echo "[CHAPTER]"; echo "TIMEBASE=1/1000"; echo "START=$start"; echo "END=$end"; echo "title=${TITLES[$i]}"; } >> tmp/meta.txt
  start=$end
done

# 3. concat + attach chapter metadata
ffmpeg -y -f concat -safe 0 -i tmp/concat.txt -i tmp/meta.txt -map_metadata 1 -c:a libmp3lame -q:a 3 "$FINAL"
rm -rf tmp
echo "Done -> $FINAL"
echo "Open magnifica-humanitas.html and the 'Read aloud' player will use it automatically."
