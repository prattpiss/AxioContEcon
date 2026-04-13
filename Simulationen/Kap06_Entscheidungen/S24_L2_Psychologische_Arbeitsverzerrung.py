"""
S24 – Psychologische Arbeitsverzerrung L.2  (§6.4)
====================================================
Gleichung L.2:
    Psi_L(L_i, L_i*, L_bar, I_i^job, H_i)

Axiomatische Eigenschaften:
  1. Rueckkehr zum Optimum: dPsi/d(L*-L) > 0
  2. Ueberlastungsschaden (Burnout): Psi_L < 0 fuer L >> L_bar
  3. Intrinsische Motivation: dPsi/dI^job > 0 (Jobidentifikation erhoeht Arbeit)
  4. Gesundheitskopplung: dPsi/dH > 0
  5. Nullpunkt: Psi_L(L*, L*, L_bar, 0, H_norm) = 0

Strukturelle Symmetrie zu V.2 (S19, Prop 6.2):
  V.2: Referenzpunkt + Verlustaversion + Relative Deprivation
  L.2: Rueckkehr + Burnout-Asymmetrie + Intrinsische Motivation

Zentraler Unterschied:
  V.2: Information DAEMPFT Psychologie (I->inf => Psi_c->0)
  L.2: Information hat DUALE Rolle:
       - Burnout-Term gedaempft durch I (wie V.2)
       - Intrinsische Motivation VERSTAERKT durch I (einzigartig!)
       -> nicht-monotone I-Abhaengigkeit

8 Regime, 8 Validierungen, 5 Sensitivitaetsanalysen, 3 Erw. Analysen
"""

import sys, io, warnings
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

def Psi_L(L, L_star, L_bar, I_job, H,
          lam_B=2.25, kappa_ref=0.3, kappa_I=1.2, psi_I=8.5,
          kappa_info_burn=1.0, Psi_max=2.0, H_norm=1.0):
    """
    L.2 Psychologische Arbeitsverzerrung.

    Psi_L = Psi_burnout + Psi_intrinsic

    Psi_burnout:
        x = L* - L  (positiv wenn L < L*: unter Referenz)
        v(x) = lam_B * x   fuer x >= 0  (L < L*: Verlust, staerker)
               x            fuer x < 0    (L > L*: Gewinn, schwaecher)
        Aber hier: Burnout = L > L* ist der Verlust (Ueberlastung)!
        Also: x = L* - L
          x > 0: L < L* -> Unterarbeit -> schwache Anziehung nach oben (Gewinn)
          x < 0: L > L* -> Ueberarbeit -> starke Rueckziehung (Burnout, Verlust)

        info_burn = 1/(1 + kappa_info * I_job) -> rational agents avoid overwork

    Psi_intrinsic:
        kappa_I * I_job/(I_job + psi_I) * (H/H_norm)
        -> Michaelis-Menten in I_job, linear in H
        -> At I_job=0: no motivation boost
        -> At I_job->inf: saturates at kappa_I * H/H_norm

    Resultat beschraenkt auf [-Psi_max, +Psi_max]
    """
    L = np.asarray(L, dtype=float)
    L_star = np.asarray(L_star, dtype=float)
    I_job = np.asarray(I_job, dtype=float)
    H = np.asarray(H, dtype=float)

    x = L_star - L  # positiv wenn L < L* (Unterarbeit)

    # Prospect Theory Wertfunktion (analog V.2, aber Burnout-Asymmetrie)
    # x > 0: L < L* -> unter Referenz -> schwache Anziehung hoch (Gewinn-Seite)
    # x < 0: L > L* -> ueber Referenz -> starke Rueckziehung (Burnout, Verlust-Seite)
    v = np.where(x >= 0, x, lam_B * x)

    # Informations-Modulation des Burnout-Terms: I_job->inf => rationale Agenten
    # vermeiden Ueberarbeit -> Burnout-Term verschwindet
    info_burn = 1.0 / (1.0 + kappa_info_burn * np.maximum(I_job, 0.0))

    psi_burnout = kappa_ref * v * info_burn

    # Intrinsische Motivation: I_job VERSTAERKT (nicht daempft!)
    # Michaelis-Menten: I/(I + psi_I), gesaettigt bei 1
    # Multipliziert mit H (Humankapital-Kopplung)
    I_safe = np.maximum(I_job, 0.0)
    psi_intrinsic = kappa_I * I_safe / (I_safe + psi_I) * (H / H_norm)

    psi_total = psi_burnout + psi_intrinsic

    return np.clip(psi_total, -Psi_max, Psi_max)


def reference_dynamics_L(L_star, L, lambda_adapt=0.1):
    """dL*/dt = lambda_adapt * (L - L*) — Arbeitsreferenz passt sich an (langsamer als Konsum!)"""
    return lambda_adapt * (L - L_star)


def gini(x):
    """Gini-Koeffizient"""
    x = np.sort(np.abs(np.asarray(x, dtype=float)))
    n = len(x)
    if n == 0 or x.sum() == 0:
        return 0.0
    return float((2 * np.sum(np.arange(1, n+1) * x) - (n + 1) * x.sum()) / (n * x.sum()))


def solve_L_star_rational(w, r, K, pi, gamma, eta):
    """L.1 (S22) rational: w*u'(c) = V'(L), CRRA+Isoelastic"""
    # u'(c) = c^{-gamma}, V'(L) = L^eta
    # w * (w*L + r*K + pi)^{-gamma} = L^eta
    from scipy.optimize import brentq
    def foc(L_v):
        c = w * L_v + r * K + pi
        if c <= 0:
            return -1e10
        return w * c**(-gamma) - L_v**eta
    try:
        return brentq(foc, 1e-6, 0.999, xtol=1e-12)
    except Exception:
        return 0.5


print("=" * 72)
print("  S24  L.2  Psychologische Arbeitsverzerrung")
print("=" * 72)

results = {}
T = 50.0
t_eval = np.linspace(0, T, 2001)

# ══════════════════════════════════════════════════════════════════════
# R1: Referenzpunktanziehung — Basis
# ══════════════════════════════════════════════════════════════════════
print("\n  R1: Referenzpunktanziehung")

L_range = np.linspace(0.1, 0.9, 200)
L_star_R1 = 0.5
# I_job=0, H=H_norm -> intrinsische Motivation = 0, nur Referenzpunkt
psi_R1 = Psi_L(L_range, L_star_R1, 0.5, 0.0, 1.0)

below = L_range < L_star_R1
above = L_range > L_star_R1
prop1_a = np.all(psi_R1[below] > 0)  # unter Referenz -> positiv (hoch ziehen)
prop1_b = np.all(psi_R1[above] < 0)  # ueber Referenz -> negativ (Burnout runter)
print(f"    Psi>0 fuer L<L*: {prop1_a}, Psi<0 fuer L>L*: {prop1_b}")
print(f"    Psi(L=0.2)={Psi_L(0.2, 0.5, 0.5, 0, 1):.4f}, "
      f"Psi(L=0.8)={Psi_L(0.8, 0.5, 0.5, 0, 1):.4f}")

results["R1"] = dict(label="R1: Referenzpunktanziehung",
                     L=L_range, psi=psi_R1, L_star=L_star_R1)

# ══════════════════════════════════════════════════════════════════════
# R2: Burnout-Asymmetrie (lam_B=2.25)
# ══════════════════════════════════════════════════════════════════════
print("\n  R2: Burnout-Asymmetrie (lam_B=2.25)")

d = 0.15
L_star_R2 = 0.5
# I_job=0 -> no intrinsic, pure reference + burnout
psi_under = Psi_L(L_star_R2 - d, L_star_R2, 0.5, 0.0, 1.0)  # L < L*: Unterarbeit
psi_over  = Psi_L(L_star_R2 + d, L_star_R2, 0.5, 0.0, 1.0)  # L > L*: Ueberarbeit
ratio_burn = abs(psi_over) / abs(psi_under)

print(f"    Psi(Unterarbeit, d={d})={psi_under:+.4f}")
print(f"    Psi(Ueberarbeit, d={d})={psi_over:+.4f}")
print(f"    |Burnout/Unterarbeit| = {ratio_burn:.2f} (soll ~{2.25:.2f})")

d_sweep = np.linspace(0.01, 0.35, 100)
psi_under_sw = np.array([Psi_L(L_star_R2 - d_, L_star_R2, 0.5, 0, 1) for d_ in d_sweep])
psi_over_sw  = np.array([Psi_L(L_star_R2 + d_, L_star_R2, 0.5, 0, 1) for d_ in d_sweep])

results["R2"] = dict(label="R2: Burnout-Asymmetrie",
                     d=d_sweep, psi_under=psi_under_sw, psi_over=psi_over_sw,
                     ratio=ratio_burn)

# ══════════════════════════════════════════════════════════════════════
# R3: Dynamische Referenzpunkt-Adaptation
# ══════════════════════════════════════════════════════════════════════
print("\n  R3: Referenzpunkt-Adaptation")

lambda_adapt_vals = [0.02, 0.05, 0.1, 0.2]

R3_data = {}
for lam_a in lambda_adapt_vals:
    def rhs_R3(t, y, lam_a=lam_a):
        L_v, L_star_v = y
        alpha_L = 0.5   # Anpassungsgeschwindigkeit zum rationalen L*
        L_target = 0.5   # wahres L*
        # Rational pull + Psi_L (I_job=0, H=1 -> nur Reference)
        psi = Psi_L(L_v, L_star_v, 0.5, 0.0, 1.0)
        dLdt = alpha_L * (L_target - L_v) + psi
        dLs_dt = reference_dynamics_L(L_star_v, L_v, lam_a)
        return [dLdt, dLs_dt]

    sol = solve_ivp(rhs_R3, [0, T], [0.75, 0.5], t_eval=t_eval,
                    method='RK45', rtol=1e-8, atol=1e-10)
    L_t = sol.y[0]
    Ls_t = sol.y[1]
    psi_t = Psi_L(L_t, Ls_t, 0.5, 0, 1)
    gap = L_t - Ls_t
    R3_data[lam_a] = dict(t=sol.t, L=L_t, L_star=Ls_t, psi=psi_t, gap=gap)
    print(f"    lam_a={lam_a:.2f}: gap(0)={gap[0]:+.3f}, gap(T)={gap[-1]:+.5f}, "
          f"L(T)={L_t[-1]:.4f}, L*(T)={Ls_t[-1]:.4f}")

results["R3"] = dict(label="R3: Referenzpunkt-Adaptation", data=R3_data)

# ══════════════════════════════════════════════════════════════════════
# R4: Intrinsische Motivation (I_job Sweep)
# ══════════════════════════════════════════════════════════════════════
print("\n  R4: Intrinsische Motivation")

I_job_sweep = np.logspace(-2, 2, 300)
L_R4 = 0.5  # genau am Referenzpunkt
L_star_R4 = 0.5

# Bei L=L*: Burnout-Term = 0. Nur Motivation wirkt.
H_vals = [0.5, 1.0, 2.0, 3.0]
R4_data = {}
for H_v in H_vals:
    psi_motiv = Psi_L(L_R4, L_star_R4, 0.5, I_job_sweep, H_v)
    R4_data[H_v] = psi_motiv
    print(f"    H={H_v:.1f}: Psi(I=0.01)={psi_motiv[0]:.4f}, "
          f"Psi(I=10)={psi_motiv[200]:.4f}, Psi(I=100)={psi_motiv[-1]:.4f}")

results["R4"] = dict(label="R4: Intrinsische Motivation",
                     I_job=I_job_sweep, data=R4_data)

# ══════════════════════════════════════════════════════════════════════
# R5: Informations-Dualitaet (I daempft Burnout, verstaerkt Motivation)
# ══════════════════════════════════════════════════════════════════════
print("\n  R5: Informations-Dualitaet")

I_sweep_R5 = np.logspace(-2, 3, 300)
L_over = 0.7    # Ueberarbeit (L > L*=0.5) -> Burnout aktiv
L_star_R5 = 0.5

psi_total_R5 = Psi_L(L_over, L_star_R5, 0.5, I_sweep_R5, 1.0)

# Decompose: Burnout-Term only (kappa_I=0)
psi_burn_only = Psi_L(L_over, L_star_R5, 0.5, I_sweep_R5, 1.0, kappa_I=0.0)
# Intrinsic-Term only (kappa_ref=0)
psi_intr_only = Psi_L(L_over, L_star_R5, 0.5, I_sweep_R5, 1.0, kappa_ref=0.0)

# Check: at some I_job, total Psi switches sign (burnout → motivation dominiert)
sign_changes = np.where(np.diff(np.sign(psi_total_R5)))[0]
if len(sign_changes) > 0:
    I_cross = I_sweep_R5[sign_changes[0]]
    print(f"    Vorzeichenwechsel bei I_job={I_cross:.2f} (Burnout→Motivation)")
else:
    I_cross = None
    print(f"    Kein Vorzeichenwechsel im Bereich")

print(f"    Psi_total(I=0.01)={psi_total_R5[0]:.4f}, Psi_total(I=100)={psi_total_R5[-1]:.4f}")
print(f"    Psi_burn(I=0.01)={psi_burn_only[0]:.4f}, Psi_burn(I=100)={psi_burn_only[-1]:.4f}")
print(f"    Psi_intr(I=0.01)={psi_intr_only[0]:.4f}, Psi_intr(I=100)={psi_intr_only[-1]:.4f}")

results["R5"] = dict(label="R5: Info-Dualitaet",
                     I=I_sweep_R5, psi_total=psi_total_R5,
                     psi_burn=psi_burn_only, psi_intr=psi_intr_only,
                     I_cross=I_cross)

# ══════════════════════════════════════════════════════════════════════
# R6: Heterogene Agenten (N=300)
# ══════════════════════════════════════════════════════════════════════
print("\n  R6: Heterogene Agenten (N=300)")

N_het = 300
# Heterogene Anfangsbedingungen
L0_het = np.random.uniform(0.2, 0.8, N_het)
Ls0_het = np.random.uniform(0.35, 0.65, N_het)  # initiale Referenz
I_job_het = np.random.lognormal(np.log(3), 1.0, N_het)
I_job_het = np.clip(I_job_het, 0.1, 100)
H_het = np.random.lognormal(np.log(1.0), 0.5, N_het)
H_het = np.clip(H_het, 0.3, 5.0)
alpha_L_het = 0.3  # Rational-Konvergenzrate
L_target_het = np.random.uniform(0.35, 0.65, N_het)  # rationale L*
lambda_adapt_het = 0.1

dt = T / 2000
N_steps = 2000
L_hist = np.zeros((N_het, N_steps + 1))
Ls_hist = np.zeros((N_het, N_steps + 1))
L_hist[:, 0] = L0_het
Ls_hist[:, 0] = Ls0_het
gini_hist = np.zeros(N_steps + 1)
gini_hist[0] = gini(L0_het)

for step in range(N_steps):
    L_now = L_hist[:, step]
    Ls_now = Ls_hist[:, step]
    L_bar = np.mean(L_now)

    psi = Psi_L(L_now, Ls_now, L_bar, I_job_het, H_het)
    dL = (alpha_L_het * (L_target_het - L_now) + psi) * dt
    dLs = reference_dynamics_L(Ls_now, L_now, lambda_adapt_het) * dt

    L_hist[:, step + 1] = np.clip(L_now + dL, 0.01, 0.99)
    Ls_hist[:, step + 1] = np.clip(Ls_now + dLs, 0.01, 0.99)
    gini_hist[step] = gini(L_hist[:, step])

gini_hist[-1] = gini(L_hist[:, -1])
t_het = np.linspace(0, T, N_steps + 1)

gini_0 = gini_hist[0]
gini_T = gini_hist[-1]

# Intrinsische Motivation erhoeht Arbeitsangebot fuer high-I agents
L_final = L_hist[:, -1]
corr_I_L = np.corrcoef(I_job_het, L_final)[0, 1]
corr_H_L = np.corrcoef(H_het, L_final)[0, 1]

R6_data = dict(N=N_het, L=L_hist, L_star=Ls_hist, t=t_het,
               gini=gini_hist, I_job=I_job_het, H=H_het)
results["R6"] = dict(label="R6: Heterogene Agenten", data=R6_data)
print(f"    Gini(0)={gini_0:.3f}, Gini(T)={gini_T:.3f}")
print(f"    L_mean(0)={L0_het.mean():.3f}, L_mean(T)={L_final.mean():.3f}")
print(f"    Corr(I_job, L_final)={corr_I_L:.3f}, Corr(H, L_final)={corr_H_L:.3f}")

# ══════════════════════════════════════════════════════════════════════
# R7: Negativer Arbeitsschock + Erholung
# ══════════════════════════════════════════════════════════════════════
print("\n  R7: Negativer Arbeitsschock + Erholung")

T_R7 = 80.0
t_eval_R7 = np.linspace(0, T_R7, 3001)
shock_t = 15.0
shock_mag = -0.4  # L: 0.5 -> 0.1 (Jobverlust)

lam_B_vals_R7 = [2.25, 1.0, 4.0]  # Standard, neutral, extrem

R7_data = {}
for lam_B in lam_B_vals_R7:
    def rhs_R7(t, y, lam_v=lam_B):
        L_v, Ls_v = y
        L_v = np.clip(L_v, 0.01, 0.99)
        alpha_L = 0.3
        L_target = 0.5
        # I_job=0: reiner Burnout/Referenz-Test ohne Motivation
        psi = Psi_L(L_v, Ls_v, 0.5, 0.0, 1.0, lam_B=lam_v)
        dLdt = alpha_L * (L_target - L_v) + psi
        dLs_dt = reference_dynamics_L(Ls_v, L_v, 0.1)
        return [dLdt, dLs_dt]

    # Phase 1: bis Schock
    sol1 = solve_ivp(rhs_R7, [0, shock_t], [0.5, 0.5],
                     t_eval=np.linspace(0, shock_t, 500),
                     method='RK45', rtol=1e-8, atol=1e-10)

    # Phase 2: nach Schock
    L_after = max(sol1.y[0][-1] + shock_mag, 0.05)
    Ls_after = sol1.y[1][-1]
    sol2 = solve_ivp(rhs_R7, [shock_t, T_R7], [L_after, Ls_after],
                     t_eval=np.linspace(shock_t, T_R7, 2501),
                     method='RK45', rtol=1e-8, atol=1e-10)

    t_full = np.concatenate([sol1.t, sol2.t])
    L_full = np.concatenate([sol1.y[0], sol2.y[0]])
    Ls_full = np.concatenate([sol1.y[1], sol2.y[1]])
    psi_full = Psi_L(L_full, Ls_full, 0.5, 0.0, 1.0, lam_B=lam_B)

    R7_data[lam_B] = dict(t=t_full, L=L_full, L_star=Ls_full, psi=psi_full)

    # Erholungszeit: wann ist L wieder auf 90% von L_target?
    post_L = sol2.y[0]
    idx_recov = np.where(post_L > 0.45)[0]  # 90% von 0.5
    t_recov = sol2.t[idx_recov[0]] - shock_t if len(idx_recov) > 0 else float('inf')
    print(f"    lam_B={lam_B:.2f}: L_min={min(sol2.y[0]):.3f}, "
          f"L(T)={sol2.y[0][-1]:.3f}, t_recov(90%)={t_recov:.1f}")

results["R7"] = dict(label="R7: Arbeitsschock", data=R7_data, shock_t=shock_t)

# ══════════════════════════════════════════════════════════════════════
# R8: Drei-Ebenen-Vergleich (L.1 rational vs L.1+L.2)
# ══════════════════════════════════════════════════════════════════════
print("\n  R8: Drei-Ebenen-Vergleich")

def sim_levels(L0, Ls0, L_target, I_job, H, include_psi, T=50, dt=0.025):
    """Simuliere dL/dt = alpha_L*(L_target-L) [+ Psi_L]"""
    steps = int(T / dt)
    L_arr = np.zeros(steps + 1)
    Ls_arr = np.zeros(steps + 1)
    L_arr[0] = L0
    Ls_arr[0] = Ls0
    alpha_L = 0.3
    for s in range(steps):
        L_v = max(L_arr[s], 0.01)
        Ls_v = Ls_arr[s]
        dL = alpha_L * (L_target - L_v)
        if include_psi:
            dL += Psi_L(L_v, Ls_v, 0.5, I_job, H)
        L_arr[s+1] = np.clip(L_v + dL * dt, 0.01, 0.99)
        Ls_arr[s+1] = max(Ls_v + reference_dynamics_L(Ls_v, L_v, 0.1) * dt, 0.01)
    return np.linspace(0, T, steps+1), L_arr, Ls_arr

configs_R8 = {
    "L.1 Rational (kein Psi)": dict(include_psi=False, I_job=0, H=1.0),
    "L.1+L.2 (I_job=0, H=1)": dict(include_psi=True, I_job=0.0, H=1.0),
    "L.1+L.2 (I_job=5, H=1)": dict(include_psi=True, I_job=5.0, H=1.0),
    "L.1+L.2 (I_job=20, H=1)": dict(include_psi=True, I_job=20.0, H=1.0),
    "L.1+L.2 (I_job=5, H=3)": dict(include_psi=True, I_job=5.0, H=3.0),
}

R8_data = {}
for name, cfg in configs_R8.items():
    t_v, L_v, Ls_v = sim_levels(0.3, 0.5, 0.5, cfg["I_job"], cfg["H"], cfg["include_psi"])
    R8_data[name] = dict(t=t_v, L=L_v, L_star=Ls_v)
    print(f"    {name:35s}: L(T)={L_v[-1]:.4f}")

results["R8"] = dict(label="R8: Drei-Ebenen-Vergleich", data=R8_data)


# ══════════════════════════════════════════════════════════════════════
# VALIDIERUNGEN
# ══════════════════════════════════════════════════════════════════════

validations = {}
print(f"\n{'='*72}\n  VALIDIERUNGEN\n{'='*72}")

# V1: Nullpunkt — Psi_L(L*, L*, L_bar, 0, H_norm) = 0
v1_val = Psi_L(0.5, 0.5, 0.5, 0.0, 1.0)
v1_pass = abs(v1_val) < 1e-15
validations["V1"] = dict(name="Nullpunkt: Psi_L(L*,L*,L_bar,0,H_norm)=0",
                         passed=v1_pass, detail=f"|Psi|={abs(v1_val):.2e}")
print(f"  V1: {'PASS' if v1_pass else 'FAIL'} ({validations['V1']['detail']})")

# V2: Referenzpunktanziehung — Psi>0 fuer L<L*, Psi<0 fuer L>L* (bei I_job=0)
L_test_lo = np.linspace(0.05, 0.49, 100)
L_test_hi = np.linspace(0.51, 0.95, 100)
psi_lo = Psi_L(L_test_lo, 0.5, 0.5, 0.0, 1.0)
psi_hi = Psi_L(L_test_hi, 0.5, 0.5, 0.0, 1.0)
v2_pass = bool(np.all(psi_lo > 0) and np.all(psi_hi < 0))
validations["V2"] = dict(name="Referenzpunkt: Psi>0(L<L*), Psi<0(L>L*)",
                         passed=v2_pass,
                         detail=f"below_pos={np.all(psi_lo > 0)}, above_neg={np.all(psi_hi < 0)}")
print(f"  V2: {'PASS' if v2_pass else 'FAIL'} ({validations['V2']['detail']})")

# V3: Burnout-Asymmetrie — |Psi(L>L*)| > |Psi(L<L*)| bei gleichem Abstand (I_job=0)
d_test = np.array([0.05, 0.1, 0.15, 0.25, 0.35])
under_vals = np.abs(Psi_L(0.5 - d_test, 0.5, 0.5, 0, 1))
over_vals  = np.abs(Psi_L(0.5 + d_test, 0.5, 0.5, 0, 1))
v3_pass = bool(np.all(over_vals > under_vals))
v3_ratio = over_vals / np.maximum(under_vals, 1e-15)
validations["V3"] = dict(name="Burnout: |Psi(L>L*)|>|Psi(L<L*)|",
                         passed=v3_pass,
                         detail=f"ratios={[f'{r:.2f}' for r in v3_ratio]}")
print(f"  V3: {'PASS' if v3_pass else 'FAIL'} ({validations['V3']['detail']})")

# V4: Beschraenktheit — |Psi| <= Psi_max
L_extreme = np.array([0.01, 0.05, 0.95, 0.99])
psi_extreme = Psi_L(L_extreme, 0.5, 0.5, 100.0, 5.0)
v4_pass = bool(np.all(np.abs(psi_extreme) <= 2.0 + 1e-10))
validations["V4"] = dict(name="Beschraenktheit: |Psi|<=Psi_max",
                         passed=v4_pass,
                         detail=f"max|Psi|={np.max(np.abs(psi_extreme)):.4f}, Psi_max=2.0")
print(f"  V4: {'PASS' if v4_pass else 'FAIL'} ({validations['V4']['detail']})")

# V5: Info-Dualitaet — Burnout: I->inf daempft; Motivation: I->inf verstaerkt
# a) Burnout only: should decrease with I
psi_burn_lo = abs(Psi_L(0.7, 0.5, 0.5, 0.01, 1.0, kappa_I=0))
psi_burn_hi = abs(Psi_L(0.7, 0.5, 0.5, 1e6,  1.0, kappa_I=0))
burn_decreases = psi_burn_lo > psi_burn_hi
# b) Intrinsic only: should increase with I
psi_intr_lo = Psi_L(0.5, 0.5, 0.5, 0.01, 1.0, kappa_ref=0)
psi_intr_hi = Psi_L(0.5, 0.5, 0.5, 1e6,  1.0, kappa_ref=0)
intr_increases = psi_intr_hi > psi_intr_lo
v5_pass = bool(burn_decreases and intr_increases)
validations["V5"] = dict(name="Info-Dualitaet: Burnout sinkt, Motivation steigt",
                         passed=v5_pass,
                         detail=f"burn_dec={burn_decreases}({psi_burn_lo:.4f}->{psi_burn_hi:.6f}), "
                                f"intr_inc={intr_increases}({psi_intr_lo:.4f}->{psi_intr_hi:.4f})")
print(f"  V5: {'PASS' if v5_pass else 'FAIL'} ({validations['V5']['detail']})")

# V6: Gesundheitskopplung — dPsi/dH > 0 monoton
H_test = np.linspace(0.3, 5.0, 100)
psi_H = Psi_L(0.5, 0.5, 0.5, 10.0, H_test)  # Am Referenzpunkt: nur Motivation
v6_pass = bool(np.all(np.diff(psi_H) > -1e-12))
validations["V6"] = dict(name="Gesundheitskopplung: dPsi/dH > 0",
                         passed=v6_pass,
                         detail=f"monoton={v6_pass}, Psi(H=0.3)={psi_H[0]:.4f}, Psi(H=5)={psi_H[-1]:.4f}")
print(f"  V6: {'PASS' if v6_pass else 'FAIL'} ({validations['V6']['detail']})")

# V7: Prop 6.2 Symmetrie V.2 <-> L.2 — Funktionale Struktur identisch
# Test: Burnout-Ratio = Lambda exakt (wie V.2 Verlustaversion-Ratio = Lambda)
d_small = 0.001
psi_over_v7 = abs(Psi_L(0.5 + d_small, 0.5, 0.5, 0, 1))
psi_under_v7 = abs(Psi_L(0.5 - d_small, 0.5, 0.5, 0, 1))
ratio_v7 = psi_over_v7 / psi_under_v7
v7_pass = abs(ratio_v7 - 2.25) < 0.01
validations["V7"] = dict(name="Prop 6.2: Burnout-Ratio=lam_B exakt",
                         passed=v7_pass,
                         detail=f"ratio={ratio_v7:.4f} (soll 2.25)")
print(f"  V7: {'PASS' if v7_pass else 'FAIL'} ({validations['V7']['detail']})")

# V8: Schock-Erholung — L konvergiert zurueck nach Schock
R7_std = R7_data[2.25]
L_end_R7 = R7_std["L"][-1]
Ls_end_R7 = R7_std["L_star"][-1]
gap_end = abs(L_end_R7 - 0.5) / 0.5  # Abstand vom Ziel
v8_pass = gap_end < 0.05
validations["V8"] = dict(name="Schock-Erholung: L konvergiert (<5% Abweichung)",
                         passed=v8_pass,
                         detail=f"|L(T)-L_target|/L_target={gap_end:.4f}")
print(f"  V8: {'PASS' if v8_pass else 'FAIL'} ({validations['V8']['detail']})")


# ══════════════════════════════════════════════════════════════════════
# SENSITIVITAETSANALYSEN
# ══════════════════════════════════════════════════════════════════════

print(f"\n{'='*72}\n  SENSITIVITAETSANALYSEN\n{'='*72}")

# SA1: lam_B Sweep (Burnout-Sensitivitaet)
lam_B_sa = np.linspace(1.0, 5.0, 200)
d_sa1 = 0.2
psi_over_sa1  = np.array([abs(Psi_L(0.7, 0.5, 0.5, 0, 1, lam_B=l)) for l in lam_B_sa])
psi_under_sa1 = np.array([abs(Psi_L(0.3, 0.5, 0.5, 0, 1, lam_B=l)) for l in lam_B_sa])
results["SA1"] = dict(lam_B=lam_B_sa, psi_over=psi_over_sa1, psi_under=psi_under_sa1)
print(f"  SA1: lam_B-Sweep: |Psi_over|(lam=1)={psi_over_sa1[0]:.4f}, "
      f"|Psi_over|(lam=5)={psi_over_sa1[-1]:.4f}")

# SA2: kappa_I Sweep (Motivation-Staerke)
kappa_I_sa = np.linspace(0.1, 3.0, 200)
psi_motiv_sa = np.array([Psi_L(0.5, 0.5, 0.5, 10.0, 1.0, kappa_I=k) for k in kappa_I_sa])
psi_motiv_sa_H3 = np.array([Psi_L(0.5, 0.5, 0.5, 10.0, 3.0, kappa_I=k) for k in kappa_I_sa])
results["SA2"] = dict(kappa_I=kappa_I_sa, psi_H1=psi_motiv_sa, psi_H3=psi_motiv_sa_H3)
print(f"  SA2: kappa_I-Sweep: Psi(k=0.1,H=1)={psi_motiv_sa[0]:.4f}, "
      f"Psi(k=3.0,H=1)={psi_motiv_sa[-1]:.4f}")

# SA3: 50x50 Heatmap Psi_L(L, I_job)
L_2d = np.linspace(0.1, 0.9, 50)
I_2d = np.logspace(-1, 2, 50)
L2D, I2D = np.meshgrid(L_2d, I_2d)
PSI_LI = Psi_L(L2D, 0.5, 0.5, I2D, 1.0)
results["SA3"] = dict(L=L_2d, I=I_2d, Psi=PSI_LI)
print(f"  SA3: 50x50 Heatmap Psi(L,I_job): min={PSI_LI.min():.4f}, max={PSI_LI.max():.4f}")

# SA4: 50x50 Heatmap Psi_L(H, I_job) bei L=L* (nur Motivation)
H_2d = np.linspace(0.3, 5, 50)
I_2d_sa4 = np.logspace(-1, 2, 50)
H2D, I2D_sa4 = np.meshgrid(H_2d, I_2d_sa4)
PSI_HI = Psi_L(0.5, 0.5, 0.5, I2D_sa4, H2D)
results["SA4"] = dict(H=H_2d, I=I_2d_sa4, Psi=PSI_HI)
print(f"  SA4: 50x50 Heatmap Psi(H,I_job): min={PSI_HI.min():.4f}, max={PSI_HI.max():.4f}")

# SA5: Erholungszeit vs lambda_adapt
lam_adapt_sa = np.linspace(0.01, 0.5, 100)
recov_times = []
for la in lam_adapt_sa:
    def rhs_sa5(t, y, la_v=la):
        L_v, Ls_v = y
        alpha_L = 0.3
        psi = Psi_L(L_v, Ls_v, 0.5, 0.0, 1.0)  # I_job=0: reiner Referenzpunkt-Test
        return [alpha_L * (0.5 - L_v) + psi,
                reference_dynamics_L(Ls_v, L_v, la_v)]
    sol_sa5 = solve_ivp(rhs_sa5, [0, 60], [0.1, 0.5],
                        t_eval=np.linspace(0, 60, 1000),
                        method='RK45', rtol=1e-7, atol=1e-9)
    idx_r = np.where(sol_sa5.y[0] > 0.45)[0]
    t_r = sol_sa5.t[idx_r[0]] if len(idx_r) > 0 else 60.0
    recov_times.append(t_r)
recov_times = np.array(recov_times)
results["SA5"] = dict(lam_adapt=lam_adapt_sa, recov_time=recov_times)
print(f"  SA5: Erholungszeit(lam=0.01)={recov_times[0]:.1f}, (lam=0.5)={recov_times[-1]:.1f}")


# ══════════════════════════════════════════════════════════════════════
# ERWEITERTE ANALYSEN
# ══════════════════════════════════════════════════════════════════════

print(f"\n{'='*72}\n  ERWEITERTE ANALYSEN\n{'='*72}")

# EA1: Burnout-Motivation Gleichgewicht
print("\n  EA1: Burnout-Motivation Gleichgewicht")
# Bei welchem I_job balancieren sich Burnout und Motivation exakt?
# An L=0.7 (Ueberarbeit): Burnout negativ, Motivation positiv
I_eq_sweep = np.logspace(-1, 3, 1000)
psi_eq = Psi_L(0.7, 0.5, 0.5, I_eq_sweep, 1.0)
crossings = np.where(np.diff(np.sign(psi_eq)))[0]
if len(crossings) > 0:
    I_equilib = I_eq_sweep[crossings[0]]
    psi_at_eq = psi_eq[crossings[0]]
    print(f"    Gleichgewicht bei I_job={I_equilib:.2f}: Psi={psi_at_eq:.6f}")
    print(f"    -> Burnout = Motivation; Ueberarbeit wird durch Jobfreude kompensiert")
else:
    I_equilib = None
    print(f"    Kein Gleichgewicht gefunden (Burnout dominiert immer oder umgekehrt)")

# EA1b: Sweep ueber verschiedene L-Werte fuer Gleichgewicht
L_eq_vals = np.array([0.55, 0.60, 0.65, 0.70, 0.75, 0.80])
I_eq_results = {}
for L_eq in L_eq_vals:
    psi_eq_v = Psi_L(L_eq, 0.5, 0.5, I_eq_sweep, 1.0)
    cr = np.where(np.diff(np.sign(psi_eq_v)))[0]
    if len(cr) > 0:
        I_eq_results[L_eq] = I_eq_sweep[cr[0]]
        print(f"    L={L_eq:.2f}: I_eq={I_eq_sweep[cr[0]]:.2f}")
    else:
        I_eq_results[L_eq] = None
        print(f"    L={L_eq:.2f}: Kein Gleichgewicht")

results["EA1"] = dict(I_sweep=I_eq_sweep, psi_at_L07=psi_eq,
                      I_equilib=I_equilib, L_eq=I_eq_results)

# EA2: Prop 6.2 Symmetrie V.2 <-> L.2 quantitativ
print("\n  EA2: Prop 6.2 Symmetrie V.2 <-> L.2")

# Vergleich der funktionalen Strukturen:
# V.2 Burnout-analog: v(x) mit lam -> identisch zu L.2
# V.2 Info-Daempfung: 1/(1+kI) -> identisch in L.2 Burnout-Term
# V.2 Deprivation: kappa_dep*Gini -> L.2 hat stattdessen kappa_I*I_job/(I_job+psi_I)*H

# Strukturtest: Bei I_job=0, H=1 (kein Motivation-Term), ist L.2 identisch zu V.2
# mit gleichen Parametern?
x_test = np.linspace(-0.4, 0.4, 200)  # Abweichung von Referenz
ref = 0.5

# L.2 bei I_job=0
psi_L2_test = Psi_L(ref - x_test, ref, ref, 0, 1)
# V.2 Analog: kappa_ref * v(x) * 1/(1+kappa_info*I) mit I=0
# v(x>=0) = lam*x, v(x<0) = x   (x = L*-L = ref - (ref-x_test) = x_test)
v_analog = np.where(x_test >= 0, x_test, 2.25 * x_test)
psi_V2_analog = 0.3 * v_analog * 1.0  # kappa_ref=0.3, info_mod=1/(1+0)=1

max_diff = np.max(np.abs(psi_L2_test - psi_V2_analog))
print(f"    max|Psi_L2 - Psi_V2_analog| = {max_diff:.2e} (bei I_job=0, H=1)")
print(f"    -> Strukturelle Identitaet: {'JA' if max_diff < 1e-10 else 'NEIN'}")

# Transmissionsstruktur-Vergleich: Michaelis-Menten
I_trans = np.logspace(-1, 2, 100)
# V.2: 1/(1+I) -> dampening
# L.2 Motivation: I/(I+psi_I) -> amplification
trans_V2 = 1.0 / (1.0 + I_trans)  # V.2 info dampening
trans_L2_intr = I_trans / (I_trans + 8.5)  # L.2 intrinsic (Michaelis-Menten)
trans_L2_burn = 1.0 / (1.0 + I_trans)  # L.2 burnout dampening (identisch!)

max_diff_burn = np.max(np.abs(trans_L2_burn - trans_V2))
print(f"    max|trans_L2_burn - trans_V2| = {max_diff_burn:.2e}")
print(f"    -> Burnout-Daempfung identisch zu V.2: {'JA' if max_diff_burn < 1e-10 else 'NEIN'}")
print(f"    -> Motivation-Verstaerkung: Michaelis-Menten (dual zu V.2-Daempfung)")

results["EA2"] = dict(x=x_test, psi_L2=psi_L2_test, psi_V2=psi_V2_analog,
                      max_diff=max_diff, max_diff_burn=max_diff_burn,
                      I_trans=I_trans, trans_V2=trans_V2,
                      trans_L2_intr=trans_L2_intr, trans_L2_burn=trans_L2_burn)

# EA3: Komparative Statik (5 Parameter)
print("\n  EA3: Komparative Statik")

L_base = 0.6
Ls_base = 0.5
I_base = 5.0
H_base = 1.0
eps_cs = 0.001

psi_base = Psi_L(L_base, Ls_base, 0.5, I_base, H_base)

dPsi_dL = (Psi_L(L_base+eps_cs, Ls_base, 0.5, I_base, H_base) - psi_base) / eps_cs
dPsi_dLs = (Psi_L(L_base, Ls_base+eps_cs, 0.5, I_base, H_base) - psi_base) / eps_cs
dPsi_dI = (Psi_L(L_base, Ls_base, 0.5, I_base+eps_cs, H_base) - psi_base) / eps_cs
dPsi_dH = (Psi_L(L_base, Ls_base, 0.5, I_base, H_base+eps_cs) - psi_base) / eps_cs
dPsi_dlamB = (Psi_L(L_base, Ls_base, 0.5, I_base, H_base, lam_B=2.25+eps_cs) - psi_base) / eps_cs

print(f"    dPsi/dL     = {dPsi_dL:+.4f}  (negativ: mehr L -> mehr Burnout)")
print(f"    dPsi/dL*    = {dPsi_dLs:+.4f}  (positiv: hoehere Referenz -> zieht L hoch)")
print(f"    dPsi/dI_job = {dPsi_dI:+.4f}  (Vorzeichen dual: burn down, motiv up)")
print(f"    dPsi/dH     = {dPsi_dH:+.4f}  (positiv: Gesundheit -> mehr Motivation)")
print(f"    dPsi/dlam_B = {dPsi_dlamB:+.4f}  (bei L>L*: staerkerer Burnout)")

results["EA3"] = dict(dPsi_dL=dPsi_dL, dPsi_dLs=dPsi_dLs,
                      dPsi_dI=dPsi_dI, dPsi_dH=dPsi_dH, dPsi_dlamB=dPsi_dlamB)


# ══════════════════════════════════════════════════════════════════════
# ZUSAMMENFASSUNG
# ══════════════════════════════════════════════════════════════════════

n_pass = sum(1 for v in validations.values() if v["passed"])
n_total = len(validations)

print(f"\n{'='*72}")
print(f"  ZUSAMMENFASSUNG: {n_pass}/{n_total} Validierungen bestanden")
print(f"{'='*72}")

for key in sorted(validations.keys()):
    v = validations[key]
    status = "PASS" if v["passed"] else "FAIL"
    print(f"  {key}: {status} — {v['name']} ({v['detail']})")


# ══════════════════════════════════════════════════════════════════════
# PLOT (27 Panels)
# ══════════════════════════════════════════════════════════════════════

print(f"\n  PLOTTE ...")
fig = plt.figure(figsize=(26, 44))
gs = GridSpec(10, 3, figure=fig, height_ratios=[1, 1, 1, 1, 1, 1, 1, 1, 1, 0.35],
              hspace=0.38, wspace=0.30)
fig.suptitle('S24  L.2  Psychologische Arbeitsverzerrung',
             fontsize=15, fontweight='bold', y=0.995)

# ── Row 1: R1 + R2 ──
ax = fig.add_subplot(gs[0, 0])
ax.plot(L_range, psi_R1, 'C0-', lw=2)
ax.axhline(0, color='gray', ls=':', lw=0.5)
ax.axvline(L_star_R1, color='red', ls='--', lw=1, label=f'L*={L_star_R1}')
ax.fill_between(L_range, psi_R1, 0, where=psi_R1 > 0, color='C0', alpha=0.15)
ax.fill_between(L_range, psi_R1, 0, where=psi_R1 < 0, color='C3', alpha=0.15)
ax.set_xlabel('L'); ax.set_ylabel(r'$\Psi_L$')
ax.set_title('(a) R1: Referenzpunktanziehung (V1, V2)')
ax.legend(fontsize=7); ax.grid(True, alpha=0.3)

ax = fig.add_subplot(gs[0, 1])
ax.plot(d_sweep, np.abs(psi_over_sw), 'C3-', lw=2, label='Burnout |Psi(L>L*)|')
ax.plot(d_sweep, np.abs(psi_under_sw), 'C0-', lw=2, label='Unterarbeit |Psi(L<L*)|')
ax.fill_between(d_sweep, np.abs(psi_over_sw), np.abs(psi_under_sw), alpha=0.15, color='C3')
ax.set_xlabel('Abstand |L-L*|'); ax.set_ylabel('|Psi|')
ax.set_title(f'(b) R2: Burnout-Asymmetrie (lam_B={2.25}) (V3)')
ax.legend(fontsize=7); ax.grid(True, alpha=0.3)

ax = fig.add_subplot(gs[0, 2])
ratio_sw = np.abs(psi_over_sw) / np.maximum(np.abs(psi_under_sw), 1e-15)
ax.plot(d_sweep, ratio_sw, 'C1-', lw=2)
ax.axhline(2.25, color='red', ls=':', lw=1, label='lam_B=2.25')
ax.set_xlabel('Abstand |L-L*|'); ax.set_ylabel('|Burnout/Unterarbeit|')
ax.set_title('(c) R2: Burnout/Unterarbeit Ratio (V7)')
ax.legend(fontsize=7); ax.grid(True, alpha=0.3)
ax.set_ylim(0, 4)

# ── Row 2: R3 ──
ax = fig.add_subplot(gs[1, 0])
for lam_a, d in R3_data.items():
    ax.plot(d["t"], d["L"], lw=2, label=f'L (lam_a={lam_a})')
ax.plot(R3_data[0.1]["t"], R3_data[0.1]["L_star"], 'k--', lw=1, label='L*')
ax.set_xlabel('t'); ax.set_ylabel('L, L*')
ax.set_title('(d) R3: Adaptation (L und L*)')
ax.legend(fontsize=6); ax.grid(True, alpha=0.3)

ax = fig.add_subplot(gs[1, 1])
for lam_a, d in R3_data.items():
    ax.plot(d["t"], d["gap"], lw=2, label=f'lam_a={lam_a}')
ax.axhline(0, color='gray', ls=':', lw=0.5)
ax.set_xlabel('t'); ax.set_ylabel('L - L*')
ax.set_title('(e) R3: Gap-Dynamik')
ax.legend(fontsize=7); ax.grid(True, alpha=0.3)

ax = fig.add_subplot(gs[1, 2])
for lam_a, d in R3_data.items():
    ax.plot(d["t"], d["psi"], lw=2, label=f'lam_a={lam_a}')
ax.axhline(0, color='gray', ls=':', lw=0.5)
ax.set_xlabel('t'); ax.set_ylabel(r'$\Psi_L(t)$')
ax.set_title('(f) R3: Psi-Verlauf')
ax.legend(fontsize=7); ax.grid(True, alpha=0.3)

# ── Row 3: R4 + R5 ──
ax = fig.add_subplot(gs[2, 0])
for H_v, psi_v in R4_data.items():
    ax.semilogx(I_job_sweep, psi_v, lw=2, label=f'H={H_v}')
ax.axhline(0, color='gray', ls=':', lw=0.5)
ax.set_xlabel('I_job (log)'); ax.set_ylabel(r'$\Psi_L$')
ax.set_title('(g) R4: Intrinsische Motivation (V5, V6)')
ax.legend(fontsize=7); ax.grid(True, alpha=0.3)

ax = fig.add_subplot(gs[2, 1])
ax.semilogx(I_sweep_R5, psi_total_R5, 'k-', lw=2.5, label='Total')
ax.semilogx(I_sweep_R5, psi_burn_only, 'C3--', lw=2, label='Burnout only')
ax.semilogx(I_sweep_R5, psi_intr_only, 'C2--', lw=2, label='Motivation only')
ax.axhline(0, color='gray', ls=':', lw=0.5)
if I_cross is not None:
    ax.axvline(I_cross, color='C1', ls=':', lw=1.5, label=f'Crossover I={I_cross:.1f}')
ax.set_xlabel('I_job (log)'); ax.set_ylabel(r'$\Psi_L$')
ax.set_title('(h) R5: Info-Dualitaet (Burnout vs. Motivation)')
ax.legend(fontsize=6); ax.grid(True, alpha=0.3)

# ── R6 ──
ax = fig.add_subplot(gs[2, 2])
idx_show = np.random.choice(N_het, 20, replace=False)
for i in idx_show:
    ax.plot(t_het, L_hist[i], lw=0.6, alpha=0.5)
ax.plot(t_het, L_hist.mean(axis=0), 'k-', lw=2, label='Mittel')
ax.set_xlabel('t'); ax.set_ylabel('L(t)')
ax.set_title(f'(i) R6: Heterogene Agenten (N={N_het})')
ax.legend(fontsize=7); ax.grid(True, alpha=0.3)

# ── Row 4: R6 + R7 ──
ax = fig.add_subplot(gs[3, 0])
ax.plot(t_het, gini_hist, 'C3-', lw=2)
ax.set_xlabel('t'); ax.set_ylabel('Gini')
ax.set_title(f'(j) R6: Gini(t) [{gini_0:.3f} -> {gini_T:.3f}]')
ax.grid(True, alpha=0.3)

ax = fig.add_subplot(gs[3, 1])
ax.scatter(I_job_het, L_final, s=8, alpha=0.5, c=H_het, cmap='viridis')
cb = plt.colorbar(ax.collections[0], ax=ax, label='H')
ax.set_xlabel('I_job'); ax.set_ylabel('L(T)')
ax.set_title(f'(k) R6: L(T) vs I_job (Corr={corr_I_L:.3f})')
ax.grid(True, alpha=0.3)

ax = fig.add_subplot(gs[3, 2])
for lam_B, d in R7_data.items():
    ax.plot(d["t"], d["L"], lw=2, label=f'L (lam_B={lam_B})')
ax.plot(R7_data[2.25]["t"], R7_data[2.25]["L_star"], 'k--', lw=1, label='L*')
ax.axvline(shock_t, color='gray', ls=':', lw=0.8, label='Schock')
ax.set_xlabel('t'); ax.set_ylabel('L, L*')
ax.set_title('(l) R7: Arbeitsschock + Erholung')
ax.legend(fontsize=6); ax.grid(True, alpha=0.3)

# ── Row 5: R7 + R8 ──
ax = fig.add_subplot(gs[4, 0])
for lam_B, d in R7_data.items():
    ax.plot(d["t"], d["psi"], lw=2, label=f'lam_B={lam_B}')
ax.axvline(shock_t, color='gray', ls=':', lw=0.8)
ax.axhline(0, color='gray', ls=':', lw=0.5)
ax.set_xlabel('t'); ax.set_ylabel(r'$\Psi_L(t)$')
ax.set_title('(m) R7: Psi nach Schock')
ax.legend(fontsize=7); ax.grid(True, alpha=0.3)

ax = fig.add_subplot(gs[4, 1])
for name, d in R8_data.items():
    ax.plot(d["t"], d["L"], lw=2, label=name.split('(')[0].strip())
ax.set_xlabel('t'); ax.set_ylabel('L(t)')
ax.set_title('(n) R8: Drei-Ebenen-Vergleich')
ax.legend(fontsize=5.5); ax.grid(True, alpha=0.3)

ax = fig.add_subplot(gs[4, 2])
for name, d in R8_data.items():
    ax.plot(d["t"], d["L_star"], lw=2, ls='--',
            label=f'L* {name.split("(")[0].strip()}')
ax.set_xlabel('t'); ax.set_ylabel('L*(t)')
ax.set_title('(o) R8: Referenzpunkt-Evolution')
ax.legend(fontsize=5.5); ax.grid(True, alpha=0.3)

# ── Row 6: SA1 + SA2 ──
ax = fig.add_subplot(gs[5, 0])
ax.plot(lam_B_sa, psi_over_sa1, 'C3-', lw=2, label='|Psi(Burnout)|')
ax.plot(lam_B_sa, psi_under_sa1, 'C0-', lw=2, label='|Psi(Unterarbeit)|')
ax.set_xlabel(r'$\lambda_B$'); ax.set_ylabel('|Psi|')
ax.set_title('(p) SA1: Burnout-Sweep')
ax.legend(fontsize=7); ax.grid(True, alpha=0.3)

ax = fig.add_subplot(gs[5, 1])
ax.plot(kappa_I_sa, psi_motiv_sa, 'C1-', lw=2, label='H=1')
ax.plot(kappa_I_sa, psi_motiv_sa_H3, 'C2-', lw=2, label='H=3')
ax.set_xlabel(r'$\kappa_I$'); ax.set_ylabel(r'$\Psi_L$')
ax.set_title('(q) SA2: Motivation-Sweep')
ax.legend(fontsize=7); ax.grid(True, alpha=0.3)

# ── SA3 Heatmap ──
ax = fig.add_subplot(gs[5, 2])
im = ax.imshow(PSI_LI, extent=[L_2d[0], L_2d[-1],
               np.log10(I_2d[0]), np.log10(I_2d[-1])],
               aspect='auto', origin='lower', cmap='RdBu_r')
ax.contour(L_2d, np.log10(I_2d), PSI_LI, levels=[0], colors='black', linewidths=2)
plt.colorbar(im, ax=ax, label=r'$\Psi_L$')
ax.axvline(0.5, color='green', ls=':', lw=1, label='L*=0.5')
ax.set_xlabel('L'); ax.set_ylabel('log10(I_job)')
ax.set_title('(r) SA3: Heatmap Psi(L, I_job)')
ax.legend(fontsize=7)

# ── Row 7: SA4 + SA5 + EA1 ──
ax = fig.add_subplot(gs[6, 0])
im = ax.imshow(PSI_HI, extent=[H_2d[0], H_2d[-1],
               np.log10(I_2d_sa4[0]), np.log10(I_2d_sa4[-1])],
               aspect='auto', origin='lower', cmap='Greens')
plt.colorbar(im, ax=ax, label=r'$\Psi_L$')
ax.set_xlabel('H'); ax.set_ylabel('log10(I_job)')
ax.set_title('(s) SA4: Heatmap Psi(H, I_job)')

ax = fig.add_subplot(gs[6, 1])
ax.plot(lam_adapt_sa, recov_times, 'C2-', lw=2)
ax.set_xlabel(r'$\lambda_{L^*}$'); ax.set_ylabel('Erholungszeit [t]')
ax.set_title('(t) SA5: Erholungszeit vs Adaptation')
ax.grid(True, alpha=0.3)

ax = fig.add_subplot(gs[6, 2])
ax.semilogx(I_eq_sweep, psi_eq, 'k-', lw=2)
ax.axhline(0, color='gray', ls=':', lw=0.5)
if I_equilib is not None:
    ax.axvline(I_equilib, color='C1', ls='--', lw=1.5,
               label=f'Gleichgewicht I={I_equilib:.1f}')
ax.set_xlabel('I_job (log)'); ax.set_ylabel(r'$\Psi_L$ bei L=0.7')
ax.set_title('(u) EA1: Burnout-Motivation Gleichgewicht')
ax.legend(fontsize=7); ax.grid(True, alpha=0.3)

# ── Row 8: EA2 ──
ax = fig.add_subplot(gs[7, 0])
ax.plot(x_test, psi_L2_test, 'C0-', lw=2, label='L.2 (I_job=0)')
ax.plot(x_test, psi_V2_analog, 'C3--', lw=2, label='V.2 analog')
ax.axhline(0, color='gray', ls=':', lw=0.5)
ax.set_xlabel('x = L* - L'); ax.set_ylabel('Psi')
ax.set_title(f'(v) EA2: L.2 vs V.2 (max|diff|={max_diff:.1e})')
ax.legend(fontsize=7); ax.grid(True, alpha=0.3)

ax = fig.add_subplot(gs[7, 1])
ax.semilogx(I_trans, trans_V2, 'C3-', lw=2, label='V.2 Daempfung 1/(1+I)')
ax.semilogx(I_trans, trans_L2_intr, 'C2-', lw=2, label='L.2 Motivation I/(I+psi)')
ax.semilogx(I_trans, trans_L2_burn, 'C0--', lw=2, label='L.2 Burn-Daemp 1/(1+I)')
ax.set_xlabel('I (log)'); ax.set_ylabel('Modulation')
ax.set_title('(w) EA2: Transmissionsstruktur V.2 vs L.2')
ax.legend(fontsize=6); ax.grid(True, alpha=0.3)

# ── EA3 ──
ax = fig.add_subplot(gs[7, 2])
params = ['dPsi/dL', 'dPsi/dL*', 'dPsi/dI', 'dPsi/dH', 'dPsi/dlam']
vals = [dPsi_dL, dPsi_dLs, dPsi_dI, dPsi_dH, dPsi_dlamB]
colors = ['C3' if v < 0 else 'C2' for v in vals]
ax.barh(params, vals, color=colors, edgecolor='black', linewidth=0.5)
ax.axvline(0, color='gray', lw=0.5)
ax.set_xlabel('Gradient')
ax.set_title('(x) EA3: Komparative Statik')
ax.grid(True, alpha=0.3, axis='x')

# ── Row 9: Kausalitaet ──
ax = fig.add_subplot(gs[8, :])
ax.axis('off')
kaus_text = (
    "KAUSALKETTEN (S24 L.2):\n"
    "═══════════════════════════════════════════════════════════════════════════════════════════════\n\n"
    "1. Referenzpunkt-Anziehung:                    2. Burnout-Asymmetrie (lam_B=2.25):              3. Intrinsische Motivation:\n"
    "   L < L* => Psi > 0                              |Psi(Burnout)| >> |Psi(Unterarbeit)|            I_job hoch + H hoch => Psi_intr >> 0\n"
    "   => Arbeit wird hochgezogen                     => Erholung von Unterarbeit schneller            => Agent arbeitet UEBER rationalem Niveau\n"
    "   L* passt sich an: 'workaholic                  als Erholung von Ueberarbeit                     => Flow-Zustand: Burnout kompensiert\n"
    "   treadmill' (langsamer als c*!)                                                                  => Gilt nur bei hoher Jobidentifikation\n\n"
    "4. Info-Dualitaet (EINZIGARTIG in L.2):        5. Prop 6.2 Symmetrie:                           6. Poverty Trap:\n"
    "   I_job daempft Burnout (wie V.2)                V.2: Verlustaversion <-> L.2: Burnout            Niedrig-I Agenten: kein Motivations-\n"
    "   I_job VERSTAERKT Motivation (NEU!)             V.2: Deprivation <-> L.2: Motivation             schub, aber volles Burnout-Risiko\n"
    "   => Bei I_cross: Burnout = Motivation           V.2: Info daempft <-> L.2: Info dual              => Arbeiten zu wenig ODER Burnout\n"
    "   => Hochinformierte: Motivation > Burnout       Strukturell identisch bei I_job=0                 => Doppelte Benachteiligung\n"
)
ax.text(0.01, 0.95, kaus_text, transform=ax.transAxes,
        fontsize=8, fontfamily='monospace', verticalalignment='top')

# ── Zusammenfassung ──
ax = fig.add_subplot(gs[9, :])
ax.axis('off')
summary = (f"S24 L.2: {n_pass}/{n_total} Validierungen bestanden | "
           f"Burnout-Ratio={ratio_burn:.2f} | "
           f"Info-Dualitaet: Burnout daempft, Motivation verstaerkt | "
           f"Gini: {gini_0:.3f} -> {gini_T:.3f} | "
           f"Corr(I_job,L)={corr_I_L:.3f} | "
           f"Prop 6.2: max|L.2-V.2|={max_diff:.1e}")
ax.text(0.5, 0.5, summary, transform=ax.transAxes,
        fontsize=10, ha='center', va='center',
        bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.8))

plt.savefig(PLOT_DIR / "S24_L2_Psychologische_Arbeitsverzerrung.png",
            dpi=150, bbox_inches='tight')
plt.close()
print(f"  Plot gespeichert: Ergebnisse/Plots/S24_L2_Psychologische_Arbeitsverzerrung.png")


# ══════════════════════════════════════════════════════════════════════
# DATEN SPEICHERN
# ══════════════════════════════════════════════════════════════════════

save_data = {
    "R1_L": results["R1"]["L"],
    "R1_psi": results["R1"]["psi"],
    "R2_d": results["R2"]["d"],
    "R2_psi_under": results["R2"]["psi_under"],
    "R2_psi_over": results["R2"]["psi_over"],
    "R6_L_hist": L_hist,
    "R6_Ls_hist": Ls_hist,
    "R6_gini": gini_hist,
    "R6_I_job": I_job_het,
    "R6_H": H_het,
    "SA3_Psi": PSI_LI,
    "SA4_Psi": PSI_HI,
    "EA2_psi_L2": results["EA2"]["psi_L2"],
    "EA2_psi_V2": results["EA2"]["psi_V2"],
}
np.savez_compressed(DATA_DIR / "S24_L2_Psychologische_Arbeitsverzerrung.npz", **save_data)
print(f"  Daten gespeichert: Ergebnisse/Daten/S24_L2_Psychologische_Arbeitsverzerrung.npz")

print(f"\n{'='*72}")
print(f"  S24 ABGESCHLOSSEN: {n_pass}/{n_total} Validierungen")
print(f"{'='*72}")
