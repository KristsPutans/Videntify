import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useMetadata } from '../context/MetadataContext';
import './ProfilePage.css';

const ProfilePage = () => {
  const { userInfo, userPermission } = useMetadata();
  const navigate = useNavigate();
  
  // Stats state
  const [stats, setStats] = useState({
    totalIdentifications: 0,
    successfulMatches: 0,
    lastActive: null,
    accountCreated: null,
    favoriteExtractors: [],
  });
  
  // Activity state
  const [recentActivity, setRecentActivity] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  
  // Fetch user profile data
  useEffect(() => {
    if (!userInfo) {
      navigate('/login');
      return;
    }
    
    const fetchProfileData = async () => {
      try {
        setIsLoading(true);
        setError(null);
        
        // Get auth token
        const token = localStorage.getItem('auth_token');
        
        if (!token) {
          setError('You must be logged in to view your profile');
          setIsLoading(false);
          return;
        }
        
        // In a real app, you would fetch this data from your API
        // For demo purposes, we'll simulate with dummy data
        
        // Simulate API call delay
        await new Promise(resolve => setTimeout(resolve, 800));
        
        // Set dummy stats
        setStats({
          totalIdentifications: 47,
          successfulMatches: 38,
          lastActive: new Date().toISOString(),
          accountCreated: '2024-01-15T08:30:00.000Z',
          favoriteExtractors: ['cnn', 'phash', 'mfcc']
        });
        
        // Set dummy recent activity
        setRecentActivity([
          {
            id: 'act-1',
            type: 'identification',
            content: 'Identified "Mountain Landscape" video',
            timestamp: new Date(Date.now() - 2 * 3600 * 1000).toISOString(),
            queryId: 'q-123456'
          },
          {
            id: 'act-2',
            type: 'login',
            content: 'Logged in from New York, USA',
            timestamp: new Date(Date.now() - 8 * 3600 * 1000).toISOString()
          },
          {
            id: 'act-3',
            type: 'identification',
            content: 'Identified "Ocean Waves" video',
            timestamp: new Date(Date.now() - 24 * 3600 * 1000).toISOString(),
            queryId: 'q-123457'
          },
          {
            id: 'act-4',
            type: 'settings',
            content: 'Updated notification preferences',
            timestamp: new Date(Date.now() - 3 * 24 * 3600 * 1000).toISOString()
          },
          {
            id: 'act-5',
            type: 'identification',
            content: 'Identified "City Timelapse" video',
            timestamp: new Date(Date.now() - 5 * 24 * 3600 * 1000).toISOString(),
            queryId: 'q-123458'
          }
        ]);
        
      } catch (err) {
        setError(err.message);
      } finally {
        setIsLoading(false);
      }
    };
    
    fetchProfileData();
  }, [userInfo, navigate]);
  
  // Format date
  const formatDate = (dateString) => {
    if (!dateString) return 'Unknown';
    
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  };
  
  // Format time ago
  const formatTimeAgo = (dateString) => {
    if (!dateString) return 'Unknown';
    
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now - date;
    const diffSecs = Math.floor(diffMs / 1000);
    const diffMins = Math.floor(diffSecs / 60);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);
    
    if (diffSecs < 60) {
      return 'Just now';
    } else if (diffMins < 60) {
      return `${diffMins} ${diffMins === 1 ? 'minute' : 'minutes'} ago`;
    } else if (diffHours < 24) {
      return `${diffHours} ${diffHours === 1 ? 'hour' : 'hours'} ago`;
    } else if (diffDays < 7) {
      return `${diffDays} ${diffDays === 1 ? 'day' : 'days'} ago`;
    } else {
      return formatDate(dateString);
    }
  };
  
  // Get extractor display name
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
  
  // Get activity icon
  const getActivityIcon = (type) => {
    const icons = {
      'identification': 'fa-fingerprint',
      'login': 'fa-sign-in-alt',
      'logout': 'fa-sign-out-alt',
      'settings': 'fa-cog',
      'account': 'fa-user-edit'
    };
    
    return icons[type] || 'fa-circle';
  };
  
  // Show loading state
  if (isLoading) {
    return (
      <div className="profile-page loading">
        <div className="loading-spinner"></div>
        <p>Loading your profile...</p>
      </div>
    );
  }
  
  // Show error
  if (error) {
    return (
      <div className="profile-page error">
        <div className="error-container">
          <i className="fas fa-exclamation-circle"></i>
          <h2>Error Loading Profile</h2>
          <p>{error}</p>
          {error === 'You must be logged in to view your profile' && (
            <Link to="/login" className="login-button">Log In</Link>
          )}
        </div>
      </div>
    );
  }
  
  return (
    <div className="profile-page">
      <div className="profile-header">
        <div className="user-info-card">
          <div className="user-avatar-container">
            {userInfo && userInfo.avatarUrl ? (
              <img 
                src={userInfo.avatarUrl} 
                alt={userInfo.name || 'User'} 
                className="user-avatar"
              />
            ) : (
              <div className="user-initials">
                {userInfo && userInfo.name ? userInfo.name.charAt(0).toUpperCase() : 'U'}
              </div>
            )}
          </div>
          
          <div className="user-details">
            <h1 className="user-name">{userInfo?.name || 'User'}</h1>
            <p className="user-email">{userInfo?.email || ''}</p>
            
            {userInfo?.role && (
              <span className="user-role">{userInfo.role.charAt(0).toUpperCase() + userInfo.role.slice(1)} User</span>
            )}
            
            <div className="user-actions">
              <Link to="/settings" className="edit-profile-button">
                <i className="fas fa-user-edit"></i> Edit Profile
              </Link>
              
              {(userPermission === 'pro' || userPermission === 'admin') && (
                <Link to="/settings?tab=api" className="api-access-button">
                  <i className="fas fa-key"></i> API Access
                </Link>
              )}
            </div>
          </div>
        </div>
      </div>
      
      <div className="profile-content">
        <div className="profile-stats">
          <div className="stats-card">
            <div className="stat">
              <div className="stat-value">{stats.totalIdentifications}</div>
              <div className="stat-label">Total Identifications</div>
            </div>
            
            <div className="stat">
              <div className="stat-value">{stats.successfulMatches}</div>
              <div className="stat-label">Successful Matches</div>
            </div>
            
            <div className="stat">
              <div className="stat-value">
                {stats.successfulMatches > 0 && stats.totalIdentifications > 0 ? 
                  `${Math.round((stats.successfulMatches / stats.totalIdentifications) * 100)}%` : 
                  '0%'}
              </div>
              <div className="stat-label">Success Rate</div>
            </div>
          </div>
          
          <div className="account-info-card">
            <h2>Account Information</h2>
            
            <div className="info-row">
              <div className="info-label">Member Since</div>
              <div className="info-value">{formatDate(stats.accountCreated)}</div>
            </div>
            
            <div className="info-row">
              <div className="info-label">Last Active</div>
              <div className="info-value">{formatTimeAgo(stats.lastActive)}</div>
            </div>
            
            <div className="info-row">
              <div className="info-label">Account Type</div>
              <div className="info-value">
                {userInfo?.role ? userInfo.role.charAt(0).toUpperCase() + userInfo.role.slice(1) : 'Standard'}
              </div>
            </div>
            
            {stats.favoriteExtractors && stats.favoriteExtractors.length > 0 && (
              <div className="info-row">
                <div className="info-label">Favorite Extractors</div>
                <div className="info-value">
                  <div className="extractor-tags">
                    {stats.favoriteExtractors.map(extractor => (
                      <span key={extractor} className="extractor-tag">
                        {getExtractorName(extractor)}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
        
        <div className="recent-activity">
          <h2>Recent Activity</h2>
          
          {recentActivity.length === 0 ? (
            <div className="no-activity">
              <i className="fas fa-history"></i>
              <p>No recent activity to display.</p>
            </div>
          ) : (
            <div className="activity-timeline">
              {recentActivity.map(activity => (
                <div className="activity-item" key={activity.id}>
                  <div className="activity-icon">
                    <i className={`fas ${getActivityIcon(activity.type)}`}></i>
                  </div>
                  
                  <div className="activity-content">
                    <div className="activity-time">{formatTimeAgo(activity.timestamp)}</div>
                    <div className="activity-text">{activity.content}</div>
                    
                    {activity.queryId && (
                      <Link to={`/results/${activity.queryId}`} className="activity-link">
                        View Results <i className="fas fa-arrow-right"></i>
                      </Link>
                    )}
                  </div>
                </div>
              ))}
              
              <div className="view-more">
                <Link to="/library" className="view-more-link">
                  View Full Activity History
                </Link>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ProfilePage;
