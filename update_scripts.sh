#!/bin/bash

set -e  # Exit on any error

SCRIPTS_FOLDER="scripts"

echo "Git Pull and Copy Python Scripts"
echo "================================="

cd quordle-scores
# Check if we're in a git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo "Error: Not in a git repository!"
    exit 1
fi

# Perform git pull
echo "Performing git pull..."
git pull
cd ..

# Create scripts folder
echo "Creating scripts folder..."
mkdir -p "$SCRIPTS_FOLDER"

# Find and copy Python files
echo "Copying Python scripts..."
cp quordle-scores/*.py $SCRIPTS_FOLDER

# Count copied files
COPIED_COUNT=$(find "$SCRIPTS_FOLDER" -name "*.py" | wc -l)

echo "Done!"
echo "Copied $COPIED_COUNT Python script(s) to $SCRIPTS_FOLDER/"