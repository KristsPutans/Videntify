import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useMetadata } from '../context/MetadataContext';
import './SettingsPage.css';

const SettingsPage = () => {
  const { userInfo, userPermission, updateUserPreferences } = useMetadata();
  const navigate = useNavigate();
  
  // Settings state
  const [generalSettings, setGeneralSettings] = useState({
    theme: 'light',
    language: 'en',
    autoPlay: false,
    showThumbnails: true
  });
  
  const [notificationSettings, setNotificationSettings] = useState({
    emailNotifications: true,
    identificationComplete: true,
    newFeatures: true,
    marketingEmails: false
  });
  
  const [apiSettings, setApiSettings] = useState({
    apiKey: '',
    showApiKey: false
  });
  
  const [profileSettings, setProfileSettings] = useState({
    name: '',
    email: '',
    avatarUrl: ''
  });
  
  const [activeTab, setActiveTab] = useState('general');
  const [isSaving, setIsSaving] = useState(false);
  const [saveMessage, setSaveMessage] = useState({ type: '', text: '' });
  
  // Load user settings on component mount
  useEffect(() => {
    if (!userInfo) {
      navigate('/login');
      return;
    }
    
    // Load user preferences from context or API
    const loadUserSettings = async () => {
      try {
        // For demo purposes, we're setting dummy data
        // In a real app, you would fetch this from your API
        setProfileSettings({
          name: userInfo.name || '',
          email: userInfo.email || '',
          avatarUrl: userInfo.avatarUrl || ''
        });
        
        // Load saved preferences if available
        const savedPreferences = localStorage.getItem('user_preferences');
        if (savedPreferences) {
          const preferences = JSON.parse(savedPreferences);
          
          setGeneralSettings(prev => ({
            ...prev,
            ...preferences.general
          }));
          
          setNotificationSettings(prev => ({
            ...prev,
            ...preferences.notifications
          }));
        }
        
        // Load API key if user has permission
        if (userPermission === 'pro' || userPermission === 'admin') {
          const token = localStorage.getItem('auth_token');
          if (token) {
            // In a real app, you would fetch the API key from your backend
            setApiSettings(prev => ({
              ...prev,
              apiKey: 'vid_' + Math.random().toString(36).substring(2, 15) + Math.random().toString(36).substring(2, 15)
            }));
          }
        }
        
      } catch (error) {
        console.error('Failed to load settings:', error);
        setSaveMessage({
          type: 'error',
          text: 'Failed to load your settings. Please try again.'
        });
      }
    };
    
    loadUserSettings();
  }, [userInfo, userPermission, navigate]);
  
  // Handle general settings change
  const handleGeneralSettingChange = (e) => {
    const { name, value, type, checked } = e.target;
    setGeneralSettings(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
  };
  
  // Handle notification settings change
  const handleNotificationSettingChange = (e) => {
    const { name, checked } = e.target;
    setNotificationSettings(prev => ({
      ...prev,
      [name]: checked
    }));
  };
  
  // Handle profile settings change
  const handleProfileSettingChange = (e) => {
    const { name, value } = e.target;
    setProfileSettings(prev => ({
      ...prev,
      [name]: value
    }));
  };
  
  // Toggle API key visibility
  const toggleApiKeyVisibility = () => {
    setApiSettings(prev => ({
      ...prev,
      showApiKey: !prev.showApiKey
    }));
  };
  
  // Generate new API key
  const generateNewApiKey = () => {
    const confirmed = window.confirm('Are you sure you want to generate a new API key? This will invalidate your existing key.');
    if (confirmed) {
      setApiSettings(prev => ({
        ...prev,
        apiKey: 'vid_' + Math.random().toString(36).substring(2, 15) + Math.random().toString(36).substring(2, 15),
        showApiKey: true
      }));
    }
  };
  
  // Save settings
  const saveSettings = async () => {
    setIsSaving(true);
    setSaveMessage({ type: '', text: '' });
    
    try {
      // Combine all settings
      const allSettings = {
        general: generalSettings,
        notifications: notificationSettings,
        profile: profileSettings
      };
      
      // In a real app, you would send this to your API
      // For demo purposes, we'll just store in localStorage
      localStorage.setItem('user_preferences', JSON.stringify({
        general: generalSettings,
        notifications: notificationSettings
      }));
      
      // Update user preferences in context
      updateUserPreferences(allSettings);
      
      setSaveMessage({
        type: 'success',
        text: 'Your settings have been saved successfully!'
      });
      
      // Clear success message after 3 seconds
      setTimeout(() => {
        setSaveMessage({ type: '', text: '' });
      }, 3000);
      
    } catch (error) {
      console.error('Failed to save settings:', error);
      setSaveMessage({
        type: 'error',
        text: 'Failed to save your settings. Please try again.'
      });
    } finally {
      setIsSaving(false);
    }
  };
  
  return (
    <div className="settings-page">
      <div className="settings-header">
        <h1>Account Settings</h1>
        <p>Manage your account preferences and settings</p>
      </div>
      
      <div className="settings-content">
        <div className="settings-sidebar">
          <ul className="settings-tabs">
            <li 
              className={activeTab === 'general' ? 'active' : ''}
              onClick={() => setActiveTab('general')}
            >
              <i className="fas fa-sliders-h"></i>
              General
            </li>
            <li 
              className={activeTab === 'profile' ? 'active' : ''}
              onClick={() => setActiveTab('profile')}
            >
              <i className="fas fa-user"></i>
              Profile
            </li>
            <li 
              className={activeTab === 'notifications' ? 'active' : ''}
              onClick={() => setActiveTab('notifications')}
            >
              <i className="fas fa-bell"></i>
              Notifications
            </li>
            {(userPermission === 'pro' || userPermission === 'admin') && (
              <li 
                className={activeTab === 'api' ? 'active' : ''}
                onClick={() => setActiveTab('api')}
              >
                <i className="fas fa-key"></i>
                API Access
              </li>
            )}
            <li 
              className={activeTab === 'privacy' ? 'active' : ''}
              onClick={() => setActiveTab('privacy')}
            >
              <i className="fas fa-shield-alt"></i>
              Privacy & Security
            </li>
          </ul>
        </div>
        
        <div className="settings-main">
          {saveMessage.text && (
            <div className={`settings-alert ${saveMessage.type}`}>
              {saveMessage.type === 'success' && <i className="fas fa-check-circle"></i>}
              {saveMessage.type === 'error' && <i className="fas fa-exclamation-circle"></i>}
              {saveMessage.text}
            </div>
          )}
          
          {/* General Settings Tab */}
          {activeTab === 'general' && (
            <div className="settings-section">
              <h2>General Settings</h2>
              <p className="section-description">Customize your application experience</p>
              
              <div className="settings-form">
                <div className="form-group">
                  <label htmlFor="theme">Theme</label>
                  <select 
                    id="theme" 
                    name="theme" 
                    value={generalSettings.theme}
                    onChange={handleGeneralSettingChange}
                  >
                    <option value="light">Light</option>
                    <option value="dark">Dark</option>
                    <option value="system">System Default</option>
                  </select>
                </div>
                
                <div className="form-group">
                  <label htmlFor="language">Language</label>
                  <select 
                    id="language" 
                    name="language" 
                    value={generalSettings.language}
                    onChange={handleGeneralSettingChange}
                  >
                    <option value="en">English</option>
                    <option value="es">Spanish</option>
                    <option value="fr">French</option>
                    <option value="de">German</option>
                    <option value="ja">Japanese</option>
                  </select>
                </div>
                
                <div className="form-group checkbox">
                  <input 
                    type="checkbox" 
                    id="autoPlay" 
                    name="autoPlay" 
                    checked={generalSettings.autoPlay}
                    onChange={handleGeneralSettingChange}
                  />
                  <label htmlFor="autoPlay">Auto-play videos</label>
                </div>
                
                <div className="form-group checkbox">
                  <input 
                    type="checkbox" 
                    id="showThumbnails" 
                    name="showThumbnails" 
                    checked={generalSettings.showThumbnails}
                    onChange={handleGeneralSettingChange}
                  />
                  <label htmlFor="showThumbnails">Show video thumbnails in results</label>
                </div>
              </div>
            </div>
          )}
          
          {/* Profile Settings Tab */}
          {activeTab === 'profile' && (
            <div className="settings-section">
              <h2>Profile Settings</h2>
              <p className="section-description">Manage your personal information</p>
              
              <div className="settings-form">
                <div className="form-group">
                  <label htmlFor="name">Name</label>
                  <input 
                    type="text" 
                    id="name" 
                    name="name" 
                    value={profileSettings.name}
                    onChange={handleProfileSettingChange}
                  />
                </div>
                
                <div className="form-group">
                  <label htmlFor="email">Email</label>
                  <input 
                    type="email" 
                    id="email" 
                    name="email" 
                    value={profileSettings.email}
                    onChange={handleProfileSettingChange}
                  />
                </div>
                
                <div className="form-group">
                  <label htmlFor="avatarUrl">Profile Picture URL</label>
                  <input 
                    type="url" 
                    id="avatarUrl" 
                    name="avatarUrl" 
                    value={profileSettings.avatarUrl}
                    onChange={handleProfileSettingChange}
                    placeholder="https://example.com/avatar.jpg"
                  />
                </div>
                
                <div className="avatar-preview">
                  {profileSettings.avatarUrl ? (
                    <img src={profileSettings.avatarUrl} alt="Profile preview" />
                  ) : (
                    <div className="avatar-placeholder">
                      <i className="fas fa-user"></i>
                    </div>
                  )}
                </div>
                
                <div className="form-group">
                  <button className="secondary-button">
                    Change Password
                  </button>
                </div>
              </div>
            </div>
          )}
          
          {/* Notifications Settings Tab */}
          {activeTab === 'notifications' && (
            <div className="settings-section">
              <h2>Notification Settings</h2>
              <p className="section-description">Control how you receive notifications</p>
              
              <div className="settings-form">
                <div className="form-group checkbox">
                  <input 
                    type="checkbox" 
                    id="emailNotifications" 
                    name="emailNotifications" 
                    checked={notificationSettings.emailNotifications}
                    onChange={handleNotificationSettingChange}
                  />
                  <label htmlFor="emailNotifications">Enable email notifications</label>
                </div>
                
                <div className="notification-options">
                  <div className="form-group checkbox">
                    <input 
                      type="checkbox" 
                      id="identificationComplete" 
                      name="identificationComplete" 
                      checked={notificationSettings.identificationComplete}
                      onChange={handleNotificationSettingChange}
                      disabled={!notificationSettings.emailNotifications}
                    />
                    <label htmlFor="identificationComplete">When identification is complete</label>
                  </div>
                  
                  <div className="form-group checkbox">
                    <input 
                      type="checkbox" 
                      id="newFeatures" 
                      name="newFeatures" 
                      checked={notificationSettings.newFeatures}
                      onChange={handleNotificationSettingChange}
                      disabled={!notificationSettings.emailNotifications}
                    />
                    <label htmlFor="newFeatures">New features and updates</label>
                  </div>
                  
                  <div className="form-group checkbox">
                    <input 
                      type="checkbox" 
                      id="marketingEmails" 
                      name="marketingEmails" 
                      checked={notificationSettings.marketingEmails}
                      onChange={handleNotificationSettingChange}
                      disabled={!notificationSettings.emailNotifications}
                    />
                    <label htmlFor="marketingEmails">Marketing and promotional emails</label>
                  </div>
                </div>
              </div>
            </div>
          )}
          
          {/* API Settings Tab */}
          {activeTab === 'api' && (userPermission === 'pro' || userPermission === 'admin') && (
            <div className="settings-section">
              <h2>API Access</h2>
              <p className="section-description">Manage your API keys and access</p>
              
              <div className="settings-form">
                <div className="api-key-container">
                  <label>Your API Key</label>
                  <div className="api-key-field">
                    <input 
                      type={apiSettings.showApiKey ? 'text' : 'password'}
                      value={apiSettings.apiKey}
                      readOnly
                    />
                    <button 
                      className="view-key-button"
                      onClick={toggleApiKeyVisibility}
                    >
                      <i className={`fas fa-${apiSettings.showApiKey ? 'eye-slash' : 'eye'}`}></i>
                    </button>
                  </div>
                </div>
                
                <div className="api-key-actions">
                  <button className="secondary-button" onClick={generateNewApiKey}>
                    <i className="fas fa-sync-alt"></i> Generate New Key
                  </button>
                  
                  <button className="copy-button">
                    <i className="fas fa-copy"></i> Copy to Clipboard
                  </button>
                </div>
                
                <div className="api-documentation">
                  <h3>API Documentation</h3>
                  <p>Learn how to use our API to identify videos programmatically:</p>
                  <a href="/docs/api" target="_blank" rel="noopener noreferrer" className="api-docs-link">
                    <i className="fas fa-book"></i> View API Documentation
                  </a>
                </div>
                
                <div className="api-usage">
                  <h3>Current Usage</h3>
                  <div className="usage-stats">
                    <div className="usage-stat">
                      <div className="stat-value">237</div>
                      <div className="stat-label">API Calls This Month</div>
                    </div>
                    
                    <div className="usage-stat">
                      <div className="stat-value">10,000</div>
                      <div className="stat-label">Monthly Limit</div>
                    </div>
                  </div>
                  <div className="usage-bar">
                    <div className="usage-progress" style={{ width: '23.7%' }}></div>
                  </div>
                  <div className="usage-info">23.7% of your monthly limit used</div>
                </div>
              </div>
            </div>
          )}
          
          {/* Privacy Settings Tab */}
          {activeTab === 'privacy' && (
            <div className="settings-section">
              <h2>Privacy & Security</h2>
              <p className="section-description">Manage your privacy and security settings</p>
              
              <div className="settings-form">
                <div className="privacy-section">
                  <h3>Privacy Options</h3>
                  
                  <div className="form-group checkbox">
                    <input 
                      type="checkbox" 
                      id="saveHistory" 
                      name="saveHistory" 
                      defaultChecked={true}
                    />
                    <label htmlFor="saveHistory">Save identification history</label>
                  </div>
                  
                  <div className="form-group checkbox">
                    <input 
                      type="checkbox" 
                      id="allowAnonymousData" 
                      name="allowAnonymousData" 
                      defaultChecked={true}
                    />
                    <label htmlFor="allowAnonymousData">Allow anonymous usage data collection to improve our services</label>
                  </div>
                </div>
                
                <div className="security-section">
                  <h3>Security Options</h3>
                  
                  <div className="form-group checkbox">
                    <input 
                      type="checkbox" 
                      id="twoFactorAuth" 
                      name="twoFactorAuth" 
                      defaultChecked={false}
                    />
                    <label htmlFor="twoFactorAuth">Enable two-factor authentication</label>
                  </div>
                  
                  <button className="secondary-button">
                    <i className="fas fa-user-shield"></i> Manage Account Security
                  </button>
                </div>
                
                <div className="data-management">
                  <h3>Data Management</h3>
                  
                  <button className="secondary-button">
                    <i className="fas fa-download"></i> Download Your Data
                  </button>
                  
                  <button className="danger-button">
                    <i className="fas fa-trash-alt"></i> Delete Account
                  </button>
                </div>
              </div>
            </div>
          )}
          
          <div className="settings-actions">
            <button 
              className="cancel-button"
              onClick={() => navigate(-1)}
            >
              Cancel
            </button>
            <button 
              className="save-button"
              onClick={saveSettings}
              disabled={isSaving}
            >
              {isSaving ? (
                <>
                  <div className="button-spinner"></div>
                  Saving...
                </>
              ) : 'Save Changes'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SettingsPage;
