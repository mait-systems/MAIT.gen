// src/tabs/GeneratorTab.js
import React, { useEffect, useState } from 'react';
import axios from 'axios';
import './GeneratorTab.css'; 

function GeneratorTab() {
  const [data, setData] = useState({});

  useEffect(() => {
    const fetchData = async () => {
      try {
        const res = await axios.get(`${process.env.REACT_APP_API_URL || ''}/api/live-stats`);
        setData(res.data);
      } catch (e) {
        console.error('Error fetching generator data', e);
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 2000);
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

  const ratingValue = data['Genset_kW_Rating'] != null ? Number(data['Genset_kW_Rating']) : null;
  const realPowerPercent = data['Generator_Total_Real_Power'] != null ? Number(data['Generator_Total_Real_Power']) : null;
  const powerOutputKw = ratingValue != null && realPowerPercent != null
    ? (realPowerPercent / 100) * ratingValue
    : null;

  return (
    <div className="generator-grid">
      {renderSection('Voltages, Line to Line', [
        { label: 'L1-L2', value: data['RMS_Generator_Voltage_L1-L2'], unit: '%' },
        { label: 'L2-L3', value: data['RMS_Generator_Voltage_L2-L3'], unit: '%' },
        { label: 'L3-L1', value: data['RMS_Generator_Voltage_L3-L1'], unit: '%' },
        { label: 'Line Avg', value: data['RMS_Generator_Voltage_Line_to_Line_Average'], unit: '%' },
        ])}
      {renderSection('Voltages, Line to Neutral', [     
	    { label: 'L1-N', value: data['RMS_Generator_Voltage_L1-N'], unit: '%' },
        { label: 'L2-N', value: data['RMS_Generator_Voltage_L2-N'], unit: '%' },
        { label: 'L3-N', value: data['RMS_Generator_Voltage_L3-N'], unit: '%' },
        { label: 'Neutral Avg', value: data['RMS_Generator_Voltage_Line_to_Neutral_Average'], unit: '%' },
      ])}
      {renderSection('Currents', [
        { label: 'L1', value: data['RMS_Generator_Current_L1'], unit: '%' },
        { label: 'L2', value: data['RMS_Generator_Current_L2'], unit: '%' },
        { label: 'L3', value: data['RMS_Generator_Current_L3'], unit: '%' },
        { label: 'Average', value: data['RMS_Generator_Current_Average'], unit: '%' },
      ])}
      {renderSection('Power', [
        { label: 'Real Total', value: data['Generator_Total_Real_Power'], unit: '%' },
        { label: 'Apparent Total', value: data['Generator_Apparent_Power'], unit: '%' },
        { label: 'Power Output', value: powerOutputKw != null ? powerOutputKw.toFixed(1) : null, unit: 'kW' },
        { label: 'Power Rating', value: ratingValue != null ? ratingValue.toFixed(1) : null, unit: 'kW' },
      ])}
    </div>
  );
}

function MetricCard({ label, value, unit }) {
  return (
    <div className="metric-card">
      <div className="metric-label">{label}</div>
      <div className="metric-value">
        {value !== undefined && value !== null && value !== '' ? `${value}${unit ? ` ${unit}` : ''}` : '—'}
      </div>
    </div>
  );
}

export default GeneratorTab;
