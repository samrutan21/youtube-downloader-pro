// YouTube Downloader Pro - Frontend Application
class YouTubeDownloaderApp {
    constructor() {
        this.socket = null;
        this.currentVideo = null;
        this.selectedQuality = null;
        this.downloadId = null;
        this.isDownloading = false;
        
        this.init();
    }
    
    init() {
        // Ensure loading overlay is hidden on startup
        this.hideLoading();
        this.setupSocketConnection();
        this.bindEvents();
        this.setDefaultDownloadPath();
    }
    
    setupSocketConnection() {
        // Try to connect to Socket.IO
        try {
            this.socket = io();
            
            this.socket.on('connect', () => {
                console.log('Connected to server');
                this.showToast('Connected to server', 'success');
            });
            
            this.socket.on('disconnect', () => {
                console.log('Disconnected from server');
                this.showToast('Disconnected from server', 'warning');
            });
        } catch (error) {
            console.error('Socket.IO connection error:', error);
            // Continue without Socket.IO for now
            this.socket = null;
        }
        
        this.socket.on('download_progress', (data) => {
            this.updateDownloadProgress(data);
        });
        
        this.socket.on('download_complete', (data) => {
            this.handleDownloadComplete(data);
        });
        
        this.socket.on('download_error', (data) => {
            this.handleDownloadError(data);
        });
    }
    
    bindEvents() {
        // URL Analysis
        document.getElementById('analyzeBtn').addEventListener('click', () => {
            this.analyzeVideo();
        });
        
        document.getElementById('videoUrl').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.analyzeVideo();
            }
        });
        
        // Download
        document.getElementById('downloadBtn').addEventListener('click', () => {
            this.startDownload();
        });
        
        // Browse folder
        document.getElementById('browseBtn').addEventListener('click', () => {
            this.browseDownloadPath();
        });
        
        // Progress controls
        document.getElementById('pauseBtn').addEventListener('click', () => {
            this.pauseDownload();
        });
        
        document.getElementById('cancelBtn').addEventListener('click', () => {
            this.cancelDownload();
        });
        
        // Clear history
        document.getElementById('clearHistoryBtn').addEventListener('click', () => {
            this.clearDownloadHistory();
        });
    }
    
    setDefaultDownloadPath() {
        const defaultPath = `${navigator.userAgent.includes('Windows') ? 'C:\\Users\\User\\Downloads' : '~/Downloads'}`;
        document.getElementById('downloadPath').value = defaultPath;
    }
    
    async analyzeVideo() {
        const url = document.getElementById('videoUrl').value.trim();
        
        if (!url) {
            this.showToast('Please enter a YouTube URL', 'error');
            return;
        }
        
        if (!this.isValidYouTubeUrl(url)) {
            const confirmed = confirm('This doesn\'t look like a YouTube URL. Continue anyway?');
            if (!confirmed) return;
        }
        
        console.log('Starting video analysis for URL:', url);
        this.showLoading('Analyzing video...');
        
        try {
            const response = await fetch('/api/analyze', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ url })
            });
            
            console.log('Response status:', response.status);
            const result = await response.json();
            console.log('Response data:', result);
            
            if (result.success) {
                this.currentVideo = result;
                this.displayVideoInfo(result.video_info);
                this.displayQualityOptions(result.formats);
                this.showToast('Video analyzed successfully!', 'success');
            } else {
                console.error('Analysis failed:', result.error);
                this.showToast(`Analysis failed: ${result.error}`, 'error');
            }
        } catch (error) {
            console.error('Network error:', error);
            this.showToast(`Network error: ${error.message}`, 'error');
        } finally {
            this.hideLoading();
        }
    }
    
    isValidYouTubeUrl(url) {
        const patterns = [
            /^https?:\/\/(www\.)?youtube\.com\/watch\?v=/,
            /^https?:\/\/youtu\.be\//,
            /^https?:\/\/(www\.)?youtube\.com\/embed\//,
            /^https?:\/\/(www\.)?youtube\.com\/v\//
        ];
        return patterns.some(pattern => pattern.test(url));
    }
    
    displayVideoInfo(videoInfo) {
        document.getElementById('videoTitle').textContent = videoInfo.title;
        document.getElementById('videoUploader').textContent = videoInfo.uploader;
        document.getElementById('videoViews').textContent = this.formatNumber(videoInfo.view_count);
        document.getElementById('videoLikes').textContent = this.formatNumber(videoInfo.like_count);
        document.getElementById('videoDescription').textContent = videoInfo.description || 'No description available';
        document.getElementById('videoDuration').textContent = this.formatDuration(videoInfo.duration);
        
        if (videoInfo.thumbnail) {
            document.getElementById('videoThumbnail').src = videoInfo.thumbnail;
        }
        
        document.getElementById('videoInfoSection').style.display = 'block';
    }
    
    displayQualityOptions(formats) {
        const qualityGrid = document.getElementById('qualityGrid');
        qualityGrid.innerHTML = '';
        
        formats.forEach((format, index) => {
            const qualityOption = document.createElement('div');
            qualityOption.className = 'quality-option';
            qualityOption.dataset.formatId = format.format_id;
            
            qualityOption.innerHTML = `
                <div class="quality-header">
                    <span class="quality-resolution">${format.resolution}</span>
                    <span class="quality-label">${format.quality}</span>
                </div>
                <div class="quality-details">
                    <div class="quality-detail">
                        <i class="fas fa-video"></i>
                        <span>${format.fps} FPS</span>
                    </div>
                    <div class="quality-detail">
                        <i class="fas fa-volume-up"></i>
                        <span>Audio: ${format.has_audio ? 'Yes' : 'No'}</span>
                    </div>
                    <div class="quality-detail">
                        <i class="fas fa-file"></i>
                        <span>${format.ext.toUpperCase()}</span>
                    </div>
                    <div class="quality-detail">
                        <i class="fas fa-weight"></i>
                        <span>~${format.size}</span>
                    </div>
                </div>
            `;
            
            qualityOption.addEventListener('click', () => {
                this.selectQuality(qualityOption, format);
            });
            
            qualityGrid.appendChild(qualityOption);
        });
        
        document.getElementById('qualitySection').style.display = 'block';
        document.getElementById('downloadSettingsSection').style.display = 'block';
    }
    
    selectQuality(element, format) {
        // Remove previous selection
        document.querySelectorAll('.quality-option').forEach(option => {
            option.classList.remove('selected');
        });
        
        // Add selection to clicked option
        element.classList.add('selected');
        this.selectedQuality = format;
        
        // Enable download button
        document.getElementById('downloadBtn').disabled = false;
        
        this.showToast(`Selected ${format.resolution} (${format.quality})`, 'success');
    }
    
    async startDownload() {
        if (!this.selectedQuality) {
            this.showToast('Please select a quality first', 'error');
            return;
        }
        
        const url = document.getElementById('videoUrl').value.trim();
        const outputPath = document.getElementById('downloadPath').value;
        
        this.showLoading('Starting download...');
        
        try {
            const response = await fetch('/api/download', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    url: url,
                    format_id: this.selectedQuality.format_id,
                    output_path: outputPath
                })
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.downloadId = result.download_id;
                this.isDownloading = true;
                this.showProgressSection();
                this.showToast('Download started!', 'success');
            } else {
                this.showToast(`Download failed: ${result.error}`, 'error');
            }
        } catch (error) {
            this.showToast(`Network error: ${error.message}`, 'error');
        } finally {
            this.hideLoading();
        }
    }
    
    showProgressSection() {
        document.getElementById('progressSection').style.display = 'block';
        document.getElementById('downloadBtn').disabled = true;
        
        // Scroll to progress section
        document.getElementById('progressSection').scrollIntoView({ 
            behavior: 'smooth' 
        });
    }
    
    updateDownloadProgress(data) {
        if (data.download_id !== this.downloadId) return;
        
        const percent = Math.round(data.percent);
        document.getElementById('progressPercent').textContent = `${percent}%`;
        document.getElementById('downloadSpeed').textContent = data.speed || '0 MB/s';
        document.getElementById('timeRemaining').textContent = data.eta || 'Calculating...';
        document.getElementById('progressFill').style.width = `${percent}%`;
        
        if (data.status === 'downloading') {
            document.getElementById('progressStatus').textContent = 'Downloading...';
        } else if (data.status === 'finished') {
            document.getElementById('progressStatus').textContent = 'Processing video...';
        }
    }
    
    handleDownloadComplete(data) {
        if (data.download_id !== this.downloadId) return;
        
        this.isDownloading = false;
        document.getElementById('progressStatus').textContent = 'Download completed successfully!';
        document.getElementById('progressPercent').textContent = '100%';
        document.getElementById('progressFill').style.width = '100%';
        
        this.showToast('Download completed successfully!', 'success');
        this.addToDownloadHistory();
        
        // Reset after 3 seconds
        setTimeout(() => {
            this.resetDownloadState();
        }, 3000);
    }
    
    handleDownloadError(data) {
        if (data.download_id !== this.downloadId) return;
        
        this.isDownloading = false;
        document.getElementById('progressStatus').textContent = 'Download failed';
        this.showToast(`Download failed: ${data.error}`, 'error');
        
        // Reset after 3 seconds
        setTimeout(() => {
            this.resetDownloadState();
        }, 3000);
    }
    
    resetDownloadState() {
        this.isDownloading = false;
        this.downloadId = null;
        document.getElementById('downloadBtn').disabled = false;
        document.getElementById('progressSection').style.display = 'none';
        
        // Reset progress
        document.getElementById('progressPercent').textContent = '0%';
        document.getElementById('downloadSpeed').textContent = '0 MB/s';
        document.getElementById('timeRemaining').textContent = 'Calculating...';
        document.getElementById('progressFill').style.width = '0%';
        document.getElementById('progressStatus').textContent = 'Preparing download...';
    }
    
    pauseDownload() {
        // Implementation for pause functionality
        this.showToast('Pause functionality not implemented yet', 'warning');
    }
    
    cancelDownload() {
        if (this.isDownloading) {
            this.isDownloading = false;
            this.downloadId = null;
            this.resetDownloadState();
            this.showToast('Download cancelled', 'warning');
        }
    }
    
    browseDownloadPath() {
        // For web applications, we can't directly browse folders
        // Instead, we'll show a prompt for the user to enter a path
        const currentPath = document.getElementById('downloadPath').value;
        const newPath = prompt('Enter download path:', currentPath);
        
        if (newPath) {
            document.getElementById('downloadPath').value = newPath;
        }
    }
    
    addToDownloadHistory() {
        if (!this.currentVideo) return;
        
        const downloadsList = document.getElementById('downloadsList');
        const emptyState = downloadsList.querySelector('.empty-state');
        
        if (emptyState) {
            emptyState.remove();
        }
        
        const downloadItem = document.createElement('div');
        downloadItem.className = 'download-item';
        downloadItem.innerHTML = `
            <div class="download-info">
                <h4>${this.currentVideo.video_info.title}</h4>
                <p>${this.selectedQuality.resolution} (${this.selectedQuality.quality}) • ${new Date().toLocaleString()}</p>
            </div>
            <div class="download-actions">
                <button class="btn-secondary btn-small">
                    <i class="fas fa-folder-open"></i>
                    Open Folder
                </button>
            </div>
        `;
        
        downloadsList.insertBefore(downloadItem, downloadsList.firstChild);
    }
    
    clearDownloadHistory() {
        const downloadsList = document.getElementById('downloadsList');
        downloadsList.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-download"></i>
                <p>No downloads yet</p>
            </div>
        `;
        this.showToast('Download history cleared', 'success');
    }
    
    showLoading(text = 'Loading...') {
        document.getElementById('loadingText').textContent = text;
        document.getElementById('loadingOverlay').style.display = 'flex';
    }
    
    hideLoading() {
        document.getElementById('loadingOverlay').style.display = 'none';
    }
    
    showToast(message, type = 'info') {
        const toastContainer = document.getElementById('toastContainer');
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.innerHTML = `
            <div class="toast-content">
                <i class="fas fa-${this.getToastIcon(type)}"></i>
                <span>${message}</span>
            </div>
        `;
        
        toastContainer.appendChild(toast);
        
        // Auto remove after 5 seconds
        setTimeout(() => {
            toast.remove();
        }, 5000);
        
        // Click to dismiss
        toast.addEventListener('click', () => {
            toast.remove();
        });
    }
    
    getToastIcon(type) {
        const icons = {
            success: 'check-circle',
            error: 'exclamation-circle',
            warning: 'exclamation-triangle',
            info: 'info-circle'
        };
        return icons[type] || 'info-circle';
    }
    
    formatNumber(num) {
        if (num >= 1000000) {
            return (num / 1000000).toFixed(1) + 'M';
        } else if (num >= 1000) {
            return (num / 1000).toFixed(1) + 'K';
        }
        return num.toString();
    }
    
    formatDuration(seconds) {
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        const secs = seconds % 60;
        
        if (hours > 0) {
            return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
        } else {
            return `${minutes}:${secs.toString().padStart(2, '0')}`;
        }
    }
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new YouTubeDownloaderApp();
});
