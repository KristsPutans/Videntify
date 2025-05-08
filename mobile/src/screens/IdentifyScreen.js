/**
 * Identify Screen
 * Allows user to record video or upload from gallery for identification
 */

import React, { useState, useRef, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Image,
  Alert,
  ActivityIndicator,
  Platform,
  Dimensions,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import * as ImagePicker from 'expo-image-picker';
import { Camera } from 'expo-camera';
import { Video } from 'expo-av';
import { Ionicons } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';
import { identifyVideo } from '../services/ApiService';

const { width, height } = Dimensions.get('window');

const IdentifyScreen = ({ navigation }) => {
  const [hasPermission, setHasPermission] = useState(null);
  const [cameraType, setCameraType] = useState(Camera.Constants.Type.back);
  const [isRecording, setIsRecording] = useState(false);
  const [videoSource, setVideoSource] = useState(null);
  const [isIdentifying, setIsIdentifying] = useState(false);
  const [recordingTime, setRecordingTime] = useState(0);
  const [timerInterval, setTimerInterval] = useState(null);
  const cameraRef = useRef(null);
  const videoRef = useRef(null);

  const MAX_RECORDING_TIME = 15; // Maximum recording time in seconds

  // Request camera permissions on component mount
  useEffect(() => {
    (async () => {
      const { status } = await Camera.requestCameraPermissionsAsync();
      const { status: audioStatus } = await Camera.requestMicrophonePermissionsAsync();
      setHasPermission(status === 'granted' && audioStatus === 'granted');
    })();
    
    return () => {
      // Clean up timer when component unmounts
      if (timerInterval) {
        clearInterval(timerInterval);
      }
    };
  }, []);

  const startRecording = async () => {
    if (cameraRef.current) {
      try {
        setIsRecording(true);
        // Start timer
        setRecordingTime(0);
        const interval = setInterval(() => {
          setRecordingTime(prev => {
            if (prev >= MAX_RECORDING_TIME) {
              stopRecording();
              return MAX_RECORDING_TIME;
            }
            return prev + 1;
          });
        }, 1000);
        setTimerInterval(interval);
        
        const video = await cameraRef.current.recordAsync({
          maxDuration: MAX_RECORDING_TIME,
          quality: Camera.Constants.VideoQuality['720p'],
        });
        setVideoSource(video.uri);
      } catch (error) {
        console.error('Error recording video:', error);
        Alert.alert('Error', 'Failed to record video. Please try again.');
        setIsRecording(false);
      }
    }
  };

  const stopRecording = async () => {
    if (cameraRef.current && isRecording) {
      clearInterval(timerInterval);
      setTimerInterval(null);
      cameraRef.current.stopRecording();
      setIsRecording(false);
    }
  };

  const toggleCameraType = () => {
    setCameraType(
      cameraType === Camera.Constants.Type.back
        ? Camera.Constants.Type.front
        : Camera.Constants.Type.back
    );
  };

  const pickVideoFromGallery = async () => {
    try {
      const result = await ImagePicker.launchImageLibraryAsync({
        mediaTypes: ImagePicker.MediaTypeOptions.Videos,
        allowsEditing: true,
        quality: 1,
        videoMaxDuration: 30,
      });

      if (!result.canceled && result.assets && result.assets.length > 0) {
        setVideoSource(result.assets[0].uri);
      }
    } catch (error) {
      console.error('Error picking video:', error);
      Alert.alert('Error', 'Failed to pick video from gallery. Please try again.');
    }
  };

  const handleIdentify = async () => {
    if (!videoSource) {
      Alert.alert('Error', 'Please record or upload a video clip first.');
      return;
    }

    setIsIdentifying(true);

    try {
      const result = await identifyVideo(videoSource);
      setIsIdentifying(false);
      navigation.navigate('Result', { result });
    } catch (error) {
      console.error('Error identifying video:', error);
      setIsIdentifying(false);
      Alert.alert('Error', 'Failed to identify video. Please try again.');
    }
  };

  const resetVideo = () => {
    setVideoSource(null);
    setRecordingTime(0);
  };

  if (hasPermission === null) {
    return (
      <SafeAreaView style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#6a11cb" />
        <Text style={styles.loadingText}>Requesting camera permission...</Text>
      </SafeAreaView>
    );
  }

  if (hasPermission === false) {
    return (
      <SafeAreaView style={styles.permissionContainer}>
        <Ionicons name="videocam-off" size={64} color="#999" style={styles.permissionIcon} />
        <Text style={styles.permissionTitle}>Camera Access Required</Text>
        <Text style={styles.permissionText}>
          VidID needs access to your camera to record video clips for identification.
          Please enable camera access in your device settings.
        </Text>
        <TouchableOpacity 
          style={styles.permissionButton}
          onPress={() => navigation.goBack()}
        >
          <Text style={styles.permissionButtonText}>Go Back</Text>
        </TouchableOpacity>
      </SafeAreaView>
    );
  }

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins < 10 ? '0' : ''}${mins}:${secs < 10 ? '0' : ''}${secs}`;
  };

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <TouchableOpacity 
          style={styles.backButton}
          onPress={() => navigation.goBack()}
        >
          <Ionicons name="arrow-back" size={24} color="#333" />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Video Identification</Text>
        <View style={styles.placeholderRight} />
      </View>
      
      <View style={styles.mainContent}>
        {videoSource ? (
          <View style={styles.videoPreviewContainer}>
            <Video
              ref={videoRef}
              source={{ uri: videoSource }}
              style={styles.videoPreview}
              useNativeControls
              resizeMode="contain"
              isLooping
              shouldPlay
            />
            <View style={styles.videoOverlayControls}>
              <TouchableOpacity 
                style={styles.resetButton}
                onPress={resetVideo}
              >
                <Ionicons name="refresh" size={22} color="#fff" />
                <Text style={styles.resetButtonText}>Reset</Text>
              </TouchableOpacity>
            </View>
          </View>
        ) : (
          <Camera
            ref={cameraRef}
            style={styles.camera}
            type={cameraType}
            flashMode={Camera.Constants.FlashMode.auto}
            ratio="16:9"
          >
            <View style={styles.cameraOverlay}>
              {isRecording && (
                <View style={styles.recordingIndicator}>
                  <View style={styles.recordingDot} />
                  <Text style={styles.recordingText}>REC</Text>
                  <Text style={styles.recordingTimer}>{formatTime(recordingTime)}</Text>
                </View>
              )}
              <View style={styles.cameraControls}>
                <TouchableOpacity 
                  style={styles.cameraControlButton}
                  onPress={toggleCameraType}
                  disabled={isRecording}
                >
                  <Ionicons 
                    name="camera-reverse" 
                    size={26} 
                    color={isRecording ? '#999' : '#fff'} 
                  />
                </TouchableOpacity>
                
                <TouchableOpacity 
                  style={[styles.recordButton, isRecording && styles.stopButton]}
                  onPress={isRecording ? stopRecording : startRecording}
                >
                  {isRecording ? (
                    <View style={styles.stopIcon} />
                  ) : (
                    <View style={styles.recordIcon} />
                  )}
                </TouchableOpacity>
                
                <TouchableOpacity 
                  style={styles.cameraControlButton}
                  onPress={pickVideoFromGallery}
                  disabled={isRecording}
                >
                  <Ionicons 
                    name="images" 
                    size={26} 
                    color={isRecording ? '#999' : '#fff'} 
                  />
                </TouchableOpacity>
              </View>
            </View>
          </Camera>
        )}
      </View>
      
      <View style={styles.bottomSection}>
        {videoSource ? (
          <View style={styles.identifySection}>
            <Text style={styles.identifyTitle}>Ready to identify your clip?</Text>
            <Text style={styles.identifyDescription}>
              Our AI will analyze the video and find the exact match in our database.
            </Text>
            <TouchableOpacity 
              style={styles.identifyButton}
              onPress={handleIdentify}
              disabled={isIdentifying}
            >
              {isIdentifying ? (
                <ActivityIndicator size="small" color="#fff" />
              ) : (
                <>
                  <Ionicons name="search" size={20} color="#fff" style={styles.identifyIcon} />
                  <Text style={styles.identifyButtonText}>Identify Now</Text>
                </>
              )}
            </TouchableOpacity>
          </View>
        ) : (
          <View style={styles.instructionSection}>
            <Text style={styles.instructionTitle}>How to identify video content</Text>
            <View style={styles.instructionItem}>
              <View style={styles.instructionIconContainer}>
                <Ionicons name="videocam" size={20} color="#6a11cb" />
              </View>
              <Text style={styles.instructionText}>Record a clip (5-15 seconds)</Text>
            </View>
            <View style={styles.instructionItem}>
              <View style={styles.instructionIconContainer}>
                <Ionicons name="images" size={20} color="#6a11cb" />
              </View>
              <Text style={styles.instructionText}>Or upload from your gallery</Text>
            </View>
            <View style={styles.instructionItem}>
              <View style={styles.instructionIconContainer}>
                <Ionicons name="search" size={20} color="#6a11cb" />
              </View>
              <Text style={styles.instructionText}>Tap identify to find the exact match</Text>
            </View>
          </View>
        )}
      </View>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f8f8f8',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#f8f8f8',
  },
  loadingText: {
    marginTop: 10,
    color: '#666',
    fontSize: 16,
  },
  permissionContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#f8f8f8',
    padding: 20,
  },
  permissionIcon: {
    marginBottom: 20,
  },
  permissionTitle: {
    fontSize: 22,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 10,
    textAlign: 'center',
  },
  permissionText: {
    fontSize: 16,
    color: '#666',
    textAlign: 'center',
    marginBottom: 25,
    lineHeight: 24,
  },
  permissionButton: {
    backgroundColor: '#6a11cb',
    paddingVertical: 12,
    paddingHorizontal: 30,
    borderRadius: 25,
  },
  permissionButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    backgroundColor: '#fff',
    paddingHorizontal: 15,
    paddingVertical: 10,
    borderBottomWidth: 1,
    borderBottomColor: '#eeeeee',
  },
  backButton: {
    padding: 5,
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
  },
  placeholderRight: {
    width: 34, // Same width as back button for alignment
  },
  mainContent: {
    flex: 1,
    backgroundColor: '#000',
  },
  camera: {
    flex: 1,
    justifyContent: 'space-between',
  },
  cameraOverlay: {
    flex: 1,
    backgroundColor: 'transparent',
    justifyContent: 'space-between',
  },
  recordingIndicator: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'rgba(0,0,0,0.6)',
    paddingHorizontal: 15,
    paddingVertical: 8,
    borderRadius: 20,
    alignSelf: 'center',
    marginTop: 20,
  },
  recordingDot: {
    width: 12,
    height: 12,
    borderRadius: 6,
    backgroundColor: '#f00',
    marginRight: 8,
  },
  recordingText: {
    color: '#fff',
    fontWeight: 'bold',
    fontSize: 14,
    marginRight: 8,
  },
  recordingTimer: {
    color: '#fff',
    fontSize: 14,
  },
  cameraControls: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    alignItems: 'center',
    paddingVertical: 20,
    paddingHorizontal: 30,
  },
  cameraControlButton: {
    width: 50,
    height: 50,
    borderRadius: 25,
    backgroundColor: 'rgba(0,0,0,0.4)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  recordButton: {
    width: 70,
    height: 70,
    borderRadius: 35,
    backgroundColor: '#fff',
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 4,
    borderColor: 'rgba(255,255,255,0.4)',
  },
  recordIcon: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: '#f00',
  },
  stopButton: {
    backgroundColor: '#fff',
  },
  stopIcon: {
    width: 30,
    height: 30,
    backgroundColor: '#f00',
    borderRadius: 3,
  },
  videoPreviewContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#000',
  },
  videoPreview: {
    width: '100%',
    height: '100%',
  },
  videoOverlayControls: {
    position: 'absolute',
    top: 20,
    right: 20,
  },
  resetButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'rgba(0,0,0,0.6)',
    paddingHorizontal: 15,
    paddingVertical: 8,
    borderRadius: 20,
  },
  resetButtonText: {
    color: '#fff',
    fontSize: 14,
    marginLeft: 5,
  },
  bottomSection: {
    backgroundColor: '#fff',
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    paddingHorizontal: 20,
    paddingVertical: 25,
    marginTop: -20,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: -3 },
    shadowOpacity: 0.1,
    shadowRadius: 5,
    elevation: 5,
  },
  instructionSection: {
    paddingHorizontal: 10,
  },
  instructionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 15,
    textAlign: 'center',
  },
  instructionItem: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 15,
  },
  instructionIconContainer: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: 'rgba(106, 17, 203, 0.1)',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  instructionText: {
    fontSize: 16,
    color: '#555',
  },
  identifySection: {
    alignItems: 'center',
  },
  identifyTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 8,
    textAlign: 'center',
  },
  identifyDescription: {
    fontSize: 14,
    color: '#666',
    textAlign: 'center',
    marginBottom: 20,
    lineHeight: 20,
  },
  identifyButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#6a11cb',
    paddingVertical: 12,
    paddingHorizontal: 25,
    borderRadius: 25,
    justifyContent: 'center',
    width: '80%',
  },
  identifyIcon: {
    marginRight: 8,
  },
  identifyButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
  },
});

export default IdentifyScreen;
