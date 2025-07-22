// src/tabs/LoadTrendChart.js
import React, { useEffect, useState } from 'react';
import axios from 'axios';
import {
  LineChart,
  Line,
  CartesianGrid,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer
} from 'recharts';

const timeRanges = {
  '2h': 2,
  '6h': 6,
  '12h': 12,
  '1 Day': 24,
  '1 Week': 24 * 7,
  '2 Weeks': 24 * 14,
  '1 Month': 24 * 30
};

const availableFields = [
  'RMS_Generator_Voltage_L1-L2',
  'RMS_Generator_Voltage_L2-L3',
  'RMS_Generator_Voltage_L3-L1',
  'RMS_Generator_Voltage_Line_to_Line_Average',
  'RMS_Generator_Voltage_L1-N',
  'RMS_Generator_Voltage_L2-N',
  'RMS_Generator_Voltage_L3-N',
  'RMS_Generator_Voltage_Line_to_Neutral_Average',
  'RMS_Generator_Current_L1',
  'RMS_Generator_Current_L2',
  'RMS_Generator_Current_L3',
  'RMS_Generator_Current_Average',
  'Generator_Frequency',
  'Generator_Real_Power_L1',
  'Generator_Real_Power_L2',
  'Generator_Real_Power_L3',
  'Generator_Total_Real_Power',
  'Generator_Reactive_Power_L1',
  'Generator_Reactive_Power_L2',
  'Generator_Reactive_Power_L3',
  'Generator_Reactive_Power',
  'Generator_Apparent_Power_L1',
  'Generator_Apparent_Power_L2',
  'Generator_Apparent_Power_L3',
  'Generator_Apparent_Power',
  'Generator_Power_Factor_Average',
  'Total_Bus_Real_Power',
  'Engine_Oil_Pressure',
  'Engine_Coolant_Temperature',
  'Engine_Speed',
  'Battery_Voltage',
  'Controller_Temperature',
  'Engine_Fuel_Pressure',
  'Engine_Fuel_Temperature',
  'Engine_Fuel_Rate',
  'Intake_Air_Temperature',
  'Intake_Air_Pressure'
];

function LoadTrendChart({ chartId, onRemove }) {
  const [data, setData] = useState([]);
  const [selectedField, setSelectedField] = useState('Generator_Apparent_Power');
  const [selectedRange, setSelectedRange] = useState('2h');

  const fetchData = async (field, hours) => {
    try {
      const res = await axios.get(`${process.env.REACT_APP_API_URL || ''}/api/trend?field=${field}&hours=${hours}`);
      const transformed = res.data.map(d => ({ ...d, value: d._value }));
      setData(transformed);
    } catch (err) {
      console.error('Failed to fetch trend data', err);
    }
  };

  useEffect(() => {
    fetchData(selectedField, timeRanges[selectedRange]);
    const interval = setInterval(() => {
      fetchData(selectedField, timeRanges[selectedRange]);
    }, 10000); // 10s refresh
    return () => clearInterval(interval);
  }, [selectedField, selectedRange]);

  return (
    <div style={{ border: '1px solid #ccc', padding: 15, borderRadius: 8 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <select value={selectedField} onChange={(e) => setSelectedField(e.target.value)}>
            {availableFields.map(field => (
              <option key={field} value={field}>{field}</option>
            ))}
          </select>

          <select
            value={selectedRange}
            onChange={(e) => setSelectedRange(e.target.value)}
            style={{ marginLeft: '10px' }}
          >
            {Object.keys(timeRanges).map(label => (
              <option key={label} value={label}>{label}</option>
            ))}
          </select>
        </div>

        <button onClick={onRemove}>🗑 Remove</button>
      </div>

      <ResponsiveContainer width="100%" height={250}>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="_time" tick={{ fontSize: 10 }} />
          <YAxis />
          <Tooltip />
          <Line
            type="monotone"
            dataKey="value"
            stroke="#8884d8"
            strokeWidth={2}
            dot={false}
            name={selectedField}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

export default LoadTrendChart;

