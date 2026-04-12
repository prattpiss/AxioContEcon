"""
S11 – Vermögensfluss II.1  (§5.4)
==========================================
Monographie-Gleichung (exakt):

    j_w = -D_w * nabla(Phi_w) + v_w * rho_w

Vermögenspotential (Def. 5.2):

    Phi_w(x,t) = h(rho_w) - beta_w * V_w(x)

wobei h(rho_w) = alpha * ln(rho_w / rho_0)  mit h' > 0

Expandiert:

    j_w = -D_w * (alpha/rho_w) * nabla(rho_w) + D_w * beta_w * nabla(V_w) + v_w * rho_w

Drei Flusskomponenten:
  1. -D_w * (alpha/rho) * nabla(rho)   Diversifikation (nichtlineare Fick-Diffusion)
  2. +D_w * beta_w * nabla(V_w)         Standortattraktivitaet (Drift zu guten Institutionen)
  3. +v_w * rho_w                        Konvektion (gerichtete Kapitalstroeme)

Kopplung: drho_w/dt = -nabla . j_w + S_w  (Vermögenskontinuität)

Anmerkung zur Vorzeichenkonvention:
  Monographie Def. 5.2 definiert h' < 0 und Phi = h + beta*V.
  Für thermodynamisch stabile Diffusion (dPhi/drho > 0) verwenden wir:
    h(rho) = alpha * ln(rho/rho_0)  mit h' = alpha/rho > 0
    Phi = h - beta*V  (Minus vor V, damit Kapital zu hohem V fliesst)
  Dies ist äquivalent zur Monographie-Physik: Diversifikation + Standortanziehung.

Lucas-Paradox (1990): V_w^{reich} >> V_w^{arm}
  -> Kapital fliesst von arm nach reich trotz Konzentrationsgefälle

5 Regime:
  R1 Reine Diversifikation (beta_w=0, v_w=0 -> reine nichtlineare Diffusion)
  R2 Lucas-Paradox (beta_w hoch, V_w-Gradient -> Kapital bleibt reich)
  R3 Kapitalflucht (V_w-Kollaps -> abrupter Abfluss)
  R4 Drift-Diffusion (v_w != 0 -> Konvektion + Diffusion)
  R5 Voll stochastisch (OU-D, OU-V, Poisson-Quellen)

7 Funktionalformen:
  Gaussprofil, Rampe, glatter Sprung, Sinusoidal (räumlich)
  Ornstein-Uhlenbeck, Logistisch/Sprung, Poisson-Pulse (zeitlich)
"""

import numpy as np
from scipy.integrate import solve_ivp
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from pathlib import Path
import warnings
warnings.filterwarnings("ignore", category=RuntimeWarning)

# ═══════════════════════════════════════════════
# Pfade
# ═══════════════════════════════════════════════
BASE = Path(__file__).resolve().parents[2]
PLOT = BASE / "Ergebnisse" / "Plots" / "S11_II1_Vermoegensfluss.png"
DATA = BASE / "Ergebnisse" / "Daten" / "S11_II1_Vermoegensfluss.npz"
PLOT.parent.mkdir(parents=True, exist_ok=True)
DATA.parent.mkdir(parents=True, exist_ok=True)

rng = np.random.default_rng(42)

# ═══════════════════════════════════════════════
# KLASSIFIKATION
# ═══════════════════════════════════════════════
#
# ENDOGENE VARIABLEN (räumlich):
#   rho_w(x,t)   Vermögensdichte      [Wäh/km]      Def. 5.1
#   j_w(x,t)     Vermögensfluss       [Wäh/(km*a)]  II.1
#   Phi_w(x,t)   Vermögenspotential   [dimlos]       Def. 5.2
#   h(rho_w)     Konzentrationsterm   [dimlos]       h = alpha * ln(rho/rho_0)
#
# EXOGENE VARIABLEN:
#   V_w(x,t)     Standortattraktivität [dimlos]    Institutionenqualität
#   v_w(x,t)     Driftgeschwindigkeit  [km/a]      Gerichtete Kapitalströme
#   S_w(x,t)     Quellen/Senken        [Wäh/(km*a)] Vermögensschöpfung
#
# PARAMETER:
#   D_w    Diffusionskoeff.     [km²/a]    Kapitalmarktliberalisierung
#   alpha  Konzentrationssens.  [dimlos]    h(rho) = alpha * ln(rho/rho_0)
#   rho_0  Referenzdichte       [Wäh/km]   h(rho_0) = 0
#   beta_w Standortsensitivität [dimlos]    Phi_w = h - beta_w * V_w
#   L      Domänenlänge         [km]

# ═══════════════════════════════════════════════
# Räumliches Gitter (1D)
# ═══════════════════════════════════════════════
L = 100.0         # Domänenlänge [km]
NX = 201          # Gitterpunkte
dx = L / (NX - 1)
x = np.linspace(0, L, NX)

T_SPAN = (0, 200)
N_EVAL = 4001
T_EVAL = np.linspace(*T_SPAN, N_EVAL)

RHO_FLOOR = 1e-6

# ═══════════════════════════════════════════════
# Hilfsfunktionen
# ═══════════════════════════════════════════════

def gaussian_profile(x, center, sigma, amplitude, baseline=0):
    """Gaußsches Raumprofil"""
    return baseline + amplitude * np.exp(-0.5 * ((x - center) / sigma) ** 2)

def smooth_step_spatial(x, x0, v_left, v_right, width=3.0):
    """Glatter räumlicher Übergang (Logistik) von v_left (x<<x0) zu v_right (x>>x0)"""
    return v_right + (v_left - v_right) / (1.0 + np.exp((x - x0) / width))

def sinusoidal_profile(x, offset, amplitude, wavenumber):
    """Sinusförmiges Raumprofil"""
    return offset + amplitude * np.sin(wavenumber * x)

def ramp_profile(x, v_left, v_right):
    """Linearer Rampen-Profil"""
    return v_left + (v_right - v_left) * x / L

def smooth_step_time(t, t0, width=3.0):
    """Glatter zeitlicher Übergang (0->1 um t0)"""
    return 1.0 / (1.0 + np.exp(-(t - t0) / width))

def ou_time_modulation(t_eval, mu, theta, sigma, x0, seed=42):
    """Ornstein-Uhlenbeck Prozess für Zeitmodulation"""
    rng_loc = np.random.default_rng(seed)
    dt = np.diff(t_eval, prepend=t_eval[0] - (t_eval[1] - t_eval[0]))
    x_arr = np.zeros(len(t_eval))
    x_arr[0] = x0
    for i in range(1, len(t_eval)):
        dW = np.sqrt(dt[i]) * rng_loc.standard_normal()
        x_arr[i] = x_arr[i-1] + theta * (mu - x_arr[i-1]) * dt[i] + sigma * dW
    return x_arr

def gbm_time_modulation(t_eval, mu, sigma, x0, seed=7):
    """GBM für Zeitmodulation"""
    rng_loc = np.random.default_rng(seed)
    dt = np.diff(t_eval, prepend=t_eval[0] - (t_eval[1] - t_eval[0]))
    x_arr = np.zeros(len(t_eval))
    x_arr[0] = x0
    for i in range(1, len(t_eval)):
        dW = np.sqrt(dt[i]) * rng_loc.standard_normal()
        x_arr[i] = x_arr[i-1] * np.exp((mu - 0.5 * sigma**2) * dt[i] + sigma * dW)
    return np.maximum(x_arr, 1e-10)


# ═══════════════════════════════════════════════
# Vermögenspotential und Flussberechnung
# ═══════════════════════════════════════════════

def vermoegenspotential(rho, alpha, rho_0, beta_w, V_w):
    """
    Phi_w = h(rho_w) - beta_w * V_w   (Def. 5.2, Vorzeichen-Korrektur)
    h(rho) = alpha * ln(rho / rho_0)  (h' = alpha/rho > 0, stabile Diffusion)

    Physik:
      - Hohe rho -> hohes Phi -> Kapital fliesst ab (Diversifikation)
      - Hohes V_w -> niedriges Phi -> Kapital fliesst hin (Standortanziehung)
    """
    rho_safe = np.maximum(rho, RHO_FLOOR)
    h = alpha * np.log(rho_safe / rho_0)
    Phi = h - beta_w * V_w
    return Phi, h


def compute_flux(rho, V_w, v_w, D_w, alpha, rho_0, beta_w):
    """
    j_w = -D_w * nabla(Phi_w) + v_w * rho_w   (II.1)

    Zerlegt in drei Komponenten auf staggered grid (NX-1 Punkte):
      j_div  = -D_w * dh/dx           (Diversifikation)
      j_attr = +D_w * beta_w * dV/dx  (Standortattraktivität)
      j_conv = v_w * rho              (Konvektion, upwind)

    j_diff = j_div + j_attr = -D_w * dPhi/dx
    j_total = j_diff + j_conv
    """
    Phi, h = vermoegenspotential(rho, alpha, rho_0, beta_w, V_w)

    # Gradienten auf staggered grid (Zwischenpunkte)
    grad_Phi = np.diff(Phi) / dx
    grad_h = np.diff(h) / dx
    grad_V = np.diff(V_w) / dx

    # Diffusive Flusskomponenten
    j_diff = -D_w * grad_Phi
    j_div = -D_w * grad_h             # Diversifikation: von hoch rho zu niedrig rho
    j_attr = D_w * beta_w * grad_V    # Attraktivität: zu hohem V_w

    # Konvektiver Fluss (Upwind-Schema)
    if np.isscalar(v_w):
        v_face = v_w * np.ones(NX - 1)
    else:
        v_face = 0.5 * (v_w[:-1] + v_w[1:])

    rho_face = np.where(v_face >= 0, rho[:-1], rho[1:])
    j_conv = v_face * rho_face

    j_total = j_diff + j_conv

    return j_total, j_diff, j_div, j_attr, j_conv, Phi


def make_rhs_mol(D_func, alpha, rho_0, beta_w, V_func, v_func, S_func):
    """
    MOL RHS: drho_w/dt = -nabla . j_w + S_w
    D_func(t) -> D_w (scalar). Für konstantes D: lambda t: D_w
    Neumann BC (j=0 an Rändern).
    """
    def rhs(t, rho_flat):
        rho = np.maximum(rho_flat, RHO_FLOOR)
        D_w = D_func(t)
        V_w = V_func(x, t)
        v_w = v_func(x, t)
        S_w = S_func(x, t)

        j_total, _, _, _, _, _ = compute_flux(
            rho, V_w, v_w, D_w, alpha, rho_0, beta_w
        )

        # Divergenz auf Gitterpunkten
        divj = np.zeros(NX)
        divj[1:-1] = (j_total[1:] - j_total[:-1]) / dx
        # Neumann BC: j=0 an Rändern
        divj[0] = j_total[0] / dx        # j_{-1/2} = 0
        divj[-1] = -j_total[-1] / dx     # j_{N+1/2} = 0

        return -divj + S_w

    return rhs


# ═══════════════════════════════════════════════
# Regime-Definitionen
# ═══════════════════════════════════════════════

def get_regime(regime):
    """Gibt alle Parameter + exogene Raumzeit-Funktionen zurück."""

    if regime == "R1":
        # Reine Diversifikation: beta_w=0, v_w=0 → nur nichtlineare Diffusion
        # Gaußsche Anfangsdichte → glättet sich zu Gleichverteilung
        rho0_init = gaussian_profile(x, 50, 10, 80, baseline=5)
        return dict(
            label="R1 Reine Diversifikation", color="C0",
            D_func=lambda t: 30.0,
            alpha=5.0, rho_0=10.0, beta_w=0.0,
            rho0_init=rho0_init,
            V_func=lambda x, t: np.full_like(x, 5.0),
            v_func=lambda x, t: np.zeros_like(x),
            S_func=lambda x, t: np.zeros_like(x),
            desc="beta=0, v=0: j = -D(alpha/rho)nabla(rho)"
        )

    elif regime == "R2":
        # Lucas-Paradox: V_w hoch links (reiche Institutionen), niedrig rechts
        # Vermögen konzentriert links → Diversifikation will nach rechts schieben
        # Aber beta_w * V_w zieht Kapital nach links zurück → Paradox
        rho0_init = smooth_step_spatial(x, 50, 60.0, 5.0, width=5.0)
        V_w_static = smooth_step_spatial(x, 50, 8.0, 2.0, width=5.0)
        return dict(
            label="R2 Lucas-Paradox", color="C1",
            D_func=lambda t: 10.0,
            alpha=5.0, rho_0=10.0, beta_w=3.0,
            rho0_init=rho0_init,
            V_func=lambda x, t, V=V_w_static: V.copy(),
            v_func=lambda x, t: np.zeros_like(x),
            S_func=lambda x, t: np.zeros_like(x),
            desc="V_w^{reich}>>V_w^{arm}, beta_w=3 -> Kapital bleibt links"
        )

    elif regime == "R3":
        # Kapitalflucht: V_w auf der linken Seite kollabiert bei t=80
        # Vorher: V_w links hoch → Kapital bleibt links (wie R2)
        # Nachher: V_w links niedrig → kein Attraktionsvorteil → Kapital fliesst rechts
        rho0_init = gaussian_profile(x, 35, 12, 60, baseline=5)

        def V_func(x_arr, t):
            V_left_pre = 8.0
            V_left_post = 1.0
            V_right = 3.0
            # Logistischer Übergang bei t=80 (Institutionenkrise)
            crisis = smooth_step_time(t, 80.0, width=3.0)
            V_left = V_left_pre - (V_left_pre - V_left_post) * crisis
            return smooth_step_spatial(x_arr, 50, V_left, V_right, width=5.0)

        return dict(
            label="R3 Kapitalflucht", color="C2",
            D_func=lambda t: 10.0,
            alpha=5.0, rho_0=10.0, beta_w=2.5,
            rho0_init=rho0_init,
            V_func=V_func,
            v_func=lambda x, t: np.zeros_like(x),
            S_func=lambda x, t: np.zeros_like(x),
            desc="V_w(links) 8->1 bei t=80 (Institutionenkrise)"
        )

    elif regime == "R4":
        # Drift-Diffusion: v_w > 0 (staatliches Investitionsprogramm)
        # v_w = v0 * sin(pi*x/L): null an Rändern, max in Mitte
        # Verschiebt Vermögen nach rechts, Diffusion wirkt dagegen
        rho0_init = gaussian_profile(x, 30, 10, 50, baseline=5)
        return dict(
            label="R4 Drift-Diffusion", color="C3",
            D_func=lambda t: 10.0,
            alpha=4.0, rho_0=10.0, beta_w=0.0,
            rho0_init=rho0_init,
            V_func=lambda x, t: np.full_like(x, 5.0),
            v_func=lambda x, t: 0.5 * np.sin(np.pi * x / L),
            S_func=lambda x, t: np.zeros_like(x),
            desc="v_w=0.5*sin(pi*x/L): konvektive Drift nach rechts"
        )

    elif regime == "R5":
        # Voll stochastisch: OU-modulierte D und V, Poisson-Quellen
        rho0_init = gaussian_profile(x, 50, 15, 40, baseline=8)

        # OU-modulierter Diffusionskoeffizient
        D_mod = ou_time_modulation(T_EVAL, mu=1.0, theta=0.3, sigma=0.1,
                                   x0=1.0, seed=42)

        def D_func(t, D_base=8.0, D_mod=D_mod):
            idx = min(int(t / T_SPAN[1] * (len(T_EVAL) - 1)), len(T_EVAL) - 1)
            return D_base * max(D_mod[idx], 0.1)

        # OU-moduliertes V_w: V_base(x) * m(t)
        V_base = ramp_profile(x, 3.0, 7.0)
        V_mod = ou_time_modulation(T_EVAL, mu=1.0, theta=0.5, sigma=0.2,
                                   x0=1.0, seed=55)

        def V_func(x_arr, t, V_b=V_base, V_m=V_mod):
            idx = min(int(t / T_SPAN[1] * (len(T_EVAL) - 1)), len(T_EVAL) - 1)
            return V_b * max(V_m[idx], 0.1)

        # Poisson-Quellen: zufällige Vermögensinjektionen
        S_events = rng.poisson(0.3, size=len(T_EVAL))
        S_centers = rng.uniform(20, 80, size=len(T_EVAL))

        def S_func(x_arr, t, S_ev=S_events, S_cen=S_centers):
            idx = min(int(t / T_SPAN[1] * (len(T_EVAL) - 1)), len(T_EVAL) - 1)
            if S_ev[idx] > 0:
                return S_ev[idx] * gaussian_profile(x_arr, S_cen[idx], 5, 1.5)
            return np.zeros_like(x_arr)

        return dict(
            label="R5 Voll stochastisch", color="C4",
            D_func=D_func,
            alpha=4.0, rho_0=10.0, beta_w=1.0,
            rho0_init=rho0_init,
            V_func=V_func,
            v_func=lambda x, t: np.zeros_like(x),
            S_func=S_func,
            desc="OU-D, OU-V_w, Poisson-Quellen"
        )


# ═══════════════════════════════════════════════
# Hauptsimulation
# ═══════════════════════════════════════════════
print("=" * 72)
print("  S11  Vermögensfluss II.1  (§5.4)")
print("=" * 72)

results = {}

for regime in ["R1", "R2", "R3", "R4", "R5"]:
    par = get_regime(regime)

    rhs = make_rhs_mol(
        par["D_func"], par["alpha"], par["rho_0"], par["beta_w"],
        par["V_func"], par["v_func"], par["S_func"]
    )

    sol = solve_ivp(rhs, T_SPAN, par["rho0_init"], t_eval=T_EVAL,
                    method="RK45", rtol=1e-9, atol=1e-11, max_step=0.2)
    assert sol.success, f"{regime}: Solver fehlgeschlagen: {sol.message}"

    rho_xt = np.maximum(sol.y, RHO_FLOOR)  # (NX, N_EVAL)

    # Masse: M(t) = integral rho dx
    mass = np.trapezoid(rho_xt, x=x, axis=0)

    # Schwerpunkt: x_bar(t) = integral(x*rho dx) / M
    x_cm = np.trapezoid(x[:, None] * rho_xt, x=x, axis=0) / mass

    # Finaler Fluss + Komponenten
    D_w_final = par["D_func"](T_SPAN[1])
    V_final = par["V_func"](x, T_SPAN[1])
    v_final = par["v_func"](x, T_SPAN[1])
    j_fin, j_diff_fin, j_div_fin, j_attr_fin, j_conv_fin, Phi_fin = compute_flux(
        rho_xt[:, -1], V_final, v_final,
        D_w_final, par["alpha"], par["rho_0"], par["beta_w"]
    )

    # Anfangsfluss
    D_w_init = par["D_func"](0)
    V_init = par["V_func"](x, 0)
    v_init = par["v_func"](x, 0)
    j_ini, j_diff_ini, j_div_ini, j_attr_ini, j_conv_ini, Phi_ini = compute_flux(
        rho_xt[:, 0], V_init, v_init,
        D_w_init, par["alpha"], par["rho_0"], par["beta_w"]
    )

    # Snapshots
    snap_indices = [0, len(T_EVAL)//4, len(T_EVAL)//2, 3*len(T_EVAL)//4, -1]
    snaps = [(T_EVAL[i], rho_xt[:, i]) for i in snap_indices]

    results[regime] = dict(
        par=par, rho_xt=rho_xt, mass=mass, x_cm=x_cm, t=T_EVAL,
        j_fin=j_fin, j_diff_fin=j_diff_fin, j_div_fin=j_div_fin,
        j_attr_fin=j_attr_fin, j_conv_fin=j_conv_fin,
        Phi_fin=Phi_fin, Phi_ini=Phi_ini,
        V_init=V_init, V_final=V_final,
        j_ini=j_ini,
        snaps=snaps,
    )

    # Zusammenfassung
    print(f"\n{'─'*60}")
    print(f"  {par['label']}  ({par['desc']})")
    print(f"{'─'*60}")
    print(f"  M(0)={mass[0]:.2f}  M(T)={mass[-1]:.2f}  "
          f"dM/M={(mass[-1]-mass[0])/mass[0]*100:+.4f}%")
    print(f"  x_cm(0)={x_cm[0]:.2f}  x_cm(T)={x_cm[-1]:.2f}  "
          f"dx={x_cm[-1]-x_cm[0]:+.2f} km")
    print(f"  rho_max(T)={rho_xt[:,-1].max():.2f}  rho_min(T)={rho_xt[:,-1].min():.4f}")
    print(f"  |j|_max(T)={np.max(np.abs(j_fin)):.4f}")
    print(f"  Phi_w: min={Phi_fin.min():.2f}  max={Phi_fin.max():.2f}")


# ═══════════════════════════════════════════════
# VALIDIERUNGEN
# ═══════════════════════════════════════════════

# V1: Massenerhaltung ohne Quellen (R1)
print(f"\n{'='*60}")
print("  V1: Massenerhaltung (R1, S_w=0)")
print(f"{'='*60}")
r1 = results["R1"]
mass_err = np.max(np.abs(r1["mass"] - r1["mass"][0])) / r1["mass"][0]
print(f"  max|dM/M(0)| = {mass_err:.2e}  {'✅' if mass_err < 5e-3 else '⚠'}")

# V2: Gleichgewicht — Gaußprofil diffundiert zu Gleichverteilung (R1)
print(f"\n{'='*60}")
print("  V2: Diversifikation -> Gleichverteilung (R1)")
print(f"{'='*60}")
rho_final_r1 = r1["rho_xt"][:, -1]
spatial_var = np.std(rho_final_r1) / np.mean(rho_final_r1)
print(f"  sigma(rho)/mean(rho)(T) = {spatial_var:.4f}  {'✅' if spatial_var < 0.1 else '⚠'}")
print(f"  mean(rho(T)) = {np.mean(rho_final_r1):.2f}  "
      f"rho_eq = {r1['mass'][-1]/L:.2f}")

# V3: Lucas-Paradox — Schwerpunkt bleibt links (R2)
print(f"\n{'='*60}")
print("  V3: Lucas-Paradox (R2)")
print(f"{'='*60}")
r2 = results["R2"]
lucas_ok = r2["x_cm"][-1] <= r2["x_cm"][0] + 5.0  # maximal 5km nach rechts
print(f"  x_cm(0) = {r2['x_cm'][0]:.2f} km")
print(f"  x_cm(T) = {r2['x_cm'][-1]:.2f} km")
print(f"  Lucas-Paradox (Kapital bleibt links): {'✅' if lucas_ok else '⚠'}")

# V4: Kapitalflucht — Schwerpunkt verschiebt sich nach rechts nach t=80 (R3)
print(f"\n{'='*60}")
print("  V4: Kapitalflucht (R3)")
print(f"{'='*60}")
r3 = results["R3"]
# Finde Index für t=80 und t=150
idx_80 = np.argmin(np.abs(T_EVAL - 80))
idx_150 = np.argmin(np.abs(T_EVAL - 150))
flight_ok = r3["x_cm"][idx_150] > r3["x_cm"][idx_80] + 1.0
print(f"  x_cm(t=80) = {r3['x_cm'][idx_80]:.2f} km  (vor Krise)")
print(f"  x_cm(t=150) = {r3['x_cm'][idx_150]:.2f} km  (nach Krise)")
print(f"  Kapitalflucht dx = {r3['x_cm'][idx_150]-r3['x_cm'][idx_80]:+.2f} km  "
      f"{'✅' if flight_ok else '⚠'}")

# V5: Konvektive Drift — Schwerpunkt bewegt sich nach rechts (R4)
print(f"\n{'='*60}")
print("  V5: Konvektive Drift (R4)")
print(f"{'='*60}")
r4 = results["R4"]
drift_ok = r4["x_cm"][-1] > r4["x_cm"][0] + 5.0
print(f"  x_cm(0) = {r4['x_cm'][0]:.2f} km")
print(f"  x_cm(T) = {r4['x_cm'][-1]:.2f} km")
print(f"  Drift dx = {r4['x_cm'][-1]-r4['x_cm'][0]:+.2f} km  "
      f"{'✅' if drift_ok else '⚠'}")

# V6: Sensitivität D_w × beta_w → Schwerpunkt-Position
print(f"\n{'='*60}")
print("  V6: Sensitivität (25x25 = 625 Punkte, D_w x beta_w)")
print(f"{'='*60}")
N_SENS = 25
D_sens = np.linspace(1.0, 40.0, N_SENS)
beta_sens = np.linspace(0.0, 5.0, N_SENS)
xcm_grid = np.zeros((N_SENS, N_SENS))

# Feste Konfiguration: Gauß-Dichte links, V_w hoch links
rho_test = smooth_step_spatial(x, 50, 50.0, 5.0, width=5.0)
V_test = smooth_step_spatial(x, 50, 8.0, 2.0, width=5.0)

for i, D_val in enumerate(D_sens):
    for j, beta_val in enumerate(beta_sens):
        j_t, _, _, _, _, _ = compute_flux(
            rho_test, V_test, np.zeros_like(x),
            D_val, 5.0, 10.0, beta_val
        )
        # Instantaner Schwerpunkt-Drift: dx_cm/dt ~ integral(x * (-d(j)/dx) dx) / M
        divj = np.zeros(NX)
        divj[1:-1] = (j_t[1:] - j_t[:-1]) / dx
        divj[0] = j_t[0] / dx
        divj[-1] = -j_t[-1] / dx
        drhodt = -divj
        M_test = np.trapezoid(rho_test, x=x)
        xcm_drift = np.trapezoid(x * drhodt, x=x) / M_test
        xcm_grid[i, j] = xcm_drift

print(f"  dx_cm/dt in [{xcm_grid.min():.3f}, {xcm_grid.max():.3f}] km/a")
print(f"  Median = {np.median(xcm_grid):.3f} km/a")
# Bei beta_w=0: diversifikation -> xcm nach rechts (Schwerpunkt links bei 30)
# Bei beta_w hoch: attraction -> xcm nach links (V_w hoch links)
sens_monoton = xcm_grid[:, 0].mean() > xcm_grid[:, -1].mean()
print(f"  Hoeheres beta -> staerkere Linksverschiebung: "
      f"{'✅' if sens_monoton else '⚠'}")


# ═══════════════════════════════════════════════
# PLOT  (5 Zeilen × 3 Spalten + Metadaten)
# ═══════════════════════════════════════════════
fig = plt.figure(figsize=(22, 32))
gs = GridSpec(6, 3, figure=fig, height_ratios=[1.0, 1.0, 1.0, 1.0, 1.0, 0.6],
              hspace=0.35, wspace=0.3)
fig.suptitle("S11 – Vermögensfluss II.1  (§5.4)\n"
             r"$\vec{j}_w = -D_w\,\nabla\Phi_w + \vec{v}_w\,\rho_w$",
             fontsize=15, fontweight="bold", y=0.98)

x_mid = 0.5 * (x[:-1] + x[1:])

# ── (a) R1: Dichte-Snapshots (reine Diversifikation) ──
ax = fig.add_subplot(gs[0, 0])
for t_s, rho_s in r1["snaps"]:
    ax.plot(x, rho_s, lw=1.2, label=f"t={t_s:.0f}")
ax.set_xlabel("x [km]"); ax.set_ylabel(r"$\rho_w$ [Wäh/km]")
ax.set_title("(a) R1: Diversifikation (Snapshots)")
ax.legend(fontsize=6); ax.grid(alpha=0.3)

# ── (b) R1: Massenerhaltung ──
ax = fig.add_subplot(gs[0, 1])
ax.plot(r1["t"], r1["mass"], "C0-", lw=1.5)
ax.set_xlabel("t [Jahre]"); ax.set_ylabel(r"$\int\rho_w\,dx$ [Wäh]")
ax.set_title(f"(b) R1: Massenerhaltung (dM/M={mass_err:.1e})")
ax.grid(alpha=0.3)

# ── (c) R1: Vermögenspotential Phi_w ──
ax = fig.add_subplot(gs[0, 2])
ax.plot(x, r1["Phi_ini"], "C0--", lw=1, label=r"$\Phi_w(t=0)$")
ax.plot(x, r1["Phi_fin"], "C0-", lw=1.5, label=r"$\Phi_w(T)$")
_, h_ini = vermoegenspotential(r1["rho_xt"][:, 0], r1["par"]["alpha"],
                                r1["par"]["rho_0"], 0, np.zeros(NX))
_, h_fin = vermoegenspotential(r1["rho_xt"][:, -1], r1["par"]["alpha"],
                                r1["par"]["rho_0"], 0, np.zeros(NX))
ax.plot(x, h_ini, "C3--", lw=0.8, label="h(t=0)")
ax.plot(x, h_fin, "C3-", lw=1, label="h(T)")
ax.set_xlabel("x [km]"); ax.set_ylabel("[dimlos]")
ax.set_title(r"(c) R1: $\Phi_w = h(\rho_w)$ (reine Konzentration)")
ax.legend(fontsize=6); ax.grid(alpha=0.3)

# ── (d) R2: Lucas-Paradox Snapshots ──
ax = fig.add_subplot(gs[1, 0])
for t_s, rho_s in r2["snaps"]:
    ax.plot(x, rho_s, lw=1.2, label=f"t={t_s:.0f}")
ax2 = ax.twinx()
ax2.plot(x, r2["V_init"], "k:", lw=1, alpha=0.4, label="$V_w(x)$")
ax2.set_ylabel("$V_w$", color="grey")
ax.set_xlabel("x [km]"); ax.set_ylabel(r"$\rho_w$ [Wäh/km]")
ax.set_title("(d) R2: Lucas-Paradox (Snapshots)")
ax.legend(fontsize=6, loc="upper right"); ax.grid(alpha=0.3)

# ── (e) R2: Flusskomponenten (final) ──
ax = fig.add_subplot(gs[1, 1])
ax.plot(x_mid, r2["j_div_fin"], "C0-", lw=1, label=r"$j_{\mathrm{div}}$ (Diversif.)")
ax.plot(x_mid, r2["j_attr_fin"], "C1--", lw=1.2, label=r"$j_{\mathrm{attr}}$ (Standort)")
ax.plot(x_mid, r2["j_conv_fin"], "C3:", lw=1, label=r"$j_{\mathrm{conv}}$ (=0)")
ax.plot(x_mid, r2["j_fin"], "k-", lw=1.5, alpha=0.7, label=r"$j_{\mathrm{total}}$")
ax.axhline(0, color="grey", ls=":", lw=0.5)
ax.set_xlabel("x [km]"); ax.set_ylabel(r"$j_w$ [Wäh/(km·a)]")
ax.set_title("(e) R2: Flusskomponenten (T)")
ax.legend(fontsize=6); ax.grid(alpha=0.3)

# ── (f) R2+R3: Schwerpunkt über Zeit ──
ax = fig.add_subplot(gs[1, 2])
ax.plot(r2["t"], r2["x_cm"], "C1-", lw=1.5, label="R2 Lucas")
ax.plot(r3["t"], r3["x_cm"], "C2-", lw=1.5, label="R3 Kapitalfl.")
ax.axvline(80, color="C2", ls=":", lw=0.8, alpha=0.5, label="Krise t=80")
ax.set_xlabel("t [Jahre]"); ax.set_ylabel(r"$\bar{x}$ [km]")
ax.set_title(r"(f) Schwerpunkt $\bar{x}(t)$: Lucas vs Flucht")
ax.legend(fontsize=6); ax.grid(alpha=0.3)

# ── (g) R3: Kapitalflucht Snapshots ──
ax = fig.add_subplot(gs[2, 0])
# Spezielle Snapshots: vor/während/nach Krise
idx_snap3 = [0, idx_80 - 200, idx_80, idx_80 + 400, -1]
for idx in idx_snap3:
    t_s = T_EVAL[idx]
    ax.plot(x, r3["rho_xt"][:, idx], lw=1.2, label=f"t={t_s:.0f}")
ax2 = ax.twinx()
V_pre = r3["par"]["V_func"](x, 0)
V_post = r3["par"]["V_func"](x, 150)
ax2.plot(x, V_pre, "k--", lw=0.8, alpha=0.3, label="$V_w$(pre)")
ax2.plot(x, V_post, "k:", lw=0.8, alpha=0.3, label="$V_w$(post)")
ax2.set_ylabel("$V_w$", color="grey")
ax.set_xlabel("x [km]"); ax.set_ylabel(r"$\rho_w$ [Wäh/km]")
ax.set_title("(g) R3: Kapitalflucht (Krise t=80)")
ax.legend(fontsize=6, loc="upper right"); ax.grid(alpha=0.3)

# ── (h) R4: Drift-Diffusion Snapshots ──
ax = fig.add_subplot(gs[2, 1])
for t_s, rho_s in r4["snaps"]:
    ax.plot(x, rho_s, lw=1.2, label=f"t={t_s:.0f}")
ax.set_xlabel("x [km]"); ax.set_ylabel(r"$\rho_w$ [Wäh/km]")
ax.set_title(r"(h) R4: Drift-Diffusion ($v_w = 0.5\sin(\pi x/L)$)")
ax.legend(fontsize=6); ax.grid(alpha=0.3)

# ── (i) R5: Stochastische Evolution ──
ax = fig.add_subplot(gs[2, 2])
r5 = results["R5"]
for t_s, rho_s in r5["snaps"]:
    ax.plot(x, rho_s, lw=1.2, label=f"t={t_s:.0f}")
ax.set_xlabel("x [km]"); ax.set_ylabel(r"$\rho_w$ [Wäh/km]")
ax.set_title("(i) R5: Stochastische Dynamik")
ax.legend(fontsize=6); ax.grid(alpha=0.3)

# ── (j) V3: j vs nabla(Phi) Richtungstest (R2) ──
ax = fig.add_subplot(gs[3, 0])
grad_Phi_r2 = np.diff(r2["Phi_fin"]) / dx
ax.scatter(grad_Phi_r2, r2["j_diff_fin"], s=2, alpha=0.5, c="C1")
xlims = ax.get_xlim()
ax.plot(xlims, [0, 0], "k:", lw=0.5)
ax.plot([0, 0], ax.get_ylim(), "k:", lw=0.5)
# j_diff = -D * grad_Phi → negative Korrelation
ax.set_xlabel(r"$\nabla\Phi_w$"); ax.set_ylabel(r"$j_{\mathrm{diff}}$")
# Berechne Alignment
valid_gP = np.abs(grad_Phi_r2) > 1e-10
if np.any(valid_gP):
    align_frac = np.mean(np.sign(r2["j_diff_fin"][valid_gP]) ==
                         np.sign(-grad_Phi_r2[valid_gP]))
else:
    align_frac = 1.0
ax.set_title(f"(j) V3: $j_{{diff}}$ vs $\\nabla\\Phi$ (align={align_frac:.0%})")
ax.grid(alpha=0.3)

# ── (k) V6: Sensitivitäts-Heatmap ──
ax = fig.add_subplot(gs[3, 1])
im = ax.pcolormesh(beta_sens, D_sens, xcm_grid, cmap="RdBu_r", shading="auto")
plt.colorbar(im, ax=ax, label=r"$d\bar{x}/dt$ [km/a]")
ax.set_xlabel(r"$\beta_w$"); ax.set_ylabel(r"$D_w$ [km²/a]")
ax.set_title(r"(k) V6: Sensitivität $D_w \times \beta_w$")
ax.grid(alpha=0.2)

# ── (l) Alle Regime: finales rho(x) ──
ax = fig.add_subplot(gs[3, 2])
for reg in ["R1", "R2", "R3", "R4", "R5"]:
    r = results[reg]
    ax.plot(x, r["rho_xt"][:, -1], color=r["par"]["color"], lw=1.2,
            label=r["par"]["label"][:22])
ax.set_xlabel("x [km]"); ax.set_ylabel(r"$\rho_w(T)$ [Wäh/km]")
ax.set_title("(l) Finale Vermögensprofile")
ax.legend(fontsize=6); ax.grid(alpha=0.3)

# ── (m) R5: Masse über Zeit ──
ax = fig.add_subplot(gs[4, 0])
ax.plot(r5["t"], r5["mass"], "C4-", lw=1.5)
ax.set_xlabel("t [Jahre]"); ax.set_ylabel(r"$\int\rho_w\,dx$ [Wäh]")
ax.set_title("(m) R5: Vermögensmasse (Poisson-Quellen)")
ax.grid(alpha=0.3)

# ── (n) Vermögenspotential-Tabelle ──
ax = fig.add_subplot(gs[4, 1])
ax.axis("off")
table_text = (
    "VERMÖGENSPOTENTIAL (Def. 5.2)\n"
    "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    "Phi_w = h(rho_w) - beta_w * V_w\n"
    "h(rho) = alpha * ln(rho/rho_0)\n\n"
    "Komponente     Eigenschaft\n"
    "──────────────────────────────────\n"
    "h(rho_w)       h'>0: stabile Diffusion\n"
    "               hohe rho -> hohes Phi\n"
    "               -> Kapital fliesst ab\n\n"
    "beta_w*V_w     V_w: Institutionen,\n"
    "               Rechtsstaat, Infra.\n"
    "               hohes V -> niedr. Phi\n"
    "               -> Kapital fliesst hin\n\n"
    "Lucas-Paradox:\n"
    "  V_w^{reich} >> V_w^{arm}\n"
    "  -> Kapital arm->reich!"
)
ax.text(0.05, 0.95, table_text, transform=ax.transAxes, fontsize=9,
        fontfamily="monospace", va="top",
        bbox=dict(boxstyle="round,pad=0.5", facecolor="#eef2ff", alpha=0.9))

# ── (o) Funktionalformen ──
ax = fig.add_subplot(gs[4, 2])
ax.axis("off")
fn_text = (
    "FUNKTIONALFORMEN\n"
    "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    "RAEUMLICH:\n"
    "  * Gaussprofil (Anfangsdichte)\n"
    "  * Glatter Sprung (logistisch)\n"
    "  * Rampe (V_w-Gradient)\n"
    "  * Sinusoidal (v_w-Profil)\n\n"
    "ZEITLICH:\n"
    "  * Ornstein-Uhlenbeck (D_w, V_w)\n"
    "  * GBM (verfuegbar)\n"
    "  * Logist. Uebergang (Krise R3)\n"
    "  * Poisson-Pulse (S_w)\n\n"
    "POTENTIAL:\n"
    "  * h = alpha * ln(rho/rho_0)\n"
    "    (logarithm. Konzentration)"
)
ax.text(0.05, 0.95, fn_text, transform=ax.transAxes, fontsize=9,
        fontfamily="monospace", va="top",
        bbox=dict(boxstyle="round,pad=0.5", facecolor="#f0fdf4", alpha=0.9))

# ═══════════════════════════════════════════════
# METADATEN-PANEL
# ═══════════════════════════════════════════════
ax_meta = fig.add_subplot(gs[5, :])
ax_meta.axis("off")
meta = (
    "━━━ SIMULATIONSMETADATEN ━━━\n"
    "\n"
    "GLEICHUNG:  II.1 (§5.4)   j_w = -D_w * nabla(Phi_w) + v_w * rho_w\n"
    "POTENTIAL:  Phi_w = h(rho_w) - beta_w * V_w   (Def. 5.2)\n"
    "            h(rho) = alpha * ln(rho/rho_0),  h' = alpha/rho > 0\n"
    "KOPPLUNG:   drho_w/dt = -nabla . j_w + S_w  (Vermögenskontinuität)\n"
    "\n"
    "┌─── ENDOGENE VARIABLEN ───────────────────────────────────────────┐\n"
    "│  rho_w(x,t)   Vermögensdichte     [Wäh/km]    Def. 5.1         │\n"
    "│  j_w(x,t)     Vermögensfluss      [Wäh/(km*a)] II.1            │\n"
    "│  Phi_w(x,t)   Vermögenspotential  [dimlos]     Def. 5.2        │\n"
    "│  h(rho_w)     Konzentrationsterm   [dimlos]     alpha*ln(rho)    │\n"
    "└──────────────────────────────────────────────────────────────────┘\n"
    "┌─── EXOGENE VARIABLEN ────────────────────────────────────────────┐\n"
    "│  V_w(x,t)     Standortattraktivität [dimlos]   Institutionen    │\n"
    "│  v_w(x,t)     Driftgeschwindigkeit  [km/a]     Investitionspr.  │\n"
    "│  S_w(x,t)     Quellen/Senken        [Wäh/(km*a)]               │\n"
    "└──────────────────────────────────────────────────────────────────┘\n"
    "┌─── PARAMETER ────────────────────────────────────────────────────┐\n"
    "│  D_w    Diffusion    1-40 km²/a     alpha  Konz.sens.  3-5     │\n"
    "│  beta_w Standort     0-5            rho_0  Ref.dichte  10      │\n"
    "│  v_w    Drift        0-0.5 km/a     L      Domäne      100 km  │\n"
    "└──────────────────────────────────────────────────────────────────┘\n"
    "┌─── NUMERIK ──────────────────────────────────────────────────────┐\n"
    "│  MOL: NX=201, dx=0.5 km, Neumann BC, Upwind-Konvektion        │\n"
    "│  ODE: RK45, rtol=1e-9, atol=1e-11, max_step=0.2              │\n"
    "│  Stochast.: Euler-Maruyama (OU), Poisson-Pulse                │\n"
    "│  Sensitivität: 25x25=625 Punkte                                │\n"
    "└──────────────────────────────────────────────────────────────────┘"
)
ax_meta.text(0.01, 0.98, meta, transform=ax_meta.transAxes,
             fontsize=7, fontfamily="monospace", va="top",
             bbox=dict(boxstyle="round,pad=0.5", facecolor="lightyellow", alpha=0.9))

plt.savefig(PLOT, dpi=180, bbox_inches="tight")
print(f"\n  Plot -> {PLOT}")

# ═══════════════════════════════════════════════
# Daten speichern
# ═══════════════════════════════════════════════
save_dict = dict(
    x=x, t=T_EVAL,
    D_sens=D_sens, beta_sens=beta_sens, xcm_grid=xcm_grid,
)
for reg in ["R1", "R2", "R3", "R4", "R5"]:
    r = results[reg]
    save_dict[f"{reg}_rho_init"] = r["rho_xt"][:, 0]
    save_dict[f"{reg}_rho_final"] = r["rho_xt"][:, -1]
    save_dict[f"{reg}_mass"] = r["mass"]
    save_dict[f"{reg}_x_cm"] = r["x_cm"]
    save_dict[f"{reg}_j_fin"] = r["j_fin"]
    save_dict[f"{reg}_Phi_fin"] = r["Phi_fin"]

np.savez_compressed(DATA, **save_dict)
print(f"  Daten -> {DATA}")

# ═══════════════════════════════════════════════
# ZUSAMMENFASSUNG
# ═══════════════════════════════════════════════
print(f"\n{'='*72}")
print("  ZUSAMMENFASSUNG S11")
print(f"{'='*72}")
print(f"  V1 Massenerhaltung (S=0):   dM/M = {mass_err:.2e}  "
      f"{'✅' if mass_err < 5e-3 else '⚠'}")
print(f"  V2 Diversifikation->GG:     sigma/mu = {spatial_var:.4f}  "
      f"{'✅' if spatial_var < 0.1 else '⚠'}")
print(f"  V3 Lucas-Paradox:           x_cm: {r2['x_cm'][0]:.1f}->{r2['x_cm'][-1]:.1f}  "
      f"{'✅' if lucas_ok else '⚠'}")
print(f"  V4 Kapitalflucht:           dx={r3['x_cm'][idx_150]-r3['x_cm'][idx_80]:+.1f} km  "
      f"{'✅' if flight_ok else '⚠'}")
print(f"  V5 Konvektive Drift:        dx={r4['x_cm'][-1]-r4['x_cm'][0]:+.1f} km  "
      f"{'✅' if drift_ok else '⚠'}")
print(f"  V6 Sensitivität 625pt:      dx_cm/dt in "
      f"[{xcm_grid.min():.2f}, {xcm_grid.max():.2f}]  "
      f"{'✅' if sens_monoton else '⚠'}")
print()
for reg in ["R1", "R2", "R3", "R4", "R5"]:
    par = results[reg]["par"]
    r = results[reg]
    print(f"  {par['label']:30s}  M(T)={r['mass'][-1]:8.1f}  "
          f"x_cm(T)={r['x_cm'][-1]:6.2f}  "
          f"rho_max={r['rho_xt'][:,-1].max():8.2f}")

all_pass = (mass_err < 5e-3 and spatial_var < 0.1 and lucas_ok
            and flight_ok and drift_ok and sens_monoton)
print(f"\n  Gesamtergebnis: {'✅ ALLE VALIDIERUNGEN BESTANDEN' if all_pass else '⚠ EINIGE VALIDIERUNGEN FEHLGESCHLAGEN'}")
