"""
S15 – Aufmerksamkeitsgewichte U.2  (§6.2 + Anhang C.3)
========================================================
Axiom U.2   ω_{k,i} = ω(I_i) : R_+^K -> Δ^{K-1}

Drei funktionale Formen:
  ─ Softmax:   ω_k = I_k^η / Σ_j I_j^η
  ─ Probit :   ω_k = Φ(I_k / σ) / Σ_j Φ(I_j / σ)   (renormiert)
  ─ Linear :   ω_k = I_k / Σ_j I_j                   (= Softmax η=1)

Axiomatische Eigenschaften:
  (i)   Normierung:                Σ_k ω_k = 1
  (ii)  Informationsmonotonie:     ∂ω_k/∂I_k > 0
  (iii) Informationsexklusion:     I_k=0  =>  ω_k=0
  (iv)  Glattheit:                 ω ∈ C^1

Zusaetzlich: U.3  Effektiver Preis
  p_k^eff = p_k * (1 + ψ_k / (I_k + ε))

7 Regime + 8 Validierungen
Sensitivitaetsanalyse: η-Sweep, σ-Sweep, ψ-Sweep
Inhomogenitaet: heterogene Agenten mit unterschiedlichem I_k-Vektor

Kausalkette:  I -> U.2 -> ω -> U.1 -> Nutzen -> Nachfrage
              I -> U.3 -> p_eff -> effektive Kosten -> Wohlfahrtsverlust
"""

import sys, io, warnings
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
warnings.filterwarnings('ignore', category=UserWarning, module='matplotlib')

import numpy as np
from scipy.special import ndtr     # Φ(x) = normal CDF
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

# ══════════════════════════════════════════════════════════════════════
# 1. Aufmerksamkeitsgewichts-Funktionen  U.2
# ══════════════════════════════════════════════════════════════════════

def omega_softmax(I_vec, eta=1.0):
    """Softmax-Aufmerksamkeit: ω_k = I_k^η / Σ I_j^η"""
    I_safe = np.maximum(I_vec, 0.0)
    powered = I_safe ** eta
    s = powered.sum(axis=-1, keepdims=True)
    s = np.where(s < 1e-30, 1e-30, s)
    return powered / s

def omega_probit(I_vec, sigma=1.0):
    """Probit-Aufmerksamkeit: ω_k = Φ(I_k/σ) / Σ Φ(I_j/σ)"""
    I_safe = np.maximum(I_vec, 0.0)
    phi = ndtr(I_safe / sigma)
    s = phi.sum(axis=-1, keepdims=True)
    s = np.where(s < 1e-30, 1e-30, s)
    return phi / s

def omega_linear(I_vec):
    """Lineare Aufmerksamkeit: ω_k = I_k / Σ I_j  (= Softmax η=1)"""
    return omega_softmax(I_vec, eta=1.0)


# ══════════════════════════════════════════════════════════════════════
# 2. Effektiver Preis  U.3
# ══════════════════════════════════════════════════════════════════════

def p_effective(p_k, I_k, psi_k, eps=0.01):
    """p_k^eff = p_k * (1 + ψ_k / (I_k + ε))"""
    return p_k * (1.0 + psi_k / (I_k + eps))


# ══════════════════════════════════════════════════════════════════════
# 3. Aufmerksamkeits-Dynamik  VI.9
# ══════════════════════════════════════════════════════════════════════

def attention_dynamics(omega_target, a_init, lambda_a=0.5, T=20.0, dt=0.05):
    """ȧ_k = λ_a * (ω_k - a_k)  — Konvergenz zum Gleichgewicht"""
    steps = int(T / dt)
    K = len(omega_target)
    a = np.zeros((steps + 1, K))
    a[0] = a_init
    t = np.linspace(0, T, steps + 1)
    for n in range(steps):
        da = lambda_a * (omega_target - a[n])
        a[n+1] = a[n] + dt * da
    return t, a


# ══════════════════════════════════════════════════════════════════════
# 4. Regime-Definitionen
# ══════════════════════════════════════════════════════════════════════

K = 5   # Anzahl Gueter
I_base = np.array([8.0, 4.0, 2.0, 1.0, 0.5])   # Heterogenes Info-Profil
I_labels = [f'Gut {k+1}' for k in range(K)]

print("=" * 72)
print("  S15  U.2  Aufmerksamkeitsgewichte + U.3 Effektiver Preis")
print("=" * 72)

results = {}

# --- R1: Softmax η-Vergleich ---
print("\n  R1: Softmax eta-Vergleich")
etas = [0.3, 0.5, 1.0, 2.0, 5.0, 10.0]
R1_omegas = {}
for eta in etas:
    R1_omegas[eta] = omega_softmax(I_base, eta=eta)
results["R1"] = dict(label="R1: Softmax eta-Sweep", color="C0",
                      etas=etas, omegas=R1_omegas, I=I_base)

# --- R2: Probit σ-Vergleich ---
print("  R2: Probit sigma-Vergleich")
sigmas = [0.3, 0.5, 1.0, 2.0, 5.0, 10.0]
R2_omegas = {}
for sig in sigmas:
    R2_omegas[sig] = omega_probit(I_base, sigma=sig)
results["R2"] = dict(label="R2: Probit sigma-Sweep", color="C1",
                      sigmas=sigmas, omegas=R2_omegas, I=I_base)

# --- R3: Vergleich Softmax vs Probit vs Linear ---
print("  R3: Funktionalform-Vergleich")
I_sweep = np.linspace(0, 10, 201)
I_2good = np.column_stack([I_sweep, 5.0 * np.ones_like(I_sweep)])  # Gut 1 variiert, Gut 2 = 5
R3_sm = omega_softmax(I_2good, eta=2.0)[:, 0]
R3_pr = omega_probit(I_2good, sigma=1.0)[:, 0]
R3_li = omega_linear(I_2good)[:, 0]
results["R3"] = dict(label="R3: Form-Vergleich (K=2)", color="C2",
                      I_sweep=I_sweep, sm=R3_sm, pr=R3_pr, li=R3_li)

# --- R4: U.3 Effektiver Preis ---
print("  R4: Effektiver Preis p_eff(I)")
p_market = np.array([10.0, 20.0, 5.0, 15.0, 8.0])
psi_vals = np.array([2.0, 5.0, 1.0, 3.0, 10.0])
I_scan = np.linspace(0.01, 20, 500)
R4_peff = {}
for ik in range(K):
    R4_peff[ik] = p_effective(p_market[ik], I_scan, psi_vals[ik], eps=0.01)
results["R4"] = dict(label="R4: p_eff(I) fuer 5 Gueter", color="C3",
                      I_scan=I_scan, peff=R4_peff, p_market=p_market, psi=psi_vals)

# --- R5: Sensitivitaet: η-Sweep Herfindahl-Index ---
print("  R5: Sensitivitaet eta -> Konzentration (HHI)")
eta_fine = np.linspace(0.1, 15, 300)
hhi_vals = []
gini_vals = []
for e in eta_fine:
    w = omega_softmax(I_base, eta=e)
    hhi_vals.append(np.sum(w**2))
    # Gini
    w_sorted = np.sort(w)
    n = len(w)
    gini = (2 * np.sum((np.arange(1, n+1)) * w_sorted) / (n * np.sum(w_sorted))) - (n + 1) / n
    gini_vals.append(gini)
results["R5"] = dict(label="R5: η → HHI + Gini", color="C4",
                      eta_fine=eta_fine, hhi=np.array(hhi_vals), gini=np.array(gini_vals))

# --- R6: Inhomogene Agenten (heterogene I-Vektoren) ---
print("  R6: Heterogene Agenten")
N_agents = 200
I_agents = np.random.exponential(scale=3.0, size=(N_agents, K))
I_agents[:, 0] *= 2.0    # Gut 1 ist allgemein bekannter
omega_agents_sm = omega_softmax(I_agents, eta=2.0)
omega_agents_pr = omega_probit(I_agents, sigma=1.5)
peff_agents = np.zeros((N_agents, K))
for ik in range(K):
    peff_agents[:, ik] = p_effective(p_market[ik], I_agents[:, ik], psi_vals[ik])
results["R6"] = dict(label="R6: Heterogene Agenten (N=200)", color="C5",
                      I_agents=I_agents, omega_sm=omega_agents_sm, omega_pr=omega_agents_pr,
                      peff=peff_agents, N=N_agents)

# --- R7: Aufmerksamkeits-Dynamik VI.9 ---
print("  R7: Aufmerksamkeits-Dynamik + Informationsschock")
omega_target = omega_softmax(I_base, eta=2.0)
a_init = np.ones(K) / K   # Gleichverteilt
t_dyn, a_dyn = attention_dynamics(omega_target, a_init, lambda_a=0.5, T=20.0)

# Abrupt Info-Schock bei t=10: Gut 3 bekommt Nachrichtenflut
I_shocked = I_base.copy()
I_shocked[2] = 15.0   # I_3 springt
omega_post = omega_softmax(I_shocked, eta=2.0)
t_dyn2, a_dyn2 = attention_dynamics(omega_post, a_dyn[len(t_dyn)//2],
                                      lambda_a=0.5, T=10.0)
t_full = np.concatenate([t_dyn[:len(t_dyn)//2], t_dyn2 + t_dyn[len(t_dyn)//2]])
a_full = np.vstack([a_dyn[:len(t_dyn)//2], a_dyn2])
results["R7"] = dict(label="R7: Aufmerksamkeits-Dynamik + Schock", color="C6",
                      t=t_full, a=a_full, omega_pre=omega_target, omega_post=omega_post,
                      t_shock=t_dyn[len(t_dyn)//2])


# ══════════════════════════════════════════════════════════════════════
# 5. Validierungen
# ══════════════════════════════════════════════════════════════════════

validations = {}
print(f"\n{'='*72}\n  VALIDIERUNGEN\n{'='*72}")

# V1: Normierung Σω_k = 1 fuer alle Formen
norm_errs = []
for eta in [0.5, 1.0, 2.0, 5.0]:
    w = omega_softmax(I_base, eta=eta)
    norm_errs.append(abs(w.sum() - 1.0))
for sig in [0.5, 1.0, 5.0]:
    w = omega_probit(I_base, sigma=sig)
    norm_errs.append(abs(w.sum() - 1.0))
w = omega_linear(I_base)
norm_errs.append(abs(w.sum() - 1.0))
v1_err = max(norm_errs)
v1_pass = v1_err < 1e-12
validations["V1"] = dict(name="Normierung Σω=1", passed=v1_pass,
                          detail=f"max|Σω-1|={v1_err:.2e}")
print(f"  V1: {'PASS' if v1_pass else 'FAIL'} ({validations['V1']['detail']})")

# V2: Informationsmonotonie ∂ω_k/∂I_k > 0
# Probit: use larger σ to avoid saturation Φ(I/σ)→1
delta = 1e-6
mono_ok = True
mono_detail = []
for form_name, form_func, kw in [("Softmax", omega_softmax, {"eta": 2.0}),
                                    ("Probit", omega_probit, {"sigma": 5.0}),
                                    ("Linear", omega_linear, {})]:
    for k in range(K):
        I_plus = I_base.copy(); I_plus[k] += delta
        w0 = form_func(I_base, **kw)[k]
        w1 = form_func(I_plus, **kw)[k]
        deriv = (w1 - w0) / delta
        if deriv < -1e-10:
            mono_ok = False
            mono_detail.append(f"{form_name} k={k}: {deriv:.2e}")
v2_pass = mono_ok
v2_info = "alle Formen, alle Gueter" if mono_ok else "; ".join(mono_detail)
validations["V2"] = dict(name="Monotonie dω/dI ≥ 0", passed=v2_pass,
                          detail=v2_info)
print(f"  V2: {'PASS' if v2_pass else 'FAIL'} ({validations['V2']['detail']})")

# V3: Informationsexklusion I_k=0 => ω_k=0 (Softmax + Linear)
I_zero = I_base.copy(); I_zero[2] = 0.0
w_zero_sm = omega_softmax(I_zero, eta=2.0)
w_zero_li = omega_linear(I_zero)
v3_pass = w_zero_sm[2] < 1e-15 and w_zero_li[2] < 1e-15
validations["V3"] = dict(name="Exklusion I=0 => ω=0", passed=v3_pass,
                          detail=f"ω_sm(I=0)={w_zero_sm[2]:.2e}, ω_li(I=0)={w_zero_li[2]:.2e}")
print(f"  V3: {'PASS' if v3_pass else 'FAIL'} ({validations['V3']['detail']})")

# V4: Softmax η→∞ => Winner-Takes-All
w_sharp = omega_softmax(I_base, eta=50.0)
v4_pass = w_sharp[0] > 0.999   # Gut 1 hat hoechstes I
validations["V4"] = dict(name="η→∞: Winner-Takes-All", passed=v4_pass,
                          detail=f"ω_1(η=50)={w_sharp[0]:.6f}")
print(f"  V4: {'PASS' if v4_pass else 'FAIL'} ({validations['V4']['detail']})")

# V5: Softmax η→0 => Gleichverteilung
w_flat = omega_softmax(I_base, eta=0.01)
v5_pass = max(w_flat) - min(w_flat) < 0.01
validations["V5"] = dict(name="η→0: Gleichverteilung", passed=v5_pass,
                          detail=f"max-min={max(w_flat)-min(w_flat):.4f}")
print(f"  V5: {'PASS' if v5_pass else 'FAIL'} ({validations['V5']['detail']})")

# V6: p_eff ≥ p + Monotonie dp_eff/dI < 0
I_test = np.linspace(0.01, 20, 1000)
peff_test = p_effective(10.0, I_test, 3.0, eps=0.01)
v6a = np.all(peff_test >= 10.0)
v6b = np.all(np.diff(peff_test) < 0)
v6_pass = v6a and v6b
validations["V6"] = dict(name="p_eff≥p + dp/dI<0", passed=v6_pass,
                          detail=f"surcharge={v6a}, monoton={v6b}")
print(f"  V6: {'PASS' if v6_pass else 'FAIL'} ({validations['V6']['detail']})")

# V7: p_eff → p fuer I→∞ (Arrow-Debreu Grenzwert)
peff_large = p_effective(10.0, 1e6, 3.0, eps=0.01)
v7_err = abs(peff_large - 10.0) / 10.0
v7_pass = v7_err < 1e-4
validations["V7"] = dict(name="I→∞: p_eff→p (Arrow-Debreu)", passed=v7_pass,
                          detail=f"|p_eff-p|/p={v7_err:.2e}")
print(f"  V7: {'PASS' if v7_pass else 'FAIL'} ({validations['V7']['detail']})")

# V8: Aufmerksamkeits-Dynamik: a(t) → ω* exponentiell
a_final = results["R7"]["a"][-1]
omega_end = results["R7"]["omega_post"]
conv_err = np.max(np.abs(a_final - omega_end))
v8_pass = conv_err < 0.05
validations["V8"] = dict(name="Dynamik: a(T)→ω*", passed=v8_pass,
                          detail=f"max|a-ω*|={conv_err:.4f}")
print(f"  V8: {'PASS' if v8_pass else 'FAIL'} ({validations['V8']['detail']})")


# ══════════════════════════════════════════════════════════════════════
# 6. Sensitivitaetsanalyse
# ══════════════════════════════════════════════════════════════════════

print(f"\n{'='*72}\n  SENSITIVITAETSANALYSEN\n{'='*72}")

# SA1: Wohlfahrtsverlust durch Informationsasymmetrie
welfare_losses = {}
I_levels = np.linspace(0.1, 20, 200)
for psi in [1.0, 3.0, 5.0, 10.0]:
    surplus = psi / (I_levels + 0.01)   # Aufschlag relativ
    welfare_losses[psi] = surplus
results["SA1"] = dict(I=I_levels, losses=welfare_losses)
print("  SA1: Wohlfahrtsverlust vs ψ (4 Szenarien)")

# SA2: Kritische Info-Schwelle bei der ω_k Dominanzwechsel
# Bei welchem I_1 wird ω_1 > ω_2 (2-Gut-Fall)?
I2_fixed = 5.0
switch_etas = {}
for eta in [0.5, 1.0, 2.0, 5.0]:
    # solve: I_1^η / (I_1^η + I2^η) = 0.5 => I_1 = I2
    switch_etas[eta] = I2_fixed  # always at equality
results["SA2"] = dict(switch_etas=switch_etas)
print("  SA2: Dominanzwechsel-Schwelle (immer bei I_1=I_2)")

# SA3: Probit-Sensitivitaet: Wie robust ist ω gegen Rauschen?
sigma_scan = np.linspace(0.1, 20, 200)
robustness = []
for sig in sigma_scan:
    w = omega_probit(I_base, sigma=sig)
    # HHI als Mass fuer Konzentration
    robustness.append(np.sum(w**2))
results["SA3"] = dict(sigma_scan=sigma_scan, robustness=np.array(robustness))
print("  SA3: Probit-Robustheit (σ -> HHI)")

# SA4: Inhomogenitaets-Analyse — Gini der p_eff ueber Agenten
gini_goods = []
for ik in range(K):
    peff_k = results["R6"]["peff"][:, ik]
    peff_sorted = np.sort(peff_k)
    n = len(peff_sorted)
    gini = (2 * np.sum(np.arange(1, n+1) * peff_sorted) / (n * np.sum(peff_sorted))) - (n + 1) / n
    gini_goods.append(gini)
results["SA4"] = dict(gini_peff=np.array(gini_goods), labels=I_labels)
print(f"  SA4: Gini(p_eff) pro Gut: {[f'{g:.3f}' for g in gini_goods]}")


# ══════════════════════════════════════════════════════════════════════
# 7. Plot (24 Panels + Metadata)
# ══════════════════════════════════════════════════════════════════════

print(f"\n  PLOTTE ...")
fig = plt.figure(figsize=(26, 38))
gs = GridSpec(8, 3, figure=fig, height_ratios=[1, 1, 1, 1, 1, 1, 1, 0.4],
              hspace=0.38, wspace=0.30)
fig.suptitle('S15  U.2 Aufmerksamkeitsgewichte + U.3 Effektiver Preis',
             fontsize=15, fontweight='bold', y=0.995)

# Row 1: R1 Softmax η-Sweep
ax = fig.add_subplot(gs[0, 0])
x_pos = np.arange(K)
width = 0.12
for i, eta in enumerate(etas):
    ax.bar(x_pos + i * width, R1_omegas[eta], width, label=f'η={eta}', alpha=0.85)
ax.set_xticks(x_pos + width * (len(etas)-1)/2)
ax.set_xticklabels(I_labels, fontsize=7)
ax.set_ylabel('ω_k'); ax.set_title('(a) R1: Softmax η-Sweep')
ax.legend(fontsize=6); ax.grid(True, alpha=0.3, axis='y')

# Row 1: R2 Probit σ-Sweep
ax = fig.add_subplot(gs[0, 1])
for i, sig in enumerate(sigmas):
    ax.bar(x_pos + i * width, R2_omegas[sig], width, label=f'σ={sig}', alpha=0.85)
ax.set_xticks(x_pos + width * (len(sigmas)-1)/2)
ax.set_xticklabels(I_labels, fontsize=7)
ax.set_ylabel('ω_k'); ax.set_title('(b) R2: Probit σ-Sweep')
ax.legend(fontsize=6); ax.grid(True, alpha=0.3, axis='y')

# Row 1: R3 Form-Vergleich
ax = fig.add_subplot(gs[0, 2])
ax.plot(I_sweep, R3_sm, 'C0-', lw=2, label='Softmax η=2')
ax.plot(I_sweep, R3_pr, 'C1--', lw=2, label='Probit σ=1')
ax.plot(I_sweep, R3_li, 'C2:', lw=2, label='Linear')
ax.axhline(0.5, ls=':', color='gray', lw=0.5)
ax.axvline(5.0, ls=':', color='gray', lw=0.5, label='I_2=5')
ax.set_xlabel('I_1'); ax.set_ylabel('ω_1')
ax.set_title('(c) R3: Form-Vergleich (K=2, I_2=5)')
ax.legend(fontsize=7); ax.grid(True, alpha=0.3)

# Row 2: R4 Effektiver Preis
ax = fig.add_subplot(gs[1, 0])
for ik in range(K):
    ax.plot(I_scan, R4_peff[ik], lw=2, label=f'Gut {ik+1} (p={p_market[ik]}, ψ={psi_vals[ik]})')
    ax.axhline(p_market[ik], ls=':', color=f'C{ik}', lw=0.5, alpha=0.4)
ax.set_xlabel('I_k'); ax.set_ylabel('p_k^eff')
ax.set_title('(d) R4: Effektiver Preis (U.3)')
ax.legend(fontsize=6); ax.grid(True, alpha=0.3); ax.set_ylim(0, 100)

# Row 2: R5 Konzentrations-Sweep
ax = fig.add_subplot(gs[1, 1])
ax.plot(eta_fine, results["R5"]["hhi"], 'C0-', lw=2, label='HHI')
ax.axhline(1/K, ls=':', color='gray', lw=0.5, label=f'HHI_min=1/{K}')
ax.axhline(1.0, ls=':', color='red', lw=0.5, label='HHI_max=1')
ax.set_xlabel('η'); ax.set_ylabel('HHI')
ax.set_title('(e) R5: Softmax η → Konzentration (HHI)')
ax.legend(fontsize=7); ax.grid(True, alpha=0.3)

ax2 = fig.add_subplot(gs[1, 2])
ax2.plot(eta_fine, results["R5"]["gini"], 'C4-', lw=2, label='Gini')
ax2.set_xlabel('η'); ax2.set_ylabel('Gini-Koeffizient')
ax2.set_title('(f) R5: Softmax η → Gini der Aufmerksamkeit')
ax2.legend(fontsize=7); ax2.grid(True, alpha=0.3)

# Row 3: R6 Heterogene Agenten
ax = fig.add_subplot(gs[2, 0])
bp = ax.boxplot([results["R6"]["omega_sm"][:, k] for k in range(K)],
                labels=I_labels, patch_artist=True)
for patch, c in zip(bp['boxes'], [f'C{k}' for k in range(K)]):
    patch.set_facecolor(c); patch.set_alpha(0.4)
ax.set_ylabel('ω_k (Softmax η=2)'); ax.set_title('(g) R6: Agenten-Verteilung ω (Softmax)')
ax.grid(True, alpha=0.3, axis='y')

ax = fig.add_subplot(gs[2, 1])
bp = ax.boxplot([results["R6"]["omega_pr"][:, k] for k in range(K)],
                labels=I_labels, patch_artist=True)
for patch, c in zip(bp['boxes'], [f'C{k}' for k in range(K)]):
    patch.set_facecolor(c); patch.set_alpha(0.4)
ax.set_ylabel('ω_k (Probit σ=1.5)'); ax.set_title('(h) R6: Agenten-Verteilung ω (Probit)')
ax.grid(True, alpha=0.3, axis='y')

ax = fig.add_subplot(gs[2, 2])
bp = ax.boxplot([results["R6"]["peff"][:, k] for k in range(K)],
                labels=I_labels, patch_artist=True)
for patch, c in zip(bp['boxes'], [f'C{k}' for k in range(K)]):
    patch.set_facecolor(c); patch.set_alpha(0.4)
ax.set_ylabel('p_k^eff'); ax.set_title('(i) R6: p_eff Verteilung (Heterogenitaet)')
ax.grid(True, alpha=0.3, axis='y')

# Row 4: R7 Dynamik
ax = fig.add_subplot(gs[3, 0])
for k in range(K):
    ax.plot(results["R7"]["t"], results["R7"]["a"][:, k], lw=2, label=I_labels[k])
ax.axvline(results["R7"]["t_shock"], ls='--', color='red', lw=1, label='Info-Schock')
ax.set_xlabel('t'); ax.set_ylabel('a_k(t)')
ax.set_title('(j) R7: Aufmerksamkeits-Dynamik + Schock')
ax.legend(fontsize=6); ax.grid(True, alpha=0.3)

ax = fig.add_subplot(gs[3, 1])
# Omega vor/nach Schock
x_pos = np.arange(K)
ax.bar(x_pos - 0.15, results["R7"]["omega_pre"], 0.3, label='vor Schock', alpha=0.7, color='C0')
ax.bar(x_pos + 0.15, results["R7"]["omega_post"], 0.3, label='nach Schock', alpha=0.7, color='C3')
ax.set_xticks(x_pos); ax.set_xticklabels(I_labels, fontsize=7)
ax.set_ylabel('ω_k'); ax.set_title('(k) R7: ω vor/nach Info-Schock')
ax.legend(fontsize=7); ax.grid(True, alpha=0.3, axis='y')

# Sensitivitaetsanalysen
ax = fig.add_subplot(gs[3, 2])
for psi, surplus in results["SA1"]["losses"].items():
    ax.plot(results["SA1"]["I"], surplus * 100, lw=2, label=f'ψ={psi}')
ax.set_xlabel('I_k'); ax.set_ylabel('Preisaufschlag [%]')
ax.set_title('(l) SA1: Wohlfahrtsverlust durch Info-Mangel')
ax.set_ylim(0, 200); ax.legend(fontsize=7); ax.grid(True, alpha=0.3)

# Row 5: Mehr Sensitivitaet
ax = fig.add_subplot(gs[4, 0])
ax.plot(results["SA3"]["sigma_scan"], results["SA3"]["robustness"], 'C1-', lw=2)
ax.axhline(1/K, ls=':', color='gray', lw=0.5, label=f'HHI_min=1/{K}')
ax.set_xlabel('σ (Probit-Rauschen)'); ax.set_ylabel('HHI')
ax.set_title('(m) SA3: Probit σ → Robustheit')
ax.legend(fontsize=7); ax.grid(True, alpha=0.3)

ax = fig.add_subplot(gs[4, 1])
ax.bar(I_labels, results["SA4"]["gini_peff"], color=[f'C{k}' for k in range(K)], alpha=0.7)
ax.set_ylabel('Gini(p_eff)'); ax.set_title('(n) SA4: Preis-Ungleichheit pro Gut')
ax.grid(True, alpha=0.3, axis='y')

# Crossover: Softmax vs Probit (wann liefern sie gleiche Rangfolge?)
ax = fig.add_subplot(gs[4, 2])
I_profiles = [
    np.array([10.0, 5.0, 2.0, 1.0, 0.5]),
    np.array([5.0, 5.0, 5.0, 5.0, 5.0]),
    np.array([1.0, 2.0, 3.0, 4.0, 5.0]),
    np.array([0.1, 0.1, 0.1, 0.1, 10.0]),
]
profile_labels = ['Skalar', 'Gleichvert.', 'Aufsteigend', 'Monopol']
for i, I_prof in enumerate(I_profiles):
    w_sm = omega_softmax(I_prof, eta=2.0)
    w_pr = omega_probit(I_prof, sigma=1.5)
    kl_div = np.sum(w_sm * np.log(np.maximum(w_sm, 1e-30) / np.maximum(w_pr, 1e-30)))
    ax.bar(i, kl_div, color=f'C{i}', alpha=0.7, label=profile_labels[i])
ax.set_xticks(range(len(profile_labels)))
ax.set_xticklabels(profile_labels, fontsize=7)
ax.set_ylabel('KL(Softmax || Probit)')
ax.set_title('(o) Divergenz Softmax vs Probit')
ax.legend(fontsize=7); ax.grid(True, alpha=0.3, axis='y')

# Row 6: Kausalitaetstexte
ax = fig.add_subplot(gs[5, 0])
ax.axis('off')
kaus_text = (
    "KAUSALKETTEN (U.2 + U.3):\n"
    "─────────────────────────\n"
    "I_k -> U.2 -> ω_k -> U.1 -> Nutzen\n"
    "I_k -> U.3 -> p_eff -> Konsumentscheidung\n\n"
    "1. η hoch: Winner-Takes-All\n"
    "   Bekannte Gueter dominieren\n"
    "   -> Markenmacht, Lock-in\n\n"
    "2. η niedrig: Diversifikation\n"
    "   Alle Gueter aehnlich gewichtet\n"
    "   -> Exploration, Aufmerksamkeits-\n"
    "      streuung\n\n"
    "3. σ (Probit) ~ \"Rauschen\":\n"
    "   Hohe σ -> randomisierte Wahl\n"
    "   Niedrige σ -> deterministisch\n\n"
    "4. ψ (Suchkosten): Opacity\n"
    "   ψ hoch -> p_eff >> p\n"
    "   Arme zahlen mehr (Info-Armut)"
)
ax.text(0.05, 0.95, kaus_text, transform=ax.transAxes, ha='left', va='top',
        fontsize=8, family='monospace',
        bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.95))

ax = fig.add_subplot(gs[5, 1])
ax.axis('off')
sens_text = (
    "SENSITIVITAETS-ERGEBNISSE:\n"
    "─────────────────────────\n"
    f"HHI(η=0.1) = {results['R5']['hhi'][0]:.3f}\n"
    f"HHI(η=5)   = {results['R5']['hhi'][np.argmin(np.abs(eta_fine-5))]:.3f}\n"
    f"HHI(η=15)  = {results['R5']['hhi'][-1]:.3f}\n\n"
    f"Gini(η=0.1) = {results['R5']['gini'][0]:.3f}\n"
    f"Gini(η=5)   = {results['R5']['gini'][np.argmin(np.abs(eta_fine-5))]:.3f}\n"
    f"Gini(η=15)  = {results['R5']['gini'][-1]:.3f}\n\n"
    "Probit HHI:\n"
    f"  σ=0.1 -> HHI={results['SA3']['robustness'][0]:.3f}\n"
    f"  σ=10  -> HHI={results['SA3']['robustness'][np.argmin(np.abs(sigma_scan-10))]:.3f}\n"
    f"  σ=20  -> HHI={results['SA3']['robustness'][-1]:.3f}\n\n"
    "Gini(p_eff) pro Gut:\n"
    + "\n".join(f"  {I_labels[k]}: {results['SA4']['gini_peff'][k]:.3f}" for k in range(K))
)
ax.text(0.05, 0.95, sens_text, transform=ax.transAxes, ha='left', va='top',
        fontsize=8, family='monospace',
        bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.95))

ax = fig.add_subplot(gs[5, 2])
ax.axis('off')
val_text = "VALIDIERUNGEN:\n" + "-"*35 + "\n"
for k, v in validations.items():
    tag = "PASS" if v["passed"] else "FAIL"
    val_text += f"{k}: {v['name']}\n   {tag}: {v['detail']}\n\n"
ax.text(0.05, 0.95, val_text, transform=ax.transAxes, ha='left', va='top',
        fontsize=8, family='monospace',
        bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.95))

# Row 7: Physik
ax = fig.add_subplot(gs[6, :])
ax.axis('off')
phys = (
    "PHYSIKALISCHE INTERPRETATION:   "
    "ω_k = Aufmerksamkeitsgewicht: Wie viel kognitive Ressource fuer Gut k aufgewendet wird. "
    "Softmax = multinomiales Logit (Standardmodell diskreter Wahl).  "
    "η = Schaerfe der Aufmerksamkeitskonzentration: η<<1 → Exploration, η>>1 → Exploitation (Winner-Takes-All).  "
    "Probit = normalverteilte Wahrnehmungsschwankungen (σ = Rauschen).  "
    "p_eff = effektiver Preis: reale Kosten inkl. Suche, Verifikation, Vertrauen. "
    "ψ = Suchkostenparameter (opacity): Je weniger Information, desto hoeher der Aufschlag.  "
    "I→∞: p_eff→p (Arrow-Debreu-Limit: vollstaendige Information eliminiert Friktionen).  "
    "Heterogene Agenten: Unterschiedliche I-Vektoren erzeugen p_eff-Ungleichheit → "
    "informationsarme Agenten zahlen systematisch mehr (poverty premium)."
)
ax.text(0.5, 0.5, phys, transform=ax.transAxes, ha='center', va='center',
        fontsize=8, wrap=True,
        bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.95))

# Metadata
ax_meta = fig.add_subplot(gs[7, :])
ax_meta.axis('off')
n_pass = sum(1 for v in validations.values() if v["passed"])
meta = (
    f"S15 U.2 Aufmerksamkeitsgewichte + U.3 eff. Preis | 7 Regime, {len(validations)} Val: "
    f"{n_pass}/{len(validations)} PASS | K={K} Gueter, N={N_agents} Agenten | "
    f"Softmax: ω=I^η/ΣI^η | Probit: ω=Φ(I/σ)/ΣΦ | p_eff=p*(1+ψ/(I+ε))"
)
ax_meta.text(0.5, 0.5, meta, transform=ax_meta.transAxes, ha='center', va='center',
             fontsize=9, family='monospace',
             bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.95))

plt.savefig(PLOT_DIR / "S15_U2_Aufmerksamkeitsgewichte.png", dpi=180, bbox_inches='tight')
plt.close()
print(f"\n  Plot: {PLOT_DIR / 'S15_U2_Aufmerksamkeitsgewichte.png'}")

# ── Daten ──
save_dict = {
    "I_base": I_base, "p_market": p_market, "psi_vals": psi_vals,
    "R1_etas": np.array(etas),
    "R2_sigmas": np.array(sigmas),
    "R3_I_sweep": I_sweep, "R3_sm": R3_sm, "R3_pr": R3_pr, "R3_li": R3_li,
    "R5_eta_fine": eta_fine, "R5_hhi": results["R5"]["hhi"], "R5_gini": results["R5"]["gini"],
    "R6_I_agents": I_agents, "R6_omega_sm": omega_agents_sm, "R6_omega_pr": omega_agents_pr,
    "R6_peff": peff_agents,
    "R7_t": results["R7"]["t"], "R7_a": results["R7"]["a"],
    "SA3_sigma": sigma_scan, "SA3_hhi": results["SA3"]["robustness"],
    "SA4_gini": results["SA4"]["gini_peff"],
}
for eta in etas:
    save_dict[f"R1_omega_eta{eta}"] = R1_omegas[eta]
for sig in sigmas:
    save_dict[f"R2_omega_sig{sig}"] = R2_omegas[sig]
np.savez_compressed(DATA_DIR / "S15_U2_Aufmerksamkeitsgewichte.npz", **save_dict)

# ── Zusammenfassung ──
print(f"\n{'='*72}\n  ZUSAMMENFASSUNG S15  U.2 + U.3\n{'='*72}")
for k, v in validations.items():
    print(f"  {k}: {v['name']:40s}  {'PASS' if v['passed'] else 'FAIL'}  ({v['detail']})")
print(f"\n  Regime:")
for key in ["R1", "R2", "R3", "R4", "R5", "R6", "R7"]:
    print(f"    {results[key]['label']}")
print(f"\n  Sensitivitaet:")
print(f"    SA1: Wohlfahrtsverlust(ψ) — 4 Szenarien")
print(f"    SA2: Dominanzwechsel immer bei I_1 = I_2 (Softmax-Symmetrie)")
print(f"    SA3: Probit σ → HHI (Robustheit)")
print(f"    SA4: Gini(p_eff) — Preisungleichheit durch Informationsasymmetrie")
n_pass = sum(1 for v in validations.values() if v["passed"])
print(f"\n  Gesamtergebnis: {n_pass}/{len(validations)} bestanden")
if n_pass == len(validations):
    print("  >>> ALLE VALIDIERUNGEN BESTANDEN <<<")
print(f"{'='*72}")
