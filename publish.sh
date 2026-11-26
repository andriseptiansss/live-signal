#!/usr/bin/env bash
# Publish website Live Signal ke GitHub Pages.
# Pemakaian:
#   GITHUB_REPO="https://github.com/<username>/live-signal.git" \
#   GITHUB_TOKEN="<personal access token>" ./publish.sh
# Token butuh scope: repo (public repo cukup: public_repo).
# Tanpa GITHUB_REPO / GITHUB_TOKEN, script hanya menjalankan sync (mode cek).
set -euo pipefail
cd "$(dirname "$0")"

echo "== sync signals.json dari tracker =="
python3 sync-signals.py

if [ -z "${GITHUB_REPO:-}" ] || [ -z "${GITHUB_TOKEN:-}" ]; then
  echo "SKIP publish: set GITHUB_REPO dan GITHUB_TOKEN untuk push ke GitHub."
  echo "File sudah siap di folder ini (index.html + signals.json)."
  exit 0
fi

if [ ! -d .git ]; then
  git init -b main
  git remote add origin "$GITHUB_REPO"
fi

# URL push pakai token (token tidak dicetak ke log)
AUTH_URL="${GITHUB_REPO/https:\/\//https:\/\/x-access-token:${GITHUB_TOKEN}@}"
git add index.html signals.json sync-signals.py publish.sh README.md
git -c user.name="live-signal-bot" -c user.email="live-signal-bot@local" \
  commit -m "Update live signal $(date '+%Y-%m-%d %H:%M WIB')" || echo "tidak ada perubahan untuk commit"
git push "$AUTH_URL" main
echo "OK: ter-publish. Aktifkan GitHub Pages sekali saja di repo Settings > Pages > Branch main."
