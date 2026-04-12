import React from 'react';
import { FUNCTION_TYPES } from '../functions/generators.js';

/**
 * Function type selector for a single exogenous variable.
 * Shows dropdown for type, plus parameter inputs for the selected type.
 */
export default function FuncSelector({ varDef, funcType, funcParams, onChange }) {
  const typeInfo = FUNCTION_TYPES[funcType];

  const handleTypeChange = (e) => {
    const newType = e.target.value;
    const newInfo = FUNCTION_TYPES[newType];
    const defaults = {};
    if (newInfo) {
      for (const p of newInfo.params) defaults[p.name] = p.default;
    }
    onChange({ type: newType, params: defaults });
  };

  const handleParamChange = (paramName, value) => {
    onChange({ type: funcType, params: { ...funcParams, [paramName]: parseFloat(value) || 0 } });
  };

  return (
    <div className="func-selector">
      <div className="func-header">
        <label className="func-label" title={varDef.description}>
          {varDef.label}
          <span className="func-unit">[{varDef.unit}]</span>
          {varDef.coupledTo && <span className="func-coupled">→ {varDef.coupledTo}</span>}
        </label>
        <select value={funcType} onChange={handleTypeChange} className="func-type-select">
          {Object.entries(FUNCTION_TYPES).map(([key, info]) => (
            <option key={key} value={key}>
              {info.label}{info.stochastic ? ' 🎲' : ''}
            </option>
          ))}
        </select>
      </div>

      {typeInfo && typeInfo.params.length > 0 && (
        <div className="func-params">
          {typeInfo.params.map(p => (
            <div key={p.name} className="func-param-row">
              <label className="func-param-label">{p.label}</label>
              <input
                type="number"
                className="func-param-input"
                value={funcParams[p.name] ?? p.default}
                min={p.min}
                max={p.max}
                step={p.step}
                onChange={e => handleParamChange(p.name, e.target.value)}
              />
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
