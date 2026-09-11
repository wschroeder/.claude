#!/bin/bash
# Render a page headless and return as soon as the output is written.
#
# Chrome does not exit after writing its screenshot or DOM dump, so waiting on
# the process costs whatever timeout it was given — measured at 120 to 152
# seconds per render for work that takes about two.
set -u

CHROME="${CHROME:-/Applications/Google Chrome.app/Contents/MacOS/Google Chrome}"
CHROME_MIN_WIDTH=500
BACKSTOP=120

WIDTH=""
HEIGHT=1200
OUT=""
URL=""
MODE=screenshot
FONTS=0
SCHEME=light

die() { echo "render.sh: $*" >&2; exit 2; }

# The probe copy lands in the caller's directory, Chrome outlives this script,
# and its throwaway profile is about 3MB a render.
cleanup() {
  [ -n "${probed_copy:-}" ] && rm -f "$probed_copy"
  [ -n "${chrome_pid:-}" ] && kill "$chrome_pid" 2>/dev/null
  [ -n "${profile_dir:-}" ] && rm -rf "$profile_dir"
  return 0
}
trap cleanup EXIT INT TERM

while [ $# -gt 0 ]; do
  case "$1" in
    --width)  WIDTH="$2";  shift 2 ;;
    --height) HEIGHT="$2"; shift 2 ;;
    --out)    OUT="$2";    shift 2 ;;
    --url)    URL="$2";    shift 2 ;;
    --mode)   MODE="$2";   shift 2 ;;
    --fonts)  FONTS=1;      shift 1 ;;
    --color-scheme) SCHEME="$2"; shift 2 ;;
    *) die "unknown argument: $1" ;;
  esac
done

case "$WIDTH" in
  ""|*[!0-9]*) die "--width must be a whole number of CSS pixels, not ${WIDTH:-<missing>}" ;;
esac
case "$HEIGHT" in
  ""|*[!0-9]*) die "--height must be a whole number of CSS pixels, not ${HEIGHT:-<missing>}" ;;
esac

if [ "$WIDTH" -lt "$CHROME_MIN_WIDTH" ]; then
  echo "render.sh: --width $WIDTH is below Chrome's ${CHROME_MIN_WIDTH}px minimum window width." >&2
  echo "render.sh: Chrome would clamp it to ${CHROME_MIN_WIDTH} and report a pass for a page you did not test." >&2
  echo "render.sh: put the page in an iframe of that width inside a wider window instead." >&2
  exit 2
fi

[ -n "$OUT" ] || die "--out is required"
[ -n "$URL" ] || die "--url is required"
[ -x "$CHROME" ] || die "no Chrome at $CHROME (set CHROME to override)"

case "$MODE" in
  screenshot) capture=(--screenshot="$OUT") ;;
  dom)        capture=(--dump-dom) ;;
  *) die "--mode must be screenshot or dom, not $MODE" ;;
esac

# Chrome flips prefers-color-scheme for --force-dark-mode and leaves every
# computed colour alone, so a page with no dark rules renders identically under
# it. That is what makes the flag safe to measure colours through.
case "$SCHEME" in
  light) scheme_flag="" ;;
  dark)  scheme_flag="--force-dark-mode" ;;
  *) die "--color-scheme must be light or dark, not $SCHEME" ;;
esac

if [ "$FONTS" = 1 ] && [ "$MODE" != dom ]; then
  die "--fonts needs --mode dom; run a dom pass for the count, then the screenshot"
fi

case "$URL" in
  [a-z]*:*) ;;
  *) [ -e "$URL" ] || die "no such file: $URL"
     URL="file://$(cd "$(dirname "$URL")" && pwd)/$(basename "$URL")" ;;
esac

render_url="$URL"
probed_copy=""
if [ "$FONTS" = 1 ]; then
  # The copy sits beside the original so its relative URLs still resolve.
  probed_copy="$(dirname "${URL#file://}")/.render-probe-$$.html"
  if ! python3 - "${URL#file://}" "$probed_copy" <<'INJECT'
import sys
src, dst = sys.argv[1], sys.argv[2]
page = open(src, encoding="utf-8", errors="replace").read()
# Set the count synchronously so the attribute is there however early Chrome
# serializes, then correct it once the faces have settled.
probe = (
    '<script id="__renderProbe">'
    "(function(){function snap(){var got=0;"
    "document.fonts.forEach(function(f){if(f.status==='loaded')got++});"
    "document.documentElement.setAttribute("
    "'data-render-fonts',got+'/'+document.fonts.size)}"
    "snap();document.fonts.ready.then(snap)})();"
    "</script>"
)
marker = "</body>"
out = page.replace(marker, probe + marker, 1) if marker in page else page + probe
open(dst, "w", encoding="utf-8").write(out)
INJECT
  then
    die "could not write the font probe beside $URL"
  fi
  render_url="file://$probed_copy"
fi

profile_dir=$(mktemp -d "${TMPDIR:-/tmp}/render-sh.XXXXXX")

rm -f "$OUT"
started=$(date +%s)

# In dom mode Chrome writes the page to stdout, so the redirect is what fills
# $OUT; in screenshot mode Chrome writes $OUT itself.
if [ "$MODE" = dom ]; then dom_target="$OUT"; else dom_target=/dev/null; fi

timeout "$BACKSTOP" "$CHROME" \
  --headless=new --disable-gpu \
  --window-size="$WIDTH,$HEIGHT" \
  --user-data-dir="$profile_dir" \
  --allow-file-access-from-files `# iframes of local files stay blank without it` \
  --virtual-time-budget=15000 \
  $scheme_flag \
  "${capture[@]}" \
  "$render_url" >"$dom_target" 2>/dev/null &
chrome_pid=$!

size=0
stable=0
while kill -0 "$chrome_pid" 2>/dev/null; do
  if [ -s "$OUT" ]; then
    now=$(wc -c < "$OUT")
    if [ "$now" = "$size" ]; then
      stable=$((stable + 1))
      [ "$stable" -ge 2 ] && break
    else
      stable=0
      size=$now
    fi
  fi
  sleep 0.25
done

kill "$chrome_pid" 2>/dev/null
wait "$chrome_pid" 2>/dev/null

[ -s "$OUT" ] || die "Chrome wrote no output to $OUT"

fonts_field=""
if [ "$FONTS" = 1 ]; then
  fonts_field=" fonts=$(python3 - "$OUT" <<'EXTRACT'
import re, sys
path = sys.argv[1]
dom = open(path, encoding="utf-8", errors="replace").read()
found = re.search(r'data-render-fonts="(\d+/\d+)"', dom)
print(found.group(1) if found else "unknown")
# Hand back the page as built, not the page as probed.
dom = re.sub(r'<script id="__renderProbe">.*?</script>', "", dom, flags=re.S)
dom = re.sub(r'\s*data-render-fonts="[\d/]+"', "", dom)
open(path, "w", encoding="utf-8").write(dom)
EXTRACT
)"
fi

elapsed=$(( $(date +%s) - started ))
echo "render: ok out=$OUT bytes=$(wc -c < "$OUT" | tr -d ' ') width=$WIDTH elapsed=${elapsed}s$fonts_field"
