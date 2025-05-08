/**
 * Test utilities for Videntify UI components
 * Provides mock data and helper functions for testing
 */

// Mock authentication data
export const mockAuthData = {
  user: {
    id: 'user-123',
    name: 'Test User',
    email: 'test@example.com',
    role: 'user',
    created_at: '2023-01-01T00:00:00Z'
  },
  token: 'mock-jwt-token.with.signature'
};

// Mock video metadata
export const mockVideoMetadata = {
  content_id: 'video-123',
  title: 'Sample Video Title',
  description: 'This is a sample video description for testing purposes.',
  duration: 125,
  timestamp: 45,
  thumbnail_url: 'https://example.com/thumbnail.jpg',
  poster_url: 'https://example.com/poster.jpg',
  release_date: '2022-10-15',
  genres: ['Action', 'Drama'],
  directors: ['Director Name'],
  cast: [
    { name: 'Actor One', role: 'Character One' },
    { name: 'Actor Two', role: 'Character Two' }
  ],
  vote_average: 8.5,
  _sources: {
    title: 'tmdb',
    description: 'tmdb',
    poster_url: 'tmdb'
  }
};

// Mock identification results
export const mockIdentificationResults = {
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
};

// Mock user identification history
export const mockUserHistory = [
  {
    query_id: 'query-123',
    title: 'Sample Video Title',
    timestamp: '2023-10-15T12:30:45Z',
    match_count: 2,
    thumbnail_url: 'https://example.com/thumbnail.jpg',
    content_type: 'movie',
    extractor_type: 'cnn'
  },
  {
    query_id: 'query-456',
    title: 'Another Query',
    timestamp: '2023-10-10T10:20:30Z',
    match_count: 1,
    thumbnail_url: 'https://example.com/another-thumbnail.jpg',
    content_type: 'tv_show',
    extractor_type: 'phash'
  }
];

// Mock metadata enrichment sources
export const mockMetadataSources = {
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
  },
  wikipedia: {
    title: 'Sample Video Title',
    extract: 'A longer description from Wikipedia with additional information...',
    url: 'https://en.wikipedia.org/wiki/Sample_Video'
  }
};

/**
 * Create a mock MetadataContext provider for testing
 * @returns {Object} Mock context value
 */
export const createMockMetadataContext = () => ({
  // Authentication values
  isAuthenticated: true,
  userInfo: mockAuthData.user,
  userPermission: 'user',
  authLoading: false,
  authError: null,
  login: jest.fn().mockResolvedValue(true),
  signUp: jest.fn().mockResolvedValue(true),
  logout: jest.fn(),
  updateUserPreferences: jest.fn().mockResolvedValue(true),
  
  // Metadata values
  metadataCache: {
    'video-123': mockVideoMetadata
  },
  loading: {},
  metadataAPI: {
    getEnriched: jest.fn(),
    getFields: jest.fn(),
    getSources: jest.fn(),
    refreshMetadata: jest.fn()
  }
});

/**
 * Mock API responses for testing
 */
export const mockApiResponses = {
  // Auth API
  '/auth/login': {
    status: 200,
    data: mockAuthData
  },
  '/auth/register': {
    status: 201,
    data: { message: 'User registered successfully' }
  },
  '/auth/validate': {
    status: 200,
    data: { valid: true }
  },
  '/auth/user': {
    status: 200,
    data: mockAuthData.user
  },
  
  // Identify API
  '/identify/file': {
    status: 202,
    data: { query_id: 'query-123', status: 'processing' }
  },
  '/identify/url': {
    status: 202,
    data: { query_id: 'query-123', status: 'processing' }
  },
  '/identify/results/query-123': {
    status: 200,
    data: mockIdentificationResults
  },
  '/identify/history': {
    status: 200,
    data: { queries: mockUserHistory }
  },
  
  // Metadata API
  '/metadata/video-123': {
    status: 200,
    data: mockMetadataSources
  },
  '/metadata/fields': {
    status: 200,
    data: {
      fields: [
        { name: 'title', type: 'string', description: 'Content title' },
        { name: 'description', type: 'string', description: 'Content description' },
        { name: 'release_date', type: 'date', description: 'Release date' }
      ]
    }
  },
  '/metadata/sources': {
    status: 200,
    data: {
      sources: [
        { id: 'tmdb', name: 'TMDB', description: 'The Movie Database' },
        { id: 'imdb', name: 'IMDb', description: 'Internet Movie Database' },
        { id: 'wikipedia', name: 'Wikipedia', description: 'Wikipedia Articles' }
      ]
    }
  }
};

/**
 * Setup mock axios for tests
 * @param {Object} mockAxios - Axios mock instance
 */
export const setupMockAxios = (mockAxios) => {
  // Default mock implementation for get requests
  mockAxios.get.mockImplementation((url) => {
    const endpoint = Object.keys(mockApiResponses).find(key => url.includes(key));
    
    if (endpoint) {
      const response = mockApiResponses[endpoint];
      return Promise.resolve({ status: response.status, data: response.data });
    }
    
    return Promise.reject(new Error(`No mock response for GET ${url}`));
  });
  
  // Default mock implementation for post requests
  mockAxios.post.mockImplementation((url) => {
    const endpoint = Object.keys(mockApiResponses).find(key => url.includes(key));
    
    if (endpoint) {
      const response = mockApiResponses[endpoint];
      return Promise.resolve({ status: response.status, data: response.data });
    }
    
    return Promise.reject(new Error(`No mock response for POST ${url}`));
  });
};
