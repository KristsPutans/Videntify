/**
 * API Service
 * Handles all API requests for the VidID mobile app
 */

import axios from 'axios';
import AsyncStorage from '@react-native-async-storage/async-storage';

// Base URL for the API
const API_URL = 'https://api.vidid.com';

// Create axios instance with default config
const apiClient = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
  },
  timeout: 30000, // 30 seconds timeout
});

// Request interceptor to add token to requests
apiClient.interceptors.request.use(
  async (config) => {
    const token = await AsyncStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

/**
 * Identify a video clip
 * @param {string} videoUri - URI to the video file
 * @returns {Promise} - Promise with identification results
 */
export const identifyVideo = async (videoUri) => {
  try {
    // Create form data object for file upload
    const formData = new FormData();
    formData.append('video_file', {
      uri: videoUri,
      type: 'video/mp4',
      name: 'video_clip.mp4',
    });
    
    // For demo purposes, return mock data instead of making an actual API call
    // In a real app, we would use the following code:
    // const response = await apiClient.post('/identify/video', formData, {
    //   headers: {
    //     'Content-Type': 'multipart/form-data',
    //   },
    // });
    // return response.data;
    
    // Simulate API delay
    await new Promise(resolve => setTimeout(resolve, 2000));
    
    // Return mock data
    return {
      query_id: 'q-' + Math.random().toString(36).substring(2, 10),
      processing_time: 1.23,
      matches: [
        {
          content_id: 'vid123',
          title: 'Interstellar',
          confidence: 0.95,
          match_type: 'ensemble',
          timestamp: 1234.5,
          formatted_timestamp: '00:20:34',
          thumbnail: null, // Base64 would be here in a real app
          streaming_services: [
            { name: 'Netflix', url: 'https://netflix.com/watch/12345' },
            { name: 'Amazon Prime', url: 'https://amazon.com/video/watch/67890' },
          ],
        },
        {
          content_id: 'vid456',
          title: 'The Dark Knight',
          confidence: 0.87,
          match_type: 'cnn_features',
          timestamp: 678.9,
          formatted_timestamp: '00:11:18',
          thumbnail: null, // Base64 would be here in a real app
          streaming_services: [
            { name: 'HBO Max', url: 'https://hbomax.com/watch/54321' },
          ],
        },
        {
          content_id: 'vid789',
          title: 'Inception',
          confidence: 0.82,
          match_type: 'perceptual_hash',
          timestamp: 432.1,
          formatted_timestamp: '00:07:12',
          thumbnail: null, // Base64 would be here in a real app
          streaming_services: [
            { name: 'Disney+', url: 'https://disneyplus.com/watch/98765' },
          ],
        },
      ],
    };
  } catch (error) {
    console.error('Error identifying video:', error);
    throw error;
  }
};

/**
 * Get user identification history
 * @returns {Promise} - Promise with user's identification history
 */
export const getIdentificationHistory = async () => {
  try {
    // For demo purposes, return mock data instead of making an actual API call
    // In a real app, we would use the following code:
    // const response = await apiClient.get('/user/history');
    // return response.data;
    
    // Simulate API delay
    await new Promise(resolve => setTimeout(resolve, 500));
    
    // Return mock data
    return {
      history: [
        {
          query_id: 'q-abc123',
          timestamp: '2025-05-07T10:30:15Z',
          matches: [
            {
              content_id: 'vid123',
              title: 'Interstellar',
              confidence: 0.95,
            },
          ],
        },
        {
          query_id: 'q-def456',
          timestamp: '2025-05-06T18:45:22Z',
          matches: [
            {
              content_id: 'vid456',
              title: 'The Dark Knight',
              confidence: 0.87,
            },
          ],
        },
        {
          query_id: 'q-ghi789',
          timestamp: '2025-05-05T14:12:08Z',
          matches: [
            {
              content_id: 'vid789',
              title: 'Inception',
              confidence: 0.82,
            },
          ],
        },
      ],
    };
  } catch (error) {
    console.error('Error getting history:', error);
    throw error;
  }
};

/**
 * Update user profile
 * @param {Object} profileData - Profile data to update
 * @returns {Promise} - Promise with updated profile
 */
export const updateUserProfile = async (profileData) => {
  try {
    const response = await apiClient.put('/user/profile', profileData);
    return response.data;
  } catch (error) {
    console.error('Error updating profile:', error);
    throw error;
  }
};

/**
 * Share identification result
 * @param {string} queryId - ID of the query to share
 * @param {string} platform - Social platform to share on
 * @returns {Promise} - Promise with sharing result
 */
export const shareIdentificationResult = async (queryId, platform) => {
  try {
    const response = await apiClient.post('/share/result', {
      query_id: queryId,
      platform: platform,
    });
    return response.data;
  } catch (error) {
    console.error('Error sharing result:', error);
    throw error;
  }
};
