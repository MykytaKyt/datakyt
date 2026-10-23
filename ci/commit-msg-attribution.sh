#!/usr/bin/env bash
# commit-msg hook: reject AI attribution lines in the message being committed.
set -euo pipefail
if grep -v '^#' "$1" | grep -qiE 'Co-Authored-By:.*anthropic|Claude-Session|Generated with'; then
  echo "commit message contains AI attribution (Co-Authored-By/Claude-Session/Generated with);" >&2
  echo "remove it - the human developer is the author. See CONTRIBUTING.md." >&2
  exit 1
fi
