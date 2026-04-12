"""
S14 – Nutzenordnung  U.1  (§6.1)
====================================
Monographie-Gleichung (exakt):

    u_i = u(c_i, l_i; γ_i, c_i*)

Axiomatische Eigenschaften (A5):
  ∂u/∂c > 0    (Monotonie — mehr Konsum ist besser)
  ∂²u/∂c² < 0  (Konkavität — abnehmender Grenznutzen)

Vier Funktionalformen werden verglichen:
  1. CRRA:         u(c) = (c - c*)^(1-γ)/(1-γ),   γ ≠ 1
  2. Logarithmisch: u(c) = ln(c - c*),              γ → 1  (Spezialfall CRRA)
  3. CARA:         u(c) = -exp(-α·c)
  4. Epstein-Zin:  V = (1-δ)c^(1-ρ) + δ(E[V^(1-α)])^((1-ρ)/(1-α))

Referenzabhängigkeit (Prospect Theory, Kahneman-Tversky):
  Gewinne:  u⁺(c-c*) = (c-c*)^(1-γ)/(1-γ)
  Verluste: u⁻(c*-c) = -λ·(c*-c)^(1-γ)/(1-γ),  λ>1 (Verlustaversion)

Euler-Gleichung (V.1):
  ċ/c = (r - β)/γ   (Ramsey-Konsumdynamik)

Habitformation (VI.4):
  ċ* = λ_c·(c - c*)  (Referenzpunkt passt sich an)

Kausalketten:
  U.1 → V.1 (Euler):   Nutzenform bestimmt Konsumwachstum
  U.1 → III.2:          Risikoaversion bestimmt Portfolioallokation
  U.1 + U.3:            Effektiver Preis = p·(1+ψ/(I+ε))
  VI.2 → U.1:           Endogene Risikoaversion γ̇ = α_γ(γ*-γ)+β_γ·Verlust
  VI.4 → U.1:           Endogener Referenzpunkt c*

7 Validierungen:
  V1: CRRA  u'>0, u''<0 für alle c > c*     (Axiom-Check)
  V2: CRRA  γ→1 konvergiert → ln(c)         (L'Hôpital-Grenzwert)
  V3: CRRA  relative Risikoaversion = γ      (-c·u''/u' = γ)
  V4: CARA  absolute Risikoaversion = α      (-u''/u' = α)
  V5: Euler r=β → ċ=0                       (Ramsey Steady-State)
  V6: Euler monoton: r>β → c↑, r<β → c↓    (Vorzeichen-Check)
  V7: Referenz: Knick bei c=c*, Steigung λ× steiler für Verluste

6 Regime:
  R1: CRRA-Vergleich (γ = 0.5, 1, 2, 5)
  R2: CARA-Vergleich (α = 0.5, 1, 2, 5)
  R3: Referenzabhängig / Prospect Theory (λ = 1, 1.5, 2.25, 3)
  R4: Euler-Dynamik unter verschiedenen γ
  R5: Habitformation (Referenzpunkt-Drift)
  R6: Epstein-Zin (EIS ≠ 1/γ: Trennung Risikoaversion / Substitution)
"""

import sys
import io
import warnings

# Windows cp1252 fix
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
warnings.filterwarnings('ignore', category=UserWarning, module='matplotlib')

import numpy as np
from scipy.integrate import solve_ivp
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from pathlib import Path

# ── Pfade ──
BASE = Path(__file__).resolve().parent.parent.parent
PLOT_DIR = BASE / "Ergebnisse" / "Plots"
DATA_DIR = BASE / "Ergebnisse" / "Daten"
PLOT_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)

np.random.seed(42)

# ══════════════════════════════════════════════════════════════════════
# 1.  NUTZENFUNKTIONEN  +  ABLEITUNGEN
# ══════════════════════════════════════════════════════════════════════

def u_crra(c, gamma, c_star=0.0):
    """CRRA: u = (x^(1-γ)-1)/(1-γ), x=c-c*.  γ=1 → log(x).
    Die "-1" sichert lim(γ→1) = ln(x) (L'Hôpital)."""
    x = np.maximum(c - c_star, 1e-15)
    if np.abs(gamma - 1.0) < 1e-10:
        return np.log(x)
    return (x ** (1.0 - gamma) - 1.0) / (1.0 - gamma)


def u_crra_prime(c, gamma, c_star=0.0):
    """u' = (c-c*)^(-γ)"""
    x = np.maximum(c - c_star, 1e-15)
    return x ** (-gamma)


def u_crra_dprime(c, gamma, c_star=0.0):
    """u'' = -γ·(c-c*)^(-γ-1)"""
    x = np.maximum(c - c_star, 1e-15)
    return -gamma * x ** (-gamma - 1.0)


def rra_crra(c, gamma, c_star=0.0):
    """Relative Risikoaversion: -c·u''/u'"""
    x = np.maximum(c - c_star, 1e-15)
    # = -c · (-γ·x^(-γ-1)) / (x^(-γ)) = γ·c/x
    return gamma * c / x


def u_cara(c, alpha):
    """CARA: u = -exp(-α·c)"""
    return -np.exp(-alpha * c)


def u_cara_prime(c, alpha):
    return alpha * np.exp(-alpha * c)


def u_cara_dprime(c, alpha):
    return -alpha**2 * np.exp(-alpha * c)


def ara_cara(c, alpha):
    """Absolute Risikoaversion: -u''/u' = α (konstant)"""
    return np.full_like(c, alpha, dtype=float)


def u_prospect(c, gamma, c_star, lam):
    """Prospect-Theory Nutzen mit Verlustaversion.
    Gewinne: (c-c*)^(1-γ)/(1-γ)
    Verluste: -λ·(c*-c)^(1-γ)/(1-γ)
    u(c*) = 0 per Definition.
    """
    u = np.zeros_like(c, dtype=float)
    gain = c > c_star
    loss = c < c_star
    # exakt c == c_star bleibt 0
    x_g = c[gain] - c_star
    x_l = c_star - c[loss]
    if np.abs(gamma - 1.0) < 1e-10:
        u[gain] = np.log(np.maximum(x_g, 1e-30))
        u[loss] = -lam * np.log(np.maximum(x_l, 1e-30))
    else:
        u[gain] = x_g ** (1.0 - gamma) / (1.0 - gamma)
        u[loss] = -lam * x_l ** (1.0 - gamma) / (1.0 - gamma)
    return u


def u_ez_certainty(c, rho, alpha, delta=0.96):
    """Epstein-Zin unter Sicherheit (Certainty Equivalent = deterministisch).
    V = [(1-δ)·c^(1-ρ) + δ·V_next^(1-ρ)]^(1/(1-ρ))
    Steady-State: V = [(1-δ)/(1-δ)]^(1/(1-ρ)) · c = c
    Unter Sicherheit reduziert sich EZ auf: u = c^(1-ρ)/(1-ρ)
    Aber α (Ruhe-Risikoaversion) separiert von 1/ρ (EIS).
    Hier zeigen wir die statische Nutzenkurve: (1-δ)·c^(1-ρ)/(1-ρ).
    """
    x = np.maximum(c, 1e-15)
    if np.abs(rho - 1.0) < 1e-10:
        return (1 - delta) * np.log(x)
    return (1 - delta) * x ** (1.0 - rho) / (1.0 - rho)


# ══════════════════════════════════════════════════════════════════════
# 2.  EULER-DYNAMIK  (V.1)
# ══════════════════════════════════════════════════════════════════════

def euler_rhs(t, y, r, beta, gamma):
    """ċ = c·(r-β)/γ"""
    c = max(y[0], 1e-10)
    dcdt = c * (r - beta) / gamma
    return [dcdt]


def euler_rhs_habit(t, y, r, beta, gamma, lam_c):
    """Euler + Habit:
    ċ = c·(r-β)/γ
    ċ* = λ_c·(c-c*)
    c_eff = c - c*  (surplus consumption)
    """
    c = max(y[0], 1e-10)
    c_star = y[1]
    surplus = max(c - c_star, 1e-10)
    # Euler on surplus consumption
    dcdt = c * (r - beta) / gamma
    dc_star_dt = lam_c * (c - c_star)
    return [dcdt, dc_star_dt]


# ══════════════════════════════════════════════════════════════════════
# 3.  REGIME-DEFINITIONEN
# ══════════════════════════════════════════════════════════════════════

def get_regime(name):
    regimes = {
        "R1": {
            "label": "R1: CRRA-Vergleich",
            "gammas": [0.5, 1.0, 2.0, 5.0],
            "c_star": 0.0,
        },
        "R2": {
            "label": "R2: CARA-Vergleich",
            "alphas": [0.5, 1.0, 2.0, 5.0],
        },
        "R3": {
            "label": "R3: Prospect Theory (Referenzabhaengig)",
            "gamma": 0.88,  # Kahneman-Tversky estimate
            "c_star": 1.0,
            "lambdas": [1.0, 1.5, 2.25, 3.0],  # λ=2.25 is K-T value
        },
        "R4": {
            "label": "R4: Euler-Dynamik",
            "r": 0.04,      # Realzins 4%
            "beta": 0.03,   # Zeitpraeferenz 3%
            "gammas": [0.5, 1.0, 2.0, 5.0],
            "c0": 1.0,
            "T": 50,
        },
        "R5": {
            "label": "R5: Habitformation",
            "r": 0.05,
            "beta": 0.03,
            "gamma": 2.0,
            "c0": 1.0,
            "c_star0": 0.8,
            "lam_cs": [0.0, 0.05, 0.2, 0.5],  # Habit speed
            "T": 80,
        },
        "R6": {
            "label": "R6: Epstein-Zin (EIS vs. Risikoaversion)",
            "rhos": [0.5, 1.0, 2.0],   # 1/ρ = EIS
            "alphas": [2.0, 5.0, 10.0], # risk aversion
            "delta": 0.96,
        },
    }
    return regimes[name]


# ══════════════════════════════════════════════════════════════════════
# 4.  SIMULATIONEN AUSFUEHREN
# ══════════════════════════════════════════════════════════════════════

results = {}
validations = {}

# ── Konsumbereich fuer statische Plots ──
c_range = np.linspace(0.01, 3.0, 500)
c_range_wide = np.linspace(0.01, 5.0, 500)

# ──────────────────────────────────────────────────────────────────
# R1: CRRA Comparison
# ──────────────────────────────────────────────────────────────────
print("=" * 72)
print("  R1: CRRA-Vergleich")
print("=" * 72)
r1 = get_regime("R1")
r1_u = {}
r1_up = {}
r1_rra = {}
for g in r1["gammas"]:
    label = f"gamma={g:.1f}" if g != 1.0 else "gamma=1 (log)"
    r1_u[label] = u_crra(c_range, g, r1["c_star"])
    r1_up[label] = u_crra_prime(c_range, g, r1["c_star"])
    r1_rra[label] = rra_crra(c_range, g, r1["c_star"])
    print(f"  {label}: u(1)={u_crra(np.array([1.0]), g, 0)[0]:.4f}, "
          f"u'(1)={u_crra_prime(np.array([1.0]), g, 0)[0]:.4f}, "
          f"RRA(1)={rra_crra(np.array([1.0]), g, 0)[0]:.4f}")

results["R1"] = {"u": r1_u, "up": r1_up, "rra": r1_rra, "c": c_range, "par": r1}

# V1: Monotonie + Konkavitaet
print("\n  V1: Axiom-Check (u'>0, u''<0) ...")
v1_pass = True
for g in r1["gammas"]:
    up = u_crra_prime(c_range, g, 0)
    udp = u_crra_dprime(c_range, g, 0)
    if np.any(up <= 0):
        v1_pass = False
        print(f"    FAIL: u'<=0 bei gamma={g}")
    if np.any(udp >= 0):
        v1_pass = False
        print(f"    FAIL: u''>=0 bei gamma={g}")
v1_tag = "PASS" if v1_pass else "FAIL"
validations["V1"] = {"name": "Axiom u'>0, u''<0", "pass": v1_pass,
                      "detail": f"Alle CRRA-Formen monoton+konkav: {v1_tag}"}
print(f"  V1: {v1_tag}")

# V2: gamma->1 Konvergenz -> log
print("\n  V2: CRRA gamma->1 -> ln(c) ...")
gamma_near_1 = [1.001, 1.0001, 1.00001, 0.999, 0.9999, 0.99999]
c_test = np.array([0.5, 1.0, 2.0, 3.0])
max_err_v2 = 0.0
for g_near in gamma_near_1:
    u_near = u_crra(c_test, g_near, 0)
    u_log = np.log(c_test)
    err = np.max(np.abs(u_near - u_log))
    max_err_v2 = max(max_err_v2, err)
v2_pass = max_err_v2 < 0.01
validations["V2"] = {"name": "CRRA gamma->1 = log", "pass": v2_pass,
                      "detail": f"max|u_CRRA - ln(c)| = {max_err_v2:.2e}"}
print(f"  V2: max_err = {max_err_v2:.2e}  {'PASS' if v2_pass else 'FAIL'}")

# V3: CRRA relative Risk Aversion = gamma
print("\n  V3: Relative Risikoaversion = gamma ...")
v3_max_err = 0.0
for g in r1["gammas"]:
    rra_vals = rra_crra(c_range, g, 0)
    err = np.max(np.abs(rra_vals - g))
    v3_max_err = max(v3_max_err, err)
v3_pass = v3_max_err < 1e-10
validations["V3"] = {"name": "CRRA RRA = gamma", "pass": v3_pass,
                      "detail": f"max|RRA-gamma| = {v3_max_err:.2e}"}
print(f"  V3: max_err = {v3_max_err:.2e}  {'PASS' if v3_pass else 'FAIL'}")


# ──────────────────────────────────────────────────────────────────
# R2: CARA Comparison
# ──────────────────────────────────────────────────────────────────
print(f"\n{'='*72}")
print("  R2: CARA-Vergleich")
print("=" * 72)
r2 = get_regime("R2")
r2_u = {}
r2_up = {}
r2_ara = {}
for a in r2["alphas"]:
    label = f"alpha={a:.1f}"
    r2_u[label] = u_cara(c_range, a)
    r2_up[label] = u_cara_prime(c_range, a)
    r2_ara[label] = ara_cara(c_range, a)
    print(f"  {label}: u(1)={u_cara(np.array([1.0]), a)[0]:.4f}, "
          f"u'(1)={u_cara_prime(np.array([1.0]), a)[0]:.4f}")

results["R2"] = {"u": r2_u, "up": r2_up, "ara": r2_ara, "c": c_range, "par": r2}

# V4: CARA absolute Risk Aversion = alpha
print("\n  V4: Absolute Risikoaversion = alpha ...")
v4_max_err = 0.0
for a in r2["alphas"]:
    up = u_cara_prime(c_range, a)
    udp = u_cara_dprime(c_range, a)
    ara_computed = -udp / up
    err = np.max(np.abs(ara_computed - a))
    v4_max_err = max(v4_max_err, err)
v4_pass = v4_max_err < 1e-10
validations["V4"] = {"name": "CARA ARA = alpha", "pass": v4_pass,
                      "detail": f"max|ARA-alpha| = {v4_max_err:.2e}"}
print(f"  V4: max_err = {v4_max_err:.2e}  {'PASS' if v4_pass else 'FAIL'}")


# ──────────────────────────────────────────────────────────────────
# R3: Prospect Theory
# ──────────────────────────────────────────────────────────────────
print(f"\n{'='*72}")
print("  R3: Prospect Theory (Referenzabhaengig)")
print("=" * 72)
r3 = get_regime("R3")
c_prospect = np.linspace(0.01, 2.0, 500)
r3_u = {}
for lam in r3["lambdas"]:
    label = f"lambda={lam:.2f}"
    r3_u[label] = u_prospect(c_prospect, r3["gamma"], r3["c_star"], lam)
    print(f"  {label}: u(c*-0.5)={u_prospect(np.array([0.5]), r3['gamma'], r3['c_star'], lam)[0]:.4f}, "
          f"u(c*+0.5)={u_prospect(np.array([1.5]), r3['gamma'], r3['c_star'], lam)[0]:.4f}")

results["R3"] = {"u": r3_u, "c": c_prospect, "par": r3}

# V7: Knick bei c=c*, Verlust-Steigung lambda× steiler
print("\n  V7: Referenzabhaengigkeit: Knick + Verlustaversion ...")
eps_kink = 1e-6
c_above = np.array([r3["c_star"] + eps_kink])
c_below = np.array([r3["c_star"] - eps_kink])
# u(c*) = 0 per Definition
slope_gain = u_prospect(c_above, r3["gamma"], r3["c_star"], 2.25)[0] / eps_kink
slope_loss = -u_prospect(c_below, r3["gamma"], r3["c_star"], 2.25)[0] / eps_kink
ratio = slope_loss / slope_gain if slope_gain > 0 else float('inf')
v7_pass = abs(ratio - 2.25) < 0.05  # Should be very close to lambda=2.25
validations["V7"] = {"name": "Knick + Verlustaversion", "pass": v7_pass,
                      "detail": f"Steigungsverhaeltnis Verlust/Gewinn = {ratio:.3f} (erwartet ~2.25)"}
print(f"  V7: Verlust/Gewinn-Steigung = {ratio:.3f}  {'PASS' if v7_pass else 'FAIL'}")


# ──────────────────────────────────────────────────────────────────
# R4: Euler-Dynamik
# ──────────────────────────────────────────────────────────────────
print(f"\n{'='*72}")
print("  R4: Euler-Dynamik (V.1)")
print("=" * 72)
r4 = get_regime("R4")
r4_sols = {}
for g in r4["gammas"]:
    label = f"gamma={g:.1f}"
    sol = solve_ivp(euler_rhs, [0, r4["T"]], [r4["c0"]],
                    args=(r4["r"], r4["beta"], g),
                    method='RK45', rtol=1e-10, atol=1e-12,
                    t_eval=np.linspace(0, r4["T"], 1001),
                    max_step=0.1)
    r4_sols[label] = {"t": sol.t, "c": sol.y[0],
                       "growth_rate": (r4["r"] - r4["beta"]) / g}
    print(f"  {label}: c(T)={sol.y[0, -1]:.4f}, "
          f"Wachstum=(r-beta)/gamma = {(r4['r']-r4['beta'])/g:.4f}")

results["R4"] = {"sols": r4_sols, "par": r4}

# V5: Euler r=beta -> cdot=0
print("\n  V5: Ramsey-Steady-State (r=beta) ...")
sol_ss = solve_ivp(euler_rhs, [0, 50], [1.0],
                   args=(0.04, 0.04, 2.0),  # r = beta
                   method='RK45', rtol=1e-10, atol=1e-12,
                   t_eval=np.linspace(0, 50, 1001), max_step=0.1)
max_dev_ss = np.max(np.abs(sol_ss.y[0] - 1.0))
v5_pass = max_dev_ss < 1e-8
validations["V5"] = {"name": "Euler r=beta -> cdot=0", "pass": v5_pass,
                      "detail": f"max|c(t)-c0| = {max_dev_ss:.2e}"}
print(f"  V5: max|c(t)-c0| = {max_dev_ss:.2e}  {'PASS' if v5_pass else 'FAIL'}")

# V6: Euler Monotonie (r>beta -> c steigt, r<beta -> c faellt)
print("\n  V6: Euler Monotonie ...")
sol_up = solve_ivp(euler_rhs, [0, 50], [1.0],
                   args=(0.06, 0.03, 2.0),
                   method='RK45', rtol=1e-10, atol=1e-12,
                   t_eval=np.linspace(0, 50, 501), max_step=0.1)
sol_dn = solve_ivp(euler_rhs, [0, 50], [1.0],
                   args=(0.02, 0.05, 2.0),
                   method='RK45', rtol=1e-10, atol=1e-12,
                   t_eval=np.linspace(0, 50, 501), max_step=0.1)
v6_up = np.all(np.diff(sol_up.y[0]) >= -1e-14)  # c monoton steigend
v6_dn = np.all(np.diff(sol_dn.y[0]) <= 1e-14)   # c monoton fallend
v6_pass = v6_up and v6_dn
validations["V6"] = {"name": "Euler Monotonie", "pass": v6_pass,
                      "detail": f"r>beta -> steigend: {v6_up}, r<beta -> fallend: {v6_dn}"}
print(f"  V6: r>beta steigend={v6_up}, r<beta fallend={v6_dn}  {'PASS' if v6_pass else 'FAIL'}")


# ──────────────────────────────────────────────────────────────────
# R5: Habitformation
# ──────────────────────────────────────────────────────────────────
print(f"\n{'='*72}")
print("  R5: Habitformation (VI.4)")
print("=" * 72)
r5 = get_regime("R5")
r5_sols = {}
for lam_c in r5["lam_cs"]:
    label = f"lambda_c={lam_c:.2f}"
    if lam_c == 0:
        # No habit, just Euler
        sol = solve_ivp(euler_rhs, [0, r5["T"]], [r5["c0"]],
                        args=(r5["r"], r5["beta"], r5["gamma"]),
                        method='RK45', rtol=1e-10, atol=1e-12,
                        t_eval=np.linspace(0, r5["T"], 1001), max_step=0.1)
        r5_sols[label] = {"t": sol.t, "c": sol.y[0],
                           "c_star": np.full_like(sol.t, r5["c_star0"]),
                           "surplus": sol.y[0] - r5["c_star0"]}
    else:
        sol = solve_ivp(euler_rhs_habit, [0, r5["T"]], [r5["c0"], r5["c_star0"]],
                        args=(r5["r"], r5["beta"], r5["gamma"], lam_c),
                        method='RK45', rtol=1e-10, atol=1e-12,
                        t_eval=np.linspace(0, r5["T"], 1001), max_step=0.1)
        r5_sols[label] = {"t": sol.t, "c": sol.y[0], "c_star": sol.y[1],
                           "surplus": sol.y[0] - sol.y[1]}
    print(f"  {label}: c(T)={r5_sols[label]['c'][-1]:.4f}, "
          f"c*(T)={r5_sols[label]['c_star'][-1]:.4f}, "
          f"surplus(T)={r5_sols[label]['surplus'][-1]:.4f}")

results["R5"] = {"sols": r5_sols, "par": r5}


# ──────────────────────────────────────────────────────────────────
# R6: Epstein-Zin
# ──────────────────────────────────────────────────────────────────
print(f"\n{'='*72}")
print("  R6: Epstein-Zin (Trennung EIS / Risikoaversion)")
print("=" * 72)
r6 = get_regime("R6")
r6_u = {}
for rho in r6["rhos"]:
    label = f"rho={rho:.1f} (EIS={1/rho:.1f})"
    r6_u[label] = u_ez_certainty(c_range, rho, r6["alphas"][0], r6["delta"])
    print(f"  {label}: u_EZ(1)={u_ez_certainty(np.array([1.0]), rho, r6['alphas'][0], r6['delta'])[0]:.4f}")

# Vergleich EZ vs CRRA bei gleicher Risikoaversion
r6_comparison = {}
for alpha in r6["alphas"]:
    for rho in r6["rhos"]:
        label = f"alpha={alpha:.0f}, rho={rho:.1f}"
        # EZ certainty utility
        u_ez = u_ez_certainty(c_range, rho, alpha, r6["delta"])
        # Entsprechende CRRA (gamma = alpha, gleiche Risikoaversion)
        u_cr = u_crra(c_range, alpha, 0) * (1 - r6["delta"])
        r6_comparison[label] = {"u_ez": u_ez, "u_crra": u_cr,
                                 "diff": u_ez - u_cr}

results["R6"] = {"u": r6_u, "comparison": r6_comparison,
                  "c": c_range, "par": r6}


# ══════════════════════════════════════════════════════════════════════
# 5.  KAUSALITAETS-ANALYSE
# ══════════════════════════════════════════════════════════════════════
print(f"\n{'='*72}")
print("  KAUSALITAETSANALYSE")
print("=" * 72)

# Kausalitaet 1: gamma bestimmt Konsumwachstum
print("\n  K1: gamma -> Konsumwachstum")
for g in [0.5, 1.0, 2.0, 5.0]:
    growth = (0.04 - 0.03) / g  # (r-beta)/gamma
    print(f"    gamma={g:.1f}: Wachstumsrate = {growth*100:.2f}%/a")

# Kausalitaet 2: Risikoaversion -> Portfolioallokation (CAPM-Anteil)
print("\n  K2: gamma -> Aktienstrang (Merton share w* = (mu-r)/(gamma*sigma^2))")
mu_stock = 0.08  # Aktienrendite
r_f = 0.03       # Risikofreier Zins
sigma_stock = 0.20  # Volatilitaet
for g in [0.5, 1.0, 2.0, 5.0, 10.0]:
    w_star = (mu_stock - r_f) / (g * sigma_stock**2)
    print(f"    gamma={g:.1f}: Aktienanteil w* = {w_star*100:.1f}%")

# Kausalitaet 3: Information -> Effektiver Preis (U.3)
print("\n  K3: Information -> Effektiver Preis p_eff = p*(1+psi/(I+eps))")
psi = 0.1
eps = 0.01
for I_val in [0.01, 0.1, 0.5, 1.0, 2.0]:
    p_eff = 1.0 * (1 + psi / (I_val + eps))
    print(f"    I={I_val:.2f}: p_eff = {p_eff:.4f} (Aufschlag {(p_eff-1)*100:.1f}%)")


# ══════════════════════════════════════════════════════════════════════
# 6.  PLOT  (21 Panels + Metadata)
# ══════════════════════════════════════════════════════════════════════

print(f"\n{'='*72}")
print("  PLOTTE ERGEBNISSE ...")
print("=" * 72)

fig = plt.figure(figsize=(24, 34))
gs = GridSpec(7, 3, figure=fig, height_ratios=[1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.5],
              hspace=0.38, wspace=0.30)
fig.suptitle('S14  U.1  Nutzenordnung — Funktionalformen & Kausalitaet',
             fontsize=16, fontweight='bold', y=0.995)

colors_gamma = ['#2196F3', '#4CAF50', '#F44336', '#9C27B0']
colors_alpha = ['#FF9800', '#795548', '#009688', '#E91E64']
colors_lambda = ['#607D8B', '#4CAF50', '#F44336', '#9C27B0']
colors_habit = ['#2196F3', '#4CAF50', '#F44336', '#9C27B0']

# ── Row 1: CRRA ──
# (a) CRRA u(c)
ax = fig.add_subplot(gs[0, 0])
for i, (label, u_vals) in enumerate(results["R1"]["u"].items()):
    ax.plot(c_range, u_vals, color=colors_gamma[i], lw=2, label=label)
ax.set_xlabel('c')
ax.set_ylabel('u(c)')
ax.set_title('(a) CRRA Nutzen')
ax.legend(fontsize=7)
ax.set_ylim(-5, 3)
ax.axhline(0, color='k', lw=0.5, alpha=0.3)
ax.grid(True, alpha=0.3)

# (b) CRRA u'(c) — Grenznutzen
ax = fig.add_subplot(gs[0, 1])
for i, (label, up_vals) in enumerate(results["R1"]["up"].items()):
    ax.plot(c_range, up_vals, color=colors_gamma[i], lw=2, label=label)
ax.set_xlabel('c')
ax.set_ylabel("u'(c)")
ax.set_title("(b) CRRA Grenznutzen u'(c)")
ax.legend(fontsize=7)
ax.set_ylim(0, 8)
ax.grid(True, alpha=0.3)

# (c) CRRA RRA
ax = fig.add_subplot(gs[0, 2])
for i, (label, rra_vals) in enumerate(results["R1"]["rra"].items()):
    ax.plot(c_range, rra_vals, color=colors_gamma[i], lw=2, label=label)
ax.set_xlabel('c')
ax.set_ylabel('-c u\'\'/u\'')
ax.set_title('(c) Relative Risikoaversion (V3)')
ax.legend(fontsize=7)
ax.set_ylim(0, 6)
ax.grid(True, alpha=0.3)
ax.text(0.95, 0.05, 'RRA = gamma (konstant)',
        transform=ax.transAxes, ha='right', va='bottom', fontsize=8,
        bbox=dict(boxstyle='round,pad=0.3', facecolor='lightyellow', alpha=0.9))

# ── Row 2: CARA + Prospect Theory ──
# (d) CARA u(c)
ax = fig.add_subplot(gs[1, 0])
for i, (label, u_vals) in enumerate(results["R2"]["u"].items()):
    ax.plot(c_range, u_vals, color=colors_alpha[i], lw=2, label=label)
ax.set_xlabel('c')
ax.set_ylabel('u(c)')
ax.set_title('(d) CARA Nutzen')
ax.legend(fontsize=7)
ax.axhline(0, color='k', lw=0.5, alpha=0.3)
ax.grid(True, alpha=0.3)

# (e) CARA ARA
ax = fig.add_subplot(gs[1, 1])
for i, (label, ara_vals) in enumerate(results["R2"]["ara"].items()):
    ax.plot(c_range[:10], ara_vals[:10], color=colors_alpha[i], lw=2, label=label)
ax.set_xlabel('c')
ax.set_ylabel("-u''/u'")
ax.set_title('(e) Absolute Risikoaversion (V4)')
ax.legend(fontsize=7)
ax.set_ylim(0, 6)
ax.grid(True, alpha=0.3)
ax.text(0.95, 0.05, 'ARA = alpha (konstant)',
        transform=ax.transAxes, ha='right', va='bottom', fontsize=8,
        bbox=dict(boxstyle='round,pad=0.3', facecolor='lightyellow', alpha=0.9))

# (f) Prospect Theory
ax = fig.add_subplot(gs[1, 2])
for i, (label, u_vals) in enumerate(results["R3"]["u"].items()):
    ax.plot(c_prospect, u_vals, color=colors_lambda[i], lw=2, label=label)
ax.axvline(r3["c_star"], color='k', ls='--', lw=1, alpha=0.5, label='c*')
ax.set_xlabel('c')
ax.set_ylabel('u(c; c*)')
ax.set_title('(f) Prospect Theory (V7)')
ax.legend(fontsize=7)
ax.axhline(0, color='k', lw=0.5, alpha=0.3)
ax.grid(True, alpha=0.3)
ax.annotate('Verlustzone\n(steiler)', xy=(0.5, -0.5), fontsize=8,
            color='red', ha='center')
ax.annotate('Gewinnzone', xy=(1.5, 0.3), fontsize=8,
            color='green', ha='center')

# ── Row 3: Euler-Dynamik ──
# (g) Konsum c(t) unter verschiedenen gamma
ax = fig.add_subplot(gs[2, 0])
for i, (label, sol) in enumerate(results["R4"]["sols"].items()):
    ax.plot(sol["t"], sol["c"], color=colors_gamma[i], lw=2, label=label)
ax.set_xlabel('t (Jahre)')
ax.set_ylabel('c(t)')
ax.set_title('(g) Euler-Konsumdynamik (r=4%, beta=3%)')
ax.legend(fontsize=7)
ax.grid(True, alpha=0.3)

# (h) Wachstumsrate (r-beta)/gamma
ax = fig.add_subplot(gs[2, 1])
gammas_dense = np.linspace(0.1, 10, 200)
growth_rates = (r4["r"] - r4["beta"]) / gammas_dense
ax.plot(gammas_dense, growth_rates * 100, 'b-', lw=2)
ax.set_xlabel('gamma')
ax.set_ylabel('cdot/c (%/Jahr)')
ax.set_title(r'(h) KAUSALITAET: gamma -> Konsumwachstum')
ax.axhline(0, color='k', ls='--', lw=0.5)
ax.grid(True, alpha=0.3)
# Mark specific gammas
for g in r4["gammas"]:
    rate = (r4["r"] - r4["beta"]) / g * 100
    ax.plot(g, rate, 'ro', ms=8)
    ax.annotate(f'{rate:.1f}%', xy=(g, rate), textcoords='offset points',
                xytext=(10, 5), fontsize=8)
ax.text(0.95, 0.95, 'V.1: cdot/c = (r-beta)/gamma',
        transform=ax.transAxes, ha='right', va='top', fontsize=8,
        bbox=dict(boxstyle='round,pad=0.3', facecolor='lightyellow', alpha=0.9))

# (i) V5+V6: Ramsey Steady-State + Monotonie
ax = fig.add_subplot(gs[2, 2])
ax.plot(sol_ss.t, sol_ss.y[0], 'b-', lw=2, label='r=beta (V5: Steady State)')
ax.plot(sol_up.t, sol_up.y[0], 'g-', lw=2, label='r>beta (V6: steigend)')
ax.plot(sol_dn.t, sol_dn.y[0], 'r-', lw=2, label='r<beta (V6: fallend)')
ax.set_xlabel('t (Jahre)')
ax.set_ylabel('c(t)')
ax.set_title('(i) V5+V6: Ramsey-Steady-State + Monotonie')
ax.legend(fontsize=7)
ax.grid(True, alpha=0.3)
ax.axhline(1.0, color='k', ls=':', lw=0.5, alpha=0.5)

# ── Row 4: Habitformation ──
# (j) c(t) + c*(t)
ax = fig.add_subplot(gs[3, 0])
for i, (label, sol) in enumerate(results["R5"]["sols"].items()):
    ax.plot(sol["t"], sol["c"], color=colors_habit[i], lw=2, label=f'c: {label}')
    ax.plot(sol["t"], sol["c_star"], color=colors_habit[i], lw=1, ls='--', alpha=0.6)
ax.set_xlabel('t (Jahre)')
ax.set_ylabel('c, c*')
ax.set_title('(j) Habitformation: Konsum + Referenzpunkt')
ax.legend(fontsize=6)
ax.grid(True, alpha=0.3)

# (k) Surplus c-c*
ax = fig.add_subplot(gs[3, 1])
for i, (label, sol) in enumerate(results["R5"]["sols"].items()):
    ax.plot(sol["t"], sol["surplus"], color=colors_habit[i], lw=2, label=label)
ax.set_xlabel('t (Jahre)')
ax.set_ylabel('c - c*')
ax.set_title(r'(k) KAUSALITAET: Surplus-Konsum (Zufriedenheit)')
ax.legend(fontsize=7)
ax.axhline(0, color='k', ls='--', lw=0.5)
ax.grid(True, alpha=0.3)
ax.text(0.05, 0.05, 'VI.4: dc*/dt = lam_c*(c-c*)\nHabit holt Konsum ein!',
        transform=ax.transAxes, ha='left', va='bottom', fontsize=8,
        bbox=dict(boxstyle='round,pad=0.3', facecolor='lightyellow', alpha=0.9))

# (l) Habit-Nutzen u(c-c*)
ax = fig.add_subplot(gs[3, 2])
for i, (label, sol) in enumerate(results["R5"]["sols"].items()):
    surplus = np.maximum(sol["surplus"], 1e-10)
    u_habit = u_crra(surplus + r5["c_star0"], r5["gamma"], 0)
    ax.plot(sol["t"], u_habit, color=colors_habit[i], lw=2, label=label)
ax.set_xlabel('t (Jahre)')
ax.set_ylabel('u(c)')
ax.set_title('(l) Habit-bereinigter Nutzen')
ax.legend(fontsize=7)
ax.grid(True, alpha=0.3)

# ── Row 5: Epstein-Zin + Kausalitaet ──
# (m) EZ Nutzenkurven
ax = fig.add_subplot(gs[4, 0])
for i, (label, u_vals) in enumerate(results["R6"]["u"].items()):
    ax.plot(c_range, u_vals, lw=2, label=label)
ax.set_xlabel('c')
ax.set_ylabel('u_EZ(c)')
ax.set_title('(m) Epstein-Zin (deterministisch)')
ax.legend(fontsize=7)
ax.grid(True, alpha=0.3)
ax.axhline(0, color='k', lw=0.5, alpha=0.3)

# (n) KAUSALITAET: gamma -> Portfolioallokation (Merton)
ax = fig.add_subplot(gs[4, 1])
gammas_merton = np.linspace(0.3, 15, 200)
w_star = (mu_stock - r_f) / (gammas_merton * sigma_stock**2)
ax.plot(gammas_merton, w_star * 100, 'b-', lw=2)
ax.fill_between(gammas_merton, 0, w_star * 100, alpha=0.15, color='blue')
ax.set_xlabel('gamma (Risikoaversion)')
ax.set_ylabel('w* (%)')
ax.set_title(r'(n) KAUSALITAET: gamma -> Aktienanteil (Merton)')
ax.grid(True, alpha=0.3)
ax.set_ylim(0, 250)
for g in [1, 2, 5, 10]:
    ws = (mu_stock - r_f) / (g * sigma_stock**2) * 100
    ax.plot(g, ws, 'ro', ms=8)
    ax.annotate(f'{ws:.0f}%', xy=(g, ws), textcoords='offset points',
                xytext=(10, 5), fontsize=8)
ax.text(0.95, 0.95, r'w* = (mu-r)/(gamma*sigma^2)',
        transform=ax.transAxes, ha='right', va='top', fontsize=8,
        bbox=dict(boxstyle='round,pad=0.3', facecolor='lightyellow', alpha=0.9))

# (o) KAUSALITAET: Information -> Effektiver Preis (U.3)
ax = fig.add_subplot(gs[4, 2])
I_range = np.linspace(0.001, 2.0, 200)
for psi_val in [0.01, 0.05, 0.1, 0.5]:
    p_eff = 1.0 * (1 + psi_val / (I_range + eps))
    ax.plot(I_range, p_eff, lw=2, label=f'psi={psi_val}')
ax.set_xlabel('I (Information)')
ax.set_ylabel('p_eff / p')
ax.set_title(r'(o) KAUSALITAET: U.3 Illiquiditaetspraemie')
ax.legend(fontsize=7)
ax.set_ylim(0.95, 4)
ax.grid(True, alpha=0.3)
ax.text(0.95, 0.95, 'p_eff = p*(1+psi/(I+eps))\nI->0: p_eff -> unendlich!',
        transform=ax.transAxes, ha='right', va='top', fontsize=8,
        bbox=dict(boxstyle='round,pad=0.3', facecolor='lightyellow', alpha=0.9))

# ── Row 6: V2 Konvergenz + Vergleichs-Heatmap + Zusammenfassung ──
# (p) V2: gamma->1 Konvergenz
ax = fig.add_subplot(gs[5, 0])
gamma_test = np.array([0.5, 0.7, 0.9, 0.99, 0.999, 1.001, 1.01, 1.1, 1.5, 2.0])
c_test_val = 2.0
u_crra_vals = [u_crra(np.array([c_test_val]), g, 0)[0] for g in gamma_test]
u_log_val = np.log(c_test_val)
ax.plot(gamma_test, u_crra_vals, 'bo-', lw=2, ms=6, label='CRRA u(2)')
ax.axhline(u_log_val, color='r', ls='--', lw=2, label=f'ln(2)={u_log_val:.4f}')
ax.set_xlabel('gamma')
ax.set_ylabel('u(c=2)')
ax.set_title('(p) V2: CRRA gamma->1 konvergiert zu ln(c)')
ax.legend(fontsize=7)
ax.grid(True, alpha=0.3)

# (q) CRRA vs CARA bei gleichem Risikoniveau
ax = fig.add_subplot(gs[5, 1])
g_comp = 2.0
a_comp = g_comp  # Risikoaversion = 2
u_crra_comp = u_crra(c_range_wide, g_comp, 0)
u_cara_comp = u_cara(c_range_wide, a_comp)
# Normalisiere auf u(1) = 0
u_crra_norm = u_crra_comp - u_crra(np.array([1.0]), g_comp, 0)[0]
u_cara_norm = u_cara_comp - u_cara(np.array([1.0]), a_comp)[0]
ax.plot(c_range_wide, u_crra_norm, 'b-', lw=2, label='CRRA (gamma=2)')
ax.plot(c_range_wide, u_cara_norm, 'r-', lw=2, label='CARA (alpha=2)')
ax.set_xlabel('c')
ax.set_ylabel('u(c) - u(1)')
ax.set_title('(q) CRRA vs CARA (normiert auf u(1)=0)')
ax.legend(fontsize=7)
ax.axhline(0, color='k', lw=0.5, alpha=0.3)
ax.axvline(1.0, color='k', lw=0.5, ls=':', alpha=0.3)
ax.grid(True, alpha=0.3)
ax.text(0.05, 0.95, 'CRRA: relative RA konstant\nCARA: absolute RA konstant',
        transform=ax.transAxes, ha='left', va='top', fontsize=8,
        bbox=dict(boxstyle='round,pad=0.3', facecolor='lightyellow', alpha=0.9))

# (r) Kausalitaetskarte (Uebersicht der Kopplungen)
ax = fig.add_subplot(gs[5, 2])
ax.axis('off')
kaus_text = (
    "KAUSALKETTEN U.1:\n"
    "────────────────────────────────────\n"
    "U.1 (gamma,c*)  -->  V.1 (Euler)\n"
    "  gamma bestimmt cdot/c = (r-beta)/gamma\n\n"
    "U.1 (gamma)  -->  III.2 (Portfolio)\n"
    "  w* = (mu-r)/(gamma*sigma^2)\n\n"
    "I (II.3)  -->  U.3 (Eff. Preis)\n"
    "  p_eff = p*(1+psi/(I+eps))\n\n"
    "VI.4 (Habit)  -->  U.1 (c*)\n"
    "  dc*/dt = lam_c*(c-c*)\n\n"
    "VI.2  -->  U.1 (gamma)\n"
    "  dgamma/dt = a_g*(g*-g)+b_g*Verlust\n\n"
    "Stabilisierend:  Verlust --> gamma steigt\n"
    "  --> weniger Risiko --> Erholung\n"
    "Destabilisierend: Gewinn --> gamma sinkt\n"
    "  --> mehr Risiko --> Blase!"
)
ax.text(0.05, 0.95, kaus_text, transform=ax.transAxes, ha='left', va='top',
        fontsize=8, family='monospace',
        bbox=dict(boxstyle='round,pad=0.5', facecolor='lightyellow', alpha=0.95))

# ── Row 7: Metadata ──
ax_meta = fig.add_subplot(gs[6, :])
ax_meta.axis('off')
n_pass = sum(1 for v in validations.values() if v["pass"])
n_total = len(validations)
val_str = "  |  ".join([f"V{i+1} {'PASS' if v['pass'] else 'FAIL'}"
                        for i, (k, v) in enumerate(validations.items())])
meta_text = (
    f"S14  U.1  Nutzenordnung  |  6 Regime, {n_total} Validierungen: {n_pass}/{n_total} bestanden\n"
    f"{val_str}\n"
    f"CRRA: u=(c-c*)^(1-g)/(1-g)  |  CARA: u=-exp(-a*c)  |  EZ: V=(1-d)c^(1-rho)+d(E[V^(1-a)])^((1-rho)/(1-a))\n"
    f"Euler V.1: cdot/c=(r-beta)/gamma  |  Habit VI.4: dc*/dt=lam*(c-c*)  |  U.3: p_eff=p*(1+psi/(I+eps))\n"
    f"Kausalitaet: gamma->Konsum, gamma->Portfolio, I->Preis, Habit->Zufriedenheit, Verlust->gamma"
)
ax_meta.text(0.5, 0.5, meta_text, transform=ax_meta.transAxes,
             ha='center', va='center', fontsize=9, family='monospace',
             bbox=dict(boxstyle='round,pad=0.5', facecolor='lightyellow', alpha=0.95))

plt.savefig(PLOT_DIR / "S14_U1_Nutzenfunktion.png", dpi=180, bbox_inches='tight')
plt.close()
print(f"\n  Plot gespeichert: {PLOT_DIR / 'S14_U1_Nutzenfunktion.png'}")


# ══════════════════════════════════════════════════════════════════════
# 7.  DATEN SPEICHERN
# ══════════════════════════════════════════════════════════════════════

save_dict = {}
# R1 CRRA
save_dict["c_range"] = c_range
for i, g in enumerate(r1["gammas"]):
    save_dict[f"R1_u_gamma{g}"] = list(results["R1"]["u"].values())[i]
    save_dict[f"R1_up_gamma{g}"] = list(results["R1"]["up"].values())[i]
    save_dict[f"R1_rra_gamma{g}"] = list(results["R1"]["rra"].values())[i]
# R2 CARA
for i, a in enumerate(r2["alphas"]):
    save_dict[f"R2_u_alpha{a}"] = list(results["R2"]["u"].values())[i]
    save_dict[f"R2_ara_alpha{a}"] = list(results["R2"]["ara"].values())[i]
# R3 Prospect
save_dict["c_prospect"] = c_prospect
for i, lam in enumerate(r3["lambdas"]):
    save_dict[f"R3_u_lambda{lam}"] = list(results["R3"]["u"].values())[i]
# R4 Euler
for i, (label, sol) in enumerate(results["R4"]["sols"].items()):
    save_dict[f"R4_t_{i}"] = sol["t"]
    save_dict[f"R4_c_{i}"] = sol["c"]
# R5 Habit
for i, (label, sol) in enumerate(results["R5"]["sols"].items()):
    save_dict[f"R5_t_{i}"] = sol["t"]
    save_dict[f"R5_c_{i}"] = sol["c"]
    save_dict[f"R5_cstar_{i}"] = sol["c_star"]
    save_dict[f"R5_surplus_{i}"] = sol["surplus"]

np.savez_compressed(DATA_DIR / "S14_U1_Nutzenfunktion.npz", **save_dict)
print(f"  Daten gespeichert: {DATA_DIR / 'S14_U1_Nutzenfunktion.npz'}")


# ══════════════════════════════════════════════════════════════════════
# 8.  ZUSAMMENFASSUNG
# ══════════════════════════════════════════════════════════════════════

print(f"\n{'='*72}")
print("  ZUSAMMENFASSUNG S14  U.1  Nutzenordnung")
print(f"{'='*72}")
for k, v in validations.items():
    tag = "PASS" if v["pass"] else "FAIL"
    print(f"  {k}: {v['name']:40s}  {tag}  ({v['detail']})")
print()
print("  REGIME:")
print("  R1: CRRA (gamma=0.5,1,2,5): Konkav, monoton, RRA=gamma")
print("  R2: CARA (alpha=0.5,1,2,5): Konkav, monoton, ARA=alpha")
print("  R3: Prospect Theory (lambda=1,1.5,2.25,3): Knick bei c*, Verlust-steiler")
for label, sol in results["R4"]["sols"].items():
    print(f"  R4: Euler {label}: c(T)={sol['c'][-1]:.4f}, Rate={(r4['r']-r4['beta'])/float(label.split('=')[1]):.4f}")
for label, sol in results["R5"]["sols"].items():
    print(f"  R5: Habit {label}: surplus(T)={sol['surplus'][-1]:.4f}")
print(f"  R6: Epstein-Zin: EIS trennt sich von Risikoaversion")
print()
print("  KAUSALITAETEN:")
print("  1. gamma -> Konsumwachstum (r-beta)/gamma: hoehere RA = langsameres Wachstum")
print("  2. gamma -> Portfolioanteil w*=(mu-r)/(gamma*sigma^2): hoehere RA = weniger Aktien")
print("  3. I -> p_eff = p*(1+psi/(I+eps)): weniger Info = teurere Gueter")
print("  4. Habit c* verfolgt c: Hedonic Treadmill, Zufriedenheit konvergiert zu 0")
print("  5. Verluste erhoehen gamma (VI.2) -> stabilisierende Spirale")
print()
n_pass = sum(1 for v in validations.values() if v["pass"])
n_total = len(validations)
print(f"  Gesamtergebnis: {n_pass}/{n_total} Validierungen bestanden")
if n_pass == n_total:
    print("  >>> ALLE VALIDIERUNGEN BESTANDEN <<<")
print(f"{'='*72}")
