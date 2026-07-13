#!/bin/sh
set -eu

target=${1:-AGENTS.md}
start='<!-- vibecode-protector:start -->'
end='<!-- vibecode-protector:end -->'

case "$target" in
  */) printf '%s\n' "error: target must be a file" >&2; exit 2 ;;
esac

directory=$(dirname "$target")
if [ ! -d "$directory" ]; then
  printf '%s\n' "error: parent directory does not exist: $directory" >&2
  exit 2
fi

if [ -f "$target" ]; then
  start_count=$(grep -Fxc "$start" "$target" || true)
  end_count=$(grep -Fxc "$end" "$target" || true)
  if { [ "$start_count" -ne 0 ] || [ "$end_count" -ne 0 ]; } && \
     { [ "$start_count" -ne 1 ] || [ "$end_count" -ne 1 ]; }; then
    printf '%s\n' "error: malformed or duplicate VibeCode Protector markers in $target" >&2
    exit 3
  fi
fi

tmp=$(mktemp "$directory/.vibecode-protector.XXXXXX")
trap 'rm -f "$tmp"' EXIT HUP INT TERM

if [ -f "$target" ]; then
  mode=$(stat -f '%Lp' "$target" 2>/dev/null || stat -c '%a' "$target")
  chmod "$mode" "$tmp"
else
  chmod 644 "$tmp"
fi

if [ -f "$target" ]; then
  awk -v start="$start" -v end="$end" '
    $0 == start {inside = 1; next}
    $0 == end {inside = 0; next}
    !inside {print}
  ' "$target" > "$tmp"
fi

while [ -s "$tmp" ] && [ "$(tail -c 1 "$tmp" | wc -l | tr -d ' ')" = "0" ]; do
  printf '\n' >> "$tmp"
done

cat >> "$tmp" <<'EOF'
<!-- vibecode-protector:start -->
## VibeCode Protector

Use `$vibecoding-protector` as the default workflow for every implementation,
bug fix, refactoring, or architectural decision in this repository. The user
does not need to invoke the skill explicitly.

At the beginning of every turn in which the workflow is active, write exactly:

*VibeCode Protector enabled*

Run its preflight before planning changes. Do not implement while technical
decisions, solution critique, slice scope, validation, or required human
authorization remain pending.
<!-- vibecode-protector:end -->
EOF

mv "$tmp" "$target"
trap - EXIT HUP INT TERM
printf '%s\n' "VibeCode Protector enabled in $target"
