#!/usr/bin/env python3
"""
Video Splitter - Splits video files into 150MB parts without quality loss
Uses ffmpeg with stream copy for maximum speed and no re-encoding
"""

import os
import sys
import subprocess
import json
import math


def get_video_info(video_path):
    """Get video information using ffprobe"""
    try:
        cmd = [
            'ffprobe',
            '-v', 'quiet',
            '-print_format', 'json',
            '-show_format',
            '-show_streams',
            video_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Error: Could not read video file. Is ffprobe installed?")
        sys.exit(1)
    except json.JSONDecodeError:
        print("Error: Could not parse video information")
        sys.exit(1)


def get_file_size_mb(file_path):
    """Get file size in MB"""
    return os.path.getsize(file_path) / (1024 * 1024)


def split_video(video_path, target_size_mb=150):
    """Split video into parts of approximately target_size_mb each"""

    # Check if file exists
    if not os.path.isfile(video_path):
        print(f"Error: File '{video_path}' not found!")
        return

    print(f"\n📹 Analyzing video: {os.path.basename(video_path)}")

    # Get video information
    info = get_video_info(video_path)

    # Get duration and file size
    try:
        duration = float(info['format']['duration'])
        file_size_mb = get_file_size_mb(video_path)
    except (KeyError, ValueError):
        print("Error: Could not get video duration or size")
        return

    # Calculate bitrate (MB per second)
    bitrate_mb_per_sec = file_size_mb / duration

    # Calculate segment duration for target size
    segment_duration = target_size_mb / bitrate_mb_per_sec

    # Calculate number of parts
    num_parts = math.ceil(duration / segment_duration)

    print(f"📊 Video duration: {duration:.2f} seconds ({duration/60:.2f} minutes)")
    print(f"📦 File size: {file_size_mb:.2f} MB")
    print(f"⚡ Bitrate: {bitrate_mb_per_sec:.2f} MB/s")
    print(f"✂️  Will create {num_parts} parts of ~{target_size_mb}MB each")
    print(f"⏱️  Each segment: ~{segment_duration:.2f} seconds")

    # Prepare output directory and filename
    base_dir = os.path.dirname(os.path.abspath(video_path))
    base_name = os.path.splitext(os.path.basename(video_path))[0]
    ext = os.path.splitext(video_path)[1]

    output_pattern = os.path.join(base_dir, f"{base_name}_part_%03d{ext}")

    print(f"\n🚀 Starting split process (no re-encoding, maximum speed)...\n")

    # Use ffmpeg to split with stream copy (no re-encoding)
    cmd = [
        'ffmpeg',
        '-i', video_path,
        '-c', 'copy',  # Stream copy - no re-encoding
        '-map', '0',   # Copy all streams
        '-f', 'segment',
        '-segment_time', str(segment_duration),
        '-reset_timestamps', '1',
        '-avoid_negative_ts', '1',
        output_pattern
    ]

    try:
        subprocess.run(cmd, check=True)
        print(f"\n✅ Success! Video split into {num_parts} parts")
        print(f"📁 Output location: {base_dir}")
        print(f"📝 Filename pattern: {base_name}_part_XXX{ext}")

        # List created files
        print("\n📄 Created files:")
        for i in range(num_parts):
            part_file = os.path.join(base_dir, f"{base_name}_part_{i:03d}{ext}")
            if os.path.exists(part_file):
                size = get_file_size_mb(part_file)
                print(f"   - {os.path.basename(part_file)} ({size:.2f} MB)")

    except subprocess.CalledProcessError:
        print("\n❌ Error: ffmpeg failed to split the video")
        print("Make sure ffmpeg is installed and the video file is valid")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n⚠️  Process interrupted by user")
        sys.exit(1)


def main():
    print("=" * 60)
    print("🎬 Video Splitter - 150MB Parts (No Quality Loss)")
    print("=" * 60)

    # Check if ffmpeg and ffprobe are available
    try:
        subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
        subprocess.run(['ffprobe', '-version'], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("\n❌ Error: ffmpeg and ffprobe are required but not found!")
        print("\nInstall with:")
        print("  Ubuntu/Debian: sudo apt-get install ffmpeg")
        print("  macOS: brew install ffmpeg")
        print("  Windows: Download from https://ffmpeg.org/download.html")
        sys.exit(1)

    # Get video path from user
    video_path = input("\n📂 Enter the path to your video file: ").strip()

    # Remove quotes if present
    video_path = video_path.strip('"').strip("'")

    # Expand user path
    video_path = os.path.expanduser(video_path)

    if not video_path:
        print("Error: No path provided!")
        sys.exit(1)

    # Split the video
    split_video(video_path, target_size_mb=150)

    print("\n✨ Done!")


if __name__ == "__main__":
    main()
