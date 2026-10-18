#!/usr/bin/env bash
# Build Scientific Cat as a PyInstaller onedir application.
set -euo pipefail
cd "$(dirname "$0")"

if [[ "${1:-}" == "--help" ]]; then
    echo "Usage: ./build.sh [--help]"
    echo "Creates dist/ScientificCat/ with bundled resources."
    exit 0
fi
if [[ -n "${1:-}" ]]; then
    echo "[ERROR] Unknown argument: $1"
    exit 1
fi

PYTHON=".venv/bin/python"
if [[ ! -x "$PYTHON" ]]; then
    echo "[ERROR] Virtual environment was not found. Create .venv and install dev dependencies."
    exit 1
fi

for resource in assets/styles assets/schema assets/katex assets/templates assets/icons; do
    if [[ ! -d "$resource" ]]; then
        echo "[ERROR] Required resource was not found: $resource"
        exit 1
    fi
done

if ! "$PYTHON" -m PyInstaller --version >/dev/null 2>&1; then
    echo "[ERROR] PyInstaller is not installed. Install the dev dependencies first."
    exit 1
fi

echo "Building application..."
"$PYTHON" -m PyInstaller --noconfirm --clean \
    --name ScientificCat \
    --windowed \
    --add-data "assets/styles:assets/styles" \
    --add-data "assets/schema:assets/schema" \
    --add-data "assets/katex:assets/katex" \
    --add-data "assets/templates:assets/templates" \
    --add-data "assets/icons:assets/icons" \
    --collect-data matplotlib \
    --collect-submodules mistletoe \
    --hidden-import lxml._elementpath \
    --hidden-import matplotlib.backends.backend_agg \
    main.py

echo "Running frozen smoke test..."
if [[ -x "dist/ScientificCat/ScientificCat" ]]; then
    dist/ScientificCat/ScientificCat --smoke-test
elif [[ -x "dist/ScientificCat.app/Contents/MacOS/ScientificCat" ]]; then
    dist/ScientificCat.app/Contents/MacOS/ScientificCat --smoke-test
else
    echo "[ERROR] Built executable was not found."
    exit 1
fi

echo "Build completed successfully."
echo "Application: dist/ScientificCat/"