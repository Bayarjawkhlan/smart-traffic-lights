#!/usr/bin/env bash
# Downloads the Peace Avenue corridor (State Department Store → Baga Toiruu east) from Overpass.
set -euo pipefail
BBOX="47.9128,106.9030,47.9218,106.9280"
OUT="$(dirname "$0")/../data/corridor.osm.xml"
QUERY="[out:xml][timeout:90];
(
  way[highway~\"^(trunk|trunk_link|primary|primary_link|secondary|secondary_link|tertiary|tertiary_link|unclassified|residential|living_street|footway|pedestrian|path|steps|crossing)$\"]($BBOX);
);
(._;>;);
out body;"
curl -sS --fail -A "corridor-sim/0.1" --data-urlencode "data=$QUERY" https://overpass-api.de/api/interpreter -o "$OUT"
echo "wrote $OUT ($(wc -c <"$OUT") bytes)"
