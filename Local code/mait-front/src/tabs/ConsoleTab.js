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
    </div>
  );
}

export default ConsoleTab;

