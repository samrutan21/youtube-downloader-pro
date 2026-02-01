# Windows Setup Guide

## Quick Answer: Can you just copy the folder?

**Yes, but with a few important steps:**
- ✅ Copy the folder, but **exclude** the `venv/` and `__pycache__/` folders
- ✅ Python needs to be installed on the Windows computer
- ✅ You'll need to recreate the virtual environment and install dependencies

---

## Step-by-Step Setup Instructions

### 1. Copy the Files

**What to copy:**
- All Python files (`.py` files)
- `requirements.txt`
- `templates/` folder
- `static/` folder  
- `README.md` (optional)

**What NOT to copy:**
- ❌ `venv/` folder (virtual environment - platform-specific)
- ❌ `__pycache__/` folders (Python cache - auto-generated)
- ❌ Any `.pyc` files (compiled Python files - auto-generated)

### 2. Install Python on Windows

1. Download Python from https://www.python.org/downloads/
2. **Important**: During installation, check "Add Python to PATH"
3. Install Python 3.7 or higher (3.10+ recommended)

### 3. Install FFmpeg (Required)

**Yes, you need FFmpeg!** The application downloads video and audio streams separately and merges them into MP4 files. This requires FFmpeg.

#### Quick Installation Steps:

1. **Download FFmpeg for Windows:**
   - Visit https://www.gyan.dev/ffmpeg/builds/ (recommended) or https://ffmpeg.org/download.html
   - Download the "release builds" - choose the "ffmpeg-release-essentials.zip" file

2. **Extract and Install:**
   - Extract the zip file to a folder (e.g., `C:\ffmpeg`)
   - You'll see a `bin` folder inside (e.g., `C:\ffmpeg\ffmpeg-xxx-essentials_build\bin`)

3. **Add to PATH (Important!):**
   - Press `Windows Key + X` and select "System"
   - Click "Advanced system settings"
   - Click "Environment Variables"
   - Under "System variables", find and select "Path", then click "Edit"
   - Click "New" and add the path to the `bin` folder (e.g., `C:\ffmpeg\ffmpeg-xxx-essentials_build\bin`)
   - Click "OK" on all windows

4. **Verify Installation:**
   - Open a new Command Prompt or PowerShell window
   - Type: `ffmpeg -version`
   - You should see version information. If you get an error, the PATH wasn't set correctly.

**Why FFmpeg is needed:**
The application uses `format_id+bestaudio`, which downloads the highest quality video and audio separately, then merges them. FFmpeg performs this merging process.

**Without FFmpeg:** Downloads may fail for high-quality formats, or you'll only be able to download formats that already have combined audio/video streams (often lower quality).

### 4. Set Up the Environment

Open **Command Prompt** or **PowerShell** in the project folder:

```bash
# Navigate to your project folder
cd path\to\YOUTUBE-DOWNLOADER

# Create a virtual environment
python -m venv venv

# Activate the virtual environment
# For Command Prompt:
venv\Scripts\activate
# For PowerShell:
venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

**Note**: If PowerShell gives you an execution policy error, run:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### 5. Run the Application

#### GUI Version (Recommended):
```bash
python youtube-downloader-gui.py
```

#### Web Version:
```bash
python start.py
# or
python app.py
```
Then open http://localhost:8000 in your browser

#### Command-Line Version:
```bash
python youtube-downloader.py
```

---

## Alternative: Simplified Setup

You can also use the `start.py` script which will automatically:
- Check for missing dependencies
- Install them if needed
- Start the web application

Just run:
```bash
python start.py
```

---

## Troubleshooting

### Issue: "python is not recognized"
- **Solution**: Make sure Python is added to PATH, or use `py` instead of `python`
- Reinstall Python and check "Add Python to PATH"

### Issue: SSL Certificate Errors
- The code includes SSL bypass configurations that should work on Windows
- If problems persist, try: `pip install --upgrade certifi yt-dlp`

### Issue: Tkinter not found (for GUI version)
- Windows usually includes tkinter with Python
- If missing: Reinstall Python and make sure "tcl/tk" components are included

### Issue: Port already in use (for web version)
- Another application is using port 8000
- You can modify the port in `app.py` or `start.py` if needed

### Issue: Video download fails or can't merge formats
- **Likely cause**: FFmpeg is not installed or not in PATH
- **Solution**: Install FFmpeg following step 3 above and restart your terminal
- Verify with: `ffmpeg -version` in Command Prompt

### Issue: "ffmpeg not found" error
- FFmpeg is not in your system PATH
- Re-check the PATH environment variable settings
- After adding FFmpeg to PATH, **close and reopen** your terminal/Command Prompt

---

## Quick Copy Checklist

✅ Copy these files/folders:
- `youtube-downloader-gui.py`
- `youtube-downloader.py`
- `app.py`
- `start.py`
- `requirements.txt`
- `templates/` folder
- `static/` folder

❌ Don't copy:
- `venv/` folder
- `__pycache__/` folders
- Any `.pyc` files

---

## Summary

Yes, you can send yourself the folder! Just:
1. Copy the code files (excluding `venv/` folder)
2. Install Python on Windows
3. **Install FFmpeg** (required for video merging)
4. Create a new virtual environment
5. Install dependencies with `pip install -r requirements.txt`
6. Run with `python youtube-downloader-gui.py` or `python start.py`

**Important**: FFmpeg is required because the application downloads video and audio streams separately and merges them. Without it, high-quality downloads will fail.

The code is cross-platform and should work identically on Windows!

