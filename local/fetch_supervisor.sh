#!/usr/bin/env bash
# Detached, resumable download supervisor: keeps running fetch_models.py for the given models until all are
# hash-verified (curl -C - resumes partial files). Usage: fetch_supervisor.sh <logname> <model> [<model>...]
set -u
cd "$(dirname "$0")/.."
log="local/runs/$1.log"; shift
for i in $(seq 1 50); do
  echo "attempt $i $(date -Is)" >> "$log"
  python local/fetch_models.py "$@" >> "$log" 2>&1 && { echo "ALL VERIFIED $(date -Is)" >> "$log"; exit 0; }
  sleep 60
done
echo "GAVE UP after 50 attempts $(date -Is)" >> "$log"
