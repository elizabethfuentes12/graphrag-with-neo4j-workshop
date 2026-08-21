#!/usr/bin/env bash
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
#
# Rebuilds static/neo4j-hotel-graph.dump with the 2026-08-18 live-Cypher repair
# baked in, so future participants start from a graph that already has
# Document.source_filename, Hotel.hotel_id, and the demo-06-maximum-guests Rule
# instead of needing setup/repair_dump.py run against a fresh restore.
#
# Runs entirely in local Docker, against the pristine shipped dump -- not
# against the Aura staging instance, which has accumulated test data (held-out
# hotels, reservation requests, memory nodes) from live notebook runs that must
# not end up in the new baseline.
#
# Requires: Docker. Uses `neo4j:latest` Community Edition -- pin an explicit
# tag here if the shipped dump ever predates a newer Aura/Neo4j release than
# whatever `latest` resolves to (neo4j-admin refuses to load a dump made by a
# newer version than the binaries loading it).
#
# Usage: setup/rebuild_dump.sh
# Output: setup/neo4j-hotel-graph-repaired.dump (review before replacing
# static/neo4j-hotel-graph.dump with it).

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
IMAGE="neo4j:latest"
VOLUME="neo4j-rebuild-dump-$$"
CONTAINER="neo4j-rebuild-dump-$$"
PASSWORD="rebuild-local-$$"
BOLT_PORT=17687
SCRATCH="$(mktemp -d)"

cleanup() {
  docker rm -f "$CONTAINER" >/dev/null 2>&1 || true
  docker volume rm "$VOLUME" >/dev/null 2>&1 || true
  rm -rf "$SCRATCH"
}
trap cleanup EXIT

mkdir -p "$SCRATCH/dumps" "$SCRATCH/dumps-out"
cp "$REPO_ROOT/static/neo4j-hotel-graph.dump" "$SCRATCH/dumps/neo4j.dump"
docker volume create "$VOLUME" >/dev/null

echo "Loading the pristine dump into a scratch Neo4j volume..."
docker run --rm \
  -v "$VOLUME:/data" \
  -v "$SCRATCH/dumps:/dumps" \
  "$IMAGE" \
  neo4j-admin database load --from-path=/dumps neo4j --overwrite-destination=true

echo "Starting Neo4j to apply the repair..."
docker run -d --name "$CONTAINER" \
  -v "$VOLUME:/data" \
  -p "$BOLT_PORT:7687" \
  -e NEO4J_AUTH="neo4j/$PASSWORD" \
  "$IMAGE" >/dev/null

for _ in $(seq 1 60); do
  if docker exec "$CONTAINER" cypher-shell -u neo4j -p "$PASSWORD" "RETURN 1" >/dev/null 2>&1; then
    break
  fi
  sleep 1
done

(
  cd "$REPO_ROOT/notebooks"
  NEO4J_URI="bolt://localhost:$BOLT_PORT" \
  NEO4J_USERNAME=neo4j \
  NEO4J_PASSWORD="$PASSWORD" \
  NEO4J_DATABASE=neo4j \
  uv run python ../setup/repair_dump.py || true
  # exits 1 on the vector/fulltext index check, which is expected here --
  # those indexes are never in the dump; Module 1 creates them. The
  # source_filename/hotel_id/fixture repair above it is what we need.
)

echo "Stopping Neo4j and dumping the repaired database..."
docker stop "$CONTAINER" >/dev/null
docker run --rm \
  -v "$VOLUME:/data" \
  -v "$SCRATCH/dumps-out:/dumps-out" \
  "$IMAGE" \
  neo4j-admin database dump --to-path=/dumps-out neo4j

OUTPUT="$REPO_ROOT/setup/neo4j-hotel-graph-repaired.dump"
cp "$SCRATCH/dumps-out/neo4j.dump" "$OUTPUT"
echo "Done: $OUTPUT"
