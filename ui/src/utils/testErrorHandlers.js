/**
 * Test error handling utilities
 * 
 * This module provides utilities for handling promise rejections and errors in tests
 * to prevent unhandled promise rejection warnings and test failures.
 */

/**
 * Wraps an async function to ensure any rejections are caught and handled
 * @param {Function} asyncFn - The async function to wrap
 * @returns {Function} A wrapped version of the original function that won't cause unhandled rejections
 */
export const withErrorHandling = (asyncFn) => {
  return async (...args) => {
    try {
      return await asyncFn(...args);
    } catch (error) {
      console.log('Caught error in withErrorHandling:', error.message);
      // Return a standardized error object that tests can check
      return { error, success: false };
    }
  };
};

/**
 * Executes a promise or async operation safely and returns its result
 * or error without throwing or causing unhandled rejections
 * 
 * @param {Promise} promise - The promise to execute safely
 * @returns {Promise} A promise that always resolves with either {data, success: true} or {error, success: false}
 */
export const safePromise = async (promise) => {
  try {
    const data = await promise;
    return { data, success: true };
  } catch (error) {
    console.log('Caught error in safePromise:', error.message);
    return { error, success: false };
  }
};

/**
 * Creates a safety wrapper for click event handlers that might trigger async operations
 * @param {Function} clickHandler - The click handler function to wrap
 * @returns {Function} A wrapped version that won't cause unhandled rejections
 */
export const createSafeClickHandler = (clickHandler) => {
  return (event) => {
    try {
      const result = clickHandler(event);
      
      // If the result is a promise, ensure it's handled
      if (result && typeof result.then === 'function') {
        result.catch(error => {
          console.log('Caught promise error in click handler:', error.message);
        });
      }
    } catch (error) {
      console.log('Caught synchronous error in click handler:', error.message);
    }
  };
};
