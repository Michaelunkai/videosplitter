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

# Emoji output crashes on legacy codepage consoles (e.g. cp1252) - degrade instead
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, 'reconfigure'):
        _stream.reconfigure(errors='replace')


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


def _pin_console_window(user32, kernel32, ctypes, wintypes, hwnd):
    """Title, un-maximize and pin our own console window to a monitor."""
    kernel32.SetConsoleTitleW("VideoSplitter - isolated console (monitor 2 only)")
    if user32.IsZoomed(hwnd):
        # SW_SHOWNOACTIVATE (4): restore from maximized WITHOUT taking
        # foreground. SW_RESTORE (9) would activate the window and steal
        # focus from a full-screen game, dropping its controller input.
        user32.ShowWindow(hwnd, 4)

    class MONITORINFO(ctypes.Structure):
        _fields_ = [('cbSize', wintypes.DWORD),
                    ('rcMonitor', wintypes.RECT),
                    ('rcWork', wintypes.RECT),
                    ('dwFlags', wintypes.DWORD)]

    monitors = []
    proto = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HANDLE, wintypes.HANDLE,
                               ctypes.POINTER(wintypes.RECT), wintypes.LPARAM)

    def _collect(monitor, _dc, _rect, _data):
        info = MONITORINFO()
        info.cbSize = ctypes.sizeof(MONITORINFO)
        if user32.GetMonitorInfoW(monitor, ctypes.byref(info)):
            monitors.append(info)
        return True

    user32.EnumDisplayMonitors(None, None, proto(_collect), None)

    secondary = next((m for m in monitors if not m.dwFlags & 1), None)
    area = secondary.rcWork if secondary else (monitors[0].rcWork if monitors else None)
    if area is None:
        return None
    width = min(760, area.right - area.left)
    height = min(480, area.bottom - area.top)
    x = area.left + (area.right - area.left - width) // 2
    y = area.top + (area.bottom - area.top - height) // 2
    user32.MoveWindow(hwnd, x, y, width, height, True)
    # Belt-and-braces: re-assert no-activation so placement can never take
    # foreground from the game / app the user is using on the main monitor.
    SWP_NOSIZE, SWP_NOMOVE = 0x0001, 0x0002
    SWP_NOZORDER, SWP_NOACTIVATE = 0x0004, 0x0010
    user32.SetWindowPos(hwnd, None, 0, 0, 0, 0,
                        SWP_NOSIZE | SWP_NOMOVE | SWP_NOZORDER | SWP_NOACTIVATE)
    if secondary:
        os.environ['VIDEOSPLITTER_ALLOWED_MONITOR'] = '2'
        return 'secondary'
    os.environ['VIDEOSPLITTER_ALLOWED_MONITOR'] = '1'
    return 'primary'


def isolate_console_window():
    """Force window isolation: dedicated, normal-sized console pinned to a
    secondary monitor when one exists, so the main monitor stays free.
    Manages only this app's own console window - never other windows, the
    mouse or the keyboard."""
    if os.name != 'nt':
        return None
    import ctypes
    from ctypes import wintypes
    try:
        user32 = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32

        # Only touch the window when this console belongs exclusively to us
        # (fresh launch) - a shell the user ran us from is never moved.
        listed = (wintypes.DWORD * 16)()
        count = kernel32.GetConsoleProcessList(listed, 16)
        pids = set(list(listed)[:max(count, 0)])
        exclusive = 0 < count <= 2 and os.getpid() in pids
        if not exclusive:
            return None

        hwnd = kernel32.GetConsoleWindow()
        already = os.environ.get('VIDEOSPLITTER_ISOLATED') == '1'
        if not already and getattr(sys.stdin, 'isatty', lambda: False)() and \
                (os.environ.get('WT_SESSION') or not hwnd):
            # A modern terminal app owns this session, so its window is not
            # ours to move: relaunch in a dedicated classic console instead.
            # STARTF_USESHOWWINDOW + SW_SHOWNOACTIVATE makes the new console
            # appear WITHOUT stealing foreground, so a running game on the
            # main monitor keeps focus (and its controller input) untouched.
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = 4  # SW_SHOWNOACTIVATE
            child_env = dict(os.environ,
                             VIDEOSPLITTER_ISOLATED='1',
                             VIDEOSPLITTER_ALLOWED_MONITOR='2')
            subprocess.Popen(['conhost.exe', os.path.abspath(sys.argv[0])],
                             creationflags=subprocess.CREATE_NEW_CONSOLE,
                             startupinfo=startupinfo, env=child_env)
            sys.exit(0)
        if hwnd:
            return _pin_console_window(user32, kernel32, ctypes, wintypes, hwnd)
    except Exception:
        pass
    return None


def _tray_thread(hwnd_console, tip):
    """Owns the tray icon: message window + Shell_NotifyIconW + context menu.
    Pure ctypes (shell32/user32) - zero new dependencies. Runs as a daemon
    thread for the whole process lifetime; Exit deletes the icon and quits."""
    import ctypes
    from ctypes import wintypes

    user32 = ctypes.windll.user32
    shell32 = ctypes.windll.shell32
    kernel32 = ctypes.windll.kernel32
    # 64-bit-safe pass-through: without argtypes ctypes narrows ints to 32-bit
    user32.DefWindowProcW.argtypes = [wintypes.HWND, wintypes.UINT,
                                      ctypes.c_ulonglong, ctypes.c_ulonglong]
    user32.DefWindowProcW.restype = ctypes.c_longlong

    WM_APP_TRAY = 0x8000 + 0x4C          # WM_APP + 'L' (unique callback msg)
    WM_LBUTTONUP, WM_RBUTTONUP, WM_LBUTTONDBLCLK = 0x0202, 0x0205, 0x0203
    NIM_ADD, NIM_MODIFY, NIM_DELETE = 0, 1, 2
    NIF_MESSAGE, NIF_ICON, NIF_TIP = 1, 2, 4

    class NOTIFYICONDATAW(ctypes.Structure):
        _fields_ = [('cbSize', wintypes.DWORD),
                    ('hWnd', wintypes.HWND),
                    ('uID', wintypes.UINT),
                    ('uFlags', wintypes.UINT),
                    ('uCallbackMessage', wintypes.UINT),
                    ('hIcon', wintypes.HICON),
                    ('szTip', wintypes.WCHAR * 128),
                    ('dwState', wintypes.DWORD),
                    ('dwStateMask', wintypes.DWORD),
                    ('szInfo', wintypes.WCHAR * 256),
                    ('uVersion', wintypes.UINT),
                    ('szInfoTitle', wintypes.WCHAR * 64),
                    ('dwInfoFlags', wintypes.DWORD)]

    state = {'icon': None, 'hwnd': None, 'added': False}

    def _add_icon(hwnd, hicon):
        nid = NOTIFYICONDATAW()
        nid.cbSize = ctypes.sizeof(NOTIFYICONDATAW)
        nid.hWnd, nid.uID, nid.uFlags = hwnd, 1, NIF_MESSAGE | NIF_ICON | NIF_TIP
        nid.uCallbackMessage, nid.hIcon, nid.szTip = WM_APP_TRAY, hicon, tip
        return shell32.Shell_NotifyIconW(NIM_ADD, ctypes.byref(nid))

    def _delete_icon():
        if state['added']:
            nid = NOTIFYICONDATAW()
            nid.cbSize = ctypes.sizeof(NOTIFYICONDATAW)
            nid.hWnd, nid.uID = state['hwnd'], 1
            shell32.Shell_NotifyIconW(NIM_DELETE, ctypes.byref(nid))
            state['added'] = False

    def _menu(hwnd):
        user32.SetForegroundWindow(hwnd)  # required before TrackPopupMenu
        menu = user32.CreatePopupMenu()
        user32.AppendMenuW(menu, 0, 1, "Show console")
        user32.AppendMenuW(menu, 0, 2, "Exit")
        pos = wintypes.POINT()
        user32.GetCursorPos(ctypes.byref(pos))
        cmd = user32.TrackPopupMenu(menu, 0x0180,  # TPM_RETURNCMD | NONOTIFY
                                    pos.x, pos.y, 0, hwnd, None)
        user32.DestroyMenu(menu)
        user32.PostMessageW(hwnd, 0x0000, 0, 0)  # WM_NULL - close the menu
        if cmd == 1 and hwnd_console:
            user32.ShowWindow(hwnd_console, 9)   # user asked - activate is OK
        elif cmd == 2:
            _delete_icon()
            os._exit(0)

    def _wndproc(hwnd, msg, wp, lp):
        if msg == WM_APP_TRAY:
            if wp & 0xFFFF == 1:
                if lp == WM_RBUTTONUP:
                    _menu(hwnd)
                elif lp in (WM_LBUTTONUP, WM_LBUTTONDBLCLK) and hwnd_console:
                    user32.ShowWindow(hwnd_console, 9)  # explicit user click
            return 0
        return user32.DefWindowProcW(hwnd, msg, wp, lp)

    WNDPROC = ctypes.WINFUNCTYPE(ctypes.c_longlong, wintypes.HWND, wintypes.UINT,
                                 ctypes.c_ulonglong, ctypes.c_ulonglong)
    wndproc_ref = WNDPROC(_wndproc)          # keep alive for thread lifetime
    class WNDCLASSW(ctypes.Structure):
        _fields_ = [('style', wintypes.UINT),
                    ('lpfnWndProc', WNDPROC),
                    ('cbClsExtra', ctypes.c_int),
                    ('cbWndExtra', ctypes.c_int),
                    ('hInstance', wintypes.HINSTANCE),
                    ('hIcon', wintypes.HICON),
                    ('hCursor', wintypes.HANDLE),
                    ('hbrBackground', wintypes.HBRUSH),
                    ('lpszMenuName', wintypes.LPCWSTR),
                    ('lpszClassName', wintypes.LPCWSTR)]

    hinst = kernel32.GetModuleHandleW(None)
    wc = WNDCLASSW()
    wc.lpfnWndProc, wc.hInstance = wndproc_ref, hinst
    wc.lpszClassName = "VideoSplitterTrayWnd"
    user32.RegisterClassW(ctypes.byref(wc))
    hwnd = user32.CreateWindowExW(0, wc.lpszClassName, "VideoSplitter tray",
                                  0, 0, 0, 0, 0, None, None, hinst, None)
    state['hwnd'] = hwnd
    hicon = user32.LoadIconW(None, 32512)    # default application icon
    state['added'] = bool(_add_icon(hwnd, hicon))

    msg = wintypes.MSG()
    while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:
        user32.TranslateMessage(ctypes.byref(msg))
        user32.DispatchMessageW(ctypes.byref(msg))
    _delete_icon()


def start_tray_icon(tip="VideoSplitter - 150MB splitter (isolated console)"):
    """Show a system tray icon for the running app (Windows only, best effort).
    The console keeps working exactly as before; the tray icon offers
    'Show console' and 'Exit'. Never touches the mouse or keyboard."""
    if os.name != 'nt':
        return False
    import ctypes
    import threading
    try:
        hwnd_console = ctypes.windll.kernel32.GetConsoleWindow()
        t = threading.Thread(target=_tray_thread, args=(hwnd_console, tip),
                             daemon=True)
        t.start()
        return True
    except Exception:
        return False


def main():
    placement = isolate_console_window()
    exe_path = (sys.executable if getattr(sys, 'frozen', False)
                else os.path.abspath(sys.argv[0]))
    tray_on = start_tray_icon()
    print("=" * 60)
    print("🎬 Video Splitter - 150MB Parts (No Quality Loss)")
    print("=" * 60)
    print(f"🖥️  Executable: {exe_path}")
    if tray_on:
        print("🫥 System tray icon active ('Show console' / 'Exit')")
    if placement == 'secondary':
        print("🔒 Isolation: window pinned to the secondary monitor (main monitor free)")
        print("🤖 AI SESSION RULE: any AI/agent session running inside this console")
        print("   is confined to the SECONDARY monitor (VIDEOSPLITTER_ALLOWED_MONITOR=2).")
        print("   It must never move the mouse, click, type, or show any window on the")
        print("   PRIMARY monitor, and must never take focus from the app in the")
        print("   foreground there (e.g. a game using the controller).")
    elif placement == 'primary':
        print("🔒 Isolation: single monitor - window centered at normal size")

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
