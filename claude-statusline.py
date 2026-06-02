#!/usr/bin/env python3
"""
Claude Code Usage Statusline

A clean two-line Claude Code statusline showing:
- model
- context usage
- 5-hour quota usage
- weekly quota usage
- reset times
- estimated session cost

No jq required. Python 3 only.
"""

import json
import os
import sys
from datetime import datetime


def load_input() -> dict:
    raw = sys.stdin.read()

    try:
        with open("/tmp/claude-statusline-last.json", "w", encoding="utf-8") as f:
            f.write(raw)
    except Exception:
        pass

    try:
        return json.loads(raw) if raw.strip() else {}
    except Exception:
        return {}


DATA = load_input()


def get(path: str, default=None):
    cur = DATA
    for key in path.split("."):
        if isinstance(cur, dict) and key in cur:
            cur = cur[key]
        else:
            return default
    return cur


def number(value, default=0.0) -> float:
    try:
        return float(value)
    except Exception:
        return default


def fmt_tokens(value) -> str:
    value = int(number(value))
    if value >= 1_000_000:
        return f"{value / 1_000_000:.1f}M"
    if value >= 1_000:
        return f"{value / 1_000:.1f}k"
    return str(value)


def fmt_reset(timestamp) -> str:
    if not timestamp:
        return "?"

    try:
        dt = datetime.fromtimestamp(float(timestamp))
        now = datetime.now()
        time_part = dt.strftime("%I:%M%p").lstrip("0").lower()
        if dt.date() == now.date():
            return time_part
        return f"{dt.strftime('%b')} {dt.day}, {time_part}"
    except Exception:
        return "?"


NO_COLOR = bool(os.environ.get("NO_COLOR"))

if NO_COLOR:
    END = BOLD = OFF = TEXT = DIM = SEP = AMBER = GOLD = WARN = BAD = ""
else:
    END = "\033[0m"
    BOLD = "\033[1m"

    # Restrained Graphite / Warm Amber theme
    OFF = "\033[38;5;252m"     # soft off-white
    TEXT = "\033[38;5;250m"    # readable light grey
    DIM = "\033[38;5;247m"     # secondary light grey
    SEP = "\033[38;5;240m"     # graphite separator

    AMBER = "\033[38;5;180m"   # muted amber
    GOLD = "\033[38;5;222m"    # pale gold
    WARN = "\033[38;5;214m"    # warm warning
    BAD = "\033[38;5;203m"     # soft red


def heat(percent: int) -> str:
    percent = int(round(number(percent)))
    if percent >= 80:
        return BAD
    if percent >= 50:
        return WARN
    return AMBER


def usage_bar(percent, width=None) -> str:
    width = int(number(width or os.environ.get("CLCS_BAR_WIDTH", 12), 12))
    width = max(4, min(40, width))

    percent = max(0, min(100, int(round(number(percent)))))
    filled = round((percent / 100) * width)

    # Non-zero usage should be visible even at small percentages.
    if percent > 0 and filled == 0:
        filled = 1

    color = heat(percent)
    return f"{color}[{'#' * filled}{'-' * (width - filled)}]{END}"


def quota(label: str, obj) -> str:
    if not isinstance(obj, dict) or obj.get("used_percentage") is None:
        return f"{AMBER}{label}{END} {DIM}[------------] --{END}"

    used = max(0, min(100, int(round(number(obj.get("used_percentage"))))))
    left = 100 - used
    reset = fmt_reset(obj.get("resets_at"))
    color = heat(used)

    return (
        f"{AMBER}{label}{END} "
        f"{usage_bar(used)} "
        f"{color}{used}/100{END} "
        f"{TEXT}used · {left} left · reset {reset}{END}"
    )


model = get("model.display_name") or get("model.id") or "Claude"

ctx_in = get("context_window.total_input_tokens", 0)
ctx_out = get("context_window.total_output_tokens", 0)
ctx_total = int(number(ctx_in)) + int(number(ctx_out))
ctx_max = get("context_window.context_window_size", 0)
ctx_pct = int(round(number(get("context_window.used_percentage", 0))))

cost = number(get("cost.total_cost_usd", get("cost_usd", 0)))

five_hour = get("rate_limits.five_hour", {})
seven_day = get("rate_limits.seven_day", {})

line1 = (
    f"{BOLD}{OFF}{model}{END} "
    f"{SEP}│{END} "
    f"{AMBER}CTX{END} {OFF}{fmt_tokens(ctx_total)}/{fmt_tokens(ctx_max)}{END} "
    f"{usage_bar(ctx_pct)} "
    f"{TEXT}{ctx_pct}%{END} "
    f"{SEP}│{END} "
    f"{GOLD}${cost:.2f}{END}"
)

line2 = (
    f"{quota('5H', five_hour)} "
    f"{SEP}│{END} "
    f"{quota('WK', seven_day)}"
)

print(line1 + "\n" + line2)
