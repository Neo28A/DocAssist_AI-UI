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

  const MIN_VALUES = {
    Hematocrit: 13.70,
    Hemoglobin: 3.80,
    Erythrocyte: 1.48,
    Leucocyte: 1.10,
    Thrombocyte: 8.00,
    Mch: 14.90,
    Mchc: 26.00,
    Mcv: 54.00,
    Age: 1.00
  };

  const MAX_VALUES = {
    Hematocrit: 69.00,
    Hemoglobin: 18.90,
    Erythrocyte: 7.86,
    Leucocyte: 76.60,
    Thrombocyte: 1183.00,
    Mch: 40.80,
    Mchc: 39.00,
    Mcv: 115.60,
    Age: 99.00
  };

  const toggleTheme = () => {
    setTheme(theme === 'light' ? 'dark' : 'light');
  };

  const resetPrediction = () => {
    setPrediction(null);
    setIsTyping(false);
    setIsContentFullyTyped(false);
    setDisplayedContent('');
  };

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
    resetPrediction();
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
    const { name, value } = e.target;
    
    // For Sex field, convert to uppercase immediately
    if (name === 'Sex') {
      setManualInputs(prev => ({
        ...prev,
        [name]: value.toUpperCase()
      }));
      return;
    }

    setManualInputs(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleInputBlur = (e) => {
    const { name, value } = e.target;
    
    if (!value) return; // Skip validation if empty

    // Validate Sex field
    if (name === 'Sex') {
      const upperValue = value.toUpperCase();
      if (!['M', 'F'].includes(upperValue)) {
        alert('Please enter only M or F for Sex');
        setManualInputs(prev => ({
          ...prev,
          [name]: ''
        }));
      }
      return;
    }

    // Validate numeric fields
    const numValue = parseFloat(value);
    if (numValue < MIN_VALUES[name] || numValue > MAX_VALUES[name]) {
      alert(`Please enter a value between ${MIN_VALUES[name]} and ${MAX_VALUES.Age} for ${name}`);
      setManualInputs(prev => ({
        ...prev,
        [name]: ''
      }));
    }
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

  const handleMethodSelection = (method) => {
    resetPrediction();
    setInputMethod(method);
  };

  const handleBackClick = () => {
    resetPrediction();
    setInputMethod(null);
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
        <div className="input-section" style={{ minHeight: '800px' }}>
          <div className="section-header">
            <button className="back-btn" onClick={handleBackClick}>
              <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M19 12H5M12 19l-7-7 7-7" />
              </svg>
              Back
            </button>
            <h2>{inputMethod === 'upload' ? 'Upload Blood Report' : 'Enter Blood Values'}</h2>
          </div>
          
          {!inputMethod && (
            <div className="method-selection">
              <button className="method-btn" onClick={() => handleMethodSelection('upload')}>
                <svg className="method-btn-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4M17 8l-5-5-5 5M12 3v12" />
                </svg>
                <span className="method-btn-text">Upload PDF Report</span>
              </button>
              <button className="method-btn" onClick={() => handleMethodSelection('manual')}>
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
                      placeholder={`${MIN_VALUES.Hematocrit} - ${MAX_VALUES.Hematocrit}`}
                      value={manualInputs.Hematocrit}
                      onChange={handleInputChange}
                      onBlur={handleInputBlur}
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
                      placeholder={`${MIN_VALUES.Hemoglobin} - ${MAX_VALUES.Hemoglobin}`}
                      value={manualInputs.Hemoglobin}
                      onChange={handleInputChange}
                      onBlur={handleInputBlur}
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
                      placeholder={`${MIN_VALUES.Erythrocyte} - ${MAX_VALUES.Erythrocyte}`}
                      value={manualInputs.Erythrocyte}
                      onChange={handleInputChange}
                      onBlur={handleInputBlur}
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
                      placeholder={`${MIN_VALUES.Leucocyte} - ${MAX_VALUES.Leucocyte}`}
                      value={manualInputs.Leucocyte}
                      onChange={handleInputChange}
                      onBlur={handleInputBlur}
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
                      placeholder={`${MIN_VALUES.Thrombocyte} - ${MAX_VALUES.Thrombocyte}`}
                      value={manualInputs.Thrombocyte}
                      onChange={handleInputChange}
                      onBlur={handleInputBlur}
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
                      placeholder={`${MIN_VALUES.Mch} - ${MAX_VALUES.Mch}`}
                      value={manualInputs.Mch}
                      onChange={handleInputChange}
                      onBlur={handleInputBlur}
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
                      placeholder={`${MIN_VALUES.Mchc} - ${MAX_VALUES.Mchc}`}
                      value={manualInputs.Mchc}
                      onChange={handleInputChange}
                      onBlur={handleInputBlur}
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
                      placeholder={`${MIN_VALUES.Mcv} - ${MAX_VALUES.Mcv}`}
                      value={manualInputs.Mcv}
                      onChange={handleInputChange}
                      onBlur={handleInputBlur}
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
                      placeholder={`${MIN_VALUES.Age} - ${MAX_VALUES.Age}`}
                      value={manualInputs.Age}
                      onChange={handleInputChange}
                      onBlur={handleInputBlur}
                      onKeyPress={(e) => handleKeyPress(e, 'Age')}
                      required
                    />
                  </div>
                  <div className="input-group">
                    <label>Sex (M for Male, F for Female)</label>
                    <input
                      type="text"
                      name="Sex"
                      placeholder="M or F"
                      value={manualInputs.Sex}
                      onChange={handleInputChange}
                      onBlur={handleInputBlur}
                      onKeyPress={(e) => handleKeyPress(e, 'Sex')}
                      maxLength="1"
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

        <div className="result-section" style={{ minHeight: '800px' }}>
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