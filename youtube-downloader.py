#!/usr/bin/env python3
"""
YouTube Video Downloader
Detects all available resolutions and lets you choose which one to download
Handles long videos (4+ hours)
"""

import sys
import os
from collections import defaultdict

try:
    import yt_dlp
except ImportError:
    print("ERROR: yt-dlp is not installed!")
    print("Please install it by running:")
    print("  pip install yt-dlp")
    sys.exit(1)


def get_available_formats(url):
    """
    Fetch and parse all available formats for a video
    
    Args:
        url: YouTube video URL
        
    Returns:
        tuple: (video_info, grouped_formats)
    """
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'nocheckcertificate': True,
        'ignoreerrors': True
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
    
    # Group formats by resolution
    resolution_formats = defaultdict(list)
    
    for fmt in info.get('formats', []):
        # Only consider formats with both video and audio, or video-only formats
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
    
    return info, resolution_formats


def display_formats(video_info, resolution_formats):
    """
    Display available resolutions in a user-friendly format
    
    Args:
        video_info: Video metadata
        resolution_formats: Dictionary of available formats grouped by resolution
    """
    title = video_info.get('title', 'Unknown')
    duration = video_info.get('duration', 0)
    uploader = video_info.get('uploader', 'Unknown')
    
    hours = duration // 3600
    minutes = (duration % 3600) // 60
    seconds = duration % 60
    
    print("\n" + "=" * 70)
    print(f"Video: {title}")
    print(f"Uploader: {uploader}")
    print(f"Duration: {hours}h {minutes}m {seconds}s")
    print("=" * 70)
    
    # Sort resolutions by height (descending)
    sorted_resolutions = sorted(
        resolution_formats.items(),
        key=lambda x: int(x[0].split('x')[1]),
        reverse=True
    )
    
    print("\nAvailable Resolutions:")
    print("-" * 70)
    
    resolution_map = {}
    choice_num = 1
    
    for resolution, formats in sorted_resolutions:
        # Get best format for this resolution (prefer formats with audio)
        best_format = max(formats, key=lambda x: (x['has_audio'], x['fps']))
        
        width, height = resolution.split('x')
        filesize = best_format['filesize']
        fps = best_format['fps']
        has_audio = "✓" if best_format['has_audio'] else "✗"
        
        # Format filesize
        if filesize > 0:
            if filesize > 1_000_000_000:
                size_str = f"{filesize / 1_000_000_000:.2f} GB"
            else:
                size_str = f"{filesize / 1_000_000:.2f} MB"
        else:
            size_str = "Unknown"
        
        # Determine quality label
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
        
        print(f"[{choice_num}] {resolution:>10} ({quality:>8}) @ {fps:>3}fps | "
              f"Audio: {has_audio} | Size: ~{size_str:>10} | {best_format['ext']}")
        
        resolution_map[str(choice_num)] = (resolution, best_format['format_id'])
        choice_num += 1
    
    print("-" * 70)
    return resolution_map


def download_video(url, format_id, output_path="downloads"):
    """
    Download a YouTube video with the specified format
    
    Args:
        url: YouTube video URL
        format_id: Format ID to download
        output_path: Directory to save the video (default: 'downloads')
    """
    
    # Create output directory if it doesn't exist
    os.makedirs(output_path, exist_ok=True)
    
    # Configure yt-dlp options
    ydl_opts = {
        # Format selection: specified format + best audio, or best available
        'format': f'{format_id}+bestaudio/best',
        
        # Output template
        'outtmpl': os.path.join(output_path, '%(title)s.%(ext)s'),
        
        # Merge into MP4 container
        'merge_output_format': 'mp4',
        
        # Show progress
        'progress_hooks': [progress_hook],
        
        # Continue partial downloads
        'continuedl': True,
        
        # No playlist, just single video
        'noplaylist': True,
        
        # Keep video after post-processing
        'keepvideo': False,
        
        # SSL certificate bypass
        'nocheckcertificate': True,
        'ignoreerrors': True
    }
    
    try:
        print("\n" + "=" * 70)
        print("Starting download...")
        print("=" * 70)
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
            
        print("\n" + "=" * 70)
        print("✓ Download completed successfully!")
        print(f"✓ Saved to: {output_path}/")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n✗ ERROR: Download failed!")
        print(f"Error details: {str(e)}")
        sys.exit(1)


def progress_hook(d):
    """Display download progress"""
    if d['status'] == 'downloading':
        # Extract progress info
        percent = d.get('_percent_str', 'N/A')
        speed = d.get('_speed_str', 'N/A')
        eta = d.get('_eta_str', 'N/A')
        downloaded = d.get('_downloaded_bytes_str', 'N/A')
        total = d.get('_total_bytes_str', 'N/A')
        
        # Print progress on same line
        print(f"\r⬇ {downloaded}/{total} | {percent} | {speed} | ETA: {eta}    ", 
              end='', flush=True)
        
    elif d['status'] == 'finished':
        print("\n✓ Download finished! Merging video and audio...")


def main():
    """Main function"""
    print("\n" + "=" * 70)
    print(" " * 20 + "YouTube Video Downloader")
    print("=" * 70)
    
    # Get URL from command line or prompt user
    if len(sys.argv) > 1:
        url = sys.argv[1]
        output_path = sys.argv[2] if len(sys.argv) > 2 else "downloads"
        auto_mode = len(sys.argv) > 3  # If format specified, use auto mode
    else:
        url = input("\nEnter YouTube video URL: ").strip()
        output_path = input("Output directory [downloads]: ").strip()
        if not output_path:
            output_path = "downloads"
        auto_mode = False
    
    if not url:
        print("✗ ERROR: No URL provided!")
        sys.exit(1)
    
    # Validate URL
    if 'youtube.com' not in url and 'youtu.be' not in url:
        print("⚠ WARNING: This doesn't look like a YouTube URL")
        if not auto_mode:
            confirm = input("Continue anyway? (y/n): ").lower()
            if confirm != 'y':
                sys.exit(0)
    
    try:
        print("\n⏳ Fetching video information and available formats...")
        video_info, resolution_formats = get_available_formats(url)
        
        if not resolution_formats:
            print("✗ ERROR: No video formats found!")
            sys.exit(1)
        
        # Display formats and get user choice
        resolution_map = display_formats(video_info, resolution_formats)
        
        # Auto mode for command-line usage
        if auto_mode and len(sys.argv) > 3:
            choice = sys.argv[3]
        else:
            print("\nOptions:")
            print("  - Enter a number to select resolution")
            print("  - Enter 'best' for highest quality")
            print("  - Enter 'q' to quit")
            choice = input("\nYour choice: ").strip().lower()
        
        if choice == 'q':
            print("Cancelled.")
            sys.exit(0)
        elif choice == 'best':
            # Get highest resolution
            resolution, format_id = list(resolution_map.values())[0]
            print(f"\n✓ Selected: {resolution} (Best Quality)")
        elif choice in resolution_map:
            resolution, format_id = resolution_map[choice]
            print(f"\n✓ Selected: {resolution}")
        else:
            print(f"✗ Invalid choice: {choice}")
            sys.exit(1)
        
        # Download the video
        download_video(url, format_id, output_path)
        
    except KeyboardInterrupt:
        print("\n\n⚠ Download cancelled by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\n✗ ERROR: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
