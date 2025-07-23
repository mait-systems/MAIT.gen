// src/App.js
import React, { useState } from 'react';
import './App.css';

// Tab imports
import DashboardTab from './tabs/DashboardTab';
import GeneratorTab from './tabs/GeneratorTab';
import EngineTab from './tabs/EngineTab';
import MaintenanceTab from './tabs/MaintenanceTab';
import TrendsTab from './tabs/TrendsTab';
import ReportsTab from './tabs/ReportsTab';
import ConsoleTab from './tabs/ConsoleTab';
import EventAlertBadge from './components/EventAlertBadge';
import Footer from './components/Footer'; 

function App() {
  const [tab, setTab] = useState('dashboard'); // default to Reports tab

  const tabLabels = {
    dashboard: '📟 Dashboard',
    generator: '⚡ Generator',
    trends: '📈 Trends',
    //engine: '🧱 Engine',
    maintenance: '🧰 Maintenance',
    reports: '📄 Reports',
    console: '💻 Console'
  };

  return (
    <div className="App">
      <h1>🛠 Generator Dashboard</h1>
      <EventAlertBadge onClick={() => setTab('dashboard')} />
      {/* Tab Buttons */}
      <div style={{ marginBottom: '20px' }}>
        {Object.keys(tabLabels).map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            style={{
              marginRight: 10,
              padding: '8px 16px',
              borderRadius: '6px',
              border: '1px solid #ccc',
              backgroundColor: tab === t ? '#007bff' : '#fff',
              color: tab === t ? '#fff' : '#000',
              cursor: 'pointer',
            }}
          >
            {tabLabels[t]}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      <div className="tab-content">
        {tab === 'dashboard' && <DashboardTab />}
        {tab === 'generator' && <GeneratorTab />}
        {tab === 'engine' && <EngineTab />}
        {tab === 'maintenance' && <MaintenanceTab />}
        {tab === 'trends' && <TrendsTab />}
        {tab === 'reports' && <ReportsTab />}
        {tab === 'console' && <ConsoleTab />}
      </div>
      
      <Footer />
    </div>
  );
}

export default App;
