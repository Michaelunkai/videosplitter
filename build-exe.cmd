@echo off
rem Rebuilds VideoSplitter.exe from video_splitter.py (onefile, console)
python -m PyInstaller --onefile --console --clean --name VideoSplitter video_splitter.py
move /Y dist\VideoSplitter.exe VideoSplitter.exe >nul
rmdir /S /Q dist
