#!/usr/bin/env bash
# Download model-v1 / model-v2 from the GitHub Release, verify the checksum recorded in
# models/<v>/model.sha256, and upload the files to the bucket "models" under models/<v>/.
set -euo pipefail
cd "$(dirname "$0")/.."
REPO="${REPO:-$(git config --get remote.origin.url | sed -E 's#(git@github.com:|https://github.com/)##; s#\.git$##')}"
TAG="${RELEASE_TAG:-v1}"
for V in v1 v2; do
  if scripts/with_s3.sh python3 scripts/s3_tool.py has-prefix models "$V/"; then echo "models/$V already in bucket"; continue; fi
  mkdir -p dist "artifacts/dl-$V"
  [ -f "dist/model-$V.tar.gz" ] || curl -fL "https://github.com/$REPO/releases/download/$TAG/model-$V.tar.gz" -o "dist/model-$V.tar.gz"
  EXPECT="$(cut -d' ' -f1 "models/$V/model.sha256")"
  GOT="$(sha256sum "dist/model-$V.tar.gz" | cut -d' ' -f1)"
  [ "$EXPECT" = "$GOT" ] || { echo "checksum mismatch for $V"; exit 1; }
  tar -xzf "dist/model-$V.tar.gz" -C "artifacts/dl-$V"
  scripts/with_s3.sh python3 scripts/s3_tool.py put-dir models "$V" "artifacts/dl-$V"
  scripts/with_s3.sh python3 scripts/s3_tool.py put-file models "$V/model.sha256" "models/$V/model.sha256"
done
