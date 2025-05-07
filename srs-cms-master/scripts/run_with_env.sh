#!/bin/bash
# Load environment variables from a file and executes a command.

if [ "$#" -lt 2 ]; then
    echo "Usage: $0 <path-to-env-file> <command> [args...]"
    exit 1
fi

ENV_FILE="$1"
shift

if [ ! -f "$ENV_FILE" ]; then
    echo "Error: file '$ENV_FILE' not found."
    exit 1
fi

export $(grep -v '^#' "$ENV_FILE" | xargs)

exec "$@"