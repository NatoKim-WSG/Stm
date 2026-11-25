from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def parse_time(value) -> float:
    """Accept seconds (123.4) or timestamps ("1:02:03.5", "02:03")."""
    if isinstance(value, (int, float)):
        return float(value)
    parts = [float(p) for p in str(value).strip().split(":")]
    total = 0.0
    for p in parts:
        total = total * 60 + p
    return total


def fmt_time(t: float) -> str:
    h, rem = divmod(max(0.0, t), 3600)
    m, s = divmod(rem, 60)
    return f"{int(h):02d}:{int(m):02d}:{s:04.1f}"
