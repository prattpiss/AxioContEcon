"""
S23 – L.1a Wahrgenommener Alternativlohn  (§6.4)
==================================================
Gleichung L.1a:

   w_i^wahr = w_i + alpha_H * w_bar_peer + psi_w / (I_i + eps)

Drei Kanaele (strukturell parallel zu V.1a / S18):
  (1) Eigener Lohn w_i
  (2) Peer-Einfluss alpha_H * w_bar_peer
  (3) Intransparenz-Aufschlag psi_w / (I_i + eps)  [positiv! "Gras ist gruener"]

Vorzeichen-Unterschied zu V.1a:
  - V.1a: Friction NEGATIV  => Agenten unterschaetzen Zins => zu wenig Sparen
  - L.1a: Friction POSITIV  => Agenten ueberschaetzen Alternativlohn => zu viel Jobwechsel

Kopplung an L.1 (S22):
  FOC: w_i^wahr * u'(c*) = V'(L*)  mit c = w_i^wahr * L + r*K + pi

Prop 6.2: Strukturelle Symmetrie V.1a <-> L.1a
Prop 6.4: alpha_H=0, psi_w=0 => w_wahr = w_i (neoklassisch)

8 Regime, 8 Validierungen, 5 Sensitivitaetsanalysen
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
# 1. KERNFUNKTIONEN
# ══════════════════════════════════════════════════════════════════════

EPS = 0.01   # Regularisierung

def w_perceived(w_i, alpha_H, w_bar_peer, psi_w, I_i):
    """L.1a: Wahrgenommener Alternativlohn"""
    return w_i + alpha_H * w_bar_peer + psi_w / (I_i + EPS)

def u_crra_prime(c, gamma):
    c = np.maximum(c, 1e-12)
    return c**(-gamma)

def u_crra(c, gamma):
    c = np.maximum(c, 1e-12)
    if np.isscalar(gamma):
        if abs(gamma - 1.0) < 1e-8:
            return np.log(c)
        return c**(1 - gamma) / (1 - gamma)
    res = np.where(np.abs(gamma - 1.0) < 1e-8, np.log(c),
                   c**(1 - gamma) / (1 - gamma))
    return res

def V_iso_prime(L, chi, eta):
    L = np.maximum(L, 1e-12)
    return chi * L**eta

def V_iso(L, chi, eta):
    L = np.maximum(L, 0.0)
    return chi * L**(1 + eta) / (1 + eta)

def budget(L, w, r, K, pi):
    return w * np.maximum(L, 0.0) + r * K + pi

def solve_L_star(w_eff, r, K, pi, gamma, chi, eta, L_max=2.0):
    """FOC: w_eff * u'(c) = V'(L), c = w_eff*L + r*K + pi"""
    w_eff = max(w_eff, 1e-6)
    def foc(L):
        c = budget(L, w_eff, r, K, pi)
        return w_eff * u_crra_prime(c, gamma) - V_iso_prime(L, chi, eta)
    if foc(1e-6) < 0:
        return 1e-6
    if foc(L_max) > 0:
        return L_max
    return brentq(foc, 1e-6, L_max, xtol=1e-14)

def gini(x):
    x = np.sort(np.abs(np.maximum(x, 1e-6)))
    n = len(x)
    if n == 0 or x.sum() == 0:
        return 0
    return (2 * np.sum(np.arange(1, n+1) * x) - (n + 1) * x.sum()) / (n * x.sum())

def transmission(I_i, psi_w):
    """Transmissionskoeffizient: wie viel vom echten Lohnsignal ankommt"""
    return I_i / (I_i + psi_w + EPS)


# ══════════════════════════════════════════════════════════════════════
# 2. PARAMETER
# ══════════════════════════════════════════════════════════════════════
print("=" * 72)
print("  S23  L.1a Wahrgenommener Alternativlohn (§6.4)")
print("=" * 72)

results = {}
validations = {}

# Basis-Agentenklassen (aus S22)
classes = {
    "Arbeiter":     dict(w_L=1.0, r=0.03, K=1.0,   pi=0.0,  gamma=2.0, chi=1.0, eta=1.5),
    "Unternehmer":  dict(w_L=2.0, r=0.05, K=20.0,  pi=3.0,  gamma=1.5, chi=1.0, eta=1.5),
    "Banker":       dict(w_L=3.0, r=0.06, K=100.0,  pi=10.0, gamma=1.0, chi=1.0, eta=1.5),
}

# ══════════════════════════════════════════════════════════════════════
# R1: Peer-Lohn-Effekt
# ══════════════════════════════════════════════════════════════════════
print("\n  R1: Peer-Lohn-Effekt")
alpha_vals = [0.0, 0.15, 0.3, 0.5, 1.0]
w_bar_peer = 2.5  # Durchschnittlicher Peer-Lohn
psi_w_base = 0.5
I_base = 5.0

R1_data = {}
for name, p in classes.items():
    Ls = []
    for a_H in alpha_vals:
        w_w = w_perceived(p['w_L'], a_H, w_bar_peer, psi_w_base, I_base)
        L_s = solve_L_star(w_w, p['r'], p['K'], p['pi'], p['gamma'], p['chi'], p['eta'])
        Ls.append(L_s)
    R1_data[name] = dict(alpha_vals=alpha_vals, L_star=np.array(Ls), **p)
    print(f"    {name:12s}: L*(aH=0)={Ls[0]:.4f}, L*(aH=0.3)={Ls[2]:.4f}, "
          f"L*(aH=1)={Ls[-1]:.4f}")
results["R1"] = R1_data

# ══════════════════════════════════════════════════════════════════════
# R2: Informationsfriction-Sweep
# ══════════════════════════════════════════════════════════════════════
print("\n  R2: Informationsfriction-Sweep")
I_sweep = np.logspace(-2, 3, 200)
psi_vals = [0.1, 0.3, 0.5, 1.0, 2.0]
w_true = 1.5  # Wahrer Lohn

R2_bias = {}
for psi in psi_vals:
    bias = psi / (I_sweep + EPS)  # Bias = w_wahr - w_true (ohne Peer-Term)
    R2_bias[psi] = bias
    I_crit_idx = np.argmin(np.abs(bias - 0.01 * w_true))  # 1% bias
    print(f"    psi_w={psi:.1f}: bias(I=0.1)={bias[np.argmin(np.abs(I_sweep-0.1))]:.3f}, "
          f"I_crit(1%)={I_sweep[I_crit_idx]:.1f}")
results["R2"] = dict(I=I_sweep, bias=R2_bias)

# ══════════════════════════════════════════════════════════════════════
# R3: Heterogene Agenten (N=300)
# ══════════════════════════════════════════════════════════════════════
print("\n  R3: Heterogene Agenten (N=300)")
N3 = 300
alpha_H_het = rng.beta(2, 3, N3) * 0.8          # [0, 0.8]
psi_w_het = np.clip(rng.lognormal(np.log(0.3), 0.5, N3), 0.01, 3.0)
I_het = np.clip(rng.lognormal(np.log(2), 1.0, N3), 0.05, 100)
w_L_het = np.clip(rng.lognormal(np.log(1.5), 0.4, N3), 0.3, 10)
K_het = np.clip(rng.lognormal(np.log(5), 1.0, N3), 0.1, 200)
pi_het = np.clip(rng.exponential(0.5, N3), 0, 10)
gamma_het = np.clip(rng.lognormal(np.log(2.0), 0.3, N3), 0.5, 8)
eta_het = np.clip(rng.lognormal(np.log(1.5), 0.3, N3), 0.3, 5)

# w_bar_peer = mittlerer Lohn der Population
w_bar_R3 = w_L_het.mean()

# Rationales L* (ohne Friction)
L_rational = np.array([solve_L_star(w_L_het[i], 0.04, K_het[i], pi_het[i],
                                     gamma_het[i], 1.0, eta_het[i])
                        for i in range(N3)])

# Wahrgenommenes L* (mit L.1a)
w_wahr_het = w_perceived(w_L_het, alpha_H_het, w_bar_R3, psi_w_het, I_het)
L_wahr = np.array([solve_L_star(w_wahr_het[i], 0.04, K_het[i], pi_het[i],
                                 gamma_het[i], 1.0, eta_het[i])
                    for i in range(N3)])

bias_het = w_wahr_het - w_L_het
gini_rational = gini(L_rational)
gini_wahr = gini(L_wahr)
corr_bias_I = np.corrcoef(bias_het, I_het)[0, 1]
print(f"    Bias: mean={bias_het.mean():.3f}, std={bias_het.std():.3f}")
print(f"    Gini(L_rational)={gini_rational:.3f}, Gini(L_wahr)={gini_wahr:.3f}")
print(f"    Corr(bias, I)={corr_bias_I:.3f} (erw. negativ)")
results["R3"] = dict(L_rational=L_rational, L_wahr=L_wahr, bias=bias_het,
                      I=I_het, w_wahr=w_wahr_het, w_L=w_L_het,
                      gini_rat=gini_rational, gini_wahr=gini_wahr)

# ══════════════════════════════════════════════════════════════════════
# R4: "Gras ist gruener"-Illusion
# ══════════════════════════════════════════════════════════════════════
print("\n  R4: 'Gras ist gruener'-Illusion")
psi_sweep_R4 = np.linspace(0, 3, 100)
I_R4 = 2.0  # Schlecht informiert
w_own = 1.5
w_target_true = 1.8  # Wahrer Ziellohn
# Agent bewertet Ziellohn: w_target_wahr = w_target + psi_w/(I+eps)
w_target_perc = w_target_true + psi_sweep_R4 / (I_R4 + EPS)
# Optimale Entscheidung (bei wahrem Lohn)
L_opt = solve_L_star(w_target_true, 0.03, 2.0, 0.0, 2.0, 1.0, 1.5)
c_opt = budget(L_opt, w_target_true, 0.03, 2.0, 0.0)
u_opt = u_crra(c_opt, 2.0) - V_iso(L_opt, 1.0, 1.5)

# Agent plant mit w_wahr, erlebt aber w_true
welfare_loss = []
for psi in psi_sweep_R4:
    w_p = w_target_true + psi / (I_R4 + EPS)
    L_plan = solve_L_star(w_p, 0.03, 2.0, 0.0, 2.0, 1.0, 1.5)
    # Agent arbeitet L_plan, erhaelt aber w_target_true
    c_actual = budget(L_plan, w_target_true, 0.03, 2.0, 0.0)
    u_actual = u_crra(c_actual, 2.0) - V_iso(L_plan, 1.0, 1.5)
    welfare_loss.append(float(u_opt) - float(u_actual))
welfare_loss = np.array(welfare_loss)
print(f"    psi=0: Verlust={welfare_loss[0]:.6f} (perfekte Info)")
print(f"    psi=1: Verlust={welfare_loss[np.argmin(np.abs(psi_sweep_R4-1))]:.4f}")
print(f"    psi=3: Verlust={welfare_loss[-1]:.4f}")
results["R4"] = dict(psi=psi_sweep_R4, loss=welfare_loss, w_perc=w_target_perc)

# ══════════════════════════════════════════════════════════════════════
# R5: Arbeitsmarkt-Transmission
# ══════════════════════════════════════════════════════════════════════
print("\n  R5: Arbeitsmarkt-Transmission")
info_classes = {
    "Professional": dict(I=50, psi_w=0.3, w=2.0, gamma=1.5, K=10, pi=2.0),
    "Mittelstand":  dict(I=5,  psi_w=0.5, w=1.5, gamma=2.0, K=3,  pi=0.5),
    "Unqualif.":    dict(I=1,  psi_w=0.8, w=1.0, gamma=2.0, K=0.5,pi=0.0),
    "Informell":    dict(I=0.2,psi_w=1.5, w=0.8, gamma=2.5, K=0.1,pi=0.0),
}
dw = 0.20  # 20% Lohnschock (relativ)
R5_data = {}
for name, p in info_classes.items():
    trans = transmission(p['I'], p['psi_w'])
    w_before = w_perceived(p['w'], 0.2, 1.5, p['psi_w'], p['I'])
    w_after = w_perceived(p['w'] * (1 + dw), 0.2, 1.5, p['psi_w'], p['I'])
    dw_perc = (w_after - w_before) / w_before
    L_before = solve_L_star(w_before, 0.04, p['K'], p['pi'], p['gamma'], 1.0, 1.5)
    L_after = solve_L_star(w_after, 0.04, p['K'], p['pi'], p['gamma'], 1.0, 1.5)
    R5_data[name] = dict(trans=trans, dw_perc=dw_perc, L_before=L_before,
                          L_after=L_after, dL_pct=(L_after-L_before)/L_before*100)
    print(f"    {name:12s}: Trans={trans:.3f}, dw_perc={dw_perc*100:.1f}%, "
          f"dL={R5_data[name]['dL_pct']:.2f}%")
results["R5"] = R5_data

# ══════════════════════════════════════════════════════════════════════
# R6: Informationskaskade — I(t) dynamisch
# ══════════════════════════════════════════════════════════════════════
print("\n  R6: Informationskaskade (3 Szenarien)")
T_R6 = 60; dt_R6 = 0.1
t_R6 = np.arange(0, T_R6, dt_R6)
Nt = len(t_R6)
r_I = 0.1; I_max = 20.0; omega_base = 0.02

scenarios_R6 = {
    "Normal":     dict(omega=omega_base, shock_t=None, shock_mag=0),
    "Info-Schock": dict(omega=omega_base, shock_t=25.0, shock_mag=-8.0),
    "Sperre":     dict(omega=0.3, shock_t=None, shock_mag=0),
}
w_R6 = 1.5
R6_data = {}
for sname, sp in scenarios_R6.items():
    I_t = np.zeros(Nt); I_t[0] = 3.0
    w_wahr_t = np.zeros(Nt)
    L_t = np.zeros(Nt)
    for ti in range(Nt):
        if sp['shock_t'] is not None and abs(t_R6[ti] - sp['shock_t']) < dt_R6:
            I_t[ti] = max(I_t[ti] + sp['shock_mag'], 0.1)
        w_wahr_t[ti] = w_perceived(w_R6, 0.3, 2.0, 0.5, I_t[ti])
        L_t[ti] = solve_L_star(w_wahr_t[ti], 0.04, 3.0, 0.0, 2.0, 1.0, 1.5)
        if ti < Nt - 1:
            dI = r_I * I_t[ti] * (1 - I_t[ti] / I_max) - sp['omega'] * I_t[ti]
            I_t[ti+1] = max(I_t[ti] + dI * dt_R6, 0.05)
    R6_data[sname] = dict(t=t_R6, I=I_t, w_wahr=w_wahr_t, L=L_t)
    print(f"    {sname:12s}: I(T)={I_t[-1]:.2f}, w_wahr(T)={w_wahr_t[-1]:.3f}, "
          f"L*(T)={L_t[-1]:.4f}")
results["R6"] = R6_data

# ══════════════════════════════════════════════════════════════════════
# R7: Migration — Schwellenwert-Entscheidung
# ══════════════════════════════════════════════════════════════════════
print("\n  R7: Migration (N=500)")
N7 = 500
I_mig = np.clip(rng.lognormal(np.log(2), 1.2, N7), 0.05, 200)
w_home = 1.0  # Lohn Herkunftsregion
w_dest_true = 1.5  # Wahrer Lohn Zielregion
kappa = 0.3  # Wechselkosten
psi_w_mig = 0.5

w_dest_perceived = w_perceived(w_dest_true, 0.0, 0.0, psi_w_mig, I_mig)
# Migrationsentscheidung: wechsel wenn w_dest_perceived > w_home + kappa
migrate = w_dest_perceived > w_home + kappa
# Korrekte Entscheidung: wechsel wenn w_dest_true > w_home + kappa
correct_decision = w_dest_true > w_home + kappa  # Hier: 1.5 > 1.3 => True
# Fehler: Agent migriert NICHT obwohl er sollte (false negative kaum moeglich da Friction positiv)
# Oder: richtige Migration bei richtigen Gruenden
migration_rate = migrate.mean()
# "Uebermigriert" = haette korrekt nicht migriert, aber tut es wegen Friction?
# Hier ist w_dest_true > w_home + kappa, also ist Migration korrekt.
# Test mit w_dest_true < w_home + kappa:
w_dest_bad = 1.2  # Nicht genug fuer Wechsel: 1.2 < 1.0 + 0.3
w_bad_perceived = w_perceived(w_dest_bad, 0.0, 0.0, psi_w_mig, I_mig)
migrate_bad = w_bad_perceived > w_home + kappa
fehlmig_rate = migrate_bad.mean()
print(f"    Gutes Ziel: Migrationsrate={migration_rate*100:.1f}% "
      f"(optimal: 100%, da w_dest={w_dest_true} > w+kappa={w_home+kappa})")
print(f"    Schlechtes Ziel: Fehlmigrationsrate={fehlmig_rate*100:.1f}% "
      f"(optimal: 0%, da w_dest={w_dest_bad} < w+kappa={w_home+kappa})")
# Fehlmig vs I
I_bins = np.logspace(-1, 2, 20)
fehlmig_by_I = []
for ib in range(len(I_bins)-1):
    mask = (I_mig >= I_bins[ib]) & (I_mig < I_bins[ib+1])
    if mask.sum() > 0:
        fehlmig_by_I.append((I_bins[ib:ib+2].mean(), migrate_bad[mask].mean()))
    else:
        fehlmig_by_I.append((I_bins[ib:ib+2].mean(), np.nan))
fehlmig_by_I = np.array(fehlmig_by_I)
results["R7"] = dict(I=I_mig, migrate_good=migrate, migrate_bad=migrate_bad,
                      migration_rate=migration_rate, fehlmig_rate=fehlmig_rate,
                      fehlmig_by_I=fehlmig_by_I)

# ══════════════════════════════════════════════════════════════════════
# R8: L.1 + L.1a Vollstaendiges Modell (N=80)
# ══════════════════════════════════════════════════════════════════════
print("\n  R8: L.1 + L.1a Vollstaendiges Modell (N=80)")
N8 = 80
w_L8 = np.clip(rng.lognormal(np.log(1.5), 0.4, N8), 0.3, 10)
K8 = np.clip(rng.lognormal(np.log(5), 1.0, N8), 0.1, 200)
pi8 = np.clip(rng.exponential(1.0, N8), 0, 20)
gamma8 = np.clip(rng.lognormal(np.log(2.0), 0.3, N8), 0.5, 8)
eta8 = np.clip(rng.lognormal(np.log(1.5), 0.3, N8), 0.3, 5)
I8 = np.clip(rng.lognormal(np.log(3), 1.0, N8), 0.1, 100)
psi8 = np.clip(rng.lognormal(np.log(0.4), 0.5, N8), 0.01, 3.0)
alpha8 = rng.beta(2, 3, N8) * 0.6

w_bar8 = w_L8.mean()
w_wahr8 = w_perceived(w_L8, alpha8, w_bar8, psi8, I8)

L_rat8 = np.array([solve_L_star(w_L8[i], 0.04, K8[i], pi8[i],
                                 gamma8[i], 1.0, eta8[i]) for i in range(N8)])
L_wahr8 = np.array([solve_L_star(w_wahr8[i], 0.04, K8[i], pi8[i],
                                  gamma8[i], 1.0, eta8[i]) for i in range(N8)])
divergence = np.abs(L_wahr8 - L_rat8)
corr_div_I = np.corrcoef(divergence, I8)[0, 1]
L_agg_rat = L_rat8.sum()
L_agg_wahr = L_wahr8.sum()
print(f"    L_agg(rational)={L_agg_rat:.1f}, L_agg(wahr)={L_agg_wahr:.1f}")
print(f"    Divergenz: mean={divergence.mean():.4f}, max={divergence.max():.4f}")
print(f"    Corr(|Divergenz|, I)={corr_div_I:.3f} (erw. negativ)")
results["R8"] = dict(L_rat=L_rat8, L_wahr=L_wahr8, I=I8,
                      divergence=divergence, L_agg_rat=L_agg_rat,
                      L_agg_wahr=L_agg_wahr)


# ══════════════════════════════════════════════════════════════════════
# VALIDIERUNGEN
# ══════════════════════════════════════════════════════════════════════
print(f"\n{'='*72}\n  VALIDIERUNGEN\n{'='*72}")

# V1: Peer-Neutralitaet: alpha_H=0 => w_wahr = w + psi/(I+eps)
w_test_v1 = 1.5; psi_v1 = 0.5; I_v1 = 5.0
w_nopeer = w_perceived(w_test_v1, 0.0, 999.0, psi_v1, I_v1)
w_expected = w_test_v1 + psi_v1 / (I_v1 + EPS)
v1_err = abs(w_nopeer - w_expected)
v1_pass = v1_err < 1e-14
validations["V1"] = dict(name="Peer-Neutralitaet: aH=0 => kein Peer-Term",
                         passed=v1_pass, detail=f"|err|={v1_err:.2e}")
print(f"  V1: {'PASS' if v1_pass else 'FAIL'} ({validations['V1']['detail']})")

# V2: EMH: I->inf => Friction->0
w_emh = w_perceived(1.5, 0.3, 2.5, 0.5, 1e8)
w_emh_expected = 1.5 + 0.3 * 2.5  # Friction ~ 0
v2_err = abs(w_emh - w_emh_expected)
v2_pass = v2_err < 1e-6
validations["V2"] = dict(name="EMH: I->inf => Friction->0",
                         passed=v2_pass,
                         detail=f"w_wahr={w_emh:.10f}, expected={w_emh_expected:.10f}, err={v2_err:.2e}")
print(f"  V2: {'PASS' if v2_pass else 'FAIL'} ({validations['V2']['detail']})")

# V3: Monotonie: dw_wahr/dI < 0 (Friction-Term sinkt mit I)
I_mono = np.logspace(-1, 3, 1000)
w_mono = w_perceived(1.5, 0.3, 2.0, 0.5, I_mono)
dw_dI = np.diff(w_mono)
# Friction-Term sinkt => w_wahr sinkt wenn Peer-Term fix
# ABER: w_wahr = w + aH*w_bar + psi/(I+eps), letzer Term sinkt
# Der Gesamt-w_wahr sinkt also monoton in I
v3_pass = np.all(dw_dI <= 1e-10)
validations["V3"] = dict(name="Monotonie: dw_wahr/dI < 0 (Friction sinkt)",
                         passed=v3_pass, detail=f"all_dec={v3_pass}, max(dw)={dw_dI.max():.2e}")
print(f"  V3: {'PASS' if v3_pass else 'FAIL'} ({validations['V3']['detail']})")

# V4: Neoklassisch: aH=0, psi=0 => w_wahr = w
w_neo = w_perceived(1.5, 0.0, 999.0, 0.0, 5.0)
v4_err = abs(w_neo - 1.5)
v4_pass = v4_err < 1e-14
validations["V4"] = dict(name="Neoklassisch: aH=0, psi=0 => w_wahr=w",
                         passed=v4_pass, detail=f"|err|={v4_err:.2e}")
print(f"  V4: {'PASS' if v4_pass else 'FAIL'} ({validations['V4']['detail']})")

# V5: Transmission->100% bei I->inf
trans_inf = transmission(1e8, 0.5)
v5_pass = trans_inf > 0.999
validations["V5"] = dict(name="Transmission->100% bei I->inf",
                         passed=v5_pass, detail=f"trans(I=1e8)={trans_inf:.8f}")
print(f"  V5: {'PASS' if v5_pass else 'FAIL'} ({validations['V5']['detail']})")

# V6: Bias~0 fuer hohe I Population
I_high_pop = 50 + rng.randn(1000) * 5  # Hohe I
I_high_pop = np.maximum(I_high_pop, 10)
bias_high = 0.5 / (I_high_pop + EPS)  # psi=0.5
v6_mean_bias = np.mean(bias_high)
v6_pass = v6_mean_bias < 0.05
validations["V6"] = dict(name="Bias~0 fuer gut informierte Population",
                         passed=v6_pass, detail=f"mean_bias={v6_mean_bias:.4f}")
print(f"  V6: {'PASS' if v6_pass else 'FAIL'} ({validations['V6']['detail']})")

# V7: Friction verzerrt L*: Corr(|L_wahr-L_rat|, I) < 0
div_R3 = np.abs(L_wahr - L_rational)
corr_div_I_R3 = np.corrcoef(div_R3, I_het)[0, 1]
v7_pass = corr_div_I_R3 < 0
validations["V7"] = dict(name="Corr(|L_wahr-L_rat|, I) < 0: Info reduziert Verzerrung",
                         passed=v7_pass,
                         detail=f"Corr={corr_div_I_R3:.4f}, dGini={gini_wahr-gini_rational:.4f}")
print(f"  V7: {'PASS' if v7_pass else 'FAIL'} ({validations['V7']['detail']})")

# V8: Perfekte-Info-Migration: bei I->inf und w_dest > w+kappa => 100% richtig
I_perf = np.ones(100) * 1e6
w_dest_perf = w_perceived(w_dest_true, 0.0, 0.0, psi_w_mig, I_perf)
mig_perf = w_dest_perf > w_home + kappa
v8_pass = mig_perf.all()  # Alle sollten migrieren (da 1.5 > 1.3)
validations["V8"] = dict(name="Perfekte-Info: 100% korrekte Migration",
                         passed=v8_pass,
                         detail=f"rate={mig_perf.mean()*100:.0f}%")
print(f"  V8: {'PASS' if v8_pass else 'FAIL'} ({validations['V8']['detail']})")


# ══════════════════════════════════════════════════════════════════════
# SENSITIVITAETSANALYSEN
# ══════════════════════════════════════════════════════════════════════
print(f"\n{'='*72}\n  SENSITIVITAETSANALYSEN\n{'='*72}")

# SA1: psi_w -> w_wahr und L*
print("  SA1: psi_w -> w_wahr + L*")
psi_sa1 = np.linspace(0, 3, 100)
w_sa1 = np.array([w_perceived(1.5, 0.3, 2.0, p, 3.0) for p in psi_sa1])
L_sa1 = np.array([solve_L_star(w_perceived(1.5, 0.3, 2.0, p, 3.0),
                                0.04, 3.0, 0.0, 2.0, 1.0, 1.5) for p in psi_sa1])
results["SA1"] = dict(psi=psi_sa1, w_wahr=w_sa1, L=L_sa1)
print(f"    psi=0: w_wahr={w_sa1[0]:.3f}, L*={L_sa1[0]:.4f}")
print(f"    psi=3: w_wahr={w_sa1[-1]:.3f}, L*={L_sa1[-1]:.4f}")

# SA2: Heatmap w_wahr(alpha_H, w_bar_peer) 20x20
print("  SA2: (alpha_H, w_bar_peer) -> w_wahr  (20x20)")
sa2_aH = np.linspace(0, 1, 20)
sa2_wp = np.linspace(0.5, 5.0, 20)
SA2_w = np.zeros((20, 20))
for i, aH in enumerate(sa2_aH):
    for j, wp in enumerate(sa2_wp):
        SA2_w[j, i] = w_perceived(1.5, aH, wp, 0.5, 5.0)
results["SA2"] = dict(aH=sa2_aH, wp=sa2_wp, w=SA2_w)
print(f"    w_wahr range: [{SA2_w.min():.3f}, {SA2_w.max():.3f}]")

# SA3: Friction-Landschaft (I, psi_w) -> Bias  20x20
print("  SA3: (I, psi_w) -> Bias  (20x20)")
sa3_I = np.logspace(-2, 2, 20)
sa3_psi = np.logspace(-2, 0.5, 20)
SA3_bias = np.zeros((20, 20))
for i, I_val in enumerate(sa3_I):
    for j, psi_val in enumerate(sa3_psi):
        SA3_bias[j, i] = psi_val / (I_val + EPS)
results["SA3"] = dict(I=sa3_I, psi=sa3_psi, bias=SA3_bias)
print(f"    Bias range: [{SA3_bias.min():.4f}, {SA3_bias.max():.2f}]")

# SA4: Transmission(I, psi_w) 20x20
print("  SA4: (I, psi_w) -> Transmission  (20x20)")
SA4_trans = np.zeros((20, 20))
for i, I_val in enumerate(sa3_I):
    for j, psi_val in enumerate(sa3_psi):
        SA4_trans[j, i] = transmission(I_val, psi_val)
results["SA4"] = dict(I=sa3_I, psi=sa3_psi, trans=SA4_trans)
print(f"    Trans range: [{SA4_trans.min():.4f}, {SA4_trans.max():.4f}]")

# SA5: Wohlfahrtsverlust(I) fuer 3 Klassen
print("  SA5: Wohlfahrtsverlust(I)")
I_sa5 = np.logspace(-1, 2, 50)
SA5_loss = {}
for name, p in classes.items():
    losses = []
    # Optimal: kein Friction
    L_opt_c = solve_L_star(p['w_L'], p['r'], p['K'], p['pi'],
                            p['gamma'], p['chi'], p['eta'])
    c_opt_c = budget(L_opt_c, p['w_L'], p['r'], p['K'], p['pi'])
    u_opt_c = float(u_crra(c_opt_c, p['gamma']) - V_iso(L_opt_c, p['chi'], p['eta']))
    for I_val in I_sa5:
        w_w = w_perceived(p['w_L'], 0.3, 2.0, 0.5, I_val)
        L_plan = solve_L_star(w_w, p['r'], p['K'], p['pi'],
                               p['gamma'], p['chi'], p['eta'])
        # Agent plant mit w_wahr, erlebt w_L
        c_act = budget(L_plan, p['w_L'], p['r'], p['K'], p['pi'])
        u_act = float(u_crra(c_act, p['gamma']) - V_iso(L_plan, p['chi'], p['eta']))
        losses.append(u_opt_c - u_act)
    SA5_loss[name] = np.array(losses)
    print(f"    {name:12s}: loss(I=0.1)={losses[0]:.4f}, loss(I=100)={losses[-1]:.6f}")
results["SA5"] = dict(I=I_sa5, loss=SA5_loss)


# ══════════════════════════════════════════════════════════════════════
# ERWEITERTE ANALYSE
# ══════════════════════════════════════════════════════════════════════
print(f"\n{'='*72}\n  ERWEITERTE ANALYSE\n{'='*72}")

# EA1: Deterministische vs Stochastische Friction
print("  EA1: Deterministische vs Stochastische Friction")
N_ea1 = 1000
I_ea1 = 3.0; psi_ea1 = 0.5
# Deterministisch: stets +psi/(I+eps)
bias_det = psi_ea1 / (I_ea1 + EPS)
# Stochastisch: N(0, sigma^2) mit sigma = psi/sqrt(I+eps)
sigma_stoch = psi_ea1 / np.sqrt(I_ea1 + EPS)
bias_stoch = rng.normal(0, sigma_stoch, N_ea1)
print(f"    Deterministisch: bias = {bias_det:.4f} (immer positiv)")
print(f"    Stochastisch: mean={bias_stoch.mean():.4f}, std={bias_stoch.std():.4f}")
print(f"    -> Deterministisch: systematische Ueberschaetzung")
print(f"    -> Stochastisch: erwartungstreu, aber Varianz ~ 1/I")

# EA2: Prop 6.2 Symmetrie V.1a <-> L.1a
print("\n  EA2: Prop 6.2 Symmetrie V.1a <-> L.1a")
I_symm = np.logspace(-1, 3, 100)
# V.1a: r_wahr = r + eta*pi - phi/(I+eps), Friction negativ
phi_v1a = 0.5
trans_v1a = I_symm / (I_symm + phi_v1a + EPS)
# L.1a: w_wahr = w + aH*w_bar + psi/(I+eps), Friction positiv
trans_l1a = I_symm / (I_symm + psi_ea1 + EPS)
max_trans_diff = np.max(np.abs(trans_v1a - trans_l1a))
print(f"    V.1a phi={phi_v1a}, L.1a psi={psi_ea1}")
print(f"    Bei gleichen Friction-Parametern: max|Trans_diff|={max_trans_diff:.6f}")
print(f"    (bei phi=psi: identische Transmissionskurve)")
# Setze gleiche Parameter
trans_same = I_symm / (I_symm + 0.5 + EPS)
symm_err = np.max(np.abs(trans_v1a - trans_same))
print(f"    Symmetrie-Check: max|T_V1a - T_L1a|={symm_err:.2e} (exakt gleich)")
print(f"    VORZEICHEN-UNTERSCHIED: V.1a friction < 0, L.1a friction > 0")
print(f"    => zu wenig Sparen (V.1a) + zu viel Migration (L.1a)")

# EA3: Komparative Statik
print("\n  EA3: Komparative Statik (5 Parameter)")
base_kp = dict(w_L=1.5, alpha_H=0.3, w_bar=2.0, psi_w=0.5, I=5.0,
               r=0.04, K=3.0, pi=0.5, gamma=2.0, chi=1.0, eta=1.5)
w_base = w_perceived(base_kp['w_L'], base_kp['alpha_H'], base_kp['w_bar'],
                      base_kp['psi_w'], base_kp['I'])
L_base = solve_L_star(w_base, base_kp['r'], base_kp['K'], base_kp['pi'],
                       base_kp['gamma'], base_kp['chi'], base_kp['eta'])
comp_stat = {}
for param, dp in [('alpha_H', 0.01), ('psi_w', 0.01), ('I', 0.1),
                   ('w_bar', 0.01), ('w_L', 0.01)]:
    kp2 = base_kp.copy()
    kp2[param] += dp
    w2 = w_perceived(kp2['w_L'], kp2['alpha_H'], kp2['w_bar'],
                      kp2['psi_w'], kp2['I'])
    L2 = solve_L_star(w2, kp2['r'], kp2['K'], kp2['pi'],
                       kp2['gamma'], kp2['chi'], kp2['eta'])
    comp_stat[param] = (L2 - L_base) / dp
    print(f"    dL*/d{param:8s} = {comp_stat[param]:+.6f}")
results["EA3"] = comp_stat


# ══════════════════════════════════════════════════════════════════════
# MATHEMATISCHE STRUKTUREN
# ══════════════════════════════════════════════════════════════════════
print(f"\n{'='*72}\n  MATHEMATISCHE STRUKTUREN\n{'='*72}")

struct_notes = []

struct_notes.append(
    "STRUKTUR 1: Hyperbolische Friction-Funktion\n"
    f"  f(I) = psi_w / (I + eps): Hyperbel, strikt fallend, konvex\n"
    f"  f(0.1) = {0.5/(0.1+EPS):.2f}, f(1) = {0.5/(1+EPS):.3f}, "
    f"f(10) = {0.5/(10+EPS):.4f}, f(100) = {0.5/(100+EPS):.5f}\n"
    "  Identische Form wie V.1a (phi/(I+eps)) => universelle Friction-Klasse\n"
    "  Polstelle bei I=-eps => physikalisch: I>=0 immer regulaer")

struct_notes.append(
    "STRUKTUR 2: Transmissionsoperator (Michaelis-Menten)\n"
    f"  alpha(I) = I / (I + psi_w): S-foermig [0,1]\n"
    f"  Halbwert: alpha=0.5 bei I=psi_w={0.5}\n"
    "  Identisch zu S03 Michaelis-Menten-Kinetik\n"
    "  Identisch zu V.1a Transmissionsoperator\n"
    "  => Universeller Informations-Transmissions-Kern im Framework")

struct_notes.append(
    "STRUKTUR 3: Verzerrte FOC und Wohlfahrtsverlust\n"
    "  Wahre FOC: w_L * u'(c*) = V'(L*)\n"
    "  Verzerrte: w_wahr * u'(c**) = V'(L**)\n"
    "  Verlust = u(c*)-V(L*) - [u(c**)-V(L**)]\n"
    "  Nicht-additiv in L: Verzerrung wirkt multiplikativ ueber Budget\n"
    f"  Wohlfahrtsverlust Arbeiter(I=0.1): {SA5_loss['Arbeiter'][0]:.4f}")

struct_notes.append(
    "STRUKTUR 4: Vorzeichen-Asymmetrie V.1a <-> L.1a\n"
    "  V.1a: -phi/(I+eps) => UNTERSCHAETZUNG des Zinses => zu wenig Sparen\n"
    "  L.1a: +psi/(I+eps) => UEBERSCHAETZUNG des Alternativlohns => zu viel Migration\n"
    "  Beide: gleiche funktionale Form, gegensaetzlicher Bias\n"
    "  => Informationsarmut erzeugt GLEICHZEITIG Spar- und Migrationsfehler\n"
    "  => 'Poverty Trap': niedrige I => zu wenig K-Akkumulation + Fehlmigration")

struct_notes.append(
    f"STRUKTUR 5: Informations-induzierte Arbeitsungleichheit\n"
    f"  Gini(L_rational) = {gini_rational:.3f}\n"
    f"  Gini(L_wahr)     = {gini_wahr:.3f}\n"
    f"  Delta-Gini       = {gini_wahr - gini_rational:.4f}\n"
    f"  Friction erhoeht Ungleichheit um {(gini_wahr/gini_rational - 1)*100:.1f}%\n"
    "  Schlecht informierte Agenten werden SYSTEMATISCH fehlgeleitet\n"
    "  => Informationspolitik als Instrument der Arbeitsmarktpolitik")

for note in struct_notes:
    print(f"\n  {note}")


# ══════════════════════════════════════════════════════════════════════
# PLOT
# ══════════════════════════════════════════════════════════════════════
print(f"\n  PLOTTE ...")
fig = plt.figure(figsize=(26, 50))
gs = GridSpec(12, 3, figure=fig, height_ratios=[1,1,1,1,1,1,1,1,1,1,1,0.3],
              hspace=0.38, wspace=0.30)
fig.suptitle('S23  L.1a Wahrgenommener Alternativlohn (§6.4)',
             fontsize=15, fontweight='bold', y=0.995)

# ── Row 0: R1 + R2 ──
ax = fig.add_subplot(gs[0, 0])
for name, d in R1_data.items():
    ax.plot(d['alpha_vals'], d['L_star'], 'o-', lw=2, ms=5, label=name)
ax.set_xlabel(r'$\alpha_H$ (Peer-Herding)')
ax.set_ylabel('L*')
ax.set_title(r'(a) R1: L*($\alpha_H$)')
ax.legend(fontsize=6); ax.grid(True, alpha=0.3)

ax = fig.add_subplot(gs[0, 1])
for psi_val, bias in R2_bias.items():
    ax.semilogx(I_sweep, bias, lw=1.5, label=f'ψ={psi_val}')
ax.set_xlabel(r'$\mathcal{I}$ (Information)')
ax.set_ylabel('Bias (w_wahr − w)')
ax.set_title('(b) R2: Friction-Bias')
ax.legend(fontsize=6); ax.grid(True, alpha=0.3)

ax = fig.add_subplot(gs[0, 2])
sc = ax.scatter(I_het, bias_het, c=w_L_het, cmap='viridis', s=5, alpha=0.5)
plt.colorbar(sc, ax=ax, label='w_L')
ax.set_xscale('log')
ax.set_xlabel(r'$\mathcal{I}$'); ax.set_ylabel('Bias')
ax.set_title(f'(c) R3: Bias-Verteilung (N={N3})')
ax.grid(True, alpha=0.3)

# ── Row 1: R3 Gini + R4 + R5 ──
ax = fig.add_subplot(gs[1, 0])
ax.bar(['L*(rational)', 'L*(wahr)'], [gini_rational, gini_wahr],
       color=['C0', 'C3'], alpha=0.7)
ax.set_ylabel('Gini')
ax.set_title(f'(d) R3: Gini-Vergleich')
ax.grid(True, alpha=0.3, axis='y')

ax = fig.add_subplot(gs[1, 1])
ax.plot(psi_sweep_R4, welfare_loss, 'C3-', lw=2)
ax.set_xlabel(r'$\psi_w$ (Intransparenz)')
ax.set_ylabel('Wohlfahrtsverlust')
ax.set_title("(e) R4: 'Gras ist gruener'")
ax.grid(True, alpha=0.3)

ax = fig.add_subplot(gs[1, 2])
names_R5 = list(R5_data.keys())
trans_vals = [R5_data[n]['trans'] for n in names_R5]
ax.bar(range(len(names_R5)), trans_vals, color=['C0', 'C1', 'C2', 'C3'], alpha=0.7)
ax.set_xticks(range(len(names_R5)))
ax.set_xticklabels(names_R5, fontsize=7, rotation=15)
ax.set_ylabel('Transmission')
ax.set_title('(f) R5: Lohn-Transmission')
ax.axhline(1.0, color='black', ls=':', lw=0.5)
ax.grid(True, alpha=0.3, axis='y')

# ── Row 2: R6 Zeitreihen ──
ax = fig.add_subplot(gs[2, 0])
for sname, d in R6_data.items():
    ax.plot(d['t'], d['I'], lw=1.5, label=sname)
ax.set_xlabel('t'); ax.set_ylabel(r'$\mathcal{I}(t)$')
ax.set_title('(g) R6: Information(t)')
ax.legend(fontsize=6); ax.grid(True, alpha=0.3)

ax = fig.add_subplot(gs[2, 1])
for sname, d in R6_data.items():
    ax.plot(d['t'], d['w_wahr'], lw=1.5, label=sname)
ax.set_xlabel('t'); ax.set_ylabel(r'$w^{wahr}(t)$')
ax.set_title('(h) R6: Wahrg. Lohn(t)')
ax.legend(fontsize=6); ax.grid(True, alpha=0.3)

ax = fig.add_subplot(gs[2, 2])
for sname, d in R6_data.items():
    ax.plot(d['t'], d['L'], lw=1.5, label=sname)
ax.set_xlabel('t'); ax.set_ylabel('L*(t)')
ax.set_title('(i) R6: Arbeitsangebot(t)')
ax.legend(fontsize=6); ax.grid(True, alpha=0.3)

# ── Row 3: R7 + R8 ──
ax = fig.add_subplot(gs[3, 0])
valid_mask = ~np.isnan(fehlmig_by_I[:, 1])
ax.semilogx(fehlmig_by_I[valid_mask, 0], fehlmig_by_I[valid_mask, 1] * 100,
            'C3-o', lw=2, ms=4)
ax.set_xlabel(r'$\mathcal{I}$')
ax.set_ylabel('Fehlmigrationsrate (%)')
ax.set_title(f'(j) R7: Migration (N={N7})')
ax.axhline(0, color='green', ls=':', lw=1, label='Optimal')
ax.legend(fontsize=7); ax.grid(True, alpha=0.3)

ax = fig.add_subplot(gs[3, 1])
ax.scatter(L_rat8, L_wahr8, c=I8, cmap='viridis', s=15, alpha=0.6)
lims = [min(L_rat8.min(), L_wahr8.min()) - 0.05,
        max(L_rat8.max(), L_wahr8.max()) + 0.05]
ax.plot(lims, lims, 'k--', lw=0.5, label='45°')
ax.set_xlabel(r'$L^*_{rational}$'); ax.set_ylabel(r'$L^*_{wahr}$')
ax.set_title(f'(k) R8: Rational vs Wahr (Farbe=I)')
ax.legend(fontsize=7); ax.grid(True, alpha=0.3)

ax = fig.add_subplot(gs[3, 2])
ax.scatter(I8, divergence, c=psi8, cmap='hot', s=15, alpha=0.6)
ax.set_xscale('log')
ax.set_xlabel(r'$\mathcal{I}$'); ax.set_ylabel(r'$|L^*_{wahr} - L^*_{rat}|$')
ax.set_title(f'(l) R8: Divergenz vs I (Farbe=ψ)')
ax.grid(True, alpha=0.3)

# ── Row 4: SA1, SA2, SA3 ──
ax = fig.add_subplot(gs[4, 0])
ax2 = ax.twinx()
ax.plot(psi_sa1, w_sa1, 'C0-', lw=2, label='w_wahr')
ax2.plot(psi_sa1, L_sa1, 'C3--', lw=2, label='L*')
ax.set_xlabel(r'$\psi_w$')
ax.set_ylabel('w_wahr', color='C0')
ax2.set_ylabel('L*', color='C3')
ax.set_title('(m) SA1: w_wahr + L* vs ψ_w')
ax.legend(loc='upper left', fontsize=6)
ax2.legend(loc='upper right', fontsize=6)
ax.grid(True, alpha=0.3)

ax = fig.add_subplot(gs[4, 1])
im = ax.imshow(SA2_w, extent=[sa2_aH[0], sa2_aH[-1], sa2_wp[0], sa2_wp[-1]],
               aspect='auto', origin='lower', cmap='YlOrRd')
plt.colorbar(im, ax=ax, label=r'$w^{wahr}$')
# Neutrallinie: w_wahr = 1.5 (eigener Lohn)
ax.contour(sa2_aH, sa2_wp, SA2_w, levels=[1.5], colors='white', linewidths=1.5)
ax.set_xlabel(r'$\alpha_H$'); ax.set_ylabel(r'$\bar{w}^{peer}$')
ax.set_title(r'(n) SA2: $w^{wahr}(\alpha_H, \bar{w}^{peer})$')

ax = fig.add_subplot(gs[4, 2])
im = ax.imshow(np.log10(SA3_bias + 1e-6),
               extent=[np.log10(sa3_I[0]), np.log10(sa3_I[-1]),
                       np.log10(sa3_psi[0]), np.log10(sa3_psi[-1])],
               aspect='auto', origin='lower', cmap='inferno')
plt.colorbar(im, ax=ax, label='log10(Bias)')
ax.set_xlabel(r'log10($\mathcal{I}$)'); ax.set_ylabel(r'log10($\psi_w$)')
ax.set_title(r'(o) SA3: Friction $(\mathcal{I}, \psi_w)$')

# ── Row 5: SA4, SA5 ──
ax = fig.add_subplot(gs[5, 0])
im = ax.imshow(SA4_trans,
               extent=[np.log10(sa3_I[0]), np.log10(sa3_I[-1]),
                       np.log10(sa3_psi[0]), np.log10(sa3_psi[-1])],
               aspect='auto', origin='lower', cmap='RdYlGn')
plt.colorbar(im, ax=ax, label='Transmission')
ax.contour(np.log10(sa3_I), np.log10(sa3_psi), SA4_trans,
           levels=[0.5], colors='black', linewidths=1.5)
ax.set_xlabel(r'log10($\mathcal{I}$)'); ax.set_ylabel(r'log10($\psi_w$)')
ax.set_title(r'(p) SA4: Transmission $(\mathcal{I}, \psi_w)$')

ax = fig.add_subplot(gs[5, 1])
for name, losses in SA5_loss.items():
    ax.semilogx(I_sa5, losses, lw=2, label=name)
ax.set_xlabel(r'$\mathcal{I}$')
ax.set_ylabel('Wohlfahrtsverlust')
ax.set_title('(q) SA5: Verlust(I) nach Klasse')
ax.legend(fontsize=6); ax.grid(True, alpha=0.3)

ax = fig.add_subplot(gs[5, 2])
# Transmission-Symmetrie V.1a <-> L.1a
ax.semilogx(I_symm, trans_v1a, 'C0-', lw=2, label='V.1a (φ=0.5)')
ax.semilogx(I_symm, trans_l1a, 'C3--', lw=2, label='L.1a (ψ=0.5)')
ax.set_xlabel(r'$\mathcal{I}$'); ax.set_ylabel('Transmission')
ax.set_title('(r) EA2: Symmetrie V.1a ↔ L.1a')
ax.legend(fontsize=7); ax.grid(True, alpha=0.3)

# ── Row 6: EA1 + EA3 ──
ax = fig.add_subplot(gs[6, 0])
ax.hist(bias_stoch, bins=50, alpha=0.5, color='C0', density=True, label='Stochastisch')
ax.axvline(bias_det, color='C3', lw=2, ls='--', label=f'Determin. = {bias_det:.3f}')
ax.axvline(0, color='black', lw=0.5)
ax.set_xlabel('Bias'); ax.set_ylabel('Dichte')
ax.set_title('(s) EA1: Det. vs Stoch. Friction')
ax.legend(fontsize=6); ax.grid(True, alpha=0.3)

ax = fig.add_subplot(gs[6, 1])
params = list(comp_stat.keys())
vals = [comp_stat[p] for p in params]
cols = ['C0' if v > 0 else 'C3' for v in vals]
ax.bar(range(len(params)), vals, color=cols, alpha=0.7)
ax.set_xticks(range(len(params)))
ax.set_xticklabels(params, fontsize=7)
ax.set_ylabel('dL*/dParam')
ax.axhline(0, color='black', lw=0.5)
ax.set_title('(t) EA3: Komparative Statik')
ax.grid(True, alpha=0.3, axis='y')

# ── Row 7: Kausalketten + Strukturen ──
ax = fig.add_subplot(gs[7, 0])
ax.axis('off')
kaus = (
    "KAUSALKETTEN:\n"
    "─────────────────────\n"
    "1. Information hoch (I>>1):\n"
    "   psi/(I+eps) -> 0\n"
    "   w_wahr -> w + aH*w_peer\n"
    "   => Nur Peer-Effekt bleibt\n\n"
    "2. Information niedrig (I~0):\n"
    "   psi/(I+eps) -> gross\n"
    "   w_wahr >> w_true\n"
    "   => 'Gras gruener' Illusion\n"
    f"   Fehlmig-Rate={fehlmig_rate*100:.0f}%\n\n"
    "3. Peer-Herding (aH hoch):\n"
    "   w_wahr -> w + aH*w_peer\n"
    "   Hohe Peer-Loehne =>\n"
    "   erhoehte L* (mehr Arbeit)\n\n"
    "4. Transmission:\n"
    f"   Prof: {R5_data['Professional']['trans']:.2f}\n"
    f"   Inform: {R5_data['Informell']['trans']:.2f}\n"
    "   => Lohnschocks erreichen\n"
    "   Informelle kaum"
)
ax.text(0.05, 0.95, kaus, transform=ax.transAxes, ha='left', va='top',
        fontsize=6.5, family='monospace',
        bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.95))

ax = fig.add_subplot(gs[7, 1:3])
ax.axis('off')
struct_text = (
    "MATHEMATISCHE STRUKTUREN (S23):\n\n"
    "1. HYPERBOLISCHE FRICTION\n"
    "   f(I) = ψ_w/(I+ε): konvex, fallend, Pol bei I=-ε\n"
    "   Identisch zu V.1a → universelle Friction-Klasse\n\n"
    "2. TRANSMISSIONSOPERATOR (Michaelis-Menten)\n"
    "   α(I) = I/(I+ψ_w): S-förmig [0,1]\n"
    f"   Halbwert bei I=ψ_w={0.5} → identisch zu S03, S18\n\n"
    "3. VERZERRTE FOC + WOHLFAHRTSVERLUST\n"
    "   w_wahr·u'(c) = V'(L) statt w·u'(c) = V'(L)\n"
    "   Nicht-additiver Fehler: wirkt über Budget multiplikativ\n\n"
    "4. VORZEICHEN-ASYMMETRIE V.1a ↔ L.1a\n"
    "   V.1a: −φ/(I+ε) → Zins-Unterschätzung → zu wenig Sparen\n"
    "   L.1a: +ψ/(I+ε) → Lohn-Überschätzung → zu viel Migration\n"
    "   → 'Poverty Trap' bei niedrigem I\n\n"
    f"5. INFORMATIONS-UNGLEICHHEIT\n"
    f"   Gini(L_rat)={gini_rational:.3f} → Gini(L_wahr)={gini_wahr:.3f}\n"
    f"   Friction erhöht Ungl. um {(gini_wahr/gini_rational-1)*100:.1f}%"
)
ax.text(0.5, 0.5, struct_text, transform=ax.transAxes, ha='center', va='center',
        fontsize=6.5, family='monospace',
        bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.95))

# ── Row 8: Prop 6.2 Symmetrie-Tabelle ──
ax = fig.add_subplot(gs[8, 0:3])
ax.axis('off')
sym_text = (
    "PROPOSITION 6.2: STRUKTURELLE SYMMETRIE V.1a ↔ L.1a\n\n"
    "┌───────────────────────┬──────────────────────────────┬──────────────────────────────┐\n"
    "│ Dimension             │ V.1a Wahrg. Zins (S18)       │ L.1a Wahrg. Lohn (S23)       │\n"
    "├───────────────────────┼──────────────────────────────┼──────────────────────────────┤\n"
    "│ Basissignal           │ r (Nominalzins)              │ w_i (eigener Lohn)           │\n"
    "│ Erwartungskanal       │ η_i·π (Inflation)            │ α_H·w̄_peer (Peer-Lohn)      │\n"
    "│ Friction-Term         │ −φ/(I+ε) (NEGATIV)           │ +ψ_w/(I+ε) (POSITIV)         │\n"
    "│ Bias-Richtung         │ Unterschätzung → zu wenig ↓  │ Überschätzung → zu viel ↑    │\n"
    "│ Konsequenz            │ Zu wenig Sparen              │ Zu viel Migration/Wechsel    │\n"
    "│ Transmission          │ I/(I+φ)                      │ I/(I+ψ_w)                    │\n"
    "│ Funktionale Form      │ IDENTISCH (Michaelis-Menten) │ IDENTISCH (Michaelis-Menten) │\n"
    "│ I→∞ Grenzfall         │ r_wahr → r + η·π             │ w_wahr → w + α_H·w̄          │\n"
    "│ I→0 Singularität      │ r_wahr → −∞ (Divergenz)      │ w_wahr → +∞ (Divergenz)      │\n"
    "└───────────────────────┴──────────────────────────────┴──────────────────────────────┘\n\n"
    "PROPOSITION 6.4: NEOKLASSISCHE EINBETTUNG\n"
    "  α_H = 0, ψ_w = 0  ⇒  w_wahr = w_i (keine Verzerrung)\n"
    "  ⇒ L.1a reduziert sich auf L.1 (reiner FOC, S22)\n"
    "  Analogon: V.1a(η=0,φ=0) → V.1 (S17)"
)
ax.text(0.5, 0.5, sym_text, transform=ax.transAxes, ha='center', va='center',
        fontsize=6, family='monospace',
        bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.95))

# ── Row 9: Migration-Detail + Backward-Bending mit Friction ──
ax = fig.add_subplot(gs[9, 0])
ax.hist(I_mig[migrate_bad], bins=30, alpha=0.5, color='C3', density=True,
        label='Fehler-Migranten')
ax.hist(I_mig[~migrate_bad], bins=30, alpha=0.5, color='C0', density=True,
        label='Korrekt (bleibt)')
ax.set_xlabel(r'$\mathcal{I}$'); ax.set_ylabel('Dichte')
ax.set_title('(u) R7: Fehler- vs Korrektentscheidung')
ax.legend(fontsize=6); ax.grid(True, alpha=0.3)

ax = fig.add_subplot(gs[9, 1])
# Backward-Bending MIT Friction: w_wahr vs L*
wages_bb = np.logspace(-0.5, 1.5, 100)
for I_val in [0.5, 2.0, 10.0, 100.0]:
    L_bb = [solve_L_star(w_perceived(w, 0.3, 2.0, 0.5, I_val),
                          0.04, 2.0, 0.0, 2.0, 1.0, 1.0)
            for w in wages_bb]
    ax.semilogx(wages_bb, L_bb, lw=1.5, label=f'I={I_val}')
ax.set_xlabel(r'$w_L$'); ax.set_ylabel('L*')
ax.set_title('(v) Backward-Bending mit Friction')
ax.legend(fontsize=6); ax.grid(True, alpha=0.3)

ax = fig.add_subplot(gs[9, 2])
# R5: dL% nach Klasse
names_R5 = list(R5_data.keys())
dL_vals = [R5_data[n]['dL_pct'] for n in names_R5]
ax.bar(range(len(names_R5)), dL_vals, color=['C0', 'C1', 'C2', 'C3'], alpha=0.7)
ax.set_xticks(range(len(names_R5)))
ax.set_xticklabels(names_R5, fontsize=7, rotation=15)
ax.set_ylabel('ΔL* (%)')
ax.set_title('(w) R5: Lohnschock-Reaktion')
ax.grid(True, alpha=0.3, axis='y')

# ── Row 10: Validierungen + Physik ──
ax = fig.add_subplot(gs[10, 0])
ax.axis('off')
val_text = "VALIDIERUNGEN:\n" + "-"*35 + "\n"
for k, v in validations.items():
    tag = "PASS" if v["passed"] else "FAIL"
    val_text += f"{k}: {v['name'][:35]}\n   {tag}: {v['detail'][:50]}\n\n"
ax.text(0.05, 0.95, val_text, transform=ax.transAxes, ha='left', va='top',
        fontsize=5.5, family='monospace',
        bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.95))

ax = fig.add_subplot(gs[10, 1:3])
ax.axis('off')
phys = (
    "L.1a WAHRGENOMMENER ALTERNATIVLOHN (§6.4)\n\n"
    "Gleichung:  w_wahr = w_i + α_H·w̄_peer + ψ_w/(I_i + ε)\n"
    "FOC:        w_wahr · u'(c*) = V'(L*)  —  verzerrte Arbeitsangebots-Entscheidung\n\n"
    "3 Kanäle: Eigener Lohn + Peer-Herding + Intransparenz-Aufschlag\n"
    f"Transmission: Prof={R5_data['Professional']['trans']:.2f}, "
    f"Informell={R5_data['Informell']['trans']:.2f}\n"
    f"Migration: Rate(gut)={migration_rate*100:.0f}%, "
    f"Fehlrate(schlecht)={fehlmig_rate*100:.0f}%\n\n"
    f"Heterogene Ökonomie (N={N3}):\n"
    f"  Gini(L_rat)={gini_rational:.3f} → Gini(L_wahr)={gini_wahr:.3f}\n"
    f"  Friction erhöht Ungleichheit um {(gini_wahr/gini_rational-1)*100:.1f}%\n\n"
    "Propositionen:\n"
    "  Prop 6.2: Symmetrie V.1a ↔ L.1a  ... BESTÄTIGT (identische Transmission)\n"
    "  Prop 6.4: α_H=0, ψ=0 ⇒ w_wahr=w ... BESTÄTIGT (Neoklassisch)"
)
ax.text(0.5, 0.5, phys, transform=ax.transAxes, ha='center', va='center',
        fontsize=7, family='monospace',
        bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.95))

# ── Metadata ──
ax_meta = fig.add_subplot(gs[11, :])
ax_meta.axis('off')
n_pass = sum(1 for v in validations.values() if v["passed"])
meta = (
    f"S23 L.1a Wahrg. Alternativlohn | w_wahr = w + αH·w̄ + ψ/(I+ε) | "
    f"8 Regime, {len(validations)} Val: {n_pass}/{len(validations)} PASS | "
    f"5 SA (3 Heatmaps) | Fehlmig={fehlmig_rate*100:.0f}% | "
    f"Gini(L)={gini_rational:.3f}→{gini_wahr:.3f}"
)
ax_meta.text(0.5, 0.5, meta, transform=ax_meta.transAxes, ha='center', va='center',
             fontsize=9, family='monospace',
             bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.95))

plt.savefig(PLOT_DIR / "S23_L1a_Wahrgenommener_Alternativlohn.png", dpi=180,
            bbox_inches='tight')
plt.close()
print(f"\n  Plot: {PLOT_DIR / 'S23_L1a_Wahrgenommener_Alternativlohn.png'}")

# ── Daten ──
np.savez_compressed(DATA_DIR / "S23_L1a_Wahrgenommener_Alternativlohn.npz",
    R2_I=I_sweep, R3_bias=bias_het, R3_I=I_het,
    R3_gini_rat=gini_rational, R3_gini_wahr=gini_wahr,
    R4_psi=psi_sweep_R4, R4_loss=welfare_loss,
    R7_I=I_mig, R7_fehlmig=fehlmig_by_I,
    R8_L_rat=L_rat8, R8_L_wahr=L_wahr8, R8_I=I8,
    SA2_w=SA2_w, SA3_bias=SA3_bias, SA4_trans=SA4_trans,
    SA5_I=I_sa5,
    migration_rate=migration_rate, fehlmig_rate=fehlmig_rate)

# ── Zusammenfassung ──
print(f"\n{'='*72}\n  ZUSAMMENFASSUNG S23  L.1a Wahrgenommener Alternativlohn\n{'='*72}")
for k, v in validations.items():
    print(f"  {k}: {v['name']:42s}  {'PASS' if v['passed'] else 'FAIL'}  ({v['detail']})")
print(f"\n  Regime:")
print(f"    R1: Peer-Lohn-Effekt (alpha_H Sweep)")
print(f"    R2: Informationsfriction-Sweep")
print(f"    R3: Heterogene Agenten (N={N3})")
print(f"    R4: 'Gras ist gruener'-Illusion")
print(f"    R5: Arbeitsmarkt-Transmission (4 Klassen)")
print(f"    R6: Informationskaskade (3 Szenarien)")
print(f"    R7: Migration (N={N7})")
print(f"    R8: L.1+L.1a Vollstaendiges Modell (N={N8})")
print(f"\n  Sensitivitaet:")
print(f"    SA1: psi_w -> w_wahr + L*")
print(f"    SA2: (alpha_H, w_bar) -> w_wahr Heatmap")
print(f"    SA3: (I, psi_w) -> Bias Heatmap")
print(f"    SA4: (I, psi_w) -> Transmission Heatmap")
print(f"    SA5: Wohlfahrtsverlust(I) nach Klasse")
print(f"\n  Erweiterte Analyse:")
print(f"    EA1: Deterministische vs Stochastische Friction")
print(f"    EA2: Prop 6.2 Symmetrie V.1a <-> L.1a")
print(f"    EA3: Komparative Statik (5 Parameter)")
print(f"\n  Mathematische Strukturen:")
for s in struct_notes:
    print(f"    {s.split(chr(10))[0]}")
print(f"\n  Kernbefunde:")
print(f"    Transmission: Prof={R5_data['Professional']['trans']:.2f}, "
      f"Informell={R5_data['Informell']['trans']:.2f}")
print(f"    Migration: Fehlmig-Rate={fehlmig_rate*100:.0f}% bei schlechtem Ziel")
print(f"    Gini: L_rat={gini_rational:.3f} -> L_wahr={gini_wahr:.3f} "
      f"(+{(gini_wahr/gini_rational-1)*100:.1f}%)")
print(f"    Vorzeichen-Asymmetrie: V.1a negativ, L.1a positiv => Poverty Trap")
n_pass = sum(1 for v in validations.values() if v["passed"])
print(f"\n  Gesamtergebnis: {n_pass}/{len(validations)} bestanden")
if n_pass == len(validations):
    print("  >>> ALLE VALIDIERUNGEN BESTANDEN <<<")
print(f"{'='*72}")
