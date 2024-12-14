#!/bin/bash

# Check if directory path is provided
if [ $# -ne 1 ]; then
    echo "Usage: $0 <directory_path>"
    exit 1
fi

# Get directory path and name
DIR_PATH=$(realpath "$1")
DIR_NAME=$(basename "$DIR_PATH")
DEVELOPMENT_DIR="$HOME/consensus"
QUERIES_DIR="$DEVELOPMENT_DIR/queries"
OUTPUT_FILE="query.txt"

# Check if directory exists
if [ ! -d "$DIR_PATH" ]; then
    echo "Error: Directory does not exist"
    exit 1
fi

# Check if Development/queries directory exists, if not create it
if [ ! -d "$QUERIES_DIR" ]; then
    mkdir -p "$QUERIES_DIR"
    if [ $? -ne 0 ]; then
        echo "Error: Could not create queries directory"
        exit 1
    fi
fi

# Check if tree command is available
if ! command -v tree &> /dev/null; then
    echo "Error: 'tree' command not found. Please install it first."
    exit 1
fi

# Create directory structure with find
{
    echo "$DIR_PATH"
    find "$DIR_PATH" \
        -name ".git" -prune -o \
        -name ".terraform" -prune -o \
        -name "node_modules" -prune -o \
        -name "venv" -prune -o \
        -name "__pycache__" -prune -o \
        -print | sort
} | sed -e "s;$DIR_PATH;.;g" | grep -v ".terraform/" > "$OUTPUT_FILE"

# Add a separator and tree view
echo -e "\n=== Tree View ===\n" >> "$OUTPUT_FILE"

# Generate tree view excluding unwanted directories
tree -I '.git|.terraform*|node_modules|venv|__pycache__|*.tfstate*|*.tfvars*|override.tf|override.tf.json|*_override.tf|*_override.tf.json|.terraformrc|terraform.rc|.terragrunt*|*.lock.json|*.lock|.env*|.DS_Store|*.log' "$DIR_PATH" >> "$OUTPUT_FILE"

# Add a separator for file contents
echo -e "\n=== File Contents ===\n" >> "$OUTPUT_FILE"

# Find all files recursively, with proper exclusions
find "$DIR_PATH" -type f \
    -not -path "*/\\.git/*" \
    -not -path "*/\\.terraform*/*" \
    -not -path "*/node_modules/*" \
    -not -path "*/venv/*" \
    -not -path "*/__pycache__/*" \
    -not -name "*.tfstate*" \
    -not -name "*.tfvars*" \
    -not -name "override.tf" \
    -not -name "override.tf.json" \
    -not -name "*_override.tf" \
    -not -name "*_override.tf.json" \
    -not -name ".terraformrc" \
    -not -name "terraform.rc" \
    -not -path "*/\\.terragrunt*/*" \
    -not -name "*.lock.json" \
    -not -name "*.lock" \
    -not -name ".env*" \
    -not -name ".DS_Store" \
    -not -name "*.log" \
    -not -name "$(basename "$OUTPUT_FILE")" \
    -print0 | \
    while IFS= read -r -d "" file; do
        # Get relative path from the directory
        rel_path="${file#$DIR_PATH/}"
        
        # Check if the file is binary
        if file "$file" | grep -q "text"; then
            # Add file header and contents to output file
            echo -e "\n#$rel_path" >> "$OUTPUT_FILE"
            cat "$file" >> "$OUTPUT_FILE"
        else
            # For binary files, just note that it's binary
            echo -e "\n#$rel_path (binary file - contents excluded)" >> "$OUTPUT_FILE"
        fi
    done

echo "Directory snapshot has been saved to: $OUTPUT_FILE"