"""
╔══════════════════════════════════════════════════════════════════════╗
║  S02 – Aggregierte Vermögenserhaltung (Gleichung I.2)              ║
║  Gleichungen: I.2 (§4.2), Proposition 4.1, M.2 (§4.3)            ║
║  Ökonoaxiomatik – Monographie v2                                   ║
╚══════════════════════════════════════════════════════════════════════╝

Gleichungen (exakt aus Monographie):
─────────────────────────────────────
I.1 (Individuelle Vermögensbilanz, §4.1):
    dw_i/dt = y_i − c_i + Σ_k θ_{ik} ṗ_k + r b_i

I.2 (Aggregierte Vermögenserhaltung, §4.2):
    dW/dt = Y − C
    wobei W = Σ_i w_i,  Y = Σ_i y_i,  C = Σ_i c_i

Proposition 4.1 (§4.2):
    Σ_i b_i = 0                 (Nullsumme Finanzpositionen, M.2)
    Σ_i Σ_k θ_{ik} ṗ_k = 0    (Nullsumme Bewertungsgewinne)

Ableitung (Monographie §4.2):
    dW/dt = Σ dw_i/dt = Y − C + [Σ_i Σ_k θ_{ik} ṗ_k] + [r Σ_i b_i]
    Behauptung: Letzten beiden Terme = 0.

Reduktion / Vereinfachung:
──────────────────────────
- K = 3 Güter mit unterschiedlichen exogenen Preispfaden
- N = 14 Agenten (8 Arbeiter, 4 Unternehmer, 2 Banken)
- Zwei Szenarien werden GLEICHZEITIG simuliert:

  Szenario A: FINANZIELLE Assets (Zero-Net-Supply)
    → Für jedes k: Σ_i θ_{ik} = 0  (Netto-Null, da Long = Short)
    → Prop. 4.1 sollte EXAKT gelten: dW/dt = Y − C

  Szenario B: REALE Assets (Positive Net Supply)
    → Für jedes k: Σ_i θ_{ik} = 1  (alle Anteile vergeben)
    → Bewertungsresiduum: dW/dt = Y − C + Σ_k ṗ_k

- Konsum: c_i = c_min + c' · max(w_i, 0)  (NB.1)
- Kreditpositionen: Σ b_i = 0 (M.2)

Analytische Ergebnisse:
───────────────────────
1. Szenario A: W(T) − W(0) = ∫₀ᵀ (Y−C) dt   (exakt bis Solver-Toleranz)
2. Szenario B: W(T) − W(0) = ∫₀ᵀ (Y−C) dt + Σ_k [p_k(T) − p_k(0)]
3. Zinsterme: r·Σ_i b_i = 0 zu JEDEM Zeitpunkt (exakt, da b_i konstant)
4. Bewertungsterme A: Σ_i Σ_k θ_{ik}^A ṗ_k = 0 zu jedem Zeitpunkt
5. Bewertungsterme B: Σ_i Σ_k θ_{ik}^B ṗ_k = Σ_k ṗ_k zu jedem Zeitpunkt
"""

import numpy as np
from scipy.integrate import solve_ivp, trapezoid
import matplotlib.pyplot as plt
import matplotlib
from pathlib import Path

matplotlib.rcParams['mathtext.fontset'] = 'cm'
matplotlib.rcParams['font.size'] = 10

# ═══════════════════════════════════════════════════════════════
# PARAMETER
# ═══════════════════════════════════════════════════════════════

N_W = 8    # Arbeiter
N_U = 4    # Unternehmer
N_B = 2    # Banken
N = N_W + N_U + N_B
K = 3      # Güter

rng = np.random.default_rng(42)

# Zinssätze
r = 0.03
r_L = 0.05
r_D = 0.02

# Lohn und Arbeitszeit
w_ell = 1.0
ell = 0.5 + 0.5 * rng.random(N_W)  # Heterogene Arbeitszeiten [0.5, 1.0]

# Produktion (Unternehmer, je 1 Gut spezialisiert)
# Unternehmer j produziert Gut (j % K)
q_base = 1.5 + rng.random(N_U)          # Basisproduktion [1.5, 2.5]
L_ent = 1.0 + 0.5 * rng.random(N_U)     # Arbeitskraft [1.0, 1.5]
K_ent = 3.0 + 2.0 * rng.random(N_U)     # Kapitalbestand [3.0, 5.0]

# Konsum
c_min = 0.3
c_prime = np.concatenate([
    0.04 * np.ones(N_W),   # Konsumneigung Arbeiter
    0.025 * np.ones(N_U),  # Konsumneigung Unternehmer
    0.008 * np.ones(N_B)   # Betriebskosten Banken
])

# ─── Finanzpositionen: M.2 exakt ────────────────────────
b = np.zeros(N)
b[:N_W] = 1.0 + rng.random(N_W)          # Arbeiter: Guthaben [1, 2]
b[N_W:N_W+N_U] = -2.0 - rng.random(N_U)  # Unternehmer: Schulden [-2, -3]
b[N_W+N_U:] = 0.0                         # Banken füllen auf
b[N_W+N_U:] = -(b[:N_W+N_U].sum()) / N_B  # M.2: Σ b_i = 0
assert abs(b.sum()) < 1e-14, f"M.2 verletzt: Σ b_i = {b.sum()}"

# ─── Banken: Kredit- und Einlagenvolumen ─────────────────
L_bank = 8.0 + 2 * rng.random(N_B)   # [8, 10]
D_bank = 6.0 + 2 * rng.random(N_B)   # [6, 8]

# ─── Portfolioanteile ────────────────────────────────────

# SZENARIO A: Zero-Net-Supply (Finanzkontrakte)
# Für jedes Gut k: Σ_i θ_{ik}^A = 0  (einige long, einige short)
theta_A = rng.standard_normal((N, K)) * 0.05
# Erzwinge Σ_i θ_{ik} = 0 für jedes k:
theta_A -= theta_A.mean(axis=0, keepdims=True)
for k_idx in range(K):
    assert abs(theta_A[:, k_idx].sum()) < 1e-14, \
        f"Szenario A: Σ θ[:{k_idx}] = {theta_A[:, k_idx].sum()}"

# SZENARIO B: Reale Assets (Positive Net Supply)
# Für jedes Gut k: Σ_i θ_{ik}^B = 1  (alle Anteile vergeben)
theta_B_raw = np.abs(rng.standard_normal((N, K))) + 0.01
theta_B = theta_B_raw / theta_B_raw.sum(axis=0, keepdims=True)  # Normieren auf Σ=1
for k_idx in range(K):
    assert abs(theta_B[:, k_idx].sum() - 1.0) < 1e-14, \
        f"Szenario B: Σ θ[:{k_idx}] = {theta_B[:, k_idx].sum()}"

# ─── Anfangsvermögen ─────────────────────────────────────
w0_base = np.concatenate([
    5.0 + 2 * rng.random(N_W),    # Arbeiter: [5, 7]
    15.0 + 5 * rng.random(N_U),   # Unternehmer: [15, 20]
    40.0 + 10 * rng.random(N_B)   # Banken: [40, 50]
])

# ═══════════════════════════════════════════════════════════════
# EXOGENE PREISPFADE (K = 3 Güter)
# ═══════════════════════════════════════════════════════════════

p0 = np.array([10.0, 15.0, 8.0])  # Basispreise

def prices(t):
    """K=3 exogene Preise mit unterschiedlicher Dynamik."""
    return np.array([
        p0[0] * (1.0 + 0.02 * t + 0.08 * np.sin(2*np.pi*t/6.0)),   # Trend + langsamer Zyklus
        p0[1] * (1.0 - 0.01 * t + 0.12 * np.sin(2*np.pi*t/4.0)),   # Fallender Trend + Zyklus
        p0[2] * (1.0 + 0.03 * t + 0.05 * np.sin(2*np.pi*t/10.0))   # Starker Trend + langsam
    ])

def prices_dot(t):
    """Analytische Zeitableitung der Preise."""
    return np.array([
        p0[0] * (0.02 + 0.08 * 2*np.pi/6.0 * np.cos(2*np.pi*t/6.0)),
        p0[1] * (-0.01 + 0.12 * 2*np.pi/4.0 * np.cos(2*np.pi*t/4.0)),
        p0[2] * (0.03 + 0.05 * 2*np.pi/10.0 * np.cos(2*np.pi*t/10.0))
    ])


# ═══════════════════════════════════════════════════════════════
# ODE-SYSTEME: Szenario A und B simultan
# ═══════════════════════════════════════════════════════════════
# Zustandsvektor: [w_A(0..N-1), w_B(0..N-1)] → 2N Variablen

def rhs(t, state):
    """RHS für beide Szenarien simultan."""
    w_A = state[:N]
    w_B = state[N:]
    
    p_t = prices(t)
    pdot = prices_dot(t)
    
    dw_A = np.zeros(N)
    dw_B = np.zeros(N)
    
    for scenario, (w, theta, dw) in enumerate([
        (w_A, theta_A, dw_A),
        (w_B, theta_B, dw_B)
    ]):
        for i in range(N):
            # Einkommen nach Klasse
            if i < N_W:
                # Arbeiter
                y_i = w_ell * ell[i]
            elif i < N_W + N_U:
                # Unternehmer: produziert Gut (j % K)
                j = i - N_W
                k_prod = j % K
                y_i = p_t[k_prod] * q_base[j] - w_ell * L_ent[j] - r * K_ent[j]
            else:
                # Bank
                j = i - N_W - N_U
                y_i = r_L * L_bank[j] - r_D * D_bank[j]
            
            # Konsum (NB.1: c ≥ c_min)
            c_i = max(c_min, c_min + c_prime[i] * max(w[i], 0.0))
            
            # Bewertung: Σ_k θ_{ik} ṗ_k
            bewertung = np.dot(theta[i, :], pdot)
            
            # Zinsen
            zinsen = r * b[i]
            
            dw[i] = y_i - c_i + bewertung + zinsen
    
    return np.concatenate([dw_A, dw_B])


# ═══════════════════════════════════════════════════════════════
# SIMULATION
# ═══════════════════════════════════════════════════════════════

T_end = 40.0
t_eval = np.linspace(0, T_end, 2000)
state0 = np.concatenate([w0_base.copy(), w0_base.copy()])  # Gleiche ICs

sol = solve_ivp(
    rhs, (0.0, T_end), state0,
    method='RK45',
    t_eval=t_eval,
    rtol=1e-10, atol=1e-12,
    max_step=0.05
)
assert sol.success, f"Solver fehlgeschlagen: {sol.message}"

t = sol.t
w_A_sol = sol.y[:N, :]     # Szenario A: alle Agenten
w_B_sol = sol.y[N:, :]     # Szenario B: alle Agenten


# ═══════════════════════════════════════════════════════════════
# BERECHNUNG DER AGGREGIERTEN GRÖßEN
# ═══════════════════════════════════════════════════════════════

W_A = w_A_sol.sum(axis=0)  # Aggregiertes Vermögen Szenario A
W_B = w_B_sol.sum(axis=0)  # Aggregiertes Vermögen Szenario B

# Y(t), C(t) für beide Szenarien
Y_A = np.zeros(len(t))
Y_B = np.zeros(len(t))
C_A = np.zeros(len(t))
C_B = np.zeros(len(t))
Bew_A = np.zeros(len(t))   # Aggregierter Bewertungsterm Szenario A
Bew_B = np.zeros(len(t))   # Aggregierter Bewertungsterm Szenario B
Zins_agg = np.zeros(len(t))  # r · Σ b_i (sollte = 0)

for it in range(len(t)):
    ti = t[it]
    p_t = prices(ti)
    pdot = prices_dot(ti)
    
    for scenario, (w_sol, Y_arr, C_arr, Bew_arr, theta) in enumerate([
        (w_A_sol, Y_A, C_A, Bew_A, theta_A),
        (w_B_sol, Y_B, C_B, Bew_B, theta_B)
    ]):
        y_total = 0.0
        c_total = 0.0
        bew_total = 0.0
        
        for i in range(N):
            # Einkommen
            if i < N_W:
                y_i = w_ell * ell[i]
            elif i < N_W + N_U:
                j = i - N_W
                k_prod = j % K
                y_i = p_t[k_prod] * q_base[j] - w_ell * L_ent[j] - r * K_ent[j]
            else:
                j = i - N_W - N_U
                y_i = r_L * L_bank[j] - r_D * D_bank[j]
            
            c_i = max(c_min, c_min + c_prime[i] * max(w_sol[i, it], 0.0))
            bew_i = np.dot(theta[i, :], pdot)
            
            y_total += y_i
            c_total += c_i
            bew_total += bew_i
        
        Y_arr[it] = y_total
        C_arr[it] = c_total
        Bew_arr[it] = bew_total
    
    Zins_agg[it] = r * b.sum()

# Preise an Start und Ende
p_start = prices(0.0)
p_end = prices(T_end)
Delta_p = (p_end - p_start).sum()   # Σ_k [p_k(T) − p_k(0)]


# ═══════════════════════════════════════════════════════════════
# INTEGRALE (exakt via Trapezregel, nicht np.gradient!)
# ═══════════════════════════════════════════════════════════════

integral_YC_A = trapezoid(Y_A - C_A, t)       # ∫(Y_A − C_A)dt
integral_YC_B = trapezoid(Y_B - C_B, t)       # ∫(Y_B − C_B)dt
integral_Bew_A = trapezoid(Bew_A, t)           # ∫(Σ θ_A ṗ)dt
integral_Bew_B = trapezoid(Bew_B, t)           # ∫(Σ θ_B ṗ)dt
integral_Zins = trapezoid(Zins_agg, t)         # ∫(r·Σb)dt — sollte ≈ 0

DeltaW_A = W_A[-1] - W_A[0]    # Tatsächliche Änderung Szenario A
DeltaW_B = W_B[-1] - W_B[0]    # Tatsächliche Änderung Szenario B


# ═══════════════════════════════════════════════════════════════
# VALIDIERUNGSPROTOKOLL
# ═══════════════════════════════════════════════════════════════

print("=" * 72)
print("S02 – VALIDIERUNGSPROTOKOLL: Aggregierte Vermögenserhaltung I.2")
print("=" * 72)

# [1] M.2: Σ b_i = 0
print(f"\n[1] M.2: Kreditmarkt-Clearing")
print(f"    Σ b_i = {b.sum():.2e}  →  {'✓ PASS' if abs(b.sum()) < 1e-12 else '✗ FAIL'}")

# [2] Portfoliokonsistenz
print(f"\n[2] Portfoliokonsistenz:")
for k_idx in range(K):
    sum_A = theta_A[:, k_idx].sum()
    sum_B = theta_B[:, k_idx].sum()
    print(f"    Gut {k_idx}: Σ θ_A = {sum_A:+.2e} (Zero-Net),"
          f"  Σ θ_B = {sum_B:.6f} (Real)")

# [3] Zinsterme canceln
print(f"\n[3] Zinsterme: r · Σ b_i = {Zins_agg[0]:.2e}")
print(f"    ∫(r·Σb)dt = {integral_Zins:.2e}  →  {'✓ PASS' if abs(integral_Zins) < 1e-10 else '✗ FAIL'}")

# [4] Bewertungsterme
print(f"\n[4] Bewertungsterme (Proposition 4.1):")
print(f"    Szenario A (Zero-Net-Supply):")
print(f"      Σ_i Σ_k θ_A ṗ(t=0)  = {Bew_A[0]:+.4e}")
print(f"      Σ_i Σ_k θ_A ṗ(t=20) = {Bew_A[len(t)//2]:+.4e}")
print(f"      max|Bew_A(t)|        = {np.max(np.abs(Bew_A)):.4e}")
print(f"      ∫ Bew_A dt           = {integral_Bew_A:+.4e}")
bew_A_pass = np.max(np.abs(Bew_A)) < 1e-10
print(f"      →  {'✓ PASS: Bewertung = 0 exakt' if bew_A_pass else '✗ FAIL'}")

print(f"    Szenario B (Reale Assets, Σ θ = 1):")
# Analytisch: Σ_i Σ_k θ_B ṗ = Σ_k ṗ_k
pdot_sum = np.array([prices_dot(ti).sum() for ti in t])
bew_B_error = np.max(np.abs(Bew_B - pdot_sum))
print(f"      Σ_i Σ_k θ_B ṗ(t=0)  = {Bew_B[0]:+.4f}")
print(f"      Σ_k ṗ_k(t=0)         = {pdot_sum[0]:+.4f}")
print(f"      max|Bew_B − Σ ṗ_k|   = {bew_B_error:.4e}")
print(f"      ∫ Bew_B dt            = {integral_Bew_B:+.4f}")
print(f"      Σ_k Δp_k             = {Delta_p:+.4f}")
bew_B_consistent = bew_B_error < 1e-10
print(f"      →  {'✓ PASS: Bew_B = Σ ṗ_k' if bew_B_consistent else '✗ FAIL'}")

# [5] KERNTEST: I.2 Identität
print(f"\n{'─'*72}")
print(f"[5] KERNTEST: I.2 – Aggregierte Vermögenserhaltung")
print(f"{'─'*72}")

# Szenario A: dW/dt = Y − C exakt (Prop. 4.1 erfüllt)
error_A = abs(DeltaW_A - integral_YC_A)
rel_error_A = error_A / max(abs(DeltaW_A), 1e-15)
print(f"\n    SZENARIO A (Zero-Net-Supply Assets):")
print(f"      ΔW_A            = {DeltaW_A:+.6f}")
print(f"      ∫(Y_A − C_A)dt = {integral_YC_A:+.6f}")
print(f"      Fehler           = {error_A:.4e}")
print(f"      Rel. Fehler      = {rel_error_A:.4e}")
I2_A_pass = rel_error_A < 1e-4
print(f"      →  {'✓ PASS: I.2 gilt EXAKT' if I2_A_pass else '✗ FAIL'}")

# Szenario B: dW/dt = Y − C + Σ ṗ
error_B_naive = abs(DeltaW_B - integral_YC_B)
error_B_corrected = abs(DeltaW_B - integral_YC_B - integral_Bew_B)
rel_error_B_naive = error_B_naive / max(abs(DeltaW_B), 1e-15)
rel_error_B_corrected = error_B_corrected / max(abs(DeltaW_B), 1e-15)

print(f"\n    SZENARIO B (Reale Assets, Σ θ = 1):")
print(f"      ΔW_B                      = {DeltaW_B:+.6f}")
print(f"      ∫(Y_B − C_B)dt           = {integral_YC_B:+.6f}")
print(f"      |ΔW − ∫(Y−C)dt|          = {error_B_naive:.4f}  (OHNE Bewertungskorrektur)")
print(f"      ∫(Bew_B)dt               = {integral_Bew_B:+.4f}")
print(f"      |ΔW − ∫(Y−C)dt − ∫Bew|  = {error_B_corrected:.4e}  (MIT Korrektur)")
print(f"      Rel. Fehler (korrigiert)  = {rel_error_B_corrected:.4e}")
I2_B_corrected_pass = rel_error_B_corrected < 1e-4
print(f"      →  I.2 OHNE Korrektur: {'GILT NICHT' if error_B_naive > 0.1 else 'gilt'}"
      f" (Differenz = {error_B_naive:.2f})")
print(f"      →  I.2 MIT Bewertung:  {'✓ PASS' if I2_B_corrected_pass else '✗ FAIL'}"
      f" (Fehler = {error_B_corrected:.2e})")

# [5c] Interpretation
print(f"\n    INTERPRETATION:")
print(f"      Die Monographie-Behauptung I.2: dW/dt = Y − C gilt EXAKT,")
print(f"      WENN θ_{'{ik}'} als Netto-Finanzpositionen (Zero-Net-Supply) interpretiert werden.")
print(f"      Für reale Assets mit Σ_i θ_{'{ik}'} = 1 gilt stattdessen:")
print(f"      dW/dt = Y − C + Σ_k ṗ_k  (Bewertungsresiduum = {integral_Bew_B:+.2f})")

# [6] Numerische Integrität
print(f"\n[6] Numerische Integrität:")
has_nan = np.any(np.isnan(sol.y))
has_inf = np.any(np.isinf(sol.y))
w_min = np.min(sol.y)
print(f"    NaN: {'✗' if has_nan else '✓ keine'}")
print(f"    Inf: {'✗' if has_inf else '✓ keine'}")
print(f"    min(w): {w_min:.2f}")

# [7] Subsistenz NB.1
print(f"\n[7] NB.1 Subsistenzkonsum: c_i ≥ {c_min}  →  ✓ PASS (by construction)")

# [8] Eigenwerte / Stabilität
print(f"\n[8] Stabilität:")
print(f"    J_ii = -c'_i (diagonal, da Agenten bei exogenen Preisen entkoppelt)")
print(f"    Eigenwerte: λ = -c'_i < 0 für alle i  →  ✓ asymptotisch stabil")
unique_cprimes = np.unique(c_prime)
for cp in unique_cprimes:
    t_half = np.log(2) / cp
    print(f"    c' = {cp:.3f} → λ = {-cp:.4f}, t_1/2 = {t_half:.1f}")

print(f"\n{'='*72}")
print(f"VALIDIERUNG ABGESCHLOSSEN")
print(f"{'='*72}")


# ═══════════════════════════════════════════════════════════════
# PLOTS
# ═══════════════════════════════════════════════════════════════

base_dir = Path(r"c:\Users\Labor\Desktop\Neuer Ordner (2)\Kriegsvorbereitung\AxioContEcon")
plot_dir = base_dir / "Ergebnisse" / "Plots"

fig, axes = plt.subplots(2, 3, figsize=(17, 11))
fig.suptitle("S02 – Aggregierte Vermögenserhaltung (Gl. I.2)\n"
             r"$dW/dt = Y - C$ (Proposition 4.1: Nullsumme Bewertung & Zinsen)",
             fontsize=13, fontweight='bold')

# (a) Aggregiertes Vermögen W(t) — beide Szenarien
ax = axes[0, 0]
ax.plot(t, W_A, 'b-', linewidth=2, label=r'$W_A(t)$ (Zero-Net-Supply)')
ax.plot(t, W_B, 'r-', linewidth=2, label=r'$W_B(t)$ (Reale Assets)')
ax.set_xlabel('Zeit $t$')
ax.set_ylabel(r'$W(t) = \sum_i w_i$')
ax.set_title('(a) Aggregiertes Vermögen')
ax.legend(fontsize=8)
ax.grid(True, alpha=0.3)

# (b) Kumulative Integrale vs. ΔW — Szenario A
ax = axes[0, 1]
cum_YC_A = np.array([trapezoid((Y_A - C_A)[:j+1], t[:j+1]) if j > 0 else 0.0
                      for j in range(len(t))])
ax.plot(t, W_A - W_A[0], 'b-', linewidth=2, label=r'$\Delta W_A(t)$')
ax.plot(t, cum_YC_A, 'k--', linewidth=1.5, label=r'$\int_0^t (Y-C)\,ds$')
ax.set_xlabel('Zeit $t$')
ax.set_ylabel('Geldeinheiten')
ax.set_title(r'(b) Szen. A: $\Delta W = \int(Y-C)dt$  ✓')
ax.legend(fontsize=8)
ax.grid(True, alpha=0.3)

# (c) Kumulative Integrale vs. ΔW — Szenario B
ax = axes[0, 2]
cum_YC_B = np.array([trapezoid((Y_B - C_B)[:j+1], t[:j+1]) if j > 0 else 0.0
                      for j in range(len(t))])
cum_Bew_B = np.array([trapezoid(Bew_B[:j+1], t[:j+1]) if j > 0 else 0.0
                       for j in range(len(t))])
ax.plot(t, W_B - W_B[0], 'r-', linewidth=2, label=r'$\Delta W_B(t)$')
ax.plot(t, cum_YC_B, 'k--', linewidth=1.5, label=r'$\int(Y-C)dt$ (ohne Bew.)')
ax.plot(t, cum_YC_B + cum_Bew_B, 'g:', linewidth=2,
        label=r'$\int(Y-C)dt + \int\sum\dot{p}\,dt$')
ax.set_xlabel('Zeit $t$')
ax.set_ylabel('Geldeinheiten')
ax.set_title(r'(c) Szen. B: $\Delta W = \int(Y-C)dt + \sum\Delta p_k$')
ax.legend(fontsize=7)
ax.grid(True, alpha=0.3)

# (d) Bewertungsterme über die Zeit
ax = axes[1, 0]
ax.plot(t, Bew_A, 'b-', linewidth=1.5, label=r'Szen. A: $\sum_i\sum_k \theta^A_{ik}\dot{p}_k$')
ax.plot(t, Bew_B, 'r-', linewidth=1.5, label=r'Szen. B: $\sum_i\sum_k \theta^B_{ik}\dot{p}_k$')
ax.plot(t, pdot_sum, 'k:', linewidth=1, label=r'$\sum_k \dot{p}_k$ (analytisch)')
ax.axhline(0, color='gray', linewidth=0.5)
ax.set_xlabel('Zeit $t$')
ax.set_ylabel('Bewertungsterm')
ax.set_title('(d) Bewertungsterme (Prop. 4.1)')
ax.legend(fontsize=7)
ax.grid(True, alpha=0.3)

# (e) Preispfade der 3 Güter
ax = axes[1, 1]
p_array = np.array([prices(ti) for ti in t])
for k_idx in range(K):
    ax.plot(t, p_array[:, k_idx], linewidth=1.5,
            label=f'$p_{k_idx+1}(t)$')
ax.set_xlabel('Zeit $t$')
ax.set_ylabel('Preis')
ax.set_title(f'(e) Exogene Preise ($K={K}$ Güter)')
ax.legend(fontsize=9)
ax.grid(True, alpha=0.3)

# (f) Fehler der I.2-Identität (beide Szenarien)
ax = axes[1, 2]
err_A_cum = np.abs((W_A - W_A[0]) - cum_YC_A)
err_B_cum = np.abs((W_B - W_B[0]) - cum_YC_B - cum_Bew_B)
ax.semilogy(t[1:], err_A_cum[1:] + 1e-16, 'b-', linewidth=1,
            label='Szen. A: $|\\Delta W - \\int(Y-C)|$')
ax.semilogy(t[1:], err_B_cum[1:] + 1e-16, 'r-', linewidth=1,
            label='Szen. B: $|\\Delta W - \\int(Y-C) - \\int\\sum\\dot{p}|$')
ax.set_xlabel('Zeit $t$')
ax.set_ylabel('Absoluter Fehler')
ax.set_title('(f) Residuum der I.2-Identität')
ax.legend(fontsize=7)
ax.grid(True, alpha=0.3)

plt.tight_layout()
plot_path = plot_dir / "S02_I2_Aggregierte_Vermoegenserh.png"
fig.savefig(plot_path, dpi=150, bbox_inches='tight')
plt.close(fig)
print(f"\nPlot gespeichert: {plot_path}")


# ═══════════════════════════════════════════════════════════════
# DATEN SPEICHERN
# ═══════════════════════════════════════════════════════════════

data_dir = base_dir / "Ergebnisse" / "Daten"
np.savez_compressed(
    data_dir / "S02_I2_Aggregierte_Vermoegenserh.npz",
    t=t, W_A=W_A, W_B=W_B,
    Y_A=Y_A, Y_B=Y_B, C_A=C_A, C_B=C_B,
    Bew_A=Bew_A, Bew_B=Bew_B,
    theta_A=theta_A, theta_B=theta_B,
    b=b, p0=p0,
    DeltaW_A=DeltaW_A, DeltaW_B=DeltaW_B,
    integral_YC_A=integral_YC_A, integral_YC_B=integral_YC_B,
    integral_Bew_B=integral_Bew_B,
    error_A=error_A, error_B_corrected=error_B_corrected
)
print(f"Daten gespeichert: {data_dir / 'S02_I2_Aggregierte_Vermoegenserh.npz'}")
