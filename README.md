# Video Splitter

A fast and efficient Python tool to split video files into 150MB parts without any quality loss.

## Features

- ✂️ Splits videos into even 150MB parts
- ⚡ Ultra-fast processing (no re-encoding)
- 🎯 No quality loss (uses stream copy)
- 📹 Supports any video format (MP4, MKV, AVI, MOV, etc.)
- 🔧 Automatic bitrate calculation
- 📊 Progress information and file details

## Requirements

- Python 3.6+
- ffmpeg and ffprobe

### Installing ffmpeg

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install ffmpeg
```

**macOS:**
```bash
brew install ffmpeg
```

**Windows:**
Download from [https://ffmpeg.org/download.html](https://ffmpeg.org/download.html)

## Usage

1. Run the script:
```bash
python3 video_splitter.py
```

2. Enter the path to your video file when prompted

3. The script will:
   - Analyze your video
   - Calculate optimal segment duration
   - Split into 150MB parts
   - Save parts in the same directory as the original

## Example

```
$ python3 video_splitter.py

============================================================
🎬 Video Splitter - 150MB Parts (No Quality Loss)
============================================================

📂 Enter the path to your video file: /path/to/my/video.mp4

📹 Analyzing video: video.mp4
📊 Video duration: 600.00 seconds (10.00 minutes)
📦 File size: 450.00 MB
⚡ Bitrate: 0.75 MB/s
✂️  Will create 3 parts of ~150MB each
⏱️  Each segment: ~200.00 seconds

🚀 Starting split process (no re-encoding, maximum speed)...

✅ Success! Video split into 3 parts
📁 Output location: /path/to/my
📝 Filename pattern: video_part_XXX.mp4

📄 Created files:
   - video_part_000.mp4 (150.00 MB)
   - video_part_001.mp4 (150.00 MB)
   - video_part_002.mp4 (150.00 MB)

✨ Done!
```

## How It Works

1. **Analysis**: Uses ffprobe to get video duration and calculate bitrate
2. **Calculation**: Determines segment duration to achieve ~150MB parts
3. **Splitting**: Uses ffmpeg with `-c copy` flag to split without re-encoding
4. **Speed**: Stream copying is 100x faster than re-encoding and maintains perfect quality

## Output Files

Files are saved in the same directory as the input video with the pattern:
```
original_filename_part_000.ext
original_filename_part_001.ext
original_filename_part_002.ext
...
```

## Notes

- The script uses stream copy, so splitting is extremely fast
- No quality is lost since there's no re-encoding
- Part sizes will be approximately 150MB (may vary slightly based on keyframe positions)
- All audio tracks, subtitles, and metadata are preserved

## Troubleshooting

**Error: ffmpeg not found**
- Install ffmpeg using the instructions above

**Error: Could not read video file**
- Make sure the file path is correct
- Verify the video file is not corrupted
- Check that you have read permissions

**Parts are not exactly 150MB**
- This is normal - ffmpeg splits at keyframes to maintain video integrity
- Parts will be close to 150MB, typically within ±10%

## License

MIT License
