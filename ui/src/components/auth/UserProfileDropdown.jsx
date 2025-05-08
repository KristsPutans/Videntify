import React, { useState, useRef, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useMetadata } from '../../context/MetadataContext';
import './UserProfileDropdown.css';

const UserProfileDropdown = () => {
  const { userInfo, logout } = useMetadata();
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef(null);
  const navigate = useNavigate();
  
  // Handle click outside to close dropdown
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    };
    
    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);
  
  // Handle logout
  const handleLogout = () => {
    logout();
    setIsOpen(false);
    navigate('/');
  };
  
  // Get user initials for avatar
  const getUserInitials = () => {
    if (!userInfo || !userInfo.name) return 'U';
    
    const nameParts = userInfo.name.split(' ');
    if (nameParts.length >= 2) {
      return `${nameParts[0][0]}${nameParts[1][0]}`;
    }
    
    return nameParts[0][0];
  };
  
  // Get user role display name
  const getRoleDisplay = (role) => {
    const roleMap = {
      'admin': 'Administrator',
      'pro': 'Premium User',
      'standard': 'Standard User',
      'basic': 'Basic User'
    };
    
    return roleMap[role] || role;
  };
  
  return (
    <div className="user-profile-dropdown" ref={dropdownRef}>
      <button 
        className="profile-button" 
        onClick={() => setIsOpen(!isOpen)}
        aria-expanded={isOpen}
        aria-haspopup="true"
      >
        {userInfo && userInfo.avatarUrl ? (
          <img 
            src={userInfo.avatarUrl} 
            alt={userInfo.name || 'User'} 
            className="user-avatar"
          />
        ) : (
          <div className="user-initials">
            {getUserInitials()}
          </div>
        )}
        <span className="user-name">{userInfo?.name || 'User'}</span>
        <i className={`fas fa-chevron-${isOpen ? 'up' : 'down'}`}></i>
      </button>
      
      {isOpen && (
        <div className="dropdown-menu">
          <div className="dropdown-header">
            <div className="user-info">
              <h4>{userInfo?.name || 'User'}</h4>
              <p>{userInfo?.email || ''}</p>
              {userInfo?.role && (
                <span className="user-role">{getRoleDisplay(userInfo.role)}</span>
              )}
            </div>
          </div>
          
          <ul className="dropdown-list">
            <li>
              <Link to="/profile" onClick={() => setIsOpen(false)}>
                <i className="fas fa-user"></i> My Profile
              </Link>
            </li>
            <li>
              <Link to="/library" onClick={() => setIsOpen(false)}>
                <i className="fas fa-history"></i> My Library
              </Link>
            </li>
            <li>
              <Link to="/settings" onClick={() => setIsOpen(false)}>
                <i className="fas fa-cog"></i> Settings
              </Link>
            </li>
            {userInfo?.role === 'admin' && (
              <li>
                <Link to="/admin" onClick={() => setIsOpen(false)}>
                  <i className="fas fa-shield-alt"></i> Admin Dashboard
                </Link>
              </li>
            )}
          </ul>
          
          <div className="dropdown-footer">
            <button className="logout-button" onClick={handleLogout}>
              <i className="fas fa-sign-out-alt"></i> Logout
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default UserProfileDropdown;
