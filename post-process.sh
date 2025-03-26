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
LOG_FILE=$(jq -r .build.log_file "$CONFIG_FILE")
BASE_URL=$(jq -r .urls.source "$CONFIG_FILE")
OUTPUT_DIR=$(jq -r .directories.assets "$CONFIG_FILE")
USER_AGENT=$(jq -r .build.user_agent "$CONFIG_FILE")
MIRROR_DIR=$(jq -r .directories.output "$CONFIG_FILE")

# Create output directory with original structure
mkdir -p "$OUTPUT_DIR"

# Process log file
grep "404 - GET" "$LOG_FILE" | while read -r line; do
    # Extract URL path and clean multi-line formatting
    path=$(echo "$line" | awk -F 'GET ' '{print $2}' | tr -d '\n')

    if [ -n "$path" ]; then
        # Create local directory structure
        dir="$OUTPUT_DIR$(dirname "$path")"
        mkdir -p "$dir"

        # Download asset with original filename
        echo "Downloading: $BASE_URL$path"
        wget -q --no-check-certificate \
            --user-agent="$USER_AGENT" \
            --directory-prefix="$dir" \
            "$BASE_URL$path"

        # Verify download
        if [ $? -eq 0 ]; then
            echo "✅ Success: $path"
        else
            echo "❌ Failed: $path"
            rm -f "$dir/$(basename "$path")" 2>/dev/null
        fi
    fi
done

echo "Downloaded assets stored in: $OUTPUT_DIR"

# Inject assets into mirror structure
echo "▸ Injecting assets into mirror structure..."

# Move assets into the mirror directory
mv "$OUTPUT_DIR" "$MIRROR_DIR/" || {
    echo "❌ Failed to move assets to $MIRROR_DIR/"
    exit 1
}

# Merge assets while preserving directory structure
rsync -a --ignore-existing "$MIRROR_DIR/$OUTPUT_DIR/wp-content/" "$MIRROR_DIR/wp-content/" || {
    echo "❌ Failed to sync assets into $MIRROR_DIR/wp-content/"
    exit 1
}

# Clean up empty directories and leftover assets
find "$MIRROR_DIR/$OUTPUT_DIR" -type d -empty -delete
rm -rf "$MIRROR_DIR/$OUTPUT_DIR"

echo "▸ Fixing HTML references to use local paths..."

# Extract special paths from config
SPECIAL_PATHS=$(jq -r '.wordpress.special_paths[]' "$CONFIG_FILE" | sed 's/^/s|/; s/$/|&|g')

find "$MIRROR_DIR" -type f -name "*.html" -exec sed -i \
    -e "s|$BASE_URL||g" \
    $SPECIAL_PATHS \
    {} \;

echo "✅ Injection complete! Assets available at:"
tree -L 4 "$MIRROR_DIR/wp-content"
