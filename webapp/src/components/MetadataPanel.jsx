import React, { useEffect, useRef } from 'react';
import katex from 'katex';

/**
 * Metadata panel showing equation, variable classification, solver info.
 */
export default function MetadataPanel({ sim, solverInfo }) {
  const eqRef = useRef(null);

  useEffect(() => {
    if (eqRef.current && sim.equationLatex) {
      try {
        katex.render(sim.equationLatex, eqRef.current, {
          throwOnError: false,
          displayMode: true,
        });
      } catch (_) {
        eqRef.current.textContent = sim.equationLatex;
      }
    }
  }, [sim.equationLatex]);

  return (
    <div className="metadata-panel">
      {/* Equation */}
      <div className="meta-equation">
        <span className="meta-eq-id">{sim.eqId} ({sim.section})</span>
        <div ref={eqRef} className="meta-eq-render" />
      </div>

      <p className="meta-description">{sim.description}</p>

      {/* Classification table */}
      <div className="meta-tables">
        <div className="meta-table">
          <h4>Endogene Variablen</h4>
          <table>
            <thead><tr><th>Symbol</th><th>Bezeichnung</th><th>Einheit</th></tr></thead>
            <tbody>
              {sim.stateVars.map(v => (
                <tr key={v.name}>
                  <td className="mono">{v.name}(t)</td>
                  <td>{v.label}</td>
                  <td>{v.unit}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="meta-table">
          <h4>Exogene Variablen</h4>
          <table>
            <thead><tr><th>Symbol</th><th>Bezeichnung</th><th>In Vollmodell →</th></tr></thead>
            <tbody>
              {sim.exogenous.map(v => (
                <tr key={v.name}>
                  <td className="mono">{v.name}(t)</td>
                  <td>{v.label}</td>
                  <td className="coupled">{v.coupledTo || '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="meta-table">
          <h4>Parameter</h4>
          <table>
            <thead><tr><th>Symbol</th><th>Bezeichnung</th><th>Einheit</th><th>Bereich</th></tr></thead>
            <tbody>
              {sim.parameters.map(p => (
                <tr key={p.name}>
                  <td className="mono">{p.label.split(' ')[1] || p.name}</td>
                  <td>{p.description}</td>
                  <td>{p.unit}</td>
                  <td>{p.min}–{p.max}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Solver info */}
      {solverInfo && (
        <div className="meta-solver">
          <h4>Numerik</h4>
          <div className="solver-info-grid">
            <span>Solver:</span><span>{solverInfo.method}</span>
            <span>Status:</span><span className={solverInfo.success ? 'ok' : 'err'}>{solverInfo.message}</span>
            <span>Schritte:</span><span>{solverInfo.steps}</span>
            <span>Rechenzeit:</span><span>{solverInfo.elapsed} ms</span>
          </div>
        </div>
      )}
    </div>
  );
}
