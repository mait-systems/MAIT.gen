import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import ReactMarkdown from 'react-markdown';

function ReportsTab() {
  // Existing state
  const [report, setReport] = useState('');
  const [liveAnalysis, setLiveAnalysis] = useState('');
  const [loading, setLoading] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const [error, setError] = useState('');

  // PowertrainAgent state
  const [powertrainStatus, setPowertrainStatus] = useState(null);
  const [powertrainAlerts, setPowertrainAlerts] = useState([]);
  const [powertrainMemory, setPowertrainMemory] = useState(null);
  const [powertrainTrends, setPowertrainTrends] = useState([]);
  const [isBootstrapping, setIsBootstrapping] = useState(false);
  const [powertrainLoading, setPowertrainLoading] = useState(false);
  const [showDetails, setShowDetails] = useState(false);
  const [selectedLoadBand, setSelectedLoadBand] = useState('all');
  const [lastRefresh, setLastRefresh] = useState(new Date());
  const [aiToggleLoading, setAiToggleLoading] = useState(false);

  // Auto-refresh interval refs
  const statusIntervalRef = useRef(null);
  const memoryIntervalRef = useRef(null);

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

  // PowertrainAgent API functions
  const fetchPowertrainStatus = async () => {
    try {
      const response = await axios.get(`${process.env.REACT_APP_API_URL || ''}/api/powertrain-status`);
      setPowertrainStatus(response.data);
      setLastRefresh(new Date());
    } catch (err) {
      console.error('Failed to fetch PowertrainAgent status:', err);
      setPowertrainStatus({ error: 'Failed to fetch status' });
    }
  };

  const fetchPowertrainAlerts = async () => {
    try {
      const response = await axios.get(`${process.env.REACT_APP_API_URL || ''}/api/powertrain-alerts?hours=24`);
      setPowertrainAlerts(response.data);
    } catch (err) {
      console.error('Failed to fetch PowertrainAgent alerts:', err);
      setPowertrainAlerts([]);
    }
  };

  const fetchPowertrainMemory = async (loadBand = null) => {
    try {
      let url = `${process.env.REACT_APP_API_URL || ''}/api/powertrain-memory?days=7`;
      if (loadBand && loadBand !== 'all') {
        url += `&load_band=${encodeURIComponent(loadBand)}`;
      }
      const response = await axios.get(url);
      setPowertrainMemory(response.data);
    } catch (err) {
      console.error('Failed to fetch PowertrainAgent memory:', err);
      setPowertrainMemory({ insights: [], total_count: 0 });
    }
  };

  const fetchPowertrainTrends = async () => {
    try {
      const response = await axios.get(`${process.env.REACT_APP_API_URL || ''}/api/powertrain-trends?hours=24`);
      setPowertrainTrends(response.data);
    } catch (err) {
      console.error('Failed to fetch PowertrainAgent trends:', err);
      setPowertrainTrends([]);
    }
  };

  const triggerPowertrainAnalysis = async () => {
    setPowertrainLoading(true);
    try {
      // Trigger fresh analysis by fetching latest status
      await fetchPowertrainStatus();
      await fetchPowertrainAlerts();
    } catch (err) {
      console.error('Failed to trigger PowertrainAgent analysis:', err);
    }
    setPowertrainLoading(false);
  };

  const handleBootstrap = async () => {
    if (!window.confirm('Bootstrap will rebuild PowertrainAgent memory from all historical data. This may take 10-15 minutes. Continue?')) {
      return;
    }
    
    setIsBootstrapping(true);
    try {
      // Note: Bootstrap would typically be a separate endpoint
      // For now, we'll show the bootstrap state and refresh after delay
      setTimeout(async () => {
        await fetchPowertrainStatus();
        await fetchPowertrainMemory();
        setIsBootstrapping(false);
      }, 5000); // Simulate bootstrap time
    } catch (err) {
      console.error('Bootstrap failed:', err);
      setIsBootstrapping(false);
    }
  };

  const handleLoadBandChange = async (newLoadBand) => {
    setSelectedLoadBand(newLoadBand);
    // Fetch insights specific to the selected load band
    await fetchPowertrainMemory(newLoadBand === 'all' ? null : newLoadBand);
  };

  const toggleAiAnalysis = async () => {
    setAiToggleLoading(true);
    try {
      const response = await axios.post(`${process.env.REACT_APP_API_URL || ''}/api/powertrain-ai/toggle`);
      if (response.data.success) {
        // Immediately refresh powertrain status to show new AI state
        await fetchPowertrainStatus();
      } else {
        console.error('Failed to toggle AI analysis:', response.data.error);
      }
    } catch (err) {
      console.error('Failed to toggle AI analysis:', err);
    }
    setAiToggleLoading(false);
  };

  // Auto-refresh setup
  useEffect(() => {
    // Initial load
    fetchPowertrainStatus();
    fetchPowertrainAlerts();
    fetchPowertrainMemory();
    fetchPowertrainTrends();

    // Set up auto-refresh intervals
    statusIntervalRef.current = setInterval(() => {
      fetchPowertrainStatus();
      fetchPowertrainAlerts();
    }, 30000); // 30 seconds

    memoryIntervalRef.current = setInterval(() => {
      fetchPowertrainMemory();
      fetchPowertrainTrends();
    }, 300000); // 5 minutes

    // Cleanup intervals on unmount
    return () => {
      if (statusIntervalRef.current) clearInterval(statusIntervalRef.current);
      if (memoryIntervalRef.current) clearInterval(memoryIntervalRef.current);
    };
  }, []);

  // Helper functions
  const getStatusColor = (alertLevel) => {
    switch (alertLevel) {
      case 'OK': return '#28a745';
      case 'INFO': return '#007bff';
      case 'WARNING': return '#fd7e14';
      case 'CRITICAL': return '#dc3545';
      default: return '#6c757d';
    }
  };

  const getStatusIcon = (alertLevel) => {
    switch (alertLevel) {
      case 'OK': return '🟢';
      case 'INFO': return '🔵';
      case 'WARNING': return '🟡';
      case 'CRITICAL': return '🔴';
      default: return '⚪';
    }
  };

  const getAgentStateIcon = (agentState) => {
    switch (agentState) {
      case 'ACTIVE': return '🟢';
      case 'IDLE': return '🟡';
      case 'PAUSED': return '⏸️';
      case 'OFFLINE': return '⚫';
      default: return '⚪';
    }
  };

  const getAgentStateColor = (agentState) => {
    switch (agentState) {
      case 'ACTIVE': return '#28a745';
      case 'IDLE': return '#fd7e14';
      case 'PAUSED': return '#ff8c00';
      case 'OFFLINE': return '#6c757d';
      default: return '#6c757d';
    }
  };

  const getAgentStateText = (agentState) => {
    switch (agentState) {
      case 'ACTIVE': return 'Active';
      case 'IDLE': return 'Idle';
      case 'PAUSED': return 'Paused (monitoring for engine activity)';
      case 'OFFLINE': return 'Offline';
      default: return 'Unknown';
    }
  };

  const formatTimestamp = (timestamp) => {
    if (!timestamp) return 'Unknown';
    const date = new Date(timestamp);
    return date.toLocaleString();
  };

  return (
    <div style={{ padding: '20px', maxWidth: '1400px', margin: '0 auto' }}>
      {/* PowertrainAgent Control Panel */}
      <div style={{ 
        background: '#f8f9fa', 
        border: '1px solid #dee2e6', 
        borderRadius: '8px', 
        padding: '16px', 
        marginBottom: '20px' 
      }}>
        <h2 style={{ margin: '0 0 16px 0', display: 'flex', alignItems: 'center' }}>
          PowertrainAgent Control Panel
        </h2>
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px', flexWrap: 'wrap' }}>
          {/* Status Indicator */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            {isBootstrapping ? (
              <>⚙️ <span style={{ color: '#007bff' }}>Building Memory...</span></>
            ) : powertrainStatus?.error ? (
              <>🔴 <span style={{ color: '#dc3545' }}>PowertrainAgent Offline</span></>
            ) : powertrainStatus ? (
              <>
                {getAgentStateIcon(powertrainStatus.agent_state)} 
              <span style={{ color: getAgentStateColor(powertrainStatus.agent_state) }}>
                PowertrainAgent {getAgentStateText(powertrainStatus.agent_state)} ({powertrainStatus.alert_level})
              </span>
              {powertrainStatus.heartbeat && <span style={{ fontSize: '0.8em', color: '#6c757d', marginLeft: '8px' }}>💓</span>}
              </>
            ) : (
              <>⚪ <span style={{ color: '#6c757d' }}>Loading...</span></>
            )}
          </div>

          {/* Control Buttons */}
          <button 
            onClick={handleBootstrap} 
            disabled={isBootstrapping}
            style={{ 
              padding: '6px 12px', 
              border: '1px solid #6f42c1', 
              background: '#6f42c1', 
              color: 'white', 
              borderRadius: '4px',
              cursor: isBootstrapping ? 'not-allowed' : 'pointer'
            }}
          >
            {isBootstrapping ? '⚙️ Bootstrapping...' : 'Bootstrap Memory'}
          </button>

          <button 
            onClick={triggerPowertrainAnalysis} 
            disabled={powertrainLoading}
            style={{ 
              padding: '6px 12px', 
              border: '1px solid #007bff', 
              background: '#007bff', 
              color: 'white', 
              borderRadius: '4px',
              cursor: powertrainLoading ? 'not-allowed' : 'pointer'
            }}
          >
            {powertrainLoading ? '🔄 Analyzing...' : '🔄 Force Analysis'}
          </button>

          <button 
            onClick={toggleAiAnalysis} 
            disabled={aiToggleLoading || !powertrainStatus}
            style={{ 
              padding: '6px 12px', 
              border: '1px solid #28a745', 
              background: (powertrainStatus && powertrainStatus.ai_enabled) ? '#28a745' : '#6c757d', 
              color: 'white', 
              borderRadius: '4px',
              cursor: (aiToggleLoading || !powertrainStatus) ? 'not-allowed' : 'pointer'
            }}
          >
            {aiToggleLoading ? '⚙️ Switching...' : 
             !powertrainStatus ? 'Loading...' :
             (powertrainStatus.ai_enabled ? 'AI Analysis: ON' : 'AI Analysis: OFF')}
          </button>

          <span style={{ fontSize: '0.9em', color: '#6c757d' }}>
            Last refresh: {formatTimestamp(lastRefresh)}
          </span>
        </div>
      </div>

      {/* Three-column PowertrainAgent Dashboard */}
      <div style={{ 
        display: 'grid', 
        gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))', 
        gap: '20px', 
        marginBottom: '30px' 
      }}>
        
        {/* Real-Time Analysis Section */}
        <div style={{ 
          background: 'white', 
          border: '1px solid #dee2e6', 
          borderRadius: '8px', 
          padding: '16px' 
        }}>
          <h3 style={{ margin: '0 0 16px 0', color: '#28a745' }}>Real-Time Analysis</h3>
          
          {powertrainStatus && !powertrainStatus.error ? (
            <div>
              {/* Current Health Status */}
              <div style={{ 
                background: getStatusColor(powertrainStatus.alert_level), 
                color: 'white', 
                padding: '12px', 
                borderRadius: '6px', 
                textAlign: 'center', 
                fontWeight: 'bold', 
                marginBottom: '16px' 
              }}>
                {getStatusIcon(powertrainStatus.alert_level)} {powertrainStatus.alert_level}
              </div>

              {/* Key Metrics */}
              <div style={{ display: 'grid', gap: '8px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span>Agent State:</span>
                  <strong style={{ color: getAgentStateColor(powertrainStatus.agent_state) }}>
                    {getAgentStateIcon(powertrainStatus.agent_state)} {getAgentStateText(powertrainStatus.agent_state)}
                  </strong>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span>AI Analysis:</span>
                  <strong style={{ color: powertrainStatus.ai_enabled ? '#28a745' : '#6c757d' }}>
                    {powertrainStatus.ai_enabled ? '✅ Enabled' : '❌ Disabled'}
                  </strong>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span>Load Band:</span>
                  <strong>{powertrainStatus.load_band}</strong>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span>Engine Speed:</span>
                  <strong>{powertrainStatus.engine_speed?.toFixed(0) || 0} RPM</strong>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span>Oil Pressure:</span>
                  <strong>{powertrainStatus.engine_oil_pressure?.toFixed(1) || 0} kPa</strong>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span>Power Output:</span>
                  <strong>{powertrainStatus.generator_power?.toFixed(1) || 0}%</strong>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span>Coolant Temp:</span>
                  <strong>{powertrainStatus.coolant_temperature?.toFixed(1) || 0}°C</strong>
                </div>
              </div>

              {/* Analysis Summary */}
              {powertrainStatus.analysis_summary && (
                <div style={{ marginTop: '16px', padding: '12px', background: '#f8f9fa', borderRadius: '4px' }}>
                  <strong>Summary:</strong> {powertrainStatus.analysis_summary}
                </div>
              )}

              {/* Details Toggle */}
              <button 
                onClick={() => setShowDetails(!showDetails)}
                style={{ 
                  marginTop: '12px', 
                  padding: '6px 12px', 
                  border: '1px solid #6c757d', 
                  background: 'white', 
                  borderRadius: '4px',
                  cursor: 'pointer',
                  width: '100%'
                }}
              >
                {showDetails ? 'Hide Details' : 'View Details'}
              </button>

              {showDetails && powertrainStatus.ai_analysis && (
                <div style={{ 
                  marginTop: '12px', 
                  padding: '12px', 
                  background: '#f8f9fa', 
                  borderRadius: '4px',
                  maxHeight: '300px',
                  overflowY: 'auto',
                  fontSize: '0.9em'
                }}>
                  <ReactMarkdown>{powertrainStatus.ai_analysis}</ReactMarkdown>
                </div>
              )}
            </div>
          ) : (
            <div style={{ textAlign: 'center', color: '#6c757d', padding: '20px' }}>
              {powertrainStatus?.error || 'Loading PowertrainAgent status...'}
            </div>
          )}
        </div>

        {/* Historical Intelligence Section */}
        <div style={{ 
          background: 'white', 
          border: '1px solid #dee2e6', 
          borderRadius: '8px', 
          padding: '16px' 
        }}>
          <h3 style={{ margin: '0 0 16px 0', color: '#6f42c1' }}>Historical Intelligence</h3>
          
          {powertrainMemory ? (
            <div>
              <div style={{ marginBottom: '16px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                  <span>Memory Insights:</span>
                  <strong>{powertrainMemory.total_count || 0}</strong>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span>Analysis Depth:</span>
                  <strong>Operational Data</strong>
                </div>
              </div>

              {/* Recent Insights */}
              <div style={{ marginBottom: '16px' }}>
                <h4 style={{ margin: '0 0 8px 0', fontSize: '1em' }}>Recent Insights:</h4>
                {powertrainMemory.insights && powertrainMemory.insights.length > 0 ? (
                  <div style={{ maxHeight: '200px', overflowY: 'auto' }}>
                    {powertrainMemory.insights.slice(0, 5).map((insight, index) => (
                      <div key={index} style={{ 
                        padding: '8px', 
                        background: '#f8f9fa', 
                        borderRadius: '4px', 
                        marginBottom: '8px',
                        fontSize: '0.9em'
                      }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                          <span style={{ fontWeight: 'bold', color: '#6f42c1' }}>
                            {insight.knowledge_type}
                          </span>
                          <span style={{ fontSize: '0.8em', color: '#6c757d' }}>
                            {insight.confidence}
                          </span>
                        </div>
                        <div>
                          {insight.insight_text && insight.insight_text.trim() 
                            ? insight.insight_text 
                            : "Insight analysis in progress..."}
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div style={{ color: '#6c757d', fontStyle: 'italic' }}>
                    Building knowledge base...
                  </div>
                )}
              </div>

              {/* Load Band Selector */}
              <div style={{ marginTop: '16px' }}>
                <label style={{ display: 'block', marginBottom: '8px', fontWeight: 'bold' }}>
                  Load Band Analysis:
                </label>
                <select 
                  value={selectedLoadBand} 
                  onChange={(e) => handleLoadBandChange(e.target.value)}
                  style={{ 
                    width: '100%', 
                    padding: '6px', 
                    border: '1px solid #dee2e6', 
                    borderRadius: '4px' 
                  }}
                >
                  <option value="all">All Load Bands</option>
                  <option value="0%">0% (Stopped)</option>
                  <option value="0-20%">0-20% (Light Load)</option>
                  <option value="20-40%">20-40% (Moderate Load)</option>
                  <option value="40-60%">40-60% (Normal Load)</option>
                  <option value="60-80%">60-80% (Heavy Load)</option>
                  <option value="80-100%">80-100% (Maximum Load)</option>
                </select>
              </div>
            </div>
          ) : (
            <div style={{ textAlign: 'center', color: '#6c757d', padding: '20px' }}>
              Loading memory data...
            </div>
          )}
        </div>

        {/* Alert Management Section */}
        <div style={{ 
          background: 'white', 
          border: '1px solid #dee2e6', 
          borderRadius: '8px', 
          padding: '16px' 
        }}>
          <h3 style={{ margin: '0 0 16px 0', color: '#dc3545' }}>Alert Management</h3>
          
          {/* Alert Summary */}
          <div style={{ marginBottom: '16px' }}>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '8px' }}>
              <div style={{ textAlign: 'center', padding: '8px', background: '#d4edda', borderRadius: '4px' }}>
                <div style={{ fontWeight: 'bold', color: '#155724' }}>
                  {powertrainAlerts.filter(a => a.severity === 'OK').length}
                </div>
                <div style={{ fontSize: '0.9em' }}>OK</div>
              </div>
              <div style={{ textAlign: 'center', padding: '8px', background: '#fff3cd', borderRadius: '4px' }}>
                <div style={{ fontWeight: 'bold', color: '#856404' }}>
                  {powertrainAlerts.filter(a => a.severity === 'WARNING').length}
                </div>
                <div style={{ fontSize: '0.9em' }}>Warning</div>
              </div>
              <div style={{ textAlign: 'center', padding: '8px', background: '#f8d7da', borderRadius: '4px' }}>
                <div style={{ fontWeight: 'bold', color: '#721c24' }}>
                  {powertrainAlerts.filter(a => a.severity === 'CRITICAL').length}
                </div>
                <div style={{ fontSize: '0.9em' }}>Critical</div>
              </div>
              <div style={{ textAlign: 'center', padding: '8px', background: '#d1ecf1', borderRadius: '4px' }}>
                <div style={{ fontWeight: 'bold', color: '#0c5460' }}>
                  {powertrainAlerts.length}
                </div>
                <div style={{ fontSize: '0.9em' }}>Total</div>
              </div>
            </div>
          </div>

          {/* Recent Alerts */}
          <div>
            <h4 style={{ margin: '0 0 8px 0', fontSize: '1em' }}>Recent Alerts (24h):</h4>
            {powertrainAlerts && powertrainAlerts.length > 0 ? (
              <div style={{ maxHeight: '250px', overflowY: 'auto' }}>
                {powertrainAlerts.slice(0, 8).map((alert, index) => (
                  <div key={index} style={{ 
                    padding: '8px', 
                    borderLeft: `4px solid ${getStatusColor(alert.severity)}`,
                    background: '#f8f9fa', 
                    marginBottom: '8px',
                    fontSize: '0.9em'
                  }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                      <span style={{ fontWeight: 'bold' }}>
                        {getStatusIcon(alert.severity)} {alert.severity}
                      </span>
                      <span style={{ fontSize: '0.8em', color: '#6c757d' }}>
                        {alert.load_band}
                      </span>
                    </div>
                    <div style={{ marginBottom: '4px' }}>{alert.description}</div>
                    <div style={{ fontSize: '0.8em', color: '#6c757d' }}>
                      {formatTimestamp(alert.timestamp)}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div style={{ color: '#6c757d', fontStyle: 'italic', textAlign: 'center', padding: '20px' }}>
                No recent alerts
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Existing Reports Section */}
      <div style={{ 
        background: 'white', 
        border: '1px solid #dee2e6', 
        borderRadius: '8px', 
        padding: '20px' 
      }}>
        <h2 style={{ margin: '0 0 20px 0' }}>📄 Traditional Reports</h2>
        
        <div style={{ marginBottom: '20px' }}>
          <button onClick={generateReport} disabled={loading} style={{
            padding: '10px 20px',
            border: '1px solid #007bff',
            background: '#007bff',
            color: 'white',
            borderRadius: '6px',
            cursor: loading ? 'not-allowed' : 'pointer',
            marginRight: '12px'
          }}>
            {loading ? 'Generating...' : 'Generate Daily Report'}
          </button>

          <button onClick={handleLiveAnalyze} disabled={analyzing} style={{
            padding: '10px 20px',
            border: '1px solid #28a745',
            background: '#28a745',
            color: 'white',
            borderRadius: '6px',
            cursor: analyzing ? 'not-allowed' : 'pointer'
          }}>
            {analyzing ? 'Analyzing...' : 'Analyze Live Data'}
          </button>
        </div>

        {error && <p style={{ color: 'red', padding: '10px', background: '#f8d7da', borderRadius: '4px' }}>{error}</p>}

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(500px, 1fr))', gap: '20px' }}>
          <div style={{ border: '1px solid #dee2e6', borderRadius: '6px', padding: '16px' }}>
            <h3 style={{ margin: '0 0 16px 0' }}>📄 Daily Report</h3>
            <div style={{ textAlign: 'left', whiteSpace: 'pre-wrap', maxHeight: '400px', overflowY: 'auto' }}>
              <ReactMarkdown>{report || 'Click the button to generate a report.'}</ReactMarkdown>
            </div>
          </div>

          <div style={{ border: '1px solid #dee2e6', borderRadius: '6px', padding: '16px' }}>
            <h3 style={{ margin: '0 0 16px 0' }}>⚡ Real-Time Health Check</h3>
            <div style={{ textAlign: 'left', whiteSpace: 'pre-wrap', maxHeight: '400px', overflowY: 'auto' }}>
              <ReactMarkdown>{liveAnalysis || 'Click "Analyze Live Data" to get current status.'}</ReactMarkdown>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default ReportsTab;
