#!/bin/bash
# Paper-CLI Wrapper Script
# Usage: ./run-paper.sh [command] [args...]

# Set the CLI directory (this script's folder)
CLI_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Save current working directory
WORK_DIR="$(pwd)"

# Export PYTHONPATH to include CLI directory
export PYTHONPATH="${CLI_DIR}:${PYTHONPATH}"

# Source the .env file
if [ -f "${CLI_DIR}/.env" ]; then
    set -a
    source "${CLI_DIR}/.env"
    set +a
fi

# Change to CLI directory temporarily to run
cd "${CLI_DIR}"

# Run the command from the original working directory
(cd "${WORK_DIR}" && python -m src.main "$@")
