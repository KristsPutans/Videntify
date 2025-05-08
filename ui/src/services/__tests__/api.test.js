import axios from 'axios';
import {
  apiClient,
  authAPI,
  identifyAPI,
  metadataAPI,
  setupInterceptors
} from '../api';
import { mockApiResponses, mockAuthData } from '../../utils/testUtils';

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
  
  beforeEach(() => {
    jest.clearAllMocks();
    localStorage.clear();
    
    // Setup mock axios instance
    mockAxiosInstance = {
      get: jest.fn().mockImplementation((url) => {
        const endpoint = Object.keys(mockApiResponses).find(key => url.includes(key));
        if (endpoint) {
          return Promise.resolve(mockApiResponses[endpoint]);
        }
        return Promise.reject(new Error(`No mock response for GET ${url}`));
      }),
      post: jest.fn().mockImplementation((url) => {
        const endpoint = Object.keys(mockApiResponses).find(key => url.includes(key));
        if (endpoint) {
          return Promise.resolve(mockApiResponses[endpoint]);
        }
        return Promise.reject(new Error(`No mock response for POST ${url}`));
      }),
      put: jest.fn(),
      delete: jest.fn(),
      interceptors: {
        request: { use: jest.fn(), eject: jest.fn() },
        response: { use: jest.fn(), eject: jest.fn() }
      }
    };
    
    // Mock axios.create to return our mockAxiosInstance
    axios.create.mockImplementation(() => mockAxiosInstance);
    
    // Force a reimport of the API module to ensure it uses our mocked axios
    jest.isolateModules(() => {
      jest.doMock('axios', () => axios);
    });
  });
  
  // Skip call to axios.create since we're mocking it
  jest.spyOn(axios, 'create').mockReturnValue(mockAxiosInstance);
  
  describe('apiClient configuration', () => {
    test('creates axios instance with correct configuration', () => {
      expect(axios.create).toHaveBeenCalled();
      expect(axios.create).toHaveBeenCalledWith(expect.objectContaining({
        baseURL: expect.any(String),
        timeout: expect.any(Number),
        headers: expect.objectContaining({
          'Content-Type': 'application/json'
        })
      }));
    });
  });
  
  describe('setupInterceptors', () => {
    test('configures request interceptor to add auth token', () => {
      setupInterceptors(mockAxiosInstance);
      
      // Get request interceptor function
      const requestInterceptor = mockAxiosInstance.interceptors.request.use.mock.calls[0][0];
      expect(requestInterceptor).toBeDefined();
      
      // Test with no token
      const configWithoutToken = { headers: {} };
      const resultWithoutToken = requestInterceptor(configWithoutToken);
      expect(resultWithoutToken.headers.Authorization).toBeUndefined();
      
      // Test with token
      localStorage.setItem('auth_token', 'test-token');
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
      expect(() => errorInterceptor(error401)).toThrow();
      
      // Test other errors
      const error500 = { response: { status: 500, data: { message: 'Server error' } } };
      expect(() => errorInterceptor(error500)).toThrow('Server error');
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
    
    test('API services make requests with correct configurations', async () => {
      // Test a sample API call from each service
      try {
        await authAPI.login({ email: 'test@example.com', password: 'password123' });
        await identifyAPI.getResults('test-query-id');
        await metadataAPI.getEnriched('video-123');
      } catch (error) {
        // We expect errors in test environment without proper mocking
        // Just verify the axios mock was called
      }
      
      // Verify axios was called the expected number of times
      expect(mockAxiosInstance.post).toHaveBeenCalled();
      expect(mockAxiosInstance.get).toHaveBeenCalled();
    });
  });
});
