import React, { useState, useEffect } from 'react';
import jsPDF from 'jspdf';
import '../App.css';
import { useNavigate } from 'react-router-dom';

function MainApp() {
  const navigate = useNavigate();
  const [file, setFile] = useState(null);
  const [prediction, setPrediction] = useState(null);
  const [theme, setTheme] = useState('dark');
  const [isTyping, setIsTyping] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [displayedContent, setDisplayedContent] = useState('');
  const [isContentFullyTyped, setIsContentFullyTyped] = useState(false);
  const [inputMethod, setInputMethod] = useState(null);
  const [manualInputs, setManualInputs] = useState({
    Hematocrit: '',
    Hemoglobin: '',
    Erythrocyte: '',
    Leucocyte: '',
    Thrombocyte: '',
    Mch: '',
    Mchc: '',
    Mcv: '',
    Age: '',
    Sex: ''
  });

  const toggleTheme = () => {
    setTheme(theme === 'light' ? 'dark' : 'light');
  };

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
    setPrediction(null);
    setIsTyping(false);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!file) {
      alert('Please select a file first');
      return;
    }

    setIsAnalyzing(true);
    setPrediction(null);
    setIsContentFullyTyped(false);
    setDisplayedContent('');
    
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch('https://docassist-ai-ui.onrender.com/predict', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Server error');
      }

      const data = await response.json();
      console.log('Prediction response:', data);
      setPrediction(data);
      setIsTyping(true);
    } catch (error) {
      console.error('Error:', error);
      alert('Server connection error. Please make sure the backend server is running on port 5000');
      setIsAnalyzing(false);
    }
  };

  const handleManualSubmit = async (e) => {
    e.preventDefault();
    setIsAnalyzing(true);
    setPrediction(null);
    setIsContentFullyTyped(false);
    setDisplayedContent('');

    try {
      const response = await fetch('https://docassist-ai-ui.onrender.com/predict_manual', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(manualInputs),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Server error');
      }

      const data = await response.json();
      console.log('Manual prediction response:', data);
      setPrediction(data);
      setIsTyping(true);
    } catch (error) {
      console.error('Error:', error);
      alert('Server connection error. Please make sure the backend server is running on port 5000');
      setIsAnalyzing(false);
    }
  };

  const handleInputChange = (e) => {
    setManualInputs(prev => ({
      ...prev,
      [e.target.name]: e.target.value
    }));
  };

  const typeContent = React.useCallback((content, index = 0) => {
    if (index < content.length) {
      setDisplayedContent(prev => prev + content.charAt(index));
      setTimeout(() => typeContent(content, index + 1), 20);
    } else {
      setIsContentFullyTyped(true);
      setIsAnalyzing(false);
    }
  }, []);

  const downloadReport = () => {
    if (!displayedContent) return;
    
    const doc = new jsPDF();
    
    doc.setFont("helvetica");
    
    doc.setFontSize(16);
    doc.text("Medical Report Analysis", 20, 20);
    
    doc.setFontSize(10);
    const date = new Date().toLocaleDateString();
    doc.text(`Generated on: ${date}`, 20, 30);
    
    doc.setFontSize(12);
    const splitText = doc.splitTextToSize(displayedContent, 170);
    doc.text(splitText, 20, 40);
    
    doc.save("medical-report.pdf");
  };

  useEffect(() => {
    if (prediction && isTyping) {
      if (!prediction.detailed_analysis) {
        console.error('No detailed analysis available');
        typeContent('Error: Analysis not available');
        return;
      }

      typeContent(prediction.detailed_analysis);
    }
  }, [prediction, isTyping, typeContent]);

  const areAllInputsFilled = () => {
    return Object.values(manualInputs).every(value => value !== '');
  };

  const handleKeyPress = (e, currentField) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      
      const fieldOrder = [
        'Hematocrit', 'Hemoglobin',
        'Erythrocyte', 'Leucocyte',
        'Thrombocyte', 'Mch',
        'Mchc', 'Mcv',
        'Age', 'Sex'
      ];
      
      const currentIndex = fieldOrder.indexOf(currentField);
      
      if (currentIndex < fieldOrder.length - 1) {
        const nextField = document.querySelector(`input[name="${fieldOrder[currentIndex + 1]}"]`);
        if (nextField) {
          nextField.focus();
        }
      }
    }
  };

  return (
    <div className={`app ${theme}`}>
      <div className="header">
        <h1 onClick={() => navigate('/')} style={{ cursor: 'pointer' }}>DocAssist AI</h1>
        <div className="theme-switch-wrapper">
          <svg className="sun-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor">
            <circle cx="12" cy="12" r="5" />
            <line x1="12" y1="1" x2="12" y2="3" />
            <line x1="12" y1="21" x2="12" y2="23" />
            <line x1="4.22" y1="4.22" x2="5.64" y2="5.64" />
            <line x1="18.36" y1="18.36" x2="19.78" y2="19.78" />
            <line x1="1" y1="12" x2="3" y2="12" />
            <line x1="21" y1="12" x2="23" y2="12" />
            <line x1="4.22" y1="19.78" x2="5.64" y2="18.36" />
            <line x1="18.36" y1="5.64" x2="19.78" y2="4.22" />
          </svg>
          <label className="theme-switch">
            <input
              type="checkbox"
              checked={theme === 'dark'}
              onChange={toggleTheme}
            />
            <span className="slider round"></span>
          </label>
          <svg className="moon-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor">
            <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
          </svg>
        </div>
      </div>
      <div className="container">
        <div className="input-section">
          <div className="section-header">
            <h2>Analysis Method</h2>
            {inputMethod && (
              <button className="back-btn" onClick={() => setInputMethod(null)}>
                ← Back to Selection
              </button>
            )}
          </div>
          
          {!inputMethod && (
            <div className="method-selection">
              <button className="method-btn" onClick={() => setInputMethod('upload')}>
                <svg className="method-btn-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M13 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z" />
                  <path d="M13 2v7h7" />
                  <path d="M12 12v6" />
                  <path d="M9 15l3-3 3 3" />
                </svg>
                <span className="method-btn-text">Upload PDF Report</span>
              </button>
              <button className="method-btn" onClick={() => setInputMethod('manual')}>
                <svg className="method-btn-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M12 5v14" />
                  <path d="M5 12h14" />
                  <rect x="3" y="3" width="18" height="18" rx="2" />
                </svg>
                <span className="method-btn-text">Enter Values Manually</span>
              </button>
            </div>
          )}

          {inputMethod === 'upload' && (
            <>
              <div className="upload-container">
                <div className="upload-area" onClick={() => document.getElementById('fileInput').click()}>
                  <input
                    type="file"
                    id="fileInput"
                    accept=".pdf"
                    onChange={handleFileChange}
                    style={{ display: 'none' }}
                  />
                  <div className="upload-content">
                    <div className={`upload-icon ${file ? 'file-uploaded' : ''}`}>
                      {file ? (
                        <div className="upload-icon file-uploaded">
                          <svg width="60" height="60" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                            <path d="M13 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                            <path d="M13 2v7h7" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                            <path d="M9 12l2 2 4-4" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                          </svg>
                        </div>
                      ) : (
                        <>
                          <div className="upload-icon">
                            <svg width="60" height="60" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                              <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4M17 8l-5-5-5 5M12 3v12" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                            </svg>
                          </div>
                          <p>Upload your blood report here</p>
                          <p className="file-type">PDF (MAX. 10MB)</p>
                        </>
                      )}
                    </div>
                    {file && (
                      <>
                        <div className="file-status">File Uploaded</div>
                        <div className="file-name">{file.name}</div>
                      </>
                    )}
                  </div>
                </div>
                <button
                  className="analyze-button"
                  onClick={handleSubmit}
                  disabled={!file || isAnalyzing}
                >
                  {isAnalyzing ? (
                    <>
                      <span className="loading-spinner"></span>
                      Analyzing Report...
                    </>
                  ) : (
                    'Analyze Report'
                  )}
                </button>
              </div>
            </>
          )}

          {inputMethod === 'manual' && (
            <>
              <form className="manual-input-form" onSubmit={handleManualSubmit}>
                <div className="input-grid">
                  <div className="input-group">
                    <label>Hematocrit</label>
                    <input
                      type="number"
                      step="0.1"
                      name="Hematocrit"
                      placeholder="e.g., 35.1"
                      value={manualInputs.Hematocrit}
                      onChange={handleInputChange}
                      onKeyPress={(e) => handleKeyPress(e, 'Hematocrit')}
                      required
                    />
                  </div>
                  <div className="input-group">
                    <label>Hemoglobin</label>
                    <input
                      type="number"
                      step="0.1"
                      name="Hemoglobin"
                      placeholder="e.g., 14.5"
                      value={manualInputs.Hemoglobin}
                      onChange={handleInputChange}
                      onKeyPress={(e) => handleKeyPress(e, 'Hemoglobin')}
                      required
                    />
                  </div>
                  <div className="input-group">
                    <label>Erythrocyte</label>
                    <input
                      type="number"
                      step="0.1"
                      name="Erythrocyte"
                      placeholder="e.g., 4.5"
                      value={manualInputs.Erythrocyte}
                      onChange={handleInputChange}
                      onKeyPress={(e) => handleKeyPress(e, 'Erythrocyte')}
                      required
                    />
                  </div>
                  <div className="input-group">
                    <label>Leucocyte</label>
                    <input
                      type="number"
                      step="0.1"
                      name="Leucocyte"
                      placeholder="e.g., 10.5"
                      value={manualInputs.Leucocyte}
                      onChange={handleInputChange}
                      onKeyPress={(e) => handleKeyPress(e, 'Leucocyte')}
                      required
                    />
                  </div>
                  <div className="input-group">
                    <label>Thrombocyte</label>
                    <input
                      type="number"
                      step="0.1"
                      name="Thrombocyte"
                      placeholder="e.g., 250"
                      value={manualInputs.Thrombocyte}
                      onChange={handleInputChange}
                      onKeyPress={(e) => handleKeyPress(e, 'Thrombocyte')}
                      required
                    />
                  </div>
                  <div className="input-group">
                    <label>Mch</label>
                    <input
                      type="number"
                      step="0.1"
                      name="Mch"
                      placeholder="e.g., 32.5"
                      value={manualInputs.Mch}
                      onChange={handleInputChange}
                      onKeyPress={(e) => handleKeyPress(e, 'Mch')}
                      required
                    />
                  </div>
                  <div className="input-group">
                    <label>Mchc</label>
                    <input
                      type="number"
                      step="0.1"
                      name="Mchc"
                      placeholder="e.g., 36.5"
                      value={manualInputs.Mchc}
                      onChange={handleInputChange}
                      onKeyPress={(e) => handleKeyPress(e, 'Mchc')}
                      required
                    />
                  </div>
                  <div className="input-group">
                    <label>Mcv</label>
                    <input
                      type="number"
                      step="0.1"
                      name="Mcv"
                      placeholder="e.g., 80"
                      value={manualInputs.Mcv}
                      onChange={handleInputChange}
                      onKeyPress={(e) => handleKeyPress(e, 'Mcv')}
                      required
                    />
                  </div>
                  <div className="input-group">
                    <label>Age</label>
                    <input
                      type="number"
                      step="1"
                      name="Age"
                      placeholder="e.g., 30"
                      value={manualInputs.Age}
                      onChange={handleInputChange}
                      onKeyPress={(e) => handleKeyPress(e, 'Age')}
                      required
                    />
                  </div>
                  <div className="input-group">
                    <label>Sex (1 for Male, 0 for Female)</label>
                    <input
                      type="text"
                      name="Sex"
                      placeholder="M for Male, F for Female"
                      value={manualInputs.Sex}
                      onChange={handleInputChange}
                      onKeyPress={(e) => handleKeyPress(e, 'Sex')}
                      required
                    />
                  </div>
                </div>
                <button
                  className="analyze-button"
                  type="submit"
                  disabled={!areAllInputsFilled() || isAnalyzing}
                >
                  {isAnalyzing ? (
                    <>
                      <span className="loading-spinner"></span>
                      Analyzing Values...
                    </>
                  ) : (
                    'Analyze Values'
                  )}
                </button>
              </form>
            </>
          )}
        </div>

        <div className="result-section">
          <div className="result-header">
            <h2>Prediction</h2>
            {prediction && isContentFullyTyped && (
              <button 
                className="download-button"
                onClick={downloadReport}
                title="Download Report"
              >
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/>
                  <polyline points="7 10 12 15 17 10"/>
                  <line x1="12" y1="15" x2="12" y2="3"/>
                </svg>
              </button>
            )}
          </div>
          {!prediction && (
            <p className="upload-message">
              Upload a PDF and click "Analyze Report" to see the prediction.
            </p>
          )}
          {prediction && prediction.status === 'success' && (
            <div className="prediction">
              <div 
                className="prediction-text"
                dangerouslySetInnerHTML={{ __html: displayedContent }}
              />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default MainApp; 