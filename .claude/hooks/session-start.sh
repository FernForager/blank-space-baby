#!/bin/bash
# Cloud sessions only: install what the screenshot and play-sweep tools need.
#  - Playwright for Python, at the version whose Chromium is preinstalled. The workspace's own playwright-core (named by the
#    .links file under PLAYWRIGHT_BROWSERS_PATH) says which: 1.56.0 with chromium-1194 on Oct 22, 2026, 1.63.0 with
#    chromium-1243 on Oct 30 (a fixed pin of 1.56.0 then found no browser, the audit's open item). Never run "playwright install".
#  - The game's two fonts, so screenshots render in Press Start 2P and Pixelify Sans even when Google Fonts is blocked.
set -euo pipefail

if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

WANT=1.56.0   # the pin that matched the Oct 22 workspace, used only when no playwright-core is found
for f in "${PLAYWRIGHT_BROWSERS_PATH:-/opt/pw-browsers}"/.links/*; do
  [ -f "$f" ] || continue
  P="$(cat "$f")/package.json"
  if [ -f "$P" ]; then
    V=$(python3 -c "import json, sys; print(json.load(open(sys.argv[1]))['version'])" "$P" 2>/dev/null || true)
    [ -n "$V" ] && WANT="$V"
  fi
done
if ! python3 -c "import importlib.metadata as m, sys; sys.exit(m.version('playwright') != sys.argv[1])" "$WANT" 2>/dev/null; then
  pip install -q "playwright==$WANT" >/dev/null 2>&1 || pip install -q --break-system-packages "playwright==$WANT"
fi

# Each font downloads to a .part file and is renamed only once it arrives whole, so a failed download
# stops the hook with an error instead of leaving a broken .ttf that would be skipped from then on
get() {
  [ -s "$1" ] && return 0
  curl -fsSL -o "$1.part" "$2"
  mv "$1.part" "$1"
}
mkdir -p "$HOME/.fonts"
cd "$HOME/.fonts"
get PressStart2P-Regular.ttf https://raw.githubusercontent.com/google/fonts/main/ofl/pressstart2p/PressStart2P-Regular.ttf
get PixelifySans.ttf "https://raw.githubusercontent.com/google/fonts/main/ofl/pixelifysans/PixelifySans%5Bwght%5D.ttf"
fc-cache -f >/dev/null 2>&1 || true
