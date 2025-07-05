import React, { useState } from 'react';
import CardsSummary from './CardsSummary';
import StatsCharts from './StatsCharts';
import TimelineActions from './TimelineActions';
import ScoringDashboard from './ScoringDashboard';
import './StatsDashboard.css';

const tabs = [
  { key: 'overview', label: 'Vue d\'ensemble' },
  { key: 'graphs', label: 'Graphiques' },
  { key: 'history', label: 'Historique' },
  { key: 'score', label: 'Scoring' },
];

const StatsDashboard = () => {
  const [activeTab, setActiveTab] = useState('overview');

  return (
    <div className="stats-dashboard">
      <div className="stats-tabs">
        {tabs.map((t) => (
          <button
            key={t.key}
            className={`tab-btn ${activeTab === t.key ? 'active' : ''}`}
            onClick={() => setActiveTab(t.key)}
          >
            {t.label}
          </button>
        ))}
      </div>

      <div className="stats-content">
        {activeTab === 'overview' && (
          <>
            <CardsSummary />
          </>
        )}

        {activeTab === 'graphs' && <StatsCharts />}

        {activeTab === 'history' && (
          <>
            <h3 style={{ marginTop: '1rem' }}>Dernières actions</h3>
            <TimelineActions />
          </>
        )}

        {activeTab === 'score' && <ScoringDashboard />}
      </div>
    </div>
  );
};

export default StatsDashboard;