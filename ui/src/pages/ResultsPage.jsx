import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useMetadata } from '../context/MetadataContext';
import MetadataDisplay from '../components/MetadataDisplay';
import './ResultsPage.css';

const ResultsPage = () => {
  const { queryId } = useParams();
  const { fetchMetadata, userPermission } = useMetadata();
  
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [results, setResults] = useState(null);
  const [matchIndex, setMatchIndex] = useState(0); // Currently selected match
  const [showMetadata, setShowMetadata] = useState(false);
  
  // Fetch query results when page loads
  useEffect(() => {
    const fetchResults = async () => {
      try {
        setLoading(true);
        const response = await fetch(`/api/identify/results/${queryId}`, {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
          }
        });
        
        if (!response.ok) {
          throw new Error(`Error fetching results: ${response.statusText}`);
        }
        
        const data = await response.json();
        setResults(data);
        
        // If there are matches, fetch metadata for the first match
        if (data.matches && data.matches.length > 0) {
          const firstMatch = data.matches[0];
          await fetchMetadata(firstMatch.content_id);
        }
        
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };
    
    fetchResults();
  }, [queryId, fetchMetadata]);
  
  // Handle selecting a different match
  const handleMatchSelect = async (index) => {
    if (results && results.matches && results.matches[index]) {
      setMatchIndex(index);
      
      // Fetch metadata for this match if not already cached
      const match = results.matches[index];
      await fetchMetadata(match.content_id);
    }
  };
  
  // Format timestamp
  const formatTimestamp = (seconds) => {
    if (typeof seconds !== 'number') return '--:--';
    
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);
    
    if (hours > 0) {
      return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    } else {
      return `${minutes}:${secs.toString().padStart(2, '0')}`;
    }
  };
  
  // Format confidence score as percentage
  const formatConfidence = (score) => {
    if (typeof score !== 'number') return '--';
    return `${Math.round(score * 100)}%`;
  };
  
  // If loading
  if (loading) {
    return (
      <div className="results-page loading">
        <div className="results-container">
          <div className="loading-animation">
            <div className="spinner"></div>
            <p>Loading identification results...</p>
          </div>
        </div>
      </div>
    );
  }
  
  // If error
  if (error) {
    return (
      <div className="results-page error">
        <div className="results-container">
          <div className="error-message">
            <i className="fas fa-exclamation-circle"></i>
            <h2>Error Loading Results</h2>
            <p>{error}</p>
            <Link to="/search" className="try-again-button">Try Again</Link>
          </div>
        </div>
      </div>
    );
  }
  
  // If no results or no matches
  if (!results || !results.matches || results.matches.length === 0) {
    return (
      <div className="results-page no-match">
        <div className="results-container">
          <div className="no-match-message">
            <i className="fas fa-search"></i>
            <h2>No Matches Found</h2>
            <p>We couldn't find any matches for your video. Try with a different clip or source.</p>
            <Link to="/search" className="try-again-button">Try Again</Link>
          </div>
          
          {results && results.query_details && (
            <div className="query-details">
              <h3>Query Details</h3>
              <div className="detail-item">
                <span className="detail-label">Query ID:</span>
                <span className="detail-value">{results.query_id}</span>
              </div>
              {results.query_details.duration && (
                <div className="detail-item">
                  <span className="detail-label">Duration:</span>
                  <span className="detail-value">{formatTimestamp(results.query_details.duration)}</span>
                </div>
              )}
              {results.query_details.timestamp && (
                <div className="detail-item">
                  <span className="detail-label">Processed:</span>
                  <span className="detail-value">{new Date(results.query_details.timestamp).toLocaleString()}</span>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    );
  }
  
  // Successfully found matches
  const currentMatch = results.matches[matchIndex];
  
  return (
    <div className="results-page">
      <div className="results-container">
        <div className="results-header">
          <h1>Identification Results</h1>
          <p className="query-info">
            Query ID: <span>{queryId}</span>
            {results.query_details && results.query_details.timestamp && (
              <> • Processed: <span>{new Date(results.query_details.timestamp).toLocaleString()}</span></>
            )}
          </p>
        </div>
        
        <div className="results-content">
          <div className="matches-section">
            <h2>Matches Found ({results.matches.length})</h2>
            
            <div className="match-list">
              {results.matches.map((match, index) => (
                <div 
                  key={match.content_id} 
                  className={`match-item ${index === matchIndex ? 'active' : ''}`}
                  onClick={() => handleMatchSelect(index)}
                >
                  <div className="match-thumbnail">
                    {match.thumbnail_url ? (
                      <img src={match.thumbnail_url} alt={match.title} />
                    ) : (
                      <div className="placeholder-thumbnail">
                        <i className="fas fa-film"></i>
                      </div>
                    )}
                    <div className="match-confidence">
                      {formatConfidence(match.confidence)}
                    </div>
                  </div>
                  <div className="match-info">
                    <h3 className="match-title">{match.title}</h3>
                    {match.timestamp !== undefined && (
                      <div className="match-time">
                        <i className="fas fa-clock"></i>
                        {formatTimestamp(match.timestamp)}
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
          
          <div className="match-details-section">
            <div className="match-header">
              <h2>{currentMatch.title}</h2>
              <div className="match-statistics">
                <div className="stat-item">
                  <span className="stat-label">Confidence:</span>
                  <span className="stat-value">{formatConfidence(currentMatch.confidence)}</span>
                </div>
                {currentMatch.timestamp !== undefined && (
                  <div className="stat-item">
                    <span className="stat-label">Matched at:</span>
                    <span className="stat-value">{formatTimestamp(currentMatch.timestamp)}</span>
                  </div>
                )}
                {currentMatch.duration && (
                  <div className="stat-item">
                    <span className="stat-label">Duration:</span>
                    <span className="stat-value">{formatTimestamp(currentMatch.duration)}</span>
                  </div>
                )}
              </div>
            </div>
            
            <div className="match-preview">
              {currentMatch.thumbnail_url ? (
                <img 
                  src={currentMatch.thumbnail_url} 
                  alt={currentMatch.title} 
                  className="match-thumbnail-large"
                />
              ) : (
                <div className="placeholder-thumbnail-large">
                  <i className="fas fa-film"></i>
                </div>
              )}
              
              <div className="match-actions">
                <button 
                  className="show-metadata-button"
                  onClick={() => setShowMetadata(!showMetadata)}
                >
                  {showMetadata ? 'Hide Metadata' : 'Show Metadata'}
                </button>
                
                {currentMatch.content_url && (
                  <a 
                    href={currentMatch.content_url} 
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="view-content-button"
                  >
                    View Content
                  </a>
                )}
              </div>
            </div>
            
            {currentMatch.overview && (
              <div className="match-overview">
                <h3>Overview</h3>
                <p>{currentMatch.overview}</p>
              </div>
            )}
            
            {/* Show quick metadata */}
            <div className="quick-metadata">
              {currentMatch.genres && currentMatch.genres.length > 0 && (
                <div className="metadata-item">
                  <span className="metadata-label">Genres:</span>
                  <span className="metadata-value">{currentMatch.genres.join(', ')}</span>
                </div>
              )}
              
              {currentMatch.release_date && (
                <div className="metadata-item">
                  <span className="metadata-label">Released:</span>
                  <span className="metadata-value">{new Date(currentMatch.release_date).getFullYear()}</span>
                </div>
              )}
              
              {currentMatch.vote_average !== undefined && (
                <div className="metadata-item">
                  <span className="metadata-label">Rating:</span>
                  <span className="metadata-value">{currentMatch.vote_average}/10</span>
                </div>
              )}
              
              {currentMatch.directors && currentMatch.directors.length > 0 && (
                <div className="metadata-item">
                  <span className="metadata-label">Director:</span>
                  <span className="metadata-value">
                    {Array.isArray(currentMatch.directors) 
                      ? currentMatch.directors.join(', ')
                      : currentMatch.directors}
                  </span>
                </div>
              )}
            </div>
          </div>
        </div>
        
        {/* Full metadata display */}
        {showMetadata && (
          <div className="full-metadata-section">
            <MetadataDisplay 
              metadata={currentMatch} 
              showAllFields={userPermission === 'admin'}
              onClose={() => setShowMetadata(false)}
            />
          </div>
        )}
        
        <div className="results-footer">
          <Link to="/search" className="new-search-button">
            <i className="fas fa-search"></i> New Search
          </Link>
        </div>
      </div>
    </div>
  );
};

export default ResultsPage;
