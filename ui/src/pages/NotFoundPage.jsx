import React from 'react';
import { Link } from 'react-router-dom';
import './NotFoundPage.css';

const NotFoundPage = () => {
  return (
    <div className="not-found-page">
      <div className="not-found-content">
        <div className="error-code">404</div>
        <h1>Page Not Found</h1>
        <p>The page you are looking for doesn't exist or has been moved.</p>
        <div className="not-found-actions">
          <Link to="/" className="home-button">
            <i className="fas fa-home"></i> Back to Home
          </Link>
          <Link to="/search" className="search-button">
            <i className="fas fa-search"></i> Identify a Video
          </Link>
        </div>
      </div>
    </div>
  );
};

export default NotFoundPage;
