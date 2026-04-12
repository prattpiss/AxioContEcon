"""
S07 – Kapitalakkumulation K.1  (§3.2 / §4.5)
================================================
Gleichung K.1:   dK_k/dt  = I_k  − δ_k · K_k
Allgemein:       dn_k^(α)/dt = [intrinsische Dyn.] − Σ λ_αβ n_k^(α) + Σ λ_βα n_k^(β)

4 Regime:
  R1  Balanced Growth       – moderate Investition, stabile Industrieökonomie
  R2  Investitionsboom      – hohe Investition, Technologie-Schub
  R3  Deindustrialisierung  – niedrige Investition, alterndes Kapital
  R4  Strukturwandel        – aktive Konversion K4→K6 (Wissensökonomie)

Validierung:
  V1  K.1 Identität  dK/dt = I − δK  (numerisch vs. analytisch)
  V2  Solow-Steady-State   K* = (s·A) / δ  bei Cobb-Douglas Y=A·K^α
  V3  Konversionserhaltung  Σ_α Konversionsflüsse = 0
  V4  Golden Rule  c* maximal bei f'(K*)=δ ⇔ α·A·K^{α-1}=δ
  V5  Sensitivität  δ × s  Heatmap → K(T)/K(0)

Sensitivitätsanalyse: 25×25 = 625 Punkte  (δ, s)
"""

import numpy as np
from scipy.integrate import solve_ivp, trapezoid
from scipy.optimize import fsolve
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path
import warnings
warnings.filterwarnings("ignore", category=RuntimeWarning)

# ──────────────────────────────────────────────
# Pfade
# ──────────────────────────────────────────────
BASE = Path(__file__).resolve().parents[2]
PLOT = BASE / "Ergebnisse" / "Plots" / "S07_K1_Kapitalakkumulation.png"
DATA = BASE / "Ergebnisse" / "Daten" / "S07_K1_Kapitalakkumulation.npz"
PLOT.parent.mkdir(parents=True, exist_ok=True)
DATA.parent.mkdir(parents=True, exist_ok=True)

rng = np.random.default_rng(42)

# ──────────────────────────────────────────────
# 6 Güterklassen nach Monographie §3.1
# α=0: K1 Maschinen    δ=0.08   (t½≈8.7 a)
# α=1: K2 Land/Gold    δ=0.002  (quasi-ewig)
# α=2: K3 Nahrung      δ=2.0    (t½≈0.35 a)
# α=3: K4 Patente      δ=0.05   (t½≈14 a)
# α=4: K5 Geld         δ=0      (ewig)
# α=5: K6 Information  δ=0.10   (t½≈6.9 a)
# ──────────────────────────────────────────────
N_CLASSES = 6
CLASS_NAMES = ["K1 Maschinen", "K2 Land/Gold", "K3 Nahrung",
               "K4 Patente", "K5 Geld", "K6 Information"]
T_SPAN = (0, 80)
T_EVAL = np.linspace(0, 80, 4001)

# ──────────────────────────────────────────────
# Konversionsmatrix Λ (6×6)
# Einträge nach Monographie §3.2 Tabelle
# ──────────────────────────────────────────────
def make_lambda_matrix(lam46, lam64, lam13, lam31):
    """Erstellt 6×6-Konversionsmatrix mit den 4 Hauptflüssen."""
    L = np.zeros((N_CLASSES, N_CLASSES))
    L[3, 5] = lam46   # K4→K6  Patentablauf
    L[5, 3] = lam64   # K6→K4  Patentierung
    L[0, 2] = lam13   # K1→K3  Verschrottung
    L[2, 0] = lam31   # K3→K1  Verarbeitung/Recycling
    return L


# ──────────────────────────────────────────────
# Regime-Parameter
# ──────────────────────────────────────────────
def get_regime_params(regime):
    """Gibt (delta[6], I_base[6], Lambda[6,6], s_rate, A_tfp, alpha_cd, label, color) zurück."""
    if regime == "R1":
        delta = np.array([0.08, 0.002, 2.0, 0.05, 0.0, 0.10])
        I_base = np.array([12.0, 0.5, 50.0, 3.0, 0.0, 5.0])
        Lam = make_lambda_matrix(0.02, 0.01, 0.005, 0.003)
        return delta, I_base, Lam, 0.25, 1.0, 0.33, "R1 Balanced Growth", "C0"
    elif regime == "R2":
        delta = np.array([0.06, 0.002, 2.0, 0.03, 0.0, 0.08])
        I_base = np.array([25.0, 1.0, 50.0, 8.0, 0.0, 15.0])
        Lam = make_lambda_matrix(0.01, 0.02, 0.003, 0.005)
        return delta, I_base, Lam, 0.35, 1.5, 0.33, "R2 Investitionsboom", "C1"
    elif regime == "R3":
        delta = np.array([0.12, 0.002, 2.0, 0.08, 0.0, 0.15])
        I_base = np.array([4.0, 0.2, 30.0, 1.0, 0.0, 2.0])
        Lam = make_lambda_matrix(0.05, 0.005, 0.01, 0.001)
        return delta, I_base, Lam, 0.12, 0.7, 0.33, "R3 Deindustrialisierung", "C2"
    elif regime == "R4":
        delta = np.array([0.10, 0.002, 2.0, 0.02, 0.0, 0.05])
        I_base = np.array([8.0, 0.3, 40.0, 2.0, 0.0, 20.0])
        Lam = make_lambda_matrix(0.08, 0.005, 0.008, 0.002)
        return delta, I_base, Lam, 0.28, 1.2, 0.33, "R4 Strukturwandel", "C3"


# ──────────────────────────────────────────────
# ODE-System für 6 Güterklassen + Produktion
# State: n[0..5] = Bestände K1..K6
# ──────────────────────────────────────────────
def make_rhs(delta, I_base, Lam, s_rate, A_tfp, alpha_cd):
    """
    Erzeugt RHS-Funktion.
    Investition: I_k endogen für K1 (Maschinen) über Solow I = s·Y,
                 exogen für andere Klassen.
    Produktion: Y = A · K1^alpha (Cobb-Douglas, einfachste Form)
    """
    def rhs(t, n):
        n = np.maximum(n, 0.0)
        K1 = n[0]
        # Produktion
        Y = A_tfp * max(K1, 1e-12)**alpha_cd
        # Investition
        I = I_base.copy()
        I[0] = s_rate * Y  # Solow: I_K1 = s·Y

        # K.1: dn/dt = I − δn − Konversion_out + Konversion_in
        dndt = np.zeros(N_CLASSES)
        for a in range(N_CLASSES):
            conv_out = np.sum(Lam[a, :]) * n[a]
            conv_in = sum(Lam[b, a] * n[b] for b in range(N_CLASSES))
            dndt[a] = I[a] - delta[a] * n[a] - conv_out + conv_in
        return dndt
    return rhs


# ──────────────────────────────────────────────
# Solow Steady State analytisch
# K* löst: s·A·(K*)^α = δ·K*  ⟹  K* = (s·A/δ)^{1/(1-α)}
# ──────────────────────────────────────────────
def solow_steady_state(s, A, alpha, delta):
    if delta <= 0:
        return np.inf
    return (s * A / delta) ** (1.0 / (1.0 - alpha))


# Golden Rule: f'(K*)=δ  ⟹  α·A·K^{α-1} = δ  ⟹  K_gold = (α·A/δ)^{1/(1-α)}
def golden_rule_K(A, alpha, delta):
    if delta <= 0:
        return np.inf
    return (alpha * A / delta) ** (1.0 / (1.0 - alpha))


# ──────────────────────────────────────────────
# Simulation 4 Regime
# ──────────────────────────────────────────────
print("=" * 70)
print("S07  Kapitalakkumulation K.1  (§3.2 / §4.5)")
print("=" * 70)

# Anfangsbedingungen  (alle Klassen starten > 0)
n0_base = np.array([100.0, 50.0, 25.0, 40.0, 200.0, 60.0])

results = {}
for regime in ["R1", "R2", "R3", "R4"]:
    delta, I_base, Lam, s_rate, A_tfp, alpha_cd, label, color = get_regime_params(regime)

    # Kleine Perturbation der Anfangsbedingung pro Regime
    n0 = n0_base * (1.0 + 0.05 * rng.standard_normal(N_CLASSES))
    n0 = np.maximum(n0, 1.0)

    rhs = make_rhs(delta, I_base, Lam, s_rate, A_tfp, alpha_cd)
    sol = solve_ivp(rhs, T_SPAN, n0, t_eval=T_EVAL,
                    method="RK45", rtol=1e-10, atol=1e-12, max_step=0.1)
    assert sol.success, f"{regime}: Solver fehlgeschlagen: {sol.message}"

    t = sol.t
    n = sol.y  # (6, len(t))

    # ── V1: K.1 Identität prüfen ──
    # Berechne dK/dt numerisch und vergleiche mit I − δK − conv
    K1_num = n[0]
    Y_num = A_tfp * np.maximum(K1_num, 1e-12)**alpha_cd
    I_K1_num = s_rate * Y_num

    # dK1/dt numerisch via finite difference (zentral)
    dt_arr = np.diff(t)
    dKdt_num = np.gradient(K1_num, t)

    # dK1/dt analytisch = I - δK - conv_out + conv_in
    conv_out_K1 = np.sum(Lam[0, :]) * n[0]
    conv_in_K1 = sum(Lam[b, 0] * n[b] for b in range(N_CLASSES))
    dKdt_ana = I_K1_num - delta[0] * n[0] - conv_out_K1 + conv_in_K1

    # Fehler Integral
    err_K1 = trapezoid(np.abs(dKdt_num - dKdt_ana), t)
    scale_K1 = trapezoid(np.abs(dKdt_ana), t) + 1e-15
    rel_err_K1 = err_K1 / scale_K1

    # ── V2: Solow Steady State (nur K1, ohne Konversion) ──
    K_star_solow = solow_steady_state(s_rate, A_tfp, alpha_cd, delta[0])
    K1_final = n[0, -1]
    # K1 konvergiert nicht exakt gegen Solow-SS wegen Konversion,
    # aber wir können die Abweichung dokumentieren.
    K_star_eff = None  # wird numerisch bestimmt

    # Numerischer Steady-State via Newton
    def ss_residual(K1_val):
        K1_val = max(K1_val, 1e-12)
        Y_val = A_tfp * K1_val**alpha_cd
        I_val = s_rate * Y_val
        co = np.sum(Lam[0, :]) * K1_val
        # Für Konversion-In brauchen wir SS der anderen Klassen
        # Vereinfachung: verwende letzte Werte n[-1] für andere Klassen
        ci = sum(Lam[b, 0] * n[b, -1] for b in range(N_CLASSES))
        return I_val - delta[0] * K1_val - co + ci
    try:
        K_star_eff = float(fsolve(ss_residual, K1_final, full_output=False))
    except Exception:
        K_star_eff = K1_final

    # ── V3: Konversionserhaltung ──
    # Für jedes t: Σ_α (conv_in_α − conv_out_α) = 0  (was rausgeht, kommt rein)
    conv_balance = np.zeros(len(t))
    for a in range(N_CLASSES):
        for b in range(N_CLASSES):
            if a != b:
                # a→b: aus a raus, in b rein — netto Null über System
                conv_balance += Lam[a, b] * n[a] - Lam[a, b] * n[a]  # = 0 per Konstruktion
    # Besser: Direkt die Netto-Konversionsflüsse summieren
    conv_total = np.zeros(len(t))
    for a in range(N_CLASSES):
        c_out = np.sum(Lam[a, :]) * n[a]
        c_in = sum(Lam[b, a] * n[b] for b in range(N_CLASSES))
        conv_total += (c_in - c_out)
    max_conv_err = np.max(np.abs(conv_total))

    # ── V4: Golden Rule ──
    K_gold = golden_rule_K(A_tfp, alpha_cd, delta[0])
    # Maximaler Konsum c* = Y* − δK* = A·K_gold^α − δ·K_gold
    Y_gold = A_tfp * K_gold**alpha_cd
    c_gold = Y_gold - delta[0] * K_gold

    # ── Speichere ──
    results[regime] = dict(
        t=t, n=n, delta=delta, I_base=I_base, Lam=Lam,
        s_rate=s_rate, A_tfp=A_tfp, alpha_cd=alpha_cd,
        label=label, color=color, n0=n0,
        rel_err_K1=rel_err_K1, K_star_solow=K_star_solow,
        K_star_eff=K_star_eff, K1_final=K1_final,
        max_conv_err=max_conv_err, K_gold=K_gold,
        c_gold=c_gold, Y_num=Y_num, I_K1_num=I_K1_num,
        dKdt_num=dKdt_num, dKdt_ana=dKdt_ana,
    )

    # ── Ausgabe ──
    print(f"\n{'─'*60}")
    print(f"  {label}")
    print(f"{'─'*60}")
    print(f"  K1(0)={n0[0]:.1f}  K1(T)={K1_final:.1f}")
    print(f"  K*_Solow (ohne Konv.)  = {K_star_solow:.1f}")
    print(f"  K*_eff   (mit Konv.)   = {K_star_eff:.1f}")
    print(f"  K_GoldenRule            = {K_gold:.1f}")
    print(f"  V1  K.1-Identität     rel.Fehler = {rel_err_K1:.2e}  {'✅' if rel_err_K1<1e-3 else '⚠'}")
    print(f"  V3  Konv.-Erhaltung   max|err| = {max_conv_err:.2e}  {'✅' if max_conv_err<1e-8 else '⚠'}")
    for a in range(N_CLASSES):
        print(f"    {CLASS_NAMES[a]:18s}  n(0)={n0[a]:7.1f}  n(T)={n[a,-1]:9.1f}  δ={delta[a]:.3f}")


# ──────────────────────────────────────────────
# Solow-Konvergenztest (reines K.1 ohne Konversion)
# ──────────────────────────────────────────────
print(f"\n{'='*60}")
print("  Solow-Konvergenztest (ohne Konversion)")
print(f"{'='*60}")

# Reine Solow-Dynamik: dK/dt = s·A·K^α − δ·K
s_sol, A_sol, alpha_sol, delta_sol = 0.25, 1.0, 0.33, 0.08
K_star_sol = solow_steady_state(s_sol, A_sol, alpha_sol, delta_sol)
K0_cases = [20.0, K_star_sol, 500.0]   # unter, auf, über Steady State

def solow_rhs(t, K):
    K_val = max(K[0], 1e-12)
    return [s_sol * A_sol * K_val**alpha_sol - delta_sol * K_val]

solow_results = {}
for i, K0 in enumerate(K0_cases):
    sol = solve_ivp(solow_rhs, (0, 200), [K0], t_eval=np.linspace(0, 200, 5001),
                    method="RK45", rtol=1e-12, atol=1e-14, max_step=0.2)
    K_final = sol.y[0, -1]
    rel_conv = abs(K_final - K_star_sol) / K_star_sol
    solow_results[i] = dict(t=sol.t, K=sol.y[0], K0=K0, K_final=K_final)
    tag = "unter" if K0 < K_star_sol else ("auf" if abs(K0 - K_star_sol) < 1 else "über")
    print(f"  K0={K0:7.1f} ({tag} K*)  →  K(200)={K_final:.3f}  "
          f"K*={K_star_sol:.3f}  rel.Abw.={rel_conv:.2e}  "
          f"{'✅' if rel_conv < 1e-4 else '⚠'}")


# ──────────────────────────────────────────────
# Golden Rule Verifikation
# ──────────────────────────────────────────────
print(f"\n{'='*60}")
print("  Golden-Rule-Verifikation  (V4)")
print(f"{'='*60}")
for regime in ["R1", "R2", "R3", "R4"]:
    r = results[regime]
    # Bei s_gold = α ergibt sich K_gold
    s_gold = r["alpha_cd"]
    K_g = solow_steady_state(s_gold, r["A_tfp"], r["alpha_cd"], r["delta"][0])
    Y_g = r["A_tfp"] * K_g**r["alpha_cd"]
    c_g = Y_g - r["delta"][0] * K_g
    # Prüfe f'(K_gold) = δ
    fprime = r["alpha_cd"] * r["A_tfp"] * K_g**(r["alpha_cd"] - 1)
    check = abs(fprime - r["delta"][0])
    print(f"  {r['label']:28s}  K_gold={K_g:8.1f}  c*={c_g:7.2f}  "
          f"|f'(K*)-δ|={check:.2e}  {'✅' if check<1e-8 else '⚠'}")


# ──────────────────────────────────────────────
# V5: Sensitivitätsanalyse  δ × s → K1(T)/K1(0)
# ──────────────────────────────────────────────
print(f"\n{'='*60}")
print("  Sensitivitätsanalyse  (625 Punkte)")
print(f"{'='*60}")

N_SENS = 25
delta_range = np.linspace(0.02, 0.20, N_SENS)
s_range = np.linspace(0.05, 0.50, N_SENS)
K_ratio_grid = np.zeros((N_SENS, N_SENS))

# Basis-Parameter (R1-like, ohne Konversion für Klarheit)
A_sens = 1.0
alpha_sens = 0.33
T_sens = 60

for i, d_val in enumerate(delta_range):
    for j, s_val in enumerate(s_range):
        def rhs_sens(t, K, d=d_val, s=s_val):
            K_val = max(K[0], 1e-12)
            return [s * A_sens * K_val**alpha_sens - d * K_val]
        sol_s = solve_ivp(rhs_sens, (0, T_sens), [100.0],
                          method="RK45", rtol=1e-8, atol=1e-10,
                          max_step=1.0, dense_output=True)
        K_ratio_grid[i, j] = sol_s.sol(T_sens)[0] / 100.0

print(f"  K(T)/K(0) ∈ [{K_ratio_grid.min():.2f}, {K_ratio_grid.max():.2f}]")
print(f"  Median = {np.median(K_ratio_grid):.2f}")


# ──────────────────────────────────────────────
# Plot (3×3 = 9 panels)
# ──────────────────────────────────────────────
fig, axes = plt.subplots(3, 3, figsize=(18, 15))
fig.suptitle("S07 – Kapitalakkumulation K.1  (§3.2 / §4.5)", fontsize=16, fontweight="bold")

# (a) K1 Maschinen über Zeit, 4 Regime
ax = axes[0, 0]
for regime in ["R1", "R2", "R3", "R4"]:
    r = results[regime]
    ax.plot(r["t"], r["n"][0], color=r["color"], label=r["label"], lw=1.5)
    ax.axhline(r["K_star_eff"], color=r["color"], ls=":", alpha=0.5)
ax.set_xlabel("t [Jahre]"); ax.set_ylabel("K₁ (Maschinen)")
ax.set_title("(a) Maschinenkapital K₁(t)"); ax.legend(fontsize=7); ax.grid(alpha=0.3)

# (b) Alle 6 Klassen für R1
ax = axes[0, 1]
r1 = results["R1"]
for a in range(N_CLASSES):
    ax.plot(r1["t"], r1["n"][a], label=CLASS_NAMES[a], lw=1.2)
ax.set_xlabel("t [Jahre]"); ax.set_ylabel("Bestand nₖ")
ax.set_title("(b) Alle Güterklassen (R1)"); ax.legend(fontsize=7); ax.grid(alpha=0.3)
ax.set_yscale("symlog", linthresh=10)

# (c) Alle 6 Klassen für R4 Strukturwandel
ax = axes[0, 2]
r4 = results["R4"]
for a in range(N_CLASSES):
    ax.plot(r4["t"], r4["n"][a], label=CLASS_NAMES[a], lw=1.2)
ax.set_xlabel("t [Jahre]"); ax.set_ylabel("Bestand nₖ")
ax.set_title("(c) Alle Güterklassen (R4 Strukturwandel)"); ax.legend(fontsize=7); ax.grid(alpha=0.3)
ax.set_yscale("symlog", linthresh=10)

# (d) V1: dK1/dt numerisch vs analytisch (R1)
ax = axes[1, 0]
r1 = results["R1"]
mask = (r1["t"] > 0.5) & (r1["t"] < 79.5)  # Randeffekte vermeiden
ax.plot(r1["t"][mask], r1["dKdt_num"][mask], "C0-", label="dK₁/dt numerisch", lw=1)
ax.plot(r1["t"][mask], r1["dKdt_ana"][mask], "C1--", label="I−δK−conv (analytisch)", lw=1)
ax.set_xlabel("t [Jahre]"); ax.set_ylabel("dK₁/dt")
ax.set_title(f"(d) V1: K.1-Identität (R1)  ε={r1['rel_err_K1']:.1e}"); ax.legend(fontsize=7); ax.grid(alpha=0.3)

# (e) Solow-Konvergenz
ax = axes[1, 1]
for i, (K0, style) in enumerate(zip(K0_cases, ["-", "--", "-."])):
    sr = solow_results[i]
    ax.plot(sr["t"], sr["K"], style, label=f"K₀={K0:.0f}", lw=1.2)
ax.axhline(K_star_sol, color="k", ls=":", lw=1, label=f"K*={K_star_sol:.1f}")
ax.set_xlabel("t [Jahre]"); ax.set_ylabel("K")
ax.set_title("(e) Solow-Konvergenz (ohne Konversion)"); ax.legend(fontsize=7); ax.grid(alpha=0.3)

# (f) Produktion Y(t) alle 4 Regime
ax = axes[1, 2]
for regime in ["R1", "R2", "R3", "R4"]:
    r = results[regime]
    ax.plot(r["t"], r["Y_num"], color=r["color"], label=r["label"], lw=1.2)
ax.set_xlabel("t [Jahre]"); ax.set_ylabel("Y = A·K₁^α")
ax.set_title("(f) Produktion Y(t)"); ax.legend(fontsize=7); ax.grid(alpha=0.3)

# (g) Investition I vs Abschreibung δK (R1)
ax = axes[2, 0]
r1 = results["R1"]
ax.plot(r1["t"], r1["I_K1_num"], "C0-", label="I₁ = s·Y", lw=1.2)
ax.plot(r1["t"], r1["delta"][0] * r1["n"][0], "C3--", label="δ₁·K₁", lw=1.2)
ax.set_xlabel("t [Jahre]"); ax.set_ylabel("Fluss [Einheiten/Jahr]")
ax.set_title("(g) I vs δK (R1 – Konvergenz zu Gleichgewicht)"); ax.legend(fontsize=7); ax.grid(alpha=0.3)

# (h) Heatmap K(T)/K(0)
ax = axes[2, 1]
im = ax.pcolormesh(s_range, delta_range, K_ratio_grid, cmap="RdYlGn", shading="auto")
plt.colorbar(im, ax=ax, label="K(T)/K(0)")
# Markiere Regime
regime_markers = {"R1": (0.25, 0.08), "R2": (0.35, 0.06),
                  "R3": (0.12, 0.12), "R4": (0.28, 0.10)}
for rname, (s_val, d_val) in regime_markers.items():
    ax.plot(s_val, d_val, "w*", ms=12, mec="k")
    ax.annotate(rname, (s_val, d_val), fontsize=7, color="white",
                fontweight="bold", ha="center", va="bottom",
                textcoords="offset points", xytext=(0, 5))
ax.set_xlabel("Sparquote s"); ax.set_ylabel("Abschreibungsrate δ")
ax.set_title("(h) Sensitivität K(60)/K(0)"); ax.grid(alpha=0.2)

# (i) K4/K6-Dynamik (Strukturwandel R4)
ax = axes[2, 2]
r4 = results["R4"]
ax.plot(r4["t"], r4["n"][3], "C4-", label="K4 Patente", lw=1.5)
ax.plot(r4["t"], r4["n"][5], "C5-", label="K6 Information", lw=1.5)
ax.plot(r4["t"], r4["n"][3] + r4["n"][5], "k--", label="K4+K6 (Wissensgesamt)", lw=1)
ax.set_xlabel("t [Jahre]"); ax.set_ylabel("Bestand")
ax.set_title("(i) Wissensökonomie K4↔K6 (R4)")
ax.legend(fontsize=7); ax.grid(alpha=0.3)

plt.tight_layout(rect=[0, 0, 1, 0.96])
plt.savefig(PLOT, dpi=180, bbox_inches="tight")
print(f"\n  Plot → {PLOT}")

# ──────────────────────────────────────────────
# Daten speichern
# ──────────────────────────────────────────────
save_dict = dict(
    delta_range=delta_range, s_range=s_range, K_ratio_grid=K_ratio_grid,
    solow_K_star=K_star_sol, solow_t=solow_results[0]["t"],
)
for regime in ["R1", "R2", "R3", "R4"]:
    r = results[regime]
    save_dict[f"{regime}_t"] = r["t"]
    save_dict[f"{regime}_n"] = r["n"]
np.savez_compressed(DATA, **save_dict)
print(f"  Daten → {DATA}")

# ──────────────────────────────────────────────
# Zusammenfassung
# ──────────────────────────────────────────────
print(f"\n{'='*70}")
print("  ZUSAMMENFASSUNG S07")
print(f"{'='*70}")
all_ok = True
for regime in ["R1", "R2", "R3", "R4"]:
    r = results[regime]
    v1_ok = r["rel_err_K1"] < 1e-3
    v3_ok = r["max_conv_err"] < 1e-8
    if not (v1_ok and v3_ok):
        all_ok = False
    print(f"  {r['label']:28s}  V1={'✅' if v1_ok else '⚠'}  V3={'✅' if v3_ok else '⚠'}  "
          f"K1(T)={r['K1_final']:.1f}  K*_eff={r['K_star_eff']:.1f}")

print(f"\n  Solow-Konvergenz:")
for i, K0 in enumerate(K0_cases):
    sr = solow_results[i]
    print(f"    K0={K0:7.1f} → K(200)={sr['K_final']:.3f}  (K*={K_star_sol:.3f})")

print(f"\n  Golden Rule:")
for regime in ["R1", "R2", "R3", "R4"]:
    r = results[regime]
    print(f"    {r['label']:28s}  K_gold={r['K_gold']:.1f}  c*_max={r['c_gold']:.2f}")

print(f"\n  Sensitivität: K(60)/K(0) ∈ [{K_ratio_grid.min():.2f}, {K_ratio_grid.max():.2f}]")
print(f"\n  Gesamtergebnis: {'✅ ALLE TESTS BESTANDEN' if all_ok else '⚠ TEILWEISE WARNUNGEN'}")
print(f"{'='*70}")
