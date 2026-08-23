#!/usr/bin/env bash
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
#
# Builds a fresh 295-document workshop graph in disposable local Neo4j, then
# writes a candidate dump for review. The five Module 1 documents are omitted
# by prepare_graph.py --mode prebuilt and remain available for live extraction.
#
# Requires Docker, uv, AWS credentials, and Bedrock model access. This script
# never connects to Aura and never replaces static/neo4j-hotel-graph.dump.
#
# Usage: setup/build_prebuilt_graph.sh
# Output: setup/neo4j-hotel-graph-prebuilt.dump

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
IMAGE="${NEO4J_IMAGE:-neo4j:latest}"
VOLUME="neo4j-prebuilt-$$"
CONTAINER="neo4j-prebuilt-$$"
PASSWORD="prebuilt-local-$$"
OUTPUT="$REPO_ROOT/setup/neo4j-hotel-graph-prebuilt.dump"

if [[ -e "$OUTPUT" ]]; then
  echo "Refusing to overwrite existing candidate: $OUTPUT" >&2
  echo "Move or delete it after review, then run this script again." >&2
  exit 1
fi

SCRATCH="$(mktemp -d)"

cleanup() {
  docker rm -f "$CONTAINER" >/dev/null 2>&1 || true
  docker volume rm "$VOLUME" >/dev/null 2>&1 || true
  rm -rf "$SCRATCH"
}
trap cleanup EXIT

mkdir -p "$SCRATCH/dumps-out"
docker volume create "$VOLUME" >/dev/null

echo "Starting disposable Neo4j with $IMAGE..."
docker run -d --name "$CONTAINER" \
  -v "$VOLUME:/data" \
  -p 127.0.0.1::7687 \
  -e NEO4J_AUTH="neo4j/$PASSWORD" \
  "$IMAGE" >/dev/null

BOLT_ENDPOINT="$(docker port "$CONTAINER" 7687/tcp)"
BOLT_PORT="${BOLT_ENDPOINT##*:}"
if [[ ! "$BOLT_PORT" =~ ^[0-9]+$ ]]; then
  echo "Could not determine the disposable Neo4j Bolt port: $BOLT_ENDPOINT" >&2
  exit 1
fi

for _ in $(seq 1 60); do
  if docker exec "$CONTAINER" cypher-shell \
    -u neo4j -p "$PASSWORD" "RETURN 1" >/dev/null 2>&1; then
    break
  fi
  sleep 1
done

docker exec "$CONTAINER" cypher-shell \
  -u neo4j -p "$PASSWORD" "RETURN 1" >/dev/null

echo "Building the 295-document prebuilt graph..."
(
  cd "$REPO_ROOT/notebooks/02-connected-context"
  NEO4J_URI="bolt://localhost:$BOLT_PORT" \
  NEO4J_USERNAME=neo4j \
  NEO4J_PASSWORD="$PASSWORD" \
  NEO4J_DATABASE=neo4j \
  uv run --project ../workshop python prepare_graph.py --mode prebuilt --rebuild
)

# Module 1 deliberately creates these indexes after participants add their five
# documents, so the release artifact must not contain them.
docker exec "$CONTAINER" cypher-shell -u neo4j -p "$PASSWORD" \
  "DROP INDEX hotel_chunk_embeddings IF EXISTS"
docker exec "$CONTAINER" cypher-shell -u neo4j -p "$PASSWORD" \
  "DROP INDEX hotel_chunk_fulltext IF EXISTS"

echo "Stopping Neo4j and creating the candidate dump..."
docker stop "$CONTAINER" >/dev/null
docker run --rm \
  -v "$VOLUME:/data" \
  -v "$SCRATCH/dumps-out:/dumps-out" \
  "$IMAGE" \
  neo4j-admin database dump --to-path=/dumps-out neo4j

cp "$SCRATCH/dumps-out/neo4j.dump" "$OUTPUT"
echo "Done: $OUTPUT"
