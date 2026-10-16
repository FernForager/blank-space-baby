#!/bin/bash
# Cloud sessions only: install what the screenshot and play-sweep tools need.
#  - Playwright for Python, pinned to match the preinstalled Chromium (chromium-1194). Never run "playwright install".
#  - The game's two fonts, so screenshots render in Press Start 2P and Pixelify Sans even when Google Fonts is blocked.
set -euo pipefail

if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

if ! python3 -c "import playwright, importlib.metadata as m; assert m.version('playwright') == '1.56.0'" 2>/dev/null; then
  pip install -q "playwright==1.56.0" >/dev/null 2>&1 || pip install -q --break-system-packages "playwright==1.56.0"
fi

mkdir -p "$HOME/.fonts"
cd "$HOME/.fonts"
[ -f PressStart2P-Regular.ttf ] || curl -sSLO https://raw.githubusercontent.com/google/fonts/main/ofl/pressstart2p/PressStart2P-Regular.ttf
[ -f PixelifySans.ttf ] || curl -sSL -o PixelifySans.ttf "https://raw.githubusercontent.com/google/fonts/main/ofl/pixelifysans/PixelifySans%5Bwght%5D.ttf"
fc-cache -f >/dev/null 2>&1 || true
