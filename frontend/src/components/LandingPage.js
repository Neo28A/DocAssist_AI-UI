import React from 'react';
import { useNavigate } from 'react-router-dom';
import './LandingPage.css';
import sampleReport from '../assets/sample-report.png';

const LandingPage = () => {
  const navigate = useNavigate();

  const scrollToFormat = () => {
    const formatSection = document.getElementById('format-section');
    const navHeight = 70; // Account for fixed nav bar height
    const targetPosition = formatSection.getBoundingClientRect().top + window.pageYOffset - (window.innerHeight/2) + (formatSection.offsetHeight/2) - navHeight;
    
    window.scrollTo({
      top: targetPosition,
      behavior: 'smooth'
    });
  };

  return (
    <div className="landing-container">
      <div className="nav-bar">
        <div className="nav-content">
          <span className="nav-brand" onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}>
            <svg className="nav-logo" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M8 2v4" />
              <path d="M16 2v4" />
              <path d="M3 10h18" />
              <path d="M12 14v4" />
              <path d="M10 16h4" />
              <rect x="3" y="4" width="18" height="18" rx="2" />
            </svg>
            <span className="nav-brand-text">DocAssist</span>
          </span>
          <div className="nav-center">
            <span className="nav-link" onClick={() => document.getElementById('features-section').scrollIntoView({ behavior: 'smooth' })}>Features</span>
            <span className="nav-link" onClick={scrollToFormat}>Format</span>
          </div>
          <button className="get-started-btn" onClick={() => navigate('/app')} style={{ padding: '0.5rem 1rem', fontSize: '0.9rem' }}>
            Try Now
          </button>
        </div>
      </div>
      <div className="landing-content">
        <div className="hero-section">
          <h1 className="landing-title">
            DocAssist Your Medical AI Assistant
          </h1>
          <p className="landing-subtitle">
            Advanced AI-powered platform that analyzes blood reports and provides instant treatment recommendations
          </p>
          <div className="button-group">
            <button className="get-started-btn" onClick={() => navigate('/app')}>
              Get Started
            </button>
            <button className="learn-more-btn" onClick={scrollToFormat}>
              Report Format <span className="arrow">↓</span>
            </button>
          </div>
        </div>
      </div>

      <div id="features-section" className="features-section">
        <h2 className="features-title">Key Features</h2>
        <div className="feature-cards">
          <div className="feature-card">
            <div className="feature-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z" />
              </svg>
            </div>
            <div className="feature-content">
              <h3>Instant Analysis</h3>
              <p>Get blood report analysis within seconds using advanced AI</p>
            </div>
          </div>

          <div className="feature-card">
            <div className="feature-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
              </svg>
            </div>
            <div className="feature-content">
              <h3>Accurate Diagnosis</h3>
              <p>Precise detection of anemia and other blood disorders</p>
            </div>
          </div>

          <div className="feature-card">
            <div className="feature-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z" />
                <polyline points="7.5 4.21 12 6.81 16.5 4.21" />
                <polyline points="7.5 19.79 7.5 14.6 3 12" />
                <polyline points="21 12 16.5 14.6 16.5 19.79" />
                <polyline points="3.27 6.96 12 12.01 20.73 6.96" />
                <line x1="12" y1="22.08" x2="12" y2="12" />
              </svg>
            </div>
            <div className="feature-content">
              <h3>Treatment Plans</h3>
              <p>Personalized treatment recommendations and dietary advice</p>
            </div>
          </div>
        </div>
      </div>

      <div id="format-section" className="format-section">
        <h2 className="format-title">Required Report Format</h2>
        <div className="format-content">
          <div className="format-text">
            <p className="format-description">
              Please ensure your blood report follows this format for accurate analysis
            </p>
            <p className="format-description">
              Sex: 1 for Male, 0 for Female
            </p>
          </div>
          <div className="format-image-container">
            <img src={sampleReport} alt="Sample Blood Report Format" className="format-image" />
          </div>
        </div>
      </div>

      <footer className="footer">
        <div className="footer-divider"></div>
        <div className="footer-content">
          <div className="footer-left">
            <span className="footer-brand">
              <svg className="footer-logo" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M8 2v4" />
                <path d="M16 2v4" />
                <path d="M3 10h18" />
                <path d="M12 14v4" />
                <path d="M10 16h4" />
                <rect x="3" y="4" width="18" height="18" rx="2" />
              </svg>
              DocAssist
            </span>
            <p className="footer-description">
              Advanced AI-powered platform for precise medical diagnostics
            </p>
            <div className="footer-social">
              <h4>Follow Us</h4>
              <div className="footer-social-links">
                <a href="https://github.com/chetankittali" target="_blank" rel="noopener noreferrer">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
                    <path d="M9 19c-5 1.5-5-2.5-7-3m14 6v-3.87a3.37 3.37 0 0 0-.94-2.61c3.14-.35 6.44-1.54 6.44-7A5.44 5.44 0 0 0 20 4.77 5.07 5.07 0 0 0 19.91 1S18.73.65 16 2.48a13.38 13.38 0 0 0-7 0C6.27.65 5.09 1 5.09 1A5.07 5.07 0 0 0 5 4.77a5.44 5.44 0 0 0-1.5 3.78c0 5.42 3.3 6.61 6.44 7A3.37 3.37 0 0 0 9 18.13V22" />
                  </svg>
                </a>
                <a href="https://linkedin.com/in/chetankittali" target="_blank" rel="noopener noreferrer">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
                    <path d="M16 8a6 6 0 0 1 6 6v7h-4v-7a2 2 0 0 0-2-2 2 2 0 0 0-2 2v7h-4v-7a6 6 0 0 1 6-6z" />
                    <rect x="2" y="9" width="4" height="12" />
                    <circle cx="4" cy="4" r="2" />
                  </svg>
                </a>
                <a href="https://twitter.com/chetankittali" target="_blank" rel="noopener noreferrer">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
                    <path d="M23 3a10.9 10.9 0 0 1-3.14 1.53 4.48 4.48 0 0 0-7.86 3v1A10.66 10.66 0 0 1 3 4s-4 9 5 13a11.64 11.64 0 0 1-7 2c9 5 20 0 20-11.5a4.5 4.5 0 0 0-.08-.83A7.72 7.72 0 0 0 23 3z" />
                  </svg>
                </a>
                <a href="https://instagram.com/chetankittali" target="_blank" rel="noopener noreferrer">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
                    <rect x="2" y="2" width="20" height="20" rx="5" ry="5" />
                    <path d="M16 11.37A4 4 0 1 1 12.63 8 4 4 0 0 1 16 11.37z" />
                    <line x1="17.5" y1="6.5" x2="17.51" y2="6.5" />
                  </svg>
                </a>
              </div>
            </div>
          </div>
          <div className="footer-right">
            <div className="footer-links">
              <div className="footer-links-column">
                <h4>Quick Links</h4>
                <span onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}>Home</span>
                <span onClick={() => document.getElementById('features-section').scrollIntoView({ behavior: 'smooth' })}>Features</span>
                <span onClick={scrollToFormat}>Format</span>
              </div>
              <div className="footer-links-column">
                <h4>Contact</h4>
                <a href="mailto:contact@docassist.ai">contact@docassist.ai</a>
                <a href="tel:+1234567890">+1 (234) 567-890</a>
              </div>
            </div>
          </div>
        </div>
        <div className="footer-bottom">
          <p>&copy; {new Date().getFullYear()} DocAssist AI. All rights reserved.</p>
        </div>
      </footer>
    </div>
  );
};

export default LandingPage; 