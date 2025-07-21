// src/tabs/MaintenanceTab.js
import React, { useEffect, useState } from 'react';
import axios from 'axios';
import './DashboardTab.css';

function MaintenanceTab() {
  const [data, setData] = useState({});

  useEffect(() => {
    const fetchData = async () => {
      try {
        const res = await axios.get(`${process.env.REACT_APP_API_BASE}/api/live-stats`);
        setData(res.data);
      } catch (e) {
        console.error('Error fetching maintenance data', e);
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
      {renderSection('Runtime Stats', [
        { label: 'Total Runtime', value: data['Total_Runtime_Hours'], unit: 'hrs' },
        { label: 'Runtime Loaded', value: data['Total_Runtime_Loaded_Hours'], unit: 'hrs' },
        { label: 'Runtime Unloaded', value: data['Total_Runtime_Unloaded_Hours'], unit: 'hrs' },
        { label: 'Total Runtime kWh', value: data['Total_Runtime_kW_Hours'], unit: 'kWh' },
      ])}
      {renderSection('Maintenance', [
        { label: 'Runtime Since Maint.', value: data['Total_Runtime_Hours_Since_Maintenance'], unit: 'hrs' },
        { label: 'Days Since Maint.', value: data['Operating_Days_Since_Last_Maintenance'], unit: 'days' },
        { label: 'Starts Since Maint.', value: data['Number_of_Starts_Since_Last_Maintenance'], unit: 'starts' },
      ])}
      {renderSection('Starts & Info', [
        { label: 'Total Starts', value: data['Total_Number_of_Starts'], unit: 'starts' },
        { label: 'ECM Fault Codes', value: data['ECM_Fault_Codes'] },
        { label: 'ECM Model', value: data['ECM_Model'] },
      ])}
      {renderSection('Model Info', [
        { label: 'Genset Model 1-2', value: data['Genset_Model_Number_1-2'] },
        { label: 'Genset Model 3-4', value: data['Genset_Model_Number_3-4'] },
        { label: 'Genset Model 5-6', value: data['Genset_Model_Number_5-6'] },
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

export default MaintenanceTab;
