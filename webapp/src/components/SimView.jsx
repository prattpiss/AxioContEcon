import React, { useState, useCallback, useRef } from 'react';
import { createFunction } from '../functions/generators.js';
import { solveODE } from '../solvers/rk45.js';
import { solveEulerMaruyama } from '../solvers/eulerMaruyama.js';
import FuncSelector from './FuncSelector.jsx';
import ParamPanel, { StatePanel, SdePanel, SolverPanel } from './ParamPanel.jsx';
import PlotPanel from './PlotPanel.jsx';
import MetadataPanel from './MetadataPanel.jsx';

/**
 * Main simulation view: controls + plot + metadata for one simulation.
 */
export default function SimView({ sim }) {
  // ── State: parameters ──
  const [params, setParams] = useState(() => {
    const obj = {};
    sim.parameters.forEach(p => { obj[p.name] = p.default; });
    return obj;
  });

  // ── State: initial conditions ──
  const [initConds, setInitConds] = useState(() => {
    const obj = {};
    sim.stateVars.forEach(v => { obj[v.name] = v.initial; });
    return obj;
  });

  // ── State: exogenous function configs ──
  const [exogConfigs, setExogConfigs] = useState(() => {
    const obj = {};
    sim.exogenous.forEach(v => {
      obj[v.name] = { type: v.defaultType, params: { ...v.defaultParams } };
    });
    return obj;
  });

  // ── State: SDE settings ──
  const [sdeEnabled, setSdeEnabled] = useState(false);
  const [sdeParams, setSdeParams] = useState(() => {
    const obj = { _nPaths: 20, _seed: 42 };
    if (sim.sdeConfig) {
      sim.sdeConfig.sigmaParams.forEach(p => { obj[p.name] = p.default; });
    }
    return obj;
  });

  // ── State: solver settings ──
  const [solverSettings, setSolverSettings] = useState(() => ({
    tEnd: sim.solverDefaults?.tEnd || 60,
    nPoints: sim.solverDefaults?.nPoints || 1000,
  }));

  // ── Results ──
  const [result, setResult] = useState(null);
  const [sdeResult, setSdeResult] = useState(null);
  const [solverInfo, setSolverInfo] = useState(null);
  const [running, setRunning] = useState(false);
  const exogFuncsRef = useRef({});

  // ── Preset loader ──
  const loadPreset = useCallback((preset) => {
    if (preset.paramOverrides) {
      setParams(prev => ({ ...prev, ...preset.paramOverrides }));
    }
    if (preset.stateOverrides) {
      setInitConds(prev => ({ ...prev, ...preset.stateOverrides }));
    }
    if (preset.exogOverrides) {
      setExogConfigs(prev => {
        const next = { ...prev };
        for (const [k, v] of Object.entries(preset.exogOverrides)) {
          next[k] = { type: v.type, params: { ...v.params } };
        }
        return next;
      });
    }
    if (preset.sdeOverrides) {
      setSdeEnabled(true);
      setSdeParams(prev => ({ ...prev, ...preset.sdeOverrides }));
    } else {
      setSdeEnabled(false);
    }
    // Clear old results
    setResult(null);
    setSdeResult(null);
    setSolverInfo(null);
  }, []);

  // ── Run simulation ──
  const runSimulation = useCallback(() => {
    setRunning(true);
    // Build exogenous functions
    const tMax = solverSettings.tEnd;
    const exogFuncs = {};
    for (const v of sim.exogenous) {
      const conf = exogConfigs[v.name];
      exogFuncs[v.name] = createFunction(conf.type, conf.params, tMax + 5);
    }
    exogFuncsRef.current = exogFuncs;

    // Build y0: for spatial state vars, use the full NX-element initialProfile
    let y0 = [];
    for (const v of sim.stateVars) {
      if (v.spatial && v.initialProfile) {
        y0.push(...v.initialProfile);
      } else {
        y0.push(initConds[v.name] ?? v.initial);
      }
    }
    const tEval = Array.from({ length: solverSettings.nPoints }, (_, i) =>
      (i / (solverSettings.nPoints - 1)) * tMax
    );

    const start = performance.now();

    try {
      if (sdeEnabled && sim.diffusion) {
        // SDE mode: Euler-Maruyama
        const drift = (t, y) => sim.rhs(t, y, exogFuncs, params);
        const diffusion = (t, y) => sim.diffusion(t, y, exogFuncs, params, sdeParams);

        const sdeRes = solveEulerMaruyama(drift, diffusion, [0, tMax], y0, {
          dt: sim.solverDefaults?.sdeDt || 0.01,
          nPaths: sdeParams._nPaths || 20,
          seed: sdeParams._seed || 42,
        });

        const elapsed = Math.round(performance.now() - start);
        setSdeResult(sdeRes);
        setResult(null);
        setSolverInfo({
          method: `Euler-Maruyama (dt=${sim.solverDefaults?.sdeDt || 0.01}, ${sdeParams._nPaths || 20} Pfade)`,
          success: true,
          message: 'OK',
          steps: Math.ceil(tMax / (sim.solverDefaults?.sdeDt || 0.01)),
          elapsed,
        });
      } else {
        // Deterministic ODE mode: RK45
        const rhs = (t, y) => sim.rhs(t, y, exogFuncs, params);
        const sol = solveODE(rhs, [0, tMax], y0, {
          rtol: sim.solverDefaults?.rtol || 1e-8,
          atol: sim.solverDefaults?.atol || 1e-10,
          maxStep: sim.solverDefaults?.maxStep || 0.1,
          tEval,
        });

        const elapsed = Math.round(performance.now() - start);
        setResult(sol);
        setSdeResult(null);
        setSolverInfo({
          method: 'RK45 (Dormand-Prince)',
          success: sol.success,
          message: sol.message,
          steps: sol.t.length,
          elapsed,
        });
      }
    } catch (err) {
      setSolverInfo({
        method: sdeEnabled ? 'Euler-Maruyama' : 'RK45',
        success: false,
        message: err.message,
        steps: 0,
        elapsed: Math.round(performance.now() - start),
      });
    }

    setRunning(false);
  }, [sim, params, initConds, exogConfigs, sdeEnabled, sdeParams, solverSettings]);

  return (
    <div className="sim-view">
      {/* Header */}
      <div className="sim-header">
        <h2 className="sim-title">
          <span className="sim-title-id">{sim.id} {sim.eqId}</span>
          {sim.title}
          <span className="sim-title-section">{sim.section}</span>
        </h2>
      </div>

      <div className="sim-content">
        {/* Left: Controls */}
        <div className="sim-controls">
          {/* Presets */}
          <div className="presets-panel">
            <h3 className="panel-title">Regime / Presets</h3>
            <div className="presets-grid">
              {sim.presets.map((preset, i) => (
                <button
                  key={i}
                  className="preset-btn"
                  onClick={() => loadPreset(preset)}
                  title={preset.description}
                >
                  <span className="preset-name">{preset.name}</span>
                </button>
              ))}
            </div>
          </div>

          {/* Initial conditions */}
          <StatePanel
            stateVars={sim.stateVars}
            values={initConds}
            onChange={(name, val) => setInitConds(prev => ({ ...prev, [name]: val }))}
          />

          {/* Parameters */}
          <ParamPanel
            paramDefs={sim.parameters}
            values={params}
            onChange={(name, val) => setParams(prev => ({ ...prev, [name]: val }))}
          />

          {/* Exogenous functions */}
          <div className="exog-panel">
            <h3 className="panel-title">Exogene Variablen</h3>
            {sim.exogenous.map(v => (
              <FuncSelector
                key={v.name}
                varDef={v}
                funcType={exogConfigs[v.name].type}
                funcParams={exogConfigs[v.name].params}
                onChange={conf => setExogConfigs(prev => ({ ...prev, [v.name]: conf }))}
              />
            ))}
          </div>

          {/* SDE mode */}
          <SdePanel
            sdeConfig={sim.sdeConfig}
            values={sdeParams}
            enabled={sdeEnabled}
            onToggle={setSdeEnabled}
            onChange={(name, val) => setSdeParams(prev => ({ ...prev, [name]: val }))}
          />

          {/* Solver settings */}
          <SolverPanel
            settings={solverSettings}
            onChange={(name, val) => setSolverSettings(prev => ({ ...prev, [name]: val }))}
          />

          {/* Run button */}
          <button
            className="run-btn"
            onClick={runSimulation}
            disabled={running}
          >
            {running ? '⏳ Berechne...' : '▶ Simulieren'}
          </button>
        </div>

        {/* Right: Results */}
        <div className="sim-results">
          <PlotPanel
            result={result}
            sdeResult={sdeResult}
            sim={sim}
            exogFuncs={exogFuncsRef.current}
            params={params}
          />
          <MetadataPanel sim={sim} solverInfo={solverInfo} />
        </div>
      </div>
    </div>
  );
}
