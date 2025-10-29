#!/usr/bin/env python3
"""
YouTube Downloader Pro - Startup Script
Installs dependencies and starts the web application
"""

import subprocess
import sys
import os
from pathlib import Path

def check_package_installed(package_name):
    """Check if a package is already installed"""
    try:
        __import__(package_name.replace('-', '_'))
        return True
    except ImportError:
        return False

def install_requirements():
    """Install required packages only if missing"""
    print("Checking dependencies...")
    
    # Read requirements file
    try:
        with open("requirements.txt", "r") as f:
            requirements = f.read().strip().split("\n")
    except FileNotFoundError:
        print("❌ requirements.txt not found!")
        return False
    
    # Check which packages are missing
    missing_packages = []
    for requirement in requirements:
        if requirement.strip() and not requirement.startswith("#"):
            # Extract package name (before == or >=)
            package_name = requirement.split("==")[0].split(">=")[0].split(" ")[0].strip()
            
            # Try to import to check if installed
            import_name = package_name.replace('-', '_')
            if package_name == "Flask-SocketIO":
                import_name = "flask_socketio"
            elif package_name == "yt-dlp":
                import_name = "yt_dlp"
            elif package_name == "python-socketio":
                import_name = "socketio"
            
            try:
                __import__(import_name)
            except ImportError:
                missing_packages.append(requirement.strip())
    
    if missing_packages:
        print(f"📦 Installing {len(missing_packages)} missing package(s)...")
        try:
            subprocess.check_call([
                sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
            ])
            print("✅ Dependencies installed successfully!")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install dependencies: {e}")
            return False
    else:
        print("✅ All dependencies are already installed!")
        return True

def start_application():
    """Start the Flask application"""
    print("\n🚀 Starting YouTube Downloader Pro...")
    print("📱 Open your browser and go to: http://localhost:8000")
    print("🛑 Press Ctrl+C to stop the server\n")
    
    try:
        from app import app, socketio
        socketio.run(app, debug=False, host='0.0.0.0', port=8000)
    except KeyboardInterrupt:
        print("\n👋 Server stopped. Goodbye!")
    except Exception as e:
        print(f"❌ Error starting server: {e}")

def main():
    """Main function"""
    print("=" * 60)
    print("🎬 YouTube Downloader Pro - Web Edition")
    print("=" * 60)
    
    # Check if we're in the right directory
    if not os.path.exists("app.py"):
        print("❌ Error: app.py not found!")
        print("Please run this script from the YouTube Downloader directory.")
        sys.exit(1)
    
    # Install requirements
    if not install_requirements():
        sys.exit(1)
    
    # Start the application
    start_application()

if __name__ == "__main__":
    main()
