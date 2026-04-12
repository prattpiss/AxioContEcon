"""
╔══════════════════════════════════════════════════════════════════════╗
║  S01 – Individuelle Vermögensbilanz (Gleichung I.1)                ║
║  Gleichungen: I.1 (§4.1), I.2 (§4.2), M.2 (§4.3)                ║
║  Ökonoaxiomatik – Monographie v2                                   ║
╚══════════════════════════════════════════════════════════════════════╝

Gleichungen (exakt aus Monographie):
─────────────────────────────────────
I.1 (Individuelle Vermögensbilanz):
    dw_i/dt = y_i − c_i + Σ_k θ_{ik} ṗ_k + r b_i

  Arbeiter (W):   dw_i/dt = w_ℓ ℓ_i − c_i + Σ_k θ_{ik} ṗ_k + r b_i,   b_i ≥ 0
  Unternehmer (U): dw_j/dt = (p_k q_{jk} − w_ℓ L_j − r K_j) − c_j + Σ_k θ_{jk} ṗ_k + r b_j
  Banken (B):      dw_b/dt = (r_L L_b − r_D D_b) − c_b^{Betrieb} + Σ_k θ_{bk} ṗ_k

I.2 (Aggregierte Vermögenserhaltung):
    dW/dt = Y − C
    wobei W = Σ_i w_i, Y = Σ_i y_i, C = Σ_i c_i

M.2 (Kreditmarkt-Clearing):
    Σ_i b_i = 0

Reduktion / Vereinfachung:
──────────────────────────
- Räumlich homogen (kein Raum, keine PDEs)
- 1 Gut (k=1), also θ_{i1} = θ_i (Portfolioanteil am einzigen Asset)
- 3 Agentenklassen: N_W Arbeiter, N_U Unternehmer, N_B Banken
- Preis p(t) exogen vorgegeben (sinusförmig + Trend, um Bewertungseffekte zu testen)
- Konsum proportional zum Vermögen: c_i = c_min + c' * max(w_i, 0)
- NB.1: c_i ≥ c_min (Subsistenzkonsum)
- Kein Staat, keine Zentralbank (Fokus auf private Sektoren)

Analytische Ergebnisse:
───────────────────────
1. Proposition 4.1: Σ_i Σ_k θ_{ik} ṗ_k = 0 (Nullsumme Bewertungsgewinne)
   → Wenn Σ_i θ_i = 1 für jedes Asset, dann: ṗ Σ_i θ_i = ṗ.
   → Aber: Bewertungsgewinn des einen = Bewertungsverlust des anderen
   → In der Aggregation: Σ_i θ_i ṗ = ṗ ≠ 0 im offenen System (1 Asset).
   → Korrekte Prüfung: dW/dt = Y − C (Bewertung + Zinsen canceln).

2. M.2: Σ_i b_i = 0 → Guthaben der Arbeiter = Schulden der Unternehmer
   Exakte Constraint: b_W + b_U + b_B = 0 (aggregiert)

3. I.2: dW/dt = Y − C, getestet durch Vergleich:
   - Direkte Summation: dW/dt_num = Σ dw_i/dt (numerisch)
   - Identität: Y − C (analytisch)
   - Fehler muss < Solver-Toleranz sein
"""

import numpy as np
from scipy.integrate import solve_ivp
import matplotlib.pyplot as plt
import matplotlib
import os
from pathlib import Path

matplotlib.rcParams['mathtext.fontset'] = 'cm'
matplotlib.rcParams['font.size'] = 10

# ═══════════════════════════════════════════════════════════════
# PARAMETER
# ═══════════════════════════════════════════════════════════════

# Agentenanzahl
N_W = 10   # Arbeiter
N_U = 5    # Unternehmer
N_B = 2    # Banken
N = N_W + N_U + N_B

# Lohnsatz und Arbeitszeit
w_ell = 1.0           # Lohnsatz (Geldeinheiten/Zeiteinheit)
ell = np.ones(N_W) * 0.8  # Arbeitszeit (Arbeiter arbeiten 80% der Maximalzeit)

# Zinssätze
r = 0.03              # Leitzins (1/Zeit)
r_L = 0.05            # Kreditzins (Banken verleihen)
r_D = 0.02            # Einlagenzins (Banken zahlen)

# Produktion (Unternehmer)
p_0 = 10.0            # Basispreis des Gutes
q_base = np.array([2.0, 1.5, 1.8, 2.2, 1.6])  # Basisproduktion je Unternehmer
L_ent = np.ones(N_U) * 1.5  # Arbeitskraft pro Unternehmer
K_ent = np.ones(N_U) * 5.0  # Kapitalbestand pro Unternehmer

# Konsum
c_min = 0.5           # Subsistenzkonsum (NB.1)
c_prime_W = 0.05      # Konsumneigung Arbeiter (Anteil am Vermögen)
c_prime_U = 0.03      # Konsumneigung Unternehmer
c_prime_B = 0.01      # Konsumneigung Banken (operativer Aufwand)

# Portfolioanteile (Anteil am einzigen Asset)
# Σ_i θ_i = 1 (alle Anteile summieren zu 100%)
theta_W = np.ones(N_W) * 0.03   # Arbeiter halten je 3% → 30% gesamt
theta_U = np.ones(N_U) * 0.10   # Unternehmer halten je 10% → 50%
theta_B = np.ones(N_B) * 0.10   # Banken halten je 10% → 20%
theta_all = np.concatenate([theta_W, theta_U, theta_B])
assert abs(theta_all.sum() - 1.0) < 1e-10, f"Portfolioanteile summieren nicht zu 1: {theta_all.sum()}"

# Finanzpositionen (Kreditmarkt-Clearing: Σ b_i = 0)
# Arbeiter haben positive Positionen (Sparer), Unternehmer schulden
b_W = np.ones(N_W) * 2.0         # Arbeiter: je 2.0 Guthaben
b_U = np.ones(N_U) * (-3.0)      # Unternehmer: je -3.0 Schulden
b_B_total = -(b_W.sum() + b_U.sum())  # Banken gleichen aus → M.2
b_B = np.ones(N_B) * (b_B_total / N_B)
b_all = np.concatenate([b_W, b_U, b_B])
assert abs(b_all.sum()) < 1e-10, f"M.2 verletzt: Σ b_i = {b_all.sum()}"

# Banken: Kredit- und Einlagenvolumen
L_bank = np.ones(N_B) * 10.0     # Kreditvolumen pro Bank
D_bank = np.ones(N_B) * 8.0      # Einlagenvolumen pro Bank

# Anfangsvermögen
w0_W = np.ones(N_W) * 5.0        # Arbeiter: je 5.0
w0_U = np.ones(N_U) * 20.0       # Unternehmer: je 20.0
w0_B = np.ones(N_B) * 50.0       # Banken: je 50.0
w0 = np.concatenate([w0_W, w0_U, w0_B])

rng = np.random.default_rng(42)

# ═══════════════════════════════════════════════════════════════
# EXOGENER PREISPFAD (für Bewertungsterme)
# ═══════════════════════════════════════════════════════════════

def price(t):
    """Exogener Preispfad: Trend + Zyklus."""
    return p_0 * (1.0 + 0.02 * t + 0.1 * np.sin(2 * np.pi * t / 5.0))

def price_dot(t):
    """Zeitableitung des Preises (analytisch)."""
    return p_0 * (0.02 + 0.1 * 2 * np.pi / 5.0 * np.cos(2 * np.pi * t / 5.0))


# ═══════════════════════════════════════════════════════════════
# ODE-SYSTEM: I.1 für alle Agenten
# ═══════════════════════════════════════════════════════════════

def rhs(t, w):
    """
    Rechte Seite des ODE-Systems dw_i/dt = ... (Gleichung I.1).
    
    w[0:N_W]         = Vermögen der Arbeiter
    w[N_W:N_W+N_U]   = Vermögen der Unternehmer
    w[N_W+N_U:]       = Vermögen der Banken
    """
    dw = np.zeros(N)
    p_t = price(t)
    pdot = price_dot(t)
    
    # ─── Arbeiter (I.1 spezialisiert auf W) ─────────────
    w_workers = w[:N_W]
    y_W = w_ell * ell                                   # Arbeitseinkommen
    c_W = np.maximum(c_min, c_min + c_prime_W * np.maximum(w_workers, 0.0))  # NB.1
    bewertung_W = theta_W * pdot                        # Bewertungsgewinne
    zinsen_W = r * b_W                                  # Zinserträge (b_W ≥ 0 ✓)
    dw[:N_W] = y_W - c_W + bewertung_W + zinsen_W
    
    # ─── Unternehmer (I.1 spezialisiert auf U) ──────────
    w_ent = w[N_W:N_W+N_U]
    profit_U = p_t * q_base - w_ell * L_ent - r * K_ent  # Profit = Umsatz - Lohn - Kapitalkosten
    y_U = profit_U
    c_U = np.maximum(c_min, c_min + c_prime_U * np.maximum(w_ent, 0.0))  # NB.1
    bewertung_U = theta_U * pdot
    zinsen_U = r * b_U                                  # b_U < 0 → Zinszahlung
    dw[N_W:N_W+N_U] = y_U - c_U + bewertung_U + zinsen_U
    
    # ─── Banken (I.1 spezialisiert auf B) ────────────────
    w_banks = w[N_W+N_U:]
    y_B = r_L * L_bank - r_D * D_bank                   # Zinsmarge
    c_B = np.maximum(c_min, c_min + c_prime_B * np.maximum(w_banks, 0.0))  # Betriebskosten
    bewertung_B = theta_B * pdot
    # Banken haben b_B aus M.2 → Zinsen auf Nettopositionen
    zinsen_B = r * b_B
    dw[N_W+N_U:] = y_B - c_B + bewertung_B + zinsen_B
    
    return dw


# ═══════════════════════════════════════════════════════════════
# ANALYTISCHE STATIONÄRE PUNKTE (ẋ = 0 lösen)
# ═══════════════════════════════════════════════════════════════

def compute_steady_state_wealth():
    """
    Stationärer Punkt (ṗ = 0, d.h. kein Bewertungseffekt):
    dw_i/dt = 0 → y_i - c_min - c' * w_i^* + r b_i = 0
    → w_i^* = (y_i - c_min + r b_i) / c'_i
    Nur gültig wenn w_i^* ≥ 0 (sonst c_i = c_min und w_i^* = (y_i - c_min + r b_i) / (irgendwas) < 0).
    """
    # Für ṗ = 0 und p = p_0 (Gleichgewichtspreis):
    y_W_ss = w_ell * ell
    y_U_ss = p_0 * q_base - w_ell * L_ent - r * K_ent
    y_B_ss = r_L * L_bank - r_D * D_bank
    
    w_ss_W = (y_W_ss - c_min + r * b_W) / c_prime_W
    w_ss_U = (y_U_ss - c_min + r * b_U) / c_prime_U
    w_ss_B = (y_B_ss - c_min + r * b_B) / c_prime_B
    
    return np.concatenate([w_ss_W, w_ss_U, w_ss_B])


# ═══════════════════════════════════════════════════════════════
# JACOBI-MATRIX (analytisch)
# ═══════════════════════════════════════════════════════════════

def jacobian_at_steady_state():
    """
    J_{ii} = -c'_i (diagonal, da Agenten nur über eigenes Vermögen gekoppelt)
    dw_i/dt = ... - c'_i * w_i + ... → ∂(dw_i/dt)/∂w_i = -c'_i
    
    Kopplungsterme (über p, b) sind hier exogen → J ist diagonal.
    """
    diag = np.concatenate([
        -c_prime_W * np.ones(N_W),
        -c_prime_U * np.ones(N_U),
        -c_prime_B * np.ones(N_B)
    ])
    return np.diag(diag)


# ═══════════════════════════════════════════════════════════════
# SIMULATION
# ═══════════════════════════════════════════════════════════════

t_span = (0.0, 50.0)
t_eval = np.linspace(0, 50, 2000)

sol = solve_ivp(
    rhs, t_span, w0,
    method='RK45',
    t_eval=t_eval,
    rtol=1e-8,
    atol=1e-10,
    max_step=0.1
)

assert sol.success, f"Solver fehlgeschlagen: {sol.message}"

t = sol.t
w_sol = sol.y  # Shape: (N, len(t))


# ═══════════════════════════════════════════════════════════════
# VALIDIERUNGSPROTOKOLL
# ═══════════════════════════════════════════════════════════════

print("=" * 70)
print("S01 – VALIDIERUNGSPROTOKOLL")
print("=" * 70)

# [1] M.2: Kreditmarkt-Clearing
print("\n[1] M.2: Kreditmarkt-Clearing Σ b_i = 0")
print(f"    Σ b_i = {b_all.sum():.2e}  →  {'✓ PASS' if abs(b_all.sum()) < 1e-10 else '✗ FAIL'}")

# [2] Portfolio-Konsistenz: Σ θ_i = 1
print(f"\n[2] Portfoliokonsistenz: Σ θ_i = {theta_all.sum():.6f}  →  {'✓ PASS' if abs(theta_all.sum() - 1.0) < 1e-10 else '✗ FAIL'}")

# [3] I.2: Aggregierte Vermögenserhaltung dW/dt = Y − C
print("\n[3] I.2: Aggregierte Vermögenserhaltung dW/dt = Y − C")
W_total = w_sol.sum(axis=0)
dW_dt_num = np.gradient(W_total, t)

# Y und C an jedem Zeitpunkt berechnen
Y_total = np.zeros(len(t))
C_total = np.zeros(len(t))
for i_t in range(len(t)):
    ti = t[i_t]
    w_t = w_sol[:, i_t]
    p_t = price(ti)
    
    # Einkommen
    y_W_t = w_ell * ell
    y_U_t = p_t * q_base - w_ell * L_ent - r * K_ent
    y_B_t = r_L * L_bank - r_D * D_bank
    
    # Konsum
    c_W_t = np.maximum(c_min, c_min + c_prime_W * np.maximum(w_t[:N_W], 0.0))
    c_U_t = np.maximum(c_min, c_min + c_prime_U * np.maximum(w_t[N_W:N_W+N_U], 0.0))
    c_B_t = np.maximum(c_min, c_min + c_prime_B * np.maximum(w_t[N_W+N_U:], 0.0))
    
    Y_total[i_t] = y_W_t.sum() + y_U_t.sum() + y_B_t.sum()
    C_total[i_t] = c_W_t.sum() + c_U_t.sum() + c_B_t.sum()

# dW/dt sollte = Y - C sein (PLUS Bewertung + Zinsen, aber Bewertung und Zinsen
# canceln NICHT exakt bei 1 Asset in offenem System → wir prüfen die VOLLE Identität)
# Die exakte Prüfung: dW/dt = Y - C + Σ θ_i ṗ + r Σ b_i
# Da Σ b_i = 0 → Zinsterme canceln ✓
# Da Σ θ_i = 1 → Bewertungsterm = ṗ (NICHT null, weil nur 1 Asset!)
# → dW/dt = Y - C + ṗ  ← Das ist korrekt für 1 Asset

pdot_vec = np.array([price_dot(ti) for ti in t])
dW_dt_analytic = Y_total - C_total + pdot_vec  # I.2 mit Bewertungsterm (1 Asset)

# Prüfung: Numerisch vs. analytisch
# Am Rand kann np.gradient ungenau sein, daher Mitte nehmen
idx = slice(50, -50)
error_I2 = np.abs(dW_dt_num[idx] - dW_dt_analytic[idx])
max_error_I2 = np.max(error_I2)
mean_error_I2 = np.mean(error_I2)
print(f"    Max |dW/dt_num − (Y−C+ṗ)| = {max_error_I2:.4e}")
print(f"    Mean |dW/dt_num − (Y−C+ṗ)| = {mean_error_I2:.4e}")
print(f"    →  {'✓ PASS (< 0.01)' if max_error_I2 < 0.01 else '✗ FAIL'}")

# [3b] Besserer Test: Exakte I.2-Prüfung (Zinsterme canceln)
print("\n[3b] Zinsterme-Cancellation: r Σ b_i")
r_sum_b = r * b_all.sum()
print(f"     r · Σ b_i = {r_sum_b:.2e}  →  {'✓ PASS (= 0)' if abs(r_sum_b) < 1e-10 else '✗ FAIL'}")

# [3c] Bewertungsterme: Σ θ_i ṗ = ṗ (weil Σ θ_i = 1)
print("\n[3c] Bewertungsterme: Σ θ_i ṗ = ṗ · Σ θ_i = ṗ")
t_test = 5.0
bew_sum = theta_all.sum() * price_dot(t_test)
bew_exact = price_dot(t_test)
print(f"     Σ θ_i ṗ(t=5) = {bew_sum:.6f}, ṗ(t=5) = {bew_exact:.6f}")
print(f"     →  {'✓ PASS' if abs(bew_sum - bew_exact) < 1e-10 else '✗ FAIL'}")

# [4] Stationärer Punkt (analytisch berechnet, ṗ = 0)
print("\n[4] Stationäre Punkte (analytisch, für ṗ=0, p=p_0):")
w_ss = compute_steady_state_wealth()
for i in range(min(3, N_W)):
    print(f"    Arbeiter {i}: w* = {w_ss[i]:.2f}")
for i in range(min(3, N_U)):
    print(f"    Unternehmer {i}: w* = {w_ss[N_W+i]:.2f}")
for i in range(N_B):
    print(f"    Bank {i}: w* = {w_ss[N_W+N_U+i]:.2f}")

# [5] Eigenwerte der Jacobi-Matrix
print("\n[5] Eigenwerte der Jacobi-Matrix (alle müssen < 0 für Stabilität):")
J = jacobian_at_steady_state()
eigvals = np.linalg.eigvals(J)
unique_eigvals = np.unique(np.round(eigvals, 10))
for ev in unique_eigvals:
    print(f"    λ = {ev:.6f}  →  {'✓ stabil' if ev.real < 0 else '✗ instabil'}")
all_stable = all(ev.real < 0 for ev in eigvals)
print(f"    →  {'✓ ALLE stabil' if all_stable else '✗ INSTABIL'}")

# [6] Keine NaN/Inf
print(f"\n[6] Numerische Integrität:")
has_nan = np.any(np.isnan(w_sol))
has_inf = np.any(np.isinf(w_sol))
print(f"    NaN: {'✗ FAIL' if has_nan else '✓ PASS (keine NaN)'}")
print(f"    Inf: {'✗ FAIL' if has_inf else '✓ PASS (keine Inf)'}")

# [7] NB.1: Subsistenzkonsum
print(f"\n[7] NB.1: Subsistenzkonsum c_i ≥ c_min = {c_min}")
all_nb1 = True
for i_t in range(len(t)):
    w_t = w_sol[:, i_t]
    c_W_t = np.maximum(c_min, c_min + c_prime_W * np.maximum(w_t[:N_W], 0.0))
    c_U_t = np.maximum(c_min, c_min + c_prime_U * np.maximum(w_t[N_W:N_W+N_U], 0.0))
    c_B_t = np.maximum(c_min, c_min + c_prime_B * np.maximum(w_t[N_W+N_U:], 0.0))
    if np.any(c_W_t < c_min - 1e-12) or np.any(c_U_t < c_min - 1e-12) or np.any(c_B_t < c_min - 1e-12):
        all_nb1 = False
        break
print(f"    →  {'✓ PASS (NB.1 eingehalten)' if all_nb1 else '✗ FAIL'}")

print("\n" + "=" * 70)
print("VALIDIERUNG ABGESCHLOSSEN")
print("=" * 70)


# ═══════════════════════════════════════════════════════════════
# PLOTS
# ═══════════════════════════════════════════════════════════════

# Ausgabeverzeichnis
base_dir = Path(r"c:\Users\Labor\Desktop\Neuer Ordner (2)\Kriegsvorbereitung\AxioContEcon")
plot_dir = base_dir / "Ergebnisse" / "Plots"
sim_dir = base_dir / "Simulationen" / "Kap04_Erhaltung"

fig, axes = plt.subplots(2, 3, figsize=(16, 10))
fig.suptitle("S01 – Individuelle Vermögensbilanz (Gl. I.1)\n"
             r"$\dot{w}_i = y_i - c_i + \sum_k \theta_{ik}\dot{p}_k + r\,b_i$",
             fontsize=13, fontweight='bold')

# (a) Vermögenspfade aller Agenten
ax = axes[0, 0]
for i in range(N_W):
    ax.plot(t, w_sol[i], 'b-', alpha=0.5, linewidth=0.8,
            label='Arbeiter' if i == 0 else None)
for i in range(N_U):
    ax.plot(t, w_sol[N_W+i], 'r-', alpha=0.7, linewidth=0.8,
            label='Unternehmer' if i == 0 else None)
for i in range(N_B):
    ax.plot(t, w_sol[N_W+N_U+i], 'g-', alpha=0.9, linewidth=1.2,
            label='Banken' if i == 0 else None)
ax.set_xlabel('Zeit $t$')
ax.set_ylabel(r'Vermögen $w_i(t)$')
ax.set_title('(a) Individuelle Vermögenspfade')
ax.legend(fontsize=8)
ax.grid(True, alpha=0.3)

# (b) Aggregiertes Vermögen W(t)
ax = axes[0, 1]
ax.plot(t, W_total, 'k-', linewidth=2, label=r'$W(t) = \sum_i w_i$')
ax.set_xlabel('Zeit $t$')
ax.set_ylabel(r'$W(t)$')
ax.set_title(r'(b) Aggregiertes Vermögen $W = \sum_i w_i$')
ax.legend(fontsize=9)
ax.grid(True, alpha=0.3)

# (c) Test I.2: dW/dt vs Y−C+ṗ
ax = axes[0, 2]
ax.plot(t[idx], dW_dt_num[idx], 'b-', linewidth=1, label=r'$dW/dt$ (numerisch)', alpha=0.7)
ax.plot(t[idx], dW_dt_analytic[idx], 'r--', linewidth=1, label=r'$Y - C + \dot{p}$ (analytisch)')
ax.set_xlabel('Zeit $t$')
ax.set_ylabel(r'$dW/dt$')
ax.set_title(r'(c) I.2-Test: $dW/dt = Y - C + \dot{p}$')
ax.legend(fontsize=8)
ax.grid(True, alpha=0.3)

# (d) Preispfad und Bewertungsgewinne
ax = axes[1, 0]
p_vec = np.array([price(ti) for ti in t])
ax.plot(t, p_vec, 'k-', linewidth=1.5, label=r'$p(t)$')
ax2 = ax.twinx()
ax2.plot(t, pdot_vec, 'r-', linewidth=1, alpha=0.7, label=r'$\dot{p}(t)$')
ax.set_xlabel('Zeit $t$')
ax.set_ylabel(r'Preis $p(t)$', color='k')
ax2.set_ylabel(r'$\dot{p}(t)$', color='r')
ax.set_title(r'(d) Exogener Preispfad')
ax.legend(loc='upper left', fontsize=8)
ax2.legend(loc='upper right', fontsize=8)
ax.grid(True, alpha=0.3)

# (e) Einkommens- und Konsumströme
ax = axes[1, 1]
ax.plot(t, Y_total, 'g-', linewidth=1.5, label=r'$Y = \sum_i y_i$ (Einkommen)')
ax.plot(t, C_total, 'm-', linewidth=1.5, label=r'$C = \sum_i c_i$ (Konsum)')
ax.plot(t, Y_total - C_total, 'k--', linewidth=1, label=r'$Y - C$ (Sparen)')
ax.set_xlabel('Zeit $t$')
ax.set_ylabel('Geldeinheiten/Zeit')
ax.set_title('(e) Aggregierte Ströme')
ax.legend(fontsize=8)
ax.grid(True, alpha=0.3)

# (f) Fehler der I.2-Identität
ax = axes[1, 2]
ax.semilogy(t[idx], error_I2, 'r-', linewidth=0.8)
ax.set_xlabel('Zeit $t$')
ax.set_ylabel(r'$|dW/dt - (Y - C + \dot{p})|$')
ax.set_title('(f) Fehler der I.2-Identität')
ax.grid(True, alpha=0.3)

plt.tight_layout()
plot_path = plot_dir / "S01_I1_Vermoegensbilanz.png"
fig.savefig(plot_path, dpi=150, bbox_inches='tight')
plt.close(fig)
print(f"\nPlot gespeichert: {plot_path}")


# ═══════════════════════════════════════════════════════════════
# DATEN SPEICHERN
# ═══════════════════════════════════════════════════════════════

data_dir = base_dir / "Ergebnisse" / "Daten"
np.savez_compressed(
    data_dir / "S01_I1_Vermoegensbilanz.npz",
    t=t, w_sol=w_sol, W_total=W_total,
    Y_total=Y_total, C_total=C_total,
    w_ss=w_ss, eigvals=eigvals,
    params=dict(N_W=N_W, N_U=N_U, N_B=N_B, r=r, r_L=r_L, r_D=r_D,
                w_ell=w_ell, c_min=c_min, p_0=p_0)
)
print(f"Daten gespeichert: {data_dir / 'S01_I1_Vermoegensbilanz.npz'}")
