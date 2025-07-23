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
        gap: '20px',
        marginTop: '30px'
      }}>
        {/* System Info */}
        <div style={{ 
          padding: '20px',
          backgroundColor: '#fff',
          border: '1px solid #dee2e6',
          borderRadius: '8px',
          boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
        }}>
          <h3 style={{ color: '#495057', marginBottom: '15px' }}>📊 System Information</h3>
          <div style={{ lineHeight: '1.8', fontSize: '0.9em' }}>
            <div><strong>Version:</strong> 2.1.0</div>
            <div><strong>Build Date:</strong> 2025-07-23</div>
            <div><strong>Architecture:</strong> Docker Microservices</div>
            <div><strong>Database:</strong> InfluxDB Time-Series</div>
            <div><strong>Protocol:</strong> Modbus TCP</div>
          </div>
        </div>

        {/* Contact Information */}
        <div style={{ 
          padding: '20px',
          backgroundColor: '#fff',
          border: '1px solid #dee2e6',
          borderRadius: '8px',
          boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
        }}>
          <h3 style={{ color: '#495057', marginBottom: '15px' }}>📞 Contact Information</h3>
          <div style={{ lineHeight: '1.8', fontSize: '0.9em' }}>
            <div><strong>Developer:</strong> Yarik Sychov</div>
            <div><strong>Email:</strong> 
              <a href="mailto:yariksychov@pm.me" style={{ 
                color: '#007bff', 
                textDecoration: 'none',
                marginLeft: '8px'
              }}>
                yariksychov@pm.me
              </a>
            </div>
            <div><strong>Support:</strong> Professional Installation & Maintenance</div>
            <div><strong>Response Time:</strong> 24-48 hours</div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default ConsoleTab;

