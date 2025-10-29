# YouTube Downloader Pro

Professional YouTube video downloader with multiple interfaces:
- **GUI Version** (`youtube-downloader-gui.py`) - Modern tkinter interface
- **Web Version** (`app.py`) - Flask web application with real-time progress
- **CLI Version** (`youtube-downloader.py`) - Command-line interface

## Features

- ✅ Download videos in any quality/resolution
- ✅ Select from available formats
- ✅ Real-time download progress
- ✅ SSL certificate bypass for macOS compatibility
- ✅ Professional, modern UI (GUI and Web versions)

## Installation

1. Clone this repository:
```bash
git clone <your-repo-url>
cd YOUTUBE-DOWNLOADER
```

2. Create a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On macOS/Linux
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Install/update certificates (macOS):
```bash
pip install --upgrade certifi
```

## Usage

### GUI Version (Recommended)
```bash
python3 youtube-downloader-gui.py
```

### Web Version
```bash
python3 start.py
# or
python3 app.py
```
Then open http://localhost:8000 in your browser

### Command-Line Version
```bash
python3 youtube-downloader.py
```

## Requirements

- Python 3.7+
- yt-dlp
- tkinter (for GUI version)
- Flask, Flask-SocketIO (for web version)

## SSL Certificate Issues (macOS)

If you encounter SSL certificate errors on macOS:
1. Update certifi: `pip install --upgrade certifi`
2. Update yt-dlp: `pip install --upgrade yt-dlp`
3. The application includes SSL bypass options that should handle this automatically

## Project Structure

```
YOUTUBE-DOWNLOADER/
├── youtube-downloader-gui.py  # Tkinter GUI application
├── youtube-downloader.py       # Command-line application
├── app.py                      # Flask web application
├── start.py                    # Web app launcher
├── requirements.txt            # Python dependencies
├── templates/                  # HTML templates (web version)
│   └── index.html
├── static/                     # Static assets (web version)
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── app.js
└── README.md                   # This file
```

## License

MIT License - Feel free to use and modify!

