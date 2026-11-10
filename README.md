<div align="center">

# 🎬 Video Splitter

**Split any video into even 150 MB parts — instantly, with zero quality loss.**

![Python](https://img.shields.io/badge/python-3.6%2B-3776AB?logo=python&logoColor=white)
![ffmpeg](https://img.shields.io/badge/powered%20by-ffmpeg-007808?logo=ffmpeg&logoColor=white)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey)
![License](https://img.shields.io/badge/license-MIT-blue)
![Re-encoding](https://img.shields.io/badge/re--encoding-none-brightgreen)

[Quick start](#-quick-start) · [Features](#features) · [Windows exe](#windows-executable) · [How it works](#how-it-works) · [Troubleshooting](#troubleshooting)

</div>

---

## ⚡ Quick start

```bash
# 1. install ffmpeg (see below), then:
python3 video_splitter.py
# 2. paste the path to your video
# 3. find video_part_000.mp4, video_part_001.mp4 ... next to the original
```

On Windows just double-click **`VideoSplitter.exe`** — no Python needed.

| | |
|---|---|
| 🚫 **No re-encoding** | ffmpeg stream copy (`-c copy`): seconds, not minutes, and bit-exact quality |
| 📦 **Even parts** | bitrate-aware segment length targets ~150 MB per part |
| 🎞️ **Everything kept** | all audio tracks, subtitles and metadata preserved |
| 🖥️ **Window-safe (Windows)** | pins its own console to the secondary monitor, never steals focus, has a tray icon |

## Features

- ✂️ Splits videos into even 150MB parts
- ⚡ Ultra-fast processing (no re-encoding)
- 🎯 No quality loss (uses stream copy)
- 📹 Supports any video format (MP4, MKV, AVI, MOV, etc.)
- 🔧 Automatic bitrate calculation
- 📊 Progress information and file details

## Requirements

- Python 3.6+ (not needed if using the Windows executable)
- ffmpeg and ffprobe on PATH

### Windows executable

`VideoSplitter.exe` is a standalone build of this exact script (PyInstaller onefile, console).
No Python installation is required — only ffmpeg/ffprobe on PATH.

- Build it yourself: `build-exe.cmd` (runs `python -m PyInstaller --onefile --console --clean --name VideoSplitter video_splitter.py`)
- Double-click to run, or run from a terminal — it prompts for the video path

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

## Isolation Guarantee (no input control, forced window isolation)

`VideoSplitter.exe` **forces its own isolation on every launch**:

- Within ~1 second of starting, the console window is re-titled
  `VideoSplitter - isolated console (monitor 2 only)`, restored to a normal size
  (never maximized or full-screen), and **pinned to a secondary monitor** —
  centered in its work area — so a full-screen app on the main monitor is never
  covered.
- **Never steals focus.** Every window operation (restore, placement, and the
  dedicated-console relaunch) uses no-activate semantics (`SW_SHOWNOACTIVATE`,
  `SWP_NOACTIVATE`, `STARTF_USESHOWWINDOW`). A game or app in the foreground on
  the main monitor keeps focus — and therefore keeps controller input — with no
  click required, even while this console is being placed or moved on monitor 2.
- If Windows Terminal is the default terminal (its window is not ours to move),
  the app relaunches itself once inside a dedicated classic console window that
  it can pin. This is automatic; no manual or permanent console settings needed.
- The window is only moved when the console belongs exclusively to the app
  (double-click/shortcut launch). If you run it from an existing shell, that
  shell's window is never touched.

### System tray icon

While the app runs, it shows a **system tray icon** (tooltip
"VideoSplitter - 150MB splitter (isolated console)") implemented in pure ctypes
`Shell_NotifyIconW` — no new dependencies. Left-click or double-click shows the
console; right-click offers `Show console` and `Exit`. The startup banner also
prints the **full path to the executable**. Clicking the tray icon is explicit
user input, so activating the console there never violates the no-focus-steal
guarantee above.

### AI session confinement

When the console is pinned to the secondary monitor, the app sets
`VIDEOSPLITTER_ALLOWED_MONITOR=2` for itself and every child process, and prints
an explicit session rule at startup: any AI/agent session running inside this
console is confined to the secondary monitor and must never move the mouse,
click, type, or show a window on the primary monitor, nor take focus from the
foreground app there.

`VideoSplitter.exe` **cannot control your mouse, keyboard, or any other window**:

- The app is console-only: it reads one file path from stdin, prints to stdout,
  writes only `*_part_%03d` files next to the source video.
- The embedded code is byte-identical to `video_splitter.py` (bytecode-level check),
  which imports only `os`, `sys`, `subprocess`, `json`, `math` (+ stdlib `ctypes`
  solely to manage **its own** console window as above) — no input synthesis,
  no hooks, no networking code of its own.
- The package contains no automation libraries (no pyautogui/pynput/pydirectinput/
  pywin32/tkinter — archive-listing verified).
- At runtime it spawns exactly two external programs and nothing else: `ffprobe` to
  read info and `ffmpeg -c copy` to split (process-tree verified in a live run).

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
