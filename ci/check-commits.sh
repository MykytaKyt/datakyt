#!/usr/bin/env bash
# Check commit messages in a git revision range, e.g. origin/develop..HEAD.
#
# Fails when a message
#   - carries AI attribution (Co-Authored-By an AI vendor, session links,
#     "Generated with" lines), or
#   - has a subject that is not a Conventional Commit of at most 72 characters.
# Merge commits are skipped.
set -euo pipefail

range="${1:?usage: ci/check-commits.sh <revision-range>}"

attribution_re='Co-Authored-By:.*anthropic|Claude-Session|Generated with'
subject_re='^(feat|fix|refactor|test|docs|ci|build|chore)(\([a-z0-9._/-]+\))?!?: [^ ].*$'

failed=0
while read -r sha; do
  [ -z "$sha" ] && continue
  message="$(git log -1 --format=%B "$sha")"
  subject="$(git log -1 --format=%s "$sha")"
  if grep -qiE "$attribution_re" <<<"$message"; then
    echo "::error::$sha: commit message contains AI attribution (Co-Authored-By/Claude-Session/Generated with)"
    failed=1
  fi
  if ! grep -qE "$subject_re" <<<"$subject"; then
    echo "::error::$sha: subject is not a Conventional Commit: $subject"
    failed=1
  elif [ "${#subject}" -gt 72 ]; then
    echo "::error::$sha: subject is longer than 72 characters (${#subject})"
    failed=1
  fi
done < <(git rev-list --no-merges "$range")

if [ "$failed" -eq 0 ]; then
  echo "commit messages in $range are fine"
fi
exit "$failed"
