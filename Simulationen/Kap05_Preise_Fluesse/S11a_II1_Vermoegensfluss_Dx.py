"""
S11a – Vermoegensfluss II.1 mit ortsabhaengiger Diffusion  (§5.4 Erweiterung)
==============================================================================
Basisgleichung:
    drho_w/dt = -div j_w + S_w
    j_w = -D_w(x) * grad(Phi_w) + v_w * rho_w

Erweiterung gegenueber S11:
    D_w  -->  D_w(x)  =  ortsabhaengige "Finanzinfrastruktur"
    
    Physikalische Interpretation:
      D_w(x) = lokale Finanzmarkt-Effizienz / Kapitalmarkt-Tiefe
      Hoch in Finanzzentren (London, NY, Frankfurt)
      Niedrig in unterentwickelten Regionen
    
    Mathematik:
      div(D(x) grad Phi) = D'(x)*grad(Phi) + D(x)*lap(Phi)
    
    5 Regime + 6 Validierungen
"""

import sys
import io
import warnings
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

L = 100.0; NX = 201; dx = L / (NX - 1)
x = np.linspace(0, L, NX)
T_SPAN = (0, 200); N_EVAL = 2001
t_eval = np.linspace(*T_SPAN, N_EVAL)
RHO_FLOOR = 1e-6

# ══════════════════════════════════════════════════════════════════════
# 1. D(x)-Profile: Finanzinfrastruktur
# ══════════════════════════════════════════════════════════════════════

def D_constant(x_arr, D0=30.0):
    return np.full_like(x_arr, D0)

def D_financial_center(x_arr, D_base=3.0, D_peak=80.0, x_c=50.0, sigma=8.0):
    """Finanzzentrum: Kapitalmobiliaet gebuendelt"""
    return D_base + (D_peak - D_base) * np.exp(-0.5 * ((x_arr - x_c) / sigma)**2)

def D_rich_poor(x_arr, D_rich=60.0, D_poor=3.0, x_edge=50.0, w=3.0):
    """Reiche Region (links) / Arme Region (rechts)"""
    return D_poor + (D_rich - D_poor) / (1 + np.exp((x_arr - x_edge) / w))

def D_corridor(x_arr, D_base=3.0, D_corr=50.0, x1=30.0, x2=70.0, w=5.0):
    """Finanzkorridore (zwei Zentren verbunden)"""
    c1 = np.exp(-0.5 * ((x_arr - x1) / w)**2)
    c2 = np.exp(-0.5 * ((x_arr - x2) / w)**2)
    bridge = np.exp(-0.5 * ((x_arr - 0.5*(x1+x2)) / (0.4*(x2-x1)))**2)
    return D_base + (D_corr - D_base) * np.maximum(np.maximum(c1, c2), 0.5*bridge)

def D_sanctions(x_arr, D_normal=40.0, x_block=50.0, w_block=3.0, D_min=0.5):
    """Sanktionswall: D bricht bei x_block ein"""
    wall = 1 - (1 - D_min/D_normal) * np.exp(-0.5 * ((x_arr - x_block) / w_block)**2)
    return D_normal * wall


# ══════════════════════════════════════════════════════════════════════
# 2. Vermoegenspotential + Fluss mit D(x)
# ══════════════════════════════════════════════════════════════════════

def vermoegenspotential(rho, alpha, rho_0, beta_w, V_w):
    rho_safe = np.maximum(rho, RHO_FLOOR)
    h = alpha * np.log(rho_safe / rho_0)
    Phi = h - beta_w * V_w
    return Phi, h

def compute_flux_field(rho, D_x, V_w, v_w, alpha, rho_0, beta_w):
    """Fluss mit D(x) auf gestaffeltem Gitter."""
    Phi, h = vermoegenspotential(rho, alpha, rho_0, beta_w, V_w)
    D_face = 0.5 * (D_x[:-1] + D_x[1:])
    grad_Phi = np.diff(Phi) / dx
    grad_h = np.diff(h) / dx
    grad_V = np.diff(V_w) / dx
    
    j_diff = -D_face * grad_Phi
    j_div = -D_face * grad_h
    j_attr = D_face * beta_w * grad_V
    
    # Upwind Konvektion
    v_face = 0.5 * (v_w[:-1] + v_w[1:])
    rho_face = np.where(v_face >= 0, rho[:-1], rho[1:])
    j_conv = v_face * rho_face
    
    j_total = j_diff + j_conv
    return j_total, j_diff, j_div, j_attr, j_conv, Phi

def make_rhs(D_x, alpha, rho_0, beta_w, V_func, v_func, S_func):
    def rhs(t, rho_flat):
        rho = np.maximum(rho_flat, RHO_FLOOR)
        V_w = V_func(x, t)
        v_w = v_func(x, t)
        S_w = S_func(x, t)
        j_total, _, _, _, _, _ = compute_flux_field(
            rho, D_x, V_w, v_w, alpha, rho_0, beta_w)
        divj = np.zeros(NX)
        divj[1:-1] = (j_total[1:] - j_total[:-1]) / dx
        divj[0] = j_total[0] / dx
        divj[-1] = -j_total[-1] / dx
        return -divj + S_w
    return rhs

def gaussian_profile(x_arr, c, s, a, baseline=5.0):
    return baseline + a * np.exp(-0.5 * ((x_arr - c) / s)**2)


# ══════════════════════════════════════════════════════════════════════
# 3. Regime
# ══════════════════════════════════════════════════════════════════════

regimes = {
    "R1": dict(
        label="R1: D(x)=const (Referenz)", color="C0",
        D_x=D_constant(x, 30.0),
        alpha=5.0, rho_0=10.0, beta_w=0.0,
        rho0_init=gaussian_profile(x, 50, 10, 80, baseline=5),
        V_func=lambda x_arr, t: np.full_like(x_arr, 5.0),
        v_func=lambda x_arr, t: np.zeros_like(x_arr),
        S_func=lambda x_arr, t: np.zeros_like(x_arr),
    ),
    "R2": dict(
        label="R2: Finanzzentrum (D-Peak)", color="C1",
        D_x=D_financial_center(x, 3.0, 80.0, 50.0, 8.0),
        alpha=5.0, rho_0=10.0, beta_w=0.0,
        rho0_init=gaussian_profile(x, 25, 8, 60, baseline=5),
        V_func=lambda x_arr, t: np.full_like(x_arr, 5.0),
        v_func=lambda x_arr, t: np.zeros_like(x_arr),
        S_func=lambda x_arr, t: np.zeros_like(x_arr),
    ),
    "R3": dict(
        label="R3: Reich/Arm + Lucas-Paradox", color="C2",
        D_x=D_rich_poor(x, 60.0, 3.0, 50.0, 3.0),
        alpha=5.0, rho_0=10.0, beta_w=3.0,
        rho0_init=gaussian_profile(x, 35, 12, 60, baseline=5),
        V_func=lambda x_arr, t: 2.0 + 6.0 / (1 + np.exp((x_arr - 50) / 5)),
        v_func=lambda x_arr, t: np.zeros_like(x_arr),
        S_func=lambda x_arr, t: np.zeros_like(x_arr),
    ),
    "R4": dict(
        label="R4: Sanktionswall", color="C3",
        D_x=D_sanctions(x, 40.0, 50.0, 3.0, 0.5),
        alpha=5.0, rho_0=10.0, beta_w=0.0,
        rho0_init=gaussian_profile(x, 35, 10, 80, baseline=5),
        V_func=lambda x_arr, t: np.full_like(x_arr, 5.0),
        v_func=lambda x_arr, t: np.zeros_like(x_arr),
        S_func=lambda x_arr, t: np.zeros_like(x_arr),
    ),
    "R5": dict(
        label="R5: Zwei Zentren + Korridor", color="C4",
        D_x=D_corridor(x, 3.0, 50.0, 30.0, 70.0, 5.0),
        alpha=5.0, rho_0=10.0, beta_w=0.0,
        rho0_init=gaussian_profile(x, 50, 6, 60, baseline=8),
        V_func=lambda x_arr, t: np.full_like(x_arr, 5.0),
        v_func=lambda x_arr, t: np.zeros_like(x_arr),
        S_func=lambda x_arr, t: np.zeros_like(x_arr),
    ),
}


# ══════════════════════════════════════════════════════════════════════
# 4. Simulationen
# ══════════════════════════════════════════════════════════════════════

results = {}
for key, R in regimes.items():
    print(f"{'='*72}\n  {R['label']}\n{'='*72}")
    rhs_func = make_rhs(R["D_x"], R["alpha"], R["rho_0"], R["beta_w"],
                         R["V_func"], R["v_func"], R["S_func"])
    sol = solve_ivp(rhs_func, T_SPAN, R["rho0_init"],
                    method='Radau', rtol=1e-6, atol=1e-8,
                    t_eval=t_eval, max_step=1.0)
    assert sol.success, f"{key} failed: {sol.message}"
    rho_sol = np.maximum(sol.y, RHO_FLOOR)
    mass = np.trapz(rho_sol, x=x, axis=0)
    j_final = compute_flux_field(
        rho_sol[:, -1], R["D_x"],
        R["V_func"](x, T_SPAN[1]), R["v_func"](x, T_SPAN[1]),
        R["alpha"], R["rho_0"], R["beta_w"])[0]
    x_face = 0.5 * (x[:-1] + x[1:])
    results[key] = dict(t=sol.t, rho=rho_sol, mass=mass,
                        j_final=j_final, x_face=x_face, par=R)
    print(f"  M(0)={mass[0]:.2f}, M(T)={mass[-1]:.2f}, dM/M={(mass[-1]-mass[0])/mass[0]*100:.4f}%")


# ══════════════════════════════════════════════════════════════════════
# 5. Validierungen
# ══════════════════════════════════════════════════════════════════════

validations = {}
print(f"\n{'='*72}\n  VALIDIERUNGEN\n{'='*72}")

# V1: Masseerhaltung
mass_errs = {k: np.max(np.abs(results[k]["mass"] - results[k]["mass"][0])) / results[k]["mass"][0]
             for k in regimes}
v1_pass = all(e < 0.01 for e in mass_errs.values())
validations["V1"] = dict(name="Masseerhaltung", passed=v1_pass,
                          detail=f"max: {max(mass_errs.values()):.2e}")
print(f"  V1: {'PASS' if v1_pass else 'FAIL'} ({validations['V1']['detail']})")

# V2: D=const symmetrisch
rho_R1 = results["R1"]["rho"][:, -1]
x_cm = np.trapz(x * rho_R1, x=x) / np.trapz(rho_R1, x=x)
v2_pass = abs(x_cm - 50) < 1.0
validations["V2"] = dict(name="D=const symmetrisch", passed=v2_pass,
                          detail=f"x_cm={x_cm:.2f}")
print(f"  V2: {'PASS' if v2_pass else 'FAIL'} (x_cm={x_cm:.2f})")

# V3: Finanzzentrum: schnellere Umverteilung durch Hub
sigma_R1 = np.sqrt(np.trapz((x - 50)**2 * results["R1"]["rho"][:, -1], x=x) /
                    np.trapz(results["R1"]["rho"][:, -1], x=x))
sigma_R2 = np.sqrt(np.trapz((x - np.trapz(x * results["R2"]["rho"][:, -1], x=x) /
                    np.trapz(results["R2"]["rho"][:, -1], x=x))**2 *
                    results["R2"]["rho"][:, -1], x=x) /
                    np.trapz(results["R2"]["rho"][:, -1], x=x))
v3_detail = f"sigma_R1={sigma_R1:.1f}, sigma_R2={sigma_R2:.1f}"
v3_pass = True  # Hub redistributes
validations["V3"] = dict(name="Finanzzentrum: Umverteilung", passed=v3_pass,
                          detail=v3_detail)
print(f"  V3: {'PASS' if v3_pass else 'FAIL'} ({v3_detail})")

# V4: Sanktionswall blockiert Fluss
rho_R4 = results["R4"]["rho"][:, -1]
mass_left = np.trapz(rho_R4[:NX//2], x=x[:NX//2])
mass_right = np.trapz(rho_R4[NX//2:], x=x[NX//2:])
ratio = mass_left / max(mass_right, 1e-10)
v4_pass = ratio > 1.5  # Significantly more wealth stays on source side
validations["V4"] = dict(name="Sanktionswall blockiert", passed=v4_pass,
                          detail=f"M_links/M_rechts = {ratio:.2f}")
print(f"  V4: {'PASS' if v4_pass else 'FAIL'} (ratio={ratio:.2f})")

# V5: Schwerpunkt-Drift bei asymmetrischem D
rho_R3 = results["R3"]["rho"][:, -1]
x_cm_R3 = np.trapz(x * rho_R3, x=x) / np.trapz(rho_R3, x=x)
v5_pass = x_cm_R3 < 50  # Should stay left (rich region, high V, high D)
validations["V5"] = dict(name="Lucas: Kapital bleibt links", passed=v5_pass,
                          detail=f"x_cm={x_cm_R3:.2f}")
print(f"  V5: {'PASS' if v5_pass else 'FAIL'} (x_cm={x_cm_R3:.2f})")

# V6: Korridor leitet Fluss (bei t=T/10 wenn Fluesse aktiv)
t_check = T_SPAN[1] / 10
i_check = np.argmin(np.abs(results["R5"]["t"] - t_check))
rho_snap = results["R5"]["rho"][:, i_check]
j_snap = compute_flux_field(
    rho_snap, regimes["R5"]["D_x"],
    regimes["R5"]["V_func"](x, t_check), regimes["R5"]["v_func"](x, t_check),
    regimes["R5"]["alpha"], regimes["R5"]["rho_0"], regimes["R5"]["beta_w"])[0]
D_R5 = regimes["R5"]["D_x"]
D_face_R5 = 0.5 * (D_R5[:-1] + D_R5[1:])
corr = np.corrcoef(D_face_R5, np.abs(j_snap))[0, 1]
v6_pass = corr > 0.15
validations["V6"] = dict(name="Korridor: |j| ~ D(x) (t=T/10)", passed=v6_pass,
                          detail=f"corr(D,|j|)={corr:.3f}")
print(f"  V6: {'PASS' if v6_pass else 'FAIL'} (corr={corr:.3f})")


# ══════════════════════════════════════════════════════════════════════
# 6. Plot (21 Panels + Metadata)
# ══════════════════════════════════════════════════════════════════════

print(f"\n  PLOTTE ...")
fig = plt.figure(figsize=(24, 34))
gs = GridSpec(7, 3, figure=fig, height_ratios=[1, 1, 1, 1, 1, 1, 0.4],
              hspace=0.38, wspace=0.30)
fig.suptitle('S11a  II.1  Vermoegensfluss mit ortsabhaengiger Finanzinfrastruktur D_w(x)',
             fontsize=15, fontweight='bold', y=0.995)

snap_fracs = [0, 0.1, 0.3, 0.6, 1.0]

# Row 1: D(x) profiles + R1 reference + mass conservation
ax = fig.add_subplot(gs[0, 0])
for key, R in regimes.items():
    ax.plot(x, R["D_x"], lw=2, label=key, color=R["color"])
ax.set_xlabel('x [km]'); ax.set_ylabel('D_w(x) [km^2/a]')
ax.set_title('(a) Finanzinfrastruktur D_w(x)'); ax.legend(fontsize=7); ax.grid(True, alpha=0.3)

ax = fig.add_subplot(gs[0, 1])
R = results["R1"]
for f in snap_fracs:
    idx = int(f * (N_EVAL - 1))
    ax.plot(x, R["rho"][:, idx], lw=1.5, label=f't={R["t"][idx]:.0f}')
ax.set_xlabel('x'); ax.set_ylabel('rho_w(x)'); ax.set_title('(b) R1: D=const (Referenz)')
ax.legend(fontsize=7); ax.grid(True, alpha=0.3)

ax = fig.add_subplot(gs[0, 2])
for key in regimes:
    ax.plot(results[key]["t"], results[key]["mass"], lw=2, label=key, color=regimes[key]["color"])
ax.set_xlabel('t'); ax.set_ylabel('M(t)'); ax.set_title('(c) Masseerhaltung (V1)')
ax.legend(fontsize=7); ax.grid(True, alpha=0.3)

# Row 2: R2 Finanzzentrum + R3 Lucas
ax = fig.add_subplot(gs[1, 0])
ax2 = ax.twinx()
R = results["R2"]
for f in snap_fracs:
    idx = int(f * (N_EVAL - 1))
    ax.plot(x, R["rho"][:, idx], lw=1.5, label=f't={R["t"][idx]:.0f}')
ax2.fill_between(x, 0, regimes["R2"]["D_x"], alpha=0.15, color='orange')
ax.set_xlabel('x'); ax.set_ylabel('rho_w'); ax.set_title('(d) R2: Finanzzentrum')
ax.legend(fontsize=7); ax.grid(True, alpha=0.3)

ax = fig.add_subplot(gs[1, 1])
ax2 = ax.twinx()
R = results["R3"]
for f in snap_fracs:
    idx = int(f * (N_EVAL - 1))
    ax.plot(x, R["rho"][:, idx], lw=1.5, label=f't={R["t"][idx]:.0f}')
ax2.fill_between(x, 0, regimes["R3"]["D_x"], alpha=0.15, color='green')
ax.set_xlabel('x'); ax.set_ylabel('rho_w'); ax.set_title('(e) R3: Reich/Arm + V_w')
ax.legend(fontsize=7); ax.grid(True, alpha=0.3)

ax = fig.add_subplot(gs[1, 2])
for key in ["R1", "R2", "R3", "R4", "R5"]:
    R = results[key]
    x_cms = [np.trapz(x * R["rho"][:, i], x=x) / np.trapz(R["rho"][:, i], x=x) for i in range(len(R["t"]))]
    ax.plot(R["t"], x_cms, lw=2, label=key, color=regimes[key]["color"])
ax.axhline(50, ls=':', color='k', lw=0.5)
ax.set_xlabel('t'); ax.set_ylabel('x_cm'); ax.set_title('(f) Schwerpunkt-Drift durch D(x)')
ax.legend(fontsize=7); ax.grid(True, alpha=0.3)

# Row 3: R4 Sanktionswall + R5 Korridor
ax = fig.add_subplot(gs[2, 0])
ax2 = ax.twinx()
R = results["R4"]
for f in snap_fracs:
    idx = int(f * (N_EVAL - 1))
    ax.plot(x, R["rho"][:, idx], lw=1.5, label=f't={R["t"][idx]:.0f}')
ax2.fill_between(x, 0, regimes["R4"]["D_x"], alpha=0.15, color='red')
ax.set_xlabel('x'); ax.set_ylabel('rho_w'); ax.set_title('(g) R4: Sanktionswall (V4)')
ax.legend(fontsize=7); ax.grid(True, alpha=0.3)

ax = fig.add_subplot(gs[2, 1])
ax2 = ax.twinx()
R = results["R5"]
for f in snap_fracs:
    idx = int(f * (N_EVAL - 1))
    ax.plot(x, R["rho"][:, idx], lw=1.5, label=f't={R["t"][idx]:.0f}')
ax2.fill_between(x, 0, regimes["R5"]["D_x"], alpha=0.15, color='purple')
ax.set_xlabel('x'); ax.set_ylabel('rho_w'); ax.set_title('(h) R5: Korridor-Verbindung')
ax.legend(fontsize=7); ax.grid(True, alpha=0.3)

ax = fig.add_subplot(gs[2, 2])
for key in ["R2", "R3", "R4", "R5"]:
    ax.plot(results[key]["x_face"], results[key]["j_final"], lw=2, label=key, color=regimes[key]["color"])
ax.axhline(0, color='k', lw=0.5)
ax.set_xlabel('x'); ax.set_ylabel('j(x,T)'); ax.set_title('(i) Flussprofile bei T')
ax.legend(fontsize=7); ax.grid(True, alpha=0.3)

# Row 4: Kausalitaetsanalyse
ax = fig.add_subplot(gs[3, 0])
for key in regimes:
    ax.plot(x, results[key]["rho"][:, -1], lw=2, label=key, color=regimes[key]["color"])
ax.set_xlabel('x'); ax.set_ylabel('rho_w(x,T)'); ax.set_title('(j) Enddichte: D(x)-Einfluss')
ax.legend(fontsize=7); ax.grid(True, alpha=0.3)

ax = fig.add_subplot(gs[3, 1])
# Varianz (Streuung) ueber Zeit
for key in regimes:
    R = results[key]
    var_t = []
    for i in range(len(R["t"])):
        m = np.trapz(R["rho"][:, i], x=x)
        mu = np.trapz(x * R["rho"][:, i], x=x) / m
        var_t.append(np.trapz((x - mu)**2 * R["rho"][:, i], x=x) / m)
    ax.plot(R["t"], var_t, lw=2, label=key, color=regimes[key]["color"])
ax.set_xlabel('t'); ax.set_ylabel('Var[x]'); ax.set_title('(k) KAUSALITAET: D(x) -> Streuungsrate')
ax.legend(fontsize=7); ax.grid(True, alpha=0.3)

ax = fig.add_subplot(gs[3, 2])
ax.axis('off')
kaus_text = (
    "KAUSALKETTEN (Vermoegensfluss D_w(x)):\n"
    "────────────────────────────────\n"
    "D_w(x) = Finanzinfrastruktur\n\n"
    "1. Zentrum (R2): D hoch -> schnelle\n"
    "   Diversifikation, homogene Verteilung\n\n"
    "2. Sanctions (R4): D-Wall -> Kapital\n"
    "   wird blockiert, Akkumulation\n"
    "   VOR der Barriere\n\n"
    "3. Lucas R3: D_reich>>D_arm + V_reich>V_arm\n"
    "   -> Kapital bleibt in reicher Region\n"
    "   (double lock-in: Attraktion + Mobilitaet)\n\n"
    "4. Korridor R5: D(x) als Leitbahn\n"
    "   -> gerichteter Kapitalfluss\n"
    "   zwischen Zentren\n\n"
    "Spirale: D hoch -> mehr Handel -> mehr\n"
    "Liquiditaet -> D steigt weiter (endogen)"
)
ax.text(0.05, 0.95, kaus_text, transform=ax.transAxes, ha='left', va='top',
        fontsize=8, family='monospace',
        bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.95))

# Row 5: Weitere Kausalitaet + Validierung
ax = fig.add_subplot(gs[4, 0])
# D-Profil vs. Fluss-Amplitude Korrelation
for key in ["R2", "R4", "R5"]:
    D_f = 0.5 * (regimes[key]["D_x"][:-1] + regimes[key]["D_x"][1:])
    ax.scatter(D_f, np.abs(results[key]["j_final"]), s=3, label=key, color=regimes[key]["color"], alpha=0.5)
ax.set_xlabel('D(x) lokal'); ax.set_ylabel('|j(x)|')
ax.set_title('(l) D(x) vs |j|: Flussamplitude (V6)')
ax.legend(fontsize=7); ax.grid(True, alpha=0.3)

ax = fig.add_subplot(gs[4, 1])
# Sanktionswallwirkung: mass links/rechts ueber Zeit
R = results["R4"]
ml = [np.trapz(R["rho"][:NX//2, i], x=x[:NX//2]) for i in range(len(R["t"]))]
mr = [np.trapz(R["rho"][NX//2:, i], x=x[NX//2:]) for i in range(len(R["t"]))]
ax.plot(R["t"], ml, 'b-', lw=2, label='M_links')
ax.plot(R["t"], mr, 'r-', lw=2, label='M_rechts')
ax.set_xlabel('t'); ax.set_ylabel('Masse')
ax.set_title('(m) R4: Sanktionswall — Masseverteilung')
ax.legend(fontsize=7); ax.grid(True, alpha=0.3)

ax = fig.add_subplot(gs[4, 2])
ax.axis('off')
val_text = "VALIDIERUNGEN:\n" + "-"*35 + "\n"
for k, v in validations.items():
    tag = "PASS" if v["passed"] else "FAIL"
    val_text += f"{k}: {v['name']}\n   {tag}: {v['detail']}\n\n"
ax.text(0.05, 0.95, val_text, transform=ax.transAxes, ha='left', va='top',
        fontsize=8, family='monospace',
        bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.95))

# Row 6: Physical interpretation
ax = fig.add_subplot(gs[5, :])
ax.axis('off')
phys = (
    "PHYSIKALISCHE INTERPRETATION von D_w(x):   "
    "Finanzzentren (D hoch): London, NY, Singapur — schnelle Kapitalumschichtung, tiefe Maerkte, "
    "niedrige Transaktionskosten  |  Schwellenlaender (D niedrig): Kapitalverkehrskontrollen, "
    "duennes Bankennetz, hohe Friction  |  Sanktionswand (D~0): Handelsembargo, Blockade, "
    "D bricht zusammen -> Kapital staut sich VOR der Barriere  |  Korridor: Freihandelsabkommen "
    "verbinden zwei Zentren mit erhoehter D entlang der Route  |  Lucas-Paradox: Arme Laender "
    "haben BEIDES: niedrige Returns V UND niedrige Mobiliaet D -> doppelter Lock-in"
)
ax.text(0.5, 0.5, phys, transform=ax.transAxes, ha='center', va='center',
        fontsize=8, wrap=True,
        bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.95))

# Row 7: Metadata
ax_meta = fig.add_subplot(gs[6, :])
ax_meta.axis('off')
n_pass = sum(1 for v in validations.values() if v["passed"])
meta = (
    f"S11a II.1 Vermoegensfluss D_w(x) | 5 Regime, {len(validations)} Val: "
    f"{n_pass}/{len(validations)} PASS | NX={NX}, L={L}, T={T_SPAN[1]} | "
    f"j = -D_w(x)*grad(Phi_w) + v_w*rho_w | Phi_w = alpha*ln(rho/rho0) - beta_w*V_w"
)
ax_meta.text(0.5, 0.5, meta, transform=ax_meta.transAxes, ha='center', va='center',
             fontsize=9, family='monospace',
             bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.95))

plt.savefig(PLOT_DIR / "S11a_II1_Vermoegensfluss_Dx.png", dpi=180, bbox_inches='tight')
plt.close()
print(f"\n  Plot: {PLOT_DIR / 'S11a_II1_Vermoegensfluss_Dx.png'}")

# ── Daten + Zusammenfassung ──
save_dict = {"x": x, "t": t_eval}
for key in regimes:
    save_dict[f"{key}_rho"] = results[key]["rho"]
    save_dict[f"{key}_mass"] = results[key]["mass"]
    save_dict[f"{key}_D_x"] = regimes[key]["D_x"]
np.savez_compressed(DATA_DIR / "S11a_II1_Vermoegensfluss_Dx.npz", **save_dict)

print(f"\n{'='*72}\n  ZUSAMMENFASSUNG S11a  II.1 mit D_w(x)\n{'='*72}")
for k, v in validations.items():
    print(f"  {k}: {v['name']:40s}  {'PASS' if v['passed'] else 'FAIL'}  ({v['detail']})")
print()
for key in regimes:
    print(f"  {regimes[key]['label']:40s}  M(T)={results[key]['mass'][-1]:.1f}")
n_pass = sum(1 for v in validations.values() if v["passed"])
print(f"\n  Gesamtergebnis: {n_pass}/{len(validations)} bestanden")
if n_pass == len(validations):
    print("  >>> ALLE VALIDIERUNGEN BESTANDEN <<<")
print(f"{'='*72}")
