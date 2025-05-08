/**
 * Video Service
 * Handles video recording, uploading, and processing
 */

import * as FileSystem from 'expo-file-system';
import * as MediaLibrary from 'expo-media-library';
import Constants from 'expo-constants';
import { Platform } from 'react-native';

// Directory for storing temporary videos
const VIDEO_DIRECTORY = `${FileSystem.cacheDirectory}videos/`;

/**
 * Initialize the video directory
 */
const initializeVideoDirectory = async () => {
  const directoryInfo = await FileSystem.getInfoAsync(VIDEO_DIRECTORY);
  if (!directoryInfo.exists) {
    await FileSystem.makeDirectoryAsync(VIDEO_DIRECTORY, { intermediates: true });
  }
};

/**
 * Save a video file to the app's cache directory
 * @param {string} videoUri - URI of the video to save
 * @returns {Promise<string>} - New URI of the saved video
 */
export const saveVideoToCache = async (videoUri) => {
  try {
    await initializeVideoDirectory();
    
    // Generate unique filename with timestamp
    const filename = `vidid_${Date.now()}.mp4`;
    const newUri = `${VIDEO_DIRECTORY}${filename}`;
    
    // Copy video to cache directory
    await FileSystem.copyAsync({
      from: videoUri,
      to: newUri,
    });
    
    return newUri;
  } catch (error) {
    console.error('Error saving video to cache:', error);
    throw error;
  }
};

/**
 * Save a video to the device's media library
 * @param {string} videoUri - URI of the video to save
 * @returns {Promise<string>} - Asset ID of the saved video
 */
export const saveVideoToGallery = async (videoUri) => {
  try {
    // Request permissions
    const { status } = await MediaLibrary.requestPermissionsAsync();
    if (status !== 'granted') {
      throw new Error('Media library permission denied');
    }
    
    // Save video to media library
    const asset = await MediaLibrary.createAssetAsync(videoUri);
    
    // Create album and add asset to it
    const album = await MediaLibrary.getAlbumAsync('VidID');
    if (album === null) {
      await MediaLibrary.createAlbumAsync('VidID', asset, false);
    } else {
      await MediaLibrary.addAssetsToAlbumAsync([asset], album, false);
    }
    
    return asset.id;
  } catch (error) {
    console.error('Error saving video to gallery:', error);
    throw error;
  }
};

/**
 * Get video metadata
 * @param {string} videoUri - URI of the video
 * @returns {Promise<Object>} - Video metadata
 */
export const getVideoMetadata = async (videoUri) => {
  try {
    // For demo purposes, just return mock metadata
    // In a real app, this would use a video processing library
    return {
      duration: 10.5, // seconds
      size: 15728640, // bytes (15MB)
      width: 1920,
      height: 1080,
      codec: 'h264',
      frameRate: 30,
    };
  } catch (error) {
    console.error('Error getting video metadata:', error);
    throw error;
  }
};

/**
 * Extract frames from video at specified intervals
 * @param {string} videoUri - URI of the video
 * @param {number} count - Number of frames to extract
 * @returns {Promise<Array<string>>} - Array of frame image URIs
 */
export const extractVideoFrames = async (videoUri, count = 3) => {
  try {
    // For demo purposes, just return mock frame URLs
    // In a real app, this would use a video processing library
    return [
      'https://via.placeholder.com/300x169?text=Frame+1',
      'https://via.placeholder.com/300x169?text=Frame+2',
      'https://via.placeholder.com/300x169?text=Frame+3',
    ];
  } catch (error) {
    console.error('Error extracting video frames:', error);
    throw error;
  }
};

/**
 * Generate video thumbnail
 * @param {string} videoUri - URI of the video
 * @returns {Promise<string>} - Thumbnail image URI
 */
export const generateVideoThumbnail = async (videoUri) => {
  try {
    // For demo purposes, just return a mock thumbnail URL
    // In a real app, this would use a video processing library
    return 'https://via.placeholder.com/300x169?text=Thumbnail';
  } catch (error) {
    console.error('Error generating video thumbnail:', error);
    throw error;
  }
};

/**
 * Clean up temporary videos
 * @returns {Promise<void>}
 */
export const cleanupTemporaryVideos = async () => {
  try {
    const directoryInfo = await FileSystem.getInfoAsync(VIDEO_DIRECTORY);
    if (directoryInfo.exists) {
      await FileSystem.deleteAsync(VIDEO_DIRECTORY);
      await FileSystem.makeDirectoryAsync(VIDEO_DIRECTORY, { intermediates: true });
    }
  } catch (error) {
    console.error('Error cleaning up temporary videos:', error);
  }
};

export default {
  saveVideoToCache,
  saveVideoToGallery,
  getVideoMetadata,
  extractVideoFrames,
  generateVideoThumbnail,
  cleanupTemporaryVideos,
};
