#!/bin/bash

# Kairos - Build script using Nuitka

set -e

echo "Building Kairos with Nuitka..."

python -m nuitka \
  --standalone \
  --enable-plugin=pyside6 \
  --include-qt-plugins=sensible,styles,platforms \
  --follow-imports \
  --output-filename=kairos \
  --output-dir=dist \
  kairos/main.py

echo "Build completed! Output in dist/"
