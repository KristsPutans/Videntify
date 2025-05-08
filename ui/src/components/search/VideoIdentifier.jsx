import React, { useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import './VideoIdentifier.css';

const VideoIdentifier = () => {
  const [file, setFile] = useState(null);
  const [videoUrl, setVideoUrl] = useState('');
  const [inputMethod, setInputMethod] = useState('file'); // 'file' or 'url'
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [error, setError] = useState(null);
  
  const fileInputRef = useRef(null);
  const navigate = useNavigate();
  
  // For drag and drop functionality
  const [isDragging, setIsDragging] = useState(false);
  
  const handleDragEnter = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  };
  
  const handleDragLeave = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  };
  
  const handleDragOver = (e) => {
    e.preventDefault();
    e.stopPropagation();
  };
  
  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const droppedFile = e.dataTransfer.files[0];
      handleFileSelection(droppedFile);
    }
  };
  
  // Handle file selection from input
  const handleFileChange = (e) => {
    if (e.target.files && e.target.files.length > 0) {
      const selectedFile = e.target.files[0];
      handleFileSelection(selectedFile);
    }
  };
  
  // Process selected file
  const handleFileSelection = (selectedFile) => {
    // Check file size (limit to 100MB)
    if (selectedFile.size > 100 * 1024 * 1024) {
      setError('File size exceeds 100MB limit. Please select a smaller file.');
      setFile(null);
      return;
    }
    
    // Check file type
    const fileType = selectedFile.type;
    if (!fileType.startsWith('video/')) {
      setError('Please select a valid video file.');
      setFile(null);
      return;
    }
    
    // Clear any previous errors
    setError(null);
    setFile(selectedFile);
  };
  
  // Handle method change between file upload and URL
  const handleMethodChange = (method) => {
    setInputMethod(method);
    setError(null);
    setFile(null);
    setVideoUrl('');
  };
  
  // Handle URL input change
  const handleUrlChange = (e) => {
    setVideoUrl(e.target.value);
    setError(null);
  };
  
  // Validate URL
  const isValidUrl = (url) => {
    try {
      new URL(url);
      // Basic check for video hosting services
      return url.includes('youtube.com') || 
             url.includes('youtu.be') || 
             url.includes('vimeo.com') || 
             url.includes('dailymotion.com') || 
             url.includes('twitch.tv') ||
             url.endsWith('.mp4') ||
             url.endsWith('.mov') ||
             url.endsWith('.avi');
    } catch (e) {
      return false;
    }
  };
  
  // Handle form submission
  const handleSubmit = async (e) => {
    e.preventDefault();
    
    // Validate input
    if (inputMethod === 'file' && !file) {
      setError('Please select a video file.');
      return;
    } else if (inputMethod === 'url' && !videoUrl) {
      setError('Please enter a video URL.');
      return;
    } else if (inputMethod === 'url' && !isValidUrl(videoUrl)) {
      setError('Please enter a valid video URL from a supported platform.');
      return;
    }
    
    // Start upload/identification process
    setIsUploading(true);
    setUploadProgress(0);
    
    try {
      let queryId;
      
      if (inputMethod === 'file') {
        // Upload the file
        const formData = new FormData();
        formData.append('video', file);
        
        // Simulated progress updates
        const progressInterval = setInterval(() => {
          setUploadProgress(prev => {
            if (prev >= 90) {
              clearInterval(progressInterval);
              return 90;
            }
            return prev + 10;
          });
        }, 500);
        
        // Make API request
        const response = await fetch('/api/identify/upload', {
          method: 'POST',
          body: formData,
          headers: {
            // No Content-Type header as it's set automatically for FormData
            'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
          }
        });
        
        clearInterval(progressInterval);
        
        if (!response.ok) {
          throw new Error(`Upload failed: ${response.statusText}`);
        }
        
        const data = await response.json();
        queryId = data.query_id;
        
      } else {
        // Send the URL
        const response = await fetch('/api/identify/url', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
          },
          body: JSON.stringify({ url: videoUrl })
        });
        
        if (!response.ok) {
          throw new Error(`URL processing failed: ${response.statusText}`);
        }
        
        const data = await response.json();
        queryId = data.query_id;
      }
      
      // Identification complete
      setUploadProgress(100);
      
      // Navigate to results page
      setTimeout(() => {
        navigate(`/results/${queryId}`);
      }, 1000);
      
    } catch (err) {
      setError(`Error: ${err.message}`);
      setIsUploading(false);
    }
  };
  
  return (
    <div className="video-identifier">
      <div className="identifier-container">
        <h2>Identify Your Video</h2>
        <p className="identifier-description">
          Upload a video clip or provide a URL to identify content and retrieve enriched metadata
        </p>
        
        <div className="input-method-tabs">
          <button 
            className={`method-tab ${inputMethod === 'file' ? 'active' : ''}`}
            onClick={() => handleMethodChange('file')}
          >
            Upload File
          </button>
          <button 
            className={`method-tab ${inputMethod === 'url' ? 'active' : ''}`}
            onClick={() => handleMethodChange('url')}
          >
            Video URL
          </button>
        </div>
        
        <form onSubmit={handleSubmit}>
          {inputMethod === 'file' ? (
            <div 
              className={`file-upload-area ${isDragging ? 'dragging' : ''}`}
              onDragEnter={handleDragEnter}
              onDragLeave={handleDragLeave}
              onDragOver={handleDragOver}
              onDrop={handleDrop}
            >
              {!file ? (
                <>
                  <div className="upload-icon">
                    <i className="fas fa-cloud-upload-alt"></i>
                  </div>
                  <p>Drag and drop your video file here</p>
                  <p>or</p>
                  <button 
                    type="button" 
                    className="browse-button"
                    onClick={() => fileInputRef.current.click()}
                  >
                    Browse Files
                  </button>
                  <input 
                    type="file" 
                    ref={fileInputRef}
                    onChange={handleFileChange}
                    accept="video/*"
                    style={{ display: 'none' }}
                    data-testid="file-input"
                  />
                  <p className="file-limits">Max file size: 100MB</p>
                </>
              ) : (
                <div className="selected-file">
                  <div className="file-info">
                    <i className="fas fa-file-video"></i>
                    <div className="file-details">
                      <p className="file-name">{file.name}</p>
                      <p className="file-size">{(file.size / (1024 * 1024)).toFixed(2)} MB</p>
                    </div>
                  </div>
                  <button 
                    type="button" 
                    className="remove-file-button"
                    onClick={() => setFile(null)}
                  >
                    <i className="fas fa-times"></i>
                  </button>
                </div>
              )}
            </div>
          ) : (
            <div className="url-input-area">
              <label htmlFor="videoUrl">Video URL</label>
              <input
                type="url"
                id="videoUrl"
                value={videoUrl}
                onChange={handleUrlChange}
                placeholder="https://www.youtube.com/watch?v=..."
                className="url-input"
              />
              <p className="url-hint">
                Supported platforms: YouTube, Vimeo, Dailymotion, Twitch, or direct video links
              </p>
            </div>
          )}
          
          {error && (
            <div className="error-message">
              <i className="fas fa-exclamation-circle"></i>
              {error}
            </div>
          )}
          
          {isUploading ? (
            <div className="upload-progress">
              <div className="progress-bar">
                <div 
                  className="progress-fill" 
                  style={{ width: `${uploadProgress}%` }}
                ></div>
              </div>
              <p className="progress-status">
                {uploadProgress < 100 
                  ? `Processing: ${uploadProgress}%` 
                  : 'Complete! Redirecting to results...'}
              </p>
            </div>
          ) : (
            <button 
              type="submit" 
              className="identify-button"
              disabled={isUploading}
            >
              Identify Video
            </button>
          )}
        </form>
      </div>
    </div>
  );
};

export default VideoIdentifier;
