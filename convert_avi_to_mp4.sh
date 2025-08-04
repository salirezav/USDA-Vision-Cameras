#!/bin/bash

# Script to convert AVI files to MP4 using H.264 codec
# Converts files in /storage directory and saves them in the same location

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to get video duration in seconds
get_duration() {
    local file="$1"
    ffprobe -v quiet -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "$file" 2>/dev/null | cut -d. -f1
}

# Function to show progress bar
show_progress() {
    local current=$1
    local total=$2
    local width=50
    local percentage=$((current * 100 / total))
    local filled=$((current * width / total))
    local empty=$((width - filled))

    printf "\r["
    printf "%*s" $filled | tr ' ' '='
    printf "%*s" $empty | tr ' ' '-'
    printf "] %d%% (%ds/%ds)" $percentage $current $total
}

# Check if ffmpeg is installed
if ! command -v ffmpeg &> /dev/null; then
    print_error "ffmpeg is not installed. Please install ffmpeg first."
    exit 1
fi

# Check if /storage directory exists
if [ ! -d "/storage" ]; then
    print_error "/storage directory does not exist."
    exit 1
fi

# Check if we have read/write permissions to /storage
if [ ! -r "/storage" ] || [ ! -w "/storage" ]; then
    print_error "No read/write permissions for /storage directory."
    exit 1
fi

print_status "Starting AVI to MP4 conversion in /storage directory..."

# Counter variables
total_files=0
converted_files=0
skipped_files=0
failed_files=0

# Find all AVI files in /storage directory (including subdirectories)
while IFS= read -r -d '' avi_file; do
    total_files=$((total_files + 1))
    
    # Get the directory and filename without extension
    dir_path=$(dirname "$avi_file")
    filename=$(basename "$avi_file" .avi)
    mp4_file="$dir_path/$filename.mp4"
    
    print_status "Processing: $avi_file"

    # Check if MP4 file already exists
    if [ -f "$mp4_file" ]; then
        print_warning "MP4 file already exists: $mp4_file (skipping)"
        skipped_files=$((skipped_files + 1))
        continue
    fi

    # Get video duration for progress calculation
    duration=$(get_duration "$avi_file")
    if [ -z "$duration" ] || [ "$duration" -eq 0 ]; then
        print_warning "Could not determine video duration, converting without progress bar..."
        # Fallback to simple conversion without progress
        if ffmpeg -i "$avi_file" -c:v libx264 -c:a aac -preset medium -crf 18 "$mp4_file" -y 2>/dev/null; then
            echo
            print_success "Converted: $avi_file -> $mp4_file"
            converted_files=$((converted_files + 1))
        else
            echo
            print_error "Failed to convert: $avi_file"
            failed_files=$((failed_files + 1))
        fi
        continue
    fi

    # Convert AVI to MP4 using H.264 codec with 95% quality (CRF 18) and show progress
    echo "Converting... (Duration: ${duration}s)"

    # Create a temporary file for ffmpeg progress
    progress_file=$(mktemp)

    # Start ffmpeg conversion in background with progress output
    ffmpeg -i "$avi_file" -c:v libx264 -c:a aac -preset medium -crf 18 \
           -progress "$progress_file" -nostats -loglevel 0 "$mp4_file" -y &

    ffmpeg_pid=$!

    # Monitor progress
    while kill -0 $ffmpeg_pid 2>/dev/null; do
        if [ -f "$progress_file" ]; then
            # Extract current time from progress file
            current_time=$(tail -n 10 "$progress_file" 2>/dev/null | grep "out_time_ms=" | tail -n 1 | cut -d= -f2)
            if [ -n "$current_time" ] && [ "$current_time" != "N/A" ]; then
                # Convert microseconds to seconds
                current_seconds=$((current_time / 1000000))
                if [ "$current_seconds" -gt 0 ] && [ "$current_seconds" -le "$duration" ]; then
                    show_progress $current_seconds $duration
                fi
            fi
        fi
        sleep 0.5
    done

    # Wait for ffmpeg to complete and get exit status
    wait $ffmpeg_pid
    ffmpeg_exit_code=$?

    # Clean up progress file
    rm -f "$progress_file"

    # Check if conversion was successful
    if [ $ffmpeg_exit_code -eq 0 ] && [ -f "$mp4_file" ]; then
        show_progress $duration $duration  # Show 100% completion
        echo
        print_success "Converted: $avi_file -> $mp4_file"
        converted_files=$((converted_files + 1))

        # Optional: Remove original AVI file (uncomment the next line if you want this)
        # rm "$avi_file"
    else
        echo
        print_error "Failed to convert: $avi_file"
        failed_files=$((failed_files + 1))
        # Clean up incomplete file
        [ -f "$mp4_file" ] && rm "$mp4_file"
    fi

    echo  # Add blank line between files
    
done < <(find /storage -name "*.avi" -type f -print0)

# Print summary
echo
print_status "=== CONVERSION SUMMARY ==="
echo "Total AVI files found: $total_files"
echo "Successfully converted: $converted_files"
echo "Skipped (MP4 exists): $skipped_files"
echo "Failed conversions: $failed_files"

if [ $total_files -eq 0 ]; then
    print_warning "No AVI files found in /storage directory."
elif [ $failed_files -eq 0 ] && [ $converted_files -gt 0 ]; then
    print_success "All conversions completed successfully!"
elif [ $failed_files -gt 0 ]; then
    print_warning "Some conversions failed. Check the output above for details."
fi
