#!/bin/bash

# Kairos - Run script for development mode

set -e

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python -m venv .venv --system-site-packages
fi

# Activate virtual environment
source .venv/bin/activate

# Install dependencies (silencioso)
echo "Installing dependencies..."
pip install -r requirements.txt -q --disable-pip-version-check > /dev/null 2>&1

# Run the application in background
echo "Starting Kairos..."

nohup python -m kairos.main > /dev/null 2>&1 < /dev/null &

# Save PID
echo $! > kairos.pid