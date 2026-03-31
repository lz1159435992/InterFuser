#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
OUT_DIR="${1:-$ROOT_DIR/release_artifacts}"
TAG="${2:-snapshot}"

mkdir -p "$OUT_DIR"

TMP_DIR="$OUT_DIR/.bundle_tmp_${TAG}"
rm -rf "$TMP_DIR"
mkdir -p "$TMP_DIR"

copy_tree() {
  local src="$1"
  local dst="$2"
  if [[ -d "$src" ]]; then
    mkdir -p "$(dirname "$dst")"
    rsync -a "$src/" "$dst/"
  fi
}

echo "[bundle] preparing tree at $TMP_DIR"

copy_tree "$ROOT_DIR/configs" "$TMP_DIR/configs"
copy_tree "$ROOT_DIR/docs" "$TMP_DIR/docs"
copy_tree "$ROOT_DIR/environment" "$TMP_DIR/environment"
copy_tree "$ROOT_DIR/experiments" "$TMP_DIR/experiments"
copy_tree "$ROOT_DIR/provenance" "$TMP_DIR/provenance"
copy_tree "$ROOT_DIR/results/processed" "$TMP_DIR/results/processed"
copy_tree "$ROOT_DIR/results/tables" "$TMP_DIR/results/tables"
copy_tree "$ROOT_DIR/results/figures" "$TMP_DIR/results/figures"
copy_tree "$ROOT_DIR/scripts" "$TMP_DIR/scripts"
copy_tree "$ROOT_DIR/third_party" "$TMP_DIR/third_party"

cp -f "$ROOT_DIR/README.md" "$TMP_DIR/README.md"
cp -f "$ROOT_DIR/CITATION.cff" "$TMP_DIR/CITATION.cff"
cp -f "$ROOT_DIR/CONTRIBUTING.md" "$TMP_DIR/CONTRIBUTING.md"

ARCHIVE="$OUT_DIR/intuitiontester-code-${TAG}.tar.gz"
echo "[bundle] creating $ARCHIVE"
tar -C "$TMP_DIR" -czf "$ARCHIVE" .

echo "[bundle] generating checksums"
(
  cd "$OUT_DIR"
  sha256sum "$(basename "$ARCHIVE")" > "SHA256SUMS-${TAG}.txt"
)

MANIFEST="$OUT_DIR/MANIFEST-${TAG}.csv"
echo "path,bytes,sha256" > "$MANIFEST"
find "$TMP_DIR" -type f | while read -r f; do
  rel="${f#$TMP_DIR/}"
  bytes="$(stat -c %s "$f")"
  sha="$(sha256sum "$f" | awk '{print $1}')"
  echo "$rel,$bytes,$sha" >> "$MANIFEST"
done

rm -rf "$TMP_DIR"
echo "[ok] bundle ready:"
echo "  - $ARCHIVE"
echo "  - $OUT_DIR/SHA256SUMS-${TAG}.txt"
echo "  - $MANIFEST"
