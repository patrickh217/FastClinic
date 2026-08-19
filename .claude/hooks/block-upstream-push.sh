#!/usr/bin/env bash
# Hard-blocks any push that would reach the PUBLIC upstream repo.
# This clone shipped with `origin` pointing at predictivelabsai/FastClinic, so the
# hazard is real rather than theoretical. Exit 0 = allow, exit 2 = hard block.

COMMAND=$(cat /dev/stdin | jq -r '.tool_input.command // empty')

echo "$COMMAND" | grep -q 'git push' || exit 0

# Explicit remote name or URL on the command line.
if echo "$COMMAND" | grep -qiE 'push[^|;&]*(upstream|predictivelabsai)'; then
  >&2 echo "BLOCKED: that push targets the public upstream repo (predictivelabsai/FastClinic)."
  >&2 echo "Push to 'origin' (patrickh217/FastClinic) instead."
  exit 2
fi

# A bare `git push` with no remote: resolve what it would actually use.
if echo "$COMMAND" | grep -qE 'git push\s*$'; then
  TARGET=$(git rev-parse --abbrev-ref '@{push}' 2>/dev/null)
  if [ -z "$TARGET" ]; then
    >&2 echo "BLOCKED: bare 'git push' with no upstream tracking - no default destination."
    >&2 echo "Be explicit: git push -u origin \$(git branch --show-current)"
    exit 2
  fi
  REMOTE="${TARGET%%/*}"
  if git remote get-url "$REMOTE" 2>/dev/null | grep -qi 'predictivelabsai'; then
    >&2 echo "BLOCKED: '$REMOTE' resolves to the public upstream repo."
    exit 2
  fi
fi

exit 0
