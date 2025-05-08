import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { authAPI, metadataAPI, userAPI } from '../services/api';

// Create the context
export const MetadataContext = createContext();

/**
 * Provider component for metadata enrichment and authentication state management
 * Handles user authentication, metadata fetching, caching, and accessibility
 */
const MetadataProvider = ({ children }) => {
  // Authentication state
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [userInfo, setUserInfo] = useState(null);
  const [userPermission, setUserPermission] = useState('public'); // default: public
  const [authLoading, setAuthLoading] = useState(true);
  const [authError, setAuthError] = useState(null);
  
  // Metadata state
  const [metadataCache, setMetadataCache] = useState({});
  const [loading, setLoading] = useState({});
  const [error, setError] = useState({});

  // Initialize authentication state from token
  useEffect(() => {
    const initAuth = async () => {
      setAuthLoading(true);
      try {
        const token = localStorage.getItem('auth_token');
        if (!token) {
          setAuthLoading(false);
          return;
        }
        
        // Validate the token
        const response = await authAPI.validateToken();
        if (response.data && response.data.valid) {
          // Get user info
          const userResponse = await authAPI.getUserInfo();
          const userData = userResponse.data;
          
          setIsAuthenticated(true);
          setUserInfo(userData);
          setUserPermission(userData.role || 'user');
          
          // Save user info to localStorage as backup
          localStorage.setItem('user_info', JSON.stringify(userData));
        } else {
          // Token is invalid, clear it
          localStorage.removeItem('auth_token');
          localStorage.removeItem('user_info');
        }
      } catch (err) {
        console.error('Authentication initialization error:', err);
        setAuthError(err.response?.data?.message || err.message);
        
        // Clear auth data if there's an error
        localStorage.removeItem('auth_token');
        localStorage.removeItem('user_info');
      } finally {
        setAuthLoading(false);
      }
    };
    
    initAuth();
  }, []);

  /**
   * Login user with credentials
   * @param {Object} credentials - User credentials (email/username and password)
   */
  const login = async (credentials) => {
    setAuthLoading(true);
    setAuthError(null);
    
    try {
      const response = await authAPI.login(credentials);
      const { token, user } = response.data;
      
      // Save token and user info
      localStorage.setItem('auth_token', token);
      localStorage.setItem('user_info', JSON.stringify(user));
      
      // Update state
      setIsAuthenticated(true);
      setUserInfo(user);
      setUserPermission(user.role || 'user');
      
      return true;
    } catch (err) {
      console.error('Login error:', err);
      setAuthError(err.response?.data?.message || 'Login failed. Please check your credentials.');
      return false;
    } finally {
      setAuthLoading(false);
    }
  };

  /**
   * Register a new user
   * @param {Object} userData - User registration data
   */
  const signUp = async (userData) => {
    setAuthLoading(true);
    setAuthError(null);
    
    try {
      const response = await authAPI.signUp(userData);
      const { token, user } = response.data;
      
      // Save token and user info
      if (token) {
        localStorage.setItem('auth_token', token);
        localStorage.setItem('user_info', JSON.stringify(user));
        
        // Update state
        setIsAuthenticated(true);
        setUserInfo(user);
        setUserPermission(user.role || 'user');
      }
      
      return true;
    } catch (err) {
      console.error('Registration error:', err);
      setAuthError(err.response?.data?.message || 'Registration failed. Please try again.');
      return false;
    } finally {
      setAuthLoading(false);
    }
  };

  /**
   * Logout the current user
   */
  const logout = useCallback(async () => {
    try {
      // Call logout API (best effort)
      try {
        await authAPI.logout();
      } catch (err) {
        console.log('Logout API call failed:', err);
      }
    } finally {
      // Clear local storage and state regardless of API success
      localStorage.removeItem('auth_token');
      localStorage.removeItem('user_info');
      
      setIsAuthenticated(false);
      setUserInfo(null);
      setUserPermission('public');
      setMetadataCache({});
    }
  }, []);

  /**
   * Update user preferences
   * @param {Object} preferences - User preference settings
   */
  const updateUserPreferences = async (preferences) => {
    if (!isAuthenticated) return false;
    
    try {
      await userAPI.updateSettings(preferences);
      
      // Update local user info
      if (userInfo) {
        const updatedUserInfo = {
          ...userInfo,
          preferences: {
            ...userInfo.preferences,
            ...preferences
          }
        };
        
        setUserInfo(updatedUserInfo);
        localStorage.setItem('user_info', JSON.stringify(updatedUserInfo));
      }
      
      return true;
    } catch (err) {
      console.error('Error updating user preferences:', err);
      return false;
    }
  };
  
  /**
   * Fetch enriched metadata for a content item
   * @param {string} contentId - The ID of the content to fetch metadata for
   * @param {Array} sources - Optional array of metadata sources to include
   * @param {boolean} forceRefresh - Whether to bypass cache and force a refresh
   */
  const fetchMetadata = async (contentId, sources = null, forceRefresh = false) => {
    // Return cached data if available and not forcing refresh
    if (!forceRefresh && metadataCache[contentId]) {
      return metadataCache[contentId];
    }
    
    // Set loading state
    setLoading(prev => ({ ...prev, [contentId]: true }));
    setError(prev => ({ ...prev, [contentId]: null }));
    
    try {
      // Make API request using our service
      const response = await metadataAPI.getEnriched(contentId, sources);
      
      // Update cache with new data
      const newData = response.data;
      setMetadataCache(prev => ({
        ...prev,
        [contentId]: newData
      }));
      
      // Clear loading state
      setLoading(prev => ({ ...prev, [contentId]: false }));
      
      return newData;
    } catch (err) {
      console.error(`Error fetching metadata for ${contentId}:`, err);
      
      // Set error state
      setError(prev => ({
        ...prev,
        [contentId]: err.response?.data?.message || err.message
      }));
      
      // Clear loading state
      setLoading(prev => ({ ...prev, [contentId]: false }));
      
      return null;
    }
  };

  /**
   * Clear the metadata cache for a specific content ID or all content
   * @param {string} contentId - Optional ID to clear specific cache entry
   */
  const clearMetadataCache = (contentId) => {
    if (contentId) {
      // Clear specific content ID
      setMetadataCache(prev => {
        const newCache = { ...prev };
        delete newCache[contentId];
        return newCache;
      });
    } else {
      // Clear all cache
      setMetadataCache({});
    }
  };

  // Context value
  const value = {
    // Authentication values
    isAuthenticated,
    userInfo,
    userPermission,
    authLoading,
    authError,
    login,
    signUp,
    logout,
    updateUserPreferences,
    
    // Metadata values
    metadataCache,
    loading,
    error,
    fetchMetadata,
    clearMetadataCache
  };

  return (
    <MetadataContext.Provider value={value}>
      {children}
    </MetadataContext.Provider>
  );
};

// Custom hook for using the metadata context
export const useMetadata = () => {
  const context = useContext(MetadataContext);
  if (!context) {
    throw new Error('useMetadata must be used within a MetadataProvider');
  }
  return context;
};

// Export the provider
export { MetadataProvider };
