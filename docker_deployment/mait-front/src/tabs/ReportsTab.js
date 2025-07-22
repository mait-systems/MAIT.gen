import React, { useState } from 'react';
import axios from 'axios';
import ReactMarkdown from 'react-markdown';

function ReportsTab() {
  const [report, setReport] = useState('');
  const [liveAnalysis, setLiveAnalysis] = useState('');
  const [loading, setLoading] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const [error, setError] = useState('');

  const generateReport = async () => {
    setLoading(true);
    setError('');
    try {
      const response = await axios.get(`${process.env.REACT_APP_API_URL || ''}/api/generate-daily-report`);
      setReport(response.data.report);
    } catch (err) {
      console.error(err);
      setError('Failed to generate report.');
    }
    setLoading(false);
  };

  const handleLiveAnalyze = async () => {
    setAnalyzing(true);
    setError('');
    try {
      const response = await axios.get(`${process.env.REACT_APP_API_URL || ''}/api/live-analysis`);
      setLiveAnalysis(response.data.analysis);
    } catch (err) {
      console.error(err);
      setError('Failed to analyze live data.');
    }
    setAnalyzing(false);
  };

  return (
    <div>
      <button onClick={generateReport} disabled={loading}>
        {loading ? 'Generating...' : 'Generate Daily Report'}
      </button>

      <button onClick={handleLiveAnalyze} disabled={analyzing} style={{ marginLeft: '12px' }}>
        {analyzing ? 'Analyzing...' : 'Analyze Live Data'}
      </button>

      {error && <p style={{ color: 'red' }}>{error}</p>}

      <div className="report-box" style={{ textAlign: 'left', whiteSpace: 'pre-wrap', marginTop: '20px' }}>
        <h3>📄 Daily Report</h3>
        <ReactMarkdown>{report || 'Click the button to generate a report.'}</ReactMarkdown>
      </div>

      <div className="report-box" style={{ textAlign: 'left', whiteSpace: 'pre-wrap', marginTop: '20px' }}>
        <h3>⚡ Real-Time Health Check</h3>
        <ReactMarkdown>{liveAnalysis || 'Click "Analyze Live Data" to get current status.'}</ReactMarkdown>
      </div>
    </div>
  );
}

export default ReportsTab;
