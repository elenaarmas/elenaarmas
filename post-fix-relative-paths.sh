#!/bin/bash

# Parse command line arguments
CONFIG_FILE="config.json"
while [[ "$#" -gt 0 ]]; do
    case $1 in
    --config)
        CONFIG_FILE="$2"
        shift
        ;;
    *)
        echo "Unknown parameter: $1"
        exit 1
        ;;
    esac
    shift
done

# Use jq to extract configuration values
OUTPUT_DIR=$(jq -r .directories.output "$CONFIG_FILE")

# Extract path rewrites from config
REWRITES=$(jq -r '.path_rewrites[] | "s/" + .from + "/" + .to + "/g"' "$CONFIG_FILE")

# Fix WordPress relative paths in HTML files using fd and sed
fd index.html "$OUTPUT_DIR" -x sed -i $REWRITES {}
