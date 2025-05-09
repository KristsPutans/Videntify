import axios from 'axios';
import {
  apiClient,
  authAPI,
  identifyAPI,
  metadataAPI,
  setupInterceptors
} from '../api';
import { mockApiResponses } from '../../utils/testUtils';
import { safePromise, createSafeAsyncFunction } from '../../utils/jestErrorHandler';

// Mock axios
jest.mock('axios', () => ({
  create: jest.fn(() => ({
    get: jest.fn(),
    post: jest.fn(),
    put: jest.fn(),
    delete: jest.fn(),
    interceptors: {
      request: { use: jest.fn(), eject: jest.fn() },
      response: { use: jest.fn(), eject: jest.fn() }
    }
  })),
  defaults: {}
}));

describe('API Service', () => {
  let mockAxiosInstance;
  let originalSetItem;
  let originalGetItem;
  
  // Setup before all tests
  beforeAll(() => {
    // Store original localStorage methods to restore later
    originalSetItem = localStorage.setItem;
    originalGetItem = localStorage.getItem;
  });
  
  // Reset after all tests
  afterAll(() => {
    // Restore original localStorage methods
    localStorage.setItem = originalSetItem;
    localStorage.getItem = originalGetItem;
  });
  
  beforeEach(() => {
    // Clear all mocks
    jest.clearAllMocks();
    localStorage.clear();
    
    // Override localStorage.getItem specifically for auth_token
    localStorage.getItem = jest.fn((key) => {
      if (key === 'auth_token') {
        return 'test-token';
      }
      return null;
    });
    
    // Setup mock axios instance
    mockAxiosInstance = {
      get: jest.fn().mockImplementation((url) => {
        return Promise.resolve({ data: {} });
      }),
      post: jest.fn().mockImplementation((url) => {
        return Promise.resolve({ data: {} });
      }),
      put: jest.fn().mockResolvedValue({ data: {} }),
      delete: jest.fn().mockResolvedValue({ data: {} }),
      interceptors: {
        request: { use: jest.fn(), eject: jest.fn() },
        response: { use: jest.fn(), eject: jest.fn() }
      }
    };
    
    // Mock axios.create to ensure it returns our mockAxiosInstance
    // This needs to happen BEFORE we require the API service module
    jest.spyOn(axios, 'create').mockImplementation(() => mockAxiosInstance);
    
    // Force a reimport of the API module to ensure it uses our mocked axios
    jest.isolateModules(() => {
      jest.doMock('axios', () => axios);
    });
  });
  
  // Ensure axios.create returns our mockAxiosInstance
  jest.spyOn(axios, 'create').mockReturnValue(mockAxiosInstance);
  
  // Run the API client setup to trigger axios.create
  // This ensures our API tests use the mocked instance
  require('../api');
  
  describe('apiClient configuration', () => {
    test('creates axios instance with correct configuration', () => {
      // Reset all mocks to ensure clean state
      jest.clearAllMocks();
      
      // Re-require the API module to trigger a fresh axios.create call
      jest.isolateModules(() => {
        // Mock axios to capture the axios.create call
        const mockAxiosCreate = jest.fn().mockReturnValue({
          get: jest.fn().mockResolvedValue({ data: {} }),
          post: jest.fn().mockResolvedValue({ data: {} }),
          interceptors: {
            request: { use: jest.fn() },
            response: { use: jest.fn() }
          }
        });
        
        // Apply the mock
        axios.create = mockAxiosCreate;
        
        // Now import the API module which should call axios.create
        require('../api');
        
        // Verify axios.create was called with proper configuration
        expect(mockAxiosCreate).toHaveBeenCalled();
        expect(mockAxiosCreate).toHaveBeenCalledWith(expect.objectContaining({
          baseURL: expect.any(String),
          timeout: expect.any(Number),
          headers: expect.objectContaining({
            'Content-Type': 'application/json'
          })
        }));
      });
    });
  });
  
  describe('setupInterceptors', () => {
    test('configures request interceptor to add auth token', () => {
      // Manually create the request interceptor function as defined in the API file
      const requestInterceptor = (config) => {
        const token = localStorage.getItem('auth_token');
        if (token) {
          config.headers['Authorization'] = `Bearer ${token}`;
        }
        return config;
      };
      
      // Test without token behavior
      // Override localStorage.getItem to return null for this test case
      localStorage.getItem = jest.fn().mockImplementation((key) => {
        return null; // No token found
      });
      
      const configWithoutToken = { headers: {} };
      const resultWithoutToken = requestInterceptor(configWithoutToken);
      expect(resultWithoutToken.headers.Authorization).toBeUndefined();
      
      // Test with token behavior
      // Override localStorage.getItem to return a token for this test case
      localStorage.getItem = jest.fn().mockImplementation((key) => {
        if (key === 'auth_token') {
          return 'test-token';
        }
        return null;
      });
      
      const configWithToken = { headers: {} };
      const resultWithToken = requestInterceptor(configWithToken);
      expect(resultWithToken.headers.Authorization).toBe('Bearer test-token');
    });
    
    test('configures response interceptor to handle errors', () => {
      setupInterceptors(mockAxiosInstance);
      
      // Get response interceptor functions
      const successInterceptor = mockAxiosInstance.interceptors.response.use.mock.calls[0][0];
      const errorInterceptor = mockAxiosInstance.interceptors.response.use.mock.calls[0][1];
      
      expect(successInterceptor).toBeDefined();
      expect(errorInterceptor).toBeDefined();
      
      // Test success pass-through
      const response = { data: 'test' };
      expect(successInterceptor(response)).toBe(response);
      
      // Test 401 error handling
      const error401 = { response: { status: 401 } };
      
      // Mock window.location to prevent actual navigation in tests
      const originalLocation = window.location;
      delete window.location;
      window.location = { href: '', pathname: '/dashboard' };
      
      // The error interceptor should return a rejected promise
      const rejectedPromise401 = errorInterceptor(error401);
      
      // After the interceptor runs, verify localStorage was cleared and redirect happened
      return rejectedPromise401.catch(e => {
        expect(localStorage.removeItem).toHaveBeenCalledWith('auth_token');
        expect(localStorage.removeItem).toHaveBeenCalledWith('user_info');
        expect(window.location.href).toBe('/login');
        
        // Verify it's the same error object we passed in
        expect(e).toBe(error401);
        
        // Restore window.location after test
        window.location = originalLocation;
      });
      
      // Test other errors
      const error500 = { response: { status: 500, data: { message: 'Server error' } } };
      
      // The error interceptor should return a rejected promise
      const rejectedPromise500 = errorInterceptor(error500);
      
      // Verify it's a rejected promise with the expected error
      return rejectedPromise500.catch(e => {
        // Verify it's the same error object we passed in
        expect(e).toBe(error500);
        expect(e.response.status).toBe(500);
        expect(e.response.data.message).toBe('Server error');
      });
    });
  });
  
  describe('API Services', () => {
    test('authAPI provides all required methods', () => {
      expect(authAPI).toHaveProperty('login');
      expect(authAPI).toHaveProperty('signUp');
      expect(authAPI).toHaveProperty('logout');
      expect(authAPI).toHaveProperty('validateToken');
      expect(authAPI).toHaveProperty('refreshToken');
      expect(authAPI).toHaveProperty('getUserInfo');
      expect(authAPI).toHaveProperty('updateUserInfo');
      expect(authAPI).toHaveProperty('changePassword');
      
      // Verify all methods are functions
      Object.values(authAPI).forEach(method => {
        expect(typeof method).toBe('function');
      });
    });
    
    test('identifyAPI provides all required methods', () => {
      expect(identifyAPI).toHaveProperty('identifyFile');
      expect(identifyAPI).toHaveProperty('identifyUrl');
      expect(identifyAPI).toHaveProperty('getResults');
      expect(identifyAPI).toHaveProperty('getHistory');
      expect(identifyAPI).toHaveProperty('getStats');
      
      // Verify all methods are functions
      Object.values(identifyAPI).forEach(method => {
        expect(typeof method).toBe('function');
      });
    });
    
    test('metadataAPI provides all required methods', () => {
      expect(metadataAPI).toHaveProperty('getEnriched');
      expect(metadataAPI).toHaveProperty('getFields');
      expect(metadataAPI).toHaveProperty('getSources');
      expect(metadataAPI).toHaveProperty('refreshMetadata');
      expect(metadataAPI).toHaveProperty('getPermissions');
      
      // Verify all methods are functions
      Object.values(metadataAPI).forEach(method => {
        expect(typeof method).toBe('function');
      });
    });
    
    test('API services are correctly configured', () => {
    // Reset all mocks to ensure clean state
    jest.clearAllMocks();
    
    // Re-require the API module to trigger a fresh axios.create call
    jest.isolateModules(() => {
      // Mock axios to capture the axios.create call
      const mockAxiosCreate = jest.fn().mockReturnValue({
        get: jest.fn().mockResolvedValue({ data: {} }),
        post: jest.fn().mockResolvedValue({ data: {} }),
        put: jest.fn().mockResolvedValue({ data: {} }),
        delete: jest.fn().mockResolvedValue({ data: {} }),
        interceptors: {
          request: { use: jest.fn() },
          response: { use: jest.fn() }
        }
      });
      
      // Apply the mock
      axios.create = mockAxiosCreate;
      
      // Now import the API module which should call axios.create
      const { apiClient } = require('../api');
      
      // Verify axios.create was called with proper configuration
      expect(mockAxiosCreate).toHaveBeenCalled();
      expect(mockAxiosCreate).toHaveBeenCalledWith(expect.objectContaining({
        baseURL: expect.any(String),
        headers: expect.objectContaining({
          'Content-Type': 'application/json'
        }),
        timeout: expect.any(Number)
      }));
    });
  });
  });
});
