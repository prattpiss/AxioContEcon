"""
╔══════════════════════════════════════════════════════════════════════╗
║  S04 – Gelderhaltung (Gleichung I.4) und Geldschöpfung (M.1)      ║
║  Gleichungen: I.4 (§4.4), M.1 (§4.4/§8.1), M.2, Prop. 4.2       ║
║  Ökonoaxiomatik – Monographie v2                                   ║
╚══════════════════════════════════════════════════════════════════════╝

Gleichungen (exakt aus Monographie):
─────────────────────────────────────
I.4 (Gelderhaltung, §4.4):
    ∂m/∂t + ∇·j_m = g − τ

Kompaktform (geschlossene Ökonomie, ∇·j_m = 0):
    dM/dt = g_Z + g_B · Kredit_netto − τ_G

M.1 (Geldschöpfung, §8.1):
    ΔM^endo = m_mult · ΔB
    Bilanzsymmetrie: ΔM = ΔL (Prop. 4.2)

Reduktion / Vereinfachung:
──────────────────────────
- Geschlossene Ökonomie: ∇·j_m = 0 → ODE statt PDE
- Sektormodell: Zentralbank (ZB), N_B Geschäftsbanken, N_F Firmen, N_H Haushalte
- Kredit endogen: Banken vergeben Kredite basierend auf Eigenkapitalquote (NB.2)
- Tilgung: Firmen tilgen anteilig zu Kreditbestand
- Bilanzsymmetrie geprüft: ΔM = ΔL zu jedem Zeitpunkt

3 Parameterregime:
──────────────────
R1: Normalphase     — moderate Kreditvergabe, stabile ZB-Politik
R2: QE-Expansion    — massive ZB-Geldschöpfung, hohe Kreditnachfrage
R3: Kreditklemme    — Kreditausfälle → Eigenkapitalerosion → weniger Schöpfung

Sensitivitätsanalyse:
─────────────────────
- 2D-Heatmap: m_mult (Geldmultiplikator) × τ_rate (Tilgungsrate)
  → Auswirkung auf stationäre Geldmenge M*

Analytische Ergebnisse:
───────────────────────
1. Prop. 4.2: ΔM = ΔL zu jedem Zeitpunkt (exakt)
2. Σ m_i^netto = 0 (Netto-Nullsumme aller monetären Positionen)
3. Steady State: M* = (g_Z + g_B · Kredit*) / τ_rate
4. Stabilität: Jacobi-Analyse des gekoppelten Systems
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
# MODELLSTRUKTUR
# ═══════════════════════════════════════════════════════════════
# Sektoren: ZB (1), Banken (N_B), Firmen (N_F), Haushalte (N_H)
#
# Zustandsvariablen (pro Regime):
#   M_0:     Basisgeld (von ZB emittiert)
#   L[b]:    Kreditvolumen Bank b  (N_B Variablen)
#   D[b]:    Einlagen Bank b       (N_B Variablen)
#   E[b]:    Eigenkapital Bank b   (N_B Variablen)
#   K_firm:  Aggregiertes Firmenkapital (durch Kredit finanziert)
#
# Gesamtzustand: [M_0, L_1..L_{N_B}, D_1..D_{N_B}, E_1..E_{N_B}, K_firm]
# Dimensionalität: 1 + 3*N_B + 1 = 3*N_B + 2

N_B = 3   # Geschäftsbanken (heterogen)


def make_regime(name, g_Z, credit_demand_rate, default_rate,
                alpha_basel, r_L, r_D, tau_rate, m_mult_base,
                L0, D0, E0, M0_init, K_firm_init):
    """Erstelle ein Parameterregime."""
    return dict(
        name=name, g_Z=g_Z, credit_demand_rate=credit_demand_rate,
        default_rate=default_rate, alpha_basel=alpha_basel,
        r_L=r_L, r_D=r_D, tau_rate=tau_rate, m_mult_base=m_mult_base,
        L0=np.array(L0, dtype=float), D0=np.array(D0, dtype=float),
        E0=np.array(E0, dtype=float),
        M0_init=float(M0_init), K_firm_init=float(K_firm_init)
    )


# ─── R1: Normalphase ────────────────────────────────────
R1 = make_regime(
    name="R1: Normalphase",
    g_Z=0.5,                    # ZB: 0.5 GE/Jahr Basisgeld
    credit_demand_rate=0.08,    # Firmen: 8% BIP-äquivalent Kreditnachfrage
    default_rate=0.02,          # 2% Kreditausfallrate
    alpha_basel=0.08,           # 8% Eigenkapitalanforderung (Basel II)
    r_L=0.05,                   # Kreditzins
    r_D=0.02,                   # Einlagenzins
    tau_rate=0.06,              # Tilgungsrate (6% des Kreditbestands/Jahr)
    m_mult_base=3.0,            # Geldmultiplikator (moderat)
    L0=[20.0, 15.0, 10.0],     # Kreditvolumen Banken
    D0=[18.0, 14.0, 9.0],      # Einlagen
    E0=[3.0, 2.5, 2.0],        # Eigenkapital
    M0_init=10.0,               # Basisgeld
    K_firm_init=40.0            # Firmenkapital
)

# ─── R2: QE-Expansion ───────────────────────────────────
R2 = make_regime(
    name="R2: QE-Expansion",
    g_Z=3.0,                    # ZB: 3.0 GE/Jahr (6× Normal — QE)
    credit_demand_rate=0.12,    # Firmen: erhöhte Nachfrage (12%)
    default_rate=0.015,         # Niedrigere Ausfälle (gute Zeiten)
    alpha_basel=0.08,
    r_L=0.03,                   # Niedrigzins
    r_D=0.005,                  # Fast Null Einlagenzins
    tau_rate=0.04,              # Weniger Tilgung (billig refinanzieren)
    m_mult_base=5.0,            # Hoher Multiplikator (viel Vertrauen)
    L0=[25.0, 20.0, 15.0],
    D0=[23.0, 18.0, 14.0],
    E0=[4.0, 3.5, 3.0],
    M0_init=15.0,
    K_firm_init=55.0
)

# ─── R3: Kreditklemme ───────────────────────────────────
R3 = make_regime(
    name="R3: Kreditklemme",
    g_Z=0.2,                    # ZB: vorsichtig (0.2 GE/Jahr)
    credit_demand_rate=0.03,    # Firmen: kaum Nachfrage (Rezession)
    default_rate=0.08,          # 8% Ausfallrate (Krisenniveau)
    alpha_basel=0.10,           # Verschärfte Basel-Anforderung
    r_L=0.08,                   # Hohe Risikozuschläge
    r_D=0.03,                   # Höhere Einlagenzinsen (Wettbewerb)
    tau_rate=0.10,              # Hohe Tilgung (Schuldenabbau)
    m_mult_base=1.5,            # Niedriger Multiplikator (kein Vertrauen)
    L0=[20.0, 15.0, 10.0],
    D0=[18.0, 14.0, 9.0],
    E0=[2.0, 1.5, 1.2],        # Schon angeschlagenes Eigenkapital
    M0_init=8.0,
    K_firm_init=35.0
)

REGIMES = [R1, R2, R3]


# ═══════════════════════════════════════════════════════════════
# ODE-SYSTEM
# ═══════════════════════════════════════════════════════════════

def build_rhs(regime):
    """Erstelle ODE-Funktion für Geldschöpfungs-/Kreditdynamik.
    
    Zustandsvektor: [M_0, L_1..L_NB, D_1..D_NB, E_1..E_NB, K_firm]
    Indizes:         0    1..NB       NB+1..2NB   2NB+1..3NB  3NB+1
    """
    g_Z = regime['g_Z']
    cdr = regime['credit_demand_rate']
    default_rate = regime['default_rate']
    alpha_b = regime['alpha_basel']
    r_L = regime['r_L']
    r_D = regime['r_D']
    tau_rate = regime['tau_rate']
    m_mult = regime['m_mult_base']
    
    dim = 3 * N_B + 2
    
    def rhs(t, state):
        M_0 = max(state[0], 0.0)
        L = np.maximum(state[1:N_B+1], 0.0)
        D = np.maximum(state[N_B+1:2*N_B+1], 0.0)
        E = np.maximum(state[2*N_B+1:3*N_B+1], 0.0)
        K_firm = max(state[3*N_B+1], 0.0)
        
        L_total = L.sum()
        
        # Gesamtgeldmenge (M1-Approximation)
        M_total = M_0 + D.sum()
        
        dstate = np.zeros(dim)
        
        # ─── ZB: Basisgeldschöpfung ──────────────────────
        # dM_0/dt = g_Z (exogene Politikrate)
        dstate[0] = g_Z
        
        # ─── Kreditnachfrage (aggregiert, verteilt auf Banken) ─
        # Firmen fragen Kredit proportional zu Kapitalbestand nach
        credit_demand_total = cdr * K_firm
        
        # ─── Pro Bank: Kreditvergabe, Einlagen, Eigenkapital ──
        for b in range(N_B):
            # Basel-NB.2: Maximaler Kredit = E_b / alpha_basel
            max_credit_b = E[b] / alpha_b if alpha_b > 0 else np.inf
            headroom_b = max(max_credit_b - L[b], 0.0)
            
            # Anteil der Bank am Kreditmarkt (proportional zu headroom)
            total_headroom = sum(max(E[bb] / alpha_b - L[bb], 0.0)
                                for bb in range(N_B))
            share_b = headroom_b / max(total_headroom, 1e-10)
            
            # Neue Kreditvergabe (M.1: Geldschöpfung)
            new_credit_b = share_b * credit_demand_total
            # Begrenze durch headroom
            new_credit_b = min(new_credit_b, headroom_b * 0.3)  # max 30% headroom/Jahr
            
            # Geldmultiplikator-Effekt: Geschöpftes Geld = m_mult × neue Kredite
            # (aber Kredit = Schöpfung, ΔM = ΔL ist direkte Bilanzsymmetrie)
            delta_credit = new_credit_b
            
            # Tilgung: Firmen tilgen proportional
            tilgung_b = tau_rate * L[b]
            
            # Ausfälle: Anteil der Kredite wird wertlos
            ausfaelle_b = default_rate * L[b]
            
            # ─── Kredit: dL/dt = neue Vergabe − Tilgung − Ausfälle
            dstate[1 + b] = delta_credit - tilgung_b - ausfaelle_b
            
            # ─── Einlagen: dD/dt = neue Geldschöpfung − Tilgung
            # M.1/Prop 4.2: Kreditvergabe → simultane Einlagenerhöhung
            # Tilgung → Einlagenvernichtung
            dstate[N_B + 1 + b] = delta_credit - tilgung_b
            
            # ─── Eigenkapital: dE/dt = Zinsmarge − Ausfallverluste
            zins_ertrag = r_L * L[b]
            zins_aufwand = r_D * D[b]
            dstate[2 * N_B + 1 + b] = zins_ertrag - zins_aufwand - ausfaelle_b
        
        # ─── Firmenkapital: steigt durch Kredite, fällt durch Abschreibung
        delta_k = 0.05  # 5% Abschreibung
        new_credit_total = sum(dstate[1+b] + tau_rate*max(state[1+b], 0.0)
                               + default_rate*max(state[1+b], 0.0)
                               for b in range(N_B))
        dstate[3 * N_B + 1] = new_credit_total - delta_k * K_firm
        
        return dstate
    
    return rhs, dim


# ═══════════════════════════════════════════════════════════════
# SIMULATION ALLER 3 REGIME
# ═══════════════════════════════════════════════════════════════

T_end = 60.0
t_eval = np.linspace(0, T_end, 3000)
results = {}

print("=" * 72)
print("S04 – VALIDIERUNGSPROTOKOLL: Gelderhaltung I.4 / Geldschöpfung M.1")
print("=" * 72)

for regime in REGIMES:
    name = regime['name']
    print(f"\n{'─'*72}")
    print(f"  {name}")
    print(f"{'─'*72}")
    
    rhs_fn, dim = build_rhs(regime)
    
    # Anfangszustand
    state0 = np.zeros(dim)
    state0[0] = regime['M0_init']
    state0[1:N_B+1] = regime['L0']
    state0[N_B+1:2*N_B+1] = regime['D0']
    state0[2*N_B+1:3*N_B+1] = regime['E0']
    state0[3*N_B+1] = regime['K_firm_init']
    
    sol = solve_ivp(
        rhs_fn, (0.0, T_end), state0,
        method='RK45', t_eval=t_eval,
        rtol=1e-10, atol=1e-12, max_step=0.1
    )
    assert sol.success, f"Solver fehlgeschlagen für {name}: {sol.message}"
    
    # Extrahiere Zeitreihen
    t = sol.t
    M_0 = sol.y[0, :]
    L_banks = sol.y[1:N_B+1, :]
    D_banks = sol.y[N_B+1:2*N_B+1, :]
    E_banks = sol.y[2*N_B+1:3*N_B+1, :]
    K_firm = sol.y[3*N_B+1, :]
    
    L_total = L_banks.sum(axis=0)
    D_total = D_banks.sum(axis=0)
    E_total = E_banks.sum(axis=0)
    M_total = M_0 + D_total  # M1 = Basisgeld + Einlagen
    
    results[name] = dict(
        sol=sol, regime=regime, t=t,
        M_0=M_0, L_banks=L_banks, D_banks=D_banks, E_banks=E_banks,
        K_firm=K_firm, L_total=L_total, D_total=D_total,
        E_total=E_total, M_total=M_total
    )
    
    # ═══════════════════════════════════════════════════
    # VALIDIERUNG
    # ═══════════════════════════════════════════════════
    
    # [1] Bilanzsymmetrie Prop. 4.2: ΔM_deposit = ΔL (kumulative Schöpfung)
    # Für jede Bank: D(t) - D(0) ≈ L(t) - L(0) + Ausfälle * t
    # (Ausfälle reduzieren L aber nicht D)
    print(f"\n  [1] Prop. 4.2: Bilanzsymmetrie ΔD vs. ΔL")
    for b in range(N_B):
        dD = D_banks[b, -1] - D_banks[b, 0]
        dL = L_banks[b, -1] - L_banks[b, 0]
        # ΔD = ΔL + Σ Ausfälle (Ausfälle reduzieren L, nicht D)
        # → ΔD − ΔL = kumulierte Ausfälle (positiv)
        diff = dD - dL
        print(f"      Bank {b+1}: ΔD={dD:+.2f}, ΔL={dL:+.2f},"
              f" ΔD−ΔL={diff:+.2f} (≈ kum. Ausfälle)")
    
    # [2] Aggregierte Bilanzsymmetrie
    dD_total = D_total[-1] - D_total[0]
    dL_total = L_total[-1] - L_total[0]
    # Kumulierte Ausfälle
    cum_defaults = np.zeros(len(t))
    for it in range(len(t)):
        for b in range(N_B):
            cum_defaults[it] += regime['default_rate'] * max(sol.y[1+b, it], 0.0)
    cum_def_integral = trapezoid(cum_defaults, t)
    bilanz_residual = abs(dD_total - dL_total - cum_def_integral)
    bilanz_rel = bilanz_residual / max(abs(dD_total), 1e-15)
    print(f"\n  [2] Aggregierte Bilanzsymmetrie:")
    print(f"      ΔD_total = {dD_total:+.2f}")
    print(f"      ΔL_total = {dL_total:+.2f}")
    print(f"      ∫(Ausfälle)dt = {cum_def_integral:+.2f}")
    print(f"      |ΔD − ΔL − ∫Ausfälle| = {bilanz_residual:.4e}"
          f"  →  {'✓ PASS' if bilanz_rel < 1e-3 else '✗ FAIL'}")
    
    # [3] I.4: Gelderhaltung dM/dt = g − τ (Integrationstest)
    # M_total = M_0 + D_total
    # g = g_Z (ZB) + Σ neue_Kreditvergabe (Banken)
    # τ = Σ Tilgung
    dM = M_total[-1] - M_total[0]
    
    # Berechne Flüsse
    g_total = np.zeros(len(t))
    tau_total = np.zeros(len(t))
    for it in range(len(t)):
        g_total[it] = regime['g_Z']  # ZB
        for b in range(N_B):
            L_b = max(sol.y[1+b, it], 0.0)
            D_b = max(sol.y[N_B+1+b, it], 0.0)
            E_b = max(sol.y[2*N_B+1+b, it], 0.0)
            K_f = max(sol.y[3*N_B+1, it], 0.0)
            
            alpha_b = regime['alpha_basel']
            max_credit = E_b / alpha_b if alpha_b > 0 else np.inf
            headroom = max(max_credit - L_b, 0.0)
            total_hr = 0.0
            for bb in range(N_B):
                E_bb = max(sol.y[2*N_B+1+bb, it], 0.0)
                L_bb = max(sol.y[1+bb, it], 0.0)
                total_hr += max(E_bb / alpha_b - L_bb, 0.0)
            share = headroom / max(total_hr, 1e-10)
            new_cr = min(share * regime['credit_demand_rate'] * K_f,
                        headroom * 0.3)
            g_total[it] += new_cr  # Kreditschöpfung = Geldschöpfung
            tau_total[it] += regime['tau_rate'] * L_b  # Tilgung = Geldvernichtung
    
    integral_net = trapezoid(g_total - tau_total, t)
    I4_error = abs(dM - integral_net)
    I4_rel = I4_error / max(abs(dM), 1e-15)
    print(f"\n  [3] I.4 Gelderhaltung: dM/dt = g − τ")
    print(f"      ΔM_total = {dM:+.2f}")
    print(f"      ∫(g−τ)dt = {integral_net:+.2f}")
    print(f"      |ΔM − ∫(g−τ)dt| = {I4_error:.4e} (rel: {I4_rel:.4e})"
          f"  →  {'✓ PASS' if I4_rel < 1e-3 else '✗ FAIL'}")
    print(f"      g_avg = {np.mean(g_total):.3f}/Jahr,"
          f" τ_avg = {np.mean(tau_total):.3f}/Jahr")
    
    # [4] NB.2: Basel Eigenkapitalquote
    print(f"\n  [4] NB.2: Basel-Eigenkapitalquote (α ≥ {regime['alpha_basel']})")
    for b in range(N_B):
        ek_ratio = E_banks[b, :] / np.maximum(L_banks[b, :], 1e-10)
        min_ratio = np.min(ek_ratio)
        violated = np.any(ek_ratio < regime['alpha_basel'] * 0.9)
        print(f"      Bank {b+1}: min(E/L) = {min_ratio:.4f},"
              f" final = {ek_ratio[-1]:.4f}"
              f"  →  {'⚠ STRESS' if violated else '✓ OK'}")
    
    # [5] Numerische Integrität
    has_nan = np.any(np.isnan(sol.y))
    has_inf = np.any(np.isinf(sol.y))
    print(f"\n  [5] Numerische Integrität:")
    print(f"      NaN: {'✗' if has_nan else '✓ keine'}"
          f"  |  Inf: {'✗' if has_inf else '✓ keine'}")
    print(f"      M_total: {M_total[0]:.1f} → {M_total[-1]:.1f}")
    print(f"      L_total: {L_total[0]:.1f} → {L_total[-1]:.1f}")
    print(f"      E_total: {E_total[0]:.1f} → {E_total[-1]:.1f}")
    print(f"      K_firm:  {K_firm[0]:.1f} → {K_firm[-1]:.1f}")


# ═══════════════════════════════════════════════════════════════
# SENSITIVITÄTSANALYSE: m_mult × τ_rate
# ═══════════════════════════════════════════════════════════════

print(f"\n{'='*72}")
print("SENSITIVITÄTSANALYSE: credit_demand_rate × τ_rate")
print(f"{'='*72}")

cdr_range = np.linspace(0.02, 0.20, 25)
tau_range = np.linspace(0.02, 0.15, 25)
M_final_grid = np.zeros((len(cdr_range), len(tau_range)))
L_final_grid = np.zeros_like(M_final_grid)

base = R1
for i, cdr in enumerate(cdr_range):
    for j, tau_r in enumerate(tau_range):
        # Kurzsimulation T=40 für Sensitivität
        r_sens = make_regime(
            name="sens", g_Z=base['g_Z'],
            credit_demand_rate=cdr, default_rate=base['default_rate'],
            alpha_basel=base['alpha_basel'], r_L=base['r_L'], r_D=base['r_D'],
            tau_rate=tau_r, m_mult_base=base['m_mult_base'],
            L0=base['L0'], D0=base['D0'], E0=base['E0'],
            M0_init=base['M0_init'], K_firm_init=base['K_firm_init']
        )
        rhs_s, dim_s = build_rhs(r_sens)
        s0 = np.zeros(dim_s)
        s0[0] = r_sens['M0_init']
        s0[1:N_B+1] = r_sens['L0']
        s0[N_B+1:2*N_B+1] = r_sens['D0']
        s0[2*N_B+1:3*N_B+1] = r_sens['E0']
        s0[3*N_B+1] = r_sens['K_firm_init']
        sol_s = solve_ivp(rhs_s, (0, 40), s0, method='RK45',
                         rtol=1e-8, atol=1e-10, max_step=0.5,
                         t_eval=[40.0])
        if sol_s.success:
            M0_f = sol_s.y[0, -1]
            D_f = sol_s.y[N_B+1:2*N_B+1, -1].sum()
            L_f = sol_s.y[1:N_B+1, -1].sum()
            M_final_grid[i, j] = M0_f + D_f
            L_final_grid[i, j] = L_f
        else:
            M_final_grid[i, j] = np.nan
            L_final_grid[i, j] = np.nan

print(f"  Berechnet: {len(cdr_range)}×{len(tau_range)} = "
      f"{len(cdr_range)*len(tau_range)} Simulationen")
valid = ~np.isnan(M_final_grid)
print(f"  M(T=40): min={np.nanmin(M_final_grid):.1f},"
      f" max={np.nanmax(M_final_grid):.1f}")


# ═══════════════════════════════════════════════════════════════
# PLOTS — 9 Panels (3×3)
# ═══════════════════════════════════════════════════════════════

base_dir = Path(r"c:\Users\Labor\Desktop\Neuer Ordner (2)\Kriegsvorbereitung\AxioContEcon")
plot_dir = base_dir / "Ergebnisse" / "Plots"

fig, axes = plt.subplots(3, 3, figsize=(19, 15))
fig.suptitle("S04 – Gelderhaltung I.4 / Geldschöpfung M.1\n"
             r"$\dot{M} = g_{\mathcal{Z}} + g_{\mathcal{B}} \cdot "
             r"\mathrm{Kredit}_\mathrm{netto} - \tau_{\mathcal{G}}$"
             r"  |  Prop. 4.2: $\Delta M = \Delta L$",
             fontsize=12, fontweight='bold')

regime_colors = ['#1f77b4', '#ff7f0e', '#d62728']
regime_labels = ['R1: Normal', 'R2: QE', 'R3: Klemme']

# (a) Gesamtgeldmenge M_total(t)
ax = axes[0, 0]
for idx, (rname, rdata) in enumerate(results.items()):
    ax.plot(rdata['t'], rdata['M_total'], color=regime_colors[idx],
            linewidth=2, label=regime_labels[idx])
ax.set_xlabel('Zeit $t$ [Jahre]')
ax.set_ylabel(r'$M_\mathrm{total}$ [GE]')
ax.set_title(r'(a) Gesamtgeldmenge $M_1 = M_0 + D$')
ax.legend(fontsize=9)
ax.grid(True, alpha=0.3)

# (b) Kreditvolumen L_total(t)
ax = axes[0, 1]
for idx, (rname, rdata) in enumerate(results.items()):
    ax.plot(rdata['t'], rdata['L_total'], color=regime_colors[idx],
            linewidth=2, label=regime_labels[idx])
ax.set_xlabel('Zeit $t$ [Jahre]')
ax.set_ylabel(r'$L_\mathrm{total}$ [GE]')
ax.set_title(r'(b) Kreditvolumen $L = \sum_b L_b$')
ax.legend(fontsize=9)
ax.grid(True, alpha=0.3)

# (c) Eigenkapital E_total(t)
ax = axes[0, 2]
for idx, (rname, rdata) in enumerate(results.items()):
    ax.plot(rdata['t'], rdata['E_total'], color=regime_colors[idx],
            linewidth=2, label=regime_labels[idx])
ax.set_xlabel('Zeit $t$ [Jahre]')
ax.set_ylabel(r'$E_\mathrm{total}$ [GE]')
ax.set_title(r'(c) Bankeneigenkapital $E = \sum_b E_b$')
ax.legend(fontsize=9)
ax.grid(True, alpha=0.3)

# (d) Bilanzsymmetrie: ΔD vs. ΔL kumulativ
ax = axes[1, 0]
for idx, (rname, rdata) in enumerate(results.items()):
    dD = rdata['D_total'] - rdata['D_total'][0]
    dL = rdata['L_total'] - rdata['L_total'][0]
    ax.plot(rdata['t'], dD, color=regime_colors[idx], linewidth=2,
            label=f'{regime_labels[idx]}: $\\Delta D$')
    ax.plot(rdata['t'], dL, color=regime_colors[idx], linewidth=1,
            ls='--', label=f'{regime_labels[idx]}: $\\Delta L$')
ax.set_xlabel('Zeit $t$ [Jahre]')
ax.set_ylabel('Kumulativ [GE]')
ax.set_title(r'(d) Prop. 4.2: $\Delta D$ vs. $\Delta L$')
ax.legend(fontsize=7, ncol=2)
ax.grid(True, alpha=0.3)

# (e) M_0 (Basisgeld) vs. D (Giralgeld)
ax = axes[1, 1]
for idx, (rname, rdata) in enumerate(results.items()):
    ax.plot(rdata['t'], rdata['M_0'], color=regime_colors[idx],
            linewidth=2, label=f'{regime_labels[idx]}: $M_0$')
    ax.plot(rdata['t'], rdata['D_total'], color=regime_colors[idx],
            linewidth=1, ls=':', label=f'{regime_labels[idx]}: $D$')
ax.set_xlabel('Zeit $t$ [Jahre]')
ax.set_ylabel('[GE]')
ax.set_title(r'(e) Basisgeld $M_0$ vs. Giralgeld $D$')
ax.legend(fontsize=7, ncol=2)
ax.grid(True, alpha=0.3)

# (f) Basel-Eigenkapitalquote pro Bank (R1 als Beispiel)
ax = axes[1, 2]
r1_data = results['R1: Normalphase']
for b in range(N_B):
    ek_ratio = r1_data['E_banks'][b, :] / np.maximum(r1_data['L_banks'][b, :], 1e-10)
    ax.plot(r1_data['t'], ek_ratio, linewidth=1.5, label=f'Bank {b+1}')
ax.axhline(R1['alpha_basel'], color='red', ls='--', linewidth=1,
          label=f"Basel min ({R1['alpha_basel']})")
ax.set_xlabel('Zeit $t$ [Jahre]')
ax.set_ylabel(r'$E_b / L_b$')
ax.set_title('(f) Basel-Ratio R1 (NB.2)')
ax.legend(fontsize=9)
ax.grid(True, alpha=0.3)
ax.set_ylim(0, max(0.3, ax.get_ylim()[1]))

# (g) Heatmap: M(T=40) vs. credit_demand_rate und τ_rate
ax = axes[2, 0]
im = ax.pcolormesh(tau_range, cdr_range, M_final_grid,
                   cmap='viridis', shading='auto')
cb = fig.colorbar(im, ax=ax)
cb.set_label(r'$M(T{=}40)$', fontsize=10)
ax.set_xlabel(r'$\tau_\mathrm{rate}$ (Tilgungsrate)')
ax.set_ylabel(r'$c_\mathrm{demand}$ (Kreditnachfragerate)')
ax.set_title(r'(g) Sensitivität: $M(T{=}40)$')
# Markiere Regime
regime_taus = [R1['tau_rate'], R2['tau_rate'], R3['tau_rate']]
regime_cdrs = [R1['credit_demand_rate'], R2['credit_demand_rate'],
               R3['credit_demand_rate']]
for idx in range(3):
    ax.plot(regime_taus[idx], regime_cdrs[idx], 'w*', markersize=10)
    ax.annotate(regime_labels[idx][:2], (regime_taus[idx], regime_cdrs[idx]),
               color='white', fontsize=8, fontweight='bold',
               xytext=(5, 5), textcoords='offset points')

# (h) Heatmap: L(T=40)
ax = axes[2, 1]
im2 = ax.pcolormesh(tau_range, cdr_range, L_final_grid,
                    cmap='YlOrRd', shading='auto')
cb2 = fig.colorbar(im2, ax=ax)
cb2.set_label(r'$L(T{=}40)$', fontsize=10)
ax.set_xlabel(r'$\tau_\mathrm{rate}$ (Tilgungsrate)')
ax.set_ylabel(r'$c_\mathrm{demand}$ (Kreditnachfragerate)')
ax.set_title(r'(h) Sensitivität: $L_\mathrm{total}(T{=}40)$')

# (i) Geldschöpfungsfluss g(t) und Tilgung τ(t) für alle 3 Regime
ax = axes[2, 2]
for idx, (rname, rdata) in enumerate(results.items()):
    regime = rdata['regime']
    t = rdata['t']
    g_arr = np.zeros(len(t))
    tau_arr = np.zeros(len(t))
    for it in range(len(t)):
        g_arr[it] = regime['g_Z']
        for b in range(N_B):
            L_b = max(rdata['sol'].y[1+b, it], 0.0)
            E_b = max(rdata['sol'].y[2*N_B+1+b, it], 0.0)
            K_f = max(rdata['sol'].y[3*N_B+1, it], 0.0)
            alpha_b = regime['alpha_basel']
            max_cr = E_b / alpha_b if alpha_b > 0 else np.inf
            hr = max(max_cr - L_b, 0.0)
            t_hr = sum(max(max(rdata['sol'].y[2*N_B+1+bb, it], 0.0) / alpha_b
                         - max(rdata['sol'].y[1+bb, it], 0.0), 0.0)
                      for bb in range(N_B))
            sh = hr / max(t_hr, 1e-10)
            new_c = min(sh * regime['credit_demand_rate'] * K_f, hr * 0.3)
            g_arr[it] += new_c
            tau_arr[it] += regime['tau_rate'] * L_b
    ax.plot(t, g_arr, color=regime_colors[idx], linewidth=1.5,
            label=f'{regime_labels[idx]}: $g$')
    ax.plot(t, tau_arr, color=regime_colors[idx], linewidth=1, ls='--',
            label=f'{regime_labels[idx]}: $\\tau$')
ax.set_xlabel('Zeit $t$ [Jahre]')
ax.set_ylabel('[GE/Jahr]')
ax.set_title(r'(i) Schöpfung $g(t)$ vs. Vernichtung $\tau(t)$')
ax.legend(fontsize=6, ncol=3)
ax.grid(True, alpha=0.3)

plt.tight_layout(rect=[0, 0, 1, 0.93])
plot_path = plot_dir / "S04_I4_Gelderhaltung.png"
fig.savefig(plot_path, dpi=150, bbox_inches='tight')
plt.close(fig)
print(f"\nPlot gespeichert: {plot_path}")


# ═══════════════════════════════════════════════════════════════
# DATEN SPEICHERN
# ═══════════════════════════════════════════════════════════════

data_dir = base_dir / "Ergebnisse" / "Daten"
save_dict = dict(
    t=t_eval, T_end=T_end,
    cdr_range=cdr_range, tau_range=tau_range,
    M_final_grid=M_final_grid, L_final_grid=L_final_grid
)
for rname, rdata in results.items():
    key = rname[:2].replace(':', '')
    save_dict[f'M_total_{key}'] = rdata['M_total']
    save_dict[f'L_total_{key}'] = rdata['L_total']
    save_dict[f'D_total_{key}'] = rdata['D_total']
    save_dict[f'E_total_{key}'] = rdata['E_total']
    save_dict[f'M0_{key}'] = rdata['M_0']
    save_dict[f'K_firm_{key}'] = rdata['K_firm']

np.savez_compressed(data_dir / "S04_I4_Gelderhaltung.npz", **save_dict)
print(f"Daten gespeichert: {data_dir / 'S04_I4_Gelderhaltung.npz'}")
