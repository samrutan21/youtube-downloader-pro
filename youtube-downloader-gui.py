#!/usr/bin/env python3
"""
YouTube Video Downloader - Professional GUI Version
Clean, intuitive interface with clear workflow
"""

# CRITICAL: Disable SSL verification BEFORE any other imports
import ssl
ssl._create_default_https_context = ssl._create_unverified_context

import sys
import os
import threading
from pathlib import Path
from collections import defaultdict

# Set environment variables to disable SSL verification
os.environ['PYTHONHTTPSVERIFY'] = '0'
os.environ['CURL_CA_BUNDLE'] = ''
os.environ['REQUESTS_CA_BUNDLE'] = ''

# Disable SSL verification for requests/urllib3 (used by yt-dlp)
try:
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    import requests
    requests.packages.urllib3.disable_warnings()
except (ImportError, AttributeError):
    pass

try:
    import yt_dlp
    # Configure yt-dlp to use requests with SSL verification disabled
    try:
        # Try to patch yt-dlp's network module
        from yt_dlp.utils import network
        import requests
        # Create a session with SSL verification disabled
        unverified_session = requests.Session()
        unverified_session.verify = False
        
        # Monkeypatch network.get_compatible_extractor to use unverified session
        if hasattr(network, 'requests'):
            network.requests = unverified_session
    except (ImportError, AttributeError):
        pass
        
except ImportError:
    print("ERROR: yt-dlp is not installed!")
    print("Please install it by running: pip install yt-dlp")
    sys.exit(1)

try:
    import tkinter as tk
    from tkinter import ttk, filedialog, messagebox, simpledialog
except ImportError:
    print("ERROR: tkinter is not installed!")
    sys.exit(1)


class YouTubeDownloaderGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("YouTube Downloader Pro")
        self.root.geometry("1000x800")
        self.root.resizable(True, True)
        
        # Variables
        self.url_var = tk.StringVar()
        self.output_var = tk.StringVar(value=str(Path.home() / "Downloads"))
        self.status_var = tk.StringVar(value="Ready to download")
        self.progress_var = tk.DoubleVar(value=0)
        self.video_info = None
        self.resolution_formats = None
        self.selected_format = None
        self.is_downloading = False
        self.available_audio_formats = []
        self.audio_format_options = []
        self.selected_audio_download_opts = None
        self.partial_downloads = []  # Store detected partial downloads
        self.selected_partial = None  # Selected partial download to resume
        
        # Modern color scheme
        self.bg_primary = "#0f0f0f"
        self.bg_secondary = "#1a1a1a"
        self.bg_tertiary = "#2a2a2a"
        self.accent_blue = "#007acc"
        self.accent_green = "#00c851"
        self.accent_red = "#ff4444"
        self.text_primary = "#ffffff"
        self.text_secondary = "#cccccc"
        self.text_muted = "#888888"
        self.border_color = "#333333"
        self.button_text = "#000000"  # Black text on buttons for contrast
        
        self.setup_ui()
        self.apply_theme()
        
        # Auto-check for partial downloads on startup
        self.root.after(100, self.check_partial_downloads)
        
    def setup_ui(self):
        """Set up the modern user interface"""
        
        # Main container with padding
        main_frame = tk.Frame(self.root, bg=self.bg_primary)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=30)
        
        # Header section
        self.setup_header(main_frame)
        
        # Main content area
        content_frame = tk.Frame(main_frame, bg=self.bg_primary)
        content_frame.pack(fill=tk.BOTH, expand=True, pady=(30, 0))
        
        # Left panel - Input and info
        left_panel = tk.Frame(content_frame, bg=self.bg_primary)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 15))
        
        # Right panel - Controls and progress
        right_panel = tk.Frame(content_frame, bg=self.bg_primary)
        right_panel.pack(side=tk.RIGHT, fill=tk.Y, padx=(15, 0))
        
        self.setup_left_panel(left_panel)
        self.setup_right_panel(right_panel)
        
    def setup_header(self, parent):
        """Set up the header section"""
        header_frame = tk.Frame(parent, bg=self.bg_primary)
        header_frame.pack(fill=tk.X)
        
        # Title
        title_label = tk.Label(
            header_frame,
            text="YouTube Downloader Pro",
            font=("SF Pro Display", 32, "bold"),
            bg=self.bg_primary,
            fg=self.text_primary
        )
        title_label.pack()
        
        # Subtitle
        subtitle_label = tk.Label(
            header_frame,
            text="Download videos in any quality with ease",
            font=("SF Pro Text", 14),
            bg=self.bg_primary,
            fg=self.text_muted
        )
        subtitle_label.pack(pady=(5, 0))
        
    def setup_left_panel(self, parent):
        """Set up the left panel with URL input and video info"""
        
        # URL Input Section
        url_section = tk.Frame(parent, bg=self.bg_secondary, relief=tk.FLAT, bd=1)
        url_section.pack(fill=tk.X, pady=(0, 20))
        
        # URL label
        url_label = tk.Label(
            url_section,
            text="Video URL",
            font=("SF Pro Text", 12, "bold"),
            bg=self.bg_secondary,
            fg=self.text_primary
        )
        url_label.pack(anchor=tk.W, padx=20, pady=(20, 10))
        
        # URL input frame
        url_input_frame = tk.Frame(url_section, bg=self.bg_tertiary)
        url_input_frame.pack(fill=tk.X, padx=20, pady=(0, 15))
        
        self.url_entry = tk.Entry(
            url_input_frame,
            textvariable=self.url_var,
            font=("SF Pro Text", 12),
            bg=self.bg_tertiary,
            fg=self.text_primary,
            insertbackground=self.text_primary,
            relief=tk.FLAT,
            bd=0,
            highlightthickness=0
        )
        self.url_entry.pack(fill=tk.X, padx=15, pady=12)
        
        # Analyze button
        self.analyze_btn = tk.Button(
            url_section,
            text="Analyze Video",
            font=("SF Pro Text", 12, "bold"),
            bg=self.accent_blue,
            fg=self.button_text,
            activebackground="#005a9e",
            activeforeground=self.button_text,
            relief=tk.FLAT,
            cursor="hand2",
            command=self.analyze_video,
            bd=0,
            highlightthickness=0
        )
        self.analyze_btn.pack(fill=tk.X, padx=20, pady=(0, 20))
        
        # Video Info Section (initially hidden)
        self.info_section = tk.Frame(parent, bg=self.bg_secondary, relief=tk.FLAT, bd=1)
        
        info_label = tk.Label(
            self.info_section,
            text="Video Information",
            font=("SF Pro Text", 12, "bold"),
            bg=self.bg_secondary,
            fg=self.text_primary
        )
        info_label.pack(anchor=tk.W, padx=20, pady=(20, 10))
        
        self.video_title_label = tk.Label(
            self.info_section,
            text="",
            font=("SF Pro Text", 11),
            bg=self.bg_secondary,
            fg=self.text_primary,
            wraplength=400,
            justify=tk.LEFT
        )
        self.video_title_label.pack(anchor=tk.W, padx=20, pady=(0, 5))
        
        self.video_details_label = tk.Label(
            self.info_section,
            text="",
            font=("SF Pro Text", 10),
            bg=self.bg_secondary,
            fg=self.text_muted
        )
        self.video_details_label.pack(anchor=tk.W, padx=20, pady=(0, 20))
        
    def setup_right_panel(self, parent):
        """Set up the right panel with quality selection and download controls"""
        
        # Quality Selection Section
        quality_section = tk.Frame(parent, bg=self.bg_secondary, relief=tk.FLAT, bd=1)
        quality_section.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
        
        quality_label = tk.Label(
            quality_section,
            text="Select Quality",
            font=("SF Pro Text", 12, "bold"),
            bg=self.bg_secondary,
            fg=self.text_primary
        )
        quality_label.pack(anchor=tk.W, padx=20, pady=(20, 10))
        
        # Quality listbox with scrollbar
        listbox_frame = tk.Frame(quality_section, bg=self.bg_tertiary)
        listbox_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 15))
        
        scrollbar = tk.Scrollbar(listbox_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.quality_listbox = tk.Listbox(
            listbox_frame,
            font=("SF Mono", 10),
            bg=self.bg_tertiary,
            fg=self.text_primary,
            selectbackground=self.accent_blue,
            selectforeground=self.text_primary,
            relief=tk.FLAT,
            bd=0,
            highlightthickness=0,
            yscrollcommand=scrollbar.set,
            activestyle='none'
        )
        self.quality_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        scrollbar.config(command=self.quality_listbox.yview)
        
        self.quality_listbox.bind('<<ListboxSelect>>', self.on_quality_select)
        
        # Download Location Section
        location_section = tk.Frame(parent, bg=self.bg_secondary, relief=tk.FLAT, bd=1)
        location_section.pack(fill=tk.X, pady=(0, 20))
        
        location_label = tk.Label(
            location_section,
            text="Download Location",
            font=("SF Pro Text", 12, "bold"),
            bg=self.bg_secondary,
            fg=self.text_primary
        )
        location_label.pack(anchor=tk.W, padx=20, pady=(20, 10))
        
        # Location input frame
        location_input_frame = tk.Frame(location_section, bg=self.bg_tertiary)
        location_input_frame.pack(fill=tk.X, padx=20, pady=(0, 10))
        
        self.location_entry = tk.Entry(
            location_input_frame,
            textvariable=self.output_var,
            font=("SF Pro Text", 10),
            bg=self.bg_tertiary,
            fg=self.text_primary,
            insertbackground=self.text_primary,
            relief=tk.FLAT,
            bd=0,
            highlightthickness=0,
            state='readonly'
        )
        self.location_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=15, pady=10)
        
        browse_btn = tk.Button(
            location_input_frame,
            text="Browse",
            font=("SF Pro Text", 10),
            bg=self.bg_primary,
            fg=self.button_text,
            activebackground=self.bg_tertiary,
            activeforeground=self.button_text,
            relief=tk.FLAT,
            cursor="hand2",
            command=self.browse_location,
            bd=0,
            highlightthickness=0
        )
        browse_btn.pack(side=tk.RIGHT, padx=(10, 15), pady=10)
        
        # Resume Partial Downloads Section
        self.resume_section = tk.Frame(location_section, bg=self.bg_secondary)
        
        resume_header = tk.Frame(self.resume_section, bg=self.bg_secondary)
        resume_header.pack(fill=tk.X, padx=20, pady=(0, 10))
        
        resume_title = tk.Label(
            resume_header,
            text="Resume Partial Downloads",
            font=("SF Pro Text", 11, "bold"),
            bg=self.bg_secondary,
            fg=self.text_primary
        )
        resume_title.pack(side=tk.LEFT)
        
        self.check_resume_btn = tk.Button(
            resume_header,
            text="Check for Partial Downloads",
            font=("SF Pro Text", 9),
            bg=self.bg_tertiary,
            fg=self.button_text,
            activebackground=self.bg_tertiary,
            activeforeground=self.button_text,
            relief=tk.FLAT,
            cursor="hand2",
            command=self.check_partial_downloads,
            bd=0,
            highlightthickness=0
        )
        self.check_resume_btn.pack(side=tk.RIGHT)
        
        self.resume_listbox_frame = tk.Frame(self.resume_section, bg=self.bg_tertiary)
        
        scrollbar_resume = tk.Scrollbar(self.resume_listbox_frame)
        scrollbar_resume.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.resume_listbox = tk.Listbox(
            self.resume_listbox_frame,
            font=("SF Pro Text", 9),
            bg=self.bg_tertiary,
            fg=self.text_primary,
            selectbackground=self.accent_blue,
            selectforeground=self.text_primary,
            relief=tk.FLAT,
            bd=0,
            highlightthickness=0,
            yscrollcommand=scrollbar_resume.set,
            activestyle='none',
            height=3
        )
        self.resume_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        scrollbar_resume.config(command=self.resume_listbox.yview)
        
        self.resume_listbox.bind('<<ListboxSelect>>', self.on_resume_select)
        
        # Pack the listbox frame into resume section
        self.resume_listbox_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 10))
        
        resume_btn_frame = tk.Frame(self.resume_section, bg=self.bg_secondary)
        resume_btn_frame.pack(fill=tk.X, padx=20, pady=(0, 10))
        
        self.resume_btn = tk.Button(
            resume_btn_frame,
            text="Resume Selected Download",
            font=("SF Pro Text", 10, "bold"),
            bg=self.accent_blue,
            fg=self.button_text,
            activebackground="#005a9e",
            activeforeground=self.button_text,
            disabledforeground=self.button_text,
            relief=tk.FLAT,
            cursor="hand2",
            command=self.resume_download,
            state=tk.DISABLED,
            bd=0,
            highlightthickness=0
        )
        self.resume_btn.pack(fill=tk.X)
        
        # Download Button
        self.download_btn = tk.Button(
            location_section,
            text="Download Video",
            font=("SF Pro Text", 14, "bold"),
            bg=self.accent_green,
            fg=self.button_text,
            activebackground="#00a041",
            activeforeground=self.button_text,
            disabledforeground=self.button_text,
            relief=tk.FLAT,
            cursor="hand2",
            command=self.start_download,
            state=tk.DISABLED,
            bd=0,
            highlightthickness=0
        )
        self.download_btn.pack(fill=tk.X, padx=20, pady=(0, 20))
        
        # Progress Section
        self.progress_section = tk.Frame(parent, bg=self.bg_secondary, relief=tk.FLAT, bd=1)
        
        progress_label = tk.Label(
            self.progress_section,
            text="Download Progress",
            font=("SF Pro Text", 12, "bold"),
            bg=self.bg_secondary,
            fg=self.text_primary
        )
        progress_label.pack(anchor=tk.W, padx=20, pady=(20, 10))
        
        # Custom progress bar
        progress_frame = tk.Frame(self.progress_section, bg=self.bg_tertiary)
        progress_frame.pack(fill=tk.X, padx=20, pady=(0, 10))
        
        self.progress_bar = ttk.Progressbar(
            progress_frame,
            variable=self.progress_var,
            maximum=100,
            mode='determinate',
            style="Custom.Horizontal.TProgressbar"
        )
        self.progress_bar.pack(fill=tk.X, padx=10, pady=10)
        
        self.status_label = tk.Label(
            self.progress_section,
            textvariable=self.status_var,
            font=("SF Pro Text", 10),
            bg=self.bg_secondary,
            fg=self.text_secondary
        )
        self.status_label.pack(anchor=tk.W, padx=20, pady=(0, 20))
        
    def apply_theme(self):
        """Apply the modern theme"""
        self.root.configure(bg=self.bg_primary)
        
        # Configure ttk styles
        style = ttk.Style()
        style.theme_use('clam')
        style.configure(
            "Custom.Horizontal.TProgressbar",
            troughcolor=self.bg_tertiary,
            background=self.accent_green,
            bordercolor=self.bg_tertiary,
            lightcolor=self.accent_green,
            darkcolor=self.accent_green
        )
        
    def analyze_video(self):
        """Analyze the video URL"""
        url = self.url_var.get().strip()
        
        if not url:
            messagebox.showwarning("No URL", "Please enter a YouTube video URL")
            return
        
        if 'youtube.com' not in url and 'youtu.be' not in url:
            result = messagebox.askyesno(
                "Invalid URL",
                "This doesn't look like a YouTube URL. Continue anyway?"
            )
            if not result:
                return
        
        # Disable button and show loading
        self.analyze_btn.config(state=tk.DISABLED, text="Analyzing...")
        self.status_var.set("Analyzing video...")
        
        # Run in separate thread
        thread = threading.Thread(target=self._analyze_video_thread, args=(url,))
        thread.daemon = True
        thread.start()
        
    def _analyze_video_thread(self, url):
        """Thread function to analyze video"""
        try:
            # Create custom SSL context that doesn't verify
            import ssl
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            
            ydl_opts = {
                'quiet': True, 
                'no_warnings': True,
                'nocheckcertificate': True,
                'no_check_certificate': True,  # Alternative format
                'ignoreerrors': True,
                'extractor_args': {
                    'default': {
                        'nocheckcertificate': True
                    },
                    'youtube': {
                        'nocheckcertificate': True
                    }
                }
            }
            
            # Try to inject unverified SSL context into yt-dlp
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Patch the HTTP client directly if possible
                if hasattr(ydl, '_opener'):
                    # Try to disable SSL verification in opener
                    pass
                
                info = ydl.extract_info(url, download=False)
            
            # Check if extraction was successful
            if info is None:
                self.root.after(0, lambda: self._show_error(
                    "Failed to extract video information. This might be due to:\n"
                    "- SSL certificate issues\n"
                    "- Video is unavailable or private\n"
                    "- Network connectivity problems\n\n"
                    "Please try again or check the video URL."
                ))
                return
            
            # Parse formats
            resolution_formats = defaultdict(list)
            
            for fmt in info.get('formats', []):
                if fmt.get('vcodec') != 'none':
                    height = fmt.get('height')
                    width = fmt.get('width')
                    fps = fmt.get('fps', 30)
                    filesize = fmt.get('filesize') or fmt.get('filesize_approx', 0)
                    ext = fmt.get('ext', 'unknown')
                    format_id = fmt.get('format_id', '')
                    vcodec = fmt.get('vcodec', 'unknown')
                    acodec = fmt.get('acodec', 'none')
                    
                    if height and width:
                        resolution_key = f"{width}x{height}"
                        resolution_formats[resolution_key].append({
                            'format_id': format_id,
                            'resolution': resolution_key,
                            'width': width,
                            'height': height,
                            'fps': fps,
                            'ext': ext,
                            'filesize': filesize,
                            'vcodec': vcodec,
                            'acodec': acodec,
                            'has_audio': acodec != 'none',
                        })
            
            # Parse audio-only formats and detect available native codecs
            audio_codecs = {}
            for fmt in info.get('formats', []):
                if fmt.get('vcodec') == 'none' and fmt.get('acodec') not in ('none', None, ''):
                    acodec = fmt.get('acodec', '') or ''
                    abr = fmt.get('abr') or 0
                    filesize = fmt.get('filesize') or fmt.get('filesize_approx') or 0
                    format_id = fmt.get('format_id', '')
                    ext = fmt.get('ext', '')

                    if acodec.startswith('mp4a') or acodec == 'aac':
                        codec_key, codec_display, container = 'aac', 'AAC', 'm4a'
                    elif acodec == 'opus':
                        codec_key, codec_display, container = 'opus', 'Opus', 'webm'
                    elif acodec == 'vorbis':
                        codec_key, codec_display, container = 'vorbis', 'Vorbis', 'webm'
                    else:
                        codec_key = acodec.lower().replace('.', '_')
                        codec_display = acodec.upper()
                        container = ext

                    if codec_key not in audio_codecs or abr > audio_codecs[codec_key].get('abr', 0):
                        audio_codecs[codec_key] = {
                            'format_id': format_id,
                            'codec_key': codec_key,
                            'codec_display': codec_display,
                            'container': container,
                            'abr': abr,
                            'filesize': filesize,
                        }

            available_audio = list(audio_codecs.values())
            codec_order = {'opus': 0, 'aac': 1}
            available_audio.sort(key=lambda x: codec_order.get(x['codec_key'], 99))

            self.video_info = info
            self.resolution_formats = resolution_formats
            self.available_audio_formats = available_audio

            # Update UI in main thread
            self.root.after(0, self._update_video_info_ui)
            
        except Exception as e:
            error_msg = f"Failed to analyze video: {str(e)}"
            self.root.after(0, lambda: self._show_error(error_msg))
            
    def _update_video_info_ui(self):
        """Update UI with video information"""
        # Re-enable button
        self.analyze_btn.config(state=tk.NORMAL, text="Analyze Video")
        
        # Show video info
        title = self.video_info.get('title', 'Unknown')
        duration = self.video_info.get('duration', 0)
        uploader = self.video_info.get('uploader', 'Unknown')
        
        hours = duration // 3600
        minutes = (duration % 3600) // 60
        seconds = duration % 60
        
        self.video_title_label.config(text=f"📹 {title}")
        self.video_details_label.config(
            text=f"⏱ {hours}h {minutes}m {seconds}s • 👤 {uploader}"
        )
        
        # Show info section
        self.info_section.pack(fill=tk.X, pady=(0, 20))
        
        # Populate quality listbox
        self.quality_listbox.delete(0, tk.END)
        self.audio_format_options = []

        # Native audio formats (only those actually present in this video)
        for af in self.available_audio_formats:
            abr_str = f" · {int(af['abr'])}kbps" if af['abr'] else ""
            display = f"🎵 {af['codec_display']} — native, no re-encode{abr_str}"
            self.audio_format_options.append({
                'display': display,
                'native': True,
                'format_id': af['format_id'],
                'codec': af['codec_key'],
                'container': af['container'],
            })
            self.quality_listbox.insert(tk.END, display)

        # Transcoded formats — always available if any audio stream exists (requires FFmpeg)
        if self.available_audio_formats:
            for codec, label, note in [
                ('mp3',  'MP3',  '192kbps · requires FFmpeg'),
                ('flac', 'FLAC', 'lossless · requires FFmpeg'),
                ('wav',  'WAV',  'lossless PCM · requires FFmpeg'),
            ]:
                display = f"🎵 {label} — {note}"
                self.audio_format_options.append({
                    'display': display,
                    'native': False,
                    'format_id': None,
                    'codec': codec,
                    'container': codec,
                })
                self.quality_listbox.insert(tk.END, display)

        # Sort resolutions by height
        sorted_resolutions = sorted(
            self.resolution_formats.items(),
            key=lambda x: int(x[0].split('x')[1]),
            reverse=True
        )
        
        for resolution, formats in sorted_resolutions:
            best_format = max(formats, key=lambda x: (x['has_audio'], x['fps']))
            
            width, height = resolution.split('x')
            filesize = best_format['filesize']
            fps = best_format['fps']
            has_audio = "✓" if best_format['has_audio'] else "✗"
            
            # Format filesize
            if filesize > 0:
                if filesize > 1_000_000_000:
                    size_str = f"{filesize / 1_000_000_000:.1f} GB"
                else:
                    size_str = f"{filesize / 1_000_000:.1f} MB"
            else:
                size_str = "Unknown"
            
            # Quality label
            height_int = int(height)
            if height_int >= 2160:
                quality = "4K"
            elif height_int >= 1440:
                quality = "2K"
            elif height_int >= 1080:
                quality = "Full HD"
            elif height_int >= 720:
                quality = "HD"
            elif height_int >= 480:
                quality = "SD"
            else:
                quality = "Low"
            
            display_text = f"{resolution} ({quality}) • {fps}fps • Audio: {has_audio} • ~{size_str}"
            self.quality_listbox.insert(tk.END, display_text)
        
        self.status_var.set("Video analyzed. Select quality and download location.")
        
    def on_quality_select(self, event):
        """Handle quality selection"""
        selection = self.quality_listbox.curselection()
        if not selection:
            return
        
        idx = selection[0]
        num_audio = len(self.audio_format_options)

        # Audio option selected
        if idx < num_audio:
            audio_opt = self.audio_format_options[idx]
            self.selected_format = 'audio'
            self.selected_audio_download_opts = audio_opt
            self.download_btn.config(state=tk.NORMAL)
            label = audio_opt['display'].replace('🎵 ', '')
            self.status_var.set(f"Ready to download: {label}")
            return

        # Video resolution selected
        video_idx = idx - num_audio
        sorted_resolutions = sorted(
            self.resolution_formats.items(),
            key=lambda x: int(x[0].split('x')[1]),
            reverse=True
        )

        resolution, formats = sorted_resolutions[video_idx]
        best_format = max(formats, key=lambda x: (x['has_audio'], x['fps']))

        self.selected_format = best_format['format_id']

        # Enable download button
        self.download_btn.config(state=tk.NORMAL)

        self.status_var.set(f"Ready to download at {resolution}")
        
    def browse_location(self):
        """Browse for download location"""
        directory = filedialog.askdirectory(initialdir=self.output_var.get())
        if directory:
            self.output_var.set(directory)
            # Auto-check for partial downloads when directory changes
            self.check_partial_downloads()
    
    def check_partial_downloads(self):
        """Scan download directory for .part files"""
        print("DEBUG: check_partial_downloads called")  # Debug output
        self.partial_downloads = []
        self.resume_listbox.delete(0, tk.END)
        
        # Always show the resume section when checking
        self.resume_section.pack(fill=tk.X, padx=20, pady=(10, 20))
        
        try:
            download_path = Path(self.output_var.get())
            print(f"DEBUG: Checking directory: {download_path}")  # Debug output
            
            if not download_path.exists():
                # Show section with error message
                self.resume_listbox.insert(0, f"Error: Directory does not exist: {download_path}")
                self.resume_section.pack(fill=tk.X, padx=20, pady=(10, 20))
                self.status_var.set("Directory not found")
                return
            
            # Find all .part files (case-insensitive search)
            part_files = list(download_path.glob("*.part"))
            part_files.extend(list(download_path.glob("*.PART")))  # Also check uppercase
            print(f"DEBUG: Found {len(part_files)} .part files")  # Debug output
            
            if not part_files:
                self.resume_listbox.insert(0, "No partial downloads found in this directory.")
                self.resume_section.pack(fill=tk.X, padx=20, pady=(10, 20))
                self.status_var.set("No partial downloads found")
                return
            
            found_count = 0
            for part_file in part_files:
                # Skip fragment files
                if "-Frag" in part_file.name or "-frag" in part_file.name:
                    continue
                
                found_count += 1
                
                # Get file size
                try:
                    size_bytes = part_file.stat().st_size
                    if size_bytes > 1_000_000_000:
                        size_str = f"{size_bytes / 1_000_000_000:.2f} GB"
                    else:
                        size_str = f"{size_bytes / 1_000_000:.2f} MB"
                except Exception as e:
                    size_str = "Unknown"
                    size_bytes = 0
                
                # Try to get video name from filename (remove .part extension)
                video_name = part_file.stem
                
                # Check if corresponding .ytdl file exists for metadata
                ytdl_file = part_file.with_suffix('.part.ytdl')
                if not ytdl_file.exists():
                    ytdl_file = part_file.parent / f"{video_name}.ytdl"
                
                self.partial_downloads.append({
                    'part_file': str(part_file),
                    'video_name': video_name,
                    'size': size_str,
                    'size_bytes': size_bytes,
                    'ytdl_file': str(ytdl_file) if ytdl_file.exists() else None
                })
                
                # Display in listbox
                display_text = f"{video_name} ({size_str})"
                self.resume_listbox.insert(tk.END, display_text)
            
            # Always show resume section with results
            if self.partial_downloads:
                self.resume_section.pack(fill=tk.X, padx=20, pady=(10, 20))
                self.status_var.set(f"Found {len(self.partial_downloads)} partial download(s)")
            else:
                self.resume_listbox.insert(0, f"Found {found_count} .part file(s), but all are fragments. No resumable downloads.")
                self.resume_section.pack(fill=tk.X, padx=20, pady=(10, 20))
                self.status_var.set("No resumable downloads found")
                
        except Exception as e:
            error_msg = f"Error checking for partial downloads: {str(e)}"
            self.resume_listbox.insert(0, error_msg)
            self.resume_section.pack(fill=tk.X, padx=20, pady=(10, 20))
            self.status_var.set(f"Error: {str(e)}")
            print(f"Error in check_partial_downloads: {e}")
            import traceback
            traceback.print_exc()
    
    def on_resume_select(self, event):
        """Handle resume selection"""
        selection = self.resume_listbox.curselection()
        if not selection:
            self.selected_partial = None
            self.resume_btn.config(state=tk.DISABLED)
            return
        
        idx = selection[0]
        if idx < len(self.partial_downloads):
            self.selected_partial = self.partial_downloads[idx]
            self.resume_btn.config(state=tk.NORMAL)
    
    def resume_download(self):
        """Resume a partial download"""
        if not self.selected_partial or self.is_downloading:
            return
        
        part_file = Path(self.selected_partial['part_file'])
        
        # Try to extract URL from .ytdl file if it exists
        url = None
        if self.selected_partial['ytdl_file']:
            try:
                with open(self.selected_partial['ytdl_file'], 'r') as f:
                    import json
                    metadata = json.load(f)
                    url = metadata.get('url') or metadata.get('webpage_url')
            except:
                pass
        
        # If no URL found, prompt user
        if not url:
            url = simpledialog.askstring(
                "Resume Download",
                f"Enter the YouTube URL for:\n{self.selected_partial['video_name']}\n\n"
                "This is needed to resume the download."
            )
            if not url:
                return
        
        # Set the URL and start download
        self.url_var.set(url)
        
        # Disable buttons
        self.resume_btn.config(state=tk.DISABLED)
        self.is_downloading = True
        
        # Show progress
        self.progress_section.pack(fill=tk.X)
        self.progress_var.set(0)
        self.status_var.set("Resuming download...")
        
        # Start resume download in separate thread
        thread = threading.Thread(target=self._resume_download_thread, args=(url, str(part_file)))
        thread.daemon = False
        thread.start()
    
    def _resume_download_thread(self, url, part_file_path):
        """Thread function to resume download"""
        try:
            output_path = self.output_var.get()
            part_file = Path(part_file_path)
            
            # yt-dlp will automatically resume if .part file exists
            # We need to determine the format from the existing file or use best
            ydl_opts = {
                'format': 'bestvideo+bestaudio/best',
                'outtmpl': str(part_file.with_suffix('')),  # Remove .part extension
                'merge_output_format': 'mp4',
                'progress_hooks': [self._progress_hook],
                'continuedl': True,  # Resume partial downloads
                'noplaylist': True,
                'keepvideo': False,
                'nocheckcertificate': True,
                'no_check_certificate': True,
                'ignoreerrors': True,
                'retries': 10,
                'fragment_retries': 10,
                'file_access_retries': 3,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            
            # Remove .part extension if download completed
            final_file = part_file.with_suffix('')
            if final_file.exists() and part_file.exists():
                # File was completed and renamed
                pass
            
            # Update UI on completion
            self.root.after(0, self._download_complete)
            
        except Exception as e:
            self.root.after(0, lambda: self._download_error(str(e)))
            
    def start_download(self):
        """Start the download process"""
        if self.is_downloading:
            messagebox.showinfo("Download in Progress", "A download is already in progress")
            return
        
        if not self.selected_format:
            messagebox.showwarning("No Quality Selected", "Please select a quality first")
            return
        
        # Disable download button
        self.download_btn.config(state=tk.DISABLED)
        self.is_downloading = True
        
        # Show progress section
        self.progress_section.pack(fill=tk.X)
        self.progress_var.set(0)
        self.status_var.set("Starting download...")
        
        # Start download in separate thread (non-daemon so it can finish merge)
        thread = threading.Thread(target=self._download_thread)
        thread.daemon = False  # Allow thread to complete merge even if GUI stays alive
        thread.start()
        
    def _download_thread(self):
        """Thread function to download video"""
        try:
            url = self.url_var.get().strip()
            output_path = self.output_var.get()
            format_id = self.selected_format
            
            # Create output directory if it doesn't exist
            os.makedirs(output_path, exist_ok=True)
            
            # Check if audio download is requested
            if format_id == 'audio':
                audio_opt = self.selected_audio_download_opts
                if audio_opt.get('native'):
                    ydl_opts = {
                        'format': audio_opt['format_id'],
                        'outtmpl': os.path.join(output_path, '%(title)s.%(ext)s'),
                        'progress_hooks': [self._progress_hook],
                        'continuedl': True,
                        'noplaylist': True,
                        'nocheckcertificate': True,
                        'no_check_certificate': True,
                        'ignoreerrors': True,
                        'retries': 10,
                        'fragment_retries': 10,
                        'file_access_retries': 3,
                    }
                else:
                    codec = audio_opt['codec']
                    quality = '0' if codec in ('flac', 'wav') else '192'
                    ydl_opts = {
                        'format': 'bestaudio/best',
                        'outtmpl': os.path.join(output_path, '%(title)s.%(ext)s'),
                        'postprocessors': [{
                            'key': 'FFmpegExtractAudio',
                            'preferredcodec': codec,
                            'preferredquality': quality,
                        }],
                        'progress_hooks': [self._progress_hook],
                        'continuedl': True,
                        'noplaylist': True,
                        'nocheckcertificate': True,
                        'no_check_certificate': True,
                        'ignoreerrors': True,
                        'retries': 10,
                        'fragment_retries': 10,
                        'file_access_retries': 3,
                    }
            else:
                ydl_opts = {
                    'format': f'{format_id}+bestaudio/best',
                    'outtmpl': os.path.join(output_path, '%(title)s.%(ext)s'),
                    'merge_output_format': 'mp4',
                    'progress_hooks': [self._progress_hook],
                    'continuedl': True,  # Resume partial downloads
                    'noplaylist': True,
                    'keepvideo': False,
                    'nocheckcertificate': True,
                    'no_check_certificate': True,  # Alternative format
                    'ignoreerrors': True,
                    'retries': 10,  # Retry on failures
                    'fragment_retries': 10,  # Retry fragment downloads
                    'file_access_retries': 3,  # Retry file access errors
                }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            
            # Update UI on completion
            self.root.after(0, self._download_complete)
            
        except Exception as e:
            error_msg = str(e)
            if format_id == 'audio' and ('ffmpeg' in error_msg.lower() or 'FFmpeg' in error_msg):
                audio_opt = self.selected_audio_download_opts or {}
                if not audio_opt.get('native'):
                    codec = audio_opt.get('codec', 'audio').upper()
                    error_msg = f"{error_msg}\n\nNote: {codec} conversion requires FFmpeg to be installed.\nPlease install FFmpeg and try again."
            self.root.after(0, lambda: self._download_error(error_msg))
            
    def _progress_hook(self, d):
        """Progress hook for download"""
        if d['status'] == 'downloading':
            try:
                downloaded = d.get('downloaded_bytes', 0)
                total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
                
                if total > 0:
                    percent = min((downloaded / total) * 100, 98.0)  # Cap at 98% until merge
                    # Fix lambda variable capture by storing in local variable
                    def update_progress(p=percent):
                        self.progress_var.set(p)
                    self.root.after(0, update_progress)
                
                speed = d.get('speed', 0)
                eta = d.get('eta', 0)
                
                if speed:
                    speed_str = f"{speed / 1_000_000:.1f} MB/s"
                else:
                    speed_str = "Calculating..."
                
                if eta:
                    eta_min = eta // 60
                    eta_sec = eta % 60
                    eta_str = f"{int(eta_min)}m {int(eta_sec)}s"
                else:
                    eta_str = "Calculating..."
                
                details = f"Speed: {speed_str} • ETA: {eta_str}"
                def update_status(s=f"Downloading... {details}"):
                    self.status_var.set(s)
                self.root.after(0, update_status)
                
            except Exception as e:
                print(f"Progress hook error: {e}")
                pass
                
        elif d['status'] == 'finished':
            def update_finished():
                self.status_var.set("Merging video and audio... (This may take a moment)")
                self.progress_var.set(99)  # Set to 99% during merge phase
            self.root.after(0, update_finished)
            
    def _download_complete(self):
        """Handle download completion"""
        self.is_downloading = False
        self.download_btn.config(state=tk.NORMAL)
        self.progress_var.set(100)  # Ensure progress shows 100%
        self.status_var.set("✓ Download completed successfully!")
        
        messagebox.showinfo(
            "Download Complete",
            f"Video downloaded successfully!\n\nSaved to: {self.output_var.get()}"
        )
        
    def _download_error(self, error_msg):
        """Handle download error"""
        self.is_downloading = False
        self.download_btn.config(state=tk.NORMAL)
        self.status_var.set("✗ Download failed")
        
        messagebox.showerror("Download Error", f"Download failed:\n\n{error_msg}")
        
    def _show_error(self, message):
        """Show error message"""
        self.analyze_btn.config(state=tk.NORMAL, text="Analyze Video")
        self.status_var.set("Error occurred")
        messagebox.showerror("Error", message)


def main():
    """Main function to run the GUI"""
    root = tk.Tk()
    app = YouTubeDownloaderGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()