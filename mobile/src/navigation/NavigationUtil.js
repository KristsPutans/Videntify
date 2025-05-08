/**
 * Navigation Utility
 * Helper functions for handling navigation throughout the app
 */

import { CommonActions } from '@react-navigation/native';
import { Alert, Linking } from 'react-native';

/**
 * Navigate to a screen and reset the navigation stack
 * Useful for flows like authentication where you don't want the user to go back
 * 
 * @param {Object} navigation - Navigation object from React Navigation
 * @param {string} routeName - Route name to navigate to
 * @param {Object} params - Route parameters
 */
export const resetStackAndNavigate = (navigation, routeName, params = {}) => {
  navigation.dispatch(
    CommonActions.reset({
      index: 0,
      routes: [{ name: routeName, params }],
    })
  );
};

/**
 * Navigate to the authentication flow
 * Used when a user needs to be logged in to access certain features
 * 
 * @param {Object} navigation - Navigation object from React Navigation
 * @param {Object} options - Navigation options
 */
export const navigateToAuth = (navigation, options = {}) => {
  const { showMessage = true, returnTo = null } = options;
  
  if (showMessage) {
    Alert.alert(
      'Sign In Required',
      'Please sign in to access this feature',
      [
        { text: 'Cancel', style: 'cancel' },
        { 
          text: 'Sign In', 
          onPress: () => resetStackAndNavigate(navigation, 'Auth', { returnTo }) 
        },
      ]
    );
  } else {
    resetStackAndNavigate(navigation, 'Auth', { returnTo });
  }
};

/**
 * Open external URL with validation
 * Handles deep links and external URLs safely
 * 
 * @param {string} url - URL to open
 * @param {Object} options - Options for opening URL
 */
export const openExternalUrl = async (url, options = {}) => {
  const { fallbackUrl, showError = true } = options;
  
  try {
    const supported = await Linking.canOpenURL(url);
    
    if (supported) {
      await Linking.openURL(url);
    } else if (fallbackUrl) {
      await Linking.openURL(fallbackUrl);
    } else if (showError) {
      Alert.alert(
        'Cannot Open URL',
        `The app cannot open the URL: ${url}`,
        [{ text: 'OK' }]
      );
    }
  } catch (error) {
    console.error('Error opening URL:', error);
    
    if (showError) {
      Alert.alert(
        'Error Opening Link',
        'There was an error opening the link. Please try again later.',
        [{ text: 'OK' }]
      );
    }
  }
};

/**
 * Share content using the native share dialog
 * 
 * @param {Object} navigation - Navigation object from React Navigation
 * @param {Object} content - Content to share (result object with title, image, etc.)
 */
export const shareIdentificationResult = (navigation, content) => {
  navigation.navigate('ShareModal', { content });
};

/**
 * Navigate to result details screen
 * 
 * @param {Object} navigation - Navigation object from React Navigation
 * @param {Object} result - Result object containing identification details
 */
export const viewResultDetails = (navigation, result) => {
  navigation.navigate('Result', { result });
};

/**
 * Open a specific settings screen
 * 
 * @param {Object} navigation - Navigation object from React Navigation
 * @param {string} settingScreen - The settings screen to navigate to
 * @param {Object} params - Navigation parameters
 */
export const openSettings = (navigation, settingScreen, params = {}) => {
  navigation.navigate('Settings', {
    screen: settingScreen,
    params,
  });
};

export default {
  resetStackAndNavigate,
  navigateToAuth,
  openExternalUrl,
  shareIdentificationResult,
  viewResultDetails,
  openSettings,
};
