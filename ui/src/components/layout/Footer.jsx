import React from 'react';
import { Link } from 'react-router-dom';
import './Footer.css';

const Footer = () => {
  const currentYear = new Date().getFullYear();
  
  return (
    <footer className="app-footer">
      <div className="footer-container">
        <div className="footer-main">
          <div className="footer-column">
            <div className="footer-logo">
              <img src="/logo.svg" alt="Videntify Logo" />
              <span>Videntify</span>
            </div>
            <p className="footer-description">
              Advanced video identification and metadata enrichment platform powered by AI
            </p>
          </div>
          
          <div className="footer-column">
            <h3>Features</h3>
            <ul>
              <li><Link to="/features/video-identification">Video Identification</Link></li>
              <li><Link to="/features/metadata-enrichment">Metadata Enrichment</Link></li>
              <li><Link to="/features/frame-detection">Frame Detection</Link></li>
              <li><Link to="/features/api-access">API Access</Link></li>
            </ul>
          </div>
          
          <div className="footer-column">
            <h3>Company</h3>
            <ul>
              <li><Link to="/about">About Us</Link></li>
              <li><Link to="/contact">Contact</Link></li>
              <li><Link to="/careers">Careers</Link></li>
              <li><Link to="/blog">Blog</Link></li>
            </ul>
          </div>
          
          <div className="footer-column">
            <h3>Support</h3>
            <ul>
              <li><Link to="/support/faq">FAQ</Link></li>
              <li><Link to="/support/documentation">Documentation</Link></li>
              <li><Link to="/support/tutorials">Tutorials</Link></li>
              <li><Link to="/support/contact">Contact Support</Link></li>
            </ul>
          </div>
        </div>
        
        <div className="footer-bottom">
          <div className="footer-links">
            <Link to="/privacy">Privacy Policy</Link>
            <Link to="/terms">Terms of Service</Link>
            <Link to="/cookies">Cookie Policy</Link>
          </div>
          
          <div className="social-links">
            <a href="https://twitter.com/videntify" target="_blank" rel="noopener noreferrer" aria-label="Twitter">
              <i className="fab fa-twitter"></i>
            </a>
            <a href="https://linkedin.com/company/videntify" target="_blank" rel="noopener noreferrer" aria-label="LinkedIn">
              <i className="fab fa-linkedin"></i>
            </a>
            <a href="https://github.com/videntify" target="_blank" rel="noopener noreferrer" aria-label="GitHub">
              <i className="fab fa-github"></i>
            </a>
            <a href="https://youtube.com/videntify" target="_blank" rel="noopener noreferrer" aria-label="YouTube">
              <i className="fab fa-youtube"></i>
            </a>
          </div>
          
          <p className="copyright">&copy; {currentYear} Videntify. All rights reserved.</p>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
