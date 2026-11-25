"""Edit effects for clips: colour grade, punch-in zooms, emoji pop-ups and sound effects.

Sound effects are synthesised with FFmpeg (no downloaded or licensed audio), so they are safe for
campaigns that ban unlicensed music. Emojis are drawn from the Windows colour emoji font.

clips.json fields (all optional; times are seconds from the clip start):
  plan:  "grade": "pop" | "none"            (default "pop")
         "intro_whoosh": true | false       (default true: whoosh under the hook at 0 s)
  clip:  "zooms":  [{"at": 4.2, "dur": 2.5, "scale": 1.2, "x": 0.5, "y": 0.4}]
                   x/y = focal point (0..1) the zoom pushes towards
         "emojis": [{"at": 6.0, "dur": 1.4, "emoji": "🔥", "x": 0.84, "y": 0.5, "size": 200}]
         "sfx":    [{"at": 6.0, "type": "pop", "gain": 0.5}]   types: SFX_TYPES
"""
import subprocess
from pathlib import Path

from . import ROOT

ASSETS = ROOT / "work" / "_assets"
EMOJI_FONT = Path("C:/Windows/Fonts/seguiemj.ttf")

# name -> (ffmpeg lavfi source, default gain)
SFX_TYPES = {
    "whoosh": ("anoisesrc=d=0.6:c=pink:r=48000:a=0.9,bandpass=f=1400:width_type=o:w=2.5,"
               "afade=t=in:st=0:d=0.22:curve=qsin,afade=t=out:st=0.22:d=0.38:curve=qsin,volume=1.6", 0.55),
    "pop":    ("aevalsrc='0.8*sin(2*PI*(500+2600*exp(-t*45))*t)*exp(-t*32)':d=0.16:s=48000", 0.5),
    "ding":   ("aevalsrc='0.45*(sin(2*PI*1568*t)+0.6*sin(2*PI*2349*t)+0.3*sin(2*PI*3136*t))*exp(-t*5)'"
               ":d=1.0:s=48000", 0.35),
    "boom":   ("aevalsrc='0.95*sin(2*PI*(42+110*exp(-t*14))*t)*exp(-t*3.5)':d=1.0:s=48000,lowpass=f=400", 0.7),
    "riser":  ("aevalsrc='0.35*sin(2*PI*(160*t+520*t*t))*(t/1.2)':d=1.2:s=48000", 0.35),
}

GRADES = {
    "pop": "eq=contrast=1.07:saturation=1.25:brightness=0.01,unsharp=5:5:0.5:5:5:0",
    "none": "",
}


def sfx_file(kind: str) -> Path:
    if kind not in SFX_TYPES:
        raise ValueError(f"unknown sfx type {kind!r}; use one of {', '.join(SFX_TYPES)}")
    path = ASSETS / f"sfx_{kind}.wav"
    if not path.exists():
        ASSETS.mkdir(parents=True, exist_ok=True)
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", SFX_TYPES[kind][0],
                        "-ac", "2", "-ar", "48000", str(path)], check=True)
    return path


def emoji_file(char: str, px: int = 240) -> Path:
    path = ASSETS / f"emoji_{'-'.join(f'{ord(c):x}' for c in char)}_{px}.png"
    if not path.exists():
        from PIL import Image, ImageDraw, ImageFont  # only needed when a clip uses emojis
        ASSETS.mkdir(parents=True, exist_ok=True)
        font = ImageFont.truetype(str(EMOJI_FONT), px)
        im = Image.new("RGBA", (px * 3, px * 2), (0, 0, 0, 0))
        ImageDraw.Draw(im).text((px // 2, px // 4), char, font=font, embedded_color=True)
        box = im.getbbox()
        if not box:
            raise ValueError(f"emoji {char!r} did not render with {EMOJI_FONT.name}")
        im.crop(box).save(path)
    return path


def _ramp(a: float, b: float, edge: float = 0.15) -> str:
    """0 outside [a, b], eases to 1 inside (edge seconds in and out)."""
    return f"clip(min((t-{a:.3f})/{edge},({b:.3f}-t)/{edge}),0,1)"


def zoom_filter(zooms, w: int, h: int) -> str:
    if not zooms:
        return ""
    z = "1" + "".join(f"+{float(zm.get('scale', 1.2)) - 1:.3f}*{_ramp(zm['at'], zm['at'] + zm.get('dur', 2.0))}"
                      for zm in zooms)
    fx = "0.5" + "".join(f"+{float(zm.get('x', 0.5)) - 0.5:.3f}*{_ramp(zm['at'], zm['at'] + zm.get('dur', 2.0))}"
                         for zm in zooms)
    fy = "0.5" + "".join(f"+{float(zm.get('y', 0.5)) - 0.5:.3f}*{_ramp(zm['at'], zm['at'] + zm.get('dur', 2.0))}"
                         for zm in zooms)
    return (f"scale=w='2*trunc({w}*({z})/2)':h='2*trunc({h}*({z})/2)':eval=frame:flags=bicubic,"
            f"crop={w}:{h}:'(iw-{w})*({fx})':'(ih-{h})*({fy})'")


def emoji_overlays(emojis, first_input: int, src_label: str, w: int, h: int):
    """Returns (filter chain text, output label). Emoji PNGs must be inputs first_input.. in order."""
    chain, label = [], src_label
    for i, e in enumerate(emojis):
        a, d, size = float(e["at"]), float(e.get("dur", 1.4)), int(e.get("size", 200))
        p = f"(t-{a:.3f})"
        pop = f"if(lt({p},0.16),0.45+0.8*{p}/0.16,if(lt({p},0.28),1.25-0.25*({p}-0.16)/0.12,1))"
        k = first_input + i
        chain.append(f"[{k}:v]scale=w='max(2,2*trunc({size}*{pop}/2))':h=-2:eval=frame[em{i}]")
        out = f"ov{i}"
        chain.append(f"[{label}][em{i}]overlay=x='{float(e.get('x', 0.84)) * w:.1f}-w/2':"
                     f"y='{float(e.get('y', 0.5)) * h:.1f}-h/2':enable='between(t,{a:.3f},{a + d:.3f})'"
                     f":shortest=1[{out}]")
        label = out
    return chain, label


def sfx_list(plan, clip):
    items = list(clip.get("sfx", []))
    if plan.get("intro_whoosh", True) and clip.get("hook") and not any(s.get("at", 0) < 0.3 for s in items):
        items.insert(0, {"at": 0.0, "type": "whoosh"})
    return items
