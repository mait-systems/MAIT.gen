
// src/tabs/TrendsTab.js
import React, { useState } from 'react';
import LoadIndicator from './LoadIndicator';
import TrendChartBlock from './LoadTrendChart';
import './DashboardTab.css';

const TrendsTab = () => {
  const [charts, setCharts] = useState([{ id: 1, defaultField: 'Generator_Apparent_Power' }]);
  const [nextId, setNextId] = useState(2);

  const addChart = () => {
    setCharts([...charts, { id: nextId }]);
    setNextId(nextId + 1);
  };

  const removeChart = (id) => {
    setCharts(charts.filter(chart => chart.id !== id));
  };

  return (
    <div className="dashboard-tab">
      <LoadIndicator />

      <div style={{ marginTop: '40px' }}>
        {charts.map((chart) => (
          <div
            key={chart.id}
            style={{
              marginBottom: '40px',
              padding: '10px',
              border: '1px solid #ccc',
              borderRadius: '8px',
              background: '#fff',
            }}
          >
            <TrendChartBlock
              chartId={chart.id}
              onRemove={() => removeChart(chart.id)}
              defaultField={chart.defaultField}
            />
          </div>
        ))}

        <div style={{ textAlign: 'center', marginTop: '20px' }}>
          <button
            onClick={addChart}
            style={{
              background: '#007bff',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              padding: '10px 20px',
              cursor: 'pointer'
            }}
          >
            ➕ Add Chart
          </button>
        </div>
      </div>
    </div>
  );
};

export default TrendsTab;
