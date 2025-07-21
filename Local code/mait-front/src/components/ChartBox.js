// src/components/ChartBox.js
import React from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, LabelList } from 'recharts';

const ChartBox = ({ title, chartData, colorFunc, yAxisDomain = [0, 100], barSize = 50 }) => {
  return (
    <div style={{ flex: 1, marginRight: '10px', border: '1px solid #ccc', padding: '10px' }}>
      <h4 style={{ textAlign: 'center', marginBottom: '10px' }}>{title}</h4>
      <ResponsiveContainer width="100%" height={240}>
        <BarChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="name" />
          <YAxis domain={yAxisDomain} />
          <Tooltip />
          <Bar
            dataKey="value"
            fill={colorFunc(chartData[0].value)}  // Apply color based on the chart value
            barSize={barSize}
          >
            <LabelList dataKey="value" position="top" />
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
};

export default ChartBox;
