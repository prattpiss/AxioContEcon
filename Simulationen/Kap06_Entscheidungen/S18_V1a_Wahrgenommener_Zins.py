"""
S18 – Wahrgenommener Zins V.1a  (§6.3)
=======================================
Gleichung V.1a:
    r_i^wahr = r + eta_i * pi - phi_i / (I_i + eps)

Drei Komponenten:
  1. Nominalzins r (Markt)
  2. Inflationserwartung eta_i * pi
  3. Informationsfriction -phi_i / (I_i + eps)

S17 behandelte V.1a nur als Teilregime (R5, R8).
S18 Deep-Dive: Fisher-Effekt, heterogene Agenten, Bias-Analyse,
Info-Kaskaden, Monetary Policy Transmission, Realzins-Illusion.

8 Regime, 8 Validierungen, 5 Sensitivitaetsanalysen
"""

import sys, io, warnings, math
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
warnings.filterwarnings('ignore', category=UserWarning, module='matplotlib')

import numpy as np
from scipy.integrate import solve_ivp
from scipy.stats import norm
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

def r_perceived(r, eta, pi, phi, I, eps=0.01):
    """V.1a: r_wahr = r + eta*pi - phi/(I+eps)"""
    return r + eta * pi - phi / (np.maximum(I, 0.0) + eps)

def r_real_fisher(r_nom, pi):
    """Fisher-Gleichung: r_real = r_nom - pi"""
    return r_nom - pi

def r_real_perceived(r, eta, pi, phi, I, eps=0.01):
    """Wahrgenommener Realzins: r_wahr - pi = r - pi*(1-eta) - phi/(I+eps)"""
    return r - pi * (1 - eta) - phi / (np.maximum(I, 0.0) + eps)

def euler_consumption(t, c, R):
    """dc/dt = R*c"""
    return R * max(c, 1e-15)

def coupled_rhs(t, state, r, pi, eta, phi, I_val, beta, gamma, y, p, eps=0.01):
    """Gekoppeltes System: dw/dt = r*w + y - p*c, dc/dt = R_wahr*c"""
    w, c = state
    r_w = r_perceived(r, eta, pi, phi, I_val, eps)
    R = (r_w - beta) / gamma
    dwdt = r * w + y - p * max(c, 0)
    dcdt = R * max(c, 1e-15)
    return [dwdt, dcdt]


print("=" * 72)
print("  S18  V.1a  Wahrgenommener Zins")
print("=" * 72)

results = {}
T = 50.0
t_eval = np.linspace(0, T, 2001)

# ══════════════════════════════════════════════════════════════════════
# R1: Fisher-Effekt — Inflationserwartungen
# ══════════════════════════════════════════════════════════════════════
print("\n  R1: Fisher-Effekt")

r_nom = 0.06
pi_vals = np.array([-0.02, 0.0, 0.02, 0.04, 0.06, 0.08, 0.10])
eta_vals = [0.0, 0.5, 1.0]  # Keine, halbe, volle Anpassung

R1_data = {}
for eta in eta_vals:
    for pi in pi_vals:
        r_w = r_perceived(r_nom, eta, pi, 0.0, 1e6)  # Kein Info-Friction
        r_real = r_w - pi
        key = (eta, pi)
        R1_data[key] = dict(r_wahr=r_w, r_real=r_real)
    # Fisher: bei eta=1 => r_wahr = r + pi, r_real_wahr = r (konstant)
    r_reals = [R1_data[(eta, p)]["r_real"] for p in pi_vals]
    spread = max(r_reals) - min(r_reals)
    print(f"    eta={eta:.1f}: r_real spread={spread:.4f} "
          f"({'Fisher-neutral' if spread < 0.001 else 'Geldillusion'})")

results["R1"] = dict(label="R1: Fisher-Effekt", data=R1_data,
                      pi_vals=pi_vals, eta_vals=eta_vals)


# ══════════════════════════════════════════════════════════════════════
# R2: Informationsfriction-Sweep
# ══════════════════════════════════════════════════════════════════════
print("\n  R2: Informationsfriction-Sweep")

I_sweep = np.logspace(-2, 3, 300)
phi_vals = [0.1, 0.3, 0.5, 1.0, 2.0]
r_base = 0.05
pi_base = 0.02
eta_base = 0.8

R2_data = {}
for phi in phi_vals:
    r_w = r_perceived(r_base, eta_base, pi_base, phi, I_sweep)
    bias = r_w - (r_base + eta_base * pi_base)  # Abweichung vom friktionslosen Wert
    R2_data[phi] = dict(r_wahr=r_w, bias=bias)
    # Kritisches I wo bias < -1% (signifikant)
    idx_crit = np.where(np.abs(bias) > 0.01)[0]
    I_crit = I_sweep[idx_crit[-1]] if len(idx_crit) > 0 else 0
    print(f"    phi={phi:.1f}: I_crit(|bias|>1%)={I_crit:.2f}, bias(I=0.1)={bias[np.argmin(np.abs(I_sweep-0.1))]:.4f}")

results["R2"] = dict(label="R2: Info-Friction Sweep", data=R2_data,
                      I_sweep=I_sweep, phi_vals=phi_vals)


# ══════════════════════════════════════════════════════════════════════
# R3: Heterogene Agenten (N=300)
# ══════════════════════════════════════════════════════════════════════
print("\n  R3: Heterogene Agenten (N=300)")

N_het = 300
eta_het = np.random.beta(3, 2, N_het)  # Inflation-Bewusstsein ∈ [0,1]
phi_het = np.random.lognormal(np.log(0.3), 0.5, N_het)
phi_het = np.clip(phi_het, 0.01, 3.0)
I_het = np.random.lognormal(np.log(2.0), 1.0, N_het)
I_het = np.clip(I_het, 0.05, 100.0)
beta_het = np.random.uniform(0.02, 0.06, N_het)
gamma_het = np.random.lognormal(np.log(1.5), 0.4, N_het)
gamma_het = np.clip(gamma_het, 0.3, 10.0)

r_market = 0.05
pi_market = 0.03

r_wahr_het = r_perceived(r_market, eta_het, pi_market, phi_het, I_het)
R_het = (r_wahr_het - beta_het) / gamma_het
c0_het = np.random.lognormal(np.log(10.0), 0.3, N_het)
c_T_het = c0_het * np.exp(R_het * T)

# Gini
def gini(x):
    x = np.sort(np.abs(x))
    n = len(x)
    if x.sum() == 0:
        return 0
    return (2 * np.sum(np.arange(1, n+1) * x) - (n + 1) * x.sum()) / (n * x.sum())

gini_0 = gini(c0_het)
gini_T = gini(np.abs(c_T_het))

# Bias-Verteilung
r_true = r_market + 0.8 * pi_market  # Referenz mit eta=0.8, phi=0
bias_het = r_wahr_het - r_true

R3_data = dict(N=N_het, eta=eta_het, phi=phi_het, I=I_het,
               r_wahr=r_wahr_het, R=R_het, c0=c0_het, c_T=c_T_het,
               bias=bias_het, gini_0=gini_0, gini_T=gini_T,
               beta=beta_het, gamma=gamma_het)
results["R3"] = dict(label="R3: Heterogene Agenten", data=R3_data)
print(f"    N={N_het}, mean_bias={np.mean(bias_het):+.4f}, std_bias={np.std(bias_het):.4f}")
print(f"    Gini(0)={gini_0:.3f}, Gini(T)={gini_T:.3f}")


# ══════════════════════════════════════════════════════════════════════
# R4: Geldillusion — eta < 1
# ══════════════════════════════════════════════════════════════════════
print("\n  R4: Geldillusion (eta < 1)")

eta_illusion = np.linspace(0, 1, 200)
pi_ill = 0.05  # 5% Inflation
r_nom_ill = 0.07

# Wahrgenommener Realzins = r_wahr - pi = r + eta*pi - pi = r - (1-eta)*pi
r_real_perc = r_nom_ill + eta_illusion * pi_ill - pi_ill  # = r + (eta-1)*pi
r_real_true = r_nom_ill - pi_ill  # = 0.02

# Konsum-Endwert basierend auf wahrgenommenem Realzins
beta_ill = 0.03
gamma_ill = 1.5
R_ill = (r_nom_ill + eta_illusion * pi_ill - beta_ill) / gamma_ill
c_T_ill = 10 * np.exp(R_ill * T)

R4_data = dict(eta=eta_illusion, r_real_perc=r_real_perc, r_real_true=r_real_true,
               R=R_ill, c_T=c_T_ill)
results["R4"] = dict(label="R4: Geldillusion", data=R4_data)
print(f"    eta=0: r_real_perc={r_real_perc[0]:+.4f} (Illusion: denkt r={r_nom_ill:.2f} ist real)")
print(f"    eta=1: r_real_perc={r_real_perc[-1]:+.4f} (korrekt)")
print(f"    c(T,eta=0)={c_T_ill[0]:.1f} vs c(T,eta=1)={c_T_ill[-1]:.1f}")


# ══════════════════════════════════════════════════════════════════════
# R5: Monetary Policy Transmission
# ══════════════════════════════════════════════════════════════════════
print("\n  R5: Monetary Policy Transmission")

# Zentralbank aendert r. Wirkung haengt von I ab.
r_pre = 0.03
r_post = 0.05  # +200 Basispunkte
dr = r_post - r_pre

I_classes = {"Finanzsektor (I=50)": 50.0, "Mittelstand (I=5)": 5.0,
             "Haushalte (I=1)": 1.0, "Informell (I=0.2)": 0.2}
phi_mp = 0.5
beta_mp = 0.03
gamma_mp = 1.5

R5_data = {}
T_shock = 10.0  # Schock bei t=10
t_eval_mp = np.linspace(0, 40, 801)

# Info-abhaengige Adjustierungs-Geschwindigkeit:
# Agent beobachtet Zinsaenderung nur partiell: alpha(I) = I/(I + phi)
# => dr_wahr = alpha * dr
# I->inf: alpha->1 (volle Transmission)
# I->0: alpha->0 (keine Transmission)

for name, I_v in I_classes.items():
    alpha = I_v / (I_v + phi_mp)  # Informationsabhaengige Anpassung
    # Wahrgenommene neue Rate: alter Zins + alpha * Aenderung
    r_w_pre = r_perceived(r_pre, 0.8, 0.02, phi_mp, I_v)
    r_w_post = r_w_pre + alpha * dr  # Nur alpha-Anteil kommt an
    R_pre = (r_w_pre - beta_mp) / gamma_mp
    R_post = (r_w_post - beta_mp) / gamma_mp
    # Konsum-Pfad
    c_pre = 10.0 * np.exp(R_pre * np.minimum(t_eval_mp, T_shock))
    c_post_start = c_pre[np.argmin(np.abs(t_eval_mp - T_shock))]
    c_full = np.where(t_eval_mp <= T_shock,
                      10.0 * np.exp(R_pre * t_eval_mp),
                      c_post_start * np.exp(R_post * (t_eval_mp - T_shock)))
    # Transmission: wie viel vom dr kommt an?
    dr_perceived = r_w_post - r_w_pre
    transmission = dr_perceived / dr * 100
    R5_data[name] = dict(c=c_full, r_w_pre=r_w_pre, r_w_post=r_w_post,
                          R_pre=R_pre, R_post=R_post, dR=R_post-R_pre,
                          transmission=transmission, I=I_v, alpha=alpha)
    print(f"    {name:25s}: alpha={alpha:.3f}, dr_wahr={dr_perceived:+.4f}, Transmission={transmission:.0f}%")

results["R5"] = dict(label="R5: Geldpolitik-Transmission", data=R5_data,
                      t_eval=t_eval_mp, T_shock=T_shock)


# ══════════════════════════════════════════════════════════════════════
# R6: Informationskaskade — I(t) dynamisch
# ══════════════════════════════════════════════════════════════════════
print("\n  R6: Informationskaskade")

# I(t) folgt Logistik + Schocks
def I_dynamics(t, I, r_I=0.15, I_max=20.0, omega=0.05, shock_t=25, shock_mag=-15):
    I_s = max(I, 0.01)
    dI = r_I * I_s * (1 - I_s / I_max) - omega * I_s
    # Schock: plotzlicher Informationsverlust
    if abs(t - shock_t) < 0.5:
        dI += shock_mag
    return dI

scenarios_R6 = {
    "Normales Wachstum": dict(I0=1.0, shock_mag=0),
    "Info-Schock t=25": dict(I0=1.0, shock_mag=-15),
    "Zensur (omega=0.3)": dict(I0=10.0, shock_mag=0),
}

R6_data = {}
for name, sc in scenarios_R6.items():
    omega_eff = 0.3 if "Zensur" in name else 0.05
    def make_rhs(sm, om):
        def rhs(t, y):
            return [max(0.15 * max(y[0],0.01) * (1 - max(y[0],0.01)/20) - om * max(y[0],0.01) +
                    (sm if abs(t-25)<0.5 else 0), -max(y[0],0.01)*0.001)]  # dummy 2nd state
        return rhs
    sol = solve_ivp(lambda t, y: [0.15 * max(y[0],0.01) * (1 - max(y[0],0.01)/20) -
                    omega_eff * max(y[0],0.01) + (sc["shock_mag"] if abs(t-25)<0.5 else 0)],
                    [0, T], [sc["I0"]], t_eval=t_eval, method='RK45',
                    rtol=1e-8, atol=1e-10)
    I_t = np.maximum(sol.y[0], 0.01)
    r_wahr_t = r_perceived(0.05, 0.8, 0.02, 0.5, I_t)
    R_t = (r_wahr_t - 0.03) / 1.5
    # Konsum via integriertes R
    dt = np.diff(sol.t)
    R_mid = 0.5 * (R_t[:-1] + R_t[1:])
    log_c = np.concatenate([[0], np.cumsum(R_mid * dt)])
    c_t = 10.0 * np.exp(log_c)
    R6_data[name] = dict(t=sol.t, I=I_t, r_wahr=r_wahr_t, R=R_t, c=c_t)
    print(f"    {name:25s}: I(T)={I_t[-1]:.2f}, r_wahr(T)={r_wahr_t[-1]:+.4f}, c(T)={c_t[-1]:.2f}")

results["R6"] = dict(label="R6: Informationskaskade", data=R6_data)


# ══════════════════════════════════════════════════════════════════════
# R7: Systematischer Bias — Uber-/Unterschaetzung
# ══════════════════════════════════════════════════════════════════════
print("\n  R7: Systematischer Bias")

# Monte-Carlo: N Agenten mit stochastischem r_wahr
N_mc = 5000
r_true = 0.05
pi_mc = 0.03

# 3 Populationen: Optimisten, Neutral, Pessimisten
populations = {
    "Optimisten (eta=1.2)": dict(eta_mu=1.2, eta_sig=0.1, phi_mu=0.1, I_mu=10),
    "Neutral (eta=0.8)": dict(eta_mu=0.8, eta_sig=0.1, phi_mu=0.1, I_mu=30),
    "Pessimisten (eta=0.3)": dict(eta_mu=0.3, eta_sig=0.1, phi_mu=1.0, I_mu=1),
}

R7_data = {}
for name, pop in populations.items():
    eta_i = np.random.normal(pop["eta_mu"], pop["eta_sig"], N_mc)
    phi_i = np.random.lognormal(np.log(pop["phi_mu"]), 0.3, N_mc)
    I_i = np.random.lognormal(np.log(pop["I_mu"]), 0.5, N_mc)
    I_i = np.clip(I_i, 0.05, 200)
    r_w = r_perceived(r_true, eta_i, pi_mc, phi_i, I_i)
    r_ref = r_true + 0.8 * pi_mc  # Was ein "korrekter" Agent sehen wuerde
    bias_i = r_w - r_ref
    R7_data[name] = dict(r_wahr=r_w, bias=bias_i, eta=eta_i, phi=phi_i, I=I_i,
                          mean_bias=np.mean(bias_i), std_bias=np.std(bias_i),
                          pct_overest=np.mean(bias_i > 0) * 100)
    print(f"    {name:30s}: mean_bias={np.mean(bias_i):+.4f}, std={np.std(bias_i):.4f}, "
          f"overest={np.mean(bias_i>0)*100:.0f}%")

results["R7"] = dict(label="R7: Systematischer Bias", data=R7_data)


# ══════════════════════════════════════════════════════════════════════
# R8: Realzins-Illusion und Wohlfahrt
# ══════════════════════════════════════════════════════════════════════
print("\n  R8: Realzins-Illusion + Wohlfahrt")

# Verschiedene (r_nom, pi)-Kombinationen mit gleichem r_real=0.02
r_real_target = 0.02
combos = [(0.02, 0.00), (0.04, 0.02), (0.06, 0.04), (0.08, 0.06), (0.12, 0.10)]
eta_R8 = 0.6  # Teilweise Geldillusion
phi_R8 = 0.3
I_R8 = 5.0
beta_R8 = 0.03
gamma_R8 = 1.5

R8_data = {}
for r_n, pi_v in combos:
    r_w = r_perceived(r_n, eta_R8, pi_v, phi_R8, I_R8)
    R_v = (r_w - beta_R8) / gamma_R8
    c_T = 10 * np.exp(R_v * T)
    # Wohlfahrt (CRRA): U = c^(1-gamma)/(1-gamma), integriert (analytisch naeherungsweise)
    # approximiere als c(T) als Proxy
    label = f"r={r_n:.0%},pi={pi_v:.0%}"
    R8_data[label] = dict(r_nom=r_n, pi=pi_v, r_real=r_n-pi_v, r_wahr=r_w,
                           R=R_v, c_T=c_T)
    print(f"    {label:20s}: r_real={r_n-pi_v:.2f}, r_wahr={r_w:+.4f}, c(T)={c_T:.1f}")

results["R8"] = dict(label="R8: Realzins-Illusion", data=R8_data, combos=combos)


# ══════════════════════════════════════════════════════════════════════
# VALIDIERUNGEN
# ══════════════════════════════════════════════════════════════════════

validations = {}
print(f"\n{'='*72}\n  VALIDIERUNGEN\n{'='*72}")

# V1: Fisher-Neutralitaet — bei eta=1, phi=0: r_real_wahr = r_nom - pi (exakt)
fisher_errors = []
for pi in pi_vals:
    r_w = R1_data[(1.0, pi)]["r_wahr"]
    r_real = r_w - pi
    fisher_errors.append(abs(r_real - r_nom))
v1_err = max(fisher_errors)
v1_pass = v1_err < 1e-12
validations["V1"] = dict(name="Fisher: eta=1 => r_real=const", passed=v1_pass,
                          detail=f"max|r_real-r|={v1_err:.2e}")
print(f"  V1: {'PASS' if v1_pass else 'FAIL'} ({validations['V1']['detail']})")

# V2: EMH-Limit — I->inf => phi/(I+eps)->0
r_emh = r_perceived(0.05, 0.8, 0.02, 0.5, 1e8)
r_nofric = 0.05 + 0.8 * 0.02
v2_err = abs(r_emh - r_nofric)
v2_pass = v2_err < 1e-8
validations["V2"] = dict(name="EMH: I->inf => friction->0", passed=v2_pass,
                          detail=f"|r_wahr-r_nofric|={v2_err:.2e}")
print(f"  V2: {'PASS' if v2_pass else 'FAIL'} ({validations['V2']['detail']})")

# V3: Monotonie — r_wahr steigt mit I (weniger Friction)
I_test = np.logspace(-1, 2, 100)
r_test = r_perceived(0.05, 0.8, 0.02, 0.5, I_test)
v3_pass = np.all(np.diff(r_test) > 0)
validations["V3"] = dict(name="Monotonie: dr_wahr/dI > 0", passed=v3_pass,
                          detail=f"all_increasing={v3_pass}")
print(f"  V3: {'PASS' if v3_pass else 'FAIL'} ({validations['V3']['detail']})")

# V4: Geldillusion — bei eta=0 ist r_real_wahr = r - pi (unterschaetzt)
r_w_eta0 = r_perceived(0.07, 0.0, 0.05, 0.0, 1e6)
v4_pass = abs(r_w_eta0 - 0.07) < 1e-10  # Agent denkt r=r_nom (ignoriert pi)
validations["V4"] = dict(name="Geldillusion: eta=0 => r_wahr=r_nom", passed=v4_pass,
                          detail=f"|r_wahr-r_nom|={abs(r_w_eta0-0.07):.2e}")
print(f"  V4: {'PASS' if v4_pass else 'FAIL'} ({validations['V4']['detail']})")

# V5: Transmission -> 100% bei I->inf (alpha=I/(I+phi) -> 1)
I_inf = 1e8
alpha_inf = I_inf / (I_inf + 0.5)
trans_inf = alpha_inf * 100
v5_pass = abs(trans_inf - 100) < 0.01
validations["V5"] = dict(name="Transmission=100% bei I->inf", passed=v5_pass,
                          detail=f"alpha(I=1e8)={alpha_inf:.10f}, Transmission={trans_inf:.6f}%")
print(f"  V5: {'PASS' if v5_pass else 'FAIL'} ({validations['V5']['detail']})")

# V6: Bias-Mittelwert — bei symmetrischen Agenten ~ 0
neutral_bias = R7_data["Neutral (eta=0.8)"]["mean_bias"]
v6_pass = abs(neutral_bias) < 0.05  # Nahe null fuer "neutrale" Population
validations["V6"] = dict(name="Bias~0 fuer neutrale Population", passed=v6_pass,
                          detail=f"mean_bias={neutral_bias:+.4f}")
print(f"  V6: {'PASS' if v6_pass else 'FAIL'} ({validations['V6']['detail']})")

# V7: Ungleichheit waechst (heterogene r_wahr -> Konsum divergiert)
v7_pass = R3_data["gini_T"] > R3_data["gini_0"]
validations["V7"] = dict(name="Gini(T) > Gini(0)", passed=v7_pass,
                          detail=f"Gini: {R3_data['gini_0']:.3f} -> {R3_data['gini_T']:.3f}")
print(f"  V7: {'PASS' if v7_pass else 'FAIL'} ({validations['V7']['detail']})")

# V8: Realzins-Illusion — alle Combos haben r_real=0.02, aber c(T) verschieden (bei eta<1)
cTs = [R8_data[f"r={r:.0%},pi={p:.0%}"]["c_T"] for r, p in combos]
v8_pass = max(cTs) / min(cTs) > 1.5  # Signifikante Unterschiede trotz gleichem r_real
validations["V8"] = dict(name="Illusion: gleiches r_real, versch. c(T)", passed=v8_pass,
                          detail=f"c(T) ratio={max(cTs)/min(cTs):.2f}")
print(f"  V8: {'PASS' if v8_pass else 'FAIL'} ({validations['V8']['detail']})")


# ══════════════════════════════════════════════════════════════════════
# SENSITIVITAETSANALYSEN
# ══════════════════════════════════════════════════════════════════════

print(f"\n{'='*72}\n  SENSITIVITAETSANALYSEN\n{'='*72}")

# SA1: phi-Sweep — Friction-Staerke
phi_sa = np.linspace(0, 3, 200)
r_w_sa1 = r_perceived(0.05, 0.8, 0.02, phi_sa, 2.0)
results["SA1"] = dict(phi=phi_sa, r_wahr=r_w_sa1)
print(f"  SA1: phi-Sweep: r_wahr(phi=0)={r_w_sa1[0]:+.4f}, r_wahr(phi=3)={r_w_sa1[-1]:+.4f}")

# SA2: eta-pi Heatmap — 50x50
eta_2d = np.linspace(0, 1.5, 50)
pi_2d = np.linspace(-0.02, 0.12, 50)
ETA, PI = np.meshgrid(eta_2d, pi_2d)
R_WAHR_2D = r_perceived(0.05, ETA, PI, 0.3, 5.0)
results["SA2"] = dict(eta=eta_2d, pi=pi_2d, r_wahr=R_WAHR_2D)
print(f"  SA2: 50x50 Heatmap (eta, pi): min={R_WAHR_2D.min():+.4f}, max={R_WAHR_2D.max():+.4f}")

# SA3: I vs phi Heatmap — wo ist Friction dominant?
I_2d = np.logspace(-1, 2, 50)
phi_2d = np.linspace(0.1, 3, 50)
I2D, PHI2D = np.meshgrid(I_2d, phi_2d)
FRICTION = PHI2D / (I2D + 0.01)
results["SA3"] = dict(I=I_2d, phi=phi_2d, friction=FRICTION)
print(f"  SA3: 50x50 Heatmap (I, phi) -> friction: max={FRICTION.max():.1f}")

# SA4: Transmission vs I fuer verschiedene phi (alpha=I/(I+phi))
I_trans = np.logspace(-1, 2, 200)
SA4_data = {}
for phi in [0.1, 0.5, 1.0, 2.0]:
    alpha_sa = I_trans / (I_trans + phi)
    trans_sa = alpha_sa * 100
    SA4_data[phi] = trans_sa
results["SA4"] = dict(I=I_trans, data=SA4_data)
print(f"  SA4: Transmission(I=0.1,phi=1)={SA4_data[1.0][0]:.0f}%, (I=100,phi=1)={SA4_data[1.0][-1]:.0f}%")

# SA5: Wohlfahrtsverlust durch Info-Friction
I_welf = np.logspace(-1, 2, 200)
r_w_welf = r_perceived(0.05, 0.8, 0.02, 0.5, I_welf)
R_welf = (r_w_welf - 0.03) / 1.5
c_T_welf = 10 * np.exp(R_welf * T)
c_T_ref = 10 * np.exp(((0.05 + 0.8*0.02 - 0.03)/1.5) * T)
welfare_loss = (c_T_ref - c_T_welf) / c_T_ref * 100
results["SA5"] = dict(I=I_welf, welfare_loss=welfare_loss, c_T=c_T_welf, c_T_ref=c_T_ref)
print(f"  SA5: Welfare loss(I=0.1)={welfare_loss[np.argmin(np.abs(I_welf-0.1))]:.0f}%, "
      f"(I=100)={welfare_loss[np.argmin(np.abs(I_welf-100))]:.1f}%")


# ══════════════════════════════════════════════════════════════════════
# PLOT (27 Panels)
# ══════════════════════════════════════════════════════════════════════

print(f"\n  PLOTTE ...")
fig = plt.figure(figsize=(26, 44))
gs = GridSpec(10, 3, figure=fig, height_ratios=[1, 1, 1, 1, 1, 1, 1, 1, 1, 0.35],
              hspace=0.38, wspace=0.30)
fig.suptitle('S18  V.1a  Wahrgenommener Zins',
             fontsize=15, fontweight='bold', y=0.995)

# ── Row 1: R1 Fisher ──
ax = fig.add_subplot(gs[0, 0])
for eta in eta_vals:
    r_reals = [R1_data[(eta, p)]["r_real"] for p in pi_vals]
    ax.plot(pi_vals * 100, r_reals, 'o-', lw=2, label=f'eta={eta}')
ax.axhline(r_nom, color='black', ls=':', lw=0.8, label='r_nom')
ax.set_xlabel('pi [%]'); ax.set_ylabel('r_real_wahr')
ax.set_title('(a) R1: Fisher-Effekt (V1)')
ax.legend(fontsize=7); ax.grid(True, alpha=0.3)

ax = fig.add_subplot(gs[0, 1])
for eta in eta_vals:
    r_wahrs = [R1_data[(eta, p)]["r_wahr"] for p in pi_vals]
    ax.plot(pi_vals * 100, r_wahrs, 'o-', lw=2, label=f'eta={eta}')
ax.set_xlabel('pi [%]'); ax.set_ylabel('r_wahr')
ax.set_title('(b) R1: r_wahr vs Inflation')
ax.legend(fontsize=7); ax.grid(True, alpha=0.3)

# ── R2 Info-Friction ──
ax = fig.add_subplot(gs[0, 2])
for phi in phi_vals:
    ax.semilogx(I_sweep, R2_data[phi]["r_wahr"], lw=2, label=f'phi={phi}')
ax.axhline(r_base + eta_base * pi_base, color='red', ls=':', lw=0.8, label='friktionslos')
ax.set_xlabel('I (log)'); ax.set_ylabel('r_wahr')
ax.set_title('(c) R2: Info-Friction (V2, V3)')
ax.legend(fontsize=6); ax.grid(True, alpha=0.3)

# ── Row 2: R3 Heterogen ──
ax = fig.add_subplot(gs[1, 0])
sc = ax.scatter(I_het, phi_het, c=r_wahr_het, cmap='RdYlGn', s=8, alpha=0.7)
plt.colorbar(sc, ax=ax, label='r_wahr')
ax.set_xscale('log')
ax.set_xlabel('I (log)'); ax.set_ylabel('phi')
ax.set_title('(d) R3: Agenten (I, phi) -> r_wahr')

ax = fig.add_subplot(gs[1, 1])
ax.hist(bias_het, bins=50, density=True, alpha=0.7, color='C0')
ax.axvline(0, color='red', ls=':', lw=1)
ax.set_xlabel('Bias (r_wahr - r_ref)'); ax.set_ylabel('Dichte')
ax.set_title(f'(e) R3: Bias-Verteilung (V6, V7)')
ax.grid(True, alpha=0.3)

ax = fig.add_subplot(gs[1, 2])
c_T_clip = np.clip(np.abs(c_T_het), 0, np.percentile(np.abs(c_T_het), 95))
ax.hist(c0_het, bins=30, alpha=0.5, density=True, label='t=0')
ax.hist(c_T_clip, bins=30, alpha=0.5, density=True, label='t=T')
ax.set_xlabel('c'); ax.set_ylabel('Dichte')
ax.set_title('(f) R3: Konsumverteilung')
ax.legend(fontsize=7); ax.grid(True, alpha=0.3)

# ── Row 3: R4 Geldillusion ──
ax = fig.add_subplot(gs[2, 0])
ax.plot(eta_illusion, r_real_perc, 'C0-', lw=2, label='r_real_wahr')
ax.axhline(r_real_true, color='red', ls=':', lw=1, label=f'r_real_true={r_real_true:.2f}')
ax.set_xlabel('eta (Inflationsbewusstsein)')
ax.set_ylabel('Wahrgenommener Realzins')
ax.set_title('(g) R4: Geldillusion (V4)')
ax.legend(fontsize=7); ax.grid(True, alpha=0.3)

ax = fig.add_subplot(gs[2, 1])
ax.plot(eta_illusion, c_T_ill, 'C1-', lw=2)
ax.set_xlabel('eta'); ax.set_ylabel('c(T)')
ax.set_title('(h) R4: Konsum bei Geldillusion')
ax.grid(True, alpha=0.3)

# ── R5 Transmission ──
ax = fig.add_subplot(gs[2, 2])
names_R5 = list(R5_data.keys())
trans_vals = [R5_data[n]["transmission"] for n in names_R5]
colors = ['C0', 'C1', 'C2', 'C3']
ax.barh(range(len(names_R5)), trans_vals, color=colors[:len(names_R5)], alpha=0.7)
ax.set_yticks(range(len(names_R5)))
ax.set_yticklabels(names_R5, fontsize=7)
ax.axvline(100, color='red', ls=':', lw=0.8, label='100%')
ax.set_xlabel('Transmission [%]')
ax.set_title('(i) R5: Geldpolitik-Transmission (V5)')
ax.legend(fontsize=7); ax.grid(True, alpha=0.3, axis='x')

# ── Row 4: R5 + R6 ──
ax = fig.add_subplot(gs[3, 0])
for name, d in R5_data.items():
    ax.plot(t_eval_mp, d["c"], lw=2, label=name.split("(")[0].strip())
ax.axvline(T_shock, color='gray', ls=':', lw=0.8, label='Zinsschock')
ax.set_xlabel('t'); ax.set_ylabel('c(t)')
ax.set_title('(j) R5: Konsum nach Zinsschock')
ax.legend(fontsize=6); ax.grid(True, alpha=0.3)

ax = fig.add_subplot(gs[3, 1])
for name, d in R6_data.items():
    ax.plot(d["t"], d["I"], lw=2, label=name)
ax.set_xlabel('t'); ax.set_ylabel('I(t)')
ax.set_title('(k) R6: Info-Dynamik')
ax.legend(fontsize=7); ax.grid(True, alpha=0.3)

ax = fig.add_subplot(gs[3, 2])
for name, d in R6_data.items():
    ax.plot(d["t"], d["r_wahr"], lw=2, label=name)
ax.axhline(0.05 + 0.8*0.02, color='red', ls=':', lw=0.8, label='friktionslos')
ax.set_xlabel('t'); ax.set_ylabel('r_wahr(t)')
ax.set_title('(l) R6: r_wahr-Dynamik')
ax.legend(fontsize=6); ax.grid(True, alpha=0.3)

# ── Row 5: R6 Konsum + R7 Bias ──
ax = fig.add_subplot(gs[4, 0])
for name, d in R6_data.items():
    ax.plot(d["t"], d["c"], lw=2, label=name)
ax.set_xlabel('t'); ax.set_ylabel('c(t)')
ax.set_title('(m) R6: Konsum bei Info-Kaskade')
ax.legend(fontsize=7); ax.grid(True, alpha=0.3)

ax = fig.add_subplot(gs[4, 1])
for name, d in R7_data.items():
    ax.hist(d["bias"], bins=50, alpha=0.4, density=True, label=name.split("(")[0].strip())
ax.axvline(0, color='black', ls='-', lw=0.5)
ax.set_xlabel('Bias'); ax.set_ylabel('Dichte')
ax.set_title('(n) R7: Bias-Verteilungen (3 Populationen)')
ax.legend(fontsize=6); ax.grid(True, alpha=0.3)

ax = fig.add_subplot(gs[4, 2])
pop_names = list(R7_data.keys())
mean_biases = [R7_data[n]["mean_bias"] for n in pop_names]
std_biases = [R7_data[n]["std_bias"] for n in pop_names]
ax.bar(range(len(pop_names)), mean_biases, yerr=std_biases,
       color=['C0', 'C1', 'C2'], alpha=0.7, capsize=5)
ax.set_xticks(range(len(pop_names)))
ax.set_xticklabels([n.split("(")[0].strip() for n in pop_names], fontsize=7)
ax.axhline(0, color='red', ls=':', lw=0.8)
ax.set_ylabel('Mittlerer Bias +/- Std')
ax.set_title('(o) R7: Bias nach Population')
ax.grid(True, alpha=0.3, axis='y')

# ── Row 6: R8 + SA1 ──
ax = fig.add_subplot(gs[5, 0])
labels_R8 = list(R8_data.keys())
cTs_R8 = [R8_data[l]["c_T"] for l in labels_R8]
ax.bar(range(len(labels_R8)), cTs_R8, color=[f'C{i}' for i in range(len(labels_R8))], alpha=0.7)
ax.set_xticks(range(len(labels_R8)))
ax.set_xticklabels(labels_R8, fontsize=6, rotation=20)
ax.set_ylabel('c(T)')
ax.set_title('(p) R8: Realzins-Illusion (V8)')
ax.grid(True, alpha=0.3, axis='y')

ax = fig.add_subplot(gs[5, 1])
ax.plot(phi_sa, r_w_sa1, 'C0-', lw=2)
ax.axhline(0.05 + 0.8*0.02, color='red', ls=':', lw=0.8)
ax.set_xlabel('phi'); ax.set_ylabel('r_wahr')
ax.set_title('(q) SA1: r_wahr vs phi')
ax.grid(True, alpha=0.3)

# ── SA2 Heatmap ──
ax = fig.add_subplot(gs[5, 2])
im = ax.imshow(R_WAHR_2D, extent=[eta_2d[0], eta_2d[-1], pi_2d[0]*100, pi_2d[-1]*100],
               aspect='auto', origin='lower', cmap='RdYlGn')
ax.contour(eta_2d, pi_2d*100, R_WAHR_2D, levels=[0.05], colors='black', linewidths=2)
plt.colorbar(im, ax=ax, label='r_wahr')
ax.set_xlabel('eta'); ax.set_ylabel('pi [%]')
ax.set_title('(r) SA2: Heatmap r_wahr(eta, pi)')

# ── Row 7: SA3-SA5 ──
ax = fig.add_subplot(gs[6, 0])
im = ax.imshow(FRICTION, extent=[np.log10(I_2d[0]), np.log10(I_2d[-1]), phi_2d[0], phi_2d[-1]],
               aspect='auto', origin='lower', cmap='hot_r')
ax.contour(np.log10(I_2d), phi_2d, FRICTION, levels=[0.1, 0.5, 1.0, 5.0],
           colors='white', linewidths=1)
plt.colorbar(im, ax=ax, label='phi/(I+eps)')
ax.set_xlabel('log10(I)'); ax.set_ylabel('phi')
ax.set_title('(s) SA3: Friction-Landschaft')

ax = fig.add_subplot(gs[6, 1])
for phi, trans in SA4_data.items():
    ax.semilogx(I_trans, trans, lw=2, label=f'phi={phi}')
ax.axhline(100, color='red', ls=':', lw=0.8)
ax.set_xlabel('I (log)'); ax.set_ylabel('Transmission [%]')
ax.set_title('(t) SA4: Transmission(I, phi)')
ax.legend(fontsize=7); ax.grid(True, alpha=0.3)

ax = fig.add_subplot(gs[6, 2])
ax.semilogx(I_welf, welfare_loss, 'C3-', lw=2)
ax.axhline(0, color='gray', ls=':', lw=0.5)
ax.set_xlabel('I (log)'); ax.set_ylabel('Welfare Loss [%]')
ax.set_title('(u) SA5: Wohlfahrtsverlust vs I')
ax.grid(True, alpha=0.3)

# ── Row 8: Kausalitaet + Physik ──
ax = fig.add_subplot(gs[7, 0])
ax.axis('off')
kaus_text = (
    "KAUSALKETTEN (S18 V.1a):\n"
    "─────────────────────────\n"
    "1. Fisher: eta=1 => Inflation\n"
    "   neutral (r_real=const)\n"
    "   eta<1 => Geldillusion\n\n"
    "2. Info-Friction: phi/(I+eps)\n"
    "   -> systematische Unter-\n"
    "     schaetzung des Zinses\n"
    "   -> Unterkonsum\n\n"
    "3. Transmission: I niedrig\n"
    "   -> Zinssenkung kommt\n"
    "   nicht an -> Geldpolitik\n"
    "   wirkungslos (Liquidity Trap)\n\n"
    "4. Kaskade: I-Schock -> r_wahr\n"
    "   kollabiert -> Konsum bricht\n"
    "   ein -> Feedback auf Markt\n\n"
    "5. Heterogenitaet:\n"
    "   (eta,phi,I) verschieden\n"
    "   -> Bias-Verteilung\n"
    "   -> Gini waechst endogen"
)
ax.text(0.05, 0.95, kaus_text, transform=ax.transAxes, ha='left', va='top',
        fontsize=7.5, family='monospace',
        bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.95))

ax = fig.add_subplot(gs[7, 1:])
ax.axis('off')
phys = (
    "PHYSIKALISCHE INTERPRETATION V.1a:\n\n"
    "r_wahr = r + eta*pi - phi/(I+eps)  hat drei Kanaele:\n\n"
    "1. NOMINALER KANAL: r ist der Marktzins (beobachtbar)\n"
    "2. INFLATIONSKANAL: eta*pi — Erwartungsanpassung.\n"
    "   eta=1: vollstaendige Fisher-Anpassung (rational)\n"
    "   eta<1: Geldillusion — Agent verwechselt nominal/real\n"
    "   eta>1: Ueberreaktion (Inflationsangst)\n\n"
    "3. FRIKTIONSKANAL: -phi/(I+eps)\n"
    "   Informationskosten reduzieren wahrgenommenen Zins\n"
    "   I->inf: verschwindet (EMH)\n"
    "   I->0: dominiert (Marktzusammenbruch)\n\n"
    "GELDPOLITIK-IMPLIKATION:\n"
    "Zinssenkung dr wirkt nur zu (1-phi*d/dI[1/(I+eps)^(-1)])% fuer info-arme Agenten\n"
    "-> In Krisen (I niedrig) ist Geldpolitik impotent"
)
ax.text(0.5, 0.5, phys, transform=ax.transAxes, ha='center', va='center',
        fontsize=8, family='monospace',
        bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.95))

# ── Row 9: Validierung ──
ax = fig.add_subplot(gs[8, 0])
ax.axis('off')
val_text = "VALIDIERUNGEN:\n" + "-"*35 + "\n"
for k, v in validations.items():
    tag = "PASS" if v["passed"] else "FAIL"
    val_text += f"{k}: {v['name'][:32]}\n   {tag}: {v['detail']}\n\n"
ax.text(0.05, 0.95, val_text, transform=ax.transAxes, ha='left', va='top',
        fontsize=6.5, family='monospace',
        bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.95))

ax = fig.add_subplot(gs[8, 1])
# V3 visuell: Monotonie
ax.semilogx(I_test, r_test, 'C0-', lw=2)
ax.set_xlabel('I (log)'); ax.set_ylabel('r_wahr')
ax.set_title('(v) V3: Monotonie r_wahr(I)')
ax.grid(True, alpha=0.3)

ax = fig.add_subplot(gs[8, 2])
# SA5 visuell: c(T) vs I
ax.semilogx(I_welf, c_T_welf, 'C0-', lw=2, label='c(T)')
ax.axhline(c_T_ref, color='red', ls=':', lw=0.8, label=f'EMH c(T)={c_T_ref:.1f}')
ax.set_xlabel('I (log)'); ax.set_ylabel('c(T)')
ax.set_title('(w) SA5: c(T) vs Information')
ax.legend(fontsize=7); ax.grid(True, alpha=0.3)

# ── Metadata ──
ax_meta = fig.add_subplot(gs[9, :])
ax_meta.axis('off')
n_pass = sum(1 for v in validations.values() if v["passed"])
meta = (
    f"S18 V.1a Wahrgenommener Zins | 8 Regime, {len(validations)} Val: "
    f"{n_pass}/{len(validations)} PASS | "
    f"Fisher, Friction, Heterogen (N={N_het}), Geldillusion, Transmission, "
    f"Info-Kaskade, Bias (N={N_mc}), Realzins-Illusion | "
    f"5 SA inkl. 3 Heatmaps | r_wahr = r + eta*pi - phi/(I+eps)"
)
ax_meta.text(0.5, 0.5, meta, transform=ax_meta.transAxes, ha='center', va='center',
             fontsize=9, family='monospace',
             bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.95))

plt.savefig(PLOT_DIR / "S18_V1a_Wahrgenommener_Zins.png", dpi=180, bbox_inches='tight')
plt.close()
print(f"\n  Plot: {PLOT_DIR / 'S18_V1a_Wahrgenommener_Zins.png'}")

# ── Daten ──
save_dict = {
    "t_eval": t_eval, "t_eval_mp": t_eval_mp,
    "R2_I": I_sweep,
    "R3_eta": eta_het, "R3_phi": phi_het, "R3_I": I_het, "R3_r_wahr": r_wahr_het,
    "R3_bias": bias_het, "R3_c0": c0_het, "R3_cT": c_T_het,
    "R4_eta": eta_illusion, "R4_r_real_perc": r_real_perc, "R4_cT": c_T_ill,
    "SA1_phi": phi_sa, "SA1_r_wahr": r_w_sa1,
    "SA2_eta": eta_2d, "SA2_pi": pi_2d, "SA2_r_wahr": R_WAHR_2D,
    "SA3_I": I_2d, "SA3_phi": phi_2d, "SA3_friction": FRICTION,
    "SA4_I": I_trans,
    "SA5_I": I_welf, "SA5_welfare_loss": welfare_loss,
}
for phi, trans in SA4_data.items():
    save_dict[f"SA4_trans_phi{phi}"] = trans
for name, d in R5_data.items():
    safe = name.split("(")[0].strip().replace(" ", "_")
    save_dict[f"R5_c_{safe}"] = d["c"]
for name, d in R6_data.items():
    safe = name.replace(" ", "_").replace("=", "")
    save_dict[f"R6_I_{safe}"] = d["I"]
    save_dict[f"R6_r_wahr_{safe}"] = d["r_wahr"]
    save_dict[f"R6_c_{safe}"] = d["c"]
np.savez_compressed(DATA_DIR / "S18_V1a_Wahrgenommener_Zins.npz", **save_dict)

# ── Zusammenfassung ──
print(f"\n{'='*72}\n  ZUSAMMENFASSUNG S18  V.1a Wahrgenommener Zins\n{'='*72}")
for k, v in validations.items():
    print(f"  {k}: {v['name']:42s}  {'PASS' if v['passed'] else 'FAIL'}  ({v['detail']})")
print(f"\n  Regime:")
for key in ["R1", "R2", "R3", "R4", "R5", "R6", "R7", "R8"]:
    print(f"    {results[key]['label']}")
print(f"\n  Sensitivitaet:")
print(f"    SA1: r_wahr vs phi")
print(f"    SA2: 50x50 Heatmap r_wahr(eta, pi)")
print(f"    SA3: 50x50 Friction-Landschaft (I, phi)")
print(f"    SA4: Transmission(I) fuer verschiedene phi")
print(f"    SA5: Wohlfahrtsverlust vs I")
n_pass = sum(1 for v in validations.values() if v["passed"])
print(f"\n  Gesamtergebnis: {n_pass}/{len(validations)} bestanden")
if n_pass == len(validations):
    print("  >>> ALLE VALIDIERUNGEN BESTANDEN <<<")
print(f"{'='*72}")
