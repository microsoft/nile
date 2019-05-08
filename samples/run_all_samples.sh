#!/usr/bin/env bash

set -euo pipefail

# run CLI based examples
for DIRECTORY in $(ls -d */); do
    echo "Running sample in $DIRECTORY"
    cd ./$DIRECTORY && python main.py && cd ..
done

echo "All samples ran successfully!"
