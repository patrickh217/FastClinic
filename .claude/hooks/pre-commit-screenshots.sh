#!/usr/bin/env bash
# Blocks `git commit` when UI files are staged and no recent screenshot exists.
# Adapted from medbackend-frontend/.claude/hooks/pre-commit-tests.sh.
# Exit 0 = allow, exit 2 = hard block.

COMMAND=$(cat /dev/stdin | jq -r '.tool_input.command // empty')

echo "$COMMAND" | grep -q 'git commit' || exit 0

STAGED=$(git diff --cached --name-only 2>/dev/null)
UI_CHANGED=$(echo "$STAGED" | grep -E '\.(py|html|css|js)$' | grep -v 'test_' | head -1)
[ -z "$UI_CHANGED" ] && exit 0

# Routes and components render HTML; services and handlers do not.
echo "$STAGED" | grep -qE '^(routes|components|app\.py|static/)' || exit 0

find .screenshots -name '*.png' -mmin -60 2>/dev/null | grep -q . && exit 0

>&2 cat <<'BLOCK'
+----------------------------------------------------------+
|  UI VISUAL REVIEW REQUIRED - COMMIT BLOCKED               |
+----------------------------------------------------------+

Staged changes touch routes/, components/, app.py or static/,
but .screenshots/ has no PNG newer than 60 minutes.

  1. python app.py            (serves on :5005)
  2. drive it with Playwright MCP, save PNGs to .screenshots/
     naming: <feature>-<NN>-<description>.png
  3. commit again

Starting the dev server is a SAFE LOCAL ACTION.
Do it yourself - never wait for the user to do it.
BLOCK
exit 2
