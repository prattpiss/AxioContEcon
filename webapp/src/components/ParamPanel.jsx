import React from 'react';

/**
 * Scalar parameter sliders + value inputs.
 */
export default function ParamPanel({ paramDefs, values, onChange }) {
  return (
    <div className="param-panel">
      <h3 className="panel-title">Parameter</h3>
      <div className="param-grid">
        {paramDefs.map(p => (
          <div key={p.name} className="param-row" title={p.description}>
            <label className="param-label">
              {p.label}
              <span className="param-unit">[{p.unit}]</span>
            </label>
            <input
              type="range"
              className="param-slider"
              min={p.min}
              max={p.max}
              step={p.step}
              value={values[p.name] ?? p.default}
              onChange={e => onChange(p.name, parseFloat(e.target.value))}
            />
            <input
              type="number"
              className="param-value"
              min={p.min}
              max={p.max}
              step={p.step}
              value={values[p.name] ?? p.default}
              onChange={e => onChange(p.name, parseFloat(e.target.value) || 0)}
            />
          </div>
        ))}
      </div>
    </div>
  );
}

/**
 * Initial condition inputs for state variables.
 */
export function StatePanel({ stateVars, values, onChange }) {
  return (
    <div className="param-panel state-panel">
      <h3 className="panel-title">Anfangsbedingungen</h3>
      <div className="param-grid">
        {stateVars.map(v => (
          <div key={v.name} className="param-row" title={v.description}>
            <label className="param-label">
              {v.label}(0)
              <span className="param-unit">[{v.unit}]</span>
            </label>
            <input
              type="number"
              className="param-value state-value"
              min={v.min}
              max={v.max}
              step={0.1}
              value={values[v.name] ?? v.initial}
              onChange={e => onChange(v.name, parseFloat(e.target.value) || 0)}
            />
          </div>
        ))}
      </div>
    </div>
  );
}

/**
 * SDE volatility controls.
 */
export function SdePanel({ sdeConfig, values, enabled, onToggle, onChange }) {
  if (!sdeConfig) return null;
  return (
    <div className="param-panel sde-panel">
      <h3 className="panel-title">
        <label className="sde-toggle">
          <input type="checkbox" checked={enabled} onChange={e => onToggle(e.target.checked)} />
          SDE-Modus
        </label>
        <span className="sde-label">{sdeConfig.label}</span>
      </h3>
      {enabled && (
        <>
          <p className="sde-desc">{sdeConfig.description}</p>
          <div className="param-grid">
            {sdeConfig.sigmaParams.map(p => (
              <div key={p.name} className="param-row">
                <label className="param-label">{p.label}</label>
                <input
                  type="range"
                  className="param-slider"
                  min={p.min}
                  max={p.max}
                  step={p.step}
                  value={values[p.name] ?? p.default}
                  onChange={e => onChange(p.name, parseFloat(e.target.value))}
                />
                <input
                  type="number"
                  className="param-value"
                  value={values[p.name] ?? p.default}
                  min={p.min}
                  max={p.max}
                  step={p.step}
                  onChange={e => onChange(p.name, parseFloat(e.target.value) || 0)}
                />
              </div>
            ))}
            <div className="param-row">
              <label className="param-label">Pfade</label>
              <input
                type="number"
                className="param-value"
                value={values._nPaths ?? 20}
                min={1}
                max={200}
                step={1}
                onChange={e => onChange('_nPaths', parseInt(e.target.value) || 10)}
              />
            </div>
            <div className="param-row">
              <label className="param-label">Seed</label>
              <input
                type="number"
                className="param-value"
                value={values._seed ?? 42}
                min={1}
                max={99999}
                step={1}
                onChange={e => onChange('_seed', parseInt(e.target.value) || 42)}
              />
            </div>
          </div>
        </>
      )}
    </div>
  );
}

/**
 * Solver settings.
 */
export function SolverPanel({ settings, onChange }) {
  return (
    <div className="param-panel solver-panel">
      <h3 className="panel-title">Numerik</h3>
      <div className="param-grid solver-grid">
        <div className="param-row">
          <label className="param-label">t_Ende</label>
          <input
            type="number"
            className="param-value"
            value={settings.tEnd}
            min={1}
            max={10000}
            step={1}
            onChange={e => onChange('tEnd', parseFloat(e.target.value) || 60)}
          />
        </div>
        <div className="param-row">
          <label className="param-label">Punkte</label>
          <input
            type="number"
            className="param-value"
            value={settings.nPoints}
            min={100}
            max={10000}
            step={100}
            onChange={e => onChange('nPoints', parseInt(e.target.value) || 1000)}
          />
        </div>
      </div>
    </div>
  );
}
