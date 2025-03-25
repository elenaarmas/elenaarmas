#!/bin/bash

# Configuration
LOG_FILE="log.txt"
BASE_URL="https://n1589766.websitebuilder.online"
OUTPUT_DIR="assets"
USER_AGENT="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

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
echo "Use these commands to move them to the correct location:"
echo "cp -n $OUTPUT_DIR/wp-content/uploads/go-x/u/* docs/n1589766.websitebuilder.online/wp-content/uploads/go-x/u/"
echo "cp -n $OUTPUT_DIR/wp-content/themes/* docs/n1589766.websitebuilder.online/wp-content/themes/"

# Configuration
MIRROR_DIR="docs"
ASSETS_DIR="assets"

# Ensure assets directory exists
if [[ ! -d "$ASSETS_DIR" ]]; then
    echo "❌ Error: Assets directory '$ASSETS_DIR' does not exist!"
    exit 1
fi

echo "▸ Injecting assets into mirror structure..."

# Move assets into the mirror directory
mv "$ASSETS_DIR" "$MIRROR_DIR/" || {
    echo "❌ Failed to move assets to $MIRROR_DIR/"
    exit 1
}

# Merge assets while preserving directory structure
rsync -a --ignore-existing "$MIRROR_DIR/assets/wp-content/" "$MIRROR_DIR/wp-content/" || {
    echo "❌ Failed to sync assets into $MIRROR_DIR/wp-content/"
    exit 1
}

# Clean up empty directories and leftover assets
find "$MIRROR_DIR/assets" -type d -empty -delete
rm -rf "$MIRROR_DIR/assets"

echo "▸ Fixing HTML references to use local paths..."
find "$MIRROR_DIR" -type f -name "*.html" -exec sed -i \
    -e 's|https://n1589766\.websitebuilder\.online||g' \
    -e 's|/wp-content/themes/gox/public/legal/maps/es-ES\.html|/wp-content/themes/gox/public/legal/maps/es-ES.html|g' \
    {} \;

echo "✅ Injection complete! Assets available at:"
tree -L 4 "$MIRROR_DIR/wp-content"
