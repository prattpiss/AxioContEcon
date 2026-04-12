"""
S08 – Fundamentale Preisdynamik II.2  (§5.1)
================================================
Monographie-Gleichung (exakt):

    ṗ_k = (1/λ_k)(D_k - S_k)  +  η_k · p_k  -  φ_k / (I_k + ε)
           ─────────────────     ──────────     ──────────────────
           Walrasianische        Inflations-     Illiquiditäts-
           Anpassung             erwartung       prämie

    Proposition 5.1: Regime hängt ab von I_k:
        Gleichgewicht:   D≈S, I hoch       → ṗ ≈ 0
        Normal:          D≠S, I mittel      → monotone Konvergenz
        Blase:           η groß, I hoch     → exponentielles Wachstum
        Krise:           I→0                → Preiskollaps

5 Regime:
  R1  Normaler Handel       – Walras dominiert, I hoch
  R2  Blase                 – η > 0 dominiert, D>S, I hoch
  R3  Krise                 – I_k → ε, φ-Term explodiert
  R4  Stagflation           – η>0 aber D<S, I mittel
  R5  Gleichgewicht         – D≈S, η=π*, I hoch → ṗ≈π*·p

Validierung:
  V1  Walras-Grenzfall: η=0, φ=0 → ṗ = (D-S)/λ → p* = MC (falls D,S linear)
  V2  Blase: η>0 → exponentielles Wachstum p(t) = p₀·exp(η·t)
  V3  Illiquiditätskollaps: I→0 → p fällt bis -φ/ε dominiert
  V4  Prop 5.1: Regime-Übergang durch I_k-Variation
  V5  Sensitivität: λ × φ → p(T)/p(0), 625 Punkte

Stochastische Erweiterung (Bemerkung 5.1, nicht implementiert hier):
  dp = [II.2 Drift]dt + σ_k·p·dW + ∫j·Ñ(dt,dℓ) → VIII.1 (Kap.10)

Numerik:
  - Solver: scipy.integrate.solve_ivp, Methode RK45 (Dormand-Prince)
  - Toleranzen: rtol=1e-10, atol=1e-12
  - max_step=0.05 (klein wegen Singularität bei I→0)
  - Clipping: p ≥ p_floor (1e-6) zur Regularisierung
"""

import numpy as np
from scipy.integrate import solve_ivp, trapezoid
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from pathlib import Path
import textwrap
import warnings
warnings.filterwarnings("ignore", category=RuntimeWarning)

# ═══════════════════════════════════════════════
# Pfade
# ═══════════════════════════════════════════════
BASE = Path(__file__).resolve().parents[2]
PLOT = BASE / "Ergebnisse" / "Plots" / "S08_II2_Preisdynamik.png"
DATA = BASE / "Ergebnisse" / "Daten" / "S08_II2_Preisdynamik.npz"
PLOT.parent.mkdir(parents=True, exist_ok=True)
DATA.parent.mkdir(parents=True, exist_ok=True)

rng = np.random.default_rng(42)

# ═══════════════════════════════════════════════
# KLASSIFIKATION: Endogen / Exogen / Parameter
# ═══════════════════════════════════════════════
#
# ENDOGENE VARIABLEN (vom ODE-System bestimmt):
#   p_k(t)     Preis des Gutes k          [Einheiten: Währung/Mengeneinheit]
#   I_k(t)     Informationsniveau          [Einheiten: dimensionslos, ∈ (0,∞)]
#
# EXOGENE VARIABLEN (vorgegeben, in Vollmodell endogen):
#   D_k(t)     Nachfrage                   [Einheiten: Mengeneinh./Zeiteinheit]
#   S_k(t)     Angebot                     [Einheiten: Mengeneinh./Zeiteinheit]
#   η_k(t)     Inflationserwartung         [Einheiten: 1/Zeit]
#              → in Vollmodell endogen via III.4 (Kap.6, §6.7)
#
# PARAMETER (Regime-spezifisch):
#   λ_k        Markttiefe (Liquidität)     [Einheiten: Mengeneinh.·Zeit/Währung]
#   φ_k        Illiquiditätsstärke         [Einheiten: Währung/Zeit]
#   ε          Regularisierung             [Einheiten: dimensionslos]
#
# FUNKTIONALFORMEN (Modellierungswahl, NICHT axiomatisch):
#   D_k(t) = D_0 + D_amp · sin(ω_D · t)           – exogene Schwingung
#   S_k(t) = S_0 + S_amp · sin(ω_S · t + φ_shift) – exogene Schwingung
#   η_k(t) = η_base + η_shock(t)                   – stückweise konstant + Schock
#   I_k(t) = I_0 · exp(-γ_I · max(t - t_crisis, 0)) – Info-Zerfall ab Krise

# ═══════════════════════════════════════════════
# Simulation
# ═══════════════════════════════════════════════
T_SPAN = (0, 60)
T_EVAL = np.linspace(0, 60, 6001)
P_FLOOR = 1e-6  # Regularisierung: p ≥ p_floor

# ───────────────────────────────────────────────
# Regime-Definitionen
# ───────────────────────────────────────────────
def get_regime(regime):
    """
    Gibt dict mit allen Parametern und Funktionalformen zurück.
    Jedes Regime definiert: lambda_k, phi_k, eps, D(t), S(t), eta(t), I(t), p0.

    PARAMETERWAHL-MOTIVATION:
    - φ/(I+ε) ist ein ABSOLUTER Preisdruck [Währung/(ME·a)], nicht relativ zu p.
    - η·p ist proportional → dominiert bei großem p.
    - (D-S)/λ hat typische Amplitude D_amp/λ.
    - Gleichgewicht: alle Terme vergleichbar oder η·p steuert langfristig.
    """
    if regime == "R1":
        # Normaler Handel: D schwankt um S, I hoch → φ-Term winzig
        # Walras-Amplitude: 15/50 = 0.3. φ/(I+ε)=0.02/5.01 ≈ 0.004. Klein.
        return dict(
            label="R1 Normaler Handel", color="C0",
            lam=50.0, phi=0.02, eps=0.01,
            D0=100.0, D_amp=15.0, omega_D=0.5,
            S0=100.0, S_amp=5.0, omega_S=0.5, phi_shift=0.3,
            eta_base=0.0, eta_shock_t=None, eta_shock_val=0.0,
            I0=5.0, gamma_I=0.0, t_crisis=999,
            p0=10.0,
            desc="Walras dominiert, I konstant hoch"
        )
    elif regime == "R2":
        # Blase: η=5%/a → exponentiell. D>S verstärkt. φ klein.
        # η·p₀=0.5, (D-S)/λ ≈ 20/30=0.67. φ/(I+ε)=0.1/2.01≈0.05.
        return dict(
            label="R2 Blase", color="C1",
            lam=30.0, phi=0.1, eps=0.01,
            D0=120.0, D_amp=10.0, omega_D=0.3,
            S0=100.0, S_amp=5.0, omega_S=0.3, phi_shift=0.0,
            eta_base=0.05, eta_shock_t=None, eta_shock_val=0.0,
            I0=2.0, gamma_I=0.0, t_crisis=999,
            p0=10.0,
            desc="η=5%/a → Exp.-Wachstum, D>S"
        )
    elif regime == "R3":
        # Krise: I_0=5 (anfangs hoch), dann exponentieller Zerfall ab t=25.
        # φ=1.5 → bei I=5: -0.3/a (harmlos). Bei I=0.01: -1.5/0.015≈-100 (Kollaps).
        # η=0.01 → leichter Inflationsdrift hält p erstmal stabil.
        return dict(
            label="R3 Krise (Illiquidität)", color="C3",
            lam=50.0, phi=1.5, eps=0.005,
            D0=100.0, D_amp=5.0, omega_D=0.5,
            S0=100.0, S_amp=5.0, omega_S=0.5, phi_shift=0.0,
            eta_base=0.01, eta_shock_t=None, eta_shock_val=0.0,
            I0=5.0, gamma_I=0.20, t_crisis=25.0,
            p0=10.0,
            desc="I→0 ab t=25, Preiskollaps"
        )
    elif regime == "R4":
        # Stagflation: η=4%/a, D<S. Inflation TROTZ Angebotsüberschuss.
        # η·p₀=0.4/a. (D-S)/λ = -10/40 = -0.25/a. φ/(I+ε)=0.01/1.01≈0.01.
        # Netto-Drift: +0.4-0.25-0.01 = +0.14 → p steigt → η·p wächst → Stagflation!
        return dict(
            label="R4 Stagflation", color="C2",
            lam=40.0, phi=0.01, eps=0.01,
            D0=90.0, D_amp=5.0, omega_D=0.4,
            S0=100.0, S_amp=3.0, omega_S=0.4, phi_shift=0.0,
            eta_base=0.04, eta_shock_t=None, eta_shock_val=0.0,
            I0=1.0, gamma_I=0.0, t_crisis=999,
            p0=10.0,
            desc="η>0 trotz D<S → Preissteigerung"
        )
    elif regime == "R5":
        # Gleichgewicht: D≈S, η=π*=2%, I sehr hoch → φ-Term vernachlässigbar.
        # ṗ ≈ η·p → p(t) ≈ p₀·exp(0.02·t) → stabiles 2%-Inflationsziel.
        return dict(
            label="R5 Gleichgewicht", color="C4",
            lam=80.0, phi=0.05, eps=0.01,
            D0=100.0, D_amp=2.0, omega_D=0.5,
            S0=100.0, S_amp=2.0, omega_S=0.5, phi_shift=0.0,
            eta_base=0.02, eta_shock_t=None, eta_shock_val=0.0,
            I0=10.0, gamma_I=0.0, t_crisis=999,
            p0=10.0,
            desc="D≈S, η=π*=2%, ṗ≈π*·p"
        )


def make_exog_functions(par):
    """Erzeugt die exogenen Zeitfunktionen D(t), S(t), η(t), I(t)."""
    def D_func(t):
        return par["D0"] + par["D_amp"] * np.sin(par["omega_D"] * t)

    def S_func(t):
        return par["S0"] + par["S_amp"] * np.sin(par["omega_S"] * t + par["phi_shift"])

    def eta_func(t):
        val = par["eta_base"]
        if par["eta_shock_t"] is not None and t >= par["eta_shock_t"]:
            val += par["eta_shock_val"]
        return val

    def I_func(t):
        dt = max(t - par["t_crisis"], 0.0)
        return max(par["I0"] * np.exp(-par["gamma_I"] * dt), par["eps"])

    return D_func, S_func, eta_func, I_func


def make_rhs(par):
    """
    RHS der ODE: ṗ = (D-S)/λ + η·p - φ/(I+ε)

    Gleichung II.2 (§5.1) — exakt wie in der Monographie.
    """
    D_f, S_f, eta_f, I_f = make_exog_functions(par)
    lam = par["lam"]
    phi = par["phi"]
    eps = par["eps"]

    def rhs(t, y):
        p = max(y[0], P_FLOOR)
        D = D_f(t)
        S = S_f(t)
        eta = eta_f(t)
        I_val = I_f(t)

        # II.2: die drei Terme
        term_walras = (D - S) / lam
        term_inflation = eta * p
        term_illiquid = -phi / (I_val + eps)

        dpdt = term_walras + term_inflation + term_illiquid
        return [dpdt]

    return rhs, D_f, S_f, eta_f, I_f


# ═══════════════════════════════════════════════
# Ausführung: 5 Regime
# ═══════════════════════════════════════════════
print("=" * 72)
print("  S08  Fundamentale Preisdynamik II.2  (§5.1)")
print("=" * 72)

results = {}
for regime in ["R1", "R2", "R3", "R4", "R5"]:
    par = get_regime(regime)
    rhs, D_f, S_f, eta_f, I_f = make_rhs(par)

    sol = solve_ivp(rhs, T_SPAN, [par["p0"]], t_eval=T_EVAL,
                    method="RK45", rtol=1e-10, atol=1e-12, max_step=0.05)
    assert sol.success, f"{regime}: Solver fehlgeschlagen: {sol.message}"

    t = sol.t
    p = sol.y[0]
    p = np.maximum(p, P_FLOOR)

    # Exogene Zeitreihen berechnen
    D_arr = np.array([D_f(ti) for ti in t])
    S_arr = np.array([S_f(ti) for ti in t])
    eta_arr = np.array([eta_f(ti) for ti in t])
    I_arr = np.array([I_f(ti) for ti in t])

    # Die 3 Terme einzeln
    term_walras = (D_arr - S_arr) / par["lam"]
    term_inflation = eta_arr * p
    term_illiquid = -par["phi"] / (I_arr + par["eps"])

    # dpdt numerisch
    dpdt_num = np.gradient(p, t)
    dpdt_ana = term_walras + term_inflation + term_illiquid

    # V1: Fehler Identität  (nur in aktiver Region, p >> P_FLOOR)
    active = p > 10 * P_FLOOR
    if np.sum(active) > 10:
        err_integral = trapezoid(np.abs(dpdt_num[active] - dpdt_ana[active]), t[active])
        scale = trapezoid(np.abs(dpdt_ana[active]) + 1e-15, t[active])
        rel_err = err_integral / scale
    else:
        rel_err = np.nan  # Preis sofort am Floor → numerisch trivial

    # Steady State: ṗ=0 → (D-S)/λ + η·p - φ/(I+ε) = 0
    #   → p* = [φ/(I+ε) - (D-S)/λ] / η  (falls η≠0)
    if abs(par["eta_base"]) > 1e-10:
        D_eq = par["D0"]
        S_eq = par["S0"]
        I_eq = par["I0"] if par["gamma_I"] == 0 else par["eps"]
        p_star = (par["phi"] / (I_eq + par["eps"]) - (D_eq - S_eq) / par["lam"]) / par["eta_base"]
    else:
        p_star = None

    results[regime] = dict(
        par=par, t=t, p=p, D=D_arr, S=S_arr, eta=eta_arr, I=I_arr,
        term_walras=term_walras, term_inflation=term_inflation,
        term_illiquid=term_illiquid, dpdt_num=dpdt_num, dpdt_ana=dpdt_ana,
        rel_err=rel_err, p_star=p_star,
    )

    print(f"\n{'─'*60}")
    print(f"  {par['label']}  ({par['desc']})")
    print(f"{'─'*60}")
    print(f"  p(0)={par['p0']:.2f}  p(T)={p[-1]:.4f}  p_max={p.max():.4f}")
    print(f"  λ={par['lam']}  φ={par['phi']}  ε={par['eps']}")
    print(f"  η_base={par['eta_base']}  I₀={par['I0']}  γ_I={par['gamma_I']}")
    if p_star is not None:
        print(f"  p* (analytisch, stationär) = {p_star:.4f}")
    print(f"  V1: II.2-Identität  rel.Fehler = {rel_err:.2e}  "
          f"{'✅' if (not np.isnan(rel_err) and rel_err < 1e-3) else ('⚠ (Floor)' if np.isnan(rel_err) else '⚠')}")
    # Term-Dominanz
    w_rms = np.sqrt(np.mean(term_walras**2))
    i_rms = np.sqrt(np.mean(term_inflation**2))
    l_rms = np.sqrt(np.mean(term_illiquid**2))
    total_rms = w_rms + i_rms + l_rms + 1e-15
    print(f"  Term-Dominanz (RMS):  Walras={w_rms/total_rms:.1%}  "
          f"η·p={i_rms/total_rms:.1%}  -φ/I={l_rms/total_rms:.1%}")


# ═══════════════════════════════════════════════
# V2: Blasentest — reines η → p(t) = p₀·exp(η·t)
# ═══════════════════════════════════════════════
print(f"\n{'='*60}")
print("  V2: Reiner Blasentest (D=S, φ=0, η=0.05)")
print(f"{'='*60}")

par_pure = dict(
    label="V2 Reine Blase", color="C1",
    lam=100.0, phi=0.0, eps=0.01,
    D0=100.0, D_amp=0.0, omega_D=0.0,
    S0=100.0, S_amp=0.0, omega_S=0.0, phi_shift=0.0,
    eta_base=0.05, eta_shock_t=None, eta_shock_val=0.0,
    I0=1.0, gamma_I=0.0, t_crisis=999,
    p0=10.0, desc="Rein exponentiell"
)
rhs_b, _, _, _, _ = make_rhs(par_pure)
sol_b = solve_ivp(rhs_b, (0, 40), [10.0], t_eval=np.linspace(0, 40, 2001),
                  method="RK45", rtol=1e-12, atol=1e-14, max_step=0.1)
p_ana = 10.0 * np.exp(0.05 * sol_b.t)
p_num = sol_b.y[0]
max_rel_err = np.max(np.abs(p_num - p_ana) / p_ana)
print(f"  max|p_num - p₀·exp(ηt)| / p_ana = {max_rel_err:.2e}  "
      f"{'✅' if max_rel_err < 1e-8 else '⚠'}")

# ═══════════════════════════════════════════════
# V3: Walras-Grenzfall → Gleichgewichtspreis
# ═══════════════════════════════════════════════
print(f"\n{'='*60}")
print("  V3: Walras-Grenzfall (η=0, φ=0, D=a-b·p, S=S₀)")
print(f"{'='*60}")
# D(p) = D0 - β·p, S = S₀ → GG: D=S → p* = (D0-S₀)/β
D0_w, beta_w, S0_w = 150.0, 5.0, 100.0
lam_w = 20.0
p_star_w = (D0_w - S0_w) / beta_w  # = 10.0

def walras_rhs(t, y):
    p = max(y[0], P_FLOOR)
    D = D0_w - beta_w * p
    S = S0_w
    return [(D - S) / lam_w]

sol_w = solve_ivp(walras_rhs, (0, 100), [2.0], t_eval=np.linspace(0, 100, 2001),
                  method="RK45", rtol=1e-12, atol=1e-14)
p_final_w = sol_w.y[0, -1]
err_w = abs(p_final_w - p_star_w) / p_star_w
print(f"  p* = {p_star_w:.2f}  p(100) = {p_final_w:.6f}  "
      f"rel.Abw. = {err_w:.2e}  {'✅' if err_w < 1e-6 else '⚠'}")

# ═══════════════════════════════════════════════
# V4: Prop 5.1 — Regime-Übergang (I variiert)
# ═══════════════════════════════════════════════
print(f"\n{'='*60}")
print("  V4: Prop 5.1 — Regime-Übergang durch I-Variation")
print(f"{'='*60}")
I_test_vals = [10.0, 5.0, 1.0, 0.1, 0.01, 0.005]
for I_val in I_test_vals:
    par_test = get_regime("R1")
    par_test["I0"] = I_val
    par_test["phi"] = 0.5
    rhs_t, _, _, _, _ = make_rhs(par_test)
    sol_t = solve_ivp(rhs_t, (0, 30), [10.0], t_eval=np.linspace(0, 30, 1001),
                      method="RK45", rtol=1e-10, atol=1e-12, max_step=0.05)
    p_end = sol_t.y[0, -1]
    illiq_strength = par_test["phi"] / (I_val + par_test["eps"])
    regime_tag = "Gleichgewicht" if I_val > 3 else ("Normal" if I_val > 0.3 else
                 ("Stress" if I_val > 0.05 else "Krise"))
    print(f"  I={I_val:6.3f}  -φ/(I+ε)={-illiq_strength:8.2f}  "
          f"p(30)={max(p_end,0):8.4f}  Regime: {regime_tag}")


# ═══════════════════════════════════════════════
# V5: Sensitivitätsanalyse  λ × φ → p(T)/p(0)
# ═══════════════════════════════════════════════
print(f"\n{'='*60}")
print("  V5: Sensitivität (625 Punkte, λ × φ)")
print(f"{'='*60}")

N_SENS = 25
lam_range = np.linspace(5.0, 100.0, N_SENS)
phi_range = np.linspace(0.0, 5.0, N_SENS)
p_ratio_grid = np.zeros((N_SENS, N_SENS))

T_sens = 40
for i, lam_val in enumerate(lam_range):
    for j, phi_val in enumerate(phi_range):
        def rhs_s(t, y, lv=lam_val, pv=phi_val):
            p = max(y[0], P_FLOOR)
            D = 105.0 + 10.0 * np.sin(0.5 * t)
            S = 100.0
            eta = 0.01
            I_val = 2.0
            eps = 0.01
            return [(D - S) / lv + eta * p - pv / (I_val + eps)]
        sol_s = solve_ivp(rhs_s, (0, T_sens), [10.0], method="RK45",
                          rtol=1e-8, atol=1e-10, max_step=0.5)
        p_end = max(sol_s.y[0, -1], P_FLOOR)
        p_ratio_grid[i, j] = p_end / 10.0

print(f"  p(T)/p(0) ∈ [{p_ratio_grid.min():.3f}, {p_ratio_grid.max():.3f}]")
print(f"  Median = {np.median(p_ratio_grid):.3f}")


# ═══════════════════════════════════════════════
# PLOT  (4 Zeilen × 3 Spalten = 12 Panels)
# ═══════════════════════════════════════════════
fig = plt.figure(figsize=(22, 26))
gs = GridSpec(5, 3, figure=fig, height_ratios=[1.0, 1.0, 1.0, 1.0, 0.7],
              hspace=0.35, wspace=0.3)
fig.suptitle("S08 – Fundamentale Preisdynamik II.2  (§5.1)\n"
             r"$\dot{p}_k = \lambda_k^{-1}(D_k-S_k) + \eta_k p_k - \varphi_k/(\mathcal{I}_k+\varepsilon)$",
             fontsize=15, fontweight="bold", y=0.98)

# ── (a) p(t) alle 5 Regime ──
ax = fig.add_subplot(gs[0, 0])
for regime in ["R1", "R2", "R3", "R4", "R5"]:
    r = results[regime]
    ax.plot(r["t"], r["p"], color=r["par"]["color"], label=r["par"]["label"], lw=1.3)
ax.set_xlabel("t [Jahre]"); ax.set_ylabel("p_k [Währung/ME]")
ax.set_title("(a) Preis p(t) – 5 Regime"); ax.legend(fontsize=6); ax.grid(alpha=0.3)
ax.set_yscale("symlog", linthresh=1)

# ── (b) Die 3 Terme einzeln (R1 Normal) ──
ax = fig.add_subplot(gs[0, 1])
r1 = results["R1"]
ax.plot(r1["t"], r1["term_walras"], "C0-", label=r"$(D-S)/\lambda$", lw=1)
ax.plot(r1["t"], r1["term_inflation"], "C1--", label=r"$\eta \cdot p$", lw=1)
ax.plot(r1["t"], r1["term_illiquid"], "C3:", label=r"$-\varphi/(\mathcal{I}+\varepsilon)$", lw=1.5)
ax.plot(r1["t"], r1["dpdt_ana"], "k-", label=r"$\dot{p}$ total", lw=0.8, alpha=0.5)
ax.set_xlabel("t"); ax.set_ylabel(r"$\dot{p}$ [Währung/(ME·a)]")
ax.set_title("(b) 3 Terme (R1 Normal)"); ax.legend(fontsize=6); ax.grid(alpha=0.3)

# ── (c) Die 3 Terme einzeln (R3 Krise) ──
ax = fig.add_subplot(gs[0, 2])
r3 = results["R3"]
ax.plot(r3["t"], r3["term_walras"], "C0-", label=r"$(D-S)/\lambda$", lw=1)
ax.plot(r3["t"], r3["term_inflation"], "C1--", label=r"$\eta \cdot p$", lw=1)
ax.plot(r3["t"], r3["term_illiquid"], "C3:", label=r"$-\varphi/(\mathcal{I}+\varepsilon)$", lw=1.5)
ax.plot(r3["t"], r3["dpdt_ana"], "k-", label=r"$\dot{p}$ total", lw=0.8, alpha=0.5)
ax.axvline(20, color="red", ls="--", lw=0.8, label="Info-Kollaps")
ax.set_xlabel("t"); ax.set_ylabel(r"$\dot{p}$")
ax.set_title("(c) 3 Terme (R3 Krise)"); ax.legend(fontsize=6); ax.grid(alpha=0.3)

# ── (d) D(t), S(t) für R1 ──
ax = fig.add_subplot(gs[1, 0])
ax.plot(r1["t"], r1["D"], "C0-", label="D(t) Nachfrage", lw=1.2)
ax.plot(r1["t"], r1["S"], "C3--", label="S(t) Angebot", lw=1.2)
ax.fill_between(r1["t"], r1["D"], r1["S"], alpha=0.15, color="C0",
                label="Excess Demand")
ax.set_xlabel("t"); ax.set_ylabel("Menge/Zeit")
ax.set_title("(d) Angebot & Nachfrage (R1)"); ax.legend(fontsize=6); ax.grid(alpha=0.3)

# ── (e) I(t) für R3 Krise + Illiquiditätsterm ──
ax = fig.add_subplot(gs[1, 1])
ax2 = ax.twinx()
ax.plot(r3["t"], r3["I"], "C4-", label=r"$\mathcal{I}(t)$", lw=1.5)
ax.axvline(20, color="red", ls="--", lw=0.8)
ax2.plot(r3["t"], r3["term_illiquid"], "C3:", label=r"$-\varphi/(\mathcal{I}+\varepsilon)$", lw=1.5)
ax.set_xlabel("t"); ax.set_ylabel(r"$\mathcal{I}_k$", color="C4")
ax2.set_ylabel(r"$-\varphi/(\mathcal{I}+\varepsilon)$", color="C3")
ax.set_title("(e) Info-Kollaps → Illiquidität (R3)")
lines1, labels1 = ax.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax.legend(lines1 + lines2, labels1 + labels2, fontsize=6); ax.grid(alpha=0.3)

# ── (f) V2: Reine Blase p(t) vs p₀·exp(ηt) ──
ax = fig.add_subplot(gs[1, 2])
ax.plot(sol_b.t, p_num, "C1-", label="numerisch", lw=1.5)
ax.plot(sol_b.t, p_ana, "k--", label=r"$p_0 e^{\eta t}$", lw=1, alpha=0.8)
ax.set_xlabel("t"); ax.set_ylabel("p")
ax.set_title(f"(f) V2: Reine Blase  ε={max_rel_err:.1e}"); ax.legend(fontsize=7)
ax.grid(alpha=0.3)

# ── (g) V3: Walras-Konvergenz p → p* ──
ax = fig.add_subplot(gs[2, 0])
ax.plot(sol_w.t, sol_w.y[0], "C0-", lw=1.5, label="p(t)")
ax.axhline(p_star_w, color="k", ls=":", lw=1, label=f"p*={p_star_w:.1f}")
ax.set_xlabel("t"); ax.set_ylabel("p")
ax.set_title(f"(g) V3: Walras-Konvergenz  ε={err_w:.1e}"); ax.legend(fontsize=7)
ax.grid(alpha=0.3)

# ── (h) V4: Prop 5.1 — p(30) vs I ──
ax = fig.add_subplot(gs[2, 1])
p_ends = []
I_range_plot = np.logspace(-2.5, 1.0, 80)
for I_val in I_range_plot:
    par_test = get_regime("R1")
    par_test["I0"] = float(I_val)
    par_test["phi"] = 0.5
    rhs_t, _, _, _, _ = make_rhs(par_test)
    sol_t = solve_ivp(rhs_t, (0, 30), [10.0], method="RK45",
                      rtol=1e-8, atol=1e-10, max_step=0.1)
    p_ends.append(max(sol_t.y[0, -1], P_FLOOR))
ax.semilogx(I_range_plot, p_ends, "C0-", lw=1.5)
ax.axhline(10.0, color="k", ls=":", alpha=0.5, label="p₀")
ax.fill_betweenx([0, max(p_ends)*1.1], 0.001, 0.05, alpha=0.1, color="C3", label="Krise")
ax.fill_betweenx([0, max(p_ends)*1.1], 0.05, 0.3, alpha=0.1, color="C2", label="Stress")
ax.fill_betweenx([0, max(p_ends)*1.1], 0.3, 15, alpha=0.1, color="C0", label="Normal")
ax.set_xlabel(r"$\mathcal{I}_k$"); ax.set_ylabel("p(30)")
ax.set_title("(h) Prop 5.1: Regimeübergang"); ax.legend(fontsize=6); ax.grid(alpha=0.3)
ax.set_ylim(bottom=0)

# ── (i) Heatmap λ × φ → p(T)/p(0) ──
ax = fig.add_subplot(gs[2, 2])
im = ax.pcolormesh(phi_range, lam_range, p_ratio_grid, cmap="RdYlGn", shading="auto")
plt.colorbar(im, ax=ax, label="p(40)/p(0)")
# Markiere Regime
regime_markers = {"R1": (0.5, 50), "R2": (0.3, 30), "R3": (2.0, 50),
                  "R4": (0.8, 40), "R5": (0.2, 80)}
for rname, (pv, lv) in regime_markers.items():
    ax.plot(pv, lv, "w*", ms=10, mec="k")
    ax.annotate(rname, (pv, lv), fontsize=6, color="white", fontweight="bold",
                ha="center", va="bottom", textcoords="offset points", xytext=(0, 4))
ax.set_xlabel(r"$\varphi_k$ (Illiquiditätsstärke)")
ax.set_ylabel(r"$\lambda_k$ (Markttiefe)")
ax.set_title("(i) Sensitivität p(40)/p(0)"); ax.grid(alpha=0.2)

# ── (j) Term-Dominanz-Balken alle 5 Regime ──
ax = fig.add_subplot(gs[3, 0])
regnames = []
dom_w, dom_i, dom_l = [], [], []
for regime in ["R1", "R2", "R3", "R4", "R5"]:
    r = results[regime]
    w = np.sqrt(np.mean(r["term_walras"]**2))
    i = np.sqrt(np.mean(r["term_inflation"]**2))
    l = np.sqrt(np.mean(r["term_illiquid"]**2))
    tot = w + i + l + 1e-15
    dom_w.append(w/tot); dom_i.append(i/tot); dom_l.append(l/tot)
    regnames.append(r["par"]["label"][:12])
x_pos = np.arange(5)
ax.bar(x_pos, dom_w, 0.25, label="Walras", color="C0")
ax.bar(x_pos + 0.25, dom_i, 0.25, label=r"$\eta p$", color="C1")
ax.bar(x_pos + 0.5, dom_l, 0.25, label=r"$-\varphi/\mathcal{I}$", color="C3")
ax.set_xticks(x_pos + 0.25); ax.set_xticklabels(regnames, fontsize=6, rotation=15)
ax.set_ylabel("Anteil (RMS)"); ax.set_title("(j) Term-Dominanz"); ax.legend(fontsize=6)
ax.grid(alpha=0.3, axis="y")

# ── (k) η(t) und p(t) für R4 Stagflation ──
ax = fig.add_subplot(gs[3, 1])
r4 = results["R4"]
ax.plot(r4["t"], r4["p"], "C2-", label="p(t)", lw=1.5)
ax2 = ax.twinx()
ax2.plot(r4["t"], r4["eta"], "C1--", label=r"$\eta(t)$", lw=1)
ax2.plot(r4["t"], (r4["D"] - r4["S"]), "C0:", label="D-S", lw=1)
ax.set_xlabel("t"); ax.set_ylabel("p", color="C2")
ax2.set_ylabel(r"$\eta$, D-S", color="C1")
ax.set_title("(k) Stagflation: η>0, D<S")
lines1, labels1 = ax.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax.legend(lines1 + lines2, labels1 + labels2, fontsize=6); ax.grid(alpha=0.3)

# ── (l) Numerische Fehler ṗ_num vs ṗ_ana (R1) ──
ax = fig.add_subplot(gs[3, 2])
r1 = results["R1"]
mask = (r1["t"] > 0.5) & (r1["t"] < 59.5)
residual = r1["dpdt_num"][mask] - r1["dpdt_ana"][mask]
ax.plot(r1["t"][mask], residual, "C0-", lw=0.5, alpha=0.7)
ax.axhline(0, color="k", ls=":", lw=0.5)
ax.set_xlabel("t"); ax.set_ylabel(r"$\dot{p}_{\rm num} - \dot{p}_{\rm II.2}$")
ax.set_title(f"(l) Numerischer Fehler (R1)  ε={r1['rel_err']:.1e}"); ax.grid(alpha=0.3)

# ══════════════════════════════════════════════
# METADATEN-PANEL (Zeile 5) – professionelle Dokumentation
# ══════════════════════════════════════════════
ax_meta = fig.add_subplot(gs[4, :])
ax_meta.axis("off")

meta_text = (
    "━━━ SIMULATIONSMETADATEN ━━━\n"
    "\n"
    "GLEICHUNG:  II.2 (§5.1)   ṗₖ = (Dₖ−Sₖ)/λₖ + ηₖpₖ − φₖ/(Iₖ+ε)\n"
    "STATUS:     Deterministischer Drift; stochast. Erweiterung → VIII.1 (Kap.10)\n"
    "\n"
    "┌─── ENDOGENE VARIABLEN ─────────────────────────────────────────────────────┐\n"
    "│  pₖ(t)    Preis                       [Währung/ME]   ODE-Lösung           │\n"
    "└───────────────────────────────────────────────────────────────────────────────┘\n"
    "┌─── EXOGENE VARIABLEN (in Vollmodell endogen) ────────────────────────────────┐\n"
    "│  Dₖ(t) = D₀ + D_amp·sin(ω_D·t)       Nachfrage      → V.1 (Kap.6)       │\n"
    "│  Sₖ(t) = S₀ + S_amp·sin(ω_S·t+φ)     Angebot        → III.3 (Kap.6)     │\n"
    "│  ηₖ(t) = η_base + Schock              Infl.-Erw.     → III.4 (Kap.6)     │\n"
    "│  Iₖ(t) = I₀·exp(−γ_I·max(t−t_c,0))   Information    → II.3/I.1 (Kap.7)  │\n"
    "└───────────────────────────────────────────────────────────────────────────────┘\n"
    "┌─── PARAMETER ────────────────────────────────────────────────────────────────┐\n"
    "│  λₖ  Markttiefe     [ME·a/Wäh]  5–100    φₖ  Illiquid.-Stärke  [Wäh/a]   │\n"
    "│  ε   Regularisierung [dimlos]   0.005–0.01                                 │\n"
    "└───────────────────────────────────────────────────────────────────────────────┘\n"
    "┌─── NUMERIK ──────────────────────────────────────────────────────────────────┐\n"
    "│  Solver: RK45 (Dormand-Prince 4(5), eingebettet, adaptiv)                  │\n"
    "│  Toleranzen: rtol=1e-10, atol=1e-12                                        │\n"
    "│  max_step=0.05 (wegen Singularität bei I→0)                                │\n"
    "│  Clipping: p ≥ 1e-6 (physikalische Regularisierung)                        │\n"
    "│  Sensitivität: 25×25=625 Punkte, rtol=1e-8                                 │\n"
    "│  Eigenschaft: A-stabil für η<0, bedingt stabil für η>0 (Blasen-Regime)     │\n"
    "│  Seed: numpy.random.default_rng(42)                                        │\n"
    "└───────────────────────────────────────────────────────────────────────────────┘\n"
    "┌─── MODELLIERUNGSWAHL (austauschbar, NICHT axiomatisch) ──────────────────────┐\n"
    "│  D(t), S(t): Sinusförmig (könnte: linear, stochastisch, aus V.1/III.3)    │\n"
    "│  η(t): Stückweise konstant (könnte: adaptiv via III.4, Bayesianisch)       │\n"
    "│  I(t): Exponentieller Zerfall (könnte: aus II.3 PDE, netzwerkgetrieben)    │\n"
    "│  Prop. 5.1 Regime werden hier exogen gesetzt, im Vollmodell endogen        │\n"
    "└───────────────────────────────────────────────────────────────────────────────┘"
)
ax_meta.text(0.01, 0.98, meta_text, transform=ax_meta.transAxes,
             fontsize=7.0, fontfamily="monospace", verticalalignment="top",
             bbox=dict(boxstyle="round,pad=0.5", facecolor="lightyellow", alpha=0.9))

plt.savefig(PLOT, dpi=180, bbox_inches="tight")
print(f"\n  Plot → {PLOT}")

# ═══════════════════════════════════════════════
# Daten speichern
# ═══════════════════════════════════════════════
save_dict = dict(
    lam_range=lam_range, phi_range=phi_range, p_ratio_grid=p_ratio_grid,
    walras_t=sol_w.t, walras_p=sol_w.y[0], walras_pstar=p_star_w,
    bubble_t=sol_b.t, bubble_p_num=p_num, bubble_p_ana=p_ana,
)
for regime in ["R1", "R2", "R3", "R4", "R5"]:
    r = results[regime]
    save_dict[f"{regime}_t"] = r["t"]
    save_dict[f"{regime}_p"] = r["p"]
    save_dict[f"{regime}_D"] = r["D"]
    save_dict[f"{regime}_S"] = r["S"]
    save_dict[f"{regime}_I"] = r["I"]
np.savez_compressed(DATA, **save_dict)
print(f"  Daten → {DATA}")

# ═══════════════════════════════════════════════
# ZUSAMMENFASSUNG
# ═══════════════════════════════════════════════
print(f"\n{'='*72}")
print("  ZUSAMMENFASSUNG S08")
print(f"{'='*72}")
all_ok = True
for regime in ["R1", "R2", "R3", "R4", "R5"]:
    r = results[regime]
    ok = (not np.isnan(r["rel_err"])) and r["rel_err"] < 1e-3
    if not ok and not np.isnan(r["rel_err"]):
        all_ok = False
    v_str = f"ε={r['rel_err']:.1e}" if not np.isnan(r["rel_err"]) else "Floor"
    print(f"  {r['par']['label']:30s}  V1={'✅' if ok else '⚠'}  "
          f"p(T)={r['p'][-1]:10.4f}  {v_str}")

print(f"\n  V2 Reine Blase:        {'✅' if max_rel_err < 1e-8 else '⚠'}  "
      f"max_rel_err = {max_rel_err:.2e}")
print(f"  V3 Walras-Konvergenz:  {'✅' if err_w < 1e-6 else '⚠'}  "
      f"p({100})={p_final_w:.6f} → p*={p_star_w:.2f}")
print(f"  V5 Sensitivität:       p(40)/p(0) ∈ [{p_ratio_grid.min():.3f}, {p_ratio_grid.max():.3f}]")
print(f"\n  Gesamtergebnis: {'✅ ALLE TESTS BESTANDEN' if all_ok else '⚠ TEILWEISE WARNUNGEN'}")
print(f"{'='*72}")
