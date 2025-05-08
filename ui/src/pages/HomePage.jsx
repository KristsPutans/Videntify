import React from 'react';
import { Link } from 'react-router-dom';
import './HomePage.css';

const HomePage = () => {
  return (
    <div className="home-page">
      <section className="hero-section">
        <div className="hero-content">
          <h1>Powerful Video Identification at Your Fingertips</h1>
          <p>
            Videntify uses advanced AI and computer vision to identify videos from just a few seconds of footage.
            Get detailed information about any video with our robust identification engine.
          </p>
          <div className="hero-buttons">
            <Link to="/search" className="primary-button">Identify Video</Link>
            <Link to="/about" className="secondary-button">Learn More</Link>
          </div>
        </div>
        <div className="hero-image">
          <img src="/images/hero-illustration.svg" alt="Video identification illustration" />
        </div>
      </section>

      <section className="features-section">
        <h2>Our Advanced Features</h2>
        <div className="features-grid">
          <div className="feature-card">
            <div className="feature-icon">
              <img src="/images/icons/visual-identification.svg" alt="Visual identification" />
            </div>
            <h3>Visual Identification</h3>
            <p>Identify videos using our CNN, perceptual hash, and motion-based feature extractors</p>
          </div>
          
          <div className="feature-card">
            <div className="feature-icon">
              <img src="/images/icons/audio-analysis.svg" alt="Audio analysis" />
            </div>
            <h3>Audio Analysis</h3>
            <p>Recognize content through audio fingerprinting, MFCC analysis, and waveform statistics</p>
          </div>
          
          <div className="feature-card">
            <div className="feature-icon">
              <img src="/images/icons/enriched-metadata.svg" alt="Enriched metadata" />
            </div>
            <h3>Enriched Metadata</h3>
            <p>Get comprehensive metadata from multiple sources including TMDB, YouTube, and more</p>
          </div>
          
          <div className="feature-card">
            <div className="feature-icon">
              <img src="/images/icons/frame-detection.svg" alt="Frame detection" />
            </div>
            <h3>Frame-level Detection</h3>
            <p>Identify specific frames and scenes within videos for precise content matching</p>
          </div>
        </div>
      </section>

      <section className="how-it-works">
        <h2>How It Works</h2>
        <div className="steps-container">
          <div className="step">
            <div className="step-number">1</div>
            <h3>Upload</h3>
            <p>Upload a video clip or provide a URL to a video you want to identify</p>
          </div>
          
          <div className="step-connector"></div>
          
          <div className="step">
            <div className="step-number">2</div>
            <h3>Process</h3>
            <p>Our advanced algorithms extract visual and audio features from your content</p>
          </div>
          
          <div className="step-connector"></div>
          
          <div className="step">
            <div className="step-number">3</div>
            <h3>Match</h3>
            <p>We compare your content against our database of video signatures</p>
          </div>
          
          <div className="step-connector"></div>
          
          <div className="step">
            <div className="step-number">4</div>
            <h3>Results</h3>
            <p>View detailed information about the matched content with enhanced metadata</p>
          </div>
        </div>
      </section>

      <section className="cta-section">
        <div className="cta-content">
          <h2>Ready to Identify Your Video?</h2>
          <p>Start using our powerful video identification engine today.</p>
          <Link to="/search" className="primary-button">Get Started</Link>
        </div>
      </section>
    </div>
  );
};

export default HomePage;
