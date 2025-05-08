import axios from 'axios';

// Create axios instance with base configuration
const apiClient = axios.create({
  baseURL: process.env.REACT_APP_API_URL || '/api',
  headers: {
    'Content-Type': 'application/json'
  },
  timeout: 30000 // 30 seconds
});

// Setup interceptors function for easier testing and configuration
export const setupInterceptors = (axiosInstance) => {
  // Request interceptor for adding auth token
  axiosInstance.interceptors.request.use(
    config => {
      const token = localStorage.getItem('auth_token');
      if (token) {
        config.headers['Authorization'] = `Bearer ${token}`;
      }
      return config;
    },
    error => Promise.reject(error)
  );

  // Response interceptor for handling errors
  axiosInstance.interceptors.response.use(
    response => response,
    error => {
      const { response } = error;
      
      // Handle authentication errors
      if (response && response.status === 401) {
        localStorage.removeItem('auth_token');
        localStorage.removeItem('user_info');
        
        // Redirect to login if not already there
        if (window.location.pathname !== '/login') {
          window.location.href = '/login';
        }
      }
      
      return Promise.reject(error);
    }
  );
};

// Set up interceptors for our API client
setupInterceptors(apiClient);

// Authentication API calls
export const authAPI = {
  login: (credentials) => apiClient.post('/auth/login', credentials),
  signUp: (userData) => apiClient.post('/auth/register', userData),
  logout: () => apiClient.post('/auth/logout'),
  validateToken: () => apiClient.get('/auth/validate'),
  refreshToken: () => apiClient.post('/auth/refresh'),
  getUserInfo: () => apiClient.get('/auth/user'),
  updateUserInfo: (userData) => apiClient.put('/auth/user', userData),
  changePassword: (passwordData) => apiClient.post('/auth/change-password', passwordData)
};

// Identification API calls
export const identifyAPI = {
  identifyFile: (formData, onUploadProgress) => apiClient.post('/identify/file', formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    },
    onUploadProgress
  }),
  identifyUrl: (urlData) => apiClient.post('/identify/url', urlData),
  getResults: (queryId) => apiClient.get(`/identify/results/${queryId}`),
  getHistory: (params) => apiClient.get('/identify/history', { params }),
  getStats: () => apiClient.get('/identify/stats')
};

// Metadata API calls
export const metadataAPI = {
  getEnriched: (contentId, sources) => apiClient.get(`/metadata/${contentId}`, {
    params: { sources: sources ? sources.join(',') : undefined }
  }),
  getFields: () => apiClient.get('/metadata/fields'),
  getSources: () => apiClient.get('/metadata/sources'),
  refreshMetadata: (contentId) => apiClient.post(`/metadata/${contentId}/refresh`),
  getPermissions: () => apiClient.get('/metadata/permissions')
};

// Library API calls
export const libraryAPI = {
  getVideos: (params) => apiClient.get('/library/videos', { params }),
  saveVideo: (videoData) => apiClient.post('/library/videos', videoData),
  deleteVideo: (videoId) => apiClient.delete(`/library/videos/${videoId}`),
  getVideoDetails: (videoId) => apiClient.get(`/library/videos/${videoId}`)
};

// User API calls
export const userAPI = {
  getProfile: () => apiClient.get('/users/profile'),
  updateProfile: (profileData) => apiClient.put('/users/profile', profileData),
  getSettings: () => apiClient.get('/users/settings'),
  updateSettings: (settingsData) => apiClient.put('/users/settings', settingsData),
  deleteAccount: () => apiClient.delete('/users/account')
};

// Admin API calls (these will only work for admin users)
export const adminAPI = {
  getUsers: (params) => apiClient.get('/admin/users', { params }),
  getUserDetails: (userId) => apiClient.get(`/admin/users/${userId}`),
  updateUser: (userId, userData) => apiClient.put(`/admin/users/${userId}`, userData),
  deleteUser: (userId) => apiClient.delete(`/admin/users/${userId}`),
  getSystemStats: () => apiClient.get('/admin/stats'),
  getSystemLogs: (params) => apiClient.get('/admin/logs', { params }),
  updateSystemSettings: (settings) => apiClient.put('/admin/settings', settings)
};

export default {
  authAPI,
  identifyAPI,
  metadataAPI,
  libraryAPI,
  userAPI,
  adminAPI
};
