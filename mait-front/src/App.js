// src/App.js
import React, { useState } from 'react';
import './App.css';
import {
  Squares2X2Icon,
  BoltIcon,
  ChartBarIcon,
  WrenchScrewdriverIcon,
  BeakerIcon,
  CommandLineIcon
} from '@heroicons/react/24/outline';

// Tab imports
import DashboardTab from './tabs/DashboardTab';
import GeneratorTab from './tabs/GeneratorTab';
import EngineTab from './tabs/EngineTab';
import MaintenanceTab from './tabs/MaintenanceTab';
import TrendsTab from './tabs/TrendsTab';
import AnalysisTab from './tabs/AnalysisTab';
import ConsoleTab from './tabs/ConsoleTab';
import EventAlertBadge from './components/EventAlertBadge';
import Footer from './components/Footer'; 

function App() {
  const [tab, setTab] = useState('dashboard'); // default to Reports tab
  const generatorLabel = process.env.REACT_APP_GENERATOR_NAME || 'Generator';
  
  // TrendsTab state - moved here to persist across tab switches
  const [trendsCharts, setTrendsCharts] = useState([{ 
    id: 1, 
    selectedField: 'Generator_Apparent_Power', 
    selectedRange: '2h' 
  }]);
  const [trendsNextId, setTrendsNextId] = useState(2);

  const tabs = [
    { key: 'dashboard', label: 'Dashboard', Icon: Squares2X2Icon },
    { key: 'generator', label: 'Generator', Icon: BoltIcon },
    { key: 'trends', label: 'Trends', Icon: ChartBarIcon },
    { key: 'maintenance', label: 'Maintenance', Icon: WrenchScrewdriverIcon },
    { key: 'analysis', label: 'Analysis', Icon: BeakerIcon },
    { key: 'console', label: 'Console', Icon: CommandLineIcon }
  ];

  return (
    <div className="App">
      <h1 style={{ display: 'flex', alignItems: 'center', gap: 8, justifyContent: 'center' }}>
        {generatorLabel} Dashboard
      </h1>
      <EventAlertBadge onClick={() => setTab('dashboard')} />
      {/* Tab Buttons */}
      <div style={{ marginBottom: '20px' }}>
        {tabs.map(({ key, label, Icon }) => (
          <button
            key={key}
            onClick={() => setTab(key)}
            style={{
              marginRight: 10,
              padding: '8px 16px',
              borderRadius: '6px',
              border: '1px solid #ccc',
              backgroundColor: tab === key ? '#007bff' : '#fff',
              color: tab === key ? '#fff' : '#000',
              cursor: 'pointer',
              display: 'inline-flex',
              alignItems: 'center',
              gap: 8,
              fontWeight: 600
            }}
          >
            <Icon style={{ width: 18, height: 18 }} />
            {label}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      <div className="tab-content">
        {tab === 'dashboard' && <DashboardTab />}
        {tab === 'generator' && <GeneratorTab />}
        {tab === 'engine' && <EngineTab />}
        {tab === 'maintenance' && <MaintenanceTab />}
        {tab === 'trends' && <TrendsTab charts={trendsCharts} setCharts={setTrendsCharts} nextId={trendsNextId} setNextId={setTrendsNextId} />}
        {tab === 'analysis' && <AnalysisTab />}
        {tab === 'console' && <ConsoleTab />}
      </div>
      
      <Footer />
    </div>
  );
}

export default App;
