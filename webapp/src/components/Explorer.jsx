import React from 'react';
import chapters from '../simulations/index.js';

/**
 * Left sidebar: chapter-grouped simulation list.
 */
export default function Explorer({ activeSim, onSelect }) {
  return (
    <nav className="explorer">
      <div className="explorer-header">
        <h1 className="explorer-title">AxioLab</h1>
        <p className="explorer-subtitle">Interaktives Simulationslabor</p>
      </div>
      <div className="explorer-chapters">
        {chapters.map(ch => (
          <div key={ch.id} className="explorer-chapter">
            <div className="chapter-title">{ch.title}</div>
            <ul className="chapter-sims">
              {ch.sims.map(sim => (
                <li
                  key={sim.id}
                  className={
                    'sim-item' +
                    (sim.available ? ' available' : ' locked') +
                    (activeSim === sim.id ? ' active' : '')
                  }
                  onClick={() => sim.available && onSelect(sim.id)}
                  title={sim.available ? `${sim.eqId}: ${sim.title}` : 'Noch nicht implementiert'}
                >
                  <span className="sim-id">{sim.id}</span>
                  <span className="sim-eq">{sim.eqId}</span>
                  <span className="sim-name">{sim.title}</span>
                  {!sim.available && <span className="sim-lock">🔒</span>}
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>
      <div className="explorer-footer">
        <a href="https://github.com/prattpiss/AxioContEcon" target="_blank" rel="noreferrer">
          GitHub Repository
        </a>
      </div>
    </nav>
  );
}
