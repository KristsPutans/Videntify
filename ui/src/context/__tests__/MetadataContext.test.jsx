import React from 'react';
import { render, act, waitFor } from '@testing-library/react';
import { MetadataContext, MetadataProvider, useMetadata } from '../MetadataContext';
import { mockAuthData, mockVideoMetadata } from '../../utils/testUtils';
import { authAPI, metadataAPI } from '../../services/api';

// Create a mock context for testing
const createMockMetadataContext = () => ({
  // Authentication values
  isAuthenticated: true,
  userInfo: mockAuthData.user,
  userPermission: 'user',
  authLoading: false,
  authError: null,
  login: jest.fn().mockResolvedValue(true),
  signUp: jest.fn().mockResolvedValue(true),
  logout: jest.fn().mockResolvedValue(),
  updateUserPreferences: jest.fn().mockResolvedValue(true),
  
  // Metadata values
  metadataCache: {
    'video-123': mockVideoMetadata
  },
  loading: {},
  error: {},
  fetchMetadata: jest.fn().mockResolvedValue(mockVideoMetadata),
  clearMetadataCache: jest.fn()
});

// Mock localStorage
const localStorageMock = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn()
};
Object.defineProperty(window, 'localStorage', { value: localStorageMock });

// Mock the API module
jest.mock('../../services/api', () => ({
  authAPI: {
    login: jest.fn(),
    signUp: jest.fn(),
    logout: jest.fn().mockReturnValue(Promise.resolve()),
    validateToken: jest.fn(),
    getUserInfo: jest.fn(),
    updateUserInfo: jest.fn()
  },
  metadataAPI: {
    getEnriched: jest.fn(),
    getFields: jest.fn(),
    getSources: jest.fn(),
    refreshMetadata: jest.fn()
  }
}));

// Test component that uses the context
const TestComponent = () => {
  const metadata = useMetadata();
  return (
    <div data-testid="test-component">
      <div data-testid="is-authenticated">{metadata.isAuthenticated ? 'true' : 'false'}</div>
      <div data-testid="user-info">{metadata.userInfo ? JSON.stringify(metadata.userInfo) : 'null'}</div>
      <button data-testid="login-button" onClick={() => metadata.login({ email: 'test@example.com', password: 'password123' })}>Login</button>
      <button data-testid="logout-button" onClick={() => metadata.logout()}>Logout</button>
      <button data-testid="fetch-metadata-button" onClick={() => metadata.fetchMetadata('video-123')}>Get Metadata</button>
    </div>
  );
};

describe('MetadataContext', () => {
  beforeEach(() => {
    // Clear all mocks before each test
    jest.clearAllMocks();
    localStorageMock.getItem.mockReset();
    localStorageMock.setItem.mockReset();
    localStorageMock.removeItem.mockReset();
  });
  
  test('initializes with default values', () => {
    localStorageMock.getItem.mockReturnValue(null); // No token in localStorage
    
    const { getByTestId } = render(
      <MetadataProvider>
        <TestComponent />
      </MetadataProvider>
    );
    
    expect(getByTestId('is-authenticated').textContent).toBe('false');
    expect(getByTestId('user-info').textContent).toBe('null');
  });
  
  test('checks token and loads user data on initialization when token exists', async () => {
    // Mock token in localStorage
    localStorageMock.getItem.mockImplementation((key) => {
      if (key === 'auth_token') return 'valid-token';
      return null;
    });
    
    // Mock successful token validation and user info retrieval
    authAPI.validateToken.mockResolvedValue({ data: { valid: true } });
    authAPI.getUserInfo.mockResolvedValue({ data: mockAuthData.user });
    
    let component;
    await act(async () => {
      component = render(
        <MetadataProvider>
          <TestComponent />
        </MetadataProvider>
      );
    });
    
    await waitFor(() => {
      expect(authAPI.validateToken).toHaveBeenCalled();
      expect(authAPI.getUserInfo).toHaveBeenCalled();
      expect(component.getByTestId('is-authenticated').textContent).toBe('true');
      expect(JSON.parse(component.getByTestId('user-info').textContent)).toEqual(mockAuthData.user);
    });
  });
  
  test('handles login successfully', async () => {
    // Mock successful login
    authAPI.login.mockResolvedValue({ data: mockAuthData });
    
    const { getByTestId } = render(
      <MetadataProvider>
        <TestComponent />
      </MetadataProvider>
    );
    
    // Initially not authenticated
    expect(getByTestId('is-authenticated').textContent).toBe('false');
    
    // Perform login
    await act(async () => {
      getByTestId('login-button').click();
    });
    
    // After login, should be authenticated
    await waitFor(() => {
      expect(authAPI.login).toHaveBeenCalled();
      expect(localStorageMock.setItem).toHaveBeenCalledWith('auth_token', mockAuthData.token);
      expect(getByTestId('is-authenticated').textContent).toBe('true');
      expect(JSON.parse(getByTestId('user-info').textContent)).toEqual(mockAuthData.user);
    });
  });
  
  test('handles logout correctly', async () => {
    // Set initial authenticated state
    localStorageMock.getItem.mockReturnValue('valid-token');
    authAPI.validateToken.mockResolvedValue({ data: { valid: true } });
    authAPI.getUserInfo.mockResolvedValue({ data: mockAuthData.user });
    
    const { getByTestId } = render(
      <MetadataProvider>
        <TestComponent />
      </MetadataProvider>
    );
    
    // Wait for initial authentication
    await waitFor(() => {
      expect(getByTestId('is-authenticated').textContent).toBe('true');
    });
    
    // Perform logout
    await act(async () => {
      getByTestId('logout-button').click();
    });
    
    // After logout, should be unauthenticated
    expect(localStorageMock.removeItem).toHaveBeenCalledWith('auth_token');
    expect(getByTestId('is-authenticated').textContent).toBe('false');
    expect(getByTestId('user-info').textContent).toBe('null');
  });
  
  test('fetches metadata successfully', async () => {
    // Mock successful metadata fetch
    metadataAPI.getEnriched.mockResolvedValue({ data: mockVideoMetadata });
    
    const { getByTestId } = render(
      <MetadataProvider>
        <TestComponent />
      </MetadataProvider>
    );
    
    // Fetch metadata
    await act(async () => {
      getByTestId('fetch-metadata-button').click();
    });
    
    // Check if API was called
    await waitFor(() => {
      expect(metadataAPI.getEnriched).toHaveBeenCalled();
    });
  });
  
  test('handles login failure correctly', async () => {
    // Mock failed login
    authAPI.login.mockRejectedValue(new Error('Invalid credentials'));
    
    const { getByTestId } = render(
      <MetadataProvider>
        <TestComponent />
      </MetadataProvider>
    );
    
    // Perform login
    await act(async () => {
      getByTestId('login-button').click();
    });
    
    // Should still be unauthenticated after failed login
    await waitFor(() => {
      expect(authAPI.login).toHaveBeenCalled();
      expect(getByTestId('is-authenticated').textContent).toBe('false');
    });
  });
});
