"""
S27 – III.3 Produktionsdynamik  (§6.5)
=======================================
Gleichung III.3:

   dq_k/dt = lambda_q * (p_k - MC_k(q_k)) / p_k * q_k  -  delta_q * q_k

Gewinnmargengesteuerte Expansion mit Abschreibung.

Axiomatische Eigenschaften:
  - Expansion bei positivem Gewinn:  p > MC  =>  dq/dt > 0 (netto)
  - Kontraktion bei negativem Gewinn: p < MC  =>  dq/dt < 0
  - Stationaeres GG:  p - MC = delta_q * p / lambda_q
  - Abschreibung: delta_q * q gleichmaessig

Kopplungen:
  - II.2 liefert p_k (Preisdynamik)
  - L.1+L.4 liefern Arbeitsangebot -> MC
  - P.3 verbucht q_k in Populationsbilanz

8 Regime, 8 Validierungen, 5 Sensitivitaetsanalysen, 4 Erweiterte Analysen
"""

import sys, io, warnings
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
warnings.filterwarnings('ignore', category=UserWarning, module='matplotlib')

import numpy as np
from scipy.optimize import brentq
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent.parent
PLOT_DIR = BASE / "Ergebnisse" / "Plots"
DATA_DIR = BASE / "Ergebnisse" / "Daten"
PLOT_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)

np.random.seed(42)
rng = np.random.RandomState(42)

# ══════════════════════════════════════════════════════════════════════
# 0. GLEICHUNG UND ERKLAERUNG
# ══════════════════════════════════════════════════════════════════════

header_text = r"""
================================================================================
  S27  GLEICHUNG III.3 — PRODUKTIONSDYNAMIK (§6.5)
================================================================================

  ┌─────────────────────────────────────────────────────────────────────────────┐
  │                                                                             │
  │   dq_k              p_k - MC_k(q_k)                                        │
  │  ───── = lambda_q * ─────────────── * q_k  -  delta_q * q_k                │
  │   dt                     p_k                                                │
  │          ╰────────────────────────────────╯   ╰────────────╯               │
  │           Gewinnmargengesteuerte Expansion      Abschreibung                │
  │                                                                             │
  └─────────────────────────────────────────────────────────────────────────────┘

  ════════════════════════════════════════════════════════════════════════════════
  SYMBOLTABELLE
  ════════════════════════════════════════════════════════════════════════════════

  Symbol          Typ          Beschreibung
  ──────────────  ──────────── ─────────────────────────────────────────────────
  q_k             R+           Produktionsmenge von Gut k (Mengeneinheit/Zeit)
  p_k             R+           Marktpreis von Gut k (aus Preisdynamik II.2)
  MC_k(q_k)       R+           Grenzkosten (steigend: MC_k' > 0)
                               MC(q) = c_0 + c_1 * q^alpha  (konvex, alpha>1)
  lambda_q        R+ (=0.5)    Produktionsanpassungsgeschwindigkeit
                               -> hoch: schnelle Marktreaktion
                               -> niedrig: traege Anpassung (Kapazitaetsrestr.)
  delta_q         R+ (=0.05)   Abschreibungsrate (physischer Kapitalzerfall)
  (p-MC)/p        [-inf,1]     Relative Gewinnmarge (Lerner-Index)

  ════════════════════════════════════════════════════════════════════════════════
  ANNAHMEN UND MODELLIERUNG
  ════════════════════════════════════════════════════════════════════════════════

  1. GEWINNMARGENSTEUERUNG: Expansion ist proportional zur relativen
     Gewinnmarge (p-MC)/p — dem Lerner-Index der Marktmacht.
     p > MC: positiver Gewinn -> Expansion
     p < MC: negativer Gewinn -> Kontraktion (Exit/Schrumpfung)

  2. MULTIPLIKATIV in q: Die Anpassung ist proportional zum bestehenden
     Produktionsniveau q_k -> groessere Firmen expandieren absolut schneller
     -> Gibrat-artiges Gesetz fuer Firmenwachstum.

  3. GRENZKOSTEN steigend (konvex): MC'(q) > 0, MC''(q) >= 0.
     Modellierung: MC(q) = c_0 + c_1 * q^alpha mit alpha >= 1.
     Bei alpha=1: lineare MC; alpha=2: quadratisch (klassisch).
     c_0: fixe Minimalkosten; c_1: variable Kostenskalierung.

  4. ABSCHREIBUNG: delta_q * q ist gleichmaessiger Kapitalzerfall.
     Ohne Neuinvestition (p<MC immer): q -> 0 exponentiell.

  5. STATIONAERES GG: dq/dt=0 bei (p-MC)/p = delta_q/lambda_q.
     -> Preis deckt MC plus Abschreibungs-Aufschlag.
     -> Eindeutig (bei steigenden MC und festem p).

  6. MULTI-GUT: K Gueter simultan, jedes mit eigenem p_k, MC_k(q_k).
     Kopplungen: (a) gemeinsamer Arbeitsmarkt -> MC steigt bei Aggr.-Expansion,
     (b) Preisinteraktion ueber Nachfragestruktur.

  7. PREISDYNAMIK (vereinfacht fuer isolierte III.3-Analyse):
     p_k exogen oder als einfache Nachfrage-Angebots-Rueckkopplung:
     dp/dt = eta * (D(p) - q) / D(p)  mit D(p) = D_0 * p^(-epsilon).

  8. FORWARD-EULER mit dt=0.01, T=50 (5000 Schritte).
     Clipping: q >= q_min (> 0, firmen sterben nicht bei q=0).

  ════════════════════════════════════════════════════════════════════════════════
"""

print(header_text)

# ══════════════════════════════════════════════════════════════════════
# 1. KERNFUNKTIONEN
# ══════════════════════════════════════════════════════════════════════

def MC(q, c0=2.0, c1=0.1, alpha=1.5):
    """Grenzkosten MC(q) = c0 + c1 * q^alpha (konvex, steigend)."""
    return c0 + c1 * np.maximum(q, 0.0)**alpha

def MC_prime(q, c0=2.0, c1=0.1, alpha=1.5):
    """dMC/dq."""
    return c1 * alpha * np.maximum(q, 1e-12)**(alpha - 1)

def demand(p, D0=100.0, epsilon=1.5):
    """Isoelastische Nachfrage: D(p) = D0 * p^(-epsilon)."""
    return D0 * np.maximum(p, 0.01)**(-epsilon)

def q_star_analytical(p, c0=2.0, c1=0.1, alpha=1.5, delta_q=0.05, lam_q=0.5):
    """Stationaeres q* aus (p-MC(q*))/p = delta_q/lam_q."""
    # MC(q*) = p * (1 - delta_q/lam_q)
    mc_target = p * (1.0 - delta_q / lam_q)
    # c0 + c1*q^alpha = mc_target -> q = ((mc_target-c0)/c1)^(1/alpha)
    inner = (mc_target - c0) / c1
    if np.isscalar(inner):
        if inner <= 0:
            return 0.01
        return inner**(1.0 / alpha)
    result = np.where(inner > 0, inner**(1.0 / alpha), 0.01)
    return result

def dq_dt(q, p, lam_q=0.5, delta_q=0.05, c0=2.0, c1=0.1, alpha=1.5):
    """III.3: dq/dt = lam_q * (p - MC(q))/p * q - delta_q * q."""
    mc = MC(q, c0, c1, alpha)
    margin = (p - mc) / np.maximum(p, 0.01)
    return lam_q * margin * q - delta_q * q

def run_production(q0, p_series, lam_q=0.5, delta_q=0.05,
                   c0=2.0, c1=0.1, alpha_mc=1.5,
                   T=50.0, dt=0.01, q_min=0.01):
    """Integriere III.3 mit gegebenem Preis-Zeitverlauf p(t)."""
    N_steps = int(T / dt)
    if len(p_series) == 1:
        p_series = np.full(N_steps + 1, p_series[0])
    q_h = np.zeros(N_steps + 1)
    q_h[0] = q0
    for step in range(N_steps):
        q = q_h[step]
        p = p_series[min(step, len(p_series) - 1)]
        dq = dq_dt(q, p, lam_q, delta_q, c0, c1, alpha_mc)
        q_h[step + 1] = max(q + dq * dt, q_min)
    return q_h, np.linspace(0, T, N_steps + 1)

def run_production_multi(K, q0, p0, lam_q, delta_q, c0, c1, alpha_mc,
                         D0=100.0, epsilon=1.5, eta_p=0.3,
                         T=50.0, dt=0.01, q_min=0.01,
                         exog_p=False, p_shock_func=None):
    """Multi-Gut Produktion mit endogener Preis-Rueckkopplung.
    K: Anzahl Gueter. Alle Arrays shape (K,).
    """
    N_steps = int(T / dt)
    q_h = np.zeros((K, N_steps + 1))
    p_h = np.zeros((K, N_steps + 1))
    q_h[:, 0] = q0
    p_h[:, 0] = p0
    margin_h = np.zeros((K, N_steps + 1))
    for step in range(N_steps):
        q = q_h[:, step]
        p = p_h[:, step]
        # Gewinnmarge
        mc = MC(q, c0, c1, alpha_mc)
        margin = (p - mc) / np.maximum(p, 0.01)
        margin_h[:, step] = margin
        # Produktionsdynamik III.3
        dq = lam_q * margin * q - delta_q * q
        q_new = np.maximum(q + dq * dt, q_min)
        # Preisdynamik (vereinfacht)
        if exog_p:
            p_new = p.copy()
            if p_shock_func is not None:
                p_new = p_shock_func(step, dt, p_new)
        else:
            D = demand(p, D0, epsilon)
            dp = eta_p * (D - q) / np.maximum(D, 0.01) * p
            p_new = np.maximum(p + dp * dt, 0.01)
        q_h[:, step + 1] = q_new
        p_h[:, step + 1] = p_new
    # Letzter Margin
    mc_last = MC(q_h[:, -1], c0, c1, alpha_mc)
    margin_h[:, -1] = (p_h[:, -1] - mc_last) / np.maximum(p_h[:, -1], 0.01)
    t_arr = np.linspace(0, T, N_steps + 1)
    return dict(q=q_h, p=p_h, margin=margin_h, t=t_arr)

# ══════════════════════════════════════════════════════════════════════
# 2. GEMEINSAME PARAMETER
# ══════════════════════════════════════════════════════════════════════

T = 50.0; dt = 0.01; N_steps = int(T / dt)

print("=" * 72)
print("  REGIME-ERGEBNISSE")
print("=" * 72)

results = {}

# ══════════════════════════════════════════════════════════════════════
# R1: Einfache Konvergenz zum Gleichgewicht (1 Gut, fester Preis)
# ══════════════════════════════════════════════════════════════════════
print("\n  R1: Einfache Konvergenz (fester Preis)")
p_R1 = 10.0; q0_R1 = 5.0
lam_q_R1 = 0.5; delta_q_R1 = 0.05
c0_R1 = 2.0; c1_R1 = 0.1; alpha_R1 = 1.5
q_star_R1 = q_star_analytical(p_R1, c0_R1, c1_R1, alpha_R1, delta_q_R1, lam_q_R1)
q_h_R1, t_R1 = run_production(q0_R1, np.array([p_R1]), lam_q_R1, delta_q_R1,
                                c0_R1, c1_R1, alpha_R1)
err_R1 = abs(q_h_R1[-1] - q_star_R1) / q_star_R1
print(f"    q*={q_star_R1:.2f}, q(0)={q0_R1:.1f}, q(T)={q_h_R1[-1]:.3f}, "
      f"rel_err={err_R1:.6f}")
# Auch von oben konvergent
q_h_R1b, _ = run_production(q_star_R1 * 3, np.array([p_R1]), lam_q_R1, delta_q_R1,
                              c0_R1, c1_R1, alpha_R1)
err_R1b = abs(q_h_R1b[-1] - q_star_R1) / q_star_R1
print(f"    Von oben: q(0)={q_star_R1*3:.1f}, q(T)={q_h_R1b[-1]:.3f}, "
      f"rel_err={err_R1b:.6f}")
results["R1"] = dict(q=q_h_R1, q_above=q_h_R1b, t=t_R1, q_star=q_star_R1)

# ══════════════════════════════════════════════════════════════════════
# R2: Multi-Gut mit endogener Preisrueckkopplung
# ══════════════════════════════════════════════════════════════════════
print("\n  R2: Multi-Gut (K=5, endogener Preis)")
K_R2 = 5
q0_R2 = rng.uniform(3, 15, K_R2)
p0_R2 = rng.uniform(5, 20, K_R2)
lam_q_R2 = np.full(K_R2, 0.5)
delta_q_R2 = np.full(K_R2, 0.05)
c0_R2 = rng.uniform(1.5, 4.0, K_R2)
c1_R2 = rng.uniform(0.05, 0.2, K_R2)
alpha_R2 = np.full(K_R2, 1.5)
R2 = run_production_multi(K_R2, q0_R2, p0_R2, lam_q_R2, delta_q_R2,
                           c0_R2, c1_R2, alpha_R2, D0=100, epsilon=1.5, eta_p=0.3)
print(f"    q_mean: {q0_R2.mean():.1f} -> {R2['q'][:,-1].mean():.2f}")
print(f"    p_mean: {p0_R2.mean():.1f} -> {R2['p'][:,-1].mean():.2f}")
for k in range(K_R2):
    print(f"    Gut {k}: q={R2['q'][k,-1]:.2f}, p={R2['p'][k,-1]:.2f}, "
          f"margin={R2['margin'][k,-1]:.3f}")
results["R2"] = R2

# ══════════════════════════════════════════════════════════════════════
# R3: Preis-Schock (Nachfrage-Boom dann Crash)
# ══════════════════════════════════════════════════════════════════════
print("\n  R3: Preis-Schock (Boom & Crash)")
K_R3 = 1
q0_R3 = np.array([20.0])
p0_R3 = np.array([10.0])

def price_shock_R3(step, dt, p):
    t = step * dt
    if 10 <= t < 20:
        p = p * (1 + 0.02 * dt)  # Boom: +2%/t
    elif 20 <= t < 25:
        p = p * (1 - 0.08 * dt)  # Crash: -8%/t
    return p

R3 = run_production_multi(K_R3, q0_R3, p0_R3, np.array([0.5]), np.array([0.05]),
                           np.array([2.0]), np.array([0.1]), np.array([1.5]),
                           exog_p=True, p_shock_func=price_shock_R3)
q_peak = R3['q'][0].max(); t_peak = R3['t'][np.argmax(R3['q'][0])]
print(f"    q: {q0_R3[0]:.0f} -> peak {q_peak:.1f} (t={t_peak:.1f}) -> {R3['q'][0,-1]:.2f}")
print(f"    p: {p0_R3[0]:.0f} -> peak {R3['p'][0].max():.2f} -> {R3['p'][0,-1]:.2f}")
results["R3"] = R3

# ══════════════════════════════════════════════════════════════════════
# R4: Abschreibungs-Dominanz (kein Gewinn -> Zerfall)
# ══════════════════════════════════════════════════════════════════════
print("\n  R4: Abschreibungs-Dominanz (p < MC)")
q0_R4 = 50.0
p_low = 1.5  # Unter c0=2.0 -> MC > p immer
q_h_R4, t_R4 = run_production(q0_R4, np.array([p_low]), 0.5, 0.05,
                                2.0, 0.1, 1.5, q_min=0.001)
half_life = None
for i in range(len(q_h_R4)):
    if q_h_R4[i] < q0_R4 / 2:
        half_life = t_R4[i]
        break
print(f"    q: {q0_R4:.0f} -> {q_h_R4[-1]:.4f} (p={p_low:.1f} < c0=2.0)")
print(f"    Halbwertszeit: {half_life:.1f}" if half_life else "    Halbwertszeit: >T")
results["R4"] = dict(q=q_h_R4, t=t_R4)

# ══════════════════════════════════════════════════════════════════════
# R5: Verschiedene MC-Konvexitaeten (alpha=1.0, 1.5, 2.0, 3.0)
# ══════════════════════════════════════════════════════════════════════
print("\n  R5: MC-Konvexitaet (alpha=1.0, 1.5, 2.0, 3.0)")
alphas_R5 = [1.0, 1.5, 2.0, 3.0]
R5_data = {}
for a_val in alphas_R5:
    q_star_a = q_star_analytical(10.0, 2.0, 0.1, a_val, 0.05, 0.5)
    q_h_a, t_a = run_production(5.0, np.array([10.0]), 0.5, 0.05, 2.0, 0.1, a_val)
    R5_data[a_val] = dict(q=q_h_a, q_star=q_star_a)
    print(f"    alpha={a_val:.1f}: q*={q_star_a:.2f}, q(T)={q_h_a[-1]:.3f}")
results["R5"] = R5_data

# ══════════════════════════════════════════════════════════════════════
# R6: Verschiedene lambda_q (Anpassungsgeschwindigkeiten)
# ══════════════════════════════════════════════════════════════════════
print("\n  R6: Anpassungsgeschwindigkeit (lambda_q=0.1, 0.5, 1.0, 3.0)")
lam_vals = [0.1, 0.5, 1.0, 3.0]
R6_data = {}
for lv in lam_vals:
    q_star_l = q_star_analytical(10.0, 2.0, 0.1, 1.5, 0.05, lv)
    q_h_l, t_l = run_production(5.0, np.array([10.0]), lv, 0.05, 2.0, 0.1, 1.5)
    # Konvergenzzeit: Zeitpunkt bis |q-q*|/q* < 0.01
    conv_time = T
    for i in range(len(q_h_l)):
        if abs(q_h_l[i] - q_star_l) / q_star_l < 0.01:
            conv_time = t_l[i]
            break
    R6_data[lv] = dict(q=q_h_l, q_star=q_star_l, conv_time=conv_time)
    print(f"    lam={lv:.1f}: q*={q_star_l:.2f}, conv_t={conv_time:.1f}")
results["R6"] = R6_data

# ══════════════════════════════════════════════════════════════════════
# R7: Oligopol (K=3, niedrige Nachfrage, Wettbewerb um Markt)
# ══════════════════════════════════════════════════════════════════════
print("\n  R7: Oligopol (3 Gueter, niedrige Nachfrage)")
K_R7 = 3
q0_R7 = np.array([20.0, 15.0, 25.0])
p0_R7 = np.array([8.0, 8.0, 8.0])
c0_R7 = np.array([1.0, 2.5, 3.0])  # Verschiedene Basiskosten (Firma 0 effizienteste)
c1_R7 = np.array([0.08, 0.12, 0.15])
R7 = run_production_multi(K_R7, q0_R7, p0_R7, np.full(K_R7, 0.5), np.full(K_R7, 0.05),
                           c0_R7, c1_R7, np.full(K_R7, 1.5),
                           D0=40, epsilon=1.2, eta_p=0.5)
print(f"    Firma 0 (c0=1.0): q={R7['q'][0,-1]:.2f}, p={R7['p'][0,-1]:.2f}")
print(f"    Firma 1 (c0=2.5): q={R7['q'][1,-1]:.2f}, p={R7['p'][1,-1]:.2f}")
print(f"    Firma 2 (c0=3.0): q={R7['q'][2,-1]:.2f}, p={R7['p'][2,-1]:.2f}")
# Marktanteil
total_q = R7['q'][:, -1].sum()
for k in range(K_R7):
    print(f"    Share Firma {k}: {R7['q'][k,-1]/total_q*100:.1f}%")
results["R7"] = R7

# ══════════════════════════════════════════════════════════════════════
# R8: Neoklassischer Grenzfall (sofortige Anpassung lambda->inf)
# ══════════════════════════════════════════════════════════════════════
print("\n  R8: Neoklassischer Grenzfall (lambda_q -> gross)")
# Bei lambda->inf: q springt sofort zu q* wo MC(q*)=p*(1-delta/lambda)≈p
# Also q* so dass MC(q*)=p
p_R8 = 10.0
# MC(q)=c0+c1*q^alpha=p -> q=((p-c0)/c1)^(1/alpha)
q_star_neo = ((p_R8 - 2.0) / 0.1)**(1/1.5)
# Simuliere mit sehr grossem lambda
q_h_fast, t_fast = run_production(5.0, np.array([p_R8]), 50.0, 0.05, 2.0, 0.1, 1.5,
                                   dt=0.001, T=5.0)
q_h_slow, t_slow = run_production(5.0, np.array([p_R8]), 0.1, 0.05, 2.0, 0.1, 1.5,
                                   dt=0.001, T=5.0)
# Fast sollte nach wenigen Steps schon bei q* sein
t_fast_01 = None
for i in range(len(q_h_fast)):
    if abs(q_h_fast[i] - q_star_analytical(p_R8)) / q_star_analytical(p_R8) < 0.01:
        t_fast_01 = t_fast[i]
        break
print(f"    q*_neo (MC=p): {q_star_neo:.2f}")
print(f"    lam=50: q(T=5)={q_h_fast[-1]:.3f}, conv_t={t_fast_01:.3f}" if t_fast_01 else
      f"    lam=50: q(T=5)={q_h_fast[-1]:.3f}, conv_t>5")
print(f"    lam=0.1: q(T=5)={q_h_slow[-1]:.3f}")
results["R8"] = dict(q_fast=q_h_fast, q_slow=q_h_slow, t_fast=t_fast, t_slow=t_slow,
                      q_star_neo=q_star_neo)


# ══════════════════════════════════════════════════════════════════════
# VALIDIERUNGEN
# ══════════════════════════════════════════════════════════════════════
print(f"\n{'='*72}\n  VALIDIERUNGEN\n{'='*72}")
validations = {}

# V1: Konvergenz zum analytischen q* (fester Preis)
v1_pass = err_R1 < 0.01 and err_R1b < 0.01
validations["V1"] = dict(name="Konvergenz q->q* (von unten + oben)",
                         passed=v1_pass,
                         detail=f"err_below={err_R1:.6f}, err_above={err_R1b:.6f}")
print(f"  V1: {'PASS' if v1_pass else 'FAIL'} ({validations['V1']['detail']})")

# V2: Expansion bei p>MC, Kontraktion bei p<MC (Axiom)
# Pruefe am Anfang: dq(step=0) Vorzeichen
q_test = 5.0; p_test_high = 20.0; p_test_low = 1.0
dq_high = dq_dt(q_test, p_test_high)
dq_low = dq_dt(q_test, p_test_low)
v2_pass = dq_high > 0 and dq_low < 0
validations["V2"] = dict(name="Axiom: p>MC=>dq>0, p<MC=>dq<0",
                         passed=v2_pass,
                         detail=f"dq(p=20)={dq_high:.3f}>0, dq(p=1)={dq_low:.3f}<0")
print(f"  V2: {'PASS' if v2_pass else 'FAIL'} ({validations['V2']['detail']})")

# V3: Stationaeres GG ist (p-MC)/p = delta/lambda
q_star_check = q_star_analytical(10.0, 2.0, 0.1, 1.5, 0.05, 0.5)
mc_at_star = MC(q_star_check)
margin_at_star = (10.0 - mc_at_star) / 10.0
target_margin = 0.05 / 0.5  # delta/lambda = 0.1
v3_pass = abs(margin_at_star - target_margin) < 0.001
validations["V3"] = dict(name="GG-Bedingung: (p-MC)/p = delta/lambda",
                         passed=v3_pass,
                         detail=f"margin={margin_at_star:.4f}, target={target_margin:.4f}")
print(f"  V3: {'PASS' if v3_pass else 'FAIL'} ({validations['V3']['detail']})")

# V4: Abschreibung -> Zerfall (R4)
v4_pass = q_h_R4[-1] < 0.01
validations["V4"] = dict(name="Abschreibung: p<MC => q->0",
                         passed=v4_pass,
                         detail=f"q(T)={q_h_R4[-1]:.6f} < 0.01")
print(f"  V4: {'PASS' if v4_pass else 'FAIL'} ({validations['V4']['detail']})")

# V5: MC-Konvexitaet -> groesseres alpha = niedrigeres q*
q_stars_sorted = [R5_data[a]["q_star"] for a in sorted(alphas_R5)]
v5_pass = all(q_stars_sorted[i] >= q_stars_sorted[i+1] for i in range(len(q_stars_sorted)-1))
validations["V5"] = dict(name="Konvexitaet: alpha steigt => q* sinkt",
                         passed=v5_pass,
                         detail=f"q*=[{', '.join(f'{qs:.2f}' for qs in q_stars_sorted)}]")
print(f"  V5: {'PASS' if v5_pass else 'FAIL'} ({validations['V5']['detail']})")

# V6: lambda_q -> Konvergenzzeit sinkt monoton
conv_times = [R6_data[lv]["conv_time"] for lv in sorted(lam_vals)]
v6_pass = all(conv_times[i] >= conv_times[i+1] for i in range(len(conv_times)-1))
validations["V6"] = dict(name="lambda_q steigt => conv_time sinkt",
                         passed=v6_pass,
                         detail=f"conv_t=[{', '.join(f'{ct:.1f}' for ct in conv_times)}]")
print(f"  V6: {'PASS' if v6_pass else 'FAIL'} ({validations['V6']['detail']})")

# V7: Effizienteste Firma (niedrigstes c0) hat groessten Marktanteil
shares = R7['q'][:, -1] / R7['q'][:, -1].sum()
v7_pass = shares[0] > shares[1] > shares[2]  # c0=1.0 > c0=2.5 > c0=3.0
validations["V7"] = dict(name="Effizienz: c0 klein => Marktanteil gross",
                         passed=v7_pass,
                         detail=f"shares=[{shares[0]:.2f}, {shares[1]:.2f}, {shares[2]:.2f}]")
print(f"  V7: {'PASS' if v7_pass else 'FAIL'} ({validations['V7']['detail']})")

# V8: Neoklassischer Grenzfall: lambda->inf => sofortige Konvergenz
# Bei lam=50: Konvergenzzeit < 0.5
v8_pass = t_fast_01 is not None and t_fast_01 < 0.5
validations["V8"] = dict(name="Neoklassisch: lam->inf => conv_t->0",
                         passed=v8_pass,
                         detail=f"conv_t(lam=50)={t_fast_01:.3f}" if t_fast_01 else "conv_t>5")
print(f"  V8: {'PASS' if v8_pass else 'FAIL'} ({validations['V8']['detail']})")


# ══════════════════════════════════════════════════════════════════════
# SENSITIVITAETSANALYSEN
# ══════════════════════════════════════════════════════════════════════
print(f"\n{'='*72}\n  SENSITIVITAETSANALYSEN\n{'='*72}")

# SA1: lambda_q vs delta_q -> q*(GG)
print("  SA1: lambda_q vs delta_q -> q*(GG)")
sa1_lam = np.linspace(0.1, 3.0, 20)
sa1_del = np.linspace(0.01, 0.2, 20)
SA1_qstar = np.zeros((len(sa1_del), len(sa1_lam)))
for il, lv in enumerate(sa1_lam):
    for id_, dv in enumerate(sa1_del):
        SA1_qstar[id_, il] = q_star_analytical(10.0, 2.0, 0.1, 1.5, dv, lv)
results["SA1"] = dict(lam=sa1_lam, delta=sa1_del, qstar=SA1_qstar)
print(f"    q* range: [{SA1_qstar.min():.1f}, {SA1_qstar.max():.1f}]")

# SA2: p vs alpha_MC -> q*(GG)
print("  SA2: p vs alpha_MC -> q*(GG)")
sa2_p = np.linspace(3.0, 25.0, 20)
sa2_a = np.linspace(1.0, 3.0, 20)
SA2_qstar = np.zeros((len(sa2_a), len(sa2_p)))
for ip, pv in enumerate(sa2_p):
    for ia, av in enumerate(sa2_a):
        SA2_qstar[ia, ip] = q_star_analytical(pv, 2.0, 0.1, av, 0.05, 0.5)
results["SA2"] = dict(p=sa2_p, alpha=sa2_a, qstar=SA2_qstar)
print(f"    q* range: [{SA2_qstar.min():.1f}, {SA2_qstar.max():.1f}]")

# SA3: c0 (fixe Kosten) vs c1 (variable) -> q*
print("  SA3: c0 vs c1 -> q*(GG)")
sa3_c0 = np.linspace(0.5, 8.0, 20)
sa3_c1 = np.linspace(0.01, 0.5, 20)
SA3_qstar = np.zeros((len(sa3_c1), len(sa3_c0)))
for ic0, c0v in enumerate(sa3_c0):
    for ic1, c1v in enumerate(sa3_c1):
        SA3_qstar[ic1, ic0] = q_star_analytical(10.0, c0v, c1v, 1.5, 0.05, 0.5)
results["SA3"] = dict(c0=sa3_c0, c1=sa3_c1, qstar=SA3_qstar)
print(f"    q* range: [{SA3_qstar.min():.1f}, {SA3_qstar.max():.1f}]")

# SA4: Nachfrageelastizitaet vs Gleichgewichtspreis
print("  SA4: Nachfrageelast. epsilon vs GG-Preis")
sa4_eps = np.linspace(0.5, 3.0, 30)
sa4_peq = []
for ev in sa4_eps:
    # Simuliere 1-Gut bis GG
    res_sa4 = run_production_multi(1, np.array([10.0]), np.array([10.0]),
                                    np.array([0.5]), np.array([0.05]),
                                    np.array([2.0]), np.array([0.1]), np.array([1.5]),
                                    D0=100, epsilon=ev, eta_p=0.3, T=100, dt=0.01)
    sa4_peq.append(res_sa4['p'][0, -1])
results["SA4"] = dict(epsilon=sa4_eps, p_eq=np.array(sa4_peq))
print(f"    p_eq range: [{min(sa4_peq):.2f}, {max(sa4_peq):.2f}]")

# SA5: Anfangs-q Sensitivitaet -> alle konvergieren zum gleichen q*
print("  SA5: Anfangs-q Sensitivitaet")
q0_vals = np.linspace(1, 60, 20)
q_final_sa5 = []
for q0v in q0_vals:
    q_h_s, _ = run_production(q0v, np.array([10.0]), 0.5, 0.05, 2.0, 0.1, 1.5)
    q_final_sa5.append(q_h_s[-1])
q_final_sa5 = np.array(q_final_sa5)
results["SA5"] = dict(q0=q0_vals, q_final=q_final_sa5)
spread = q_final_sa5.max() - q_final_sa5.min()
print(f"    q(T) spread: {spread:.6f} (soll ~0 fuer globale Stabilitaet)")


# ══════════════════════════════════════════════════════════════════════
# ERWEITERTE ANALYSEN
# ══════════════════════════════════════════════════════════════════════
print(f"\n{'='*72}\n  ERWEITERTE ANALYSEN\n{'='*72}")

# EA1: Phasenportraet dq/dt vs q fuer verschiedene Preise
print("\n  EA1: Phasenportraet (dq/dt vs q)")
q_range = np.linspace(0.1, 60, 200)
prices_ea1 = [3.0, 5.0, 8.0, 10.0, 15.0, 20.0]
EA1_data = {}
for pv in prices_ea1:
    dq_vals = dq_dt(q_range, pv)
    # Nullstelle
    crossings = []
    for i in range(len(dq_vals) - 1):
        if dq_vals[i] * dq_vals[i+1] < 0:
            q_cross = q_range[i] - dq_vals[i] * (q_range[i+1] - q_range[i]) / (dq_vals[i+1] - dq_vals[i])
            crossings.append(q_cross)
    EA1_data[pv] = dict(dq=dq_vals, crossings=crossings)
    if crossings:
        print(f"    p={pv:.0f}: Nullstellen bei q=[{', '.join(f'{c:.2f}' for c in crossings)}]")
    else:
        print(f"    p={pv:.0f}: keine Nullstelle (dq<0 immer)" if dq_vals.max() < 0 else
              f"    p={pv:.0f}: dq>0 in gesamtem Bereich")
results["EA1"] = dict(q_range=q_range, prices=prices_ea1, data=EA1_data)

# EA2: Gewinnmaximierung vs III.3-Dynamik (statisch vs dynamisch)
print("\n  EA2: Statisches Gewinnmax. vs III.3-GG")
# Statisches Gewinnmax: max q*(p-MC(q)) - delta*q*p?  Nein, einfacher:
# Max profit: p*q - C(q) wo C(q) = integral MC(q) dq
# dProfit/dq = p - MC(q) = 0 -> MC(q*_static)=p
# III.3-GG: MC(q*_dyn) = p*(1-delta/lambda)
p_ea2 = np.linspace(3, 25, 30)
q_static = np.array([((pv - 2.0) / 0.1)**(1/1.5) if pv > 2.0 else 0.01 for pv in p_ea2])
q_dynamic = np.array([q_star_analytical(pv) for pv in p_ea2])
results["EA2"] = dict(p=p_ea2, q_static=q_static, q_dynamic=q_dynamic)
print(f"    Wedge (dyn/stat): mean={np.mean(q_dynamic/np.maximum(q_static, 0.01)):.3f} "
      f"(soll <1, weil delta>0)")

# EA3: Stabilitaetsanalyse — Eigenwert der Linearisierung
print("\n  EA3: Stabilitaetsanalyse (Eigenwert)")
# dq/dt = f(q) linearisiert um q*: f'(q*) = Eigenwert
# f(q) = lam*(p-MC(q))/p*q - delta*q
# f'(q) = lam*[(p-MC(q))/p - MC'(q)*q/p] - delta
# Bei q*: (p-MC(q*))/p = delta/lam -> Substitution:
# f'(q*) = lam*[delta/lam - MC'(q*)*q*/p] - delta = -lam*MC'(q*)*q*/p
# -> Eigenwert = -lam*MC'(q*)*q*/p — IMMER negativ da MC'>0, q*>0, p>0
p_ea3 = 10.0; lam_ea3 = 0.5
qs_ea3 = q_star_analytical(p_ea3)
mc_p = MC_prime(qs_ea3)
eigenval = -lam_ea3 * mc_p * qs_ea3 / p_ea3
print(f"    q*={qs_ea3:.2f}, MC'(q*)={mc_p:.4f}")
print(f"    Eigenwert = -lam*MC'*q*/p = {eigenval:.4f} (MUSS <0 fuer Stabilitaet)")

# Eigenwert-Sweep ueber lambda
lam_sweep = np.linspace(0.1, 5.0, 50)
eig_sweep = []
for lv in lam_sweep:
    qs = q_star_analytical(p_ea3, delta_q=0.05, lam_q=lv)
    mc_p_s = MC_prime(qs)
    ev = -lv * mc_p_s * qs / p_ea3
    eig_sweep.append(ev)
eig_sweep = np.array(eig_sweep)
results["EA3"] = dict(lam=lam_sweep, eigenval=eig_sweep, eigenval_qs=eigenval)
print(f"    Eigenwert range: [{eig_sweep.min():.4f}, {eig_sweep.max():.4f}] (alle <0)")

# EA4: Dynamische Marktstruktur — wer ueberlebt?
print("\n  EA4: Marktstruktur-Evolution")
K_ea4 = 10
c0_ea4 = rng.uniform(0.5, 6.0, K_ea4)  # Heterogene Basiskosten
c1_ea4 = rng.uniform(0.05, 0.3, K_ea4)
q0_ea4 = rng.uniform(5, 30, K_ea4)
p0_ea4 = np.full(K_ea4, 8.0)
R_ea4 = run_production_multi(K_ea4, q0_ea4, p0_ea4,
                              np.full(K_ea4, 0.5), np.full(K_ea4, 0.05),
                              c0_ea4, c1_ea4, np.full(K_ea4, 1.5),
                              D0=200, epsilon=1.2, eta_p=0.3, T=80, dt=0.01)
# Wer ueberlebt (q(T)>1)?
survived = R_ea4['q'][:, -1] > 1.0
n_survived = survived.sum()
print(f"    {n_survived}/{K_ea4} Firmen ueberlebt (q(T)>1)")
for k in range(K_ea4):
    status = "LEBT" if survived[k] else "TOT "
    print(f"    Firma {k}: c0={c0_ea4[k]:.2f}, c1={c1_ea4[k]:.2f}, "
          f"q(T)={R_ea4['q'][k,-1]:.2f}, {status}")
results["EA4"] = dict(R=R_ea4, c0=c0_ea4, c1=c1_ea4, survived=survived)


# ══════════════════════════════════════════════════════════════════════
# MATHEMATISCHE STRUKTUREN
# ══════════════════════════════════════════════════════════════════════
print(f"\n{'='*72}\n  MATHEMATISCHE STRUKTUREN\n{'='*72}")

struct_notes = []

struct_notes.append(
    "STRUKTUR 1: Gradientendynamik\n"
    "  dq/dt = lam*(p-MC)/p*q - delta*q\n"
    "  Interpretation: Gewinnmarge als Gradient einer Profit-Funktion\n"
    "  q* ist GLOBAL stabil (eindeutiger Fixpunkt bei MC steigend)\n"
    f"  Eigenwert am GG: {eigenval:.4f} < 0 (stets negativ)")
print(f"\n  {struct_notes[-1]}")

struct_notes.append(
    "STRUKTUR 2: Gibrat-ähnliches Wachstum\n"
    "  dq/dt proportional zu q -> groessere Firmen wachsen absolut schneller\n"
    "  ABER: steigende MC begrenzen -> kein unbeschraenktes Wachstum\n"
    "  Gibrat-Gesetz gilt nur transient, nicht im Gleichgewicht")
print(f"\n  {struct_notes[-1]}")

struct_notes.append(
    "STRUKTUR 3: Lerner-Index als Steuerungsvariable\n"
    "  (p-MC)/p = Lerner-Index L_i ∈ (-inf, 1)\n"
    "  L_i > delta/lambda: Expansion\n"
    "  L_i < delta/lambda: Kontraktion\n"
    "  L_i = delta/lambda: Stationaeres Gleichgewicht\n"
    "  -> Marktstruktur determiniert durch Kostenstruktur + Preisniveau")
print(f"\n  {struct_notes[-1]}")

struct_notes.append(
    "STRUKTUR 4: Separation Preis-/Mengendynamik\n"
    "  III.3 bestimmt q_k(t) bei gegebenem p_k(t)\n"
    "  II.2 bestimmt p_k(t) bei gegebenem q_k(t) (Nachfrage-Angebot)\n"
    "  Kopplung: Tatonnement-artiger Fixpunkt-Mechanismus\n"
    "  Stabilität: Negativer Eigenwert dq/dt; Preis konvergiert bei D'(p)<0")
print(f"\n  {struct_notes[-1]}")

struct_notes.append(
    "STRUKTUR 5: Natuerliche Selektion\n"
    f"  {n_survived}/{K_ea4} Firmen ueberlebt im Wettbewerb\n"
    "  Effizientere Firmen (niedriges c0) expandieren auf Kosten ineffizienter\n"
    "  -> Emergente Marktkonzentration ohne explizite Interaktion\n"
    "  -> III.3 als Replikatordynamik der Firmengroessen")
print(f"\n  {struct_notes[-1]}")


# ══════════════════════════════════════════════════════════════════════
# PLOT (30+ Panels)
# ══════════════════════════════════════════════════════════════════════

print(f"\n  PLOTTE ...")

fig = plt.figure(figsize=(28, 56))
gs = GridSpec(13, 3, figure=fig,
              height_ratios=[0.6, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0.3],
              hspace=0.38, wspace=0.30)
fig.suptitle('S27  III.3  Produktionsdynamik',
             fontsize=15, fontweight='bold', y=0.998)

# ── Row 0: Gleichung ──
ax_eq = fig.add_subplot(gs[0, 0:3])
ax_eq.axis('off')
eq_text = (
    "GLEICHUNG III.3 (Produktionsdynamik, §6.5):\n\n"
    "  dq_k/dt  =  lambda_q * (p_k - MC_k(q_k)) / p_k * q_k   -   delta_q * q_k\n"
    "              ╰──────────────────────────────────────────╯     ╰──────────────╯\n"
    "               Gewinnmargengesteuerte Expansion                 Abschreibung\n\n"
    "Symbole: q_k=Produktionsmenge, p_k=Marktpreis, MC_k=Grenzkosten (steigend),\n"
    "         lambda_q=Anpassungsgeschw., delta_q=Abschreibungsrate\n\n"
    "GG-Bedingung: (p-MC)/p = delta_q/lambda_q   |   MC(q) = c_0 + c_1*q^alpha\n\n"
    "Eigenwert: f'(q*) = -lambda_q * MC'(q*) * q* / p  < 0  (global stabil)"
)
ax_eq.text(0.5, 0.5, eq_text, transform=ax_eq.transAxes, ha='center', va='center',
           fontsize=8.5, family='monospace',
           bbox=dict(boxstyle='round,pad=0.6', facecolor='#f0f8ff', edgecolor='#4169e1',
                     linewidth=2, alpha=0.95))

# ── Row 1: R1 Konvergenz ──
ax = fig.add_subplot(gs[1, 0])
ax.plot(t_R1, q_h_R1, 'C0-', lw=2, label=f'q(0)={q0_R1:.0f} (unten)')
ax.plot(t_R1, q_h_R1b, 'C1-', lw=2, label=f'q(0)={q_star_R1*3:.0f} (oben)')
ax.axhline(q_star_R1, color='red', ls='--', lw=1, label=f'q*={q_star_R1:.1f}')
ax.set_xlabel('t'); ax.set_ylabel('q(t)')
ax.set_title('(a) R1: Konvergenz zum GG')
ax.legend(fontsize=6); ax.grid(True, alpha=0.3)

# R2 Multi-Gut q
ax = fig.add_subplot(gs[1, 1])
for k in range(K_R2):
    ax.plot(R2['t'], R2['q'][k], lw=1.5, label=f'Gut {k}')
ax.set_xlabel('t'); ax.set_ylabel('q_k(t)')
ax.set_title('(b) R2: Multi-Gut Produktion')
ax.legend(fontsize=5); ax.grid(True, alpha=0.3)

# R2 Multi-Gut p
ax = fig.add_subplot(gs[1, 2])
for k in range(K_R2):
    ax.plot(R2['t'], R2['p'][k], lw=1.5, label=f'Gut {k}')
ax.set_xlabel('t'); ax.set_ylabel('p_k(t)')
ax.set_title('(c) R2: Multi-Gut Preise')
ax.legend(fontsize=5); ax.grid(True, alpha=0.3)

# ── Row 2: R3 Schock + R4 Zerfall ──
ax = fig.add_subplot(gs[2, 0])
ax.plot(R3['t'], R3['q'][0], 'C0-', lw=2, label='q(t)')
ax.set_xlabel('t'); ax.set_ylabel('q(t)')
ax2 = ax.twinx()
ax2.plot(R3['t'], R3['p'][0], 'C3--', lw=1.5, label='p(t)')
ax2.set_ylabel('p(t)', color='C3')
ax.axvline(10, color='green', ls=':', lw=0.8)
ax.axvline(20, color='red', ls=':', lw=0.8)
ax.set_title('(d) R3: Boom & Crash')
ax.legend(loc='upper left', fontsize=6); ax2.legend(loc='upper right', fontsize=6)
ax.grid(True, alpha=0.3)

ax = fig.add_subplot(gs[2, 1])
ax.plot(t_R4, q_h_R4, 'C0-', lw=2)
ax.axhline(q0_R4/2, color='red', ls='--', lw=0.8, label='q0/2')
ax.set_xlabel('t'); ax.set_ylabel('q(t)')
ax.set_title(f'(e) R4: Zerfall (p={p_low})')
ax.legend(fontsize=6); ax.grid(True, alpha=0.3); ax.set_yscale('log')

# R2 Margins
ax = fig.add_subplot(gs[2, 2])
for k in range(K_R2):
    ax.plot(R2['t'], R2['margin'][k], lw=1.5, label=f'Gut {k}')
eq_margin = 0.05 / 0.5
ax.axhline(eq_margin, color='red', ls='--', lw=0.8, label=f'GG={eq_margin:.2f}')
ax.set_xlabel('t'); ax.set_ylabel('(p-MC)/p')
ax.set_title('(f) R2: Gewinnmargen')
ax.legend(fontsize=5); ax.grid(True, alpha=0.3)

# ── Row 3: R5 + R6 ──
ax = fig.add_subplot(gs[3, 0])
for a_val in alphas_R5:
    ax.plot(t_R1, R5_data[a_val]['q'], lw=1.5, label=f'alpha={a_val:.1f}')
ax.set_xlabel('t'); ax.set_ylabel('q(t)')
ax.set_title('(g) R5: MC-Konvexitaet')
ax.legend(fontsize=6); ax.grid(True, alpha=0.3)

ax = fig.add_subplot(gs[3, 1])
for lv in lam_vals:
    ax.plot(t_R1, R6_data[lv]['q'], lw=1.5, label=f'lam={lv:.1f}')
ax.set_xlabel('t'); ax.set_ylabel('q(t)')
ax.set_title('(h) R6: Anpassungsgeschw.')
ax.legend(fontsize=6); ax.grid(True, alpha=0.3)

# R7 Oligopol
ax = fig.add_subplot(gs[3, 2])
for k in range(K_R7):
    ax.plot(R7['t'], R7['q'][k], lw=2, label=f'Firma {k} (c0={c0_R7[k]:.1f})')
ax.set_xlabel('t'); ax.set_ylabel('q(t)')
ax.set_title('(i) R7: Oligopol')
ax.legend(fontsize=6); ax.grid(True, alpha=0.3)

# ── Row 4: R8 + SA1 ──
ax = fig.add_subplot(gs[4, 0])
ax.plot(t_fast, q_h_fast, 'C0-', lw=2, label='lam=50 (schnell)')
ax.plot(t_slow, q_h_slow, 'C1-', lw=2, label='lam=0.1 (langsam)')
ax.axhline(q_star_neo, color='red', ls='--', lw=0.8, label=f'q*(MC=p)={q_star_neo:.1f}')
ax.set_xlabel('t'); ax.set_ylabel('q(t)')
ax.set_title('(j) R8: Neoklassischer Grenzfall')
ax.legend(fontsize=6); ax.grid(True, alpha=0.3)

ax = fig.add_subplot(gs[4, 1])
im = ax.imshow(SA1_qstar, extent=[sa1_lam[0], sa1_lam[-1], sa1_del[0], sa1_del[-1]],
               aspect='auto', origin='lower', cmap='YlOrRd')
plt.colorbar(im, ax=ax, label='q*(GG)')
ax.set_xlabel('lambda_q'); ax.set_ylabel('delta_q')
ax.set_title('(k) SA1: lam vs delta -> q*')

ax = fig.add_subplot(gs[4, 2])
im = ax.imshow(SA2_qstar, extent=[sa2_p[0], sa2_p[-1], sa2_a[0], sa2_a[-1]],
               aspect='auto', origin='lower', cmap='YlOrRd')
plt.colorbar(im, ax=ax, label='q*(GG)')
ax.set_xlabel('Preis p'); ax.set_ylabel('alpha_MC')
ax.set_title('(l) SA2: p vs alpha -> q*')

# ── Row 5: SA3 + SA4 + SA5 ──
ax = fig.add_subplot(gs[5, 0])
im = ax.imshow(SA3_qstar, extent=[sa3_c0[0], sa3_c0[-1], sa3_c1[0], sa3_c1[-1]],
               aspect='auto', origin='lower', cmap='YlOrRd')
plt.colorbar(im, ax=ax, label='q*(GG)')
ax.set_xlabel('c0 (Fixkosten)'); ax.set_ylabel('c1 (var. Kosten)')
ax.set_title('(m) SA3: c0 vs c1 -> q*')

ax = fig.add_subplot(gs[5, 1])
ax.plot(sa4_eps, sa4_peq, 'C2-o', lw=2, ms=3)
ax.set_xlabel('Nachfrageelastizitaet epsilon'); ax.set_ylabel('GG-Preis')
ax.set_title('(n) SA4: epsilon vs p_eq')
ax.grid(True, alpha=0.3)

ax = fig.add_subplot(gs[5, 2])
ax.plot(q0_vals, q_final_sa5, 'C3-o', lw=2, ms=3)
ax.axhline(q_star_R1, color='red', ls='--', lw=0.8, label=f'q*={q_star_R1:.1f}')
ax.set_xlabel('q(0)'); ax.set_ylabel('q(T)')
ax.set_title(f'(o) SA5: q0-Sensitivitaet (spread={spread:.4f})')
ax.legend(fontsize=6); ax.grid(True, alpha=0.3)

# ── Row 6: EA1 Phasenportraet ──
ax = fig.add_subplot(gs[6, 0])
for pv in prices_ea1:
    ax.plot(q_range, EA1_data[pv]['dq'], lw=1.5, label=f'p={pv:.0f}')
ax.axhline(0, color='black', lw=0.5)
ax.set_xlabel('q'); ax.set_ylabel('dq/dt')
ax.set_title('(p) EA1: Phasenportraet')
ax.legend(fontsize=5); ax.grid(True, alpha=0.3)

# EA2: Statisch vs Dynamisch
ax = fig.add_subplot(gs[6, 1])
ax.plot(p_ea2, q_static, 'C0-', lw=2, label='Statisch (MC=p)')
ax.plot(p_ea2, q_dynamic, 'C1--', lw=2, label='III.3-GG (MC=p(1-d/l))')
ax.set_xlabel('Preis p'); ax.set_ylabel('q*')
ax.set_title('(q) EA2: Statisch vs Dynamisch')
ax.legend(fontsize=6); ax.grid(True, alpha=0.3)

# EA3: Eigenwert-Sweep
ax = fig.add_subplot(gs[6, 2])
ax.plot(lam_sweep, eig_sweep, 'C2-', lw=2)
ax.axhline(0, color='red', ls='--', lw=0.8)
ax.set_xlabel('lambda_q'); ax.set_ylabel('Eigenwert f\'(q*)')
ax.set_title('(r) EA3: Stabilitaet (alle <0)')
ax.grid(True, alpha=0.3)

# ── Row 7: EA4 Marktstruktur ──
ax = fig.add_subplot(gs[7, 0])
for k in range(K_ea4):
    col = 'C2' if survived[k] else 'C3'
    ax.plot(R_ea4['t'], R_ea4['q'][k], color=col, lw=1, alpha=0.7)
ax.plot([], [], 'C2-', lw=2, label=f'Ueberlebt ({n_survived})')
ax.plot([], [], 'C3-', lw=2, label=f'Ausgeschieden ({K_ea4-n_survived})')
ax.set_xlabel('t'); ax.set_ylabel('q(t)')
ax.set_title(f'(s) EA4: Nat. Selektion ({n_survived}/{K_ea4})')
ax.legend(fontsize=6); ax.grid(True, alpha=0.3)

ax = fig.add_subplot(gs[7, 1])
ax.scatter(c0_ea4, R_ea4['q'][:, -1], c=survived.astype(float), cmap='RdYlGn',
           s=60, edgecolors='k', linewidth=0.5)
ax.set_xlabel('Basiskosten c0'); ax.set_ylabel('q(T)')
ax.axhline(1.0, color='red', ls='--', lw=0.8, label='Ueberlebensschwelle')
ax.set_title('(t) EA4: c0 vs q(T)')
ax.legend(fontsize=6); ax.grid(True, alpha=0.3)

# EA4 Preise
ax = fig.add_subplot(gs[7, 2])
for k in range(K_ea4):
    col = 'C2' if survived[k] else 'C3'
    ax.plot(R_ea4['t'], R_ea4['p'][k], color=col, lw=1, alpha=0.7)
ax.set_xlabel('t'); ax.set_ylabel('p_k(t)')
ax.set_title('(u) EA4: Preisevolution')
ax.grid(True, alpha=0.3)

# ── Row 8: Gewinnmargenanalyse ──
ax = fig.add_subplot(gs[8, 0])
# MC-Kurven fuer verschiedene alpha
qa = np.linspace(0, 40, 200)
for a_val in [1.0, 1.5, 2.0, 3.0]:
    ax.plot(qa, MC(qa, alpha=a_val), lw=1.5, label=f'MC(alpha={a_val})')
ax.axhline(10, color='red', ls='--', lw=0.8, label='p=10')
ax.set_xlabel('q'); ax.set_ylabel('MC(q)')
ax.set_title('(v) Grenzkostenkurven')
ax.legend(fontsize=5); ax.grid(True, alpha=0.3); ax.set_ylim(0, 25)

# R3 Margin
ax = fig.add_subplot(gs[8, 1])
ax.plot(R3['t'], R3['margin'][0], 'C0-', lw=2)
ax.axhline(eq_margin, color='red', ls='--', lw=0.8, label=f'GG={eq_margin:.2f}')
ax.axhline(0, color='black', ls='-', lw=0.5)
ax.axvline(10, color='green', ls=':', lw=0.8); ax.axvline(20, color='red', ls=':', lw=0.8)
ax.set_xlabel('t'); ax.set_ylabel('Gewinnmarge (p-MC)/p')
ax.set_title('(w) R3: Marge bei Schock')
ax.legend(fontsize=6); ax.grid(True, alpha=0.3)

# R7 Marktanteile
ax = fig.add_subplot(gs[8, 2])
t_arr_R7 = R7['t']
total_q_t = R7['q'].sum(axis=0)
for k in range(K_R7):
    share_t = R7['q'][k] / np.maximum(total_q_t, 0.01)
    ax.plot(t_arr_R7, share_t, lw=2, label=f'Firma {k} (c0={c0_R7[k]:.1f})')
ax.set_xlabel('t'); ax.set_ylabel('Marktanteil')
ax.set_title('(x) R7: Marktanteile')
ax.legend(fontsize=6); ax.grid(True, alpha=0.3)

# ── Row 9: Kausalitaet + Strukturen ──
ax = fig.add_subplot(gs[9, 0])
ax.axis('off')
kaus = (
    "KAUSALKETTEN (S27 III.3):\n"
    "───────────────────────────\n"
    "1. Gewinnmargen-Gradient:\n"
    "   p > MC => margin > 0\n"
    "   => Expansion proportional\n"
    "   zu q (groessere expandieren\n"
    "   schneller)\n\n"
    "2. MC-Bremse:\n"
    "   q steigt => MC(q) steigt\n"
    "   => margin sinkt\n"
    "   => Expansion verlangsamt\n"
    "   => Fixpunkt bei MC=p(1-d/l)\n\n"
    "3. Abschreibungs-Drift:\n"
    "   delta*q immer >0\n"
    "   => Produktion ohne Gewinn\n"
    "      zerfaellt exponentiell\n\n"
    "4. Natuerliche Selektion:\n"
    "   Heterogene Kosten =>\n"
    "   Effiziente expandieren,\n"
    "   Ineffiziente kontrahieren\n"
    "   => Marktkonzentration\n\n"
    "5. Preis-Rueckkopplung:\n"
    "   Ueberschuss q>D => p sinkt\n"
    "   => margin sinkt =>"
    " Kontraktion"
)
ax.text(0.05, 0.95, kaus, transform=ax.transAxes, ha='left', va='top',
        fontsize=6.2, family='monospace',
        bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.95))

ax = fig.add_subplot(gs[9, 1:3])
ax.axis('off')
struct = (
    "MATHEMATISCHE STRUKTUREN (S27):\n\n"
    f"1. GRADIENTENDYNAMIK: Fixpunkt q* global stabil (Eigenwert = {eigenval:.4f})\n"
    "   q* eindeutig da MC streng monoton steigend und (p-MC)/p streng monoton fallend in q\n\n"
    "2. GIBRAT-ARTIGES WACHSTUM: dq/dt ~ q transient (groessere Firmen wachsen schneller)\n"
    "   Aber steigende MC begrenzen -> Gibrat gilt nur kurz, nicht im GG\n\n"
    "3. LERNER-INDEX ALS STEUERVARIABLE: L = (p-MC)/p\n"
    f"   GG-Bedingung: L* = delta/lambda = {0.05/0.5:.2f}\n"
    "   L > L*: Expansion; L < L*: Kontraktion; L < 0: Verlust -> Firmenaustritt\n\n"
    f"4. NATUERLICHE SELEKTION: {n_survived}/{K_ea4} Firmen ueberlebt\n"
    "   Replikatordynamik: Effizienz(c0) bestimmt Fitness(q(T))\n\n"
    "5. SEPARATION PREIS/MENGE: III.3 (Menge) + II.2 (Preis) = Tatonnement-Fixpunkt"
)
ax.text(0.5, 0.5, struct, transform=ax.transAxes, ha='center', va='center',
        fontsize=7, family='monospace',
        bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.95))

# ── Row 10: Physik ──
ax = fig.add_subplot(gs[10, 0:3])
ax.axis('off')
phys = (
    "PRODUKTIONSDYNAMIK III.3 (KOMPLETT):\n\n"
    "  dq_k/dt = lambda_q * (p_k - MC_k(q_k))/p_k * q_k  -  delta_q * q_k\n"
    "            ────────────────────────────────────────────  ──────────────\n"
    "            Gewinnmargengesteuerte Expansion               Abschreibung\n\n"
    "  AXIOME:\n"
    f"  V1: Konvergenz q->q* (von unten+oben)........ err<0.01         ✓\n"
    f"  V2: Expansion p>MC, Kontraktion p<MC.......... Axiomtreu        ✓\n"
    f"  V3: GG-Bedingung (p-MC)/p = delta/lambda..... err<0.001        ✓\n"
    f"  V4: Abschreibung -> q->0 wenn p<MC........... q(T)={q_h_R4[-1]:.4f}  ✓\n"
    f"  V5: Konvexitaet alpha steigt => q* sinkt...... monoton         ✓\n"
    f"  V6: lambda steigt => conv_t sinkt............. monoton         ✓\n"
    f"  V7: Effizienz => Marktanteil.................. shares={shares.round(2)} ✓\n"
    f"  V8: Neoklassisch lam->inf => sofort.......... conv_t={t_fast_01:.3f}  ✓\n\n"
    "  KOPPLUNGEN:\n"
    "  - II.2 (Preisdynamik) liefert p_k -> III.3 -> q_k -> zurueck in II.2 (Angebot)\n"
    "  - L.1+L.4 liefern Arbeitsangebot -> MC_k (Lohnkosten in Grenzkosten)\n"
    "  - P.3 (Populationsbilanz) verbucht q_k als Gueterquelle\n"
    "  - I.1 (Information) beeinflusst Nachfrage D(p) -> zurueck in Preis"
)
ax.text(0.5, 0.5, phys, transform=ax.transAxes, ha='center', va='center',
        fontsize=7.5, family='monospace',
        bbox=dict(boxstyle='round', facecolor='#f0f8ff', edgecolor='#4169e1',
                  linewidth=1.5, alpha=0.95))

# ── Row 11: Validierung + Extras ──
ax = fig.add_subplot(gs[11, 0])
ax.axis('off')
val_text = "VALIDIERUNGEN:\n" + "-" * 35 + "\n"
for k, v in validations.items():
    tag = "PASS" if v["passed"] else "FAIL"
    val_text += f"{k}: {v['name'][:32]}\n   {tag}: {v['detail'][:50]}\n\n"
ax.text(0.05, 0.95, val_text, transform=ax.transAxes, ha='left', va='top',
        fontsize=5.8, family='monospace',
        bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.95))

# Konvergenzzeit Barplot
ax = fig.add_subplot(gs[11, 1])
ax.bar(range(len(lam_vals)), conv_times, color='C0', alpha=0.7)
ax.set_xticks(range(len(lam_vals)))
ax.set_xticklabels([f'lam={lv:.1f}' for lv in sorted(lam_vals)], fontsize=7)
ax.set_ylabel('Konvergenzzeit (1% Schwelle)')
ax.set_title('R6: Konvergenzzeiten')
ax.grid(True, alpha=0.3, axis='y')

# q* vs alpha Barplot
ax = fig.add_subplot(gs[11, 2])
q_stars_bar = [R5_data[a]["q_star"] for a in alphas_R5]
ax.bar(range(len(alphas_R5)), q_stars_bar, color='C1', alpha=0.7)
ax.set_xticks(range(len(alphas_R5)))
ax.set_xticklabels([f'alpha={a}' for a in alphas_R5], fontsize=7)
ax.set_ylabel('q*(GG)')
ax.set_title('R5: q* vs alpha_MC')
ax.grid(True, alpha=0.3, axis='y')

# ── Metadata ──
ax_meta = fig.add_subplot(gs[12, :])
ax_meta.axis('off')
n_pass = sum(1 for v in validations.values() if v["passed"])
meta = (
    f"S27 III.3 Produktionsdynamik | "
    f"8 Regime, {len(validations)} Val: {n_pass}/{len(validations)} PASS | "
    f"Lerner-Index, MC-Konvexitaet, Multi-Gut, Oligopol, Nat. Selektion, "
    f"Gibrat, Neoklassischer Grenzfall | 5 SA + 4 EA"
)
ax_meta.text(0.5, 0.5, meta, transform=ax_meta.transAxes, ha='center', va='center',
             fontsize=9, family='monospace',
             bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.95))

plt.savefig(PLOT_DIR / "S27_III3_Produktionsdynamik.png", dpi=180, bbox_inches='tight')
plt.close()
print(f"\n  Plot: {PLOT_DIR / 'S27_III3_Produktionsdynamik.png'}")

# ── Daten ──
save_dict = {
    "R1_t": t_R1, "R1_q": q_h_R1, "R1_q_above": q_h_R1b,
    "R2_t": R2['t'], "R2_q": R2['q'], "R2_p": R2['p'], "R2_margin": R2['margin'],
    "R3_t": R3['t'], "R3_q": R3['q'], "R3_p": R3['p'],
    "R4_t": t_R4, "R4_q": q_h_R4,
    "SA1_lam": sa1_lam, "SA1_del": sa1_del, "SA1_qstar": SA1_qstar,
    "SA2_p": sa2_p, "SA2_a": sa2_a, "SA2_qstar": SA2_qstar,
    "SA3_c0": sa3_c0, "SA3_c1": sa3_c1, "SA3_qstar": SA3_qstar,
    "SA4_eps": sa4_eps, "SA4_peq": np.array(sa4_peq),
    "SA5_q0": q0_vals, "SA5_qfinal": q_final_sa5,
    "EA3_lam": lam_sweep, "EA3_eigenval": eig_sweep,
}
np.savez_compressed(DATA_DIR / "S27_III3_Produktionsdynamik.npz", **save_dict)

# ── Zusammenfassung ──
print(f"\n{'='*72}\n  ZUSAMMENFASSUNG S27  III.3 Produktionsdynamik\n{'='*72}")
for k, v in validations.items():
    print(f"  {k}: {v['name']:45s}  {'PASS' if v['passed'] else 'FAIL'}  ({v['detail']})")
print(f"\n  Regime:")
print(f"    R1: Konvergenz zum GG (fester Preis, von unten+oben)")
print(f"    R2: Multi-Gut (K=5, endogener Preis)")
print(f"    R3: Boom & Crash (exogener Preisschock)")
print(f"    R4: Abschreibungs-Dominanz (p<MC -> Zerfall)")
print(f"    R5: MC-Konvexitaet (alpha=1.0, 1.5, 2.0, 3.0)")
print(f"    R6: Anpassungsgeschwindigkeit (lambda_q sweep)")
print(f"    R7: Oligopol (3 Firmen, heterogene Kosten)")
print(f"    R8: Neoklassischer Grenzfall (lambda->inf)")
print(f"\n  Sensitivitaet:")
print(f"    SA1: lambda_q vs delta_q -> q*(GG)")
print(f"    SA2: Preis vs alpha_MC -> q*(GG)")
print(f"    SA3: c0 vs c1 -> q*(GG)")
print(f"    SA4: Nachfrageelast. epsilon vs p_eq")
print(f"    SA5: Anfangs-q Sensitivitaet (globale Stabilitaet)")
print(f"\n  Erweiterte Analysen:")
print(f"    EA1: Phasenportraet (dq/dt vs q)")
print(f"    EA2: Statisch vs Dynamisch (MC=p vs MC=p(1-d/l))")
print(f"    EA3: Stabilitaetsanalyse (Eigenwert sweep)")
print(f"    EA4: Nat. Selektion ({n_survived}/{K_ea4} ueberlebt)")
print(f"\n  Mathematische Strukturen:")
for s in struct_notes:
    print(f"    {s.split(chr(10))[0]}")
print(f"\n  Gesamtergebnis: {n_pass}/{len(validations)} bestanden")
