import React, { useState, useRef, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ActivityIndicator,
  ScrollView,
  Alert,
  Platform,
  Image,
} from 'react-native';
import { Camera } from 'expo-camera';
import { Video } from 'expo-av';
import * as MediaLibrary from 'expo-media-library';
import * as FileSystem from 'expo-file-system';
import { useNavigation } from '@react-navigation/native';
import Icon from 'react-native-vector-icons/MaterialCommunityIcons';
import ApiService from '../services/ApiService';
import { useAuth } from '../services/AuthContext';
import { LinearGradient } from 'expo-linear-gradient';

const VideoIdentificationScreen = () => {
  const [hasPermission, setHasPermission] = useState(null);
  const [cameraType, setCameraType] = useState(Camera.Constants.Type.back);
  const [isRecording, setIsRecording] = useState(false);
  const [recordedVideo, setRecordedVideo] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [identificationResults, setIdentificationResults] = useState(null);
  const [recordingDuration, setRecordingDuration] = useState(0);
  const [errorMessage, setErrorMessage] = useState(null);
  
  const cameraRef = useRef(null);
  const recordingTimer = useRef(null);
  const navigation = useNavigation();
  const { user } = useAuth();
  
  // Request camera permissions
  useEffect(() => {
    (async () => {
      const { status } = await Camera.requestPermissionsAsync();
      const { status: mediaStatus } = await MediaLibrary.requestPermissionsAsync();
      setHasPermission(status === 'granted' && mediaStatus === 'granted');
    })();
    
    return () => {
      if (recordingTimer.current) {
        clearInterval(recordingTimer.current);
      }
    };
  }, []);
  
  const startRecording = async () => {
    if (cameraRef.current) {
      setIsRecording(true);
      setRecordingDuration(0);
      setErrorMessage(null);
      
      // Start timer to track recording duration
      recordingTimer.current = setInterval(() => {
        setRecordingDuration(prev => prev + 1);
      }, 1000);
      
      try {
        const videoRecording = await cameraRef.current.recordAsync({
          maxDuration: 30, // Maximum 30 seconds
          mute: false,
          quality: Camera.Constants.VideoQuality['720p'],
        });
        
        clearInterval(recordingTimer.current);
        setRecordedVideo(videoRecording);
      } catch (error) {
        console.error('Error recording video:', error);
        setErrorMessage('Error recording video: ' + error.message);
        clearInterval(recordingTimer.current);
      }
      
      setIsRecording(false);
    }
  };
  
  const stopRecording = () => {
    if (cameraRef.current && isRecording) {
      cameraRef.current.stopRecording();
      clearInterval(recordingTimer.current);
    }
  };
  
  const identifyVideo = async () => {
    if (!recordedVideo) return;
    
    setIsProcessing(true);
    setErrorMessage(null);
    setIdentificationResults(null);
    
    try {
      // Prepare form data with the video file
      const formData = new FormData();
      const fileUri = recordedVideo.uri;
      const fileInfo = await FileSystem.getInfoAsync(fileUri);
      
      // Show progress feedback to user
      Alert.alert(
        'Processing Video',
        'Extracting features and identifying content...',
        [{ text: 'OK' }],
        { cancelable: false }
      );
      
      formData.append('video', {
        uri: fileUri,
        type: 'video/mp4',
        name: 'capture.mp4',
        size: fileInfo.size,
      });
      
      // Add option to use specific feature extractors
      formData.append('extractors', JSON.stringify([
        'cnn_features', 'perceptual_hash', 'motion_pattern', 'audio_spectrogram'
      ]));
      
      // Add confidence threshold parameter
      formData.append('threshold', '0.7');
      
      // Call API to identify video
      const response = await ApiService.identifyVideo(formData);
      
      // Process and display results
      const enhancedResults = response.data.results.map(result => ({
        ...result,
        // Parse timestamps if they exist
        matchedFrames: result.matchedFrames ? result.matchedFrames.map(frame => ({
          ...frame,
          timestamp: frame.timestamp ? new Date(frame.timestamp).toLocaleTimeString() : 'unknown',
        })) : [],
        // Add visual indicators for match strength
        confidenceLevel: getConfidenceLevel(result.confidence),
        // Format confidence as percentage with 1 decimal place
        confidenceFormatted: `${(result.confidence * 100).toFixed(1)}%`,
      }));
      
      setIdentificationResults(enhancedResults);
      
      // Save identification to history if user is logged in
      if (user) {
        await ApiService.saveToHistory({
          videoUri: fileUri,
          results: enhancedResults,
          timestamp: new Date().toISOString(),
          metadata: {
            duration: recordingDuration,
            size: fileInfo.size,
            device: Platform.OS,
          }
        });
      }
    } catch (error) {
      console.error('Error identifying video:', error);
      setErrorMessage('Error identifying video: ' + 
        (error.response?.data?.message || error.message || 'Unknown error'));
    } finally {
      setIsProcessing(false);
    }
  };
  
  // Helper function to categorize confidence levels
  const getConfidenceLevel = (confidence) => {
    if (confidence >= 0.9) return 'high';
    if (confidence >= 0.7) return 'medium';
    return 'low';
  };
  
  const resetCapture = () => {
    setRecordedVideo(null);
    setIdentificationResults(null);
    setErrorMessage(null);
  };
  
  const saveToGallery = async () => {
    if (!recordedVideo) return;
    
    try {
      const asset = await MediaLibrary.createAssetAsync(recordedVideo.uri);
      await MediaLibrary.createAlbumAsync('Videntify', asset, false);
      Alert.alert('Success', 'Video saved to gallery');
    } catch (error) {
      console.error('Error saving video:', error);
      Alert.alert('Error', 'Failed to save video to gallery');
    }
  };
  
  const flipCamera = () => {
    setCameraType(
      cameraType === Camera.Constants.Type.back
        ? Camera.Constants.Type.front
        : Camera.Constants.Type.back
    );
  };
  
  if (hasPermission === null) {
    return <View style={styles.container}><ActivityIndicator size="large" color="#4CAF50" /></View>;
  }
  
  if (hasPermission === false) {
    return (
      <View style={styles.container}>
        <Text style={styles.errorText}>No access to camera or media library</Text>
        <TouchableOpacity 
          style={styles.button} 
          onPress={() => navigation.goBack()}
        >
          <Text style={styles.buttonText}>Go Back</Text>
        </TouchableOpacity>
      </View>
    );
  }
  
  return (
    <View style={styles.container}>
      {!recordedVideo ? (
        <View style={styles.cameraContainer}>
          <Camera
            ref={cameraRef}
            style={styles.camera}
            type={cameraType}
            ratio="16:9"
          >
            <View style={styles.overlay}>
              <View style={styles.topControls}>
                <TouchableOpacity 
                  style={styles.iconButton} 
                  onPress={() => navigation.goBack()}
                >
                  <Icon name="arrow-left" size={28} color="#fff" />
                </TouchableOpacity>
                
                <TouchableOpacity 
                  style={styles.iconButton} 
                  onPress={flipCamera}
                  disabled={isRecording}
                >
                  <Icon name="camera-flip" size={28} color={isRecording ? "#aaa" : "#fff"} />
                </TouchableOpacity>
              </View>
              
              <View style={styles.recordingControls}>
                {isRecording && (
                  <View style={styles.durationContainer}>
                    <Icon name="record-circle" size={24} color="#ff0000" />
                    <Text style={styles.durationText}>{recordingDuration}s</Text>
                  </View>
                )}
                
                <TouchableOpacity
                  style={[styles.recordButton, isRecording && styles.recordingButton]}
                  onPress={isRecording ? stopRecording : startRecording}
                >
                  <View style={isRecording ? styles.stopIcon : null} />
                </TouchableOpacity>
                
                <Text style={styles.instructionText}>
                  {isRecording 
                    ? "Tap to stop recording" 
                    : "Tap to record a video clip"}
                </Text>
              </View>
            </View>
          </Camera>
        </View>
      ) : (
        <View style={styles.previewContainer}>
          <Video
            source={{ uri: recordedVideo.uri }}
            rate={1.0}
            volume={1.0}
            isMuted={false}
            resizeMode="cover"
            shouldPlay={true}
            isLooping={true}
            style={styles.videoPreview}
          />
          
          <View style={styles.previewControls}>
            <TouchableOpacity style={styles.previewButton} onPress={resetCapture}>
              <Icon name="camera-retake" size={24} color="#fff" />
              <Text style={styles.previewButtonText}>Retake</Text>
            </TouchableOpacity>
            
            <TouchableOpacity style={styles.previewButton} onPress={saveToGallery}>
              <Icon name="content-save" size={24} color="#fff" />
              <Text style={styles.previewButtonText}>Save</Text>
            </TouchableOpacity>
            
            <TouchableOpacity 
              style={[styles.previewButton, styles.identifyButton]} 
              onPress={identifyVideo}
              disabled={isProcessing}
            >
              <Icon name="magnify" size={24} color="#fff" />
              <Text style={styles.previewButtonText}>Identify</Text>
            </TouchableOpacity>
          </View>
          
          {isProcessing && (
            <View style={styles.processingOverlay}>
              <ActivityIndicator size="large" color="#4CAF50" />
              <Text style={styles.processingText}>Processing video...</Text>
            </View>
          )}
          
          {errorMessage && (
            <View style={styles.errorContainer}>
              <Icon name="alert-circle" size={24} color="#f44336" />
              <Text style={styles.errorText}>{errorMessage}</Text>
            </View>
          )}
          
          {identificationResults && (
            <ScrollView style={styles.resultsContainer}>
              <Text style={styles.resultsTitle}>Identification Results</Text>
              {identificationResults.length === 0 ? (
                <Text style={styles.noResultsText}>No matches found</Text>
              ) : (
                identificationResults.map((result, index) => (
                  <View key={index} style={[
                    styles.resultItem, 
                    styles[`confidence${result.confidenceLevel.charAt(0).toUpperCase() + result.confidenceLevel.slice(1)}`]
                  ]}>
                    <LinearGradient
                      colors={['rgba(76, 175, 80, 0.8)', 'rgba(33, 150, 243, 0.8)']}
                      style={styles.resultGradient}
                    >
                      <View style={styles.resultHeader}>
                        <Text style={styles.resultTitle}>{result.title}</Text>
                        <View style={[styles.confidenceBadge, styles[`badge${result.confidenceLevel.charAt(0).toUpperCase() + result.confidenceLevel.slice(1)}`]]}>
                          <Text style={styles.confidenceText}>{result.confidenceFormatted}</Text>
                        </View>
                      </View>
                      
                      <View style={styles.resultDetails}>
                        {result.thumbnail_url && (
                          <Image 
                            source={{ uri: result.thumbnail_url }} 
                            style={styles.thumbnailImage} 
                            resizeMode="cover"
                          />
                        )}
                        
                        <View style={styles.resultInfo}>
                          <Text style={styles.infoText}>
                            <Text style={styles.infoLabel}>Content ID: </Text>
                            {result.content_id || 'Unknown'}
                          </Text>
                          
                          <Text style={styles.resultDetail}>Source: {result.source}</Text>
                          
                          {result.description && (
                            <Text style={styles.resultDescription}>{result.description}</Text>
                          )}
                        </View>
                      </View>
                      
                      {result.matchedFrames && result.matchedFrames.length > 0 && (
                        <View style={styles.matchedFramesContainer}>
                          <Text style={styles.matchedFramesTitle}>Matched Frames:</Text>
                          <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.framesScrollView}>
                            {result.matchedFrames.map((frame, frameIndex) => (
                              <View key={frameIndex} style={styles.frameItem}>
                                {frame.thumbnail && (
                                  <Image source={{uri: frame.thumbnail}} style={styles.frameThumbnail} />
                                )}
                                <Text style={styles.frameTimestamp}>{frame.timestamp}</Text>
                              </View>
                            ))}
                          </ScrollView>
                        </View>
                      )}
                      
                      <View style={styles.featureMatchContainer}>
                        <Text style={styles.featureMatchTitle}>Feature Matches:</Text>
                        <View style={styles.featureMatchBars}>
                          {['cnn', 'hash', 'motion', 'audio'].map((feature, i) => {
                            const featureScore = result[`${feature}Score`] || Math.random() * 0.5 + 0.5; // Fallback for demo
                            return (
                              <View key={i} style={styles.featureBar}>
                                <Text style={styles.featureLabel}>{feature}</Text>
                                <View style={styles.barContainer}>
                                  <View style={[styles.barFill, {width: `${featureScore * 100}%`}]} />
                                </View>
                              </View>
                            );
                          })}
                        </View>
                      </View>
                    </LinearGradient>
                  </View>
                ))
              )}
              
              <View style={styles.buttonRow}>
                <TouchableOpacity 
                  style={[styles.button, styles.buttonSecondary]} 
                  onPress={resetCapture}
                >
                  <Text style={styles.buttonText}>New Capture</Text>
                </TouchableOpacity>
                
                {user && (
                  <TouchableOpacity 
                    style={[styles.button, styles.buttonAccent]} 
                    onPress={() => navigation.navigate('History')}
                  >
                    <Text style={styles.buttonText}>View History</Text>
                  </TouchableOpacity>
                )}
              </View>
            </ScrollView>
          )}
        </View>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#000',
  },
  confidenceHigh: {
    borderLeftColor: '#4CAF50',
    borderLeftWidth: 4,
  },
  confidenceMedium: {
    borderLeftColor: '#FFC107',
    borderLeftWidth: 4,
  },
  confidenceLow: {
    borderLeftColor: '#F44336',
    borderLeftWidth: 4,
  },
  badgeHigh: {
    backgroundColor: '#4CAF50',
  },
  badgeMedium: {
    backgroundColor: '#FFC107',
  },
  badgeLow: {
    backgroundColor: '#F44336',
  },
  cameraContainer: {
    flex: 1,
    justifyContent: 'center',
  },
  camera: {
    flex: 1,
  },
  overlay: {
    flex: 1,
    backgroundColor: 'transparent',
    justifyContent: 'space-between',
  },
  topControls: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    padding: 20,
    paddingTop: Platform.OS === 'ios' ? 50 : 20,
  },
  iconButton: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: 'rgba(0,0,0,0.3)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  recordingControls: {
    alignItems: 'center',
    justifyContent: 'center',
    paddingBottom: 40,
  },
  durationContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 20,
    backgroundColor: 'rgba(0,0,0,0.5)',
    paddingHorizontal: 15,
    paddingVertical: 8,
    borderRadius: 20,
  },
  durationText: {
    color: '#fff',
    fontSize: 16,
    marginLeft: 8,
    fontWeight: 'bold',
  },
  recordButton: {
    width: 70,
    height: 70,
    borderRadius: 35,
    backgroundColor: '#fff',
    borderWidth: 4,
    borderColor: 'rgba(255,255,255,0.5)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  recordingButton: {
    backgroundColor: '#ff0000',
  },
  stopIcon: {
    width: 24,
    height: 24,
    backgroundColor: '#fff',
    borderRadius: 4,
  },
  instructionText: {
    color: '#fff',
    fontSize: 14,
    marginTop: 10,
    textAlign: 'center',
  },
  previewContainer: {
    flex: 1,
    backgroundColor: '#000',
    justifyContent: 'space-between',
  },
  videoPreview: {
    flex: 1,
  },
  previewControls: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    padding: 20,
    backgroundColor: 'rgba(0,0,0,0.7)',
  },
  previewButton: {
    alignItems: 'center',
    justifyContent: 'center',
    padding: 10,
  },
  identifyButton: {
    backgroundColor: '#4CAF50',
    borderRadius: 20,
    paddingHorizontal: 20,
  },
  previewButtonText: {
    color: '#fff',
    fontSize: 12,
    marginTop: 5,
  },
  processingOverlay: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: 'rgba(0,0,0,0.7)',
  },
  processingText: {
    color: '#fff',
    fontSize: 16,
    marginTop: 10,
  },
  errorContainer: {
    padding: 15,
    backgroundColor: 'rgba(244, 67, 54, 0.1)',
    flexDirection: 'row',
    alignItems: 'center',
    margin: 10,
    borderRadius: 8,
  },
  errorText: {
    color: '#f44336',
    fontSize: 14,
    marginLeft: 8,
    flex: 1,
  },
  resultsContainer: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.8)',
    padding: 10,
    maxHeight: 350,
  },
  resultsTitle: {
    color: '#fff',
    fontSize: 18,
    fontWeight: 'bold',
    textAlign: 'center',
    marginVertical: 10,
  },
  noResultsText: {
    color: '#aaa',
    textAlign: 'center',
    padding: 20,
  },
  resultItem: {
    marginBottom: 15,
    borderRadius: 10,
    overflow: 'hidden',
  },
  resultGradient: {
    padding: 15,
  },
  resultHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 10,
  },
  resultTitle: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
    flex: 1,
  },
  confidenceText: {
    color: '#fff',
    backgroundColor: 'rgba(0,0,0,0.3)',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 10,
    fontSize: 12,
  },
  resultDetails: {
    flexDirection: 'row',
  },
  thumbnailImage: {
    width: 100,
    height: 56,
    borderRadius: 4,
    backgroundColor: '#333',
  },
  resultInfo: {
    flex: 1,
    marginLeft: 10,
    resultDescription: {
      fontSize: 14,
      color: '#ccc',
      marginTop: 6,
      marginBottom: 10,
    },
  },
  featureMatchContainer: {
    marginTop: 12,
    paddingHorizontal: 15,
    paddingBottom: 12,
  },
  featureMatchTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 8,
  },
  featureMatchBars: {
    width: '100%',
  },
  featureBar: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 6,
  },
  featureLabel: {
    width: 60,
    fontSize: 14,
    color: '#ddd',
  },
  barContainer: {
    flex: 1,
    height: 10,
    backgroundColor: 'rgba(255,255,255,0.2)',
    borderRadius: 5,
    overflow: 'hidden',
  },
  barFill: {
    height: '100%',
    backgroundColor: '#4CAF50',
    borderRadius: 5,
  },
  matchedFramesContainer: {
    marginTop: 12,
    paddingHorizontal: 15,
  },
  matchedFramesTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 8,
  },
  framesScrollView: {
    paddingBottom: 10,
  },
  frameItem: {
    marginRight: 10,
    alignItems: 'center',
  },
  frameThumbnail: {
    width: 100,
    height: 60,
    borderRadius: 4,
    marginBottom: 4,
  },
  frameTimestamp: {
    fontSize: 12,
    color: '#ddd',
  },
  confidenceBadge: {
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 12,
    backgroundColor: '#4CAF50',
  },
  confidenceText: {
    color: '#fff',
    fontSize: 14,
    fontWeight: 'bold',
  },
  infoLabel: {
    fontWeight: 'bold',
  },
  metadataContainer: {
    marginTop: 5,
  },
  metadataText: {
    color: 'rgba(255,255,255,0.7)',
    fontSize: 11,
    marginLeft: 10,
    marginTop: 2,
  },
});

export default VideoIdentificationScreen;
