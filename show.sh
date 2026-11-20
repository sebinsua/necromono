#!/bin/sh
# Build NecroMono, install it for this user, and open a Ghostty window set in it.
#   ./show.sh        build, install, open at your usual Ghostty font size
#   ./show.sh 20     same, at 20pt
set -e
cd "$(dirname "$0")"
ROOT="$(pwd)"
SIZE="${1:-}"

.venv/bin/python -m necromono.build
cp fonts/NecroMono-*.ttf "$HOME/Library/Fonts/"

# close the previous preview window (only instances started with this config file)
pkill -f "config-file=$ROOT/preview/ghostty.conf" 2>/dev/null || true
sleep 0.5

open -na /Applications/Ghostty.app --args \
  "--config-file=$ROOT/preview/ghostty.conf" \
  "--font-family=" "--font-family=${FONT:-NecroMono}" \
  ${SIZE:+"--font-size=$SIZE"} \
  "--command=/bin/sh -c 'cat \"$ROOT/preview/sample.txt\" \"$ROOT/preview/session.txt\"; exec \"\${SHELL:-/bin/zsh}\" -i'"
echo "opened Ghostty preview at ${SIZE:-your usual size}${SIZE:+pt}"
