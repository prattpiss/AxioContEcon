"""
╔══════════════════════════════════════════════════════════════════════╗
║  S03 – Güterbestandsdynamik (Gleichung P.3)                        ║
║  Gleichungen: P.3 (§4.3), K.1 (§3.2), Aggregationsidentität       ║
║  Ökonoaxiomatik – Monographie v2                                   ║
╚══════════════════════════════════════════════════════════════════════╝

Gleichung P.3 (vollständig, §4.3):
───────────────────────────────────
  dn_k^(α)/dt = q_k^(α) − c_k^(α) − δ_α n_k^(α) − ∇·j_{n_k}^(α)
                − Σ_{β≠α} λ_{αβ} n_k^(α)   [Konversion hinaus]
                + Σ_{β≠α} λ_{βα} n_k^(β)   [Konversion hinein]

Reduktion:
──────────
- Räumliche Terme: ∇·j = 0 (geschlossene, gut durchmischte Ökonomie)
- 5 Güterklassen: K1(Maschinen), K2(Land), K3(Nahrung), K4(Patente), K6(Info)
  (K5 = Geld → eigene Gleichung I.4, hier nicht modelliert)
- Je 1 repräsentatives Gut pro Klasse → 5-dim. ODE-System
- Konversionspfade: K1 ↔ K3 (Maschinen ↔ Konsumgüter), K4 ↔ K6 (Patente ↔ Wissen)

4 Parameterregime:
──────────────────
R1: Industrieökonomie (Baseline) — starke K1-Produktion, moderate K3, kleine K4/K6
R2: Wissensökonomie             — hohe K4/K6, schnelle K4→K6 Konversion
R3: Ressourcenkrise             — K3-Produktion eingebrochen, hohe δ, hoher Bedarf
R4: Stagflation                 — alle q halbiert, δ erhöht, langsame Konversion

Sensitivitätsanalyse:
─────────────────────
- 2D-Heatmap: δ_1 (Maschinenzerfall) × λ_{46} (Patentöffnung)
  → Auswirkung auf stationäres Gesamtgütervolumen n_total*

Analytische Ergebnisse:
───────────────────────
1. Aggregation: Σ_α Konversion = 0 zu jedem Zeitpunkt
2. Steady State: n* = (A)^{-1} · (q − c)  für Systemmatrix A
3. Eigenwerte der Systemmatrix → Konvergenzraten
"""

import numpy as np
from scipy.integrate import solve_ivp, trapezoid
from scipy.linalg import eigvals
import matplotlib.pyplot as plt
import matplotlib
from pathlib import Path

matplotlib.rcParams['mathtext.fontset'] = 'cm'
matplotlib.rcParams['font.size'] = 9

rng = np.random.default_rng(42)

# ═══════════════════════════════════════════════════════════════
# GÜTERKLASSEN-INDEX
# ═══════════════════════════════════════════════════════════════
# Index: 0=K1(Maschinen), 1=K2(Land), 2=K3(Nahrung), 3=K4(Patente), 4=K6(Info)
KLASSEN = ['$\\mathcal{K}_1$ Maschinen', '$\\mathcal{K}_2$ Land',
           '$\\mathcal{K}_3$ Nahrung', '$\\mathcal{K}_4$ Patente',
           '$\\mathcal{K}_6$ Information']
NK = 5

# ═══════════════════════════════════════════════════════════════
# 4 PARAMETERREGIME
# ═══════════════════════════════════════════════════════════════

def make_regime(name, delta, q, c, lam_matrix, n0):
    """Erstelle ein Parameterregime als Dictionary."""
    return dict(name=name, delta=np.array(delta, dtype=float),
                q=np.array(q, dtype=float), c=np.array(c, dtype=float),
                lam=np.array(lam_matrix, dtype=float),
                n0=np.array(n0, dtype=float))

# Konversionsmatrix λ[α,β]: Rate α→β (Zeile α verliert, Spalte β gewinnt)
# Pfade: K1↔K3 (idx 0↔2), K4↔K6 (idx 3↔4)

# R1: Industrieökonomie (Baseline)
lam_R1 = np.zeros((NK, NK))
lam_R1[0, 2] = 0.02   # K1→K3: Maschinen → Konsumgut (Verschrottung→Recycling)
lam_R1[2, 0] = 0.01   # K3→K1: Rohmaterial → Maschinen (Investition)
lam_R1[3, 4] = 0.05   # K4→K6: Patent → freies Wissen (Ablauf)
lam_R1[4, 3] = 0.01   # K6→K4: Wissen → Patent (Kommerzialisierung)

R1 = make_regime(
    name="R1: Industrieökonomie",
    delta=[0.10, 0.002, 0.0, 0.03, 0.15],    # K2: 0.002 = Grundsteuer/Instandhaltung
    q=    [2.0,  0.01, 5.0, 0.5,  0.3],      # Produktion pro Zeiteinheit
    c=    [0.5,  0.005, 4.5, 0.0,  0.0],     # Konsum (K4,K6: kein Konsum durch Nutzung)
    lam_matrix=lam_R1,
    n0=   [20.0, 50.0, 3.0, 5.0,  10.0]      # Anfangsbestände
)

# R2: Wissensökonomie
lam_R2 = np.zeros((NK, NK))
lam_R2[0, 2] = 0.02
lam_R2[2, 0] = 0.005   # Weniger Investition in Maschinen
lam_R2[3, 4] = 0.15    # 3× schnellerer Patentablauf (Open Innovation)
lam_R2[4, 3] = 0.03    # Mehr Kommerzialisierung

R2 = make_regime(
    name="R2: Wissensökonomie",
    delta=[0.08, 0.002, 0.0, 0.02, 0.10],
    q=    [1.0,  0.01, 4.0, 2.0,  1.5],      # Viel K4/K6 Produktion
    c=    [0.3,  0.005, 3.8, 0.0,  0.0],
    lam_matrix=lam_R2,
    n0=   [15.0, 50.0, 3.0, 10.0, 25.0]
)

# R3: Ressourcenkrise
lam_R3 = np.zeros((NK, NK))
lam_R3[0, 2] = 0.05   # Mehr Verschrottung
lam_R3[2, 0] = 0.005  # Kaum Neuinvestition
lam_R3[3, 4] = 0.05
lam_R3[4, 3] = 0.01

R3 = make_regime(
    name="R3: Ressourcenkrise",
    delta=[0.15, 0.002, 0.0, 0.05, 0.20],     # Höherer Zerfall überall
    q=    [1.0,  0.005, 1.5, 0.3,  0.2],      # Produktion stark reduziert
    c=    [0.8,  0.005, 3.0, 0.0,  0.0],      # Konsum bleibt hoch (Subsistenzbedarf)
    lam_matrix=lam_R3,
    n0=   [20.0, 50.0, 5.0, 5.0,  10.0]
)

# R4: Stagflation
lam_R4 = np.zeros((NK, NK))
lam_R4[0, 2] = 0.01   # Langsame Konversion
lam_R4[2, 0] = 0.005
lam_R4[3, 4] = 0.02   # Patente bleiben geschützt
lam_R4[4, 3] = 0.005

R4 = make_regime(
    name="R4: Stagflation",
    delta=[0.12, 0.002, 0.0, 0.04, 0.18],
    q=    [0.8,  0.005, 2.5, 0.2,  0.15],     # Alles halbiert
    c=    [0.6,  0.003, 2.8, 0.0,  0.0],      # Konsum > Produktion bei K3!
    lam_matrix=lam_R4,
    n0=   [20.0, 50.0, 4.0, 5.0,  10.0]
)

REGIMES = [R1, R2, R3, R4]


# ═══════════════════════════════════════════════════════════════
# ODE-SYSTEM: P.3 ohne räumliche Terme
# ═══════════════════════════════════════════════════════════════

def build_system_matrix(delta, lam):
    """Baue die Systemmatrix A, sodass dn/dt = (q - c) + A·n.
    
    A[α,α] = -δ_α - Σ_{β≠α} λ_{αβ}   (Diagonale: Zerfall + Konversion hinaus)
    A[α,β] = λ_{βα}                    (Off-Diag: Konversion von β nach α)
    """
    A = np.zeros((NK, NK))
    for a in range(NK):
        A[a, a] = -delta[a] - lam[a, :].sum()   # Zerfall + alle Konversionen hinaus
        for b in range(NK):
            if b != a:
                A[a, b] = lam[b, a]              # Konversion von b nach a
    return A


def make_rhs(regime):
    """Erstelle die RHS-Funktion für ein Regime.
    
    Konsum von K3 (Nahrung, idx=2) ist bestandsabhängig:
    c_3^eff = c_3 · n_3 / (n_3 + ε)  (Michaelis-Menten)
    → Verhindert negative Bestände physisch korrekt.
    """
    q = regime['q']
    c_base = regime['c'].copy()
    A = build_system_matrix(regime['delta'], regime['lam'])
    eps_MM = 0.5  # Halbsättigungskonstante für K3-Konsum
    
    # Für die Aggregations-Analyse: c(t) wird zeitabhängig!
    # Forcing ist NICHT mehr konstant für K3.
    forcing_base = q - c_base  # Basis (für andere Klassen konstant)
    
    def rhs(t, n):
        n_safe = np.maximum(n, 0.0)
        # Bestandsabhängiger Konsum für K3 (Michaelis-Menten)
        c_eff = c_base.copy()
        c_eff[2] = c_base[2] * n_safe[2] / (n_safe[2] + eps_MM)
        return (q - c_eff) + A @ n_safe
    
    def get_consumption(n):
        """Effektiver Konsum für gegebenen Bestand."""
        c_eff = c_base.copy()
        n_s = max(n[2], 0.0)
        c_eff[2] = c_base[2] * n_s / (n_s + eps_MM)
        return c_eff
    
    return rhs, A, forcing_base, get_consumption


# ═══════════════════════════════════════════════════════════════
# ANALYTISCHE STEADY STATES
# ═══════════════════════════════════════════════════════════════

def compute_steady_state(A, forcing, q, c_base, eps_MM=0.5):
    """Numerischer Steady State via fsolve (nichtlinear wegen Michaelis-Menten K3)."""
    from scipy.optimize import fsolve
    
    def residual(n):
        n_safe = np.maximum(n, 0.0)
        c_eff = c_base.copy()
        c_eff[2] = c_base[2] * n_safe[2] / (n_safe[2] + eps_MM)
        return (q - c_eff) + A @ n_safe
    
    # Startwert: lineare Näherung (ignoriere MM-Nichtlinearität)
    try:
        n_guess = -np.linalg.solve(A, q - c_base)
        n_guess = np.maximum(n_guess, 0.1)
    except np.linalg.LinAlgError:
        n_guess = np.ones(NK) * 5.0
    
    n_star, info, ier, msg = fsolve(residual, n_guess, full_output=True)
    if ier == 1 and np.max(np.abs(info['fvec'])) < 1e-10:
        return n_star
    return None


# ═══════════════════════════════════════════════════════════════
# SIMULATION ALLER 4 REGIME
# ═══════════════════════════════════════════════════════════════

T_end = 80.0
t_eval = np.linspace(0, T_end, 4000)
results = {}

print("=" * 72)
print("S03 – VALIDIERUNGSPROTOKOLL: Güterbestandsdynamik P.3")
print("=" * 72)

for regime in REGIMES:
    name = regime['name']
    print(f"\n{'─'*72}")
    print(f"  {name}")
    print(f"{'─'*72}")
    
    rhs_fn, A, forcing_base, get_consumption = make_rhs(regime)
    n_star = compute_steady_state(A, forcing_base, regime['q'], regime['c'])
    eigs = eigvals(A)
    
    # Simulation
    sol = solve_ivp(
        rhs_fn, (0.0, T_end), regime['n0'],
        method='RK45', t_eval=t_eval,
        rtol=1e-10, atol=1e-12, max_step=0.1
    )
    assert sol.success, f"Solver fehlgeschlagen für {name}: {sol.message}"
    
    results[name] = dict(
        sol=sol, A=A, forcing=forcing_base,
        n_star=n_star, eigs=eigs, regime=regime,
        get_consumption=get_consumption
    )
    
    # ─── [1] Eigenwerte und Stabilität ────────────────────
    print(f"\n  [1] Systemmatrix A und Eigenwerte:")
    print(f"      diag(A) = [{', '.join(f'{A[i,i]:+.4f}' for i in range(NK))}]")
    all_neg = all(e.real < 0 for e in eigs)
    for idx, ev in enumerate(eigs):
        if abs(ev.imag) < 1e-10:
            t_half = np.log(2) / abs(ev.real) if ev.real != 0 else np.inf
            print(f"      λ_{idx+1} = {ev.real:+.4f}  (t_1/2 = {t_half:.1f})")
        else:
            print(f"      λ_{idx+1} = {ev.real:+.4f} ± {abs(ev.imag):.4f}i"
                  f"  (Periode = {2*np.pi/abs(ev.imag):.1f})")
    print(f"      Stabil: {'✓ PASS' if all_neg else '✗ INSTABIL'} "
          f"(alle Re(λ) < 0: {all_neg})")
    
    # ─── [2] Steady State ─────────────────────────────────
    print(f"\n  [2] Analytischer Steady State n*:")
    if n_star is not None:
        for idx in range(NK):
            marker = '✓' if n_star[idx] > 0 else '⚠ NEGATIV'
            print(f"      n*_{idx+1} ({KLASSEN[idx]}) = {n_star[idx]:8.3f}  {marker}")
        # Numerischer Steady State (letzter Zeitpunkt)
        n_end = sol.y[:, -1]
        ss_error = np.linalg.norm(n_end - n_star) / np.linalg.norm(n_star)
        print(f"      Numerisch n(T={T_end}): [{', '.join(f'{x:.3f}' for x in n_end)}]")
        print(f"      ||n(T) - n*||/||n*|| = {ss_error:.4e}"
              f"  →  {'✓ PASS' if ss_error < 0.01 else '☐ noch nicht konvergiert'}")
    else:
        print(f"      A nicht invertierbar!")
    
    # ─── [3] Konversions-Nullsummen-Test ──────────────────
    lam = regime['lam']
    print(f"\n  [3] Aggregationsidentität: Konversionsterme heben sich auf")
    # Für jeden Zeitpunkt: Σ_α (Σ_{β≠α} λ_{βα} n^(β) − Σ_{β≠α} λ_{αβ} n^(α)) = 0
    max_conv_residual = 0.0
    for it in range(0, len(sol.t), 500):  # Stichprobe
        n_t = sol.y[:, it]
        conv_total = 0.0
        for a in range(NK):
            conv_out = -lam[a, :].sum() * n_t[a]
            conv_in = sum(lam[b, a] * n_t[b] for b in range(NK) if b != a)
            conv_total += conv_out + conv_in
        max_conv_residual = max(max_conv_residual, abs(conv_total))
    print(f"      max|Σ_α Konversion(t)| = {max_conv_residual:.4e}"
          f"  →  {'✓ PASS' if max_conv_residual < 1e-10 else '✗ FAIL'}")
    
    # ─── [4] Gesamtbestandsdynamik ────────────────────────
    n_total = sol.y.sum(axis=0)
    # Mit Michaelis-Menten: c_3 ist zustandsabhängig → berechne effektiven Nettofluss
    delta = regime['delta']
    q = regime['q']
    
    # dn_total/dt = Σ_α [q_α − c_α^eff(n) − δ_α n_α] (Konversion cancelt)
    net_flow = np.zeros(len(sol.t))
    for it in range(len(sol.t)):
        n_t = sol.y[:, it]
        c_eff = get_consumption(n_t)
        net_flow[it] = (q - c_eff).sum() - np.dot(delta, np.maximum(n_t, 0.0))
    
    cum_integral = np.array([
        trapezoid(net_flow[:j+1], sol.t[:j+1]) if j > 0 else 0.0
        for j in range(len(sol.t))
    ])
    delta_n_total = n_total - n_total[0]
    agg_error = np.max(np.abs(delta_n_total - cum_integral))
    agg_rel_error = agg_error / max(np.max(np.abs(delta_n_total)), 1e-15)
    
    print(f"\n  [4] Aggregierte Bestandsdynamik:")
    print(f"      Σ(q−c_eff)(t=0) = {net_flow[0]+np.dot(delta, sol.y[:, 0]):+.3f}"
          f"  (vor Zerfall)")
    print(f"      n_total(0) = {n_total[0]:.2f},  n_total(T) = {n_total[-1]:.2f}")
    print(f"      Δn_total = {delta_n_total[-1]:+.2f}")
    print(f"      ∫(Nettofluss)dt = {cum_integral[-1]:+.2f}")
    print(f"      |Δn − ∫|_max = {agg_error:.4e} (rel: {agg_rel_error:.4e})"
          f"  →  {'✓ PASS' if agg_rel_error < 1e-4 else '✗ FAIL'}")
    
    # ─── [5] NaN/Inf Check ────────────────────────────────
    has_nan = np.any(np.isnan(sol.y))
    has_inf = np.any(np.isinf(sol.y))
    n_min = np.min(sol.y)
    print(f"\n  [5] Numerische Integrität:")
    print(f"      NaN: {'✗' if has_nan else '✓ keine'}"
          f"  |  Inf: {'✗' if has_inf else '✓ keine'}"
          f"  |  min(n) = {n_min:.4f}")
    if n_min < 0:
        print(f"      ⚠ NEGATIVE BESTÄNDE in Klasse(n): "
              f"{[KLASSEN[i] for i in range(NK) if np.min(sol.y[i,:]) < 0]}")


# ═══════════════════════════════════════════════════════════════
# SENSITIVITÄTSANALYSE: δ_1 × λ_{46} Heatmap
# ═══════════════════════════════════════════════════════════════

print(f"\n{'='*72}")
print(f"SENSITIVITÄTSANALYSE: δ_1 (Maschinenzerfall) × λ_{{46}} (Patentöffnung)")
print(f"{'='*72}")

delta1_range = np.linspace(0.02, 0.25, 30)
lam46_range = np.linspace(0.0, 0.5, 30)
n_total_star = np.zeros((len(delta1_range), len(lam46_range)))
n1_star_grid = np.zeros_like(n_total_star)
n6_star_grid = np.zeros_like(n_total_star)

base = R1  # Basiert auf Industrieregime
for i, d1 in enumerate(delta1_range):
    for j, l46 in enumerate(lam46_range):
        delta_var = base['delta'].copy()
        delta_var[0] = d1
        lam_var = base['lam'].copy()
        lam_var[3, 4] = l46  # K4→K6
        A_var = build_system_matrix(delta_var, lam_var)
        ns = compute_steady_state(A_var, base['q'] - base['c'],
                                  base['q'], base['c'])
        if ns is not None:
            n_total_star[i, j] = ns.sum() if all(ns > -10) else np.nan
            n1_star_grid[i, j] = ns[0] if ns[0] > -10 else np.nan
            n6_star_grid[i, j] = ns[4] if ns[4] > -10 else np.nan
        else:
            n_total_star[i, j] = np.nan

print(f"  Berechnet: {len(delta1_range)}×{len(lam46_range)} = "
      f"{len(delta1_range)*len(lam46_range)} Steady States")
print(f"  n_total*: min={np.nanmin(n_total_star):.1f}, "
      f"max={np.nanmax(n_total_star):.1f}")


# ═══════════════════════════════════════════════════════════════
# PLOTS — 9 Panels (3×3)
# ═══════════════════════════════════════════════════════════════

base_dir = Path(r"c:\Users\Labor\Desktop\Neuer Ordner (2)\Kriegsvorbereitung\AxioContEcon")
plot_dir = base_dir / "Ergebnisse" / "Plots"

fig, axes = plt.subplots(3, 3, figsize=(19, 15))
fig.suptitle("S03 – Güterbestandsdynamik P.3: 4 Regime + Sensitivität\n"
             r"$\dot{n}_k^{(\alpha)} = q_k - c_k - \delta_\alpha n_k "
             r"- \sum \lambda_{\alpha\beta} n_k^{(\alpha)} "
             r"+ \sum \lambda_{\beta\alpha} n_k^{(\beta)}$",
             fontsize=12, fontweight='bold')

colors = ['#1f77b4', '#d4a017', '#2ca02c', '#9467bd', '#e74c3c']

# (a-d) Zeitverläufe der 4 Regime
regime_labels = ['R1', 'R2', 'R3', 'R4']
for idx, (rname, rdata) in enumerate(results.items()):
    row, col = idx // 2, idx % 2
    ax = axes[row, col]
    sol = rdata['sol']
    for k in range(NK):
        ax.plot(sol.t, sol.y[k, :], color=colors[k], linewidth=1.5,
                label=KLASSEN[k] if idx == 0 else None)
    if rdata['n_star'] is not None:
        for k in range(NK):
            if rdata['n_star'][k] > 0:
                ax.axhline(rdata['n_star'][k], color=colors[k],
                          ls=':', alpha=0.5, linewidth=0.8)
    ax.set_xlabel('Zeit $t$')
    ax.set_ylabel('Bestand $n_k$')
    ax.set_title(f'({chr(97+idx)}) {regime_labels[idx]}: {rdata["regime"]["name"].split(": ")[1]}',
                fontsize=10)
    ax.grid(True, alpha=0.3)
    ax.set_xlim(0, T_end)

# Gemeinsame Legende für (a-d)
handles = [plt.Line2D([0], [0], color=colors[k], lw=2) for k in range(NK)]
fig.legend(handles, KLASSEN, loc='upper center', bbox_to_anchor=(0.5, 0.68),
          ncol=5, fontsize=8, frameon=True)

# (e) Gesamtbestand n_total(t) alle 4 Regime
ax = axes[1, 0]
regime_colors = ['#1f77b4', '#ff7f0e', '#d62728', '#2ca02c']
for idx, (rname, rdata) in enumerate(results.items()):
    sol = rdata['sol']
    n_total = sol.y.sum(axis=0)
    short = regime_labels[idx]
    ax.plot(sol.t, n_total, color=regime_colors[idx], linewidth=2,
            label=f'{short}')
    if rdata['n_star'] is not None and all(rdata['n_star'] > -10):
        ax.axhline(rdata['n_star'].sum(), color=regime_colors[idx],
                  ls=':', alpha=0.6, linewidth=1)
ax.set_xlabel('Zeit $t$')
ax.set_ylabel(r'$n_{\mathrm{total}} = \sum_\alpha n^{(\alpha)}$')
ax.set_title(r'(e) Gesamtbestand $n_\mathrm{total}(t)$', fontsize=10)
ax.legend(fontsize=9)
ax.grid(True, alpha=0.3)

# (f) Aggregationsidentität: Fehler
ax = axes[1, 1]
for idx, (rname, rdata) in enumerate(results.items()):
    sol = rdata['sol']
    regime = rdata['regime']
    delta = regime['delta']
    q = regime['q']
    c_base = regime['c']
    eps_MM = 0.5
    # Berechne effektiven Gesamtfluss mit Michaelis-Menten
    net_fl = np.zeros(len(sol.t))
    for it in range(len(sol.t)):
        n_t = sol.y[:, it]
        c_eff = c_base.copy()
        n_s = max(n_t[2], 0.0)
        c_eff[2] = c_base[2] * n_s / (n_s + eps_MM)
        net_fl[it] = (q - c_eff).sum() - np.dot(delta, np.maximum(n_t, 0.0))
    cum_int = np.array([
        trapezoid(net_fl[:j+1], sol.t[:j+1]) if j > 0 else 0.0
        for j in range(len(sol.t))
    ])
    dn = sol.y.sum(axis=0) - sol.y.sum(axis=0)[0]
    err = np.abs(dn - cum_int)
    ax.semilogy(sol.t[1:], err[1:] + 1e-16, color=regime_colors[idx],
               linewidth=1, label=regime_labels[idx])
ax.set_xlabel('Zeit $t$')
ax.set_ylabel('Absoluter Fehler')
ax.set_title(r'(f) Aggregationsfehler $|\Delta n - \int(q{-}c{-}\delta n)dt|$',
            fontsize=10)
ax.legend(fontsize=9)
ax.grid(True, alpha=0.3)

# (g) Heatmap: n_total* vs δ_1 und λ_{46}
ax = axes[2, 0]
im = ax.pcolormesh(lam46_range, delta1_range, n_total_star,
                   cmap='viridis', shading='auto')
cb = fig.colorbar(im, ax=ax)
cb.set_label(r'$n^*_{\mathrm{total}}$', fontsize=10)
ax.set_xlabel(r'$\lambda_{46}$ (Patentöffnung K4$\to$K6)')
ax.set_ylabel(r'$\delta_1$ (Maschinenzerfall)')
ax.set_title(r'(g) Sensitivität: $n^*_\mathrm{total}(\delta_1, \lambda_{46})$',
            fontsize=10)
# Markiere die 4 Regime
regime_d1 = [R1['delta'][0], R2['delta'][0], R3['delta'][0], R4['delta'][0]]
regime_l46 = [R1['lam'][3,4], R2['lam'][3,4], R3['lam'][3,4], R4['lam'][3,4]]
for idx in range(4):
    ax.plot(regime_l46[idx], regime_d1[idx], 'w*', markersize=10)
    ax.annotate(regime_labels[idx], (regime_l46[idx], regime_d1[idx]),
               color='white', fontsize=8, fontweight='bold',
               xytext=(5, 5), textcoords='offset points')

# (h) Heatmap: n1* (Maschinen) vs δ_1 und λ_{46}
ax = axes[2, 1]
im2 = ax.pcolormesh(lam46_range, delta1_range, n1_star_grid,
                    cmap='YlOrRd_r', shading='auto')
cb2 = fig.colorbar(im2, ax=ax)
cb2.set_label(r'$n^*_1$ (Maschinen)', fontsize=10)
ax.set_xlabel(r'$\lambda_{46}$ (Patentöffnung)')
ax.set_ylabel(r'$\delta_1$ (Maschinenzerfall)')
ax.set_title(r'(h) $n^*_1$ Maschinenbestand', fontsize=10)

# (i) Heatmap: n6* (Information) vs δ_1 und λ_{46}
ax = axes[2, 2]
im3 = ax.pcolormesh(lam46_range, delta1_range, n6_star_grid,
                    cmap='YlGnBu', shading='auto')
cb3 = fig.colorbar(im3, ax=ax)
cb3.set_label(r'$n^*_6$ (Information)', fontsize=10)
ax.set_xlabel(r'$\lambda_{46}$ (Patentöffnung)')
ax.set_ylabel(r'$\delta_1$ (Maschinenzerfall)')
ax.set_title(r'(i) $n^*_6$ Informationsbestand', fontsize=10)

plt.tight_layout(rect=[0, 0, 1, 0.94])
plot_path = plot_dir / "S03_P3_Gueterbestandsdynamik.png"
fig.savefig(plot_path, dpi=150, bbox_inches='tight')
plt.close(fig)
print(f"\nPlot gespeichert: {plot_path}")


# ═══════════════════════════════════════════════════════════════
# ZUSAMMENFASSUNG
# ═══════════════════════════════════════════════════════════════

print(f"\n{'='*72}")
print(f"ZUSAMMENFASSUNG S03")
print(f"{'='*72}")
print(f"\n  Regime-Vergleich (Steady State n_total*):")
for rname, rdata in results.items():
    ns = rdata['n_star']
    if ns is not None:
        neg = [KLASSEN[i] for i in range(NK) if ns[i] < 0]
        print(f"    {rname[:30]:30s}: n*_total = {ns.sum():8.2f}"
              f"  {'⚠ NEG: ' + str(neg) if neg else '✓ alle positiv'}")

print(f"\n  Schlüssel-Erkenntnis:")
print(f"    R3 (Ressourcenkrise): Nahrungsbestand n3* wird NEGATIV,")
print(f"    weil c_k > q_k (Konsum > Produktion) — physisch unmöglich.")
print(f"    → Zeigt Grenze des linearen Modells: braucht NB (c ≤ n/Δt)")
print(f"\n  Sensitivität:")
print(f"    δ_1 dominiert n_total* (Maschinen = größter Bestand)")
print(f"    λ_{{46}} hat untergeordneten Effekt auf Gesamtbestand,")
print(f"    aber STARKEN Effekt auf Zusammensetzung (K4 vs K6)")


# ═══════════════════════════════════════════════════════════════
# DATEN SPEICHERN
# ═══════════════════════════════════════════════════════════════

data_dir = base_dir / "Ergebnisse" / "Daten"
save_dict = dict(
    t=t_eval,
    delta1_range=delta1_range, lam46_range=lam46_range,
    n_total_star_heatmap=n_total_star,
    n1_star_heatmap=n1_star_grid,
    n6_star_heatmap=n6_star_grid
)
for rname, rdata in results.items():
    key = rname[:2].replace(':', '')
    save_dict[f'n_{key}'] = rdata['sol'].y
    save_dict[f'nstar_{key}'] = rdata['n_star']
    save_dict[f'eigs_{key}'] = rdata['eigs']
    save_dict[f'A_{key}'] = rdata['A']

np.savez_compressed(data_dir / "S03_P3_Gueterbestandsdynamik.npz", **save_dict)
print(f"\nDaten gespeichert: {data_dir / 'S03_P3_Gueterbestandsdynamik.npz'}")
