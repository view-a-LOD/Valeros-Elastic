#!/usr/bin/env bash
set -euo pipefail

if ! command -v qlever >/dev/null 2>&1; then
  echo "Error: qlever CLI not found in PATH. Run 'pip install qlever' first." >&2
  exit 1
fi

if [ $# -ne 1 ]; then
  echo "Usage: $0 path/to/dataset" >&2
  exit 1
fi

dataset_dir="$1"

if [ ! -d "$dataset_dir" ]; then
  echo "Error: '$dataset_dir' is not a directory" >&2
  exit 1
fi

if [ ! -f "$dataset_dir/Qleverfile" ]; then
  echo "Error: No Qleverfile found in '$dataset_dir'" >&2
  exit 1
fi

echo "=== Processing dataset: $dataset_dir ==="
cd "$dataset_dir"

if ! ls *.index-* >/dev/null 2>&1; then
  echo "No index files found, running 'qlever index'..."
  qlever index
else
  echo "Index files already present, skipping 'qlever index'."
fi

echo "Starting QLever server via 'qlever start' (press Ctrl-C to stop viewing logs, server keeps running)..."
qlever start --kill-existing-with-same-port
