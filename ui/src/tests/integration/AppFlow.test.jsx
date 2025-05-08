import React from 'react';
import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import App from '../../App';
import { renderWithProviders, setupMockAPIResponses, createMockVideoFile } from '../../utils/integrationTestUtils';
import axios from 'axios';

// Mock axios
jest.mock('axios', () => {
  const mockAxios = {
    create: jest.fn(() => mockAxios),
    get: jest.fn(),
    post: jest.fn(),
    put: jest.fn(),
    delete: jest.fn(),
    interceptors: {
      request: { use: jest.fn(), eject: jest.fn() },
      response: { use: jest.fn(), eject: jest.fn() }
    }
  };
  return mockAxios;
});

// Mock window.matchMedia to avoid JSDOM errors
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: jest.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: jest.fn(), // deprecated
    removeListener: jest.fn(), // deprecated
    addEventListener: jest.fn(),
    removeEventListener: jest.fn(),
    dispatchEvent: jest.fn()
  }))
});

// Mock localStorage to avoid errors
const localStorageMock = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn()
};
Object.defineProperty(window, 'localStorage', { value: localStorageMock });

describe('Videntify App Integration Flow', () => {
  let user;
  
  beforeEach(() => {
    // Setup mock API responses
    setupMockAPIResponses(axios);
    
    // Clear mocks
    jest.clearAllMocks();
    localStorageMock.getItem.mockReset();
    localStorageMock.setItem.mockReset();
    
    // Create user event
    user = userEvent.default ? userEvent.default : userEvent;
  });
  
  it('completes full authentication and video identification flow', async () => {
    // Mock API responses and localStorage before rendering
    setupMockAPIResponses();
    
    // Render the application - don't wrap with Router since App already has a Router
    renderWithProviders(<App />, { withRouter: false });
    
    // Initially, should redirect to login page if not authenticated
    expect(screen.getByText(/Log In to Videntify/i)).toBeInTheDocument();
    
    // Perform login
    await user.type(screen.getByLabelText(/Email Address/i), 'test@example.com');
    await user.type(screen.getByLabelText(/Password/i), 'password123');
    await user.click(screen.getByRole('button', { name: /Log In/i }));
    
    // Wait for login to complete and redirect to home page
    await waitFor(() => {
      expect(axios.post).toHaveBeenCalledWith(expect.stringContaining('/auth/login'), expect.any(Object));
      expect(localStorageMock.setItem).toHaveBeenCalledWith('auth_token', expect.any(String));
    });
    
    // User should now be redirected to home page
    await waitFor(() => {
      expect(screen.getByText(/Welcome to Videntify/i)).toBeInTheDocument();
    });
    
    // Navigate to search page (assuming there's a navigation button/link)
    const searchLink = screen.getByText(/Search/i);
    await user.click(searchLink);
    
    // Verify we're on the search page
    await waitFor(() => {
      expect(screen.getByText(/Upload a file/i)).toBeInTheDocument();
    });
    
    // Perform file upload for identification
    const fileInput = screen.getByTestId('file-input');
    const file = createMockVideoFile();
    
    // Mock file selection
    await user.upload(fileInput, file);
    
    // Verify file is displayed
    await waitFor(() => {
      expect(screen.getByText(/test-video.mp4/i)).toBeInTheDocument();
    });
    
    // Click identify button
    await user.click(screen.getByRole('button', { name: /Identify Video/i }));
    
    // Verify API call was made and redirect to results page
    await waitFor(() => {
      expect(axios.post).toHaveBeenCalledWith(
        expect.stringContaining('/identify/file'),
        expect.any(Object),
        expect.any(Object)
      );
    });
    
    // Verify results are displayed
    await waitFor(() => {
      expect(screen.getByText(/Identification Results/i)).toBeInTheDocument();
      expect(screen.getByText(/Sample Video Title/i)).toBeInTheDocument();
    });
    
    // View details of the identified video
    await user.click(screen.getByText(/Sample Video Title/i));
    
    // Verify metadata is displayed
    await waitFor(() => {
      expect(screen.getByText(/Video Details/i)).toBeInTheDocument();
      expect(screen.getByText(/Director Name/i)).toBeInTheDocument();
    });
    
    // Test logout functionality
    const userMenu = screen.getByTestId('user-menu');
    await user.click(userMenu);
    
    const logoutButton = screen.getByText(/Log Out/i);
    await user.click(logoutButton);
    
    // Verify user is logged out and redirected to login page
    await waitFor(() => {
      expect(localStorageMock.removeItem).toHaveBeenCalledWith('auth_token');
      expect(screen.getByText(/Log In to Videntify/i)).toBeInTheDocument();
    });
  });
});
