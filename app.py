#!/usr/bin/env python3
"""
YouTube Downloader - Professional Web Application
Modern web interface with Flask backend
"""

import os
import sys
import json
import threading
import ssl
from pathlib import Path
from collections import defaultdict
from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_socketio import SocketIO, emit

# Disable SSL verification at Python level for macOS compatibility
# This MUST be done before importing yt_dlp
ssl._create_default_https_context = ssl._create_unverified_context

# Set environment variables to disable SSL verification
os.environ['PYTHONHTTPSVERIFY'] = '0'
os.environ['CURL_CA_BUNDLE'] = ''

# Import yt_dlp after SSL context is disabled
import yt_dlp

# Also disable SSL verification for urllib3/requests if available
try:
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
except ImportError:
    pass

app = Flask(__name__)
app.config['SECRET_KEY'] = 'youtube_downloader_secret_key'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

class YouTubeDownloader:
    def __init__(self):
        self.downloads = {}
        self.download_threads = {}
        
    def analyze_video(self, url):
        """Analyze video and return available formats"""
        try:
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'nocheckcertificate': True,
                'ignoreerrors': True,
                'no_check_certificate': True,
                'extractor_args': {
                    'youtube': {
                        'skip': ['dash', 'hls']
                    }
                }
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
            
            # Check if info extraction was successful
            if info is None:
                return {
                    'success': False,
                    'error': 'Failed to extract video information. The video may be unavailable or restricted.'
                }
            
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
            
            # Prepare response
            video_info = {
                'title': info.get('title', 'Unknown'),
                'duration': info.get('duration', 0),
                'uploader': info.get('uploader', 'Unknown'),
                'thumbnail': info.get('thumbnail', ''),
                'description': info.get('description', ''),
                'view_count': info.get('view_count', 0),
                'like_count': info.get('like_count', 0)
            }
            
            # Sort resolutions by height
            sorted_resolutions = sorted(
                resolution_formats.items(),
                key=lambda x: int(x[0].split('x')[1]),
                reverse=True
            )
            
            formats = []
            for resolution, format_list in sorted_resolutions:
                best_format = max(format_list, key=lambda x: (x['has_audio'], x['fps']))
                
                width, height = resolution.split('x')
                filesize = best_format['filesize']
                fps = best_format['fps']
                has_audio = best_format['has_audio']
                
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
                
                formats.append({
                    'format_id': best_format['format_id'],
                    'resolution': resolution,
                    'quality': quality,
                    'fps': fps,
                    'has_audio': has_audio,
                    'size': size_str,
                    'ext': best_format['ext']
                })
            
            return {
                'success': True,
                'video_info': video_info,
                'formats': formats
            }
            
        except Exception as e:
            error_msg = str(e)
            # Provide more helpful error messages
            if 'SSL' in error_msg or 'CERTIFICATE' in error_msg:
                error_msg = f"SSL Certificate Error: {error_msg}. Please ensure SSL verification is properly disabled."
            elif "'NoneType' object has no attribute 'get'" in error_msg:
                error_msg = "Failed to extract video information. The video may be unavailable, private, or restricted. Please check the URL and try again."
            
            return {
                'success': False,
                'error': error_msg
            }
    
    def download_video(self, url, format_id, output_path, download_id):
        """Download video with progress updates"""
        try:
            # Create output directory if it doesn't exist
            os.makedirs(output_path, exist_ok=True)
            
            def progress_hook(d):
                if d['status'] == 'downloading':
                    try:
                        downloaded = d.get('downloaded_bytes', 0)
                        total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
                        
                        if total > 0:
                            percent = (downloaded / total) * 100
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
                            
                            # Emit progress update
                            socketio.emit('download_progress', {
                                'download_id': download_id,
                                'percent': percent,
                                'speed': speed_str,
                                'eta': eta_str,
                                'status': 'downloading'
                            })
                            
                    except Exception:
                        pass
                        
                elif d['status'] == 'finished':
                    socketio.emit('download_progress', {
                        'download_id': download_id,
                        'percent': 100,
                        'status': 'finished'
                    })
            
            ydl_opts = {
                'format': f'{format_id}+bestaudio/best',
                'outtmpl': os.path.join(output_path, '%(title)s.%(ext)s'),
                'merge_output_format': 'mp4',
                'progress_hooks': [progress_hook],
                'continuedl': True,
                'noplaylist': True,
                'keepvideo': False,
                'nocheckcertificate': True,
                'ignoreerrors': True
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            
            # Mark download as complete
            self.downloads[download_id]['status'] = 'completed'
            socketio.emit('download_complete', {
                'download_id': download_id,
                'message': 'Download completed successfully!'
            })
            
        except Exception as e:
            self.downloads[download_id]['status'] = 'error'
            socketio.emit('download_error', {
                'download_id': download_id,
                'error': str(e)
            })

# Initialize downloader
downloader = YouTubeDownloader()

@app.route('/')
def index():
    """Serve the main page"""
    return render_template('index.html')

@app.route('/api/analyze', methods=['POST'])
def analyze_video():
    """Analyze video URL"""
    data = request.get_json()
    url = data.get('url', '').strip()
    
    if not url:
        return jsonify({'success': False, 'error': 'No URL provided'})
    
    result = downloader.analyze_video(url)
    return jsonify(result)

@app.route('/api/download', methods=['POST'])
def start_download():
    """Start video download"""
    data = request.get_json()
    url = data.get('url', '').strip()
    format_id = data.get('format_id', '')
    output_path = data.get('output_path', str(Path.home() / "Downloads"))
    
    if not url or not format_id:
        return jsonify({'success': False, 'error': 'Missing required parameters'})
    
    # Generate unique download ID
    import uuid
    download_id = str(uuid.uuid4())
    
    # Store download info
    downloader.downloads[download_id] = {
        'url': url,
        'format_id': format_id,
        'output_path': output_path,
        'status': 'starting'
    }
    
    # Start download in separate thread
    thread = threading.Thread(
        target=downloader.download_video,
        args=(url, format_id, output_path, download_id)
    )
    thread.daemon = True
    thread.start()
    
    downloader.download_threads[download_id] = thread
    
    return jsonify({
        'success': True,
        'download_id': download_id
    })

@app.route('/api/downloads')
def get_downloads():
    """Get all downloads"""
    return jsonify(downloader.downloads)

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    print('Client connected')
    emit('connected', {'message': 'Connected to server'})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    print('Client disconnected')

if __name__ == '__main__':
    # Create templates directory if it doesn't exist
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static/css', exist_ok=True)
    os.makedirs('static/js', exist_ok=True)
    
    print("Starting YouTube Downloader Pro...")
    print("Open your browser and go to: http://localhost:8000")
    socketio.run(app, debug=False, host='0.0.0.0', port=8000, allow_unsafe_werkzeug=True)
