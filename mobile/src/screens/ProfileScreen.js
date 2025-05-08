import React, { useState, useContext, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Image,
  ScrollView,
  Switch,
  ActivityIndicator,
  Alert,
  Modal,
  TextInput
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { AuthContext } from '../services/AuthContext';
import { useNavigation } from '@react-navigation/native';
import { Ionicons, MaterialIcons } from '@expo/vector-icons';
import * as ImagePicker from 'expo-image-picker';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { LinearGradient } from 'expo-linear-gradient';

const ProfileScreen = () => {
  const { user, signOut, updateUserProfile } = useContext(AuthContext);
  const navigation = useNavigation();
  const [isLoading, setIsLoading] = useState(false);
  const [profileImage, setProfileImage] = useState(null);
  const [notificationsEnabled, setNotificationsEnabled] = useState(true);
  const [darkModeEnabled, setDarkModeEnabled] = useState(false);
  const [saveHistory, setSaveHistory] = useState(true);
  const [showEditNameModal, setShowEditNameModal] = useState(false);
  const [newName, setNewName] = useState('');
  const [showEditEmailModal, setShowEditEmailModal] = useState(false);
  const [newEmail, setNewEmail] = useState('');
  
  useEffect(() => {
    if (user?.profileImage) {
      setProfileImage(user.profileImage);
    }
    
    // Load user preferences from storage
    const loadPreferences = async () => {
      try {
        const notifPref = await AsyncStorage.getItem('notifications_enabled');
        const darkModePref = await AsyncStorage.getItem('dark_mode_enabled');
        const saveHistoryPref = await AsyncStorage.getItem('save_history');
        
        if (notifPref !== null) setNotificationsEnabled(JSON.parse(notifPref));
        if (darkModePref !== null) setDarkModeEnabled(JSON.parse(darkModePref));
        if (saveHistoryPref !== null) setSaveHistory(JSON.parse(saveHistoryPref));
      } catch (e) {
        console.error('Error loading preferences:', e);
      }
    };
    
    loadPreferences();
  }, [user]);
  
  const pickImage = async () => {
    try {
      const permissionResult = await ImagePicker.requestMediaLibraryPermissionsAsync();
      
      if (!permissionResult.granted) {
        Alert.alert('Permission Required', 'You need to grant access to your photos to change your profile picture.');
        return;
      }
      
      const result = await ImagePicker.launchImageLibraryAsync({
        mediaTypes: ImagePicker.MediaTypeOptions.Images,
        allowsEditing: true,
        aspect: [1, 1],
        quality: 0.8,
      });
      
      if (!result.canceled) {
        setIsLoading(true);
        try {
          // In a real app, you would upload the image to your server here
          // For this demo, we'll just update the local state
          setProfileImage(result.assets[0].uri);
          await updateUserProfile({ profileImage: result.assets[0].uri });
          setIsLoading(false);
          Alert.alert('Success', 'Profile picture updated successfully');
        } catch (error) {
          setIsLoading(false);
          Alert.alert('Error', 'Failed to update profile picture');
        }
      }
    } catch (error) {
      Alert.alert('Error', 'Something went wrong when trying to pick an image');
    }
  };
  
  const handleToggleNotifications = async (value) => {
    setNotificationsEnabled(value);
    await AsyncStorage.setItem('notifications_enabled', JSON.stringify(value));
  };
  
  const handleToggleDarkMode = async (value) => {
    setDarkModeEnabled(value);
    await AsyncStorage.setItem('dark_mode_enabled', JSON.stringify(value));
    // In a real app, you would apply the theme change here
  };
  
  const handleToggleSaveHistory = async (value) => {
    setSaveHistory(value);
    await AsyncStorage.setItem('save_history', JSON.stringify(value));
  };
  
  const handleEditName = () => {
    if (user?.name) {
      setNewName(user.name);
    }
    setShowEditNameModal(true);
  };
  
  const handleSaveName = async () => {
    if (!newName.trim()) {
      Alert.alert('Error', 'Name cannot be empty');
      return;
    }
    
    setIsLoading(true);
    try {
      await updateUserProfile({ name: newName });
      setShowEditNameModal(false);
      setIsLoading(false);
      Alert.alert('Success', 'Name updated successfully');
    } catch (error) {
      setIsLoading(false);
      Alert.alert('Error', 'Failed to update name');
    }
  };
  
  const handleEditEmail = () => {
    if (user?.email) {
      setNewEmail(user.email);
    }
    setShowEditEmailModal(true);
  };
  
  const handleSaveEmail = async () => {
    if (!newEmail.trim()) {
      Alert.alert('Error', 'Email cannot be empty');
      return;
    }
    
    // Validate email format
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(newEmail)) {
      Alert.alert('Error', 'Please enter a valid email address');
      return;
    }
    
    setIsLoading(true);
    try {
      await updateUserProfile({ email: newEmail });
      setShowEditEmailModal(false);
      setIsLoading(false);
      Alert.alert('Success', 'Email updated successfully');
    } catch (error) {
      setIsLoading(false);
      Alert.alert('Error', 'Failed to update email');
    }
  };
  
  const handleChangePassword = () => {
    navigation.navigate('ChangePassword');
  };
  
  const handleSignOut = async () => {
    Alert.alert(
      'Sign Out',
      'Are you sure you want to sign out?',
      [
        { text: 'Cancel', style: 'cancel' },
        { 
          text: 'Sign Out', 
          style: 'destructive',
          onPress: signOut
        }
      ]
    );
  };
  
  const handleDeleteAccount = () => {
    Alert.alert(
      'Delete Account',
      'Are you sure you want to delete your account? This action cannot be undone.',
      [
        { text: 'Cancel', style: 'cancel' },
        { 
          text: 'Delete', 
          style: 'destructive',
          onPress: () => {
            // In a real app, you would call an API to delete the account
            Alert.alert('Account Deleted', 'Your account has been successfully deleted.');
            signOut();
          }
        }
      ]
    );
  };

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView contentContainerStyle={styles.scrollContent}>
        {/* Header */}
        <LinearGradient
          colors={['#6a11cb', '#2575fc']}
          style={styles.header}
        >
          <View style={styles.profileImageContainer}>
            {isLoading ? (
              <ActivityIndicator size="large" color="#fff" />
            ) : (
              <TouchableOpacity onPress={pickImage}>
                {profileImage ? (
                  <Image source={{ uri: profileImage }} style={styles.profileImage} />
                ) : (
                  <View style={styles.profileImagePlaceholder}>
                    <Text style={styles.profileImagePlaceholderText}>
                      {user?.name ? user.name.charAt(0).toUpperCase() : 'U'}
                    </Text>
                  </View>
                )}
                <View style={styles.editImageButton}>
                  <Ionicons name="camera" size={16} color="#fff" />
                </View>
              </TouchableOpacity>
            )}
          </View>
          <Text style={styles.userName}>{user?.name || 'User'}</Text>
          <Text style={styles.userEmail}>{user?.email || 'user@example.com'}</Text>
          <View style={styles.statsContainer}>
            <View style={styles.statItem}>
              <Text style={styles.statValue}>42</Text>
              <Text style={styles.statLabel}>Identifications</Text>
            </View>
            <View style={styles.statItem}>
              <Text style={styles.statValue}>12</Text>
              <Text style={styles.statLabel}>Saved</Text>
            </View>
            <View style={styles.statItem}>
              <Text style={styles.statValue}>5</Text>
              <Text style={styles.statLabel}>Shared</Text>
            </View>
          </View>
        </LinearGradient>
        
        {/* Account Settings */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Account Settings</Text>
          
          <TouchableOpacity style={styles.menuItem} onPress={handleEditName}>
            <View style={styles.menuItemLeft}>
              <Ionicons name="person-outline" size={22} color="#555" style={styles.menuItemIcon} />
              <Text style={styles.menuItemText}>Edit Name</Text>
            </View>
            <Ionicons name="chevron-forward" size={22} color="#aaa" />
          </TouchableOpacity>
          
          <TouchableOpacity style={styles.menuItem} onPress={handleEditEmail}>
            <View style={styles.menuItemLeft}>
              <Ionicons name="mail-outline" size={22} color="#555" style={styles.menuItemIcon} />
              <Text style={styles.menuItemText}>Change Email</Text>
            </View>
            <Ionicons name="chevron-forward" size={22} color="#aaa" />
          </TouchableOpacity>
          
          <TouchableOpacity style={styles.menuItem} onPress={handleChangePassword}>
            <View style={styles.menuItemLeft}>
              <Ionicons name="lock-closed-outline" size={22} color="#555" style={styles.menuItemIcon} />
              <Text style={styles.menuItemText}>Change Password</Text>
            </View>
            <Ionicons name="chevron-forward" size={22} color="#aaa" />
          </TouchableOpacity>
        </View>
        
        {/* Preferences */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Preferences</Text>
          
          <View style={styles.menuItem}>
            <View style={styles.menuItemLeft}>
              <Ionicons name="notifications-outline" size={22} color="#555" style={styles.menuItemIcon} />
              <Text style={styles.menuItemText}>Notifications</Text>
            </View>
            <Switch
              value={notificationsEnabled}
              onValueChange={handleToggleNotifications}
              trackColor={{ false: '#d1d1d1', true: '#a28fd0' }}
              thumbColor={notificationsEnabled ? '#6a11cb' : '#f4f3f4'}
            />
          </View>
          
          <View style={styles.menuItem}>
            <View style={styles.menuItemLeft}>
              <Ionicons name="moon-outline" size={22} color="#555" style={styles.menuItemIcon} />
              <Text style={styles.menuItemText}>Dark Mode</Text>
            </View>
            <Switch
              value={darkModeEnabled}
              onValueChange={handleToggleDarkMode}
              trackColor={{ false: '#d1d1d1', true: '#a28fd0' }}
              thumbColor={darkModeEnabled ? '#6a11cb' : '#f4f3f4'}
            />
          </View>
          
          <View style={styles.menuItem}>
            <View style={styles.menuItemLeft}>
              <Ionicons name="time-outline" size={22} color="#555" style={styles.menuItemIcon} />
              <Text style={styles.menuItemText}>Save History</Text>
            </View>
            <Switch
              value={saveHistory}
              onValueChange={handleToggleSaveHistory}
              trackColor={{ false: '#d1d1d1', true: '#a28fd0' }}
              thumbColor={saveHistory ? '#6a11cb' : '#f4f3f4'}
            />
          </View>
        </View>
        
        {/* Support & About */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Support & About</Text>
          
          <TouchableOpacity style={styles.menuItem} onPress={() => navigation.navigate('Help')}>
            <View style={styles.menuItemLeft}>
              <Ionicons name="help-circle-outline" size={22} color="#555" style={styles.menuItemIcon} />
              <Text style={styles.menuItemText}>Help & Support</Text>
            </View>
            <Ionicons name="chevron-forward" size={22} color="#aaa" />
          </TouchableOpacity>
          
          <TouchableOpacity style={styles.menuItem} onPress={() => navigation.navigate('About')}>
            <View style={styles.menuItemLeft}>
              <Ionicons name="information-circle-outline" size={22} color="#555" style={styles.menuItemIcon} />
              <Text style={styles.menuItemText}>About VidID</Text>
            </View>
            <Ionicons name="chevron-forward" size={22} color="#aaa" />
          </TouchableOpacity>
          
          <TouchableOpacity style={styles.menuItem} onPress={() => navigation.navigate('Privacy')}>
            <View style={styles.menuItemLeft}>
              <MaterialIcons name="privacy-tip" size={22} color="#555" style={styles.menuItemIcon} />
              <Text style={styles.menuItemText}>Privacy Policy</Text>
            </View>
            <Ionicons name="chevron-forward" size={22} color="#aaa" />
          </TouchableOpacity>
        </View>
        
        {/* Account Actions */}
        <View style={styles.accountActions}>
          <TouchableOpacity style={styles.signOutButton} onPress={handleSignOut}>
            <Text style={styles.signOutButtonText}>Sign Out</Text>
          </TouchableOpacity>
          
          <TouchableOpacity style={styles.deleteAccountButton} onPress={handleDeleteAccount}>
            <Text style={styles.deleteAccountButtonText}>Delete Account</Text>
          </TouchableOpacity>
        </View>
        
        <View style={styles.versionContainer}>
          <Text style={styles.versionText}>VidID v1.0.0</Text>
        </View>
      </ScrollView>
      
      {/* Edit Name Modal */}
      <Modal
        animationType="slide"
        transparent={true}
        visible={showEditNameModal}
        onRequestClose={() => setShowEditNameModal(false)}
      >
        <View style={styles.modalContainer}>
          <View style={styles.modalContent}>
            <Text style={styles.modalTitle}>Edit Name</Text>
            
            <TextInput
              style={styles.modalInput}
              placeholder="Enter your name"
              value={newName}
              onChangeText={setNewName}
              autoCapitalize="words"
            />
            
            <View style={styles.modalButtons}>
              <TouchableOpacity 
                style={[styles.modalButton, styles.modalCancelButton]} 
                onPress={() => setShowEditNameModal(false)}
              >
                <Text style={styles.modalCancelButtonText}>Cancel</Text>
              </TouchableOpacity>
              
              <TouchableOpacity 
                style={[styles.modalButton, styles.modalSaveButton]} 
                onPress={handleSaveName}
                disabled={isLoading}
              >
                {isLoading ? (
                  <ActivityIndicator color="#fff" size="small" />
                ) : (
                  <Text style={styles.modalSaveButtonText}>Save</Text>
                )}
              </TouchableOpacity>
            </View>
          </View>
        </View>
      </Modal>
      
      {/* Edit Email Modal */}
      <Modal
        animationType="slide"
        transparent={true}
        visible={showEditEmailModal}
        onRequestClose={() => setShowEditEmailModal(false)}
      >
        <View style={styles.modalContainer}>
          <View style={styles.modalContent}>
            <Text style={styles.modalTitle}>Change Email</Text>
            
            <TextInput
              style={styles.modalInput}
              placeholder="Enter your email"
              value={newEmail}
              onChangeText={setNewEmail}
              autoCapitalize="none"
              keyboardType="email-address"
            />
            
            <View style={styles.modalButtons}>
              <TouchableOpacity 
                style={[styles.modalButton, styles.modalCancelButton]} 
                onPress={() => setShowEditEmailModal(false)}
              >
                <Text style={styles.modalCancelButtonText}>Cancel</Text>
              </TouchableOpacity>
              
              <TouchableOpacity 
                style={[styles.modalButton, styles.modalSaveButton]} 
                onPress={handleSaveEmail}
                disabled={isLoading}
              >
                {isLoading ? (
                  <ActivityIndicator color="#fff" size="small" />
                ) : (
                  <Text style={styles.modalSaveButtonText}>Save</Text>
                )}
              </TouchableOpacity>
            </View>
          </View>
        </View>
      </Modal>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  scrollContent: {
    paddingBottom: 30,
  },
  header: {
    padding: 20,
    alignItems: 'center',
    paddingBottom: 30,
  },
  profileImageContainer: {
    marginTop: 10,
    marginBottom: 15,
    alignItems: 'center',
    justifyContent: 'center',
  },
  profileImage: {
    width: 100,
    height: 100,
    borderRadius: 50,
    borderWidth: 3,
    borderColor: '#fff',
  },
  profileImagePlaceholder: {
    width: 100,
    height: 100,
    borderRadius: 50,
    backgroundColor: 'rgba(255,255,255,0.3)',
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 3,
    borderColor: '#fff',
  },
  profileImagePlaceholderText: {
    fontSize: 40,
    color: '#fff',
    fontWeight: 'bold',
  },
  editImageButton: {
    position: 'absolute',
    bottom: 0,
    right: 0,
    backgroundColor: '#6a11cb',
    width: 32,
    height: 32,
    borderRadius: 16,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 2,
    borderColor: '#fff',
  },
  userName: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 5,
  },
  userEmail: {
    fontSize: 14,
    color: 'rgba(255,255,255,0.8)',
    marginBottom: 20,
  },
  statsContainer: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    width: '100%',
    paddingHorizontal: 20,
  },
  statItem: {
    alignItems: 'center',
  },
  statValue: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#fff',
  },
  statLabel: {
    fontSize: 12,
    color: 'rgba(255,255,255,0.8)',
  },
  section: {
    backgroundColor: '#fff',
    borderRadius: 15,
    padding: 15,
    margin: 15,
    marginTop: 10,
    marginBottom: 10,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 5,
    elevation: 3,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 15,
  },
  menuItem: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#f0f0f0',
  },
  menuItemLeft: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  menuItemIcon: {
    marginRight: 15,
  },
  menuItemText: {
    fontSize: 16,
    color: '#333',
  },
  accountActions: {
    margin: 15,
  },
  signOutButton: {
    backgroundColor: '#fff',
    borderRadius: 10,
    paddingVertical: 15,
    alignItems: 'center',
    marginBottom: 15,
    borderWidth: 1,
    borderColor: '#ddd',
  },
  signOutButtonText: {
    color: '#6a11cb',
    fontSize: 16,
    fontWeight: 'bold',
  },
  deleteAccountButton: {
    backgroundColor: 'rgba(255,59,48,0.1)',
    borderRadius: 10,
    paddingVertical: 15,
    alignItems: 'center',
  },
  deleteAccountButtonText: {
    color: '#ff3b30',
    fontSize: 16,
    fontWeight: 'bold',
  },
  versionContainer: {
    alignItems: 'center',
    marginVertical: 20,
  },
  versionText: {
    color: '#888',
    fontSize: 12,
  },
  modalContainer: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.5)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  modalContent: {
    backgroundColor: '#fff',
    borderRadius: 15,
    padding: 20,
    width: '85%',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.25,
    shadowRadius: 3.84,
    elevation: 5,
  },
  modalTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 20,
    textAlign: 'center',
  },
  modalInput: {
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 8,
    padding: 12,
    fontSize: 16,
    marginBottom: 20,
  },
  modalButtons: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  modalButton: {
    flex: 1,
    paddingVertical: 12,
    borderRadius: 8,
    alignItems: 'center',
  },
  modalCancelButton: {
    backgroundColor: '#f2f2f2',
    marginRight: 10,
  },
  modalCancelButtonText: {
    color: '#333',
    fontWeight: 'bold',
    fontSize: 16,
  },
  modalSaveButton: {
    backgroundColor: '#6a11cb',
    marginLeft: 10,
  },
  modalSaveButtonText: {
    color: '#fff',
    fontWeight: 'bold',
    fontSize: 16,
  },
});

export default ProfileScreen;
