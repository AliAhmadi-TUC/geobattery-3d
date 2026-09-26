#!/usr/bin/env bash
# Switch the /poster/ page of the site between the waiting page and the real interactive poster.
#
#   tools/poster.sh publish            show the interactive poster (restored from branch poster-hold)
#   tools/poster.sh hold               show the "opens after the conference" waiting page again
#   tools/poster.sh status             say which page the site's main branch currently carries
#   add --dry-run to publish/hold      do everything except commit and push, then undo
#
# The same script runs behind the GitHub "Poster" workflow button (--ci) and the desktop shortcut.
# GitHub Pages deploys from main; the live page changes about a minute after the push.
set -euo pipefail

ACTION="${1:-status}"; shift || true
DRY=0; CI=0
for a in "$@"; do case "$a" in --dry-run) DRY=1 ;; --ci) CI=1 ;; *) echo "unknown option: $a" >&2; exit 2 ;; esac; done
[ "$ACTION" = "dry-run" ] && { ACTION=publish; DRY=1; }

cd "$(git rev-parse --show-toplevel)"
SITE="https://aliahmadi-tuc.github.io/geobattery-3d/poster/"
LIVE_MARK='Geobattery · the interactive poster'
HOLD_MARK='the interactive poster opens after the conference'

state() { if grep -qF "$LIVE_MARK" poster/index.html; then echo live;
          elif grep -qF "$HOLD_MARK" poster/index.html; then echo hold; else echo unknown; fi; }

if [ "$CI" = 1 ]; then          # commits made by the button are authored as the site's owner, not a bot
  git config user.name  "Ali Ahmadi"
  git config user.email "aa30@tu-clausthal.de"
fi

git fetch -q origin main poster-hold
if [ "$CI" = 0 ]; then
  if ! git diff --quiet -- poster/ || ! git diff --cached --quiet -- poster/; then
    echo "poster/ has uncommitted local changes; commit or discard them first." >&2; exit 1; fi
  git checkout -q main
  git merge -q --ff-only origin/main
fi

NOW="$(state)"
echo "main currently carries: $NOW"
[ "$ACTION" = status ] && exit 0

# a previous run may have committed but failed to push (e.g. no network): push that first
if [ "$CI" = 0 ] && [ "$DRY" = 0 ] && [ "$(git rev-list --count origin/main..HEAD)" -gt 0 ]; then
  echo "Pushing $(git rev-list --count origin/main..HEAD) earlier commit(s) that never reached GitHub..."
  git push -q origin HEAD:main
fi

case "$ACTION" in
  publish)
    [ "$NOW" = live ] && { echo "The interactive poster is already published. Nothing to do."; exit 0; }
    git checkout -q origin/poster-hold -- poster/
    MSG="Publish the interactive poster" ;;
  hold)
    [ "$NOW" = hold ] && { echo "The waiting page is already up. Nothing to do."; exit 0; }
    git rm -q -r --cached poster/ >/dev/null
    rm -rf poster/ && mkdir -p poster && cp tools/poster-holding.html poster/index.html
    git add poster/
    MSG="Hold the interactive poster offline" ;;
  *) echo "usage: tools/poster.sh publish|hold|status [--dry-run]" >&2; exit 2 ;;
esac

git add -A poster/
echo "after the switch it would carry: $(state)"
git --no-pager diff --cached --stat -- poster/
if [ "$(state)" != "$([ "$ACTION" = publish ] && echo live || echo hold)" ]; then
  echo "Safety check failed: poster/index.html is not the expected page. Undoing." >&2
  git restore --staged --worktree --source=HEAD -- poster/ 2>/dev/null || git checkout -q HEAD -- poster/
  exit 1
fi

if [ "$DRY" = 1 ]; then
  git restore --staged --worktree --source=HEAD -- poster/ 2>/dev/null || { git reset -q -- poster/; git checkout -q HEAD -- poster/; }
  git clean -fdq -- poster/
  echo "DRY RUN: nothing was committed or pushed. main still carries: $(state)"
  exit 0
fi

git commit -q -m "$MSG"
git push -q origin HEAD:main
echo "Pushed: $MSG. GitHub Pages will update $SITE in about a minute."

# local runs: wait for the live page to change (the site caches pages for up to 10 minutes,
# so a query string that is new every time is used to see past the cache)
if [ "$CI" = 0 ] && command -v curl >/dev/null; then
  WANT=$([ "$ACTION" = publish ] && echo "$LIVE_MARK" || echo "$HOLD_MARK")
  for i in $(seq 1 24); do
    sleep 10
    if curl -fsSL "${SITE}?v=$(date +%s)" 2>/dev/null | grep -qF "$WANT"; then
      echo "LIVE: $SITE now shows the $([ "$ACTION" = publish ] && echo 'interactive poster' || echo 'waiting page')."
      echo "(Browsers that opened it in the last 10 minutes may need a refresh.)"; exit 0; fi
  done
  echo "Not visible yet after 4 minutes; it usually appears within a few more. Check $SITE"
fi
