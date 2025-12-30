
// src/tabs/TrendsTab.js
import React from 'react';
import LoadIndicator from './LoadIndicator';
import TrendChartBlock from './LoadTrendChart';
import './DashboardTab.css';

const TrendsTab = ({ charts, setCharts, nextId, setNextId }) => {

  const addChart = () => {
    setCharts([...charts, { 
      id: nextId, 
      selectedField: 'Generator_Apparent_Power', 
      selectedRange: '2h' 
    }]);
    setNextId(nextId + 1);
  };

  const updateChart = (chartId, field, range) => {
    setCharts(charts.map(chart => 
      chart.id === chartId 
        ? { ...chart, selectedField: field, selectedRange: range }
        : chart
    ));
  };

  const removeChart = (id) => {
    setCharts(charts.filter(chart => chart.id !== id));
  };

  return (
    <div className="dashboard-tab">
      <LoadIndicator />

      <div style={{ marginTop: '40px' }}>
        {charts.map((chart) => (
          <TrendChartBlock
            key={chart.id}
            chartId={chart.id}
            selectedField={chart.selectedField}
            selectedRange={chart.selectedRange}
            onRemove={() => removeChart(chart.id)}
            onSettingsChange={(field, range) => updateChart(chart.id, field, range)}
          />
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
