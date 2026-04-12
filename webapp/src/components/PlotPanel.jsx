import React, { useMemo } from 'react';
import Plot from 'react-plotly.js';

/**
 * Interactive plot panel using Plotly.
 * Shows: (1) state variables, (2) individual terms, (3) exogenous functions.
 */
export default function PlotPanel({ result, sim, exogFuncs, params, sdeResult }) {
  const plotData = useMemo(() => {
    if (!result && !sdeResult) return null;

    const traces = [];
    const t = result?.t || sdeResult?.t;
    if (!t || t.length === 0) return null;

    // ── State variables ──
    if (sdeResult && sdeResult.paths) {
      // SDE: show individual paths (faded) + mean (bold) + std band
      for (let p = 0; p < sdeResult.paths.length; p++) {
        traces.push({
          x: t,
          y: sdeResult.paths[p][0],
          type: 'scatter',
          mode: 'lines',
          line: { color: 'rgba(37, 99, 235, 0.12)', width: 0.8 },
          showlegend: p === 0,
          name: `MC Pfade (${sdeResult.paths.length})`,
          hoverinfo: 'skip',
        });
      }
      // Mean
      traces.push({
        x: t,
        y: sdeResult.mean[0],
        type: 'scatter',
        mode: 'lines',
        line: { color: '#2563eb', width: 2.5 },
        name: 'E[p(t)]',
      });
      // ±1σ band
      const upper = sdeResult.mean[0].map((m, i) => m + sdeResult.std[0][i]);
      const lower = sdeResult.mean[0].map((m, i) => m - sdeResult.std[0][i]);
      traces.push({
        x: [...t, ...t.slice().reverse()],
        y: [...upper, ...lower.slice().reverse()],
        type: 'scatter',
        fill: 'toself',
        fillcolor: 'rgba(37, 99, 235, 0.1)',
        line: { width: 0 },
        showlegend: true,
        name: '±1σ',
        hoverinfo: 'skip',
      });
    } else if (result) {
      // Deterministic
      sim.stateVars.forEach((v, i) => {
        traces.push({
          x: t,
          y: result.y[i],
          type: 'scatter',
          mode: 'lines',
          line: { color: '#2563eb', width: 2.5 },
          name: v.label,
        });
      });
    }

    return { t, traces };
  }, [result, sdeResult, sim]);

  // ── Term decomposition ──
  const termTraces = useMemo(() => {
    if (!result || !sim.terms) return [];
    const t = result.t;
    return sim.terms.map(term => {
      const y = t.map((ti, idx) => {
        const yi = sim.stateVars.map((_, j) => result.y[j][idx]);
        return term.compute(ti, yi, exogFuncs, params);
      });
      return {
        x: t,
        y,
        type: 'scatter',
        mode: 'lines',
        line: { color: term.color, width: 1.5 },
        name: term.label,
      };
    });
  }, [result, sim, exogFuncs, params]);

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
        type: 'scatter',
        mode: 'lines',
        line: { color: colors[i % colors.length], width: 1.5 },
        name: exDef.label,
      };
    }).filter(Boolean);
  }, [result, sdeResult, sim, exogFuncs]);

  if (!plotData) {
    return <div className="plot-empty">Drücke ▶ Simulieren um zu starten</div>;
  }

  const commonLayout = {
    margin: { l: 60, r: 20, t: 35, b: 45 },
    font: { family: 'Inter, system-ui, sans-serif', size: 11 },
    paper_bgcolor: 'transparent',
    plot_bgcolor: '#fafafa',
    xaxis: { title: 't [Zeiteinheiten]', gridcolor: '#e5e7eb' },
    legend: { orientation: 'h', y: -0.15, font: { size: 10 } },
    hovermode: 'x unified',
  };

  return (
    <div className="plot-panel">
      {/* Main state plot */}
      <div className="plot-container">
        <Plot
          data={plotData.traces}
          layout={{
            ...commonLayout,
            title: { text: `${sim.stateVars[0]?.label || 'y'}(t)`, font: { size: 13 } },
            yaxis: { title: sim.stateVars[0]?.unit || '', gridcolor: '#e5e7eb' },
          }}
          config={{ responsive: true, displayModeBar: true, displaylogo: false }}
          style={{ width: '100%', height: '340px' }}
          useResizeHandler
        />
      </div>

      {/* Term decomposition */}
      {termTraces.length > 0 && (
        <div className="plot-container">
          <Plot
            data={termTraces}
            layout={{
              ...commonLayout,
              title: { text: 'Terme (Dekomposition der Dynamik)', font: { size: 13 } },
              yaxis: { title: 'ṗ [Einh./a]', gridcolor: '#e5e7eb' },
            }}
            config={{ responsive: true, displayModeBar: false, displaylogo: false }}
            style={{ width: '100%', height: '260px' }}
            useResizeHandler
          />
        </div>
      )}

      {/* Exogenous functions */}
      <div className="plot-container">
        <Plot
          data={exogTraces}
          layout={{
            ...commonLayout,
            title: { text: 'Exogene Variablen', font: { size: 13 } },
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
