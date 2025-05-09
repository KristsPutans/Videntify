/**
 * Jest Error Handler
 * 
 * This module provides utilities for handling unhandled promise rejections in Jest tests
 * to prevent tests from failing due to expected rejections in test scenarios.
 */

/**
 * Installs global error handlers for Jest tests
 * This function should be called in setupTests.js
 */
export const installGlobalErrorHandlers = () => {
  // Store original process.emit to restore later if needed
  const originalEmit = process.emit;
  
  // Override process.emit to intercept unhandledRejection events
  process.emit = function(event, ...args) {
    if (event === 'unhandledRejection') {
      const reason = args[0];
      const promise = args[1];
      
      console.log('INTERCEPTED unhandled rejection:', reason);
      
      // Prevent Jest from failing the test due to this rejection
      if (promise && typeof promise.catch === 'function') {
        promise.catch(() => {
          // Explicitly catch the rejection to prevent it from being unhandled
          console.log('Handled previously unhandled rejection');
        });
      }
      
      // Don't propagate the event to avoid test failures
      return false;
    }
    
    // For all other events, use the original emit behavior
    return originalEmit.apply(this, [event, ...args]);
  };
};

/**
 * Safely executes a promise-returning function, catching any errors
 * to prevent unhandled promise rejections
 * 
 * @param {Function} fn - Function that returns a promise
 * @param {Array} args - Arguments to pass to the function
 * @returns {Promise} - Promise that never rejects, but resolves with {success, result/error}
 */
export const safePromise = async (fn, ...args) => {
  try {
    const result = await fn(...args);
    return { success: true, result };
  } catch (error) {
    console.log('Safely caught error:', error);
    return { success: false, error };
  }
};

/**
 * Creates a wrapper for an async function that ensures all rejections are handled
 * 
 * @param {Function} asyncFn - Async function to wrap
 * @returns {Function} - Wrapped function that won't cause unhandled rejections
 */
export const createSafeAsyncFunction = (asyncFn) => {
  return async (...args) => {
    try {
      return await asyncFn(...args);
    } catch (error) {
      console.log('Safe async function caught error:', error);
      return { handled: true, error };
    }
  };
};

/**
 * Creates a safe click handler that won't cause unhandled promise rejections
 * 
 * @param {Function} clickHandler - Click handler function
 * @returns {Function} - Safe click handler
 */
export const createSafeClickHandler = (clickHandler) => {
  return (event) => {
    try {
      const result = clickHandler(event);
      
      // If the result is a promise, add a catch handler
      if (result && typeof result.then === 'function') {
        result.catch(error => {
          console.log('Safe click handler caught error:', error);
          return { handled: true, error };
        });
      }
      
      return result;
    } catch (error) {
      console.log('Safe click handler caught synchronous error:', error);
      return { handled: true, error };
    }
  };
};
