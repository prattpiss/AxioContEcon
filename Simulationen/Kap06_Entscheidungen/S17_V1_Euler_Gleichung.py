"""
S17 – Euler-Gleichung V.1: Rationaler Konsum  (§6.3)
=====================================================
Gleichung V.1:
    dc_i/dt = R_i * c_i,   R_i = (r - beta_i) / gamma_i

Sonderfaelle:
    S17a: r = beta  ->  dc/dt = 0  (Ramsey-Steady-State)
    S17b: gamma -> 0  ->  risikoneutral  (explosive Dynamik)
    S17c: gamma -> inf ->  extreme Risikoaversion  (Glattung)

V.1a: Wahrgenommener Zins  r_wahr = r + eta*p - phi/(I+eps)

8 Regime, 8 Validierungen, 5 Sensitivitaetsanalysen
"""

import sys, io, warnings, math
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
warnings.filterwarnings('ignore', category=UserWarning, module='matplotlib')

import numpy as np
from scipy.integrate import solve_ivp
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

# ══════════════════════════════════════════════════════════════════════
# 1. Kernfunktionen
# ══════════════════════════════════════════════════════════════════════

def R_euler(r, beta, gamma):
    """Euler-Wachstumsrate R = (r - beta) / gamma"""
    return (r - beta) / gamma

def c_analytical(t, c0, R):
    """Analytische Loesung c(t) = c0 * exp(R*t)"""
    return c0 * np.exp(R * t)

def r_perceived(r, I, phi=0.5, eps=0.01):
    """Wahrgenommener Zins V.1a: r_wahr = r - phi/(I+eps)"""
    return r - phi / (I + eps)

def wealth_rhs(t, state, r, y, p, beta, gamma, eps_I=0.01, phi=0.0, I_val=np.inf):
    """Gekoppeltes System: dw/dt = r*w + y - p*c,  dc/dt = R*c
       mit optionalem wahrgenommenem Zins"""
    w, c = state
    r_eff = r - phi / (I_val + eps_I) if phi > 0 else r
    R = (r_eff - beta) / gamma
    dwdt = r * w + y - p * max(c, 0)
    dcdt = R * max(c, 1e-15)
    return [dwdt, dcdt]


print("=" * 72)
print("  S17  V.1  Euler-Gleichung: Rationaler Konsum")
print("=" * 72)

results = {}
T = 50.0
t_eval = np.linspace(0, T, 2001)

# ══════════════════════════════════════════════════════════════════════
# R1: Ramsey-Euler Basis — 3 Agentenklassen
# ══════════════════════════════════════════════════════════════════════
print("\n  R1: Ramsey-Euler Basis (3 Klassen)")

r_market = 0.05
agents = {
    "Geduldig (W)":   dict(beta=0.02, gamma=2.0, c0=10.0),
    "Neutral (U)":    dict(beta=0.05, gamma=1.0, c0=10.0),
    "Ungeduldig (B)": dict(beta=0.08, gamma=0.5, c0=10.0),
}

R1_data = {}
for name, ag in agents.items():
    R_val = R_euler(r_market, ag["beta"], ag["gamma"])
    c_t = c_analytical(t_eval, ag["c0"], R_val)
    R1_data[name] = dict(R=R_val, c=c_t, **ag)
    print(f"    {name:20s}: R={R_val:+.4f}, c(T)={c_t[-1]:.2f}")

results["R1"] = dict(label="R1: Ramsey-Euler Basis", data=R1_data)


# ══════════════════════════════════════════════════════════════════════
# R2: Ramsey-Steady-State  r = beta  (S17a)
# ══════════════════════════════════════════════════════════════════════
print("\n  R2: Ramsey-Steady-State (r = beta)")

r_sweep_ss = np.array([0.02, 0.03, 0.04, 0.05, 0.06, 0.07, 0.08])
beta_ss = 0.05
gamma_ss = 1.5
R2_data = {}
for r_val in r_sweep_ss:
    R_val = R_euler(r_val, beta_ss, gamma_ss)
    c_t = c_analytical(t_eval, 10.0, R_val)
    R2_data[r_val] = dict(R=R_val, c=c_t, is_ss=(abs(r_val - beta_ss) < 1e-10))
    tag = " <-- Steady State" if abs(r_val - beta_ss) < 1e-10 else ""
    print(f"    r={r_val:.2f}: R={R_val:+.4f}, c(T)={c_t[-1]:.2f}{tag}")

results["R2"] = dict(label="R2: Steady-State", data=R2_data,
                      r_sweep=r_sweep_ss, beta=beta_ss, gamma=gamma_ss)


# ══════════════════════════════════════════════════════════════════════
# R3: Risikoneutral gamma -> 0  (S17b)
# ══════════════════════════════════════════════════════════════════════
print("\n  R3: Risikoneutral (gamma -> 0)")

gamma_low = [0.05, 0.1, 0.2, 0.5, 1.0, 2.0]
r_rn = 0.05
beta_rn = 0.03
R3_data = {}
for g in gamma_low:
    R_val = R_euler(r_rn, beta_rn, g)
    c_t = c_analytical(t_eval, 10.0, R_val)
    R3_data[g] = dict(R=R_val, c=c_t)
    print(f"    gamma={g:.2f}: R={R_val:+.4f}, c(T)={c_t[-1]:.2e}")

results["R3"] = dict(label="R3: Risikoneutral", data=R3_data, gammas=gamma_low)


# ══════════════════════════════════════════════════════════════════════
# R4: Extreme Risikoaversion gamma -> inf  (S17c)
# ══════════════════════════════════════════════════════════════════════
print("\n  R4: Extreme Risikoaversion (gamma -> inf)")

gamma_high = [1.0, 5.0, 10.0, 25.0, 50.0, 100.0]
R4_data = {}
for g in gamma_high:
    R_val = R_euler(r_rn, beta_rn, g)
    c_t = c_analytical(t_eval, 10.0, R_val)
    R4_data[g] = dict(R=R_val, c=c_t)
    print(f"    gamma={g:6.1f}: R={R_val:+.6f}, c(T)={c_t[-1]:.4f}")

results["R4"] = dict(label="R4: Extreme Risikoaversion", data=R4_data, gammas=gamma_high)


# ══════════════════════════════════════════════════════════════════════
# R5: Wahrgenommener Zins V.1a
# ══════════════════════════════════════════════════════════════════════
print("\n  R5: Wahrgenommener Zins V.1a")

I_levels = [0.1, 0.5, 1.0, 5.0, 20.0, 1e6]
phi_val = 0.5
r_base = 0.05
beta_wahr = 0.03
gamma_wahr = 1.5
R5_data = {}
for I_v in I_levels:
    r_w = r_perceived(r_base, I_v, phi_val)
    R_val = R_euler(r_w, beta_wahr, gamma_wahr)
    c_t = c_analytical(t_eval, 10.0, R_val)
    R5_data[I_v] = dict(r_wahr=r_w, R=R_val, c=c_t)
    label = "EMH" if I_v > 1e5 else f"I={I_v}"
    print(f"    {label:10s}: r_wahr={r_w:+.4f}, R={R_val:+.4f}, c(T)={c_t[-1]:.2f}")

results["R5"] = dict(label="R5: Wahrgenommener Zins", data=R5_data, I_levels=I_levels)


# ══════════════════════════════════════════════════════════════════════
# R6: Gekoppeltes System  w(t) + c(t)
# ══════════════════════════════════════════════════════════════════════
print("\n  R6: Gekoppeltes Vermoegen-Konsum-System")

coupled_agents = {
    "Sparer":     dict(beta=0.02, gamma=2.0, c0=8.0,  w0=100.0, y=5.0, p=1.0),
    "Balanced":   dict(beta=0.04, gamma=1.0, c0=10.0, w0=100.0, y=5.0, p=1.0),
    "Verschwender": dict(beta=0.08, gamma=0.5, c0=15.0, w0=100.0, y=5.0, p=1.0),
}
r_coupled = 0.05

R6_data = {}
for name, ag in coupled_agents.items():
    sol = solve_ivp(lambda t, s: wealth_rhs(t, s, r_coupled, ag["y"], ag["p"],
                    ag["beta"], ag["gamma"]),
                    [0, T], [ag["w0"], ag["c0"]], t_eval=t_eval,
                    method='RK45', rtol=1e-10, atol=1e-12)
    R6_data[name] = dict(t=sol.t, w=sol.y[0], c=sol.y[1], **ag)
    print(f"    {name:15s}: w(T)={sol.y[0][-1]:.1f}, c(T)={sol.y[1][-1]:.2f}")

results["R6"] = dict(label="R6: Gekoppeltes System", data=R6_data)


# ══════════════════════════════════════════════════════════════════════
# R7: Heterogene Agenten (N=200) — Verteilungsdynamik
# ══════════════════════════════════════════════════════════════════════
print("\n  R7: Heterogene Agenten (N=200)")

N_het = 200
beta_het = np.random.lognormal(np.log(0.04), 0.3, N_het)
beta_het = np.clip(beta_het, 0.005, 0.15)
gamma_het = np.random.lognormal(np.log(1.5), 0.5, N_het)
gamma_het = np.clip(gamma_het, 0.1, 20.0)
c0_het = np.random.lognormal(np.log(10.0), 0.3, N_het)

R_het = R_euler(r_market, beta_het, gamma_het)
# c(t) fuer alle Agenten
c_het_t0 = c0_het.copy()
c_het_t25 = c0_het * np.exp(R_het * 25.0)
c_het_T = c0_het * np.exp(R_het * T)

# Gini-Koeffizient
def gini(x):
    x = np.sort(np.abs(x))
    n = len(x)
    if x.sum() == 0:
        return 0
    return (2 * np.sum((np.arange(1, n+1)) * x) - (n + 1) * x.sum()) / (n * x.sum())

gini_0 = gini(c0_het)
gini_25 = gini(np.abs(c_het_t25))
gini_T = gini(np.abs(c_het_T))

R7_data = dict(N=N_het, beta=beta_het, gamma=gamma_het, c0=c0_het, R=R_het,
               c_t0=c_het_t0, c_t25=c_het_t25, c_T=c_het_T,
               gini_0=gini_0, gini_25=gini_25, gini_T=gini_T)
results["R7"] = dict(label="R7: Heterogene Agenten", data=R7_data)
print(f"    N={N_het}, Gini(t=0)={gini_0:.3f}, Gini(t=25)={gini_25:.3f}, Gini(T)={gini_T:.3f}")


# ══════════════════════════════════════════════════════════════════════
# R8: Budgetbeschraenkung + Info-Friction (gekoppelt + V.1a)
# ══════════════════════════════════════════════════════════════════════
print("\n  R8: Budget mit Info-Friction")

I_friction_vals = [0.2, 1.0, 5.0, 50.0]
phi_fr = 0.8
R8_data = {}
for I_fr in I_friction_vals:
    sol = solve_ivp(lambda t, s: wealth_rhs(t, s, r_coupled, 5.0, 1.0,
                    0.04, 1.5, eps_I=0.01, phi=phi_fr, I_val=I_fr),
                    [0, T], [100.0, 10.0], t_eval=t_eval,
                    method='RK45', rtol=1e-10, atol=1e-12)
    r_w = r_perceived(r_coupled, I_fr, phi_fr)
    R8_data[I_fr] = dict(t=sol.t, w=sol.y[0], c=sol.y[1], r_wahr=r_w)
    print(f"    I={I_fr:5.1f}: r_wahr={r_w:+.4f}, w(T)={sol.y[0][-1]:.1f}, c(T)={sol.y[1][-1]:.2f}")

results["R8"] = dict(label="R8: Budget + Info-Friction", data=R8_data)


# ══════════════════════════════════════════════════════════════════════
# VALIDIERUNGEN
# ══════════════════════════════════════════════════════════════════════

validations = {}
print(f"\n{'='*72}\n  VALIDIERUNGEN\n{'='*72}")

# V1: Nullpunkt r=beta => c(t)=c(0)
c_ss = R2_data[0.05]["c"]
v1_err = abs(c_ss[-1] - c_ss[0]) / c_ss[0]
v1_pass = v1_err < 1e-10
validations["V1"] = dict(name="Nullpunkt: r=beta => c=const", passed=v1_pass,
                          detail=f"|c(T)-c(0)|/c(0)={v1_err:.2e}")
print(f"  V1: {'PASS' if v1_pass else 'FAIL'} ({validations['V1']['detail']})")

# V2: Analytische Loesung — numerisch vs exakt
test_r, test_beta, test_gamma, test_c0 = 0.06, 0.03, 1.5, 10.0
R_test = R_euler(test_r, test_beta, test_gamma)
c_exact = c_analytical(t_eval, test_c0, R_test)
# Numerische Loesung via ODE
sol_v2 = solve_ivp(lambda t, y: [R_test * y[0]], [0, T], [test_c0],
                    t_eval=t_eval, method='RK45', rtol=1e-12, atol=1e-14)
c_num = sol_v2.y[0]
v2_err = np.max(np.abs(c_exact - c_num) / c_exact)
v2_pass = v2_err < 1e-6
validations["V2"] = dict(name="Analytisch vs Numerisch", passed=v2_pass,
                          detail=f"max_rel_err={v2_err:.2e}")
print(f"  V2: {'PASS' if v2_pass else 'FAIL'} ({validations['V2']['detail']})")

# V3: Monotonie dR/dr>0, dR/dbeta<0, d|R|/dgamma<0
r_grid = np.linspace(0.01, 0.10, 50)
beta_grid = np.linspace(0.01, 0.08, 50)
gamma_grid = np.linspace(0.2, 10.0, 50)

R_of_r = R_euler(r_grid, 0.04, 1.5)
R_of_beta = R_euler(0.05, beta_grid, 1.5)
R_of_gamma = R_euler(0.06, 0.03, gamma_grid)

mon_r = np.all(np.diff(R_of_r) > 0)           # dR/dr > 0
mon_beta = np.all(np.diff(R_of_beta) < 0)     # dR/dbeta < 0
mon_gamma = np.all(np.diff(np.abs(R_of_gamma)) < 0)  # d|R|/dgamma < 0 (for r>beta)
v3_pass = mon_r and mon_beta and mon_gamma
validations["V3"] = dict(name="Monotonie: dR/dr>0, dR/dbeta<0, d|R|/dgamma<0",
                          passed=v3_pass,
                          detail=f"r:{mon_r}, beta:{mon_beta}, gamma:{mon_gamma}")
print(f"  V3: {'PASS' if v3_pass else 'FAIL'} ({validations['V3']['detail']})")

# V4: Klassenspreizung — geduldiger Agent ueberholt ungeduldigen
c_W = R1_data["Geduldig (W)"]["c"]
c_B = R1_data["Ungeduldig (B)"]["c"]
# Geduldig hat R>0 (r=0.05>beta=0.02), Ungeduldig hat R<0 (r=0.05<beta=0.08)
v4_pass = c_W[-1] > c_W[0] and c_B[-1] < c_B[0] and c_W[-1] > c_B[-1]
validations["V4"] = dict(name="Klassen: Geduldig waechst, Ungeduldig schrumpft",
                          passed=v4_pass,
                          detail=f"c_W(T)={c_W[-1]:.1f}>c_W(0)={c_W[0]:.0f}, "
                                 f"c_B(T)={c_B[-1]:.2f}<c_B(0)={c_B[0]:.0f}")
print(f"  V4: {'PASS' if v4_pass else 'FAIL'} ({validations['V4']['detail']})")

# V5: Risikoneutral explosive Dynamik
c_rn005 = R3_data[0.05]["c"][-1]
c_rn2 = R3_data[2.0]["c"][-1]
v5_pass = c_rn005 > c_rn2 * 10   # gamma=0.05 => R=0.4, viel staerkeres Wachstum
validations["V5"] = dict(name="Risikoneutral: gamma=0.05 >> gamma=2.0",
                          passed=v5_pass,
                          detail=f"c(T,g=0.05)={c_rn005:.0f} >> c(T,g=2)={c_rn2:.1f}")
print(f"  V5: {'PASS' if v5_pass else 'FAIL'} ({validations['V5']['detail']})")

# V6: Extreme Risikoaversion — c fast konstant
c_g100 = R4_data[100.0]["c"]
v6_err = abs(c_g100[-1] - c_g100[0]) / c_g100[0]
v6_pass = v6_err < 0.02  # weniger als 2% Aenderung bei gamma=100
validations["V6"] = dict(name="Risikoavers: gamma=100 => c~const", passed=v6_pass,
                          detail=f"|Dc/c|={v6_err:.4f}")
print(f"  V6: {'PASS' if v6_pass else 'FAIL'} ({validations['V6']['detail']})")

# V7: EMH-Limit — r_wahr -> r bei I -> inf
r_emh = R5_data[1e6]["r_wahr"]
v7_pass = abs(r_emh - r_base) < 1e-6
validations["V7"] = dict(name="EMH: I->inf => r_wahr->r", passed=v7_pass,
                          detail=f"|r_wahr-r|={abs(r_emh-r_base):.2e}")
print(f"  V7: {'PASS' if v7_pass else 'FAIL'} ({validations['V7']['detail']})")

# V8: Ungleichheit waechst (Gini steigt)
v8_pass = gini_T > gini_0
validations["V8"] = dict(name="Gini(T) > Gini(0) (Divergenz)", passed=v8_pass,
                          detail=f"Gini: {gini_0:.3f} -> {gini_T:.3f}")
print(f"  V8: {'PASS' if v8_pass else 'FAIL'} ({validations['V8']['detail']})")


# ══════════════════════════════════════════════════════════════════════
# SENSITIVITAETSANALYSEN
# ══════════════════════════════════════════════════════════════════════

print(f"\n{'='*72}\n  SENSITIVITAETSANALYSEN\n{'='*72}")

# SA1: gamma-Sweep fuer Wachstumsrate R
gamma_sa1 = np.array([0.1, 0.2, 0.5, 1.0, 2.0, 5.0, 10.0, 50.0])
R_sa1 = R_euler(0.05, 0.03, gamma_sa1)
results["SA1"] = dict(gamma=gamma_sa1, R=R_sa1)
print(f"  SA1: R(gamma=0.1)={R_sa1[0]:+.3f}, R(gamma=50)={R_sa1[-1]:+.6f}")

# SA2: beta-Sweep
beta_sa2 = np.linspace(0.0, 0.10, 100)
R_sa2 = R_euler(0.05, beta_sa2, 1.5)
results["SA2"] = dict(beta=beta_sa2, R=R_sa2)
print(f"  SA2: R(beta=0)={R_sa2[0]:+.4f}, R(beta=0.10)={R_sa2[-1]:+.4f}")

# SA3: r-Sweep inkl. negative Zinsen
r_sa3 = np.linspace(-0.03, 0.12, 100)
R_sa3 = R_euler(r_sa3, 0.04, 1.5)
results["SA3"] = dict(r=r_sa3, R=R_sa3)
print(f"  SA3: R(r=-0.03)={R_sa3[0]:+.4f}, R(r=0.12)={R_sa3[-1]:+.4f}")

# SA4: Information I -> Konsum-Endwert
I_sa4 = np.logspace(-2, 3, 200)
r_wahr_sa4 = r_perceived(0.05, I_sa4, 0.5)
R_sa4 = R_euler(r_wahr_sa4, 0.03, 1.5)
c_T_sa4 = 10.0 * np.exp(R_sa4 * T)
results["SA4"] = dict(I=I_sa4, r_wahr=r_wahr_sa4, R=R_sa4, c_T=c_T_sa4)
print(f"  SA4: c(T, I=0.01)={c_T_sa4[0]:.2e}, c(T, I=1000)={c_T_sa4[-1]:.2f}")

# SA5: 2D-Heatmap (gamma, r) -> R
gamma_2d = np.linspace(0.2, 8.0, 50)
r_2d = np.linspace(-0.02, 0.10, 50)
G2d, R2d = np.meshgrid(gamma_2d, r_2d)
R_heatmap = R_euler(R2d, 0.04, G2d)
results["SA5"] = dict(gamma=gamma_2d, r=r_2d, R_heatmap=R_heatmap)
print(f"  SA5: 50x50 Heatmap (gamma, r) -> R: min={R_heatmap.min():+.4f}, max={R_heatmap.max():+.4f}")


# ══════════════════════════════════════════════════════════════════════
# PLOT (27 Panels)
# ══════════════════════════════════════════════════════════════════════

print(f"\n  PLOTTE ...")
fig = plt.figure(figsize=(26, 44))
gs = GridSpec(10, 3, figure=fig, height_ratios=[1, 1, 1, 1, 1, 1, 1, 1, 1, 0.35],
              hspace=0.38, wspace=0.30)
fig.suptitle('S17  V.1  Euler-Gleichung: Rationaler Konsum',
             fontsize=15, fontweight='bold', y=0.995)

# ── Row 1: R1 Basis ──
ax = fig.add_subplot(gs[0, 0])
for name, d in R1_data.items():
    ax.plot(t_eval, d["c"], lw=2, label=name)
ax.set_xlabel('t'); ax.set_ylabel('c(t)')
ax.set_title('(a) R1: Ramsey-Euler 3 Klassen')
ax.legend(fontsize=7); ax.grid(True, alpha=0.3)

ax = fig.add_subplot(gs[0, 1])
names_R1 = list(R1_data.keys())
Rs_R1 = [R1_data[n]["R"] for n in names_R1]
colors_R1 = ['C0', 'C1', 'C2']
bars = ax.bar(range(len(names_R1)), Rs_R1, color=colors_R1, alpha=0.7)
ax.axhline(0, color='black', lw=0.5)
ax.set_xticks(range(len(names_R1)))
ax.set_xticklabels(names_R1, fontsize=7, rotation=15)
ax.set_ylabel('R = (r-beta)/gamma'); ax.set_title('(b) R1: Wachstumsrate R')
ax.grid(True, alpha=0.3, axis='y')

# R1: Konsum-Ratio
ax = fig.add_subplot(gs[0, 2])
c_ratio = R1_data["Geduldig (W)"]["c"] / R1_data["Ungeduldig (B)"]["c"]
ax.plot(t_eval, c_ratio, 'C3-', lw=2)
ax.set_xlabel('t'); ax.set_ylabel('c_W / c_B')
ax.set_title('(c) R1: Konsum-Ratio W/B (V4)')
ax.grid(True, alpha=0.3)

# ── Row 2: R2 Steady-State ──
ax = fig.add_subplot(gs[1, 0])
for r_val, d in R2_data.items():
    lw = 3 if d["is_ss"] else 1.5
    ls = '--' if d["is_ss"] else '-'
    ax.plot(t_eval, d["c"], lw=lw, ls=ls, label=f'r={r_val:.2f}')
ax.set_xlabel('t'); ax.set_ylabel('c(t)')
ax.set_title('(d) R2: Steady-State r=beta=0.05 (V1)')
ax.legend(fontsize=6, ncol=2); ax.grid(True, alpha=0.3)

# R2: R vs r
ax = fig.add_subplot(gs[1, 1])
R_vals_r2 = [R2_data[r]["R"] for r in r_sweep_ss]
ax.plot(r_sweep_ss, R_vals_r2, 'C0-o', lw=2)
ax.axhline(0, color='red', ls=':', lw=0.8, label='R=0 (SS)')
ax.axvline(beta_ss, color='gray', ls=':', lw=0.8, label=f'beta={beta_ss}')
ax.set_xlabel('r'); ax.set_ylabel('R')
ax.set_title('(e) R2: R(r) bei beta=0.05')
ax.legend(fontsize=7); ax.grid(True, alpha=0.3)

# ── Row 2: R3 Risikoneutral ──
ax = fig.add_subplot(gs[1, 2])
for g in gamma_low:
    c_vals = R3_data[g]["c"]
    ax.semilogy(t_eval, c_vals, lw=2, label=f'gamma={g}')
ax.set_xlabel('t'); ax.set_ylabel('c(t) [log]')
ax.set_title('(f) R3: Risikoneutral gamma->0 (V5)')
ax.legend(fontsize=6); ax.grid(True, alpha=0.3)

# ── Row 3: R4 + R5 ──
ax = fig.add_subplot(gs[2, 0])
for g in gamma_high:
    ax.plot(t_eval, R4_data[g]["c"], lw=2, label=f'gamma={g}')
ax.set_xlabel('t'); ax.set_ylabel('c(t)')
ax.set_title('(g) R4: Risikoaversion gamma->inf (V6)')
ax.legend(fontsize=6); ax.grid(True, alpha=0.3)

ax = fig.add_subplot(gs[2, 1])
for I_v in I_levels:
    d = R5_data[I_v]
    label = "EMH" if I_v > 1e5 else f"I={I_v}"
    ax.plot(t_eval, d["c"], lw=2, label=label)
ax.set_xlabel('t'); ax.set_ylabel('c(t)')
ax.set_title('(h) R5: Wahrgen. Zins V.1a (V7)')
ax.legend(fontsize=6); ax.grid(True, alpha=0.3)

ax = fig.add_subplot(gs[2, 2])
I_plot = [x for x in I_levels if x < 1e5]
r_wahrs = [R5_data[I_v]["r_wahr"] for I_v in I_plot]
ax.semilogx(I_plot, r_wahrs, 'C0-o', lw=2)
ax.axhline(r_base, color='red', ls=':', lw=0.8, label=f'r_true={r_base}')
ax.set_xlabel('I (log)'); ax.set_ylabel('r_wahr')
ax.set_title('(i) R5: r_wahr(I) -> r (EMH)')
ax.legend(fontsize=7); ax.grid(True, alpha=0.3)

# ── Row 4: R6 Gekoppelt ──
ax = fig.add_subplot(gs[3, 0])
for name, d in R6_data.items():
    ax.plot(d["t"], d["c"], lw=2, label=name)
ax.set_xlabel('t'); ax.set_ylabel('c(t)')
ax.set_title('(j) R6: Gekoppeltes System — Konsum')
ax.legend(fontsize=7); ax.grid(True, alpha=0.3)

ax = fig.add_subplot(gs[3, 1])
for name, d in R6_data.items():
    ax.plot(d["t"], d["w"], lw=2, label=name)
ax.set_xlabel('t'); ax.set_ylabel('w(t)')
ax.set_title('(k) R6: Gekoppelt — Vermoegen')
ax.legend(fontsize=7); ax.grid(True, alpha=0.3)

ax = fig.add_subplot(gs[3, 2])
for name, d in R6_data.items():
    dwdt = np.gradient(d["w"], d["t"])
    ax.plot(d["t"], dwdt, lw=2, label=name)
ax.axhline(0, color='black', lw=0.5)
ax.set_xlabel('t'); ax.set_ylabel('dw/dt')
ax.set_title('(l) R6: Sparrate dw/dt')
ax.legend(fontsize=7); ax.grid(True, alpha=0.3)

# ── Row 5: R7 Heterogen ──
ax = fig.add_subplot(gs[4, 0])
sc = ax.scatter(beta_het, gamma_het, c=R_het, cmap='RdYlGn', s=15, alpha=0.7)
plt.colorbar(sc, ax=ax, label='R')
ax.set_xlabel('beta'); ax.set_ylabel('gamma')
ax.set_title('(m) R7: Agenten im (beta,gamma)-Raum')

ax = fig.add_subplot(gs[4, 1])
ax.hist(c_het_t0, bins=30, alpha=0.5, label='t=0', density=True)
ax.hist(np.clip(c_het_T, 0, np.percentile(np.abs(c_het_T), 95)), bins=30, alpha=0.5, label='t=T', density=True)
ax.set_xlabel('c'); ax.set_ylabel('Dichte')
ax.set_title('(n) R7: Konsumverteilung t=0 vs t=T (V8)')
ax.legend(fontsize=7); ax.grid(True, alpha=0.3)

ax = fig.add_subplot(gs[4, 2])
t_gini = np.linspace(0, T, 50)
ginis = [gini(np.abs(c0_het * np.exp(R_het * t))) for t in t_gini]
ax.plot(t_gini, ginis, 'C3-', lw=2)
ax.axhline(gini_0, ls=':', color='gray', lw=0.8, label=f'Gini(0)={gini_0:.3f}')
ax.set_xlabel('t'); ax.set_ylabel('Gini')
ax.set_title('(o) R7: Gini(t) — Ungleichheitsdynamik')
ax.legend(fontsize=7); ax.grid(True, alpha=0.3)

# ── Row 6: R8 Budget+Friction ──
ax = fig.add_subplot(gs[5, 0])
for I_fr, d in R8_data.items():
    ax.plot(d["t"], d["c"], lw=2, label=f'I={I_fr}')
ax.set_xlabel('t'); ax.set_ylabel('c(t)')
ax.set_title('(p) R8: Konsum mit Info-Friction')
ax.legend(fontsize=7); ax.grid(True, alpha=0.3)

ax = fig.add_subplot(gs[5, 1])
for I_fr, d in R8_data.items():
    ax.plot(d["t"], d["w"], lw=2, label=f'I={I_fr}')
ax.set_xlabel('t'); ax.set_ylabel('w(t)')
ax.set_title('(q) R8: Vermoegen mit Info-Friction')
ax.legend(fontsize=7); ax.grid(True, alpha=0.3)

ax = fig.add_subplot(gs[5, 2])
I_fr_list = sorted(R8_data.keys())
cT_fr = [R8_data[I_fr]["c"][-1] for I_fr in I_fr_list]
ax.semilogx(I_fr_list, cT_fr, 'C0-o', lw=2)
ax.set_xlabel('I (Info)'); ax.set_ylabel('c(T)')
ax.set_title('(r) R8: Endkonsum vs Information')
ax.grid(True, alpha=0.3)

# ── Row 7: SA1-SA3 ──
ax = fig.add_subplot(gs[6, 0])
ax.semilogx(gamma_sa1, R_sa1, 'C0-o', lw=2, markersize=5)
ax.axhline(0, color='red', ls=':', lw=0.8)
ax.set_xlabel('gamma (log)'); ax.set_ylabel('R')
ax.set_title('(s) SA1: R(gamma) bei r=0.05, beta=0.03')
ax.grid(True, alpha=0.3)

ax = fig.add_subplot(gs[6, 1])
ax.plot(beta_sa2, R_sa2, 'C1-', lw=2)
ax.axhline(0, color='red', ls=':', lw=0.8)
ax.axvline(0.05, color='gray', ls=':', lw=0.8, label='beta=r')
ax.set_xlabel('beta'); ax.set_ylabel('R')
ax.set_title('(t) SA2: R(beta) bei r=0.05')
ax.legend(fontsize=7); ax.grid(True, alpha=0.3)

ax = fig.add_subplot(gs[6, 2])
ax.plot(r_sa3, R_sa3, 'C2-', lw=2)
ax.axhline(0, color='red', ls=':', lw=0.8)
ax.axvline(0.04, color='gray', ls=':', lw=0.8, label='r=beta')
ax.fill_between(r_sa3, R_sa3, 0, where=R_sa3 > 0, alpha=0.15, color='green')
ax.fill_between(r_sa3, R_sa3, 0, where=R_sa3 < 0, alpha=0.15, color='red')
ax.set_xlabel('r'); ax.set_ylabel('R')
ax.set_title('(u) SA3: R(r) inkl. negative Zinsen')
ax.legend(fontsize=7); ax.grid(True, alpha=0.3)

# ── Row 8: SA4-SA5 + Kausalitaet ──
ax = fig.add_subplot(gs[7, 0])
ax.semilogx(I_sa4, c_T_sa4, 'C0-', lw=2)
ax.set_xlabel('I (log)'); ax.set_ylabel('c(T)')
ax.set_title('(v) SA4: c(T) vs Information I')
ax.grid(True, alpha=0.3)

ax = fig.add_subplot(gs[7, 1])
im = ax.imshow(R_heatmap, extent=[gamma_2d[0], gamma_2d[-1], r_2d[0], r_2d[-1]],
               aspect='auto', origin='lower', cmap='RdYlGn')
ax.contour(gamma_2d, r_2d, R_heatmap, levels=[0], colors='black', linewidths=2)
plt.colorbar(im, ax=ax, label='R')
ax.set_xlabel('gamma'); ax.set_ylabel('r')
ax.set_title('(w) SA5: 2D-Heatmap R(gamma, r)')

ax = fig.add_subplot(gs[7, 2])
ax.axis('off')
kaus_text = (
    "KAUSALKETTEN (S17 V.1):\n"
    "────────────────────────\n"
    "1. r > beta => R > 0 => c waechst\n"
    "   -> Geduld wird belohnt\n"
    "   -> Vermoegensdivergenz\n\n"
    "2. r = beta => R = 0 => Steady State\n"
    "   -> Ramsey-Goldene Regel\n\n"
    "3. gamma -> 0 => |R| -> inf\n"
    "   -> Explosive Dynamik\n"
    "   -> Risikoneutral\n\n"
    "4. gamma -> inf => R -> 0\n"
    "   -> Perfekte Glattung\n"
    "   -> Keine Reaktion auf r-beta\n\n"
    "5. I -> 0 => r_wahr << r\n"
    "   -> Info-Arme unterschaetzen\n"
    "     Zinsen -> Unterkonsum\n\n"
    "6. Heterogenitaet (beta,gamma)\n"
    "   -> Gini waechst ueber Zeit\n"
    "   -> Endogene Ungleichheit"
)
ax.text(0.05, 0.95, kaus_text, transform=ax.transAxes, ha='left', va='top',
        fontsize=8, family='monospace',
        bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.95))

# ── Row 9: Validierung + Analytik ──
ax = fig.add_subplot(gs[8, 0])
ax.axis('off')
val_text = "VALIDIERUNGEN:\n" + "-"*35 + "\n"
for k, v in validations.items():
    tag = "PASS" if v["passed"] else "FAIL"
    val_text += f"{k}: {v['name'][:35]}\n   {tag}: {v['detail']}\n\n"
ax.text(0.05, 0.95, val_text, transform=ax.transAxes, ha='left', va='top',
        fontsize=6.5, family='monospace',
        bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.95))

ax = fig.add_subplot(gs[8, 1])
# V2 visuell: Analytisch vs Numerisch
ax.plot(t_eval, c_exact, 'C0-', lw=2, label='Analytisch')
ax.plot(t_eval[::50], c_num[::50], 'C1x', markersize=6, label='Numerisch')
ax.set_xlabel('t'); ax.set_ylabel('c(t)')
ax.set_title('(x) V2: Analytisch vs Numerisch')
ax.legend(fontsize=7); ax.grid(True, alpha=0.3)

ax = fig.add_subplot(gs[8, 2])
# V3 visuell: Monotonie
ax.plot(r_grid, R_of_r, 'C0-', lw=2, label='R(r)')
ax.plot(beta_grid, R_of_beta, 'C1-', lw=2, label='R(beta)')
ax.plot(gamma_grid, R_of_gamma, 'C2-', lw=2, label='R(gamma)')
ax.axhline(0, color='black', lw=0.5)
ax.set_xlabel('Parameter'); ax.set_ylabel('R')
ax.set_title('(y) V3: Monotonie-Check')
ax.legend(fontsize=7); ax.grid(True, alpha=0.3)

# ── Metadata ──
ax_meta = fig.add_subplot(gs[9, :])
ax_meta.axis('off')
n_pass = sum(1 for v in validations.values() if v["passed"])
meta = (
    f"S17 V.1 Euler-Gleichung | 8 Regime, {len(validations)} Val: "
    f"{n_pass}/{len(validations)} PASS | "
    f"Ramsey-Euler, Steady-State, Risikoneutral, Risikoavers, V.1a, Gekoppelt, "
    f"Heterogen (N={N_het}), Budget+Friction | "
    f"5 SA inkl. 50x50 Heatmap | dc/dt = [(r-beta)/gamma]*c"
)
ax_meta.text(0.5, 0.5, meta, transform=ax_meta.transAxes, ha='center', va='center',
             fontsize=9, family='monospace',
             bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.95))

plt.savefig(PLOT_DIR / "S17_V1_Euler_Gleichung.png", dpi=180, bbox_inches='tight')
plt.close()
print(f"\n  Plot: {PLOT_DIR / 'S17_V1_Euler_Gleichung.png'}")

# ── Daten ──
save_dict = {
    "t_eval": t_eval,
    "R7_beta": beta_het, "R7_gamma": gamma_het, "R7_c0": c0_het, "R7_R": R_het,
    "SA1_gamma": gamma_sa1, "SA1_R": R_sa1,
    "SA2_beta": beta_sa2, "SA2_R": R_sa2,
    "SA3_r": r_sa3, "SA3_R": R_sa3,
    "SA4_I": I_sa4, "SA4_cT": c_T_sa4,
    "SA5_gamma": gamma_2d, "SA5_r": r_2d, "SA5_R_heatmap": R_heatmap,
}
for name, d in R1_data.items():
    safe = name.replace(" ", "_").replace("(", "").replace(")", "")
    save_dict[f"R1_c_{safe}"] = d["c"]
for name, d in R6_data.items():
    safe = name.replace(" ", "_")
    save_dict[f"R6_w_{safe}"] = d["w"]
    save_dict[f"R6_c_{safe}"] = d["c"]
np.savez_compressed(DATA_DIR / "S17_V1_Euler_Gleichung.npz", **save_dict)

# ── Zusammenfassung ──
print(f"\n{'='*72}\n  ZUSAMMENFASSUNG S17  V.1 Euler-Gleichung\n{'='*72}")
for k, v in validations.items():
    print(f"  {k}: {v['name']:45s}  {'PASS' if v['passed'] else 'FAIL'}  ({v['detail']})")
print(f"\n  Regime:")
for key in ["R1", "R2", "R3", "R4", "R5", "R6", "R7", "R8"]:
    print(f"    {results[key]['label']}")
print(f"\n  Sensitivitaet:")
print(f"    SA1: R(gamma)")
print(f"    SA2: R(beta)")
print(f"    SA3: R(r) inkl. negative Zinsen")
print(f"    SA4: c(T) vs Information I")
print(f"    SA5: 50x50 Heatmap R(gamma, r)")
n_pass = sum(1 for v in validations.values() if v["passed"])
print(f"\n  Gesamtergebnis: {n_pass}/{len(validations)} bestanden")
if n_pass == len(validations):
    print("  >>> ALLE VALIDIERUNGEN BESTANDEN <<<")
print(f"{'='*72}")
