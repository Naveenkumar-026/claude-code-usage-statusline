#!/usr/bin/env bash
set -euo pipefail

APP_NAME="claude-code-usage-statusline"
CLAUDE_DIR="$HOME/.claude"
BACKUP_DIR="$CLAUDE_DIR/statusline-backups"
TARGET_SCRIPT="$CLAUDE_DIR/$APP_NAME.py"
WRAPPER="$CLAUDE_DIR/statusline.sh"
SETTINGS="$CLAUDE_DIR/settings.json"
STAMP="$(date +%Y%m%d-%H%M%S)"

if ! command -v python3 >/dev/null 2>&1; then
  echo "Error: python3 is required."
  exit 1
fi

mkdir -p "$CLAUDE_DIR" "$BACKUP_DIR"

if [ -f "$SETTINGS" ]; then
  cp "$SETTINGS" "$BACKUP_DIR/settings.json.$STAMP.bak"
fi

if [ -f "$WRAPPER" ]; then
  cp "$WRAPPER" "$BACKUP_DIR/statusline.sh.$STAMP.bak"
fi

cp ./claude-statusline.py "$TARGET_SCRIPT"
chmod +x "$TARGET_SCRIPT"

cat > "$WRAPPER" <<EOF2
#!/usr/bin/env bash
python3 "$TARGET_SCRIPT"
EOF2

chmod +x "$WRAPPER"

python3 - <<PY
import json
from pathlib import Path

settings_path = Path("$SETTINGS")
settings_path.parent.mkdir(parents=True, exist_ok=True)

if settings_path.exists() and settings_path.read_text().strip():
    try:
        data = json.loads(settings_path.read_text())
    except Exception:
        data = {}
else:
    data = {}

data["statusLine"] = {
    "type": "command",
    "command": "~/.claude/statusline.sh",
    "padding": 1,
    "refreshInterval": 2
}

settings_path.write_text(json.dumps(data, indent=2) + "\n")
PY

echo
echo "Installed Claude Code Usage Statusline."
echo
echo "Restart Claude Code:"
echo "  pkill -f claude 2>/dev/null || true"
echo "  claude"
echo
echo "Backups saved in:"
echo "  $BACKUP_DIR"
