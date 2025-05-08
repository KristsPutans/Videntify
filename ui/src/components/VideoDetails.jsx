import React, { useEffect, useState } from 'react';
import { useMetadata } from '../context/MetadataContext';
import MetadataDisplay from './MetadataDisplay';

/**
 * Video Details component that uses the metadata context to fetch and display enriched metadata
 * @param {Object} props Component properties
 * @param {string} props.contentId ID of the content to display
 */
const VideoDetails = ({ contentId }) => {
  const { fetchMetadata, loading, error, userPermission } = useMetadata();
  const [metadata, setMetadata] = useState(null);
  const [showMetadata, setShowMetadata] = useState(false);

  useEffect(() => {
    if (contentId) {
      // Load metadata when component mounts or contentId changes
      const loadMetadata = async () => {
        const data = await fetchMetadata(contentId);
        if (data) {
          setMetadata(data);
        }
      };
      
      loadMetadata();
    }
  }, [contentId, fetchMetadata]);

  const handleRefresh = async () => {
    const data = await fetchMetadata(contentId, true); // force refresh
    if (data) {
      setMetadata(data);
    }
  };

  // Handle loading state
  if (loading[contentId]) {
    return <div className="loading-spinner">Loading metadata...</div>;
  }

  // Handle error state
  if (error[contentId]) {
    return (
      <div className="error-message">
        <p>Error loading metadata: {error[contentId]}</p>
        <button onClick={handleRefresh}>Try Again</button>
      </div>
    );
  }

  // Handle no metadata case
  if (!metadata) {
    return (
      <div className="no-metadata">
        <p>No metadata available for this content.</p>
        <button onClick={handleRefresh}>Try Loading Metadata</button>
      </div>
    );
  }

  return (
    <div className="video-details">
      <div className="video-header">
        <h1>{metadata.title || 'Unknown Title'}</h1>
        {metadata.release_date && (
          <div className="release-year">{new Date(metadata.release_date).getFullYear()}</div>
        )}
      </div>

      {/* Basic information preview */}
      <div className="video-preview">
        {metadata.poster_url && (
          <div className="poster">
            <img src={metadata.poster_url} alt={metadata.title} />
          </div>
        )}
        
        <div className="video-info">
          {metadata.genres && (
            <div className="genres">
              {metadata.genres.join(', ')}
            </div>
          )}
          
          {metadata.runtime && (
            <div className="runtime">
              {Math.floor(metadata.runtime / 60)}h {metadata.runtime % 60}m
            </div>
          )}
          
          {metadata.overview && (
            <div className="overview">{metadata.overview}</div>
          )}
          
          <button 
            className="view-metadata-btn"
            onClick={() => setShowMetadata(!showMetadata)}
          >
            {showMetadata ? 'Hide Details' : 'View All Metadata'}
          </button>
          
          <button 
            className="refresh-btn"
            onClick={handleRefresh}
          >
            Refresh Metadata
          </button>
        </div>
      </div>

      {/* Show full metadata display when requested */}
      {showMetadata && (
        <MetadataDisplay 
          metadata={metadata} 
          showAllFields={userPermission === 'admin'}
          onClose={() => setShowMetadata(false)}
        />
      )}
    </div>
  );
};

export default VideoDetails;
