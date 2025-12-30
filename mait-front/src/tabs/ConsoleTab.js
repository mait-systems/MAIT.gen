import React, { useEffect, useState, useRef } from 'react';
import axios from 'axios';
import './DashboardTab.css';

function ConsoleTab() {
  const [log, setLog] = useState('');
  const logRef = useRef(null); // Create a ref for the <pre> element

  useEffect(() => {
    const fetchLogs = async () => {
      try {
        // Use environment variable or default to relative URL for Docker
        const apiUrl = process.env.REACT_APP_API_URL || '';
        const res = await axios.get(`${apiUrl}/api/logs`);
        setLog(res.data.log);
      } catch (err) {
        console.error('Error loading logs:', err);
        setLog('Failed to load logs');
      }
    };

    fetchLogs();
    const interval = setInterval(fetchLogs, 2000); // refresh every 2 sec
    return () => clearInterval(interval);
  }, []);

  // Auto-scroll to bottom when log updates
  useEffect(() => {
    if (logRef.current) {
      logRef.current.scrollTop = logRef.current.scrollHeight;
    }
  }, [log]);

  return (
    <div className="dashboard-tab">
      <pre
        ref={logRef}
        style={{
          backgroundColor: '#f5f5f5',
          color: '#333',
          padding: '5px',
          borderRadius: '5px',
          border: '1px solid #ccc',
          maxHeight: '600px',
          overflowY: 'scroll',
          fontFamily: 'Menlo, Consolas, monospace',
          fontSize: '14px',
          lineHeight: '1.5',
          whiteSpace: 'pre-wrap',
        }}
      >
        {log}
      </pre>

      {/* System Information Section */}
      <div style={{ 
        display: 'grid', 
        gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', 
        gap: '16px',
        marginTop: '30px'
      }}>
        {/* System Info */}
        <div style={{ 
          padding: '14px 16px',
          backgroundColor: '#fff',
          border: '1px solid #dee2e6',
          borderRadius: '8px',
          boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
        }}>
          <h3 style={{ color: '#495057', margin: '0 0 12px 0', textAlign: 'center' }}>📊 System Information</h3>
          <div style={{ lineHeight: '1.8', fontSize: '0.9em' }}>
            <div><strong>Version:</strong> 2.2.0</div>
            <div><strong>Build Date:</strong> 2025-12-03</div>
            <div><strong>Protocol:</strong> Modbus TCP</div>
          </div>
        </div>

        {/* Contact Information */}
        <div style={{ 
          padding: '14px 16px',
          backgroundColor: '#fff',
          border: '1px solid #dee2e6',
          borderRadius: '8px',
          boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
        }}>
          <h3 style={{ color: '#495057', margin: '0 0 12px 0', textAlign: 'center' }}>📞 Contact Information</h3>
          <div style={{ lineHeight: '1.8', fontSize: '0.9em' }}>
            <div><strong>Email:</strong> 
              <a href="mailto:ys@mait.tech" style={{ 
                color: '#007bff', 
                textDecoration: 'none',
                marginLeft: '8px'
              }}>
                ys@mait.tech
              </a>
            </div>
            <div><strong>Website:</strong> 
              <a href="https://mait.tech" style={{ 
                color: '#007bff', 
                textDecoration: 'none',
                marginLeft: '8px'
              }}>
                mait.tech
              </a>
            </div>
            <div><strong>GitHub:</strong> 
              <a href="https://github.com/mait-systems/MAIT.gen" style={{ 
                color: '#007bff', 
                textDecoration: 'none',
                marginLeft: '8px'
              }}>
                github.com/mait-systems/MAIT.gen
              </a>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default ConsoleTab;
