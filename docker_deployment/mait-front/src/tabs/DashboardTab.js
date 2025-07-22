import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './DashboardTab.css';

function DashboardTab() {
  const [data, setData] = useState({});
  const [events, setEvents] = useState([]);

  useEffect(() => {
    const fetchLiveData = async () => {
      try {
        const res = await axios.get(`${process.env.REACT_APP_API_URL || ''}/api/live-stats`);
        setData(res.data);
      } catch (err) {
        console.error('Failed to fetch live data:', err);
      }
    };

    const fetchEvents = async () => {
      try {
        const res = await axios.get(`${process.env.REACT_APP_API_URL || ''}/api/active-events`);
        setEvents(res.data.events || []);
      } catch (err) {
        console.error('Failed to fetch active events:', err);
      }
    };

    fetchLiveData();
    fetchEvents();

    const interval = setInterval(() => {
      fetchLiveData();
      fetchEvents();
    }, 2000);

    return () => clearInterval(interval);
  }, []);

  const renderSection = (title, metrics) => (
    <>
      <h3>{title}</h3>
      <div className="metrics-grid">
        {metrics.map((m) => (
          <MetricCard key={m.label} {...m} />
        ))}
      </div>
    </>
  );

  return (
    <div className="dashboard-tab">
      <h2>📟 Live Status</h2>

      {renderSection('Core Metrics', [
        { label: 'Engine Speed', value: data['Engine_Speed'], unit: 'RPM' },
        { label: 'Load', value: data['Generator_Apparent_Power'], unit: '%' },
        { label: 'Coolant Temp', value: data['Engine_Coolant_Temperature'], unit: '°C' },
        { label: 'Oil Pressure', value: data['Engine_Oil_Pressure'], unit: 'kPa' },
      ])}

      {renderSection('Fuel System', [
        { label: 'Fuel Pressure', value: data['Engine_Fuel_Pressure'], unit: 'kPa' },
        { label: 'Fuel Temp', value: data['Engine_Fuel_Temperature'], unit: '°C' },
        { label: 'Fuel Rate', value: data['Engine_Fuel_Rate'], unit: 'l/hr' },
      ])}

      {renderSection('Air Intake', [
        { label: 'Air Temp', value: data['Intake_Air_Temperature'], unit: '°C' },
        { label: 'Air Pressure', value: data['Intake_Air_Pressure'], unit: 'kPa' },
      ])}

      {renderSection('Electrical', [
        { label: 'Battery Voltage', value: data['Battery_Voltage'], unit: 'V' },
        { label: 'Controller Temp', value: data['Controller_Temperature'], unit: '°C' },
      ])}

      {events.length > 0 && (
        <div className="active-events-section">
          <h3>🚨 Active Alerts</h3>
          <ul className="event-list">
            {events.map((e, idx) => (
              <li key={idx}>
                <strong>{new Date(e.time).toLocaleTimeString()}:</strong> {e.message}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

function MetricCard({ label, value, unit }) {
  return (
    <div className="metric-card">
      <div className="metric-label">{label}</div>
      <div className="metric-value">
        {value !== undefined ? `${value} ${unit || ''}` : '—'}
      </div>
    </div>
  );
}

export default DashboardTab;

