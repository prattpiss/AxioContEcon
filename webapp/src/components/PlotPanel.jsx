import React, { useMemo } from 'react';
import Plot from 'react-plotly.js';

// Color palette for snapshot lines
const SNAP_COLORS = ['#2563eb', '#7c3aed', '#059669', '#d97706', '#dc2626', '#6366f1', '#0891b2', '#be185d'];

/**
 * Interactive plot panel using Plotly.
 * Handles both scalar (time-series) and spatial (PDE profile) simulations.
 */
export default function PlotPanel({ result, sim, exogFuncs, params, sdeResult }) {
  // Detect spatial mode
  const spatialVar = sim.stateVars.find(v => v.spatial);
  const isSpatial = !!spatialVar;
  const NX = spatialVar?.nx || 0;
  const domainLength = spatialVar?.domainLength || 100;

  // ═══════════════════════════════════════════════
  // SPATIAL MODE: ρ(x) profiles at time snapshots
  // ═══════════════════════════════════════════════
  const spatialPlot = useMemo(() => {
    if (!isSpatial || !result || !result.y || result.y.length < NX) return null;
    const t = result.t;
    const nT = t.length;
    if (nT === 0) return null;

    // Build x coordinates
    const x = Array.from({ length: NX }, (_, i) => (i / (NX - 1)) * domainLength);

    // Pick ~6 time snapshots (evenly spaced including t=0 and t=T)
    const nSnaps = Math.min(6, nT);
    const snapIndices = [];
    for (let s = 0; s < nSnaps; s++) {
      snapIndices.push(Math.round(s * (nT - 1) / (nSnaps - 1)));
    }

    const traces = snapIndices.map((idx, si) => {
      const profile = new Array(NX);
      for (let j = 0; j < NX; j++) profile[j] = result.y[j][idx];
      return {
        x, y: profile,
        type: 'scatter', mode: 'lines',
        line: { color: SNAP_COLORS[si % SNAP_COLORS.length], width: 2 },
        name: `t = ${t[idx].toFixed(0)}`,
      };
    });

    return { x, traces };
  }, [result, isSpatial, NX, domainLength]);

  // ═══════════════════════════════════════════════
  // SPATIAL: derived outputs vs time (mass, x_cm, etc.)
  // ═══════════════════════════════════════════════
  const derivedTraces = useMemo(() => {
    if (!isSpatial || !result || !sim.derivedOutputs || result.y.length < NX) return [];
    const t = result.t;
    const colors = ['#2563eb', '#dc2626', '#059669', '#d97706'];
    return sim.derivedOutputs.map((dout, di) => {
      const y = t.map((ti, idx) => {
        const yi = new Array(NX);
        for (let j = 0; j < NX; j++) yi[j] = result.y[j][idx];
        return dout.compute(ti, yi, exogFuncs, params);
      });
      return {
        x: t, y,
        type: 'scatter', mode: 'lines',
        line: { color: colors[di % colors.length], width: 2 },
        name: `${dout.label}${dout.unit ? ' [' + dout.unit + ']' : ''}`,
      };
    });
  }, [result, isSpatial, sim, exogFuncs, params, NX]);

  // ═══════════════════════════════════════════════
  // SPATIAL: term decomposition at midpoint vs time
  // ═══════════════════════════════════════════════
  const spatialTermTraces = useMemo(() => {
    if (!isSpatial || !result || !sim.terms || result.y.length < NX) return [];
    const t = result.t;
    return sim.terms.map(term => {
      const y = t.map((ti, idx) => {
        const yi = new Array(NX);
        for (let j = 0; j < NX; j++) yi[j] = result.y[j][idx];
        return term.compute(ti, yi, exogFuncs, params);
      });
      return {
        x: t, y,
        type: 'scatter', mode: 'lines',
        line: { color: term.color, width: 1.5 },
        name: term.label,
      };
    });
  }, [result, isSpatial, sim, exogFuncs, params, NX]);

  // ═══════════════════════════════════════════════
  // SCALAR MODE (existing logic)
  // ═══════════════════════════════════════════════
  const plotData = useMemo(() => {
    if (isSpatial) return null; // handled by spatialPlot
    if (!result && !sdeResult) return null;

    const traces = [];
    const t = result?.t || sdeResult?.t;
    if (!t || t.length === 0) return null;

    // ── State variables ──
    if (sdeResult && sdeResult.paths) {
      for (let p = 0; p < sdeResult.paths.length; p++) {
        traces.push({
          x: t,
          y: sdeResult.paths[p][0],
          type: 'scatter', mode: 'lines',
          line: { color: 'rgba(37, 99, 235, 0.12)', width: 0.8 },
          showlegend: p === 0,
          name: `MC Pfade (${sdeResult.paths.length})`,
          hoverinfo: 'skip',
        });
      }
      traces.push({
        x: t, y: sdeResult.mean[0],
        type: 'scatter', mode: 'lines',
        line: { color: '#2563eb', width: 2.5 },
        name: 'E[p(t)]',
      });
      const upper = sdeResult.mean[0].map((m, i) => m + sdeResult.std[0][i]);
      const lower = sdeResult.mean[0].map((m, i) => m - sdeResult.std[0][i]);
      traces.push({
        x: [...t, ...t.slice().reverse()],
        y: [...upper, ...lower.slice().reverse()],
        type: 'scatter', fill: 'toself',
        fillcolor: 'rgba(37, 99, 235, 0.1)',
        line: { width: 0 },
        showlegend: true, name: '±1σ',
        hoverinfo: 'skip',
      });
    } else if (result) {
      sim.stateVars.forEach((v, i) => {
        traces.push({
          x: t, y: result.y[i],
          type: 'scatter', mode: 'lines',
          line: { color: '#2563eb', width: 2.5 },
          name: v.label,
        });
      });
    }

    return { t, traces };
  }, [result, sdeResult, sim, isSpatial]);

  // ── Scalar term decomposition ──
  const termTraces = useMemo(() => {
    if (isSpatial) return []; // handled by spatialTermTraces
    if (!result || !sim.terms) return [];
    const t = result.t;
    return sim.terms.map(term => {
      const y = t.map((ti, idx) => {
        const yi = sim.stateVars.map((_, j) => result.y[j][idx]);
        return term.compute(ti, yi, exogFuncs, params);
      });
      return {
        x: t, y,
        type: 'scatter', mode: 'lines',
        line: { color: term.color, width: 1.5 },
        name: term.label,
      };
    });
  }, [result, sim, exogFuncs, params, isSpatial]);

  // ── Exogenous functions ──
  const exogTraces = useMemo(() => {
    if (!result && !sdeResult) return [];
    const t = result?.t || sdeResult?.t;
    if (!t) return [];
    const colors = ['#8b5cf6', '#06b6d4', '#f59e0b', '#10b981'];
    return sim.exogenous.map((exDef, i) => {
      const fn = exogFuncs[exDef.name];
      if (!fn) return null;
      return {
        x: t,
        y: t.map(ti => fn(ti)),
        type: 'scatter', mode: 'lines',
        line: { color: colors[i % colors.length], width: 1.5 },
        name: exDef.label,
      };
    }).filter(Boolean);
  }, [result, sdeResult, sim, exogFuncs]);

  // ── No data yet ──
  if (!spatialPlot && !plotData) {
    return <div className="plot-empty">Drücke ▶ Simulieren um zu starten</div>;
  }

  const commonLayout = {
    margin: { l: 60, r: 20, t: 35, b: 45 },
    font: { family: 'Inter, system-ui, sans-serif', size: 11 },
    paper_bgcolor: 'transparent',
    plot_bgcolor: '#fafafa',
    legend: { orientation: 'h', y: -0.15, font: { size: 10 } },
    hovermode: 'x unified',
  };

  // ═══════════════════════════════════════════════
  // SPATIAL RENDERING
  // ═══════════════════════════════════════════════
  if (isSpatial && spatialPlot) {
    return (
      <div className="plot-panel">
        {/* 1: Spatial profile snapshots ρ(x) */}
        <div className="plot-container">
          <Plot
            data={spatialPlot.traces}
            layout={{
              ...commonLayout,
              title: { text: `${spatialVar.label} — Räumliche Profile`, font: { size: 13 } },
              xaxis: { title: `x [km]`, gridcolor: '#e5e7eb' },
              yaxis: { title: spatialVar.unit || '', gridcolor: '#e5e7eb' },
            }}
            config={{ responsive: true, displayModeBar: true, displaylogo: false }}
            style={{ width: '100%', height: '370px' }}
            useResizeHandler
          />
        </div>

        {/* 2: Derived outputs vs time (mass, x_cm, etc.) */}
        {derivedTraces.length > 0 && derivedTraces.map((trace, i) => (
          <div className="plot-container" key={`derived-${i}`}>
            <Plot
              data={[trace]}
              layout={{
                ...commonLayout,
                title: { text: trace.name, font: { size: 13 } },
                xaxis: { title: 't [Zeiteinheiten]', gridcolor: '#e5e7eb' },
                yaxis: { title: '', gridcolor: '#e5e7eb' },
              }}
              config={{ responsive: true, displayModeBar: false, displaylogo: false }}
              style={{ width: '100%', height: '240px' }}
              useResizeHandler
            />
          </div>
        ))}

        {/* 3: Term decomposition at midpoint vs time */}
        {spatialTermTraces.length > 0 && (
          <div className="plot-container">
            <Plot
              data={spatialTermTraces}
              layout={{
                ...commonLayout,
                title: { text: 'Flusskomponenten bei x = L/2', font: { size: 13 } },
                xaxis: { title: 't [Zeiteinheiten]', gridcolor: '#e5e7eb' },
                yaxis: { title: 'j [Einh./(km·a)]', gridcolor: '#e5e7eb' },
              }}
              config={{ responsive: true, displayModeBar: false, displaylogo: false }}
              style={{ width: '100%', height: '260px' }}
              useResizeHandler
            />
          </div>
        )}

        {/* 4: Exogenous functions */}
        <div className="plot-container">
          <Plot
            data={exogTraces}
            layout={{
              ...commonLayout,
              title: { text: 'Exogene Variablen', font: { size: 13 } },
              xaxis: { title: 't [Zeiteinheiten]', gridcolor: '#e5e7eb' },
              yaxis: { title: '', gridcolor: '#e5e7eb' },
            }}
            config={{ responsive: true, displayModeBar: false, displaylogo: false }}
            style={{ width: '100%', height: '260px' }}
            useResizeHandler
          />
        </div>
      </div>
    );
  }

  // ═══════════════════════════════════════════════
  // SCALAR RENDERING (unchanged)
  // ═══════════════════════════════════════════════
  return (
    <div className="plot-panel">
      <div className="plot-container">
        <Plot
          data={plotData.traces}
          layout={{
            ...commonLayout,
            title: { text: `${sim.stateVars[0]?.label || 'y'}(t)`, font: { size: 13 } },
            xaxis: { title: 't [Zeiteinheiten]', gridcolor: '#e5e7eb' },
            yaxis: { title: sim.stateVars[0]?.unit || '', gridcolor: '#e5e7eb' },
          }}
          config={{ responsive: true, displayModeBar: true, displaylogo: false }}
          style={{ width: '100%', height: '340px' }}
          useResizeHandler
        />
      </div>
      {termTraces.length > 0 && (
        <div className="plot-container">
          <Plot
            data={termTraces}
            layout={{
              ...commonLayout,
              title: { text: 'Terme (Dekomposition der Dynamik)', font: { size: 13 } },
              xaxis: { title: 't [Zeiteinheiten]', gridcolor: '#e5e7eb' },
              yaxis: { title: 'ṗ [Einh./a]', gridcolor: '#e5e7eb' },
            }}
            config={{ responsive: true, displayModeBar: false, displaylogo: false }}
            style={{ width: '100%', height: '260px' }}
            useResizeHandler
          />
        </div>
      )}
      <div className="plot-container">
        <Plot
          data={exogTraces}
          layout={{
            ...commonLayout,
            title: { text: 'Exogene Variablen', font: { size: 13 } },
            xaxis: { title: 't [Zeiteinheiten]', gridcolor: '#e5e7eb' },
            yaxis: { title: '', gridcolor: '#e5e7eb' },
          }}
          config={{ responsive: true, displayModeBar: false, displaylogo: false }}
          style={{ width: '100%', height: '260px' }}
          useResizeHandler
        />
      </div>
    </div>
  );
}
