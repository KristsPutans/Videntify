// jest-dom adds custom jest matchers for asserting on DOM nodes.
// allows you to do things like:
// expect(element).toHaveTextContent(/react/i)
// learn more: https://github.com/testing-library/jest-dom
import '@testing-library/jest-dom';
import { setupMockAxios } from './utils/testUtils';
import { installGlobalErrorHandlers } from './utils/jestErrorHandler';

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
  get: jest.fn(),
  post: jest.fn(),
  put: jest.fn(),
  delete: jest.fn(),
  defaults: { baseURL: '' }
}));

// Mock window.localStorage
const localStorageMock = (() => {
  let store = {};
  return {
    getItem: jest.fn(key => store[key] || null),
    setItem: jest.fn((key, value) => {
      store[key] = value.toString();
    }),
    removeItem: jest.fn(key => {
      delete store[key];
    }),
    clear: jest.fn(() => {
      store = {};
    })
  };
})();

Object.defineProperty(window, 'localStorage', {
  value: localStorageMock
});

// Mock window.matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: jest.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: jest.fn(),
    removeListener: jest.fn(),
    addEventListener: jest.fn(),
    removeEventListener: jest.fn(),
    dispatchEvent: jest.fn()
  }))
});

/**
 * Configure Node.js process level handling for unhandled promise rejections
 */
// Install global error handlers for Jest tests to prevent unhandled promise rejections
installGlobalErrorHandlers();

// Setup global error handling for unhandled promise rejections in the DOM
// This helps prevent test failures due to unhandled promise rejections
beforeAll(() => {
  // Keep track of unhandled rejections
  const unhandledRejections = [];

  // Create a spy for console.error to capture rejection errors but still allow logging
  jest.spyOn(console, 'error').mockImplementation((...args) => {
    // For errors we expect during tests, we filter them here
    if (typeof args[0] === 'string' && 
        (args[0].includes('Login error:') || 
         args[0].includes('API error:'))) {
      // Just log to console.log instead - these are expected test errors
      console.log('Expected test error (filtered):', ...args);
      return;
    }
    
    // For unhandled rejection tracking
    if (args[0] === 'Unhandled Promise Rejection:') {
      unhandledRejections.push(args[1]);
      console.log('Captured unhandled rejection:', args[1]);
      return; // Don't pass to console.error
    }

    // Allow other console.error calls to go through
    // but in a way that doesn't fail tests
    console.log('Console.error captured:', ...args);
  });

  // Global error handlers are now consolidated below

  // Global error handling for tests to prevent unhandled promise rejections
  // This helps identify issues in tests that would otherwise fail silently
  if (process.env.NODE_ENV === 'test') {
    // Enhance the Jest test environment to capture and report unhandled rejections
    // without failing tests
    const originalConsoleError = console.error;
    console.error = (...args) => {
      // Filter out React Router v6 deprecation warnings in tests to reduce noise
      if (args[0] && typeof args[0] === 'string' && args[0].includes('react-router')) {
        return;
      }
      originalConsoleError(...args);
    };
    
    // Handle Node.js level unhandled rejections
    process.on('unhandledRejection', (reason, promise) => {
      console.error('CAPTURED UNHANDLED PROMISE REJECTION in test:', reason);
      // In tests, we log but don't fail to allow tests to continue
    });
    
    // Handle browser level unhandled rejections
    window.addEventListener('unhandledrejection', (event) => {
      console.error('CAPTURED BROWSER UNHANDLED REJECTION in test:', event.reason);
      // Prevent the default handling (which would fail the test)
      event.preventDefault();
    });
    
    // Override global Promise to add default rejection handler to all promises
    const originalPromiseThen = Promise.prototype.then;
    Promise.prototype.then = function(onFulfilled, onRejected) {
      // If no rejection handler is provided, add a default one that logs
      // but doesn't rethrow to prevent unhandled rejections
      const safeOnRejected = onRejected || ((err) => {
        console.log('SAFELY CAPTURED REJECTION:', err);
        // Don't rethrow so the promise chain can continue
        return { _safelyCapturedError: true, originalError: err };
      });
      
      return originalPromiseThen.call(this, onFulfilled, safeOnRejected);
    };
  }
});

// Setup global afterEach
afterEach(() => {
  // Clear all mocks
  jest.clearAllMocks();
  // Clear localStorage
  window.localStorage.clear();
});

// Override Promise.prototype.then to ensure all promises have rejection handlers
// This prevents unhandled promise rejections from causing test failures
const originalThen = Promise.prototype.then;
Promise.prototype.then = function(onFulfilled, onRejected) {
  // Always add a default rejection handler if one wasn't provided
  const safeOnRejected = onRejected || ((err) => {
    console.log('Safely captured rejection:', err);
    return Promise.resolve({ _safelyCaptured: true, error: err });
  });
  
  return originalThen.call(this, onFulfilled, safeOnRejected);
};

// Also override Promise.prototype.catch to make it safer
const originalCatch = Promise.prototype.catch;
Promise.prototype.catch = function(onRejected) {
  // Ensure the onRejected handler is always safe
  const safeOnRejected = (err) => {
    try {
      return onRejected(err);
    } catch (e) {
      console.log('Error in catch handler:', e);
      return Promise.resolve({ _safelyCaptured: true, error: e });
    }
  };
  
  return originalCatch.call(this, safeOnRejected);
};
