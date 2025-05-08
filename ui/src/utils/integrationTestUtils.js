/**
 * Integration test utilities for Videntify UI
 * Provides helpers for testing the full application flow
 */
import React from 'react';
import { render } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { MetadataProvider } from '../context/MetadataContext';

/**
 * Custom renderer that wraps components with all necessary providers for integration testing
 * @param {JSX.Element} ui - Component to render
 * @param {Object} options - Additional options for customizing the rendering
 * @param {boolean} options.withRouter - Whether to wrap with BrowserRouter (default: false)
 * @returns {Object} Rendered component with testing utilities
 */
export const renderWithProviders = (ui, { withRouter = false } = {}) => {
  // Wrap with providers based on options
  const Wrapper = ({ children }) => (
    <MetadataProvider>
      {withRouter ? <BrowserRouter>{children}</BrowserRouter> : children}
    </MetadataProvider>
  );
  
  return render(ui, { wrapper: Wrapper });
};

/**
 * Simulate a complete authentication flow
 * @param {Object} user - User interface from testing-library
 * @param {Object} screen - Screen from testing-library
 * @param {Object} credentials - User credentials (email, password)
 */
export const performLogin = async (user, screen, credentials = { email: 'test@example.com', password: 'password123' }) => {
  // Fill in the email field
  await user.type(screen.getByLabelText(/email address/i), credentials.email);
  
  // Fill in the password field
  await user.type(screen.getByLabelText(/password/i), credentials.password);
  
  // Click login button
  await user.click(screen.getByRole('button', { name: /log in/i }));
};

/**
 * Simulate a complete video identification flow using file upload
 * @param {Object} user - User interface from testing-library
 * @param {Object} screen - Screen from testing-library
 * @param {File} videoFile - Video file to identify
 */
export const performVideoIdentification = async (user, screen, videoFile) => {
  // Assume we're on the search page with VideoIdentifier component
  
  // Find the file input
  const fileInput = screen.getByTestId('file-input');
  
  // Upload the video file
  await user.upload(fileInput, videoFile);
  
  // Click the identify button
  await user.click(screen.getByRole('button', { name: /identify video/i }));
};

/**
 * Create a mock video file for testing
 * @returns {File} Mock video file
 */
export const createMockVideoFile = () => {
  return new File(['dummy video content'], 'test-video.mp4', { type: 'video/mp4' });
};

/**
 * Mock API responses for integration testing
 * @param {Object} mockAxios - Mock axios instance (optional)
 */
export const setupMockAPIResponses = (mockAxios = require('axios')) => {
  // If axios is not mocked yet, mock it
  if (!mockAxios.post?.mockImplementation) {
    jest.mock('axios', () => ({
      post: jest.fn(),
      get: jest.fn(),
      create: jest.fn().mockReturnThis(),
      interceptors: {
        request: { use: jest.fn() },
        response: { use: jest.fn() }
      }
    }));
    mockAxios = require('axios');
  }
  // Auth endpoints
  mockAxios.post.mockImplementation((url, data) => {
    if (url.includes('/auth/login')) {
      return Promise.resolve({
        status: 200,
        data: {
          token: 'mock-jwt-token',
          user: {
            id: 'user-123',
            name: 'Test User',
            email: 'test@example.com',
            role: 'user'
          }
        }
      });
    }
    
    if (url.includes('/identify/file')) {
      return Promise.resolve({
        status: 202,
        data: {
          query_id: 'query-123',
          status: 'processing'
        }
      });
    }
    
    if (url.includes('/identify/url')) {
      return Promise.resolve({
        status: 202,
        data: {
          query_id: 'query-456',
          status: 'processing'
        }
      });
    }
    
    return Promise.reject(new Error(`No mock for POST ${url}`));
  });
  
  // GET endpoints
  mockAxios.get.mockImplementation((url) => {
    if (url.includes('/auth/validate')) {
      return Promise.resolve({
        status: 200,
        data: {
          valid: true
        }
      });
    }
    
    if (url.includes('/auth/user')) {
      return Promise.resolve({
        status: 200,
        data: {
          id: 'user-123',
          name: 'Test User',
          email: 'test@example.com',
          role: 'user'
        }
      });
    }
    
    if (url.includes('/identify/results/')) {
      return Promise.resolve({
        status: 200,
        data: {
          query_id: 'query-123',
          status: 'completed',
          created_at: '2023-10-15T12:30:45Z',
          duration: 2.5,
          matches: [
            {
              content_id: 'video-123',
              confidence: 0.95,
              timestamp: 45,
              title: 'Sample Video Title',
              thumbnail_url: 'https://example.com/thumbnail.jpg'
            },
            {
              content_id: 'video-456',
              confidence: 0.75,
              timestamp: 120,
              title: 'Another Video',
              thumbnail_url: 'https://example.com/another-thumbnail.jpg'
            }
          ]
        }
      });
    }
    
    if (url.includes('/metadata/')) {
      return Promise.resolve({
        status: 200,
        data: {
          tmdb: {
            title: 'Sample Video Title',
            overview: 'This is a sample video description for testing purposes.',
            poster_url: 'https://example.com/poster.jpg',
            release_date: '2022-10-15',
            vote_average: 8.5
          },
          imdb: {
            title: 'Sample Video Title (Original)',
            plot: 'A slightly different description from IMDb',
            directors: ['Director Name'],
            cast: [
              { name: 'Actor One', role: 'Character One' },
              { name: 'Actor Two', role: 'Character Two' }
            ]
          }
        }
      });
    }
    
    return Promise.reject(new Error(`No mock for GET ${url}`));
  });
};
