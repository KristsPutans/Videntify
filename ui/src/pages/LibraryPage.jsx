import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useMetadata } from '../context/MetadataContext';
import './LibraryPage.css';

const LibraryPage = () => {
  const { userPermission } = useMetadata();
  const [queries, setQueries] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeFilter, setActiveFilter] = useState('all');
  const [filterOptions, setFilterOptions] = useState({
    extractors: [],
    contentTypes: [],
    dateRange: 'all'
  });
  
  // Fetch user's queries and identified videos
  useEffect(() => {
    const fetchQueries = async () => {
      try {
        setIsLoading(true);
        setError(null);
        
        // Get auth token
        const token = localStorage.getItem('auth_token');
        
        if (!token) {
          setError('You must be logged in to view your library');
          setIsLoading(false);
          return;
        }
        
        // Fetch queries from API
        const response = await fetch('/api/identify/history', {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });
        
        if (!response.ok) {
          throw new Error('Failed to fetch query history');
        }
        
        const data = await response.json();
        setQueries(data.queries || []);
        
        // Extract filter options from queries
        if (data.queries && data.queries.length > 0) {
          const extractors = new Set();
          const contentTypes = new Set();
          
          data.queries.forEach(query => {
            if (query.extractor_type) extractors.add(query.extractor_type);
            if (query.content_type) contentTypes.add(query.content_type);
          });
          
          setFilterOptions({
            extractors: Array.from(extractors),
            contentTypes: Array.from(contentTypes),
            dateRange: 'all'
          });
        }
        
      } catch (err) {
        setError(err.message);
      } finally {
        setIsLoading(false);
      }
    };
    
    fetchQueries();
  }, []);
  
  // Format timestamp
  const formatDate = (timestamp) => {
    if (!timestamp) return 'Unknown';
    
    const date = new Date(timestamp);
    return date.toLocaleString();
  };
  
  // Filter queries based on selected filter
  const getFilteredQueries = () => {
    if (activeFilter === 'all') return queries;
    
    return queries.filter(query => {
      // Filter by extractor type
      if (filterOptions.extractors.includes(activeFilter)) {
        return query.extractor_type === activeFilter;
      }
      
      // Filter by content type
      if (filterOptions.contentTypes.includes(activeFilter)) {
        return query.content_type === activeFilter;
      }
      
      // Filter by date range
      if (activeFilter === 'today') {
        const today = new Date();
        today.setHours(0, 0, 0, 0);
        return new Date(query.timestamp) >= today;
      }
      
      if (activeFilter === 'week') {
        const weekAgo = new Date();
        weekAgo.setDate(weekAgo.getDate() - 7);
        return new Date(query.timestamp) >= weekAgo;
      }
      
      if (activeFilter === 'month') {
        const monthAgo = new Date();
        monthAgo.setMonth(monthAgo.getMonth() - 1);
        return new Date(query.timestamp) >= monthAgo;
      }
      
      return true;
    });
  };
  
  // Get feature extractor display name
  const getExtractorName = (type) => {
    const extractorNames = {
      'cnn': 'CNN Visual Features',
      'phash': 'Perceptual Hash',
      'motion': 'Motion Features',
      'mfcc': 'MFCC Audio',
      'audio_fingerprint': 'Audio Fingerprint',
      'waveform': 'Waveform Statistics',
      'combined': 'Combined Features'
    };
    
    return extractorNames[type] || type;
  };
  
  // Show loading state
  if (isLoading) {
    return (
      <div className="library-page loading">
        <div className="loading-spinner"></div>
        <p>Loading your identification history...</p>
      </div>
    );
  }
  
  // Show error
  if (error) {
    return (
      <div className="library-page error">
        <div className="error-container">
          <i className="fas fa-exclamation-circle"></i>
          <h2>Error Loading Library</h2>
          <p>{error}</p>
          {error === 'You must be logged in to view your library' && (
            <Link to="/login" className="login-button">Log In</Link>
          )}
        </div>
      </div>
    );
  }
  
  // Show empty state
  if (queries.length === 0) {
    return (
      <div className="library-page empty">
        <div className="empty-library">
          <i className="fas fa-folder-open"></i>
          <h2>Your Library is Empty</h2>
          <p>You haven't identified any videos yet. Start by identifying your first video!</p>
          <Link to="/search" className="identify-button">Identify a Video</Link>
        </div>
      </div>
    );
  }
  
  // Filter buttons
  const filteredQueries = getFilteredQueries();
  
  return (
    <div className="library-page">
      <div className="library-header">
        <h1>Your Identification Library</h1>
        <p>View your past video identifications and results</p>
      </div>
      
      <div className="library-filters">
        <div className="filters-section">
          <h3>Filter By:</h3>
          <div className="filter-buttons">
            <button 
              className={activeFilter === 'all' ? 'active' : ''}
              onClick={() => setActiveFilter('all')}
            >
              All
            </button>
            
            <button 
              className={activeFilter === 'today' ? 'active' : ''}
              onClick={() => setActiveFilter('today')}
            >
              Today
            </button>
            
            <button 
              className={activeFilter === 'week' ? 'active' : ''}
              onClick={() => setActiveFilter('week')}
            >
              This Week
            </button>
            
            <button 
              className={activeFilter === 'month' ? 'active' : ''}
              onClick={() => setActiveFilter('month')}
            >
              This Month
            </button>
            
            {filterOptions.extractors.map(extractor => (
              <button 
                key={`extractor-${extractor}`}
                className={activeFilter === extractor ? 'active' : ''}
                onClick={() => setActiveFilter(extractor)}
              >
                {getExtractorName(extractor)}
              </button>
            ))}
            
            {filterOptions.contentTypes.map(type => (
              <button 
                key={`type-${type}`}
                className={activeFilter === type ? 'active' : ''}
                onClick={() => setActiveFilter(type)}
              >
                {type.charAt(0).toUpperCase() + type.slice(1)}
              </button>
            ))}
          </div>
        </div>
        
        <div className="search-section">
          <input 
            type="text" 
            placeholder="Search by title or ID..."
            className="search-input"
          />
        </div>
      </div>
      
      <div className="library-content">
        <div className="query-count">
          Showing {filteredQueries.length} of {queries.length} identifications
        </div>
        
        <div className="queries-grid">
          {filteredQueries.map(query => (
            <div className="query-card" key={query.query_id}>
              <div className="query-thumbnail">
                {query.thumbnail_url ? (
                  <img src={query.thumbnail_url} alt="Query thumbnail" />
                ) : (
                  <div className="placeholder-thumbnail">
                    <i className="fas fa-film"></i>
                  </div>
                )}
                
                {query.match_count > 0 && (
                  <div className="match-count">
                    <i className="fas fa-check-circle"></i>
                    {query.match_count} {query.match_count === 1 ? 'match' : 'matches'}
                  </div>
                )}
                
                {query.match_count === 0 && (
                  <div className="no-match">
                    <i className="fas fa-times-circle"></i>
                    No matches
                  </div>
                )}
              </div>
              
              <div className="query-details">
                <h3 className="query-title">
                  {query.title || 'Unknown Content'}
                </h3>
                
                <div className="query-info">
                  <div className="info-item">
                    <i className="fas fa-clock"></i>
                    {formatDate(query.timestamp)}
                  </div>
                  
                  {query.extractor_type && (
                    <div className="info-item">
                      <i className="fas fa-fingerprint"></i>
                      {getExtractorName(query.extractor_type)}
                    </div>
                  )}
                  
                  {query.duration && (
                    <div className="info-item">
                      <i className="fas fa-hourglass-half"></i>
                      {Math.floor(query.duration / 60)}:{(query.duration % 60).toString().padStart(2, '0')}
                    </div>
                  )}
                </div>
                
                <Link to={`/results/${query.query_id}`} className="view-results-button">
                  View Results
                </Link>
              </div>
            </div>
          ))}
        </div>
      </div>
      
      {userPermission === 'admin' && (
        <div className="admin-actions">
          <button className="export-button">
            <i className="fas fa-file-export"></i>
            Export History
          </button>
          
          <button className="clear-button">
            <i className="fas fa-trash-alt"></i>
            Clear History
          </button>
        </div>
      )}
    </div>
  );
};

export default LibraryPage;
