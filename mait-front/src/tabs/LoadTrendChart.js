// src/tabs/LoadTrendChart.js
import React, { useEffect, useMemo, useState } from 'react';
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

function LoadTrendChart({ chartId, selectedField, selectedRange, onRemove, onSettingsChange }) {
  const [data, setData] = useState([]);
  const yDomain = useMemo(() => {
    if (!data.length) {
      return ['auto', 'auto'];
    }

    const values = data
      .map((point) => Number(point.value))
      .filter((value) => Number.isFinite(value));

    if (!values.length) {
      return ['auto', 'auto'];
    }

    const min = Math.min(...values);
    const max = Math.max(...values);

    if (!Number.isFinite(min) || !Number.isFinite(max)) {
      return ['auto', 'auto'];
    }

    const range = max - min;
    const base = range === 0 ? Math.abs(max || min) : range;
    const padding = base === 0 ? 1 : base * 0.15;

    const lowerBound = min >= 0 && (min - padding) < 0 ? 0 : min - padding;
    const upperBound = max + padding;

    return [lowerBound, upperBound];
  }, [data]);

  const formatYAxisTick = (tick) => {
    const value = Number(tick);
    if (!Number.isFinite(value)) {
      return tick;
    }

    return value.toFixed(1);
  };

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
    <div className="trend-chart-container">
      <div className="trend-chart-header">
        <div className="trend-controls">
          <select 
            value={selectedField} 
            onChange={(e) => onSettingsChange(e.target.value, selectedRange)}
            className="trend-select"
            title={selectedField} /* Show full name on hover */
          >
            {availableFields.map(field => (
              <option key={field} value={field}>
                {field.length > 30 ? field.substring(0, 30) + '...' : field}
              </option>
            ))}
          </select>

          <select
            value={selectedRange}
            onChange={(e) => onSettingsChange(selectedField, e.target.value)}
            className="trend-select"
          >
            {Object.keys(timeRanges).map(label => (
              <option key={label} value={label}>{label}</option>
            ))}
          </select>
        </div>

        <button onClick={onRemove} className="trend-remove-button">
          🗑 Remove
        </button>
      </div>

      <ResponsiveContainer width="100%" height={250}>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="_time" tick={{ fontSize: 10 }} />
          <YAxis
            domain={yDomain}
            allowDataOverflow
            tickFormatter={formatYAxisTick}
          />
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
