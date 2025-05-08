import React, { useState } from 'react';
import './MetadataDisplay.css';

/**
 * Component for displaying enriched video metadata
 * 
 * @param {Object} props Component properties
 * @param {Object} props.metadata The enriched metadata object to display
 * @param {boolean} props.showAllFields Whether to show all fields or just the most important ones
 * @param {function} props.onClose Optional function to call when closing the display
 */
const MetadataDisplay = ({ metadata, showAllFields = false, onClose }) => {
  const [activeTab, setActiveTab] = useState('basic');
  // State for section expansion (used in future implementation)
  const [, setExpandedSections] = useState({});

  // Define the tabs and their content
  const tabs = [
    { id: 'basic', label: 'Basic Info' },
    { id: 'media', label: 'Media Details' },
    { id: 'content', label: 'Content' },
    { id: 'external', label: 'External Links' },
    { id: 'technical', label: 'Technical' },
  ];

  // Group metadata fields by category
  const categorizedMetadata = {
    basic: [
      { key: 'title', label: 'Title' },
      { key: 'release_date', label: 'Release Date' },
      { key: 'genres', label: 'Genres' },
      { key: 'runtime', label: 'Runtime', formatter: formatRuntime },
      { key: 'vote_average', label: 'Rating', formatter: formatRating },
      { key: 'directors', label: 'Directors' },
      { key: 'overview', label: 'Overview' }
    ],
    media: [
      { key: 'poster_url', label: 'Poster', type: 'image' },
      { key: 'backdrop_url', label: 'Backdrop', type: 'image' },
      { key: 'thumbnail_medium_url', label: 'Thumbnail', type: 'image' },
      { key: 'locations_map_url', label: 'Filming Locations', type: 'image' },
      { key: 'filming_locations', label: 'Filming Locations', type: 'locations' },
      { key: 'cast', label: 'Cast', type: 'list' }
    ],
    content: [
      { key: 'themes', label: 'Themes', type: 'tags' },
      { key: 'mood', label: 'Mood' },
      { key: 'time_period', label: 'Time Period' },
      { key: 'keywords', label: 'Keywords', type: 'tags' },
      { key: 'wikipedia_extract', label: 'Description', type: 'longtext' },
      { key: 'soundtrack_name', label: 'Soundtrack' },
      { key: 'soundtrack_url', label: 'Soundtrack Link', type: 'link' },
      { key: 'soundtrack_artists', label: 'Artists', type: 'list' }
    ],
    external: [
      { key: 'video_url', label: 'Video Link', type: 'link' },
      { key: 'wikipedia_url', label: 'Wikipedia', type: 'link' },
      { key: 'availability', label: 'Availability', type: 'availability' },
      { key: 'streaming_services', label: 'Streaming On', type: 'services' },
      { key: 'purchase_options', label: 'Purchase Options', type: 'services' }
    ],
    technical: [
      { key: 'content_id', label: 'Content ID' },
      { key: 'tmdb_id', label: 'TMDB ID' },
      { key: 'youtube_id', label: 'YouTube ID' },
      { key: 'width', label: 'Width' },
      { key: 'height', label: 'Height' },
      { key: 'codec', label: 'Codec' },
      { key: 'duration', label: 'Duration', formatter: formatDuration },
      { key: 'bitrate', label: 'Bitrate', formatter: formatBitrate },
      { key: 'file_size', label: 'File Size', formatter: formatFileSize },
      { key: 'audio_codec', label: 'Audio Codec' },
      { key: 'audio_channels', label: 'Audio Channels' },
      { key: 'timestamp', label: 'Match Timestamp', formatter: formatTimestamp },
      { key: 'formatted_timestamp', label: 'Formatted Timestamp' }
    ]
  };

  // Toggle a section's expanded state - will be used when implementing collapsible sections
  // eslint-disable-next-line no-unused-vars
  const handleSectionToggle = (section) => {
    setExpandedSections(prev => ({
      ...prev,
      [section]: !prev[section]
    }));
  };

  // Formatters for specific data types
  function formatRuntime(minutes) {
    if (!minutes) return 'Unknown';
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    return hours > 0 ? `${hours}h ${mins}m` : `${mins}m`;
  }

  function formatRating(rating) {
    if (!rating) return 'No rating';
    return `${rating}/10`;
  }

  function formatDuration(seconds) {
    if (!seconds) return 'Unknown';
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);
    return hours > 0 
      ? `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}` 
      : `${minutes}:${secs.toString().padStart(2, '0')}`;
  }

  function formatBitrate(bitrate) {
    if (!bitrate) return 'Unknown';
    return `${Math.round(bitrate / 1000)} kbps`;
  }

  function formatFileSize(bytes) {
    if (!bytes) return 'Unknown';
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    if (bytes === 0) return '0 Bytes';
    const i = parseInt(Math.floor(Math.log(bytes) / Math.log(1024)));
    return Math.round(bytes / Math.pow(1024, i), 2) + ' ' + sizes[i];
  }

  function formatTimestamp(seconds) {
    if (!seconds && seconds !== 0) return 'Unknown';
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);
    return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  }

  // Renders different field types appropriately
  const renderField = (field, value) => {
    if (!value && value !== 0) return null;

    switch (field.type) {
      case 'image':
        return (
          <div className="metadata-image-container">
            <img src={value} alt={field.label} className="metadata-image" />
          </div>
        );

      case 'link':
        return (
          <a href={value} target="_blank" rel="noopener noreferrer" className="metadata-link">
            {field.linkText || 'View'}
          </a>
        );

      case 'tags':
        if (Array.isArray(value)) {
          return (
            <div className="metadata-tags">
              {value.map((tag, index) => (
                <span key={index} className="metadata-tag">{tag}</span>
              ))}
            </div>
          );
        }
        return <span>{value}</span>;

      case 'list':
        if (Array.isArray(value)) {
          return (
            <ul className="metadata-list">
              {value.map((item, index) => (
                <li key={index}>
                  {typeof item === 'object' 
                    ? item.name || JSON.stringify(item)
                    : item
                  }
                </li>
              ))}
            </ul>
          );
        }
        return <span>{value}</span>;

      case 'longtext':
        return <div className="metadata-longtext">{value}</div>;

      case 'locations':
        if (Array.isArray(value)) {
          return (
            <ul className="metadata-locations">
              {value.map((loc, index) => (
                <li key={index}>
                  {loc.name || loc.place_name || JSON.stringify(loc)}
                </li>
              ))}
            </ul>
          );
        }
        return <span>{value}</span>;

      case 'availability':
        if (typeof value === 'object' && value !== null) {
          return (
            <div className="metadata-availability">
              {value.services && value.services.length > 0 && (
                <div className="availability-section">
                  <h4>Available on:</h4>
                  <ul>
                    {value.services.map((service, index) => (
                      <li key={index}>
                        {service.url ? (
                          <a href={service.url} target="_blank" rel="noopener noreferrer">
                            {service.name}
                          </a>
                        ) : service.name}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          );
        }
        return null;

      case 'services':
        if (Array.isArray(value)) {
          return (
            <div className="metadata-services">
              {value.map((service, index) => (
                <div key={index} className="service-item">
                  {service.url ? (
                    <a href={service.url} target="_blank" rel="noopener noreferrer">
                      {service.name}
                    </a>
                  ) : service.name}
                  {service.price && <span className="service-price">${service.price}</span>}
                </div>
              ))}
            </div>
          );
        }
        return null;

      default:
        // Apply formatter if provided
        if (field.formatter && typeof field.formatter === 'function') {
          return <span>{field.formatter(value)}</span>;
        }
        
        // Handle arrays and objects
        if (Array.isArray(value)) {
          return <span>{value.join(', ')}</span>;
        } else if (typeof value === 'object' && value !== null) {
          return <span>{JSON.stringify(value)}</span>;
        }
        return <span>{value}</span>;
    }
  };

  // Get the metadata from the enriched_metadata field if it exists
  const enrichedData = metadata?.enriched_metadata || metadata || {};
  
  return (
    <div className="metadata-display">
      <div className="metadata-header">
        <h2>{enrichedData.title || 'Video Metadata'}</h2>
        {onClose && (
          <button onClick={onClose} className="close-button">
            u00d7
          </button>
        )}
      </div>
      
      <div className="metadata-tabs">
        {tabs.map(tab => (
          <button
            key={tab.id}
            className={activeTab === tab.id ? 'active' : ''}
            onClick={() => setActiveTab(tab.id)}
          >
            {tab.label}
          </button>
        ))}
      </div>
      
      <div className="metadata-content">
        {tabs.map(tab => (
          <div 
            key={tab.id} 
            className={`metadata-tab-content ${activeTab === tab.id ? 'active' : ''}`}
          >
            {activeTab === tab.id && (
              <div className="metadata-fields">
                {categorizedMetadata[tab.id]
                  .filter(field => showAllFields || enrichedData[field.key])
                  .map(field => (
                    <div key={field.key} className="metadata-field">
                      <div className="field-label">{field.label}</div>
                      <div className="field-value">
                        {renderField(field, enrichedData[field.key])}
                      </div>
                    </div>
                  ))
                }
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};

export default MetadataDisplay;
