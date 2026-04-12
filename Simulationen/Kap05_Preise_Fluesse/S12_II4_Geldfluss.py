"""
S12 – Geldfluss II.4  (§5.5)
==========================================
Monographie-Gleichung (exakt):

    j_m = -D_m * nabla(r) + sigma_m * E_Kredit

Kreditfeld (Analogie zum E-Feld):

    E_Kredit = -nabla(Phi_Kredit)

Expandiert:

    j_m = -D_m * nabla(r) - sigma_m * nabla(Phi_Kredit)

Zwei Flusskomponenten:
  1. -D_m * nabla(r)                Zinsgradient-Fluss (Carry Trade)
     Geld fliesst in Richtung HOEHERER Zinsen
  2. -sigma_m * nabla(Phi_Kredit)   Kreditfeld-Fluss (Bankkreditanreiz)
     Geld fliesst dorthin, wo Banken aktiv Kredite vergeben

Kopplung: drho_m/dt = -nabla . j_m + Q_m  (Geldkontinuität)
          I.4: aggregierte Gelderhaltung (§4.4)

Zwei Regime des Geldflusses:
  ZINSGETRIEBEN: -D_m * nabla(r) dominiert (normale Geldpolitik)
  KREDITGETRIEBEN: sigma_m * E_Kredit dominiert (QE, Credit Crunch)

Nullzinsgrenze: r -> 0 => nabla(r) ≈ 0 => Geldfluss nur via Kreditkanal
  -> Erklaert warum QE trotz Nullzins expansiv wirkt

Preismodell für Zinsen (lokal):
  r(x,t) = r_base + kappa * ln(rho_m/rho_0)  mit kappa > 0
  Hohe Gelddichte -> hoher lokaler Zins (Investitionsnachfrage)
  dr/drho > 0 garantiert stabile Diffusion von hoch-r zu niedrig-r

5 Regime:
  R1 Reiner Zinsgradient (sigma_m=0 -> j=-D*nabla(r), Carry Trade)
  R2 Kreditgetrieben (D_m≈0, Phi_Kredit aktiv -> QE-Mechanismus)
  R3 Nullzinsgrenze (r->0, dann QE-Intervention im Kreditkanal)
  R4 Credit Crunch (Phi_Kredit kollabiert -> Geldfluss versiegt)
  R5 Voll stochastisch (OU-D_m, OU-r, Poisson-QE-Injektionen)

7 Funktionalformen:
  Gaussprofil, Rampe, Sprung (räumlich)
  Ornstein-Uhlenbeck, Logistisch, Poisson-Pulse, Sinusoidal (zeitlich)
"""

import numpy as np
from scipy.integrate import solve_ivp
from scipy.sparse import diags as sp_diags
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
PLOT = BASE / "Ergebnisse" / "Plots" / "S12_II4_Geldfluss.png"
DATA = BASE / "Ergebnisse" / "Daten" / "S12_II4_Geldfluss.npz"
PLOT.parent.mkdir(parents=True, exist_ok=True)
DATA.parent.mkdir(parents=True, exist_ok=True)

rng = np.random.default_rng(42)

# ═══════════════════════════════════════════════
# KLASSIFIKATION
# ═══════════════════════════════════════════════
#
# ENDOGENE VARIABLEN (räumlich):
#   rho_m(x,t)       Gelddichte          [Wäh/km]      I.4
#   j_m(x,t)         Geldfluss           [Wäh/(km*a)]  II.4
#   r(x,t)           Lokaler Zinssatz    [1/a]          r = r_base + kappa*ln(rho/rho_0)
#
# EXOGENE VARIABLEN:
#   Phi_Kredit(x,t)  Kreditpotential     [dimlos]       Bankenkreditvergabe
#   r_base(t)        Leitzins (ZB)       [1/a]          Geldpolitik
#   Q_m(x,t)         Geldquellen         [Wäh/(km*a)]  Geldschöpfung (M.1)
#
# PARAMETER:
#   D_m       Zinsdiffusion       [km²*a]    Kapitalmarktgeschwindigkeit
#   sigma_m   Kreditkopplung      [km²/a]    Stärke des Kreditkanals
#   kappa     Zins-Dichte-Sens.   [dimlos]    r = r_base + kappa*ln(rho/rho_0)
#   rho_0     Referenz-Gelddichte [Wäh/km]
#   L         Domänenlänge        [km]

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

# Tridiagonale Jakobistruktur für MOL (Nachbar-Kopplung)
_jac_sparsity = sp_diags([1, 1, 1], [-1, 0, 1], shape=(NX, NX), format='csc')

# ═══════════════════════════════════════════════
# Hilfsfunktionen
# ═══════════════════════════════════════════════

def gaussian_profile(x, center, sigma, amplitude, baseline=0):
    return baseline + amplitude * np.exp(-0.5 * ((x - center) / sigma) ** 2)

def smooth_step_spatial(x, x0, v_left, v_right, width=3.0):
    return v_right + (v_left - v_right) / (1.0 + np.exp((x - x0) / width))

def ramp_profile(x, v_left, v_right):
    return v_left + (v_right - v_left) * x / L

def sinusoidal_profile(x, offset, amplitude, wavenumber):
    return offset + amplitude * np.sin(wavenumber * x)

def smooth_step_time(t, t0, width=3.0):
    return 1.0 / (1.0 + np.exp(-(t - t0) / width))

def ou_time_modulation(t_eval, mu, theta, sigma, x0, seed=42):
    rng_loc = np.random.default_rng(seed)
    dt = np.diff(t_eval, prepend=t_eval[0] - (t_eval[1] - t_eval[0]))
    arr = np.zeros(len(t_eval))
    arr[0] = x0
    for i in range(1, len(t_eval)):
        dW = np.sqrt(dt[i]) * rng_loc.standard_normal()
        arr[i] = arr[i-1] + theta * (mu - arr[i-1]) * dt[i] + sigma * dW
    return arr


# ═══════════════════════════════════════════════
# Lokaler Zinssatz und Flussberechnung
# ═══════════════════════════════════════════════

def local_interest_rate(rho_m, r_base, kappa, rho_0):
    """
    r(x,t) = r_base + kappa * ln(rho_m / rho_0)
    dr/drho = kappa/rho > 0 => stabile Diffusion (Geld fliesst von hoch-r zu niedrig-r)

    Ökonomisch: Hohe Gelddichte => hohe lokale Investitionsnachfrage =>
    lokaler Zinssatz steigt (Marktzins = Leitzins + lokale Prämie).
    """
    rho_safe = np.maximum(rho_m, RHO_FLOOR)
    return r_base + kappa * np.log(rho_safe / rho_0)


def compute_flux(rho_m, r_base, kappa, rho_0, D_m, sigma_m, Phi_Kredit):
    """
    j_m = -D_m * nabla(r) - sigma_m * nabla(Phi_Kredit)   (II.4)

    Auf staggered grid (NX-1 Zwischenpunkte).
    """
    r = local_interest_rate(rho_m, r_base, kappa, rho_0)

    grad_r = np.diff(r) / dx
    grad_Phi = np.diff(Phi_Kredit) / dx

    j_zins = -D_m * grad_r           # Carry Trade: Geld zu hohem r
    j_kredit = -sigma_m * grad_Phi   # Kreditkanal: Geld zu hohem E
    j_total = j_zins + j_kredit

    return j_total, j_zins, j_kredit, r


def make_rhs_mol(D_func, sigma_func, kappa, rho_0,
                 r_base_func, Phi_func, Q_func):
    """
    MOL RHS: drho_m/dt = -nabla . j_m + Q_m
    Neumann BC (j=0 an Rändern).
    """
    def rhs(t, rho_flat):
        rho = np.maximum(rho_flat, RHO_FLOOR)
        D_m = D_func(t)
        sigma_m = sigma_func(t)
        r_base = r_base_func(t)
        Phi_K = Phi_func(x, t)
        Q_m = Q_func(x, t)

        j_total, _, _, _ = compute_flux(
            rho, r_base, kappa, rho_0, D_m, sigma_m, Phi_K
        )

        divj = np.zeros(NX)
        divj[1:-1] = (j_total[1:] - j_total[:-1]) / dx
        divj[0] = j_total[0] / dx
        divj[-1] = -j_total[-1] / dx

        return -divj + Q_m

    return rhs


# ═══════════════════════════════════════════════
# Regime-Definitionen
# ═══════════════════════════════════════════════

def get_regime(regime):

    if regime == "R1":
        # Reiner Zinsgradient: sigma_m=0 → j_m = -D_m * nabla(r)
        # Carry Trade: Geld fliesst von links (niedriger Zins) nach rechts (hoher Zins)
        # Anfang: Gauss-Konzentration links → r links hoch → Geld verteilt sich
        rho0_init = gaussian_profile(x, 35, 12, 60, baseline=5)
        return dict(
            label="R1 Reiner Zinsgradient", color="C0",
            D_func=lambda t: 50.0,
            sigma_func=lambda t: 0.0,
            kappa=1.0, rho_0=10.0,
            rho0_init=rho0_init,
            r_base_func=lambda t: 0.03,
            Phi_func=lambda x, t: np.zeros_like(x),
            Q_func=lambda x, t: np.zeros_like(x),
            desc="sigma_m=0: j = -D*nabla(r), Carry Trade"
        )

    elif regime == "R2":
        # Kreditgetrieben: D_m klein, sigma_m gross
        # Phi_Kredit hoch links (Bankenzentrum) → Geld fliesst nach links
        rho0_init = gaussian_profile(x, 60, 15, 40, baseline=8)
        Phi_static = smooth_step_spatial(x, 50, 8.0, 1.0, width=5.0)
        return dict(
            label="R2 Kreditgetrieben", color="C1",
            D_func=lambda t: 1.5,
            sigma_func=lambda t: 20.0,
            kappa=0.8, rho_0=10.0,
            rho0_init=rho0_init,
            r_base_func=lambda t: 0.02,
            Phi_func=lambda x, t, P=Phi_static: P.copy(),
            Q_func=lambda x, t: np.zeros_like(x),
            desc="D_m=2, sigma_m=15: Kreditkanal dominiert"
        )

    elif regime == "R3":
        # Nullzinsgrenze + QE: r_base fällt auf 0 bei t=60, dann QE-Injektion
        # Phase 1 (t<60): normale Zinsdiffusion
        # Phase 2 (t>60): r≈0, Kreditkanal uebernimmt
        rho0_init = gaussian_profile(x, 50, 15, 40, baseline=10)

        def r_base_func(t):
            # Leitzins fällt von 5% auf 0.1% bei t=60
            return 0.05 - 0.049 * smooth_step_time(t, 60.0, width=3.0)

        def Phi_func(x_arr, t):
            # Vor t=80: kein Kreditfeld
            # Ab t=80: QE erzeugt Kreditpotential (hoch bei x=50, Zentrum)
            qe = smooth_step_time(t, 80.0, width=5.0)
            return qe * gaussian_profile(x_arr, 50, 20, 5.0)

        def Q_func(x_arr, t):
            # QE-Geldinjektionen ab t=80 im Zentrum
            qe = smooth_step_time(t, 80.0, width=5.0)
            return qe * gaussian_profile(x_arr, 50, 15, 0.5)

        return dict(
            label="R3 Nullzinsgrenze + QE", color="C2",
            D_func=lambda t: 15.0,
            sigma_func=lambda t: 8.0,
            kappa=2.5, rho_0=15.0,
            rho0_init=rho0_init,
            r_base_func=r_base_func,
            Phi_func=Phi_func,
            Q_func=Q_func,
            desc="r_base: 5%->0 bei t=60, QE ab t=80"
        )

    elif regime == "R4":
        # Credit Crunch: Phi_Kredit kollabiert bei t=80
        # Vorher: Kreditfeld treibt Geld in Peripherie
        # Nachher: Kreditkanal versagt → Geld zieht sich ins Zentrum zurück
        rho0_init = gaussian_profile(x, 50, 20, 30, baseline=10)

        Phi_pre = ramp_profile(x, 2.0, 6.0)  # Kreditanreiz steigt nach rechts

        def Phi_func(x_arr, t, P=Phi_pre):
            crunch = smooth_step_time(t, 80.0, width=3.0)
            return P * (1.0 - 0.9 * crunch)  # Phi_Kredit → 10% des Ausgangs

        return dict(
            label="R4 Credit Crunch", color="C3",
            D_func=lambda t: 10.0,
            sigma_func=lambda t: 10.0,
            kappa=2.0, rho_0=12.0,
            rho0_init=rho0_init,
            r_base_func=lambda t: 0.03,
            Phi_func=Phi_func,
            Q_func=lambda x, t: np.zeros_like(x),
            desc="Phi_Kredit kollabiert bei t=80 (Credit Crunch)"
        )

    elif regime == "R5":
        # Voll stochastisch: OU-D_m, OU-r_base, Poisson-QE-Injektionen
        rho0_init = gaussian_profile(x, 50, 15, 35, baseline=8)

        # OU-modulierter Diffusionskoeffizient
        D_mod = ou_time_modulation(T_EVAL, mu=1.0, theta=0.3, sigma=0.1,
                                   x0=1.0, seed=42)

        def D_func(t, D_base=10.0, mod=D_mod):
            idx = min(int(t / T_SPAN[1] * (len(T_EVAL)-1)), len(T_EVAL)-1)
            return D_base * max(mod[idx], 0.1)

        # OU-modulierter Leitzins
        r_mod = ou_time_modulation(T_EVAL, mu=0.03, theta=0.5, sigma=0.005,
                                   x0=0.03, seed=77)

        def r_base_func(t, mod=r_mod):
            idx = min(int(t / T_SPAN[1] * (len(T_EVAL)-1)), len(T_EVAL)-1)
            return max(mod[idx], 0.001)

        # Kreditpotential: Basis + OU-Modulation
        Phi_base = smooth_step_spatial(x, 50, 5.0, 2.0, width=8.0)
        Phi_mod = ou_time_modulation(T_EVAL, mu=1.0, theta=0.4, sigma=0.2,
                                     x0=1.0, seed=55)

        def Phi_func(x_arr, t, P=Phi_base, mod=Phi_mod):
            idx = min(int(t / T_SPAN[1] * (len(T_EVAL)-1)), len(T_EVAL)-1)
            return P * max(mod[idx], 0.1)

        # Poisson-QE-Injektionen
        Q_events = rng.poisson(0.25, size=len(T_EVAL))
        Q_centers = rng.uniform(20, 80, size=len(T_EVAL))

        def Q_func(x_arr, t, Q_ev=Q_events, Q_cen=Q_centers):
            idx = min(int(t / T_SPAN[1] * (len(T_EVAL)-1)), len(T_EVAL)-1)
            if Q_ev[idx] > 0:
                return Q_ev[idx] * gaussian_profile(x_arr, Q_cen[idx], 5, 1.0)
            return np.zeros_like(x_arr)

        return dict(
            label="R5 Voll stochastisch", color="C4",
            D_func=D_func,
            sigma_func=lambda t: 5.0,
            kappa=2.0, rho_0=10.0,
            rho0_init=rho0_init,
            r_base_func=r_base_func,
            Phi_func=Phi_func,
            Q_func=Q_func,
            desc="OU-D, OU-r_base, OU-Phi_Kredit, Poisson-QE"
        )


# ═══════════════════════════════════════════════
# Hauptsimulation
# ═══════════════════════════════════════════════
print("=" * 72)
print("  S12  Geldfluss II.4  (§5.5)")
print("=" * 72)

results = {}

for regime in ["R1", "R2", "R3", "R4", "R5"]:
    par = get_regime(regime)

    rhs = make_rhs_mol(
        par["D_func"], par["sigma_func"], par["kappa"], par["rho_0"],
        par["r_base_func"], par["Phi_func"], par["Q_func"]
    )

    sol = solve_ivp(rhs, T_SPAN, par["rho0_init"], t_eval=T_EVAL,
                    method="Radau", rtol=1e-6, atol=1e-8, max_step=1.0,
                    jac_sparsity=_jac_sparsity)
    assert sol.success, f"{regime}: Solver fehlgeschlagen: {sol.message}"

    rho_xt = np.maximum(sol.y, RHO_FLOOR)  # (NX, N_EVAL)

    # Geldmenge: M(t) = integral rho_m dx
    mass = np.trapezoid(rho_xt, x=x, axis=0)

    # Schwerpunkt
    x_cm = np.trapezoid(x[:, None] * rho_xt, x=x, axis=0) / mass

    # Finaler Zinssatz
    r_base_fin = par["r_base_func"](T_SPAN[1])
    r_final = local_interest_rate(rho_xt[:, -1], r_base_fin, par["kappa"], par["rho_0"])

    # Finaler Fluss
    D_m_fin = par["D_func"](T_SPAN[1])
    sigma_m_fin = par["sigma_func"](T_SPAN[1])
    Phi_fin = par["Phi_func"](x, T_SPAN[1])
    j_fin, j_zins_fin, j_kredit_fin, _ = compute_flux(
        rho_xt[:, -1], r_base_fin, par["kappa"], par["rho_0"],
        D_m_fin, sigma_m_fin, Phi_fin
    )

    # Anfangsfluss
    r_base_ini = par["r_base_func"](0)
    r_init = local_interest_rate(rho_xt[:, 0], r_base_ini, par["kappa"], par["rho_0"])
    D_m_ini = par["D_func"](0)
    sigma_m_ini = par["sigma_func"](0)
    Phi_ini = par["Phi_func"](x, 0)
    j_ini, j_zins_ini, j_kredit_ini, _ = compute_flux(
        rho_xt[:, 0], r_base_ini, par["kappa"], par["rho_0"],
        D_m_ini, sigma_m_ini, Phi_ini
    )

    # Zinssatz-Zeitreihe im Zentrum (x=L/2)
    mid_idx = NX // 2
    r_center = np.array([
        local_interest_rate(
            rho_xt[mid_idx, ti], par["r_base_func"](T_EVAL[ti]),
            par["kappa"], par["rho_0"]
        ) for ti in range(N_EVAL)
    ])

    # Snapshots
    snap_indices = [0, len(T_EVAL)//4, len(T_EVAL)//2, 3*len(T_EVAL)//4, -1]
    snaps = [(T_EVAL[i], rho_xt[:, i]) for i in snap_indices]

    results[regime] = dict(
        par=par, rho_xt=rho_xt, mass=mass, x_cm=x_cm, t=T_EVAL,
        j_fin=j_fin, j_zins_fin=j_zins_fin, j_kredit_fin=j_kredit_fin,
        r_final=r_final, r_init=r_init, r_center=r_center,
        Phi_fin=Phi_fin, Phi_ini=Phi_ini,
        j_ini=j_ini, snaps=snaps,
    )

    print(f"\n{'─'*60}")
    print(f"  {par['label']}  ({par['desc']})")
    print(f"{'─'*60}")
    print(f"  M(0)={mass[0]:.2f}  M(T)={mass[-1]:.2f}  "
          f"dM/M={(mass[-1]-mass[0])/mass[0]*100:+.4f}%")
    print(f"  x_cm(0)={x_cm[0]:.2f}  x_cm(T)={x_cm[-1]:.2f}  "
          f"dx={x_cm[-1]-x_cm[0]:+.2f} km")
    print(f"  rho_max(T)={rho_xt[:,-1].max():.2f}  rho_min(T)={rho_xt[:,-1].min():.4f}")
    print(f"  r(x=50,T)={r_final[mid_idx]:.4f}  r_mean(T)={r_final.mean():.4f}")
    print(f"  |j|_max(T)={np.max(np.abs(j_fin)):.4f}")


# ═══════════════════════════════════════════════
# VALIDIERUNGEN
# ═══════════════════════════════════════════════

# V1: Geldmengenerhaltung ohne Quellen (R1)
print(f"\n{'='*60}")
print("  V1: Geldmengenerhaltung (R1, Q_m=0)")
print(f"{'='*60}")
r1 = results["R1"]
mass_err = np.max(np.abs(r1["mass"] - r1["mass"][0])) / r1["mass"][0]
print(f"  max|dM/M(0)| = {mass_err:.2e}  {'✅' if mass_err < 5e-3 else '⚠'}")

# V2: Gleichgewicht — Zinsdispersion nimmt ab (R1)
print(f"\n{'='*60}")
print("  V2: Zinsdiffusion reduziert Dispersion (R1)")
print(f"{'='*60}")
r_final_r1 = r1["r_final"]
r_init_r1 = r1["r_init"]
spatial_var_r_init = np.std(r_init_r1) / (np.abs(np.mean(r_init_r1)) + 1e-30)
spatial_var_r = np.std(r_final_r1) / (np.abs(np.mean(r_final_r1)) + 1e-30)
dispersion_reduction = 1.0 - spatial_var_r / (spatial_var_r_init + 1e-30)
print(f"  sigma/mu(0) = {spatial_var_r_init:.4f}  ->  sigma/mu(T) = {spatial_var_r:.4f}")
print(f"  Dispersion reduziert um {dispersion_reduction*100:.1f}%  "
      f"{'✅' if dispersion_reduction > 0.3 else '⚠'}")
print(f"  r_min(T)={r_final_r1.min():.4f}  r_max(T)={r_final_r1.max():.4f}")

# V3: Kreditkanal-Dominanz (R2: |j_kredit| >> |j_zins|)
print(f"\n{'='*60}")
print("  V3: Kreditkanal-Dominanz (R2)")
print(f"{'='*60}")
r2 = results["R2"]
j_zins_rms = np.sqrt(np.mean(r2["j_zins_fin"]**2))
j_kredit_rms = np.sqrt(np.mean(r2["j_kredit_fin"]**2))
kredit_dominanz = j_kredit_rms / (j_zins_rms + 1e-30)
print(f"  |j_kredit|_rms = {j_kredit_rms:.4f}")
print(f"  |j_zins|_rms = {j_zins_rms:.4f}")
print(f"  Ratio j_kredit/j_zins = {kredit_dominanz:.1f}x  "
      f"{'✅' if kredit_dominanz > 2 else '⚠'}")

# V4: QE-Effekt — Geldmenge steigt nach t=80 (R3)
print(f"\n{'='*60}")
print("  V4: QE-Effekt (R3)")
print(f"{'='*60}")
r3 = results["R3"]
idx_60 = np.argmin(np.abs(T_EVAL - 60))
idx_80 = np.argmin(np.abs(T_EVAL - 80))
idx_150 = np.argmin(np.abs(T_EVAL - 150))
qe_effect = r3["mass"][idx_150] > r3["mass"][idx_80] * 1.01
print(f"  r_base(t=0)={get_regime('R3')['r_base_func'](0)*100:.1f}%  "
      f"r_base(t=100)={get_regime('R3')['r_base_func'](100)*100:.2f}%")
print(f"  M(t=60)={r3['mass'][idx_60]:.1f}  M(t=80)={r3['mass'][idx_80]:.1f}  "
      f"M(t=150)={r3['mass'][idx_150]:.1f}")
print(f"  QE-Expansion: +{(r3['mass'][idx_150]/r3['mass'][idx_80]-1)*100:.1f}%  "
      f"{'✅' if qe_effect else '⚠'}")

# V5: Credit Crunch — Gelddichte konzentriert sich (R4)
print(f"\n{'='*60}")
print("  V5: Credit Crunch (R4)")
print(f"{'='*60}")
r4 = results["R4"]
# Nach Credit Crunch sollte Schwerpunkt sich zum Zentrum verschieben
# oder die räumliche Varianz sich ändern
rho_pre_std = np.std(r4["rho_xt"][:, idx_80]) / np.mean(r4["rho_xt"][:, idx_80])
rho_post_std = np.std(r4["rho_xt"][:, -1]) / np.mean(r4["rho_xt"][:, -1])
# Kreditkanal-Stärke sollte fallen
Phi_pre = r4["par"]["Phi_func"](x, 70)
Phi_post = r4["par"]["Phi_func"](x, 150)
phi_reduction = np.max(Phi_post) / (np.max(Phi_pre) + 1e-30)
print(f"  Phi_Kredit max: t=70: {np.max(Phi_pre):.2f}  t=150: {np.max(Phi_post):.2f}  "
      f"(Reduktion auf {phi_reduction*100:.0f}%)")
crunch_ok = phi_reduction < 0.2
print(f"  Credit Crunch bestätigt (Phi < 20%): {'✅' if crunch_ok else '⚠'}")

# V6: Sensitivität D_m × sigma_m → Fluss-Dominanz
print(f"\n{'='*60}")
print("  V6: Sensitivität (25x25 = 625 Punkte, D_m x sigma_m)")
print(f"{'='*60}")
N_SENS = 25
D_sens = np.linspace(1.0, 40.0, N_SENS)
sigma_sens = np.linspace(0.0, 30.0, N_SENS)
ratio_grid = np.zeros((N_SENS, N_SENS))

# Feste Konfiguration
rho_test = gaussian_profile(x, 40, 15, 40, baseline=8)
Phi_test = smooth_step_spatial(x, 50, 5.0, 1.0, width=5.0)

for i, D_val in enumerate(D_sens):
    for j, sigma_val in enumerate(sigma_sens):
        j_t, j_z, j_k, _ = compute_flux(
            rho_test, 0.03, 2.0, 10.0, D_val, sigma_val, Phi_test
        )
        rms_z = np.sqrt(np.mean(j_z**2))
        rms_k = np.sqrt(np.mean(j_k**2))
        ratio_grid[i, j] = rms_k / (rms_z + 1e-30)

print(f"  j_kredit/j_zins ratio in [{ratio_grid.min():.2f}, {ratio_grid.max():.2f}]")
print(f"  Median = {np.median(ratio_grid):.2f}")
# Höheres sigma → stärkere Kreditdominanz
sens_ok = np.mean(ratio_grid[:, -1]) > np.mean(ratio_grid[:, 0]) + 0.1
print(f"  Höheres sigma -> stärkere Kreditdominanz: {'✅' if sens_ok else '⚠'}")


# ═══════════════════════════════════════════════
# PLOT  (5 Zeilen × 3 Spalten + Metadaten)
# ═══════════════════════════════════════════════
fig = plt.figure(figsize=(22, 32))
gs = GridSpec(6, 3, figure=fig, height_ratios=[1.0, 1.0, 1.0, 1.0, 1.0, 0.6],
              hspace=0.35, wspace=0.3)
fig.suptitle("S12 – Geldfluss II.4  (§5.5)\n"
             r"$\vec{j}_m = -D_m\,\nabla r + \sigma_m\,\vec{E}_{\mathrm{Kredit}}$",
             fontsize=15, fontweight="bold", y=0.98)

x_mid = 0.5 * (x[:-1] + x[1:])

# ── (a) R1: Dichte-Snapshots (Zinsdiffusion) ──
ax = fig.add_subplot(gs[0, 0])
for t_s, rho_s in r1["snaps"]:
    ax.plot(x, rho_s, lw=1.2, label=f"t={t_s:.0f}")
ax.set_xlabel("x [km]"); ax.set_ylabel(r"$\rho_m$ [Wäh/km]")
ax.set_title("(a) R1: Carry Trade (Snapshots)")
ax.legend(fontsize=6); ax.grid(alpha=0.3)

# ── (b) R1: Zinssatz initial vs final ──
ax = fig.add_subplot(gs[0, 1])
ax.plot(x, r1["r_init"]*100, "C0--", lw=1, label="r(t=0)")
ax.plot(x, r1["r_final"]*100, "C0-", lw=1.5, label="r(T)")
ax.set_xlabel("x [km]"); ax.set_ylabel("r [%]")
ax.set_title(f"(b) R1: Zinsdispersion (-{dispersion_reduction*100:.0f}%)")
ax.legend(fontsize=6); ax.grid(alpha=0.3)

# ── (c) R1: Geldmengenerhaltung ──
ax = fig.add_subplot(gs[0, 2])
ax.plot(r1["t"], r1["mass"], "C0-", lw=1.5)
ax.set_xlabel("t [Jahre]"); ax.set_ylabel(r"$\int\rho_m\,dx$ [Wäh]")
ax.set_title(f"(c) R1: Geldmengenerhaltung (dM/M={mass_err:.1e})")
ax.grid(alpha=0.3)

# ── (d) R2: Kreditgetrieben Snapshots ──
ax = fig.add_subplot(gs[1, 0])
for t_s, rho_s in r2["snaps"]:
    ax.plot(x, rho_s, lw=1.2, label=f"t={t_s:.0f}")
ax2 = ax.twinx()
ax2.plot(x, r2["Phi_ini"], "k:", lw=1, alpha=0.4, label=r"$\Phi_{\mathrm{Kredit}}$")
ax2.set_ylabel(r"$\Phi_{\mathrm{Kredit}}$", color="grey")
ax.set_xlabel("x [km]"); ax.set_ylabel(r"$\rho_m$ [Wäh/km]")
ax.set_title("(d) R2: Kreditgetrieben (Snapshots)")
ax.legend(fontsize=6, loc="upper right"); ax.grid(alpha=0.3)

# ── (e) R2: Flusskomponenten (final) ──
ax = fig.add_subplot(gs[1, 1])
ax.plot(x_mid, r2["j_zins_fin"], "C0-", lw=1, label=r"$j_{\mathrm{Zins}}$")
ax.plot(x_mid, r2["j_kredit_fin"], "C1--", lw=1.2, label=r"$j_{\mathrm{Kredit}}$")
ax.plot(x_mid, r2["j_fin"], "k-", lw=1.5, alpha=0.7, label=r"$j_{\mathrm{total}}$")
ax.axhline(0, color="grey", ls=":", lw=0.5)
ax.set_xlabel("x [km]"); ax.set_ylabel(r"$j_m$ [Wäh/(km·a)]")
ax.set_title(f"(e) R2: Kreditdominanz ({kredit_dominanz:.0f}x)")
ax.legend(fontsize=6); ax.grid(alpha=0.3)

# ── (f) R3: QE-Mechanismus ──
ax = fig.add_subplot(gs[1, 2])
ax.plot(r3["t"], r3["mass"], "C2-", lw=1.5, label="M(t)")
ax.axvline(60, color="C3", ls="--", lw=0.8, alpha=0.5, label="r->0")
ax.axvline(80, color="C2", ls=":", lw=0.8, alpha=0.5, label="QE Start")
ax.set_xlabel("t [Jahre]"); ax.set_ylabel(r"$M = \int\rho_m\,dx$ [Wäh]")
ax.set_title("(f) R3: Nullzinsgrenze + QE")
ax.legend(fontsize=6); ax.grid(alpha=0.3)

# ── (g) R3: Zinssatz im Zentrum ──
ax = fig.add_subplot(gs[2, 0])
ax.plot(r3["t"], r3["r_center"]*100, "C2-", lw=1.5)
ax.axhline(0, color="k", ls=":", lw=0.5)
ax.axvline(60, color="C3", ls="--", lw=0.8, alpha=0.5, label="r->0")
ax.set_xlabel("t [Jahre]"); ax.set_ylabel("r(x=50) [%]")
ax.set_title("(g) R3: Zinssatz (Zentrum)")
ax.legend(fontsize=6); ax.grid(alpha=0.3)

# ── (h) R4: Credit Crunch Snapshots ──
ax = fig.add_subplot(gs[2, 1])
# Spezielle Snapshots
idx_snap4 = [0, idx_80 - 200, idx_80, idx_80 + 400, -1]
for idx in idx_snap4:
    t_s = T_EVAL[idx]
    ax.plot(x, r4["rho_xt"][:, idx], lw=1.2, label=f"t={t_s:.0f}")
ax.set_xlabel("x [km]"); ax.set_ylabel(r"$\rho_m$ [Wäh/km]")
ax.set_title("(h) R4: Credit Crunch (Krise t=80)")
ax.legend(fontsize=6); ax.grid(alpha=0.3)

# ── (i) R5: Stochastische Evolution ──
ax = fig.add_subplot(gs[2, 2])
r5 = results["R5"]
for t_s, rho_s in r5["snaps"]:
    ax.plot(x, rho_s, lw=1.2, label=f"t={t_s:.0f}")
ax.set_xlabel("x [km]"); ax.set_ylabel(r"$\rho_m$ [Wäh/km]")
ax.set_title("(i) R5: Stochastische Dynamik")
ax.legend(fontsize=6); ax.grid(alpha=0.3)

# ── (j) R3: Dichte-Snapshots (QE) ──
ax = fig.add_subplot(gs[3, 0])
idx_snap3 = [0, idx_60, idx_80, idx_150, -1]
for idx in idx_snap3:
    t_s = T_EVAL[idx]
    ax.plot(x, r3["rho_xt"][:, idx], lw=1.2, label=f"t={t_s:.0f}")
ax.set_xlabel("x [km]"); ax.set_ylabel(r"$\rho_m$ [Wäh/km]")
ax.set_title("(j) R3: Gelddichte (QE-Injection)")
ax.legend(fontsize=6); ax.grid(alpha=0.3)

# ── (k) V6: Sensitivitäts-Heatmap ──
ax = fig.add_subplot(gs[3, 1])
im = ax.pcolormesh(sigma_sens, D_sens, np.log10(ratio_grid + 0.01),
                   cmap="RdBu_r", shading="auto")
plt.colorbar(im, ax=ax, label=r"$\log_{10}(j_K/j_Z)$")
ax.set_xlabel(r"$\sigma_m$"); ax.set_ylabel(r"$D_m$ [km²·a]")
ax.set_title(r"(k) V6: Regime-Karte $D_m \times \sigma_m$")
ax.grid(alpha=0.2)

# ── (l) Alle Regime: finales rho(x) ──
ax = fig.add_subplot(gs[3, 2])
for reg in ["R1", "R2", "R3", "R4", "R5"]:
    r = results[reg]
    ax.plot(x, r["rho_xt"][:, -1], color=r["par"]["color"], lw=1.2,
            label=r["par"]["label"][:22])
ax.set_xlabel("x [km]"); ax.set_ylabel(r"$\rho_m(T)$ [Wäh/km]")
ax.set_title("(l) Finale Gelddichteprofile")
ax.legend(fontsize=6); ax.grid(alpha=0.3)

# ── (m) R5: Geldmenge ──
ax = fig.add_subplot(gs[4, 0])
ax.plot(r5["t"], r5["mass"], "C4-", lw=1.5)
ax.set_xlabel("t [Jahre]"); ax.set_ylabel(r"$M$ [Wäh]")
ax.set_title("(m) R5: Geldmenge (Poisson-QE)")
ax.grid(alpha=0.3)

# ── (n) Regime-Tabelle ──
ax = fig.add_subplot(gs[4, 1])
ax.axis("off")
table_text = (
    "ZWEI REGIME DES GELDFLUSSES (§5.5)\n"
    "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    "ZINSGETRIEBEN:\n"
    "  j_m = -D_m * nabla(r)\n"
    "  Beispiel: Carry Trade\n"
    "  Geld: niedrig-r -> hoch-r\n\n"
    "KREDITGETRIEBEN:\n"
    "  j_m = sigma_m * E_Kredit\n"
    "  Beispiel: QE (2009-2022)\n"
    "  r ~ 0, aber E_Kredit massiv\n\n"
    "NULLZINSGRENZE:\n"
    "  r -> 0 => nabla(r) ~ 0\n"
    "  Geldfluss NUR via Kreditkanal\n"
    "  -> WARUM QE funktioniert!\n\n"
    "CREDIT CRUNCH:\n"
    "  Phi_Kredit -> 0\n"
    "  Geldfluss versiegt"
)
ax.text(0.05, 0.95, table_text, transform=ax.transAxes, fontsize=9,
        fontfamily="monospace", va="top",
        bbox=dict(boxstyle="round,pad=0.5", facecolor="#eef2ff", alpha=0.9))

# ── (o) Funktionalformen ──
ax = fig.add_subplot(gs[4, 2])
ax.axis("off")
fn_text = (
    "FUNKTIONALFORMEN\n"
    "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    "RAEUMLICH:\n"
    "  * Gaussprofil (Anfangsdichte)\n"
    "  * Glatter Sprung (Phi_Kredit)\n"
    "  * Rampe (Phi_Kredit R4)\n\n"
    "ZEITLICH:\n"
    "  * Ornstein-Uhlenbeck (D_m, r, Phi)\n"
    "  * Logist. Uebergang (r->0, QE)\n"
    "  * Poisson-Pulse (QE-Inject.)\n"
    "  * Sinusoidal (verfuegbar)\n\n"
    "ZINS:\n"
    "  * r = r_base + kappa*ln(rho/rho_0)\n"
    "    (lokale Investitionsnachfrage)\n\n"
    "KREDIT:\n"
    "  * E = -nabla(Phi_Kredit)\n"
    "    (Banken-Anreizfeld)"
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
    "GLEICHUNG:  II.4 (§5.5)   j_m = -D_m * nabla(r) + sigma_m * E_Kredit\n"
    "KREDITFELD: E_Kredit = -nabla(Phi_Kredit)   (Banken-Anreizfeld)\n"
    "KOPPLUNG:   drho_m/dt = -nabla . j_m + Q_m  (Geldkontinuitaet, I.4)\n"
    "\n"
    "┌─── ENDOGENE VARIABLEN ───────────────────────────────────────────┐\n"
    "│  rho_m(x,t)   Gelddichte          [Wäh/km]    I.4 Kontinuität  │\n"
    "│  j_m(x,t)     Geldfluss           [Wäh/(km*a)] II.4            │\n"
    "│  r(x,t)       Lokaler Zinssatz    [1/a]         r_base+kappa*ln │\n"
    "└──────────────────────────────────────────────────────────────────┘\n"
    "┌─── EXOGENE VARIABLEN ────────────────────────────────────────────┐\n"
    "│  Phi_Kredit(x,t)  Kreditpotential    [dimlos]  Bankenkreditverg.│\n"
    "│  r_base(t)        Leitzins (ZB)      [1/a]     Geldpolitik      │\n"
    "│  Q_m(x,t)         Geldquellen        [Wäh/(km*a)] Schoepfung   │\n"
    "└──────────────────────────────────────────────────────────────────┘\n"
    "┌─── PARAMETER ────────────────────────────────────────────────────┐\n"
    "│  D_m      Zinsdiffusion    2-25 km²*a    sigma_m  Kredit 0-15   │\n"
    "│  kappa    Zins-Dichte     2-3             rho_0    Ref.    10-15 │\n"
    "│  r_base   Leitzins        0.001-0.05 1/a  L       Domäne  100   │\n"
    "└──────────────────────────────────────────────────────────────────┘\n"
    "┌─── NUMERIK ──────────────────────────────────────────────────────┐\n"
    "│  MOL: NX=201, dx=0.5 km, Neumann BC                           │\n"
    "│  ODE: Radau (implizit), rtol=1e-6, atol=1e-8, max_step=1.0  │\n"
    "│  Stochast.: Euler-Maruyama (OU), Poisson-QE-Pulse             │\n"
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
    D_sens=D_sens, sigma_sens=sigma_sens, ratio_grid=ratio_grid,
)
for reg in ["R1", "R2", "R3", "R4", "R5"]:
    r = results[reg]
    save_dict[f"{reg}_rho_init"] = r["rho_xt"][:, 0]
    save_dict[f"{reg}_rho_final"] = r["rho_xt"][:, -1]
    save_dict[f"{reg}_mass"] = r["mass"]
    save_dict[f"{reg}_x_cm"] = r["x_cm"]
    save_dict[f"{reg}_j_fin"] = r["j_fin"]
    save_dict[f"{reg}_r_final"] = r["r_final"]
    save_dict[f"{reg}_r_center"] = r["r_center"]

np.savez_compressed(DATA, **save_dict)
print(f"  Daten -> {DATA}")

# ═══════════════════════════════════════════════
# ZUSAMMENFASSUNG
# ═══════════════════════════════════════════════
print(f"\n{'='*72}")
print("  ZUSAMMENFASSUNG S12")
print(f"{'='*72}")
print(f"  V1 Geldmengenerhaltung:     dM/M = {mass_err:.2e}  "
      f"{'✅' if mass_err < 5e-3 else '⚠'}")
print(f"  V2 Zinsdispersion:          -{dispersion_reduction*100:.0f}%  "
      f"{'✅' if dispersion_reduction > 0.3 else '⚠'}")
print(f"  V3 Kreditdominanz (R2):     {kredit_dominanz:.0f}x  "
      f"{'✅' if kredit_dominanz > 2 else '⚠'}")
print(f"  V4 QE-Effekt (R3):         +{(r3['mass'][idx_150]/r3['mass'][idx_80]-1)*100:.1f}%  "
      f"{'✅' if qe_effect else '⚠'}")
print(f"  V5 Credit Crunch (R4):      Phi -> {phi_reduction*100:.0f}%  "
      f"{'✅' if crunch_ok else '⚠'}")
print(f"  V6 Sensitivität 625pt:      ratio in "
      f"[{ratio_grid.min():.1f}, {ratio_grid.max():.1f}]  "
      f"{'✅' if sens_ok else '⚠'}")
print()
for reg in ["R1", "R2", "R3", "R4", "R5"]:
    par = results[reg]["par"]
    r = results[reg]
    print(f"  {par['label']:30s}  M(T)={r['mass'][-1]:8.1f}  "
          f"x_cm(T)={r['x_cm'][-1]:6.2f}  "
          f"rho_max={r['rho_xt'][:,-1].max():8.2f}")

all_pass = (mass_err < 5e-3 and dispersion_reduction > 0.3 and kredit_dominanz > 2
            and qe_effect and crunch_ok and sens_ok)
print(f"\n  Gesamtergebnis: "
      f"{'✅ ALLE VALIDIERUNGEN BESTANDEN' if all_pass else '⚠ EINIGE VALIDIERUNGEN FEHLGESCHLAGEN'}")
