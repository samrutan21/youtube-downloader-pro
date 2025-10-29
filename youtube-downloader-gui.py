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
    from tkinter import ttk, filedialog, messagebox
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
        
        self.setup_ui()
        self.apply_theme()
        
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
            fg=self.text_primary,
            activebackground="#005a9e",
            activeforeground=self.text_primary,
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
            fg=self.text_primary,
            activebackground=self.bg_tertiary,
            activeforeground=self.text_primary,
            relief=tk.FLAT,
            cursor="hand2",
            command=self.browse_location,
            bd=0,
            highlightthickness=0
        )
        browse_btn.pack(side=tk.RIGHT, padx=(10, 15), pady=10)
        
        # Download Button
        self.download_btn = tk.Button(
            location_section,
            text="Download Video",
            font=("SF Pro Text", 14, "bold"),
            bg=self.accent_green,
            fg=self.text_primary,
            activebackground="#00a041",
            activeforeground=self.text_primary,
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
            
            self.video_info = info
            self.resolution_formats = resolution_formats
            
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
        sorted_resolutions = sorted(
            self.resolution_formats.items(),
            key=lambda x: int(x[0].split('x')[1]),
            reverse=True
        )
        
        resolution, formats = sorted_resolutions[idx]
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
        
        # Start download in separate thread
        thread = threading.Thread(target=self._download_thread)
        thread.daemon = True
        thread.start()
        
    def _download_thread(self):
        """Thread function to download video"""
        try:
            url = self.url_var.get().strip()
            output_path = self.output_var.get()
            format_id = self.selected_format
            
            # Create output directory if it doesn't exist
            os.makedirs(output_path, exist_ok=True)
            
            ydl_opts = {
                'format': f'{format_id}+bestaudio/best',
                'outtmpl': os.path.join(output_path, '%(title)s.%(ext)s'),
                'merge_output_format': 'mp4',
                'progress_hooks': [self._progress_hook],
                'continuedl': True,
                'noplaylist': True,
                'keepvideo': False,
                'nocheckcertificate': True,
                'no_check_certificate': True,  # Alternative format
                'ignoreerrors': True
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            
            # Update UI on completion
            self.root.after(0, self._download_complete)
            
        except Exception as e:
            self.root.after(0, lambda: self._download_error(str(e)))
            
    def _progress_hook(self, d):
        """Progress hook for download"""
        if d['status'] == 'downloading':
            try:
                downloaded = d.get('downloaded_bytes', 0)
                total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
                
                if total > 0:
                    percent = (downloaded / total) * 100
                    self.root.after(0, lambda: self.progress_var.set(percent))
                
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
                self.root.after(0, lambda: self.status_var.set(f"Downloading... {details}"))
                
            except Exception:
                pass
                
        elif d['status'] == 'finished':
            self.root.after(0, lambda: self.status_var.set("Download complete! Processing..."))
            self.root.after(0, lambda: self.progress_var.set(100))
            
    def _download_complete(self):
        """Handle download completion"""
        self.is_downloading = False
        self.download_btn.config(state=tk.NORMAL)
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