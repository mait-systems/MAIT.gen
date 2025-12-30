// src/tabs/EngineTab.js
import React, { useEffect, useState } from 'react';
import axios from 'axios';
import './DashboardTab.css';

function EngineTab() {
  const [data, setData] = useState({});

  useEffect(() => {
    const fetchData = async () => {
      try {
        const baseUrl = process.env.REACT_APP_API_URL || '';
        const res = await axios.get(`${baseUrl}/api/live-stats`);
        setData(res.data);
      } catch (e) {
        console.error('Error fetching engine data', e);
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 10000);
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
      <h2>🧱 Engine Metrics</h2>
      {renderSection('Core Metrics', [
        { label: 'Engine Speed', value: data['Engine_Speed'], unit: 'RPM' },
        { label: 'Coolant Temp', value: data['Engine_Coolant_Temperature'], unit: '°C' },
        { label: 'Fuel Temp', value: data['Engine_Fuel_Temperature'], unit: '°C' },
        { label: 'Oil Pressure', value: data['Engine_Oil_Pressure'], unit: 'kPa' },
      ])}
      {renderSection('Fuel System', [
        { label: 'Fuel Pressure', value: data['Engine_Fuel_Pressure'], unit: 'kPa' },
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

export default EngineTab;
