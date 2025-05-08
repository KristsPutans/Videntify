import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useMetadata } from '../../context/MetadataContext';
import './Header.css';

const Header = () => {
  const { userPermission } = useMetadata();
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const navigate = useNavigate();
  
  // Check if user is logged in (has a role higher than guest)
  const isLoggedIn = userPermission !== 'guest';
  
  // Handle logout
  const handleLogout = () => {
    // Remove auth token
    localStorage.removeItem('auth_token');
    // Redirect to login
    navigate('/login');
  };
  
  return (
    <header className="app-header">
      <div className="header-container">
        <div className="logo-section">
          <Link to="/" className="logo">
            <img src="/logo.svg" alt="Videntify Logo" />
            <span>Videntify</span>
          </Link>
        </div>
        
        <nav className="desktop-nav">
          <ul>
            <li><Link to="/">Home</Link></li>
            <li><Link to="/search">Identify</Link></li>
            <li><Link to="/library">Library</Link></li>
            {userPermission === 'admin' && (
              <li><Link to="/admin">Admin</Link></li>
            )}
            {userPermission === 'staff' || userPermission === 'admin' ? (
              <li><Link to="/dashboard">Dashboard</Link></li>
            ) : null}
          </ul>
        </nav>
        
        <div className="auth-section">
          {isLoggedIn ? (
            <div className="user-menu">
              <button 
                className="user-button"
                onClick={() => setIsMenuOpen(!isMenuOpen)}
              >
                <span className="username">{userPermission}</span>
                <i className="icon-dropdown"></i>
              </button>
              {isMenuOpen && (
                <div className="dropdown-menu">
                  <Link to="/profile" onClick={() => setIsMenuOpen(false)}>Profile</Link>
                  <Link to="/settings" onClick={() => setIsMenuOpen(false)}>Settings</Link>
                  <button onClick={handleLogout}>Logout</button>
                </div>
              )}
            </div>
          ) : (
            <div className="auth-buttons">
              <Link to="/login" className="login-button">Login</Link>
              <Link to="/signup" className="signup-button">Sign Up</Link>
            </div>
          )}
        </div>
        
        <button className="mobile-menu-button" onClick={() => setIsMenuOpen(!isMenuOpen)}>
          <span className="sr-only">Menu</span>
          <i className={`icon-menu ${isMenuOpen ? 'open' : ''}`}></i>
        </button>
      </div>
      
      {isMenuOpen && (
        <div className="mobile-menu">
          <nav>
            <ul>
              <li><Link to="/" onClick={() => setIsMenuOpen(false)}>Home</Link></li>
              <li><Link to="/search" onClick={() => setIsMenuOpen(false)}>Identify</Link></li>
              <li><Link to="/library" onClick={() => setIsMenuOpen(false)}>Library</Link></li>
              {userPermission === 'admin' && (
                <li><Link to="/admin" onClick={() => setIsMenuOpen(false)}>Admin</Link></li>
              )}
              {userPermission === 'staff' || userPermission === 'admin' ? (
                <li><Link to="/dashboard" onClick={() => setIsMenuOpen(false)}>Dashboard</Link></li>
              ) : null}
              
              {!isLoggedIn && (
                <>
                  <li><Link to="/login" onClick={() => setIsMenuOpen(false)}>Login</Link></li>
                  <li><Link to="/signup" onClick={() => setIsMenuOpen(false)}>Sign Up</Link></li>
                </>
              )}
              {isLoggedIn && (
                <>
                  <li><Link to="/profile" onClick={() => setIsMenuOpen(false)}>Profile</Link></li>
                  <li><Link to="/settings" onClick={() => setIsMenuOpen(false)}>Settings</Link></li>
                  <li><button onClick={() => { handleLogout(); setIsMenuOpen(false); }}>Logout</button></li>
                </>
              )}
            </ul>
          </nav>
        </div>
      )}
    </header>
  );
};

export default Header;
