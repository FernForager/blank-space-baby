#!/bin/bash
# Cloud sessions only: install what the screenshot and play-sweep tools need.
#  - Playwright for Python, pinned to match the preinstalled Chromium (chromium-1194). Never run "playwright install".
# The game's fonts live in docs/fonts/ and the test tools serve them from there (tools/docsroute.py), so nothing else is needed.
set -euo pipefail

if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

if ! python3 -c "import playwright, importlib.metadata as m; assert m.version('playwright') == '1.56.0'" 2>/dev/null; then
  pip install -q "playwright==1.56.0" >/dev/null 2>&1 || pip install -q --break-system-packages "playwright==1.56.0"
fi
