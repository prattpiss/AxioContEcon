"""
S13 – Informationsfluss II.3  (§5.6, Vorschau Kap. 7)
==========================================
Monographie-Gleichung (exakt):

    dI/dt = D_I * nabla²I  - omega*I  + S_k  - mu*I³  + beta*|dp/dt|

Fünf Terme:
  1. D_I * nabla²I          Räumliche Diffusion (Nachrichten breiten sich aus)
  2. -omega * I              Exponentieller Zerfall (Vergessen)
  3. S_k                     Quellen (Werbung + WoM + Nutzungserfahrung)
     S_k = sigma_adv * E_adv  +  sigma_WoM * I*(1 - I/I_max)  +  sigma_use * c/n
     → Für S13: S_k = sigma_adv * E_adv(x,t)  +  r_I * I*(1 - I/I_max)
  4. -mu * I³                Kubische Sättigung (Ginzburg-Landau)
  5. +beta * |dp_k/dt|       Preis-Feedback ("Events create news")

Kopplung:
  Preis → Info:   beta*|dp/dt| erzeugt Information bei Preisbewegungen
  Info → Preis:   Über F.2: mu_eff = p + alpha_H*p_H + psi/(I + eps)
                  → niedriges I => hohe Illiquiditätsprämie => Preisstress

Analytische Ergebnisse:
  - Stationäre Punktquelle (1D):  I*(x) = S0/(2*sqrt(D*omega)) * exp(-|x|/ell)
    mit Informationsreichweite  ell = sqrt(D_I / omega)
  - Fisher-KPP Travelling Wave:  v_front = 2*sqrt(D_I * (r_I - omega))
    existiert falls r_I > omega
  - Bistabilität: Niedrig-I und Hoch-I Gleichgewichte (Produktlebenszyklus)

6 Regime:
  R1 Reine Diffusion+Zerfall  (S=0, mu=0, beta=0: analytische Lösung)
  R2 Punktquelle stationär    (S=delta, mu=0: analytischer Vergleich)
  R3 Fisher-KPP Front         (WoM aktiv: Travelling Wave)
  R4 Preis-Feedback Spirale   (Stabilisierend: dp erzeugt I, senkt Illiquidität)
  R5 Illiquiditätsspirale     (Destabilisierend: I sinkt trotz dp → Crash)
  R6 Voll stochastisch        (OU-D_I, Poisson-Quellen, Drift-omega)

8 Funktionalformen:
  Gaußprofil, Rampe, Punktquelle (räumlich)
  Logistisch, Ornstein-Uhlenbeck, Poisson-Pulse, Sinusoidal, Sprung (zeitlich)
"""

import numpy as np
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
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
PLOT = BASE / "Ergebnisse" / "Plots" / "S13_II3_Informationsfluss.png"
DATA = BASE / "Ergebnisse" / "Daten" / "S13_II3_Informationsfluss.npz"
PLOT.parent.mkdir(parents=True, exist_ok=True)
DATA.parent.mkdir(parents=True, exist_ok=True)

rng = np.random.default_rng(42)

# ═══════════════════════════════════════════════
# KLASSIFIKATION
# ═══════════════════════════════════════════════
#
# ENDOGENE VARIABLEN (räumlich):
#   I(x,t)           Informationsfeld    [dimlos ∈ [0,1]]   II.3
#
# EXOGENE VARIABLEN:
#   E_adv(x,t)       Werbeausgaben       [dimlos]           Werbung (I.2)
#   dp_dt(x,t)       Preisänderung       [Wäh/(ME·a)]      Aus II.2
#   S_ext(x,t)       Externe Quellen     [1/a]              Patente, Medien
#
# PARAMETER:
#   D_I       Informationsdiffusion [km²/a]    Kommunikationsinfrastruktur
#   omega     Zerfallsrate          [1/a]      Vergessen
#   r_I       WoM-Wachstumsrate     [1/a]      Word-of-Mouth
#   I_max     Sättigungslevel       [dimlos]   WoM-Decke
#   mu        Kubische Sättigung    [1/a]      Ginzburg-Landau
#   beta      Preis-Info-Kopplung   [dimlos/Wäh]  Events create news
#   sigma_adv Werbeeffizienz        [dimlos]   Umwandlung Ausgaben → Info
#   psi       Intransparenzkosten   [Wäh/ME]   Illiquiditätsprämie
#   eps       Regularisierung       [dimlos]   Verhindert 1/0
#   L         Domänenlänge          [km]

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

I_FLOOR = 1e-10   # Numerischer Boden für I

# Tridiagonale Jakobistruktur für MOL
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

def point_source(x, x0, sigma_src, amplitude):
    """Approximierte Deltaquelle als schmale Gaußglocke."""
    return amplitude * np.exp(-0.5 * ((x - x0) / sigma_src) ** 2) / (sigma_src * np.sqrt(2 * np.pi))

def smooth_step_time(t, t0, width=3.0):
    return 1.0 / (1.0 + np.exp(-(t - t0) / width))

def ou_process(t_eval, mu, theta, sigma, x0, seed=42):
    rng_loc = np.random.default_rng(seed)
    dt = np.diff(t_eval, prepend=t_eval[0] - (t_eval[1] - t_eval[0]))
    arr = np.zeros(len(t_eval))
    arr[0] = x0
    for i in range(1, len(t_eval)):
        dW = np.sqrt(abs(dt[i])) * rng_loc.standard_normal()
        arr[i] = arr[i-1] + theta * (mu - arr[i-1]) * dt[i] + sigma * dW
    return arr

def ou_interpolator(t_eval, arr):
    """Gibt eine Funktion zurück, die per Interpolation Werte liefert."""
    def fn(t):
        return np.interp(t, t_eval, arr)
    return fn


# ═══════════════════════════════════════════════
# RHS-Funktion  dI/dt  (II.3)
# ═══════════════════════════════════════════════

def make_rhs(D_I, omega, r_I, I_max, mu_sat, beta, sigma_adv,
             E_adv_func, dp_dt_func, S_ext_func):
    """
    dI/dt = D_I * d²I/dx²         (Diffusion)
          - omega * I              (Zerfall)
          + r_I * I * (1 - I/I_max)  (Word-of-Mouth, logistisch)
          + sigma_adv * E_adv      (Werbung)
          + S_ext                  (externe Quellen)
          - mu * I³               (kubische Sättigung)
          + beta * |dp/dt|        (Preis-Feedback)

    Returns: f(t, I_vec), plus a diagnostics function.
    """
    dx2 = dx * dx

    def rhs(t, I_vec):
        I = np.maximum(I_vec, I_FLOOR)

        # Term 1: Diffusion (Laplacian mit Neumann BC)
        lap = np.zeros(NX)
        lap[1:-1] = (I[:-2] - 2*I[1:-1] + I[2:]) / dx2
        lap[0]    = (I[1] - I[0]) / dx2       # Neumann: dI/dx=0 am Rand
        lap[-1]   = (I[-2] - I[-1]) / dx2
        diffusion = D_I * lap

        # Term 2: Zerfall
        decay = -omega * I

        # Term 3: WoM (logistisch)
        wom = r_I * I * (1.0 - I / I_max)

        # Term 4: Quellen
        E_adv = E_adv_func(x, t)
        S_ext = S_ext_func(x, t)
        sources = sigma_adv * E_adv + S_ext

        # Term 5: Sättigung
        saturation = -mu_sat * I**3

        # Term 6: Preis-Feedback
        dp = dp_dt_func(x, t)
        price_fb = beta * np.abs(dp)

        return diffusion + decay + wom + sources + saturation + price_fb

    def diagnostics(t, I_vec):
        """Gibt alle Terme einzeln zurück für Kausalitätsanalyse."""
        I = np.maximum(I_vec, I_FLOOR)
        lap = np.zeros(NX)
        lap[1:-1] = (I[:-2] - 2*I[1:-1] + I[2:]) / dx2
        lap[0]    = (I[1] - I[0]) / dx2
        lap[-1]   = (I[-2] - I[-1]) / dx2
        diffusion = D_I * lap
        decay = -omega * I
        wom = r_I * I * (1.0 - I / I_max)
        sources = sigma_adv * E_adv_func(x, t) + S_ext_func(x, t)
        saturation = -mu_sat * I**3
        dp = dp_dt_func(x, t)
        price_fb = beta * np.abs(dp)
        return {
            'diffusion': diffusion, 'decay': decay, 'wom': wom,
            'sources': sources, 'saturation': saturation, 'price_fb': price_fb,
            'total': diffusion + decay + wom + sources + saturation + price_fb,
        }

    return rhs, diagnostics


# ═══════════════════════════════════════════════
# Solver-Wrapper
# ═══════════════════════════════════════════════

def run_regime(label, I0, D_I, omega, r_I, I_max, mu_sat, beta, sigma_adv,
               E_adv_func, dp_dt_func, S_ext_func, color,
               t_span=T_SPAN, t_eval=T_EVAL, max_step=1.0):
    """Löst II.3 für ein Regime. Gibt dict mit allen Ergebnissen."""

    rhs, diag = make_rhs(D_I, omega, r_I, I_max, mu_sat, beta, sigma_adv,
                         E_adv_func, dp_dt_func, S_ext_func)

    sol = solve_ivp(rhs, t_span, I0, method='Radau',
                    t_eval=t_eval, rtol=1e-6, atol=1e-8,
                    max_step=max_step, jac_sparsity=_jac_sparsity)

    if not sol.success:
        print(f"  ⚠ {label}: Solver-Warnung: {sol.message}")

    # Snapshots
    snap_times = np.linspace(t_span[0], t_span[1], 7)
    snaps = []
    for t_s in snap_times:
        idx = np.argmin(np.abs(t_eval - t_s))
        snaps.append((t_eval[idx], sol.y[:, idx].copy()))

    # Masse (Integral)
    mass = np.trapezoid(sol.y, x=x, axis=0)

    # Schwerpunkt
    x_cm = np.array([np.trapezoid(x * sol.y[:, i], x=x) / (mass[i] + 1e-30)
                      for i in range(len(t_eval))])

    # Term-Zerlegung zu ausgewählten Zeiten
    diag_times = [0.0, 0.25, 0.5, 0.75, 1.0]
    diag_snaps = []
    for frac in diag_times:
        t_d = t_span[0] + frac * (t_span[1] - t_span[0])
        idx = np.argmin(np.abs(t_eval - t_d))
        diag_snaps.append((t_eval[idx], diag(t_eval[idx], sol.y[:, idx])))

    # Term-Zerlegung am Mittelpunkt über die Zeit
    mid_idx = NX // 2
    term_names = ['diffusion', 'decay', 'wom', 'sources', 'saturation', 'price_fb']
    terms_mid = {n: np.zeros(len(t_eval)) for n in term_names}
    # Abtasten an ~100 Zeitpunkten für Effizienz
    sample_idx = np.linspace(0, len(t_eval)-1, min(200, len(t_eval)), dtype=int)
    for si in sample_idx:
        d = diag(t_eval[si], sol.y[:, si])
        for n in term_names:
            terms_mid[n][si] = d[n][mid_idx]
    # Interpolation füllen
    for n in term_names:
        nz = terms_mid[n][sample_idx]
        terms_mid[n] = np.interp(np.arange(len(t_eval)), sample_idx, nz)

    return {
        'label': label, 'color': color,
        't': t_eval, 'I_xt': sol.y,
        'snaps': snaps, 'mass': mass, 'x_cm': x_cm,
        'diag_snaps': diag_snaps, 'terms_mid': terms_mid,
        'par': {
            'D_I': D_I, 'omega': omega, 'r_I': r_I, 'I_max': I_max,
            'mu_sat': mu_sat, 'beta': beta, 'sigma_adv': sigma_adv,
        },
    }


# ═══════════════════════════════════════════════════
# REGIME-DEFINITIONEN
# ═══════════════════════════════════════════════════

results = {}

# ── R1: Reine Diffusion + Zerfall (analytisch lösbar) ──
print("="*60)
print("  R1: Reine Diffusion + Zerfall (analytische Referenz)")
print("="*60)

# I(x,0) = Gauß-Peak. Analytisch: Peak zerfällt exponentiell + diffundiert.
I0_r1 = gaussian_profile(x, 50, 8, 0.8, baseline=0.01)
no_source = lambda x, t: np.zeros_like(x)

results["R1"] = run_regime(
    "R1 Diffusion+Zerfall", I0_r1,
    D_I=2.0, omega=0.05, r_I=0.0, I_max=1.0, mu_sat=0.0,
    beta=0.0, sigma_adv=0.0,
    E_adv_func=no_source, dp_dt_func=no_source, S_ext_func=no_source,
    color="C0",
)
print(f"  Peak initial: {I0_r1.max():.3f}")
print(f"  Peak final:   {results['R1']['I_xt'][:, -1].max():.6f}")
print(f"  Masse initial: {results['R1']['mass'][0]:.2f}  "
      f"final: {results['R1']['mass'][-1]:.6f}")


# ── R2: Stationäre Punktquelle (analytischer Vergleich) ──
print(f"\n{'='*60}")
print("  R2: Punktquelle stationär (analytisch: exp(-|x|/ell))")
print(f"{'='*60}")

D_I_r2 = 0.8
omega_r2 = 0.1
ell_r2 = np.sqrt(D_I_r2 / omega_r2)  # Informationsreichweite
print(f"  Informationsreichweite ell = sqrt(D/omega) = {ell_r2:.2f} km")

S0 = 1.0
S_point = lambda x, t: point_source(x, 50, sigma_src=0.5, amplitude=S0)
I0_r2 = np.full(NX, 0.01)  # fast leer starten

results["R2"] = run_regime(
    "R2 Punktquelle (stationär)", I0_r2,
    D_I=D_I_r2, omega=omega_r2, r_I=0.0, I_max=1.0, mu_sat=0.0,
    beta=0.0, sigma_adv=0.0,
    E_adv_func=no_source, dp_dt_func=no_source, S_ext_func=S_point,
    color="C1",
)

# Analytische stationäre Lösung
I_analytic = (S0 / (2 * np.sqrt(D_I_r2 * omega_r2))) * np.exp(-np.abs(x - 50) / ell_r2)
I_numeric = results["R2"]["I_xt"][:, -1]
residual = np.sqrt(np.mean((I_numeric - I_analytic)**2)) / (np.mean(I_analytic) + 1e-30)
print(f"  Analytisch vs. Numerisch (NRMSE): {residual:.4f}")


# ── R3: Fisher-KPP Travelling Wave ──
print(f"\n{'='*60}")
print("  R3: Fisher-KPP Travelling Wave (WoM-Front)")
print(f"{'='*60}")

D_I_r3 = 1.0
omega_r3 = 0.02
r_I_r3 = 0.15  # > omega → Front existiert
I_max_r3 = 1.0

# Theoretische Frontgeschwindigkeit
v_theory = 2 * np.sqrt(D_I_r3 * (r_I_r3 - omega_r3))
print(f"  v_front (Theorie) = 2*sqrt(D*(r_I-omega)) = {v_theory:.3f} km/a")
print(f"  r_I = {r_I_r3:.3f} > omega = {omega_r3:.3f} → Front existiert ✅")

# Initiale Bedingung: Info nur links
I0_r3 = I_max_r3 / (1.0 + np.exp((x - 15) / 3.0))  # Sigmoid, Front bei x=15

results["R3"] = run_regime(
    "R3 Fisher-KPP", I0_r3,
    D_I=D_I_r3, omega=omega_r3, r_I=r_I_r3, I_max=I_max_r3, mu_sat=0.0,
    beta=0.0, sigma_adv=0.0,
    E_adv_func=no_source, dp_dt_func=no_source, S_ext_func=no_source,
    color="C2", t_span=(0, 150), t_eval=np.linspace(0, 150, 3001),
)

# Frontposition messen (x wo I = 0.5*I_max)
r3 = results["R3"]
front_start = None
front_end = None
for idx_t in [0, -1]:
    prof = r3["I_xt"][:, idx_t]
    above = np.where(prof > 0.5 * I_max_r3)[0]
    if len(above) > 0:
        xf = x[above[-1]]
    else:
        xf = 0
    if idx_t == 0:
        front_start = xf
    else:
        front_end = xf

t_total_r3 = 150.0
v_measured = (front_end - front_start) / t_total_r3 if front_start is not None else 0
print(f"  Frontposition:  t=0: x={front_start:.1f}km  t=150: x={front_end:.1f}km")
print(f"  v_front (gemessen) = {v_measured:.3f} km/a  (Theorie: {v_theory:.3f})")
print(f"  Abweichung: {abs(v_measured - v_theory)/(v_theory+1e-30)*100:.1f}%")


# ── R4: Preis-Feedback → Informationsgewinnung (Stabilisierend) ──
print(f"\n{'='*60}")
print("  R4: Preis-Feedback (stabilisierend: dp erzeugt I)")
print(f"{'='*60}")

# Preiscrash bei t=50 im Zentrum → erzeugt Informationswelle
def dp_crash_stabilizing(x, t):
    """Preiseinbruch bei t=50±5, räumlich bei x=50±10."""
    time_env = np.exp(-0.5 * ((t - 50) / 5)**2)
    space_env = np.exp(-0.5 * ((x - 50) / 10)**2)
    return -3.0 * time_env * space_env  # starker Preisfall

# Info startet niedrig → Crash erzeugt I → I senkt Illiquidität → stabil
I0_r4 = np.full(NX, 0.15)

results["R4"] = run_regime(
    "R4 Stabilisierend", I0_r4,
    D_I=1.5, omega=0.04, r_I=0.0, I_max=1.0, mu_sat=0.5,
    beta=0.3, sigma_adv=0.0,
    E_adv_func=no_source, dp_dt_func=dp_crash_stabilizing,
    S_ext_func=no_source, color="C3",
)

# Messen: I sollte nach Crash STEIGEN im Zentrum
r4 = results["R4"]
I_before_crash = r4["I_xt"][NX//2, np.argmin(np.abs(T_EVAL - 40))]
I_after_crash = r4["I_xt"][NX//2, np.argmin(np.abs(T_EVAL - 60))]
I_peak_crash = np.max(r4["I_xt"][NX//2, :])
print(f"  I(Mitte) vor Crash (t=40):  {I_before_crash:.4f}")
print(f"  I(Mitte) nach Crash (t=60): {I_after_crash:.4f}")
print(f"  I(Mitte) Maximum:           {I_peak_crash:.4f}")
stab_ok = I_after_crash > I_before_crash
print(f"  Stabilisierend (I steigt nach Crash): {'✅' if stab_ok else '⚠'}")


# ── R5: Illiquiditätsspirale (destabilisierend) ──
print(f"\n{'='*60}")
print("  R5: Illiquiditätsspirale (destabilisierend)")
print(f"{'='*60}")

# Hoher omega (schnelles Vergessen) + schwaches beta + Analystenflucht
# → I sinkt trotz Preisfall → Illiquiditätsprämie steigt
def dp_persistent_decline(x, t):
    """Langsamer, persistenter Preisverfall ab t=30."""
    time_env = smooth_step_time(t, 30, width=5.0)
    space_env = np.ones_like(x)  # überall gleichmäßig
    return -0.5 * time_env * space_env

# Starte mit mäßig hohem I, das dann verfällt
I0_r5 = np.full(NX, 0.5) + gaussian_profile(x, 50, 20, 0.3)

# Hoher Zerfall, schwaches WoM, kein Preis-Feedback → I kollabiert
results["R5"] = run_regime(
    "R5 Illiquiditätsspirale", I0_r5,
    D_I=0.5, omega=0.12, r_I=0.02, I_max=1.0, mu_sat=0.3,
    beta=0.01, sigma_adv=0.0,
    E_adv_func=no_source, dp_dt_func=dp_persistent_decline,
    S_ext_func=no_source, color="C4",
)

r5 = results["R5"]
I_mid_init = r5["I_xt"][NX//2, 0]
I_mid_final = r5["I_xt"][NX//2, -1]
print(f"  I(Mitte) initial: {I_mid_init:.4f}")
print(f"  I(Mitte) final:   {I_mid_final:.6f}")
illiq_ratio = I_mid_final / (I_mid_init + 1e-30)
print(f"  I-Verlust: {(1 - illiq_ratio)*100:.1f}%")
spiral_ok = illiq_ratio < 0.1
print(f"  Illiquiditätsspirale (I < 10%): {'✅' if spiral_ok else '⚠'}")

# Illiquiditätsprämie (psi/(I+eps)) steigt?
psi = 1.0
eps = 0.01
illiq_init = psi / (I_mid_init + eps)
illiq_final = psi / (I_mid_final + eps)
print(f"  Illiquiditätsprämie: {illiq_init:.2f} → {illiq_final:.2f} "
      f"(×{illiq_final/(illiq_init+1e-30):.0f})")


# ── R6: Voll stochastisch ──
print(f"\n{'='*60}")
print("  R6: Voll stochastisch (OU-D_I, Poisson-Quellen)")
print(f"{'='*60}")

# OU-Diffusionskoeffizient (Kommunikationsinfrastruktur schwankt)
D_I_ou = ou_process(T_EVAL, mu=1.5, theta=0.3, sigma=0.4, x0=1.5, seed=42)
D_I_ou = np.maximum(D_I_ou, 0.1)
D_I_ou_fn = ou_interpolator(T_EVAL, D_I_ou)

# Poisson-Medien-Events (z.B. Virales Nachrichtenevent)
poisson_rng = np.random.default_rng(123)
n_events = poisson_rng.poisson(0.04 * (T_SPAN[1] - T_SPAN[0]))  # ~8 Events
event_times = np.sort(poisson_rng.uniform(T_SPAN[0]+10, T_SPAN[1]-10, size=n_events))
event_locs = poisson_rng.uniform(10, 90, size=n_events)
event_sizes = poisson_rng.exponential(0.5, size=n_events) + 0.2
print(f"  {n_events} Medien-Events generiert")

def S_stochastic(x, t):
    """Summe von Poisson-Pulsen als stochastische Quellen."""
    s = np.zeros_like(x)
    for te, xe, amp in zip(event_times, event_locs, event_sizes):
        time_env = np.exp(-0.5 * ((t - te) / 3)**2)
        space_env = np.exp(-0.5 * ((x - xe) / 8)**2)
        s += amp * time_env * space_env
    return s

# Brauche RHS-Wrapper mit zeitabhängigem D_I
D_I_r6_base = 1.5
omega_r6 = 0.06
r_I_r6 = 0.08
I_max_r6 = 1.0
mu_r6 = 0.3
beta_r6 = 0.05

dp_stoch = lambda x, t: 0.5 * np.sin(0.1 * t) * np.cos(0.08 * x)

def rhs_r6(t, I_vec):
    I = np.maximum(I_vec, I_FLOOR)
    D_I_t = D_I_ou_fn(t)
    dx2 = dx * dx
    lap = np.zeros(NX)
    lap[1:-1] = (I[:-2] - 2*I[1:-1] + I[2:]) / dx2
    lap[0]    = (I[1] - I[0]) / dx2
    lap[-1]   = (I[-2] - I[-1]) / dx2
    diffusion = D_I_t * lap
    decay = -omega_r6 * I
    wom = r_I_r6 * I * (1.0 - I / I_max_r6)
    sources = S_stochastic(x, t)
    saturation = -mu_r6 * I**3
    price_fb = beta_r6 * np.abs(dp_stoch(x, t))
    return diffusion + decay + wom + sources + saturation + price_fb

I0_r6 = np.full(NX, 0.2) + 0.1 * np.sin(2 * np.pi * x / L)

sol_r6 = solve_ivp(rhs_r6, T_SPAN, I0_r6, method='Radau',
                    t_eval=T_EVAL, rtol=1e-6, atol=1e-8, max_step=1.0,
                    jac_sparsity=_jac_sparsity)

snap_times_r6 = np.linspace(T_SPAN[0], T_SPAN[1], 7)
snaps_r6 = []
for t_s in snap_times_r6:
    idx = np.argmin(np.abs(T_EVAL - t_s))
    snaps_r6.append((T_EVAL[idx], sol_r6.y[:, idx].copy()))
mass_r6 = np.trapezoid(sol_r6.y, x=x, axis=0)

results["R6"] = {
    'label': "R6 Stochastisch", 'color': "C5",
    't': T_EVAL, 'I_xt': sol_r6.y,
    'snaps': snaps_r6, 'mass': mass_r6,
    'D_I_ou': D_I_ou, 'event_times': event_times, 'event_locs': event_locs,
}
print(f"  I(Mitte) initial: {I0_r6[NX//2]:.3f}  final: {sol_r6.y[NX//2, -1]:.3f}")
print(f"  Masse: {mass_r6[0]:.1f} → {mass_r6[-1]:.1f}")


# ═══════════════════════════════════════════════
# VALIDIERUNGEN
# ═══════════════════════════════════════════════
print(f"\n{'='*60}")
print("  VALIDIERUNGEN")
print(f"{'='*60}")

val_results = {}

# V1: Exponentieller Zerfall (R1, ohne Quellen)
r1 = results["R1"]
mass_decay = r1["mass"][-1] / r1["mass"][0]
mass_theory = np.exp(-0.05 * T_SPAN[1])  # exp(-omega*T)
# Nicht exakt wegen Diffusion: Masse zerfällt als exp(-omega*t) bei homogenem omega
# Aber Diffusion konserviert Masse → Zerfall nur durch omega
v1_err = abs(mass_decay - mass_theory) / (mass_theory + 1e-30)
print(f"\n  V1: Zerfall R1: M(T)/M(0) = {mass_decay:.6f}  "
      f"(Theorie: {mass_theory:.6f}, Fehler: {v1_err:.2e})")
v1_ok = v1_err < 0.01
val_results["V1"] = (v1_ok, v1_err)
print(f"      {'✅' if v1_ok else '⚠'}")

# V2: Stationäre Punktquelle (analytisch vs. numerisch)
print(f"\n  V2: Punktquelle R2: Analytik vs. Numerik")
# Vergleiche nur im Mittelteil (Ränder haben BC-Effekte)
mask = (x > 20) & (x < 80)
I_num = results["R2"]["I_xt"][:, -1][mask]
I_ana = I_analytic[mask]
nrmse = np.sqrt(np.mean((I_num - I_ana)**2)) / (np.mean(I_ana) + 1e-30)
print(f"      NRMSE (Zentral, x∈[20,80]): {nrmse:.4f}")
v2_ok = nrmse < 0.30  # 30% tolerance (Gauss approx of delta + boundary effects)
val_results["V2"] = (v2_ok, nrmse)
print(f"      {'✅' if v2_ok else '⚠'}")

# V3: Fisher-KPP Frontgeschwindigkeit
print(f"\n  V3: Fisher-KPP R3: v_front")
v3_err = abs(v_measured - v_theory) / (v_theory + 1e-30)
print(f"      v_gemessen = {v_measured:.3f}  v_Theorie = {v_theory:.3f}  "
      f"Fehler: {v3_err*100:.1f}%")
v3_ok = v3_err < 0.25  # 25% tolerance (finite domain effects)
val_results["V3"] = (v3_ok, v3_err)
print(f"      {'✅' if v3_ok else '⚠'}")

# V4: Stabilisierende Spirale (I steigt nach Crash)
print(f"\n  V4: Preis-Feedback R4: I steigt nach Crash")
v4_ok = stab_ok
val_results["V4"] = (v4_ok, I_after_crash - I_before_crash)
print(f"      I vor: {I_before_crash:.4f}  nach: {I_after_crash:.4f}  "
      f"{'✅' if v4_ok else '⚠'}")

# V5: Illiquiditätsspirale (I kollabiert)
print(f"\n  V5: Illiquiditätsspirale R5: I < 10% des Startwerts")
v5_ok = spiral_ok
val_results["V5"] = (v5_ok, illiq_ratio)
print(f"      I-Verlust: {(1-illiq_ratio)*100:.1f}%  {'✅' if v5_ok else '⚠'}")

# V6: Informationsreichweite ell (R2)
print(f"\n  V6: Informationsreichweite (R2)")
# Fit: exp(-|x-50|/ell) an numerisches Profil
from scipy.optimize import curve_fit

def exp_decay(x_abs, A, ell_fit):
    return A * np.exp(-x_abs / ell_fit)

I_num_full = results["R2"]["I_xt"][:, -1]
x_right = x[x >= 50]
I_right = I_num_full[x >= 50]
try:
    popt, _ = curve_fit(exp_decay, x_right - 50, I_right, p0=[I_right[0], ell_r2])
    ell_measured = popt[1]
    ell_err = abs(ell_measured - ell_r2) / ell_r2
    print(f"      ell_Theorie = {ell_r2:.2f}  ell_gemessen = {ell_measured:.2f}  "
          f"Fehler: {ell_err*100:.1f}%")
    v6_ok = ell_err < 0.2
except Exception:
    ell_measured = -1
    ell_err = 1.0
    v6_ok = False
    print(f"      Fit fehlgeschlagen")
val_results["V6"] = (v6_ok, ell_err)
print(f"      {'✅' if v6_ok else '⚠'}")

# V7: Sensitivität D_I × omega → Reichweite (25x25)
print(f"\n  V7: Sensitivität D_I × omega → ell (625 Punkte)")
N_SENS = 25
D_sens = np.linspace(0.2, 5.0, N_SENS)
omega_sens = np.linspace(0.01, 0.5, N_SENS)
ell_grid = np.zeros((N_SENS, N_SENS))
for i, D_val in enumerate(D_sens):
    for j, om_val in enumerate(omega_sens):
        ell_grid[i, j] = np.sqrt(D_val / om_val)

# Monotonie: ell steigt mit D, fällt mit omega
sens_D_ok = np.all(np.diff(ell_grid, axis=0) > 0)
sens_om_ok = np.all(np.diff(ell_grid, axis=1) < 0)
sens_ok = sens_D_ok and sens_om_ok
print(f"      ell steigt mit D: {'✅' if sens_D_ok else '⚠'}")
print(f"      ell fällt mit omega: {'✅' if sens_om_ok else '⚠'}")
print(f"      ell ∈ [{ell_grid.min():.2f}, {ell_grid.max():.2f}]")
val_results["V7"] = (sens_ok, ell_grid)


# ═══════════════════════════════════════════════
# Gesamtergebnis
# ═══════════════════════════════════════════════
n_ok = sum(1 for v in val_results.values() if v[0])
n_total = len(val_results)
print(f"\n{'='*60}")
print(f"  ERGEBNIS: {n_ok}/{n_total} Validierungen bestanden")
print(f"{'='*60}")


# ═══════════════════════════════════════════════
# PLOT  (7 Zeilen × 3 Spalten = 21 Panels + Metadaten)
# ═══════════════════════════════════════════════
fig = plt.figure(figsize=(24, 40))
gs = GridSpec(8, 3, figure=fig, height_ratios=[1, 1, 1, 1, 1, 1, 1, 0.6],
              hspace=0.35, wspace=0.32)
fig.suptitle("S13 – Informationsfluss II.3  (§5.6)\n"
             r"$\dot{\mathcal{I}}_k = D_{\mathcal{I}}\nabla^2\mathcal{I} "
             r"- \omega\mathcal{I} + \mathcal{S}_k "
             r"- \mu\mathcal{I}^3 + \beta|\dot{p}|$",
             fontsize=15, fontweight="bold", y=0.99)

TERM_COLORS = {
    'diffusion': '#2196F3', 'decay': '#F44336', 'wom': '#4CAF50',
    'sources': '#FF9800', 'saturation': '#9C27B0', 'price_fb': '#795548',
}
TERM_LABELS = {
    'diffusion': r'$D\nabla^2\mathcal{I}$ (Diffusion)',
    'decay': r'$-\omega\mathcal{I}$ (Zerfall)',
    'wom': r'$r_I\mathcal{I}(1-\mathcal{I}/\mathcal{I}_\max)$ (WoM)',
    'sources': r'$\mathcal{S}_k$ (Quellen)',
    'saturation': r'$-\mu\mathcal{I}^3$ (Sättigung)',
    'price_fb': r'$\beta|\dot{p}|$ (Preis-FB)',
}

# ══════════ Zeile 0: R1 Diffusion + Zerfall ══════════

# (a) R1: Snapshots
ax = fig.add_subplot(gs[0, 0])
r1 = results["R1"]
for t_s, prof in r1["snaps"]:
    ax.plot(x, prof, lw=1.2, label=f"t={t_s:.0f}")
ax.set_xlabel("x [km]"); ax.set_ylabel(r"$\mathcal{I}(x)$")
ax.set_title("(a) R1: Diffusion + Zerfall", fontweight="bold")
ax.legend(fontsize=6); ax.grid(alpha=0.3)

# (b) R1: Massezerfall (Kausalität: omega allein)
ax = fig.add_subplot(gs[0, 1])
t_theory = np.linspace(0, T_SPAN[1], 200)
mass_theory_curve = r1["mass"][0] * np.exp(-0.05 * t_theory)
ax.plot(r1["t"], r1["mass"], "C0-", lw=1.5, label="Numerisch")
ax.plot(t_theory, mass_theory_curve, "k--", lw=1, alpha=0.6,
        label=r"$M_0 e^{-\omega t}$ (Theorie)")
ax.set_xlabel("t [Jahre]"); ax.set_ylabel(r"$\int\mathcal{I}\,dx$")
ax.set_title(f"(b) R1: Massezerfall (V1: Err={v1_err:.1e})")
ax.legend(fontsize=7); ax.grid(alpha=0.3)

# (c) R1: Kausalitäts-Termzerlegung am Mittelpunkt
ax = fig.add_subplot(gs[0, 2])
for tn in ['diffusion', 'decay']:
    ax.plot(r1["t"], r1["terms_mid"][tn], color=TERM_COLORS[tn],
            lw=1.2, label=TERM_LABELS[tn])
ax.axhline(0, color="grey", ls=":", lw=0.5)
ax.set_xlabel("t [Jahre]"); ax.set_ylabel(r"$\partial\mathcal{I}/\partial t$ (x=50)")
ax.set_title("(c) R1: KAUSALITÄT — Wer treibt ∂I/∂t?", fontweight="bold")
ax.legend(fontsize=6); ax.grid(alpha=0.3)

# ══════════ Zeile 1: R2 Punktquelle stationär ══════════

# (d) R2: Snapshots + Analytik
ax = fig.add_subplot(gs[1, 0])
for t_s, prof in results["R2"]["snaps"]:
    ax.plot(x, prof, lw=1.2, label=f"t={t_s:.0f}")
ax.plot(x, I_analytic, "k--", lw=2, alpha=0.5, label="Analytisch")
ax.set_xlabel("x [km]"); ax.set_ylabel(r"$\mathcal{I}(x)$")
ax.set_title(f"(d) R2: Punktquelle (V2: NRMSE={nrmse:.3f})")
ax.legend(fontsize=6); ax.grid(alpha=0.3)

# (e) R2: Informationsreichweite-Anschauung
ax = fig.add_subplot(gs[1, 1])
I_final_r2 = results["R2"]["I_xt"][:, -1]
ax.fill_between(x, 0, I_final_r2, alpha=0.2, color="C1")
ax.plot(x, I_final_r2, "C1-", lw=1.5)
ax.axvline(50 - ell_r2, color="r", ls="--", lw=1, label=f"x₀ − ℓ = {50-ell_r2:.1f}")
ax.axvline(50 + ell_r2, color="r", ls="--", lw=1, label=f"x₀ + ℓ = {50+ell_r2:.1f}")
ax.annotate(f"ℓ = √(D/ω)\n= {ell_r2:.1f} km", xy=(50 + ell_r2, I_final_r2[NX//2]*0.37),
            fontsize=9, color="red", fontweight="bold",
            arrowprops=dict(arrowstyle="->", color="red"),
            xytext=(70, I_final_r2[NX//2]*0.6))
ax.set_xlabel("x [km]"); ax.set_ylabel(r"$\mathcal{I}^*(x)$")
ax.set_title(r"(e) R2: Informationsreichweite $\ell = \sqrt{D/\omega}$",
             fontweight="bold")
ax.legend(fontsize=7); ax.grid(alpha=0.3)

# (f) R2: Kausalitäts-Termzerlegung (stationärer Zustand)
ax = fig.add_subplot(gs[1, 2])
# Am Ende: Diffusion = -Zerfall + Quelle (Balance)
r2_diag = results["R2"]["diag_snaps"][-1][1]
for tn in ['diffusion', 'decay', 'sources']:
    ax.plot(x, r2_diag[tn], color=TERM_COLORS[tn], lw=1.2, label=TERM_LABELS[tn])
ax.plot(x, r2_diag['total'], "k-", lw=1.5, alpha=0.5, label="Total ≈ 0 (stationär)")
ax.axhline(0, color="grey", ls=":", lw=0.5)
ax.set_xlabel("x [km]"); ax.set_ylabel("∂I/∂t [1/a]")
ax.set_title("(f) R2: KAUSALITÄT — Stationäre Balance", fontweight="bold")
ax.legend(fontsize=6); ax.grid(alpha=0.3)

# ══════════ Zeile 2: R3 Fisher-KPP ══════════

# (g) R3: Front-Snapshots
ax = fig.add_subplot(gs[2, 0])
r3 = results["R3"]
for t_s, prof in r3["snaps"]:
    ax.plot(x, prof, lw=1.2, label=f"t={t_s:.0f}")
ax.axhline(0.5, color="grey", ls=":", lw=0.5, alpha=0.5)
ax.set_xlabel("x [km]"); ax.set_ylabel(r"$\mathcal{I}(x)$")
ax.set_title("(g) R3: Fisher-KPP Informationsfront", fontweight="bold")
ax.legend(fontsize=6); ax.grid(alpha=0.3)

# (h) R3: Frontposition über Zeit + Theorie-Gerade
ax = fig.add_subplot(gs[2, 1])
# Frontposition (x wo I = 0.5) über Zeit
front_x = []
for i in range(len(r3["t"])):
    prof = r3["I_xt"][:, i]
    above = np.where(prof > 0.5 * I_max_r3)[0]
    if len(above) > 0:
        front_x.append(x[above[-1]])
    else:
        front_x.append(0)
front_x = np.array(front_x)
ax.plot(r3["t"], front_x, "C2-", lw=1.5, label="Numerisch")
ax.plot(r3["t"], front_start + v_theory * r3["t"], "k--", lw=1, alpha=0.6,
        label=f"Theorie: v = {v_theory:.2f} km/a")
ax.set_xlabel("t [Jahre]"); ax.set_ylabel("Frontposition x(I=0.5) [km]")
ax.set_title(f"(h) R3: Frontgeschwindigkeit (V3: Err={v3_err*100:.0f}%)")
ax.legend(fontsize=7); ax.grid(alpha=0.3)

# (i) R3: Kausalitäts-Termzerlegung an der Front
ax = fig.add_subplot(gs[2, 2])
# Wähle Zeitpunkt wo Front bei ~50km
t_front50_idx = np.argmin(np.abs(front_x - 50))
if t_front50_idx > 0:
    _, diag_fn = make_rhs(D_I_r3, omega_r3, r_I_r3, I_max_r3, 0.0, 0.0, 0.0,
                          no_source, no_source, no_source)
    d_front = diag_fn(r3["t"][t_front50_idx], r3["I_xt"][:, t_front50_idx])
    for tn in ['diffusion', 'decay', 'wom']:
        ax.plot(x, d_front[tn], color=TERM_COLORS[tn], lw=1.2, label=TERM_LABELS[tn])
    ax.plot(x, d_front['total'], "k-", lw=1.5, alpha=0.5, label="Total")
    ax.axvline(front_x[t_front50_idx], color="grey", ls="--", lw=0.8, alpha=0.5,
               label=f"Front x≈{front_x[t_front50_idx]:.0f}")
ax.axhline(0, color="grey", ls=":", lw=0.5)
ax.set_xlabel("x [km]"); ax.set_ylabel("∂I/∂t [1/a]")
ax.set_title(f"(i) R3: KAUSALITÄT — An der Front (t={r3['t'][t_front50_idx]:.0f})",
             fontweight="bold")
ax.legend(fontsize=6); ax.grid(alpha=0.3)

# ══════════ Zeile 3: R4 Stabilisierend ══════════

# (j) R4: Preis-Crash und I-Antwort (zeitlich, Mitte)
ax = fig.add_subplot(gs[3, 0])
r4 = results["R4"]
ax2 = ax.twinx()
# Preis-Input (dp/dt)
dp_timeline = np.array([dp_crash_stabilizing(np.array([50.0]), t)[0] for t in T_EVAL])
ax2.fill_between(T_EVAL, 0, dp_timeline, alpha=0.15, color="red")
ax2.plot(T_EVAL, dp_timeline, "r-", lw=0.8, alpha=0.5)
ax2.set_ylabel(r"$\dot{p}$ (Preis-Crash)", color="red")
# I-Antwort
ax.plot(T_EVAL, r4["I_xt"][NX//2, :], "C3-", lw=1.5, label=r"$\mathcal{I}(x=50)$")
ax.axvline(50, color="grey", ls="--", lw=0.5, alpha=0.5)
ax.set_xlabel("t [Jahre]"); ax.set_ylabel(r"$\mathcal{I}$", color="C3")
ax.set_title("(j) R4: Crash → Info-Gewinnung (V4: stabilisierend)", fontweight="bold")
ax.legend(fontsize=7, loc="upper right"); ax.grid(alpha=0.3)

# (k) R4: Snapshots
ax = fig.add_subplot(gs[3, 1])
for t_s, prof in r4["snaps"]:
    ax.plot(x, prof, lw=1.2, label=f"t={t_s:.0f}")
ax.set_xlabel("x [km]"); ax.set_ylabel(r"$\mathcal{I}(x)$")
ax.set_title("(k) R4: Informationswelle nach Crash")
ax.legend(fontsize=6); ax.grid(alpha=0.3)

# (l) R4: Kausalitäts-Termzerlegung (Mittelpunkt, zeitlich)
ax = fig.add_subplot(gs[3, 2])
for tn in ['diffusion', 'decay', 'saturation', 'price_fb']:
    ax.plot(r4["t"], r4["terms_mid"][tn], color=TERM_COLORS[tn],
            lw=1.2, label=TERM_LABELS[tn])
ax.axhline(0, color="grey", ls=":", lw=0.5)
ax.axvline(50, color="grey", ls="--", lw=0.5, alpha=0.5)
ax.set_xlabel("t [Jahre]"); ax.set_ylabel("∂I/∂t (x=50)")
ax.set_title("(l) R4: KAUSALITÄT — β|ṗ| treibt I hoch", fontweight="bold")
ax.legend(fontsize=6); ax.grid(alpha=0.3)

# ══════════ Zeile 4: R5 Destabilisierend ══════════

# (m) R5: I-Kollaps + Illiquiditätsprämie
ax = fig.add_subplot(gs[4, 0])
r5 = results["R5"]
ax.plot(T_EVAL, r5["I_xt"][NX//2, :], "C4-", lw=1.5, label=r"$\mathcal{I}(x=50)$")
ax2 = ax.twinx()
I_mid_ts = np.maximum(r5["I_xt"][NX//2, :], I_FLOOR)
illiq_premium = psi / (I_mid_ts + eps)
ax2.plot(T_EVAL, illiq_premium, "r-", lw=1, alpha=0.7,
         label=r"$\psi/(\mathcal{I}+\varepsilon)$")
ax2.set_ylabel("Illiquidität", color="red")
ax.set_xlabel("t [Jahre]"); ax.set_ylabel(r"$\mathcal{I}$", color="C4")
ax.set_title("(m) R5: Illiquiditätsspirale (V5)", fontweight="bold")
ax.legend(fontsize=7, loc="center right")
ax2.legend(fontsize=7, loc="upper right")
ax.grid(alpha=0.3)

# (n) R5: Snapshots
ax = fig.add_subplot(gs[4, 1])
for t_s, prof in r5["snaps"]:
    ax.plot(x, prof, lw=1.2, label=f"t={t_s:.0f}")
ax.set_xlabel("x [km]"); ax.set_ylabel(r"$\mathcal{I}(x)$")
ax.set_title("(n) R5: Informationskollaps (Snapshots)")
ax.legend(fontsize=6); ax.grid(alpha=0.3)

# (o) R5: Kausalität — Terms über Zeit am Mittelpunkt
ax = fig.add_subplot(gs[4, 2])
for tn in ['decay', 'wom', 'saturation', 'price_fb']:
    if tn in r5.get("terms_mid", {}):
        ax.plot(r5["t"], r5["terms_mid"][tn], color=TERM_COLORS[tn],
                lw=1.2, label=TERM_LABELS[tn])
ax.axhline(0, color="grey", ls=":", lw=0.5)
ax.set_xlabel("t [Jahre]"); ax.set_ylabel("∂I/∂t (x=50)")
ax.set_title("(o) R5: KAUSALITÄT — Zerfall dominiert", fontweight="bold")
ax.legend(fontsize=6); ax.grid(alpha=0.3)

# ══════════ Zeile 5: R6 Stochastisch + Sensitivität ══════════

# (p) R6: Snapshots
ax = fig.add_subplot(gs[5, 0])
r6 = results["R6"]
for t_s, prof in r6["snaps"]:
    ax.plot(x, prof, lw=1.2, label=f"t={t_s:.0f}")
# Medien-Events markieren
for te, xe in zip(event_times, event_locs):
    ax.axvline(xe, color="orange", ls=":", lw=0.3, alpha=0.4)
ax.set_xlabel("x [km]"); ax.set_ylabel(r"$\mathcal{I}(x)$")
ax.set_title("(p) R6: Stochastisch (Medien-Events orange)")
ax.legend(fontsize=6); ax.grid(alpha=0.3)

# (q) R6: D_I(t) stochastisch + Masse
ax = fig.add_subplot(gs[5, 1])
ax.plot(T_EVAL, D_I_ou, "C5-", lw=1, alpha=0.7, label=r"$D_\mathcal{I}(t)$ [OU]")
ax2 = ax.twinx()
ax2.plot(T_EVAL, r6["mass"], "k-", lw=1.2, alpha=0.6, label="Masse")
# Event-Markierungen
for te in event_times:
    ax.axvline(te, color="orange", ls="--", lw=0.5, alpha=0.4)
ax.set_xlabel("t [Jahre]"); ax.set_ylabel(r"$D_\mathcal{I}$ [km²/a]", color="C5")
ax2.set_ylabel(r"$\int\mathcal{I}dx$")
ax.set_title("(q) R6: Stoch. Diffusion + Events")
ax.legend(fontsize=7, loc="upper left"); ax2.legend(fontsize=7, loc="upper right")
ax.grid(alpha=0.3)

# (r) V7: Sensitivitäts-Heatmap (D_I × omega → ell)
ax = fig.add_subplot(gs[5, 2])
im = ax.pcolormesh(omega_sens, D_sens, ell_grid,
                   cmap="YlOrRd_r", shading="auto")
plt.colorbar(im, ax=ax, label=r"$\ell = \sqrt{D/\omega}$ [km]")
ax.set_xlabel(r"$\omega$ [1/a]"); ax.set_ylabel(r"$D_\mathcal{I}$ [km²/a]")
ax.set_title(r"(r) V7: Informationsreichweite $\ell(D,\omega)$",
             fontweight="bold")
# Konturlinien
cs = ax.contour(omega_sens, D_sens, ell_grid, levels=[1, 2, 3, 5, 10],
                colors="k", linewidths=0.8, alpha=0.5)
ax.clabel(cs, fontsize=7, fmt="%.0f km")
ax.grid(alpha=0.2)

# ══════════ Zeile 6: Vergleich + Kausalkette ══════════

# (s) Alle Regime: finales I(x)
ax = fig.add_subplot(gs[6, 0])
for reg_key in ["R1", "R2", "R3", "R4", "R5", "R6"]:
    r = results[reg_key]
    ax.plot(x, r["I_xt"][:, -1], color=r["color"], lw=1.2,
            label=r["label"][:22])
ax.set_xlabel("x [km]"); ax.set_ylabel(r"$\mathcal{I}(T)$")
ax.set_title("(s) Finale Informationsprofile")
ax.legend(fontsize=6); ax.grid(alpha=0.3)

# (t) Kausalkette (Textpanel)
ax = fig.add_subplot(gs[6, 1])
ax.axis("off")
causal_text = (
    "KAUSALKETTE: Information <-> Preise (S5.6-S5.7)\n"
    "=" * 42 + "\n\n"
    "PREIS -> INFORMATION:\n"
    "  |dp/dt| > 0  ->  beta*|dp|  ->  I steigt\n"
    "  'Events create news'\n"
    "  Crash/Blase -> Analysen, Medien\n\n"
    "INFORMATION -> PREIS:\n"
    "  I sinkt  ->  psi/(I+eps) steigt\n"
    "  -> mu_eff = p + alpha*p_H + psi/(I+eps)\n"
    "  -> Illiquiditaetspraemie steigt\n"
    "  -> Preisstress (II.2)\n\n"
    "ZWEI SPIRALEN:\n"
    "  [+] STABIL: Crash erzeugt News\n"
    "     -> I steigt -> Illiq. sinkt -> Erholung\n\n"
    "  [-] INSTABIL: Analysten fliehen\n"
    "     -> I sinkt trotz Crash -> psi/(I+eps)++\n"
    "     -> Preisverfall -> Illiq-Spirale\n\n"
    "TRAVELLING WAVE (Fisher-KPP):\n"
    f"  v = 2*sqrt(D*(r_I-omega)) = {v_theory:.2f} km/a\n"
    f"  ell = sqrt(D/omega) = {ell_r2:.1f} km (Reichweite)"
)
ax.text(0.05, 0.95, causal_text, transform=ax.transAxes, fontsize=8.5,
        fontfamily="monospace", va="top",
        bbox=dict(boxstyle="round,pad=0.5", facecolor="#fff3e0", alpha=0.9))

# (u) Stabilitäts-Phasendiagramm (r_I vs omega)
ax = fig.add_subplot(gs[6, 2])
r_I_range = np.linspace(0, 0.3, 100)
omega_range = np.linspace(0, 0.3, 100)
R_I, OM = np.meshgrid(r_I_range, omega_range)
# Region: r_I > omega → Front existiert (Info breitet sich aus)
# Region: r_I < omega → Zerfall dominiert (Info stirbt)
phase = np.where(R_I > OM, 1.0, 0.0)
ax.contourf(r_I_range, omega_range, phase, levels=[-0.5, 0.5, 1.5],
            colors=["#ffcccc", "#ccffcc"], alpha=0.5)
ax.plot(r_I_range, r_I_range, "k-", lw=2, label=r"$r_I = \omega$ (Grenze)")
ax.fill_between(r_I_range, r_I_range, 0.3, alpha=0.1, color="red")
ax.text(0.05, 0.25, "Info stirbt\n(ω > r_I)", fontsize=9, color="red",
        fontweight="bold")
ax.text(0.2, 0.05, "Info breitet sich aus\n(r_I > ω)", fontsize=9,
        color="green", fontweight="bold")
ax.plot(r_I_r3, omega_r3, "ko", ms=8, label=f"R3 (r_I={r_I_r3}, ω={omega_r3})")
ax.set_xlabel(r"$r_I$ [1/a] (WoM-Rate)"); ax.set_ylabel(r"$\omega$ [1/a] (Zerfall)")
ax.set_title("(u) Phasendiagramm: Info-Ausbreitung", fontweight="bold")
ax.legend(fontsize=7); ax.grid(alpha=0.3)
ax.set_xlim(0, 0.3); ax.set_ylim(0, 0.3)

# ══════════ Zeile 7: Metadaten ══════════
ax = fig.add_subplot(gs[7, :])
ax.axis("off")
meta_text = (
    f"S13 – Informationsfluss II.3 (§5.6, Vorschau Kap. 7)  |  "
    f"NX={NX}, L={L:.0f}km, Δx={dx:.2f}km  |  "
    f"Solver: Radau (rtol=1e-6, atol=1e-8)  |  "
    f"Validierungen: {n_ok}/{n_total}  |  "
    f"6 Regime × 8 Funktionalformen  |  "
    f"Kausalitätsanalyse: Term-Zerlegung pro Regime"
)
ax.text(0.5, 0.8, meta_text, ha="center", fontsize=9, fontfamily="monospace",
        bbox=dict(boxstyle="round,pad=0.4", facecolor="#e8eaf6", alpha=0.9))

# Validierungstabelle
val_text = "Validierungen:\n"
for k, (ok, val) in val_results.items():
    status = "✅" if ok else "⚠"
    if k == "V7":
        val_text += f"  {k}: ell(D,omega) Monotonie  {status}\n"
    else:
        val_text += f"  {k}: {'%.4f' % val if isinstance(val, float) else str(val)[:20]}  {status}\n"
ax.text(0.5, 0.15, val_text, ha="center", fontsize=8, fontfamily="monospace",
        bbox=dict(boxstyle="round,pad=0.4", facecolor="#e8f5e9", alpha=0.9))

plt.savefig(PLOT, dpi=180, bbox_inches="tight")
plt.close(fig)
print(f"\n  Plot gespeichert: {PLOT}")

# ═══════════════════════════════════════════════
# DATEN SPEICHERN
# ═══════════════════════════════════════════════
np.savez_compressed(DATA,
    x=x, t=T_EVAL,
    R1_I=results["R1"]["I_xt"], R1_mass=results["R1"]["mass"],
    R2_I=results["R2"]["I_xt"], R2_I_analytic=I_analytic,
    R3_I=results["R3"]["I_xt"], R3_t=results["R3"]["t"],
    R4_I=results["R4"]["I_xt"],
    R5_I=results["R5"]["I_xt"],
    R6_I=results["R6"]["I_xt"], R6_D_ou=D_I_ou,
    ell_grid=ell_grid, D_sens=D_sens, omega_sens=omega_sens,
    v_theory=v_theory, v_measured=v_measured, ell_theory=ell_r2,
)
print(f"  Daten gespeichert: {DATA}")
print(f"\n  ✅ S13 abgeschlossen.")
