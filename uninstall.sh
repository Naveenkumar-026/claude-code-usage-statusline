#!/usr/bin/env bash
set -euo pipefail

CLAUDE_DIR="$HOME/.claude"
SETTINGS="$CLAUDE_DIR/settings.json"

python3 - <<PY
import json
from pathlib import Path

settings_path = Path("$SETTINGS")

if settings_path.exists() and settings_path.read_text().strip():
    try:
        data = json.loads(settings_path.read_text())
    except Exception:
        data = {}
else:
    data = {}

status = data.get("statusLine", {})
cmd = status.get("command", "") if isinstance(status, dict) else ""

if "statusline.sh" in cmd or "claude-code-usage-statusline" in cmd:
    data.pop("statusLine", None)
    settings_path.write_text(json.dumps(data, indent=2) + "\n")
    print("Removed statusLine from Claude Code settings.")
else:
    print("No matching statusLine entry found. Nothing changed.")
PY

echo "Installed files were left in ~/.claude for safety."
echo "Remove manually if needed:"
echo "  rm -f ~/.claude/statusline.sh ~/.claude/claude-code-usage-statusline.py"
