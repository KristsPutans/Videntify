/**
 * Authentication Context Provider
 */

import React, { createContext, useReducer, useEffect } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';

// Initial state
const initialState = {
  isLoading: true,
  isAuthenticated: false,
  token: null,
  user: null,
  error: null,
};

// Create context
export const AuthContext = createContext(initialState);

// Authentication reducer
const authReducer = (state, action) => {
  switch (action.type) {
    case 'RESTORE_TOKEN':
      return {
        ...state,
        token: action.token,
        user: action.user,
        isAuthenticated: action.token !== null,
        isLoading: false,
      };
    case 'SIGN_IN':
      return {
        ...state,
        isAuthenticated: true,
        token: action.token,
        user: action.user,
        error: null,
      };
    case 'SIGN_OUT':
      return {
        ...state,
        isAuthenticated: false,
        token: null,
        user: null,
      };
    case 'AUTH_ERROR':
      return {
        ...state,
        error: action.error,
      };
    default:
      return state;
  }
};

// Authentication provider component
export const AuthProvider = ({ children }) => {
  const [state, dispatch] = useReducer(authReducer, initialState);

  // Actions
  const authActions = {
    restoreToken: async () => {
      let token = null;
      let user = null;

      try {
        token = await AsyncStorage.getItem('token');
        const userJson = await AsyncStorage.getItem('user');
        if (userJson) {
          user = JSON.parse(userJson);
        }
      } catch (e) {
        console.error('Failed to load authentication tokens', e);
      }

      dispatch({ type: 'RESTORE_TOKEN', token, user });
    },

    signIn: async (credentials) => {
      try {
        // This would normally be an API call to authenticate
        // For demo purposes, we'll simulate it
        const { email, password } = credentials;
        
        // Simple validation
        if (!email || !password) {
          throw new Error('Email and password are required');
        }
        
        const mockResponse = {
          token: 'mock-auth-token',
          user: {
            id: 'user123',
            name: email.split('@')[0], // Extract name from email for demo
            email: email,
            profileImage: null,
          },
        };

        // Save authentication data
        await AsyncStorage.setItem('token', mockResponse.token);
        await AsyncStorage.setItem('user', JSON.stringify(mockResponse.user));

        dispatch({
          type: 'SIGN_IN',
          token: mockResponse.token,
          user: mockResponse.user,
        });

        return { success: true };
      } catch (error) {
        dispatch({
          type: 'AUTH_ERROR',
          error: 'Invalid username or password',
        });
        return { success: false, message: error.message || 'Authentication failed' };
      }
    },

    signOut: async () => {
      try {
        // Remove authentication data
        await AsyncStorage.removeItem('token');
        await AsyncStorage.removeItem('user');
        dispatch({ type: 'SIGN_OUT' });
      } catch (error) {
        console.error('Failed to sign out', error);
      }
    },

    signUp: async (userData) => {
      try {
        // This would normally be an API call to register a new user
        // For demo purposes, we'll simulate it
        const { name, email, password } = userData;
        
        // Simple validation
        if (!name || !email || !password) {
          throw new Error('Name, email, and password are required');
        }
        
        const mockResponse = {
          token: 'mock-auth-token',
          user: {
            id: 'user123',
            name: name,
            email: email,
            profileImage: null,
          },
        };

        // Save authentication data
        await AsyncStorage.setItem('token', mockResponse.token);
        await AsyncStorage.setItem('user', JSON.stringify(mockResponse.user));

        dispatch({
          type: 'SIGN_IN',
          token: mockResponse.token,
          user: mockResponse.user,
        });

        return { success: true };
      } catch (error) {
        dispatch({
          type: 'AUTH_ERROR',
          error: 'Registration failed',
        });
        return { success: false, message: error.message || 'Registration failed' };
      }
    },
    
    forgotPassword: async (email) => {
      try {
        // This would normally be an API call to trigger password reset
        // For demo purposes, we'll simulate it
        
        // Simple validation
        if (!email) {
          throw new Error('Email is required');
        }
        
        // Simulate API call delay
        await new Promise(resolve => setTimeout(resolve, 1000));
        
        return { success: true };
      } catch (error) {
        return { success: false, message: error.message || 'Failed to send password reset link' };
      }
    },
    
    updateUserProfile: async (userData) => {
      try {
        // Get current user data
        const userJson = await AsyncStorage.getItem('user');
        if (!userJson) {
          throw new Error('User not found');
        }
        
        const currentUser = JSON.parse(userJson);
        
        // Update user data with new values
        const updatedUser = { ...currentUser, ...userData };
        
        // Save updated user data
        await AsyncStorage.setItem('user', JSON.stringify(updatedUser));
        
        // Update state
        dispatch({
          type: 'SIGN_IN',
          token: state.token, // Keep the same token
          user: updatedUser,
        });
        
        return { success: true };
      } catch (error) {
        return { success: false, message: error.message || 'Failed to update profile' };
      }
    },
    
    changePassword: async (currentPassword, newPassword) => {
      try {
        // This would normally be an API call to change password
        // For demo purposes, we'll simulate it and just check if currentPassword is provided
        
        // Simple validation
        if (!currentPassword || !newPassword) {
          throw new Error('Current password and new password are required');
        }
        
        // Simulate API call delay
        await new Promise(resolve => setTimeout(resolve, 1000));
        
        return { success: true };
      } catch (error) {
        return { success: false, message: error.message || 'Failed to change password' };
      }
    },
  };

  // Effect to restore token when app loads
  useEffect(() => {
    authActions.restoreToken();
  }, []);

  return (
    <AuthContext.Provider value={{ state, ...authActions }}>
      {children}
    </AuthContext.Provider>
  );
};
