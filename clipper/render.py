"""Render vertical 9:16 Shorts from a clip plan.

Usage:  python -m clipper.render work/<video name>/clips.json [--only 01 03]

clips.json format:
{
  "source": "sources/video.mp4",
  "campaign": "campaigns/<slug>.md",
  "reframe": "blur",                    # default for all clips: "blur" (fit + blurred fill), "crop",
                                        # or "box" (cut "box": [x0,y0,x1,y1] out, show it full-width
                                        # at "box_center_y", blurred copy behind; hides stream overlays)
  "grade": "pop",                       # colour grade ("none" to switch off)
  "style": {"caption_margin_v": 560},   # optional overrides of clipper/captions.py DEFAULT_STYLE
  "clips": [
    {
      "id": "01",
      "start": "00:12:03.5", "end": "00:12:41.0",
      # or jump cuts: "segments": [{"start": 830.6, "end": 836.4}, {"start": 860.2, "end": 865.0}]
      "hook": "TEXT SHOWN AT THE TOP with *ACCENT* words",
      "title": "YouTube title", "description": "...", "hashtags": ["#shorts"],
      "reframe": "crop", "crop_x": 0.5,  # optional per clip; crop_x 0 = left edge, 1 = right edge
      "zooms": [...], "emojis": [...], "sfx": [...],   # see clipper/effects.py (times = clip seconds)
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
from . import effects as fx
from .captions import PLAY_H, PLAY_W, build_ass

MAX_SHORT_SECONDS = 180


def has_audio(src: Path) -> bool:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries", "stream=index", "-of", "csv=p=0", str(src)],
        capture_output=True, text=True,
    )
    return bool(out.stdout.strip())


def reframe_graph(reframe: str, crop_x: float, vin: str = "[0:v]", box=None, box_center_y: float = 0.45) -> str:
    """Source -> 9:16 frame, output label [rf]."""
    W, H = PLAY_W, PLAY_H
    if reframe == "crop":
        return f"{vin}scale=-2:{H},crop={W}:{H}:(iw-{W})*{crop_x}:0,setsar=1[rf]"
    if reframe == "box":
        # cut a region [x0, y0, x1, y1] (fractions) out of the source, show it full-width, and fill
        # the rest with a blurred copy of that same region (so overlays outside it never show)
        x0, y0, x1, y1 = box
        return (f"{vin}crop=iw*{x1 - x0:.4f}:ih*{y1 - y0:.4f}:iw*{x0:.4f}:ih*{y0:.4f},split=2[bg][fg];"
                f"[bg]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},boxblur=25:2[bgb];"
                f"[fg]scale={W}:-2[fgs];"
                f"[bgb][fgs]overlay=0:'max(0,min(H-h,{box_center_y}*H-h/2))',setsar=1[rf]")
    # "blur": whole frame fitted in the middle, blurred zoomed copy filling the background
    return (f"{vin}split=2[bg][fg];"
            f"[bg]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},boxblur=25:2[bgb];"
            f"[fg]scale={W}:{H}:force_original_aspect_ratio=decrease[fgs];"
            f"[bgb][fgs]overlay=(W-w)/2:(H-h)/2,setsar=1[rf]")


def video_graph(plan, clip, reframe: str, crop_x: float, first_emoji_input: int, vin: str = "[0:v]"):
    """reframe -> colour grade -> punch-in zooms -> emoji pop-ups -> captions, output label [v]."""
    W, H = PLAY_W, PLAY_H
    box = clip.get("box", plan.get("box"))
    if reframe == "box" and not box:
        raise ValueError(f"clip {clip['id']}: reframe 'box' needs \"box\": [x0, y0, x1, y1]")
    parts = [reframe_graph(reframe, crop_x, vin, box, float(clip.get("box_center_y", plan.get("box_center_y", 0.45))))]
    grade = fx.GRADES.get(plan.get("grade", "pop"), plan.get("grade", ""))
    zoom = fx.zoom_filter(clip.get("zooms", []), W, H)
    middle = ",".join(f for f in (grade, zoom) if f) or "null"
    parts.append(f"[rf]{middle}[base]")
    chain, label = fx.emoji_overlays(clip.get("emojis", []), first_emoji_input, "base", W, H)
    parts += chain
    parts.append(f"[{label}]ass=subs.ass[v]")
    return ";".join(parts)


def audio_graph(sfx, first_sfx_input: int, dur: float, has_src_audio: bool, ain: str = "[0:a:0]"):
    """Source speech (loudness-normalised) + sound effects, output label [a]."""
    stereo = "aformat=sample_rates=48000:channel_layouts=stereo"
    if has_src_audio:
        parts = [f"{ain}loudnorm=I=-14:TP=-1.5:LRA=11,{stereo}[a0]"]
    else:
        parts = [f"anullsrc=r=48000:cl=stereo,atrim=0:{dur:.3f}[a0]"]
    labels = ["[a0]"]
    for i, s in enumerate(sfx):
        gain = float(s.get("gain", fx.SFX_TYPES[s["type"]][1]))
        ms = int(round(float(s["at"]) * 1000))
        parts.append(f"[{first_sfx_input + i}:a]adelay={ms}:all=1,volume={gain:.2f},{stereo}[s{i}]")
        labels.append(f"[s{i}]")
    if len(labels) == 1:
        parts.append("[a0]anull[a]")
    else:
        parts.append(f"{''.join(labels)}amix=inputs={len(labels)}:normalize=0:duration=first,"
                     f"alimiter=limit=0.97[a]")
    return ";".join(parts)


def words_in_range(transcript, start, end):
    out = []
    for seg in transcript["segments"]:
        if seg["end"] < start or seg["start"] > end:
            continue
        for w in seg["words"]:
            if w["start"] >= start - 0.05 and w["end"] <= end + 0.3:
                out.append({"word": w["word"], "start": w["start"] - start, "end": min(w["end"], end) - start})
    return out


def clip_segments(clip):
    """[(start, end), ...] in source seconds: "segments" (jump cuts) or a single start/end."""
    if clip.get("segments"):
        segs = [(parse_time(s["start"]), parse_time(s["end"])) if isinstance(s, dict)
                else (parse_time(s[0]), parse_time(s[1])) for s in clip["segments"]]
    else:
        segs = [(parse_time(clip["start"]), parse_time(clip["end"]))]
    for a, b in segs:
        if b <= a:
            raise ValueError(f"clip {clip['id']}: segment end {b} must be after start {a}")
    return segs


def concat_graph(segs, in_start: float, has_audio: bool) -> str:
    """Cut the segments out of input 0 and join them: outputs [cv] (and [ca])."""
    parts, joins = [], []
    for i, (a, b) in enumerate(segs):
        a, b = a - in_start, b - in_start
        parts.append(f"[0:v]trim=start={a:.3f}:end={b:.3f},setpts=PTS-STARTPTS[cv{i}]")
        joins.append(f"[cv{i}]")
        if has_audio:
            parts.append(f"[0:a:0]atrim=start={a:.3f}:end={b:.3f},asetpts=PTS-STARTPTS[ca{i}]")
            joins.append(f"[ca{i}]")
    outs = "[cv][ca]" if has_audio else "[cv]"
    parts.append(f"{''.join(joins)}concat=n={len(segs)}:v=1:a={1 if has_audio else 0}{outs}")
    return ";".join(parts)


def render_clip(plan, clip, transcript, src, audio, work_dir, out_dir):
    cid = str(clip["id"])
    segs = clip_segments(clip)
    start, end = segs[0][0], segs[-1][1]
    in_start, in_end = min(a for a, _ in segs), max(b for _, b in segs)
    dur = sum(b - a for a, b in segs)
    if dur > MAX_SHORT_SECONDS:
        raise ValueError(f"clip {cid}: {dur:.0f}s is longer than the {MAX_SHORT_SECONDS}s Shorts limit")

    reframe = clip.get("reframe", plan.get("reframe", "blur"))
    crop_x = float(clip.get("crop_x", 0.5))
    words, offset = [], 0.0
    for a, b in segs:
        words += [{**w, "start": w["start"] + offset, "end": w["end"] + offset} for w in words_in_range(transcript, a, b)]
        offset += b - a

    clip_work = work_dir / f"clip{cid}"
    clip_work.mkdir(parents=True, exist_ok=True)
    (clip_work / "subs.ass").write_text(
        build_ass(words, dur, hook=clip.get("hook"), hook_duration=clip.get("hook_duration"),
                  style=plan.get("style")),
        encoding="utf-8",
    )

    out = out_dir / f"clip{cid}.mp4"
    emojis = clip.get("emojis", [])
    sfx = fx.sfx_list(plan, clip)
    cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-nostats",
           "-ss", f"{in_start:.3f}", "-t", f"{in_end - in_start:.3f}", "-i", str(src)]
    for e in emojis:
        cmd += ["-loop", "1", "-t", f"{dur:.3f}", "-i", str(fx.emoji_file(e["emoji"]))]
    for s in sfx:
        cmd += ["-i", str(fx.sfx_file(s["type"]))]
    if len(segs) > 1:
        vin, ain = "[cv]", "[ca]"
        prefix = concat_graph(segs, in_start, audio) + ";"
    else:
        vin, ain, prefix = "[0:v]", "[0:a:0]", ""
    graph = (prefix + video_graph(plan, clip, reframe, crop_x, 1, vin) + ";"
             + audio_graph(sfx, 1 + len(emojis), dur, audio, ain))
    cmd += ["-filter_complex", graph, "-map", "[v]", "-map", "[a]",
            "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p", "-r", "30",
            "-ar", "48000", "-c:a", "aac", "-b:a", "160k", "-t", f"{dur:.3f}",
            "-movflags", "+faststart", str(out)]

    print(f"\nclip{cid}  {fmt_time(start)} -> {fmt_time(end)}  ({dur:.1f}s, {len(segs)} part(s), {reframe}, {len(words)} words, "
          f"{len(clip.get('zooms', []))} zooms, {len(emojis)} emojis, {len(sfx)} sfx)")
    subprocess.run(cmd, cwd=clip_work, check=True)  # cwd so the ass filter path needs no escaping
    return out


def write_upload_info(plan, clips, out_dir):
    lines = [f"# Upload info", "", f"Campaign: {plan.get('campaign', '(not set)')}", ""]
    for c in clips:
        tags = " ".join(c.get("hashtags", []))
        lines += [
            f"## clip{c['id']}.mp4",
            "- **Moment:** " + (" + ".join(f"{s['start']}-{s['end']}" if isinstance(s, dict) else f"{s[0]}-{s[1]}"
                                           for s in c["segments"]) if c.get("segments")
                                else f"{c['start']} - {c['end']}"),
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
