"""Transcribe a source video with word-level timestamps.

Usage:  python -m clipper.transcribe sources/video.mp4 [--model small] [--language en]

Writes work/<video name>/transcript.json (full data, used by render)
   and work/<video name>/transcript.txt  (timestamped lines, for picking moments)
"""
import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

from . import ROOT, fmt_time

os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")
SAMPLE_RATE = 16000


def load_audio(src: Path):
    """Decode audio with ffmpeg to 16 kHz mono float32 (avoids PyAV version issues)."""
    import numpy as np

    proc = subprocess.run(
        ["ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error", "-i", str(src),
         "-vn", "-ac", "1", "-ar", str(SAMPLE_RATE), "-f", "s16le", "-"],
        capture_output=True, check=True,
    )
    return np.frombuffer(proc.stdout, np.int16).astype(np.float32) / 32768.0


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("source", help="path to the source video or audio file")
    ap.add_argument("--model", default="small",
                    help="tiny | base | small | medium | large-v3  (bigger = more accurate, slower)")
    ap.add_argument("--language", default=None, help="e.g. en; auto-detected if omitted")
    ap.add_argument("--device", default="auto", choices=["auto", "cpu", "cuda"],
                    help="auto = NVIDIA GPU (CUDA) when available, else CPU")
    args = ap.parse_args()

    src = Path(args.source).resolve()
    if not src.exists():
        sys.exit(f"Source not found: {src}")
    out_dir = ROOT / "work" / src.stem
    out_dir.mkdir(parents=True, exist_ok=True)

    from faster_whisper import WhisperModel  # slow import; keep --help fast

    print("Extracting audio...")
    audio = load_audio(src)
    device = args.device
    if device == "auto":
        import ctranslate2
        device = "cuda" if ctranslate2.get_cuda_device_count() > 0 else "cpu"
    compute_type = "float16" if device == "cuda" else "int8"
    print(f"Loading Whisper model '{args.model}' on {device} ({compute_type}) (first run downloads it)...")
    model = WhisperModel(args.model, device=device, compute_type=compute_type)
    segments, info = model.transcribe(
        audio, word_timestamps=True, vad_filter=True, language=args.language
    )
    print(f"Language: {info.language}  |  duration: {fmt_time(info.duration)}")

    t0 = time.time()
    data = {"source": str(src), "language": info.language, "duration": info.duration, "segments": []}
    for seg in segments:
        data["segments"].append({
            "start": round(seg.start, 2),
            "end": round(seg.end, 2),
            "text": seg.text.strip(),
            "words": [{"word": w.word.strip(), "start": round(w.start, 2), "end": round(w.end, 2)}
                      for w in (seg.words or [])],
        })
        print(f"\r  transcribed {fmt_time(seg.end)} / {fmt_time(info.duration)}", end="", flush=True)
    print(f"\nDone in {time.time() - t0:.0f}s, {len(data['segments'])} segments.")

    (out_dir / "transcript.json").write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    with open(out_dir / "transcript.txt", "w", encoding="utf-8") as f:
        for s in data["segments"]:
            f.write(f"[{fmt_time(s['start'])} - {fmt_time(s['end'])}] {s['text']}\n")
    print(f"Wrote {out_dir / 'transcript.txt'}")


if __name__ == "__main__":
    main()
