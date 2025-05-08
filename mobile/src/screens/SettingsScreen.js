import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  Switch,
  TouchableOpacity,
  ScrollView,
  Alert,
  Platform
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useNavigation } from '@react-navigation/native';
import { Ionicons, MaterialIcons } from '@expo/vector-icons';
import AsyncStorage from '@react-native-async-storage/async-storage';
import * as Notifications from 'expo-notifications';
import * as Linking from 'expo-linking';

const SettingsScreen = () => {
  const navigation = useNavigation();
  // Notification settings
  const [identificationNotifs, setIdentificationNotifs] = useState(true);
  const [updateNotifs, setUpdateNotifs] = useState(true);
  const [promotionalNotifs, setPromotionalNotifs] = useState(false);

  // Privacy settings
  const [analyticsEnabled, setAnalyticsEnabled] = useState(true);
  const [saveSearchHistory, setSaveSearchHistory] = useState(true);
  const [locationAccess, setLocationAccess] = useState(false);
  
  // Appearance settings
  const [darkMode, setDarkMode] = useState(false);
  const [autoPlayVideos, setAutoPlayVideos] = useState(true);
  const [highQualityPreviews, setHighQualityPreviews] = useState(false);

  // Data usage settings
  const [wifiOnly, setWifiOnly] = useState(false);
  const [dataSaver, setDataSaver] = useState(false);
  
  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    try {
      // Notification settings
      const idNotifs = await AsyncStorage.getItem('identification_notifications');
      const updateNotifs = await AsyncStorage.getItem('update_notifications');
      const promoNotifs = await AsyncStorage.getItem('promotional_notifications');
      
      // Privacy settings
      const analytics = await AsyncStorage.getItem('analytics_enabled');
      const history = await AsyncStorage.getItem('save_search_history');
      const location = await AsyncStorage.getItem('location_access');
      
      // Appearance settings
      const dark = await AsyncStorage.getItem('dark_mode');
      const autoPlay = await AsyncStorage.getItem('auto_play_videos');
      const highQuality = await AsyncStorage.getItem('high_quality_previews');
      
      // Data usage settings
      const wifi = await AsyncStorage.getItem('wifi_only');
      const saver = await AsyncStorage.getItem('data_saver');
      
      // Set states based on stored values, using default if null
      if (idNotifs !== null) setIdentificationNotifs(JSON.parse(idNotifs));
      if (updateNotifs !== null) setUpdateNotifs(JSON.parse(updateNotifs));
      if (promoNotifs !== null) setPromotionalNotifs(JSON.parse(promoNotifs));
      
      if (analytics !== null) setAnalyticsEnabled(JSON.parse(analytics));
      if (history !== null) setSaveSearchHistory(JSON.parse(history));
      if (location !== null) setLocationAccess(JSON.parse(location));
      
      if (dark !== null) setDarkMode(JSON.parse(dark));
      if (autoPlay !== null) setAutoPlayVideos(JSON.parse(autoPlay));
      if (highQuality !== null) setHighQualityPreviews(JSON.parse(highQuality));
      
      if (wifi !== null) setWifiOnly(JSON.parse(wifi));
      if (saver !== null) setDataSaver(JSON.parse(saver));
      
    } catch (error) {
      console.error('Error loading settings:', error);
    }
  };

  const saveSettings = async (key, value) => {
    try {
      await AsyncStorage.setItem(key, JSON.stringify(value));
    } catch (error) {
      console.error('Error saving settings:', error);
      Alert.alert('Error', 'Failed to save your settings');
    }
  };

  const handleToggleNotification = async (type, value) => {
    // Request notification permissions if enabling any notification
    if (value && Platform.OS !== 'web') {
      const { status } = await Notifications.requestPermissionsAsync();
      if (status !== 'granted') {
        Alert.alert(
          'Notification Permissions',
          'Please enable notifications in your device settings to receive updates.',
          [
            { text: 'Cancel', style: 'cancel' },
            { text: 'Open Settings', onPress: () => Linking.openSettings() }
          ]
        );
        return;
      }
    }

    switch (type) {
      case 'identification':
        setIdentificationNotifs(value);
        saveSettings('identification_notifications', value);
        break;
      case 'update':
        setUpdateNotifs(value);
        saveSettings('update_notifications', value);
        break;
      case 'promotional':
        setPromotionalNotifs(value);
        saveSettings('promotional_notifications', value);
        break;
    }
  };

  const handleTogglePrivacy = (type, value) => {
    switch (type) {
      case 'analytics':
        setAnalyticsEnabled(value);
        saveSettings('analytics_enabled', value);
        break;
      case 'history':
        setSaveSearchHistory(value);
        saveSettings('save_search_history', value);
        break;
      case 'location':
        setLocationAccess(value);
        saveSettings('location_access', value);
        if (value) {
          // This would request location permissions in a real app
          Alert.alert(
            'Location Access',
            'The app will use your location to provide relevant content recommendations.',
            [{ text: 'OK' }]
          );
        }
        break;
    }
  };

  const handleToggleAppearance = (type, value) => {
    switch (type) {
      case 'darkMode':
        setDarkMode(value);
        saveSettings('dark_mode', value);
        // Apply dark mode theme in a real app
        break;
      case 'autoPlay':
        setAutoPlayVideos(value);
        saveSettings('auto_play_videos', value);
        break;
      case 'highQuality':
        setHighQualityPreviews(value);
        saveSettings('high_quality_previews', value);
        break;
    }
  };

  const handleToggleDataUsage = (type, value) => {
    switch (type) {
      case 'wifiOnly':
        setWifiOnly(value);
        saveSettings('wifi_only', value);
        if (value) {
          // Disable data saver if wifi-only is enabled, as they're mutually exclusive
          setDataSaver(false);
          saveSettings('data_saver', false);
        }
        break;
      case 'dataSaver':
        setDataSaver(value);
        saveSettings('data_saver', value);
        if (value) {
          // Disable high quality if data saver is enabled
          setHighQualityPreviews(false);
          saveSettings('high_quality_previews', false);
          // Disable wifi-only if data saver is enabled
          setWifiOnly(false);
          saveSettings('wifi_only', false);
        }
        break;
    }
  };

  const clearData = () => {
    Alert.alert(
      'Clear App Data',
      'This will clear all your saved data including identification history and preferences. This action cannot be undone.',
      [
        { text: 'Cancel', style: 'cancel' },
        { 
          text: 'Clear Data', 
          style: 'destructive',
          onPress: async () => {
            try {
              // Keep only user authentication data
              const authToken = await AsyncStorage.getItem('auth_token');
              const userId = await AsyncStorage.getItem('user_id');
              
              await AsyncStorage.clear();
              
              // Restore authentication data
              if (authToken) await AsyncStorage.setItem('auth_token', authToken);
              if (userId) await AsyncStorage.setItem('user_id', userId);
              
              // Reset settings to defaults
              await loadSettings();
              
              Alert.alert('Success', 'All app data has been cleared');
            } catch (error) {
              console.error('Error clearing data:', error);
              Alert.alert('Error', 'Failed to clear app data');
            }
          }
        }
      ]
    );
  };

  const renderSwitchItem = (icon, iconPack, title, description, value, onToggle) => (
    <View style={styles.settingItem}>
      <View style={styles.settingIconContainer}>
        {iconPack === 'material' ? (
          <MaterialIcons name={icon} size={24} color="#6a11cb" />
        ) : (
          <Ionicons name={icon} size={24} color="#6a11cb" />
        )}
      </View>
      <View style={styles.settingContent}>
        <Text style={styles.settingTitle}>{title}</Text>
        <Text style={styles.settingDescription}>{description}</Text>
      </View>
      <Switch
        value={value}
        onValueChange={onToggle}
        trackColor={{ false: '#d1d1d1', true: '#a28fd0' }}
        thumbColor={value ? '#6a11cb' : '#f4f3f4'}
      />
    </View>
  );

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Settings</Text>
      </View>

      <ScrollView style={styles.scrollView}>
        {/* Notification Settings */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Notifications</Text>
          
          {renderSwitchItem(
            'notifications-outline',
            'ionicons',
            'Identification Results',
            'Get notified when your video identification is complete',
            identificationNotifs,
            (value) => handleToggleNotification('identification', value)
          )}
          
          {renderSwitchItem(
            'refresh-outline',
            'ionicons',
            'App Updates',
            'Receive notifications about new features and updates',
            updateNotifs,
            (value) => handleToggleNotification('update', value)
          )}
          
          {renderSwitchItem(
            'megaphone-outline',
            'ionicons',
            'Promotional',
            'Receive promotional offers and marketing communications',
            promotionalNotifs,
            (value) => handleToggleNotification('promotional', value)
          )}
        </View>

        {/* Privacy Settings */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Privacy</Text>
          
          {renderSwitchItem(
            'analytics-outline',
            'ionicons',
            'Analytics',
            'Allow anonymous usage data collection to improve the app',
            analyticsEnabled,
            (value) => handleTogglePrivacy('analytics', value)
          )}
          
          {renderSwitchItem(
            'time-outline',
            'ionicons',
            'Search History',
            'Save your identification history',
            saveSearchHistory,
            (value) => handleTogglePrivacy('history', value)
          )}
          
          {renderSwitchItem(
            'location-outline',
            'ionicons',
            'Location Access',
            'Allow access to your location for regional content',
            locationAccess,
            (value) => handleTogglePrivacy('location', value)
          )}
        </View>

        {/* Appearance Settings */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Appearance</Text>
          
          {renderSwitchItem(
            'moon-outline',
            'ionicons',
            'Dark Mode',
            'Use dark theme throughout the app',
            darkMode,
            (value) => handleToggleAppearance('darkMode', value)
          )}
          
          {renderSwitchItem(
            'play-circle-outline',
            'ionicons',
            'Auto-Play Videos',
            'Automatically play video previews when available',
            autoPlayVideos,
            (value) => handleToggleAppearance('autoPlay', value)
          )}
          
          {renderSwitchItem(
            'image-outline',
            'ionicons',
            'High Quality Previews',
            'Load higher quality thumbnails and previews',
            highQualityPreviews,
            (value) => handleToggleAppearance('highQuality', value)
          )}
        </View>

        {/* Data Usage Settings */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Data Usage</Text>
          
          {renderSwitchItem(
            'wifi-outline',
            'ionicons',
            'Wi-Fi Only',
            'Only stream video and download content on Wi-Fi',
            wifiOnly,
            (value) => handleToggleDataUsage('wifiOnly', value)
          )}
          
          {renderSwitchItem(
            'cellular-outline',
            'ionicons',
            'Data Saver',
            'Reduce data usage by loading lower quality content',
            dataSaver,
            (value) => handleToggleDataUsage('dataSaver', value)
          )}
        </View>

        {/* Data Management */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Data Management</Text>
          
          <TouchableOpacity style={styles.actionItem} onPress={clearData}>
            <View style={styles.settingIconContainer}>
              <Ionicons name="trash-outline" size={24} color="#ff3b30" />
            </View>
            <View style={styles.settingContent}>
              <Text style={styles.actionItemTitle}>Clear App Data</Text>
              <Text style={styles.actionItemDescription}>Clear all saved data and reset preferences</Text>
            </View>
            <Ionicons name="chevron-forward" size={22} color="#aaa" />
          </TouchableOpacity>
          
          <TouchableOpacity 
            style={styles.actionItem} 
            onPress={() => navigation.navigate('DataExport')}
          >
            <View style={styles.settingIconContainer}>
              <Ionicons name="download-outline" size={24} color="#6a11cb" />
            </View>
            <View style={styles.settingContent}>
              <Text style={styles.actionItemTitle}>Export Data</Text>
              <Text style={styles.actionItemDescription}>Download a copy of your personal data</Text>
            </View>
            <Ionicons name="chevron-forward" size={22} color="#aaa" />
          </TouchableOpacity>
        </View>

        {/* App Information */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>About</Text>
          
          <TouchableOpacity 
            style={styles.actionItem} 
            onPress={() => navigation.navigate('About')}
          >
            <View style={styles.settingIconContainer}>
              <Ionicons name="information-circle-outline" size={24} color="#6a11cb" />
            </View>
            <View style={styles.settingContent}>
              <Text style={styles.actionItemTitle}>About VidID</Text>
              <Text style={styles.actionItemDescription}>Version 1.0.0</Text>
            </View>
            <Ionicons name="chevron-forward" size={22} color="#aaa" />
          </TouchableOpacity>
          
          <TouchableOpacity 
            style={styles.actionItem} 
            onPress={() => navigation.navigate('Help')}
          >
            <View style={styles.settingIconContainer}>
              <Ionicons name="help-circle-outline" size={24} color="#6a11cb" />
            </View>
            <View style={styles.settingContent}>
              <Text style={styles.actionItemTitle}>Help & Support</Text>
              <Text style={styles.actionItemDescription}>Get assistance with using the app</Text>
            </View>
            <Ionicons name="chevron-forward" size={22} color="#aaa" />
          </TouchableOpacity>
          
          <TouchableOpacity 
            style={styles.actionItem} 
            onPress={() => navigation.navigate('PrivacyPolicy')}
          >
            <View style={styles.settingIconContainer}>
              <MaterialIcons name="privacy-tip" size={24} color="#6a11cb" />
            </View>
            <View style={styles.settingContent}>
              <Text style={styles.actionItemTitle}>Privacy Policy</Text>
              <Text style={styles.actionItemDescription}>Read our privacy policy</Text>
            </View>
            <Ionicons name="chevron-forward" size={22} color="#aaa" />
          </TouchableOpacity>
          
          <TouchableOpacity 
            style={styles.actionItem} 
            onPress={() => navigation.navigate('TermsOfService')}
          >
            <View style={styles.settingIconContainer}>
              <Ionicons name="document-text-outline" size={24} color="#6a11cb" />
            </View>
            <View style={styles.settingContent}>
              <Text style={styles.actionItemTitle}>Terms of Service</Text>
              <Text style={styles.actionItemDescription}>Read our terms of service</Text>
            </View>
            <Ionicons name="chevron-forward" size={22} color="#aaa" />
          </TouchableOpacity>
        </View>
        
        <View style={styles.versionContainer}>
          <Text style={styles.versionText}>VidID v1.0.0 (Build 124)</Text>
          <Text style={styles.copyrightText}>© 2025 VidID Technologies, Inc.</Text>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f8f8f8',
  },
  header: {
    backgroundColor: '#fff',
    padding: 15,
    borderBottomWidth: 1,
    borderBottomColor: '#eeeeee',
  },
  headerTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#333',
  },
  scrollView: {
    flex: 1,
  },
  section: {
    backgroundColor: '#fff',
    borderRadius: 10,
    marginHorizontal: 15,
    marginTop: 15,
    padding: 15,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 3,
    elevation: 2,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 15,
  },
  settingItem: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#f0f0f0',
  },
  settingIconContainer: {
    width: 40,
    alignItems: 'center',
  },
  settingContent: {
    flex: 1,
    marginLeft: 10,
  },
  settingTitle: {
    fontSize: 16,
    color: '#333',
    fontWeight: '500',
  },
  settingDescription: {
    fontSize: 13,
    color: '#777',
    marginTop: 2,
  },
  actionItem: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#f0f0f0',
  },
  actionItemTitle: {
    fontSize: 16,
    color: '#333',
    fontWeight: '500',
  },
  actionItemDescription: {
    fontSize: 13,
    color: '#777',
    marginTop: 2,
  },
  versionContainer: {
    alignItems: 'center',
    marginVertical: 30,
  },
  versionText: {
    fontSize: 14,
    color: '#888',
  },
  copyrightText: {
    fontSize: 12,
    color: '#999',
    marginTop: 5,
  },
});

export default SettingsScreen;
