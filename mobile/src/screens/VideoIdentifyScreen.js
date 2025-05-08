/**
 * Video Identification Screen
 * This is the main screen where users can capture video for identification
 */

import React, { useState, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ActivityIndicator,
  Alert,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { RNCamera } from 'react-native-camera';
import Icon from 'react-native-vector-icons/MaterialIcons';

import { identifyVideo } from '../services/ApiService';

const VideoIdentifyScreen = ({ navigation }) => {
  const [isRecording, setIsRecording] = useState(false);
  const [recordingTime, setRecordingTime] = useState(0);
  const [isProcessing, setIsProcessing] = useState(false);
  const cameraRef = useRef(null);
  const timerRef = useRef(null);

  // Start recording video
  const startRecording = async () => {
    if (cameraRef.current) {
      try {
        setIsRecording(true);
        setRecordingTime(0);
        
        // Start timer
        timerRef.current = setInterval(() => {
          setRecordingTime((prevTime) => {
            // Stop recording after 10 seconds
            if (prevTime >= 10) {
              stopRecording();
              return 10;
            }
            return prevTime + 1;
          });
        }, 1000);

        // Start recording
        const options = { 
          quality: 0.5, 
          maxDuration: 10,
          maxFileSize: 10 * 1024 * 1024,
          mute: false,
        };
        const data = await cameraRef.current.recordAsync(options);
        processVideo(data.uri);
      } catch (error) {
        console.error('Error starting recording:', error);
        setIsRecording(false);
        clearInterval(timerRef.current);
        Alert.alert('Error', 'Failed to start recording. Please try again.');
      }
    }
  };

  // Stop recording video
  const stopRecording = async () => {
    if (cameraRef.current && isRecording) {
      clearInterval(timerRef.current);
      cameraRef.current.stopRecording();
      setIsRecording(false);
    }
  };

  // Process the recorded video for identification
  const processVideo = async (videoUri) => {
    try {
      setIsProcessing(true);
      const result = await identifyVideo(videoUri);
      setIsProcessing(false);
      
      if (result && result.matches && result.matches.length > 0) {
        // Navigate to results screen with matches data
        navigation.navigate('Result', { result });
      } else {
        Alert.alert(
          'No Matches Found',
          'We couldn\'t identify this video clip. Try recording a different scene.',
          [{ text: 'OK' }]
        );
      }
    } catch (error) {
      console.error('Error identifying video:', error);
      setIsProcessing(false);
      Alert.alert(
        'Identification Failed',
        'There was a problem identifying your video. Please try again.',
        [{ text: 'OK' }]
      );
    }
  };

  return (
    <SafeAreaView style={styles.container}>
      {/* Camera preview */}
      <RNCamera
        ref={cameraRef}
        style={styles.preview}
        type={RNCamera.Constants.Type.back}
        flashMode={RNCamera.Constants.FlashMode.off}
        captureAudio={true}
        androidCameraPermissionOptions={{
          title: 'Permission to use camera',
          message: 'We need your permission to use your camera',
          buttonPositive: 'OK',
          buttonNegative: 'Cancel',
        }}
        androidRecordAudioPermissionOptions={{
          title: 'Permission to use audio recording',
          message: 'We need your permission to use your audio',
          buttonPositive: 'OK',
          buttonNegative: 'Cancel',
        }}
      >
        {/* Recording timer */}
        {isRecording && (
          <View style={styles.timerContainer}>
            <View style={styles.timerBadge}>
              <Icon name="fiber-manual-record" size={12} color="#FF0000" />
              <Text style={styles.timerText}>{recordingTime}s</Text>
            </View>
          </View>
        )}

        {/* Camera controls */}
        <View style={styles.controlsContainer}>
          {isProcessing ? (
            <View style={styles.processingContainer}>
              <ActivityIndicator size="large" color="#FFFFFF" />
              <Text style={styles.processingText}>Identifying video...</Text>
            </View>
          ) : (
            <TouchableOpacity
              style={[styles.captureButton, isRecording && styles.stopButton]}
              onPress={isRecording ? stopRecording : startRecording}
            >
              <Icon 
                name={isRecording ? "stop" : "videocam"} 
                size={30} 
                color="#FFFFFF" 
              />
            </TouchableOpacity>
          )}
        </View>

        {/* Instructions */}
        <View style={styles.instructionsContainer}>
          <Text style={styles.instructionsText}>
            {isRecording
              ? 'Recording... Tap to stop'
              : 'Point camera at video content and tap to identify'}
          </Text>
        </View>
      </RNCamera>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#000000',
  },
  preview: {
    flex: 1,
    justifyContent: 'flex-end',
    alignItems: 'center',
  },
  timerContainer: {
    position: 'absolute',
    top: 30,
    left: 0,
    right: 0,
    alignItems: 'center',
  },
  timerBadge: {
    backgroundColor: 'rgba(0, 0, 0, 0.6)',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 20,
    flexDirection: 'row',
    alignItems: 'center',
  },
  timerText: {
    color: '#FFFFFF',
    fontSize: 14,
    fontWeight: 'bold',
    marginLeft: 5,
  },
  controlsContainer: {
    flex: 0,
    flexDirection: 'row',
    justifyContent: 'center',
    marginBottom: 40,
  },
  captureButton: {
    backgroundColor: '#4C6EF5',
    borderRadius: 50,
    padding: 20,
    alignItems: 'center',
    justifyContent: 'center',
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 2,
    },
    shadowOpacity: 0.25,
    shadowRadius: 3.84,
    elevation: 5,
  },
  stopButton: {
    backgroundColor: '#dc3545',
  },
  processingContainer: {
    backgroundColor: 'rgba(0, 0, 0, 0.6)',
    borderRadius: 10,
    padding: 20,
    alignItems: 'center',
  },
  processingText: {
    color: '#FFFFFF',
    marginTop: 10,
    fontSize: 16,
  },
  instructionsContainer: {
    position: 'absolute',
    bottom: 110,
    left: 20,
    right: 20,
    alignItems: 'center',
  },
  instructionsText: {
    color: '#FFFFFF',
    fontSize: 14,
    textAlign: 'center',
    backgroundColor: 'rgba(0, 0, 0, 0.6)',
    paddingHorizontal: 20,
    paddingVertical: 10,
    borderRadius: 20,
  },
});

export default VideoIdentifyScreen;
