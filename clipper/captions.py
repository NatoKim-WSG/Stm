"""Build an .ass subtitle file: word-by-word captions plus an optional hook title."""

PLAY_W, PLAY_H = 1080, 1920

DEFAULT_STYLE = {
    "font": "Arial Black",
    "caption_size": 78,
    "caption_margin_v": 560,     # distance of caption baseline from the bottom edge
    "hook_size": 64,
    "hook_margin_v": 240,        # distance of hook box from the top edge
    "highlight": "&H00FFFF&",    # active word colour, ASS BGR order (this is yellow)
    "uppercase": True,
    "max_words": 3,              # words shown on screen at once
    "max_chars": 18,
}


def _ts(t: float) -> str:
    t = max(0.0, t)
    cs = int(round(t * 100))
    h, cs = divmod(cs, 360000)
    m, cs = divmod(cs, 6000)
    s, cs = divmod(cs, 100)
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"


def _clean(text: str) -> str:
    return text.replace("{", "").replace("}", "").replace("\\", "").strip()


def _chunks(words, max_words, max_chars):
    """Group words into short on-screen phrases, breaking on pauses and punctuation."""
    chunk = []
    for w in words:
        if chunk:
            gap = w["start"] - chunk[-1]["end"]
            length = sum(len(x["word"]) + 1 for x in chunk) + len(w["word"])
            ends_sentence = chunk[-1]["word"].rstrip()[-1:] in ".?!,"
            if len(chunk) >= max_words or length > max_chars or gap > 0.6 or ends_sentence:
                yield chunk
                chunk = []
        chunk.append(w)
    if chunk:
        yield chunk


def build_ass(words, duration, hook=None, hook_duration=None, style=None):
    """words: [{"word", "start", "end"}] with times relative to the clip start."""
    st = {**DEFAULT_STYLE, **(style or {})}
    words = [{**w, "word": _clean(w["word"])} for w in words]
    words = [w for w in words if w["word"]]
    if st["uppercase"]:
        words = [{**w, "word": w["word"].upper()} for w in words]

    lines = [
        "[Script Info]",
        "ScriptType: v4.00+",
        f"PlayResX: {PLAY_W}",
        f"PlayResY: {PLAY_H}",
        "WrapStyle: 0",
        "ScaledBorderAndShadow: yes",
        "",
        "[V4+ Styles]",
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, "
        "Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, "
        "Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
        f"Style: Caption,{st['font']},{st['caption_size']},&H00FFFFFF,&H00FFFFFF,&H00000000,&H80000000,"
        f"-1,0,0,0,100,100,0,0,1,7,3,2,70,70,{st['caption_margin_v']},1",
        f"Style: Hook,{st['font']},{st['hook_size']},&H00FFFFFF,&H00FFFFFF,&H20000000,&H00000000,"
        f"-1,0,0,0,100,100,0,0,3,16,0,8,90,90,{st['hook_margin_v']},1",
        "",
        "[Events]",
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
    ]

    if hook:
        end = duration if hook_duration is None else min(duration, float(hook_duration))
        lines.append(f"Dialogue: 1,{_ts(0)},{_ts(end)},Hook,,0,0,0,,{_clean(hook)}")

    chunks = list(_chunks(words, st["max_words"], st["max_chars"]))
    for ci, chunk in enumerate(chunks):
        chunk_end = chunk[-1]["end"]
        if ci + 1 < len(chunks):
            nxt = chunks[ci + 1][0]["start"]
            if nxt - chunk_end < 0.35:      # avoid flicker between close phrases
                chunk_end = nxt
        for i, w in enumerate(chunk):
            start = w["start"]
            end = chunk[i + 1]["start"] if i + 1 < len(chunk) else chunk_end
            if end <= start:
                continue
            text = " ".join(
                f"{{\\c{st['highlight']}}}{x['word']}{{\\c&HFFFFFF&}}" if j == i else x["word"]
                for j, x in enumerate(chunk)
            )
            lines.append(f"Dialogue: 0,{_ts(start)},{_ts(min(end, duration))},Caption,,0,0,0,,{text}")

    return "\n".join(lines) + "\n"
