"""Render vertical 9:16 Shorts from a clip plan.

Usage:  python -m clipper.render work/<video name>/clips.json [--only 01 03]

clips.json format:
{
  "source": "sources/video.mp4",
  "campaign": "campaigns/<slug>.md",
  "reframe": "blur",                    # default for all clips: "blur" (fit + blurred fill) or "crop"
  "style": {"caption_margin_v": 560},   # optional overrides of clipper/captions.py DEFAULT_STYLE
  "clips": [
    {
      "id": "01",
      "start": "00:12:03.5", "end": "00:12:41.0",
      "hook": "TEXT SHOWN AT THE TOP",
      "title": "YouTube title", "description": "...", "hashtags": ["#shorts"],
      "reframe": "crop", "crop_x": 0.5,  # optional per clip; crop_x 0 = left edge, 1 = right edge
      "reason": "why this moment works"
    }
  ]
}
Output goes to output/<video name>/clip<id>.mp4 plus upload_info.md with titles and descriptions.
"""
import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

from . import ROOT, fmt_time, parse_time
from .captions import PLAY_H, PLAY_W, build_ass

MAX_SHORT_SECONDS = 180


def has_audio(src: Path) -> bool:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries", "stream=index", "-of", "csv=p=0", str(src)],
        capture_output=True, text=True,
    )
    return bool(out.stdout.strip())


def video_graph(reframe: str, crop_x: float) -> str:
    W, H = PLAY_W, PLAY_H
    if reframe == "crop":
        return (f"[0:v]scale=-2:{H},crop={W}:{H}:(iw-{W})*{crop_x}:0,setsar=1,ass=subs.ass[v]")
    # "blur": whole frame fitted in the middle, blurred zoomed copy filling the background
    return (f"[0:v]split=2[bg][fg];"
            f"[bg]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},boxblur=25:2[bgb];"
            f"[fg]scale={W}:{H}:force_original_aspect_ratio=decrease[fgs];"
            f"[bgb][fgs]overlay=(W-w)/2:(H-h)/2,setsar=1,ass=subs.ass[v]")


def words_in_range(transcript, start, end):
    out = []
    for seg in transcript["segments"]:
        if seg["end"] < start or seg["start"] > end:
            continue
        for w in seg["words"]:
            if w["start"] >= start - 0.05 and w["end"] <= end + 0.3:
                out.append({"word": w["word"], "start": w["start"] - start, "end": min(w["end"], end) - start})
    return out


def render_clip(plan, clip, transcript, src, audio, work_dir, out_dir):
    cid = str(clip["id"])
    start, end = parse_time(clip["start"]), parse_time(clip["end"])
    dur = end - start
    if dur <= 0:
        raise ValueError(f"clip {cid}: end must be after start")
    if dur > MAX_SHORT_SECONDS:
        raise ValueError(f"clip {cid}: {dur:.0f}s is longer than the {MAX_SHORT_SECONDS}s Shorts limit")

    reframe = clip.get("reframe", plan.get("reframe", "blur"))
    crop_x = float(clip.get("crop_x", 0.5))
    words = words_in_range(transcript, start, end)

    clip_work = work_dir / f"clip{cid}"
    clip_work.mkdir(parents=True, exist_ok=True)
    (clip_work / "subs.ass").write_text(
        build_ass(words, dur, hook=clip.get("hook"), hook_duration=clip.get("hook_duration"),
                  style=plan.get("style")),
        encoding="utf-8",
    )

    out = out_dir / f"clip{cid}.mp4"
    cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-nostats",
           "-ss", f"{start:.3f}", "-t", f"{dur:.3f}", "-i", str(src),
           "-filter_complex", video_graph(reframe, crop_x), "-map", "[v]",
           "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p", "-r", "30"]
    if audio:
        cmd += ["-map", "0:a:0", "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-ar", "48000",
                "-c:a", "aac", "-b:a", "160k"]
    cmd += ["-movflags", "+faststart", str(out)]

    print(f"\nclip{cid}  {fmt_time(start)} -> {fmt_time(end)}  ({dur:.1f}s, {reframe}, {len(words)} words)")
    subprocess.run(cmd, cwd=clip_work, check=True)  # cwd so the ass filter path needs no escaping
    return out


def write_upload_info(plan, clips, out_dir):
    lines = [f"# Upload info", "", f"Campaign: {plan.get('campaign', '(not set)')}", ""]
    for c in clips:
        tags = " ".join(c.get("hashtags", []))
        lines += [
            f"## clip{c['id']}.mp4",
            f"- **Moment:** {c['start']} - {c['end']}",
            f"- **Title:** {c.get('title', '')}",
            f"- **Description:** {c.get('description', '')} {tags}".rstrip(),
            f"- **Why:** {c.get('reason', '')}",
            "",
        ]
    (out_dir / "upload_info.md").write_text("\n".join(lines), encoding="utf-8")


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("plan", help="path to work/<video name>/clips.json")
    ap.add_argument("--only", nargs="*", help="render only these clip ids")
    args = ap.parse_args()

    if not shutil.which("ffmpeg"):
        sys.exit("ffmpeg not found on PATH")
    plan_path = Path(args.plan).resolve()
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    work_dir = plan_path.parent
    transcript = json.loads((work_dir / "transcript.json").read_text(encoding="utf-8"))

    src = Path(plan.get("source") or transcript["source"])
    if not src.is_absolute():
        src = ROOT / src
    if not src.exists():
        sys.exit(f"Source not found: {src}")

    out_dir = ROOT / "output" / work_dir.name
    out_dir.mkdir(parents=True, exist_ok=True)
    clips = [c for c in plan["clips"] if not args.only or str(c["id"]) in args.only]
    audio = has_audio(src)

    done = [render_clip(plan, c, transcript, src, audio, work_dir, out_dir) for c in clips]
    write_upload_info(plan, plan["clips"], out_dir)
    print(f"\nRendered {len(done)} clip(s) to {out_dir}")


if __name__ == "__main__":
    main()
