import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';

function AnalysisTab() {
  // PowertrainAgent state
  const [powertrainStatus, setPowertrainStatus] = useState(null);
    const [powertrainMemory, setPowertrainMemory] = useState(null);
  const [selectedFrequency, setSelectedFrequency] = useState(5);
  const [lastRefresh, setLastRefresh] = useState(new Date());
  
  // New statistical analysis data
  const [localAnalysis, setLocalAnalysis] = useState(null);
  const [baselineData, setBaselineData] = useState(null);
  const [localAlerts, setLocalAlerts] = useState([]);
  const [aiAlerts, setAiAlerts] = useState([]);
  const [analysisSections, setAnalysisSections] = useState(null);
const parseAnalysisSections = (sections, fallbackSummary) => {
  let parsed = sections;
  if (!parsed) {
    parsed = {};
  }
  if (typeof parsed === 'string') {
    try {
      parsed = JSON.parse(parsed);
    } catch {
      parsed = {};
    }
  }
  return {
    summary: parsed.summary || fallbackSummary || 'Awaiting AI analysis...',
    trend_analysis: parsed.trend_analysis || [],
    recommendations: parsed.recommendations || [],
    memory_notes: parsed.memory_notes || [],
    extra: parsed.extra || []
  };
};

  //Unified AI Analysis Button
  const [aiCheckStatus, setAiCheckStatus] = useState('idle'); // idle | running | success | failed
  const [aiCheckMessage, setAiCheckMessage] = useState('AI Analysis');
  const [globalAiEnabled, setGlobalAiEnabled] = useState(false);

  // Collapsible sections state
  const [powertrainExpanded, setPowertrainExpanded] = useState(true);
  const [aiAnalysisExpanded, setAiAnalysisExpanded] = useState(false);

  // Auto-refresh interval refs
  const statusIntervalRef = useRef(null);
  const memoryIntervalRef = useRef(null);
  const healthIntervalRef = useRef(null);


  // PowertrainAgent API functions
  const fetchPowertrainStatus = async () => {
    try {
      const response = await axios.get(`${process.env.REACT_APP_API_URL || ''}/api/powertrain-status`);
      const newStatus = response.data;
      
      // No complex state management needed - button mirrors gateway status automatically
      
      setPowertrainStatus(newStatus);
      setAiAlerts(newStatus.alerts || []);
      setAnalysisSections(parseAnalysisSections(newStatus.analysis_sections, newStatus.analysis_summary));
      setLastRefresh(new Date());
    } catch (err) {
      console.error('Failed to fetch PowertrainAgent status:', err);
      setPowertrainStatus({ error: 'Failed to fetch status' });
      setAiAlerts([]);
      setAnalysisSections(null);
    }
  };

  const fetchPowertrainMemory = async () => {
    try {
      const url = `${process.env.REACT_APP_API_URL || ''}/api/powertrain-memory?days=7`;
      const response = await axios.get(url);
      setPowertrainMemory(response.data);
    } catch (err) {
      console.error('Failed to fetch PowertrainAgent memory:', err);
      setPowertrainMemory({ insights: [], total_count: 0 });
    }
  };

  const fetchLocalAnalysis = async () => {
    try {
      const response = await axios.get(`${process.env.REACT_APP_API_URL || ''}/api/powertrain-local-analysis`);
      setLocalAnalysis(response.data);
      const alerts = response.data?.alerts || [];
      setLocalAlerts(alerts);
    } catch (err) {
      console.error('Failed to fetch local analysis:', err);
      setLocalAnalysis(null);
      setLocalAlerts([]);
    }
  };

  const fetchBaselines = async (loadBand) => {
    try {
      const response = await axios.get(`${process.env.REACT_APP_API_URL || ''}/api/powertrain-baselines?load_band=${encodeURIComponent(loadBand)}`);
      const data = response.data;
      setBaselineData(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error('Failed to fetch baselines:', err);
      setBaselineData([]);
    }
  };

  const fetchGlobalAiStatus = async () => {
    try {
      const response = await axios.get(`${process.env.REACT_APP_API_URL || ''}/api/ai/status`);
      const aiEnabled = response.data.ai_enabled;
      setGlobalAiEnabled(response.data.ai_enabled);
      
      // Sync button state with global AI status
      if (aiEnabled) {
        setAiCheckStatus('success');
        setAiCheckMessage('✅ AI Analysis ON');
      } else {
        setAiCheckStatus('idle');
        setAiCheckMessage('AI Analysis');
      }

    } catch (err) {
      console.error('Failed to fetch global AI status:', err);
      setGlobalAiEnabled(false);
    }
  };

  useEffect(() => {
    if (globalAiEnabled) {
      setAiAnalysisExpanded(true);
    } else {
      setAiAnalysisExpanded(false);
    }
  }, [globalAiEnabled]);

  const handleAiSectionToggle = () => {
    if (!globalAiEnabled) {
      return;
    }
    setAiAnalysisExpanded(prev => !prev);
  };


  const updateFrequency = async (newFrequency) => {
    try {
      const response = await axios.post(`${process.env.REACT_APP_API_URL || ''}/api/agents/ai-frequency`, {
        frequency: newFrequency
      });
      if (response.data.success) {
        setSelectedFrequency(newFrequency);
        // Refresh status to show updated frequency
        await fetchPowertrainStatus();
      } else {
        console.error('Failed to update frequency:', response.data.error);
      }
    } catch (err) {
      console.error('Failed to update frequency:', err);
    }
  };




  // Unified AI Analysis button: Step Execution Function
  const runAiAnalysisCheck = async () => {
  setAiCheckStatus('running');

  const steps = [
    { label: 'Pinging Gateway', fn: pingGatewayTest },
    { label: 'Testing Memory', fn: testMemoryCheck },
    { label: 'Checking Builder', fn: testPromptBuilderCheck },
    { label: 'Testing AI', fn: testAiCheck }
  ];

  for (const step of steps) {
    setAiCheckMessage(step.label);
    await new Promise(r => setTimeout(r, 1000));

    const success = await step.fn();
    if (!success) {
      setAiCheckStatus('failed');
      setAiCheckMessage(`${step.label.replace('...', '')} Failed`);
      setTimeout(() => {
        setAiCheckStatus('idle');
        setAiCheckMessage('AI Analysis');
      }, 5000);
      return;
    }
  }

  // All passed
  setAiCheckStatus('success');
  setAiCheckMessage('✅ AI Analysis ON');
  await axios.post(`${process.env.REACT_APP_API_URL}/api/ai/toggle`);
  setGlobalAiEnabled(true); // for immediate dropdown list show up
  
  // Start health monitoring after successful activation
  startHealthMonitoring();
};

  // Unified AI Analysis button: Each Step’s Test Function
  const pingGatewayTest = async () => {
  try {
    const res = await axios.get(`${process.env.REACT_APP_API_URL}/api/gateway-ping`);
    return res.data.status === 'OK';
  } catch {
    return false;
  }
};

const testMemoryCheck = async () => {
  try {
    const res = await axios.get(`${process.env.REACT_APP_API_URL}/api/gateway-health`);
    return res.data.memory_manager === 'OK';
  } catch {
    return false;
  }
};

const testPromptBuilderCheck = async () => {
  try {
    const res = await axios.get(`${process.env.REACT_APP_API_URL}/api/gateway-prompt-health`);
    return res.data.status === 'OK';
  } catch {
    return false;
  }
};

const testAiCheck = async () => {
  try {
    const res = await axios.get(`${process.env.REACT_APP_API_URL}/api/gateway-ai-health`);
    return res.data.status === 'OK';
  } catch {
    return false;
  }
};


const handleAiButtonClick = async () => {
  if (aiCheckStatus === 'success' || aiCheckStatus === 'failed') {
    // When AI is ON (success state), toggle it OFF
    if (aiCheckStatus === 'success') {
      try {
        await axios.post(`${process.env.REACT_APP_API_URL}/api/ai/toggle`);
        setGlobalAiEnabled(false);
        // Stop health monitoring when turning AI off
        stopHealthMonitoring();
      } catch (error) {
        console.error('Failed to toggle AI OFF:', error);
      }
    }
    // Reset to initial idle state
    setAiCheckStatus('idle');
    setAiCheckMessage('AI Analysis');
  } else {
    runAiAnalysisCheck();
  }
};

  // Health monitoring functions
  const startHealthMonitoring = () => {
    healthIntervalRef.current = setInterval(async () => {
      try {
        const response = await axios.get(`${process.env.REACT_APP_API_URL || ''}/api/gateway-health`, {
          timeout: 10000
        });
        
        if (response.data && response.data.memory_manager !== 'OK') {
          // Health failed - disable AI
          console.log('Gateway health check failed - disabling AI');
          await axios.post(`${process.env.REACT_APP_API_URL || ''}/api/ai/toggle`);
          setGlobalAiEnabled(false);
          stopHealthMonitoring();
          // Reset AI button state
          setAiCheckStatus('idle');
          setAiCheckMessage('AI Analysis');
        }
      } catch (err) {
        // Gateway unreachable - disable AI
        console.log('Gateway unreachable - disabling AI');
        await axios.post(`${process.env.REACT_APP_API_URL || ''}/api/ai/toggle`);
        setGlobalAiEnabled(false);
        stopHealthMonitoring();
        // Reset AI button state
        setAiCheckStatus('idle');
        setAiCheckMessage('AI Analysis');
      }
    }, 60000); // Check every minute
  };

  const stopHealthMonitoring = () => {
    if (healthIntervalRef.current) {
      clearInterval(healthIntervalRef.current);
      healthIntervalRef.current = null;
    }
  };

  // Update frequency when powertrainStatus changes
  useEffect(() => {
    if (powertrainStatus && powertrainStatus.frequency) {
      setSelectedFrequency(powertrainStatus.frequency);
    }
  }, [powertrainStatus]);

  // Fetch baselines when local analysis changes (to get matching load band)
  useEffect(() => {
    if (!localAnalysis) return;
    const band = localAnalysis.current_load_band || localAnalysis.load_band;
    if (band) {
      fetchBaselines(band);
    }
  }, [localAnalysis]);

  // Auto-refresh setup
  useEffect(() => {
    // Initial load
    fetchPowertrainStatus();
    fetchPowertrainMemory();
    fetchGlobalAiStatus();
    fetchLocalAnalysis();

    // Set up auto-refresh intervals
    statusIntervalRef.current = setInterval(() => {
      fetchPowertrainStatus();
        fetchGlobalAiStatus();
      fetchLocalAnalysis();
    }, 10000); // 10 seconds - matches agent heartbeat frequency

    memoryIntervalRef.current = setInterval(() => {
      fetchPowertrainMemory();
    }, 300000); // 5 minutes

    // Cleanup intervals on unmount
    return () => {
      if (statusIntervalRef.current) clearInterval(statusIntervalRef.current);
      if (memoryIntervalRef.current) clearInterval(memoryIntervalRef.current);
      if (healthIntervalRef.current) clearInterval(healthIntervalRef.current);
    };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const getAgentStateColor = (agentState) => {
    switch (agentState) {
      case 'ACTIVE': return '#28a745';
      case 'PAUSED': return '#ff8c00';
      case 'OFFLINE': return '#6c757d';
      default: return '#6c757d';
    }
  };

  const getAgentStateText = (agentState) => {
    switch (agentState) {
      case 'ACTIVE': return 'Active';
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

  const getInsightSourceTag = (insight) => {
    // Check if insight contains statistical indicators
    if (insight.insight_text && (
      insight.insight_text.includes('R²=') || 
      insight.insight_text.includes('trend in') ||
      insight.insight_text.includes('load band')
    )) {
      return 'STAT: ';
    }
    
    // Do not prefix non-statistical insights
    return '';
  };

  // Statistical comparison table component
  const renderStatisticalTable = () => {
    if (!localAnalysis || !Array.isArray(baselineData) || baselineData.length === 0) {
      return (
        <div style={{ textAlign: 'center', color: '#6c757d', padding: '20px' }}>
          Loading statistical analysis...
        </div>
      );
    }

    const baseline = baselineData[0]; // Use most recent baseline
    if (!baseline) {
      return (
        <div style={{ textAlign: 'center', color: '#6c757d', padding: '20px' }}>
          No baseline data available yet.
        </div>
      );
    }
    const hasLiveMetrics = localAnalysis.live_metrics && Object.keys(localAnalysis.live_metrics).length > 0;
    const metrics = hasLiveMetrics
      ? { ...(localAnalysis.analysis_metrics_snapshot || {}), ...localAnalysis.live_metrics }
      : (localAnalysis.current_metrics || {});
    
    // Define metrics to display with their display names and units
    const metricsToShow = [
      { key: 'engine_speed', label: 'Engine Speed', unit: 'RPM', baselineKey: 'avg_engine_speed', stddevKey: 'stddev_engine_speed' },
      { key: 'engine_oil_pressure', label: 'Oil Pressure', unit: 'kPa', baselineKey: 'avg_oil_pressure', stddevKey: 'stddev_oil_pressure' },
      { key: 'coolant_temperature', label: 'Coolant Temp', unit: '°C', baselineKey: 'avg_coolant_temperature', stddevKey: 'stddev_coolant_temperature' },
      { key: 'engine_fuel_pressure', label: 'Fuel Pressure', unit: 'kPa', baselineKey: 'avg_fuel_pressure', stddevKey: 'stddev_fuel_pressure' },
      { key: 'engine_fuel_rate', label: 'Fuel Rate', unit: 'l/hr', baselineKey: 'avg_fuel_rate', stddevKey: 'stddev_fuel_rate' },
      { key: 'engine_fuel_temperature', label: 'Fuel Temp', unit: '°C', baselineKey: 'avg_fuel_temperature', stddevKey: 'stddev_fuel_temperature' },
      { key: 'intake_air_temperature', label: 'Intake Air Temp', unit: '°C', baselineKey: 'avg_intake_air_temperature', stddevKey: 'stddev_intake_air_temperature' },
      { key: 'intake_air_pressure', label: 'Intake Air Pressure', unit: 'kPa', baselineKey: 'avg_intake_air_pressure', stddevKey: 'stddev_intake_air_pressure' }
    ];

    const getStatusColor = (alertColor) => {
      switch (alertColor) {
        case 'green': return '#28a745';
        case 'yellow': return '#ffc107';
        case 'red': return '#dc3545';
        default: return '#6c757d';
      }
    };

    const getStatusIcon = (alertColor) => {
      switch (alertColor) {
        case 'green': return '🟢';
        case 'yellow': return '🟡';
        case 'red': return '🔴';
        default: return '⚪';
      }
    };

    return (
      <div>
        <table style={{ width: '100%', borderCollapse: 'collapse', marginTop: '16px' }}>
          <thead>
            <tr style={{ backgroundColor: '#f8f9fa' }}>
              <th style={{ padding: '12px 8px', textAlign: 'left', border: '1px solid #dee2e6', fontWeight: 'bold' }}>Metric</th>
              <th style={{ padding: '12px 8px', textAlign: 'center', border: '1px solid #dee2e6', fontWeight: 'bold' }}>Current</th>
              <th style={{ padding: '12px 8px', textAlign: 'center', border: '1px solid #dee2e6', fontWeight: 'bold' }}>Baseline±σ</th>
              <th style={{ padding: '12px 8px', textAlign: 'center', border: '1px solid #dee2e6', fontWeight: 'bold' }}>Status</th>
            </tr>
          </thead>
          <tbody>
            {metricsToShow.map((metric) => {
              const current = metrics[metric.key] || 0;
              const baselineAvg = baseline[metric.baselineKey] || 0;
              const baselineStddev = baseline[metric.stddevKey] || 0;
              const deviation = baselineStddev > 0 ? Math.abs(current - baselineAvg) / baselineStddev : 0;
              
              let status = 'Normal';
              let statusColor = 'green';
              if (deviation > 3) {
                status = 'Critical';
                statusColor = 'red';
              } else if (deviation > 2) {
                status = 'Warning';
                statusColor = 'yellow';
              }

              return (
                <tr key={metric.key}>
                  <td style={{ padding: '8px', border: '1px solid #dee2e6' }}>{metric.label}</td>
                  <td style={{ padding: '8px', border: '1px solid #dee2e6', textAlign: 'center', fontWeight: 'bold' }}>
                    {current.toFixed(1)} {metric.unit}
                  </td>
                  <td style={{ padding: '8px', border: '1px solid #dee2e6', textAlign: 'center' }}>
                    {baselineAvg.toFixed(1)}±{baselineStddev.toFixed(1)} {metric.unit}
                  </td>
                  <td style={{ padding: '8px', border: '1px solid #dee2e6', textAlign: 'center', color: getStatusColor(statusColor) }}>
                    {getStatusIcon(statusColor)} {status} ({deviation > 0 ? `${deviation.toFixed(1)}σ` : '0σ'})
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    );
  };




  const getBootstrapStatusColor = (status) => {
    switch (status) {
      case 'complete': return '#28a745';  // Green
      case 'in_progress': return '#fd7e14';  // Orange
      case 'needed': return '#6c757d';  // Gray
      case 'completed_no_baselines': return '#dc3545';  // Red
      case 'unknown': return '#6c757d';  // Gray
      default: return '#6c757d';
    }
  };

  
  const getBootstrapStatusDisplay = (status) => {
    if (!status) return '⚪ Unknown';
    
    const { bootstrap_status, bootstrap_progress, baseline_count, bootstrap_timestamp, agent_state } = status;
    
    // Calculate time since bootstrap
    const getTimeSince = (timestamp) => {
      if (!timestamp) return '';
      const now = new Date();
      const past = new Date(timestamp);
      const diffHours = Math.floor((now - past) / (1000 * 60 * 60));
      const diffDays = Math.floor(diffHours / 24);
      
      if (diffDays > 0) return `${diffDays}d ago`;
      if (diffHours > 0) return `${diffHours}h ago`;
      return 'Just completed';
    };

    switch (bootstrap_status) {
      case 'complete':
        return `🟢 Complete (${baseline_count} baselines) - ${getTimeSince(bootstrap_timestamp)}`;
      case 'in_progress':
        return `🟡 In Progress - ${bootstrap_progress.toFixed(0)}%`;
      case 'needed':
        // Context-aware message based on agent state
        if (agent_state === 'PAUSED') {
          return `⚪ Needed - Will auto-start when agent resumes`;
        } else {
          return `⚪ Needed - Will auto-start on next analysis`;
        }
      case 'completed_no_baselines':
        return `🔴 Failed - No baselines created`;
      case 'unknown':
        return `⚪ Unknown - Checking status...`;
      default:
        return `⚪ Unknown status: ${bootstrap_status}`;
    }
  };

  return (
    <div style={{ padding: '10px 20px 20px 20px', maxWidth: '1400px', margin: '0 auto' }}>
      
      {/* Global AI Control */}
      <div style={{ 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center', 
        gap: '20px', 
        flexWrap: 'wrap',
        marginBottom: '10px'
      }}>
        <button
          onClick={handleAiButtonClick}
          disabled={aiCheckStatus === 'running'}
          style={{
            padding: '8px 16px',
            border: `2px solid ${
              aiCheckStatus === 'success'
                  ? '#28a745' // success green
                  : aiCheckStatus === 'running'
                  ? '#ffc107' // warning yellow
                  : aiCheckStatus === 'failed'
                  ? '#dc3545' // danger red
                  : '#007bff' // idle blue border
              }`,
              background: 
                aiCheckStatus === 'success'
                  ? '#28a745'
                  : aiCheckStatus === 'running'
                  ? '#ffc107'
                  : aiCheckStatus === 'failed'
                  ? '#dc3545'
                  : 'white',
              color: aiCheckStatus === 'idle' ? '#007bff' : 'white',
              borderRadius: '8px',
              cursor: aiCheckStatus === 'running' ? 'not-allowed' : 'pointer',
              fontSize: '1em',
              fontWeight: 'bold',
              minWidth: '160px',
              transition: 'all 0.3s ease',
              boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)',
              transform: aiCheckStatus === 'running' ? 'scale(0.98)' : 'scale(1)'
            }}
          >
            {aiCheckMessage}
        </button>

        {/* AI Analysis Frequency Selector */}
        {globalAiEnabled && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <label style={{ fontSize: '1em', color: '#495057', fontWeight: '500' }}>Analysis Frequency:</label>
            <select 
              value={selectedFrequency}
              onChange={(e) => updateFrequency(parseInt(e.target.value))}
              style={{ 
                padding: '8px 12px', 
                border: '1px solid #ced4da', 
                borderRadius: '4px',
                fontSize: '1em',
                fontWeight: '500',
                background: 'white',
                color: '#495057'
              }}
            >
              <option value={1}>1 minute</option>
              <option value={3}>3 minutes</option>
              <option value={5}>5 minutes</option>
              <option value={10}>10 minutes</option>
              <option value={15}>15 minutes</option>
              <option value={30}>30 minutes</option>
            </select>
          </div>
        )}
      </div>
      
      {/* Agent Management Section */}
      <div style={{ marginBottom: '30px' }}>
        
        {/* PowertrainAgent Control Panel */}
        <div style={{ 
          background: '#f8f9fa', 
          border: '1px solid #dee2e6', 
          borderRadius: '8px', 
          padding: '16px', 
          marginBottom: '20px' 
        }}>
          <div style={{ 
            display: 'flex', 
            justifyContent: 'space-between', 
            alignItems: 'center',
            marginBottom: powertrainExpanded ? '16px' : '0',
            minHeight: '48px'
          }}>
            <h2 style={{ margin: '0', flex: '0 0 auto' }}>
              Powertrain Agent
            </h2>
            <div style={{ flex: '1', display: 'flex', justifyContent: 'center' }}>
              {powertrainStatus?.error ? (
                <>🔴 <span style={{ color: '#dc3545', fontWeight: 'normal' }}>Offline</span></>
              ) : powertrainStatus ? (
                <span style={{ color: getAgentStateColor(powertrainStatus.agent_state), fontWeight: 'normal' }}>
                  {getAgentStateText(powertrainStatus.agent_state)}{powertrainStatus.heartbeat && ' 💓'}
                </span>
              ) : (
                <>⚪ <span style={{ color: '#6c757d', fontWeight: 'normal' }}>Loading...</span></>
              )}
            </div>                        
            <button
              onClick={() => setPowertrainExpanded(!powertrainExpanded)}
              style={{
                padding: '6px 12px',
                border: '1px solid #007bff',
                background: 'white',
                color: '#007bff',
                borderRadius: '4px',
                cursor: 'pointer',
                fontSize: '0.9em'
              }}
            >
              {powertrainExpanded ? 'Show Less' : 'See More'}
            </button>
          </div>
          
          
          {/* Collapsible PowertrainAgent Details */}
          {powertrainExpanded && (
            <div style={{ 
              marginTop: '20px',
              display: 'flex',
              flexDirection: 'column',
              gap: '20px'
            }}>
              
              {/* Agent Details Section */}
              <div style={{ 
                background: 'white', 
                border: '1px solid #dee2e6', 
                borderRadius: '8px', 
                padding: '16px' 
              }}>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '16px', fontSize: '0.9em' }}>
                  
                  {/* Last Refresh */}
                  <div>
                    <div style={{ fontWeight: 'bold', marginBottom: '4px' }}>Last Refresh:</div>
                    <div style={{ color: '#6c757d' }}>{formatTimestamp(lastRefresh)}</div>
                  </div>
                  
                  {/* Memory Status */}
                  <div>
                    <div style={{ fontWeight: 'bold', marginBottom: '4px' }}>Memory System:</div>
                    {powertrainStatus ? (
                      <div style={{ color: getBootstrapStatusColor(powertrainStatus.bootstrap_status) }}>
                        {getBootstrapStatusDisplay(powertrainStatus)}
                      </div>
                    ) : (
                      <div style={{ color: '#6c757d' }}>Loading...</div>
                    )}
                  </div>
                  
                  {/* Analysis Frequency */}
                  <div>
                    <div style={{ fontWeight: 'bold', marginBottom: '4px' }}>Analysis Frequency:</div>
                    <div style={{ color: '#007bff' }}>Every {selectedFrequency} minutes</div>
                  </div>
                  
                </div>
              </div>
              
              {/* Row 1: Statistical Analysis */}
              <div style={{ 
                background: 'white', 
                border: '1px solid #dee2e6', 
                borderRadius: '8px', 
                padding: '16px' 
              }}>
                <h3 style={{ margin: '0 0 16px 0', color: '#333' }}>
                  Local Statistical Analysis {localAnalysis ? `(Current Load Band: ${localAnalysis.current_load_band || localAnalysis.load_band})` : ''}
                </h3>
                
                <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: '12px', marginBottom: '12px' }}>
                  {/* Latest Local Alerts */}
                  <div style={{ padding: '10px', background: '#f8f9fa', borderRadius: '6px' }}>
                    <div style={{ fontWeight: 'bold', marginBottom: '6px', textAlign: 'center' }}>Latest Local Alerts</div>
                    {localAlerts && localAlerts.length > 0 ? (
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                        {localAlerts.map((alert, idx) => (
                          <div key={idx} style={{ fontSize: '0.9em', color: '#333' }}>
                            <strong>{alert.level || alert.severity || 'INFO'}:</strong> {alert.message || alert.description || 'Alert detected'}
                          </div>
                        ))}
                      </div>
                    ) : (
                      <div style={{ fontSize: '0.9em', color: '#6c757d', fontStyle: 'italic' }}>
                        No alerts in the latest local analysis
                      </div>
                    )}
                  </div>
                </div>
                
                {renderStatisticalTable()}
              </div>

            </div>
          )}
        </div>
      </div>

      {/* AI Analysis Section */}
      <div style={{ marginBottom: '30px' }}>
        <div style={{ 
          background: '#f8f9fa', 
          border: '1px solid #dee2e6', 
          borderRadius: '8px', 
          padding: '16px'
        }}>
          <div style={{ 
            display: 'flex', 
            justifyContent: 'space-between', 
            alignItems: 'center',
            marginBottom: aiAnalysisExpanded ? '16px' : '0',
            minHeight: '48px'
          }}>
            <h2 style={{ margin: '0', flex: '0 0 auto' }}>AI Analysis</h2>
            <div style={{ 
              flex: '1', 
              display: 'flex', 
              justifyContent: 'center', 
              fontWeight: 'normal',
              color: globalAiEnabled ? '#28a745' : '#6c757d'
            }}>
              {globalAiEnabled ? 'Enabled' : 'Disabled'}
            </div>
            <button
              onClick={handleAiSectionToggle}
              disabled={!globalAiEnabled}
              style={{
                padding: '6px 12px',
                border: '1px solid #007bff',
                background: globalAiEnabled ? 'white' : '#e9ecef',
                color: globalAiEnabled ? '#007bff' : '#6c757d',
                borderRadius: '4px',
                cursor: globalAiEnabled ? 'pointer' : 'not-allowed',
                fontSize: '0.9em'
              }}
            >
              {aiAnalysisExpanded ? 'Show Less' : 'See More'}
            </button>
          </div>

          {!globalAiEnabled && (
            <div style={{ color: '#6c757d', fontStyle: 'italic' }}>
              Enable AI analysis to view the latest gateway insights.
            </div>
          )}

          {aiAnalysisExpanded && (
            <div style={{ 
              marginTop: '20px',
              background: 'white', 
              border: '1px solid #dee2e6', 
              borderRadius: '8px', 
              padding: '16px'
            }}>
              {powertrainStatus && powertrainStatus.agent_state !== 'OFFLINE' ? (
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px', alignItems: 'stretch' }}>
                  
                  {/* Left Column - Current Analysis (cards-only layout) */}
                  <div>
                    <h4 style={{ margin: '0 0 16px 0', fontSize: '1.1em', color: '#333' }}>Current Analysis</h4>

                    <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: '12px' }}>
                      <div style={{ padding: '10px', background: '#fff', border: '1px solid #e0e0e0', borderRadius: '4px', textAlign: 'left' }}>
                        <strong style={{ display: 'block', textAlign: 'center' }}>AI Alerts:</strong>
                        {aiAlerts && aiAlerts.length > 0 ? (
                          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', marginTop: '6px' }}>
                            {aiAlerts.map((alert, idx) => (
                              <div key={idx} style={{ padding: '8px', background: '#f8f9fa', borderRadius: '4px', border: '1px solid #e0e0e0', fontSize: '0.95em' }}>
                                <div style={{ color: '#343a40' }}>
                                  <span style={{ fontWeight: 'bold', marginRight: '6px' }}>
                                    {alert.severity || alert.level || 'INFO'}:
                                  </span>
                                  <span>{(alert.description || alert.message || alert.text || 'Alert detected').replace(/^INFO:\\s*/i, '')}</span>
                                </div>
                              </div>
                            ))}
                          </div>
                        ) : (
                          <div style={{ marginTop: '6px', color: '#6c757d', fontStyle: 'italic' }}>No AI alerts in the latest analysis</div>
                        )}
                      </div>

                      <div style={{ padding: '10px', background: '#fff', border: '1px solid #e0e0e0', borderRadius: '4px', textAlign: 'left' }}>
                        <strong style={{ display: 'block', textAlign: 'center' }}>Summary:</strong>
                        <div style={{ marginTop: '6px', color: '#343a40' }}>
                          {analysisSections?.summary || powertrainStatus.analysis_summary || 'Awaiting AI analysis...'}
                        </div>
                      </div>

                      <div style={{ padding: '10px', background: '#fff', border: '1px solid #e0e0e0', borderRadius: '4px', textAlign: 'left' }}>
                        <strong style={{ display: 'block', textAlign: 'center' }}>Trend Analysis:</strong>
                        {analysisSections?.trend_analysis?.length ? (
                          <div style={{ marginTop: '6px', color: '#343a40' }}>
                            {analysisSections.trend_analysis.map((item, idx) => (
                              <div key={idx} style={{ marginBottom: '6px' }}>{item}</div>
                            ))}
                          </div>
                        ) : (
                          <div style={{ marginTop: '6px', color: '#6c757d', fontStyle: 'italic' }}>No trends yet</div>
                        )}
                      </div>

                      <div style={{ padding: '10px', background: '#fff', border: '1px solid #e0e0e0', borderRadius: '4px', textAlign: 'left' }}>
                        <strong style={{ display: 'block', textAlign: 'center' }}>Recommendations:</strong>
                        {analysisSections?.recommendations?.length ? (
                          <div style={{ marginTop: '6px', color: '#343a40' }}>
                            {analysisSections.recommendations.map((item, idx) => (
                              <div key={idx} style={{ marginBottom: '6px' }}>{item}</div>
                            ))}
                          </div>
                        ) : (
                          <div style={{ marginTop: '6px', color: '#6c757d', fontStyle: 'italic' }}>No recommendations yet</div>
                        )}
                      </div>

                      <div style={{ padding: '10px', background: '#fff', border: '1px solid #e0e0e0', borderRadius: '4px', textAlign: 'left' }}>
                        <strong style={{ display: 'block', textAlign: 'center' }}>Memory Notes:</strong>
                        {analysisSections?.memory_notes?.length ? (
                          <div style={{ marginTop: '6px', color: '#343a40' }}>
                            {analysisSections.memory_notes.map((item, idx) => (
                              <div key={idx} style={{ marginBottom: '6px' }}>{item}</div>
                            ))}
                          </div>
                        ) : (
                          <div style={{ marginTop: '6px', color: '#6c757d', fontStyle: 'italic' }}>No memory notes yet</div>
                        )}
                      </div>

                      <div style={{ padding: '10px', background: '#fff', border: '1px solid #e0e0e0', borderRadius: '4px', textAlign: 'left' }}>
                        <strong style={{ display: 'block', textAlign: 'center' }}>Extra:</strong>
                        {analysisSections?.extra?.length ? (
                          <div style={{ marginTop: '6px', color: '#343a40' }}>
                            {analysisSections.extra.map((item, idx) => (
                              <div key={idx} style={{ marginBottom: '6px' }}>{item}</div>
                            ))}
                          </div>
                        ) : (
                          <div style={{ marginTop: '6px', color: '#6c757d', fontStyle: 'italic' }}>No extra findings yet</div>
                        )}
                      </div>
                    </div>
                  </div>

                  {/* Right Column - Recent Insights */}
                  <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
                    <h4 style={{ margin: '0 0 16px 0', fontSize: '1.1em', color: '#333' }}>Recent Insights</h4>
                    
                    {powertrainMemory ? (
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', height: '100%' }}>
                        {/* Insights List */}
                        {powertrainMemory.insights && powertrainMemory.insights.length > 0 ? (
                          <div style={{ flex: 1, minHeight: 0, maxHeight: '470px', overflowY: 'auto' }}>
                            {powertrainMemory.insights.slice(0, 9).map((insight, index) => (
                              <div key={index} style={{ 
                                padding: '8px', 
                                background: '#f8f9fa', 
                                borderRadius: '4px', 
                                marginBottom: '8px',
                                fontSize: '0.9em'
                              }}>
                                <div style={{ marginBottom: '4px' }}>
                                  <span style={{ fontWeight: 'bold', color: '#6f42c1' }}>
                                    {insight.knowledge_type}
                                  </span>
                                </div>
                                <div>
                                  {insight.insight_text && insight.insight_text.trim() 
                                    ? `${getInsightSourceTag(insight)}${insight.insight_text}`
                                    : "Insight analysis in progress..."}
                                </div>
                              </div>
                            ))}
                          </div>
                        ) : (
                          <div style={{ color: '#6c757d', fontStyle: 'italic', textAlign: 'center', padding: '20px' }}>
                            Building knowledge base...
                          </div>
                        )}
                      </div>
                    ) : (
                      <div style={{ textAlign: 'center', color: '#6c757d', padding: '20px' }}>
                        Loading insights...
                      </div>
                    )}

                  </div>

                </div>
              ) : (
                <div style={{ textAlign: 'center', color: '#6c757d', padding: '20px' }}>
                  {powertrainStatus?.agent_state === 'OFFLINE' 
                    ? 'Agent offline - AI intelligence unavailable' 
                    : (powertrainStatus?.error || 'Loading PowertrainAgent status...')}
                </div>
              )}
            </div>
          )}
        </div>
      </div>

    </div>
  );
}

export default AnalysisTab;
