#!/usr/bin/env bash
set -euo pipefail

dest="$(cd "$(dirname "$0")/.." && pwd)/videos"
mkdir -p "$dest"

# Wikimedia rejects requests without a descriptive User-Agent.
ua="smart-traffic-signals-vision/0.1 (sample video fetch)"

fetch() {
  local name="$1" url="$2"
  if [[ -s "$dest/$name" ]]; then
    echo "have  $name"
    return
  fi
  echo "fetch $name"
  curl -fsSL --retry 3 -A "$ua" -o "$dest/$name.part" "$url"
  mv "$dest/$name.part" "$dest/$name"
}

# Licences and authors are listed in videos/SOURCES.md.
fetch tyumen-respubliki-ordzhonikidze.webm \
  "https://upload.wikimedia.org/wikipedia/commons/8/8f/Kruci%C4%9Do_de_stratoj_Respubliko_kaj_Or%C4%9Donikidze_%28Tjumeno%29.webm"
fetch toronto-yonge-dundas.webm \
  "https://upload.wikimedia.org/wikipedia/commons/d/d2/DiagonalCrosswalkYongeDundas.webm"
