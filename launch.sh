#!/bin/bash
# Ensure script runs from project root
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR" || exit 1

# 1️⃣ Run run.py which handles system deps, venv, and Python packages
python3 "$DIR/run.py"
