import React from 'react';
import VideoIdentifier from '../components/search/VideoIdentifier';
import './SearchPage.css';

const SearchPage = () => {
  return (
    <div className="search-page">
      <div className="search-page-header">
        <h1>Identify Your Video</h1>
        <p>Upload a video file or provide a URL to identify the content</p>
      </div>
      
      <VideoIdentifier />
      
      <div className="search-features">
        <div className="feature">
          <div className="feature-icon">
            <i className="fas fa-tachometer-alt"></i>
          </div>
          <h3>Fast Identification</h3>
          <p>Our advanced algorithms can identify videos in seconds</p>
        </div>
        
        <div className="feature">
          <div className="feature-icon">
            <i className="fas fa-bullseye"></i>
          </div>
          <h3>Frame-Accurate</h3>
          <p>Identify the exact frame and timestamp in the original content</p>
        </div>
        
        <div className="feature">
          <div className="feature-icon">
            <i className="fas fa-fingerprint"></i>
          </div>
          <h3>Multiple Techniques</h3>
          <p>Using visual, audio, and motion features for highest accuracy</p>
        </div>
        
        <div className="feature">
          <div className="feature-icon">
            <i className="fas fa-database"></i>
          </div>
          <h3>Rich Metadata</h3>
          <p>Get comprehensive information about matched content</p>
        </div>
      </div>
    </div>
  );
};

export default SearchPage;
