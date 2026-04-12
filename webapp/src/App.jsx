import React, { useState } from 'react';
import Explorer from './components/Explorer.jsx';
import SimView from './components/SimView.jsx';
import { getSimulation } from './simulations/index.js';

export default function App() {
  const [activeSim, setActiveSim] = useState('S08');
  const sim = getSimulation(activeSim);

  return (
    <div className="app">
      <Explorer activeSim={activeSim} onSelect={setActiveSim} />
      <main className="main">
        {sim ? (
          <SimView key={activeSim} sim={sim} />
        ) : (
          <div className="no-sim">
            <div className="no-sim-content">
              <h2>Simulation nicht verfügbar</h2>
              <p>Diese Simulation wurde noch nicht implementiert.</p>
              <p>Wähle eine verfügbare Simulation aus der Seitenleiste.</p>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
