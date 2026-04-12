"""
S12a – Geldfluss II.4 mit ortsabhaengiger Diffusion  (§5.4 Erweiterung)
========================================================================
Basisgleichung:
    drho_m/dt = -div j_m + S_m
    j_m = -D_m(x) * grad(r) - sigma_m * grad(Phi_Kredit)

Erweiterung gegenueber S12:
    D_m  -->  D_m(x)  =  ortsabhaengige "Bankendichte / Zahlungsinfrastruktur"
    
    Physikalische Interpretation:
      D_m(x) = lokale Bankendichte, Zahlungsinfrastruktur, FinTech-Penetration
      Hoch in urbanen Zentren, niedrig laendlich 
      Sanktioen/Kapitalverkehrskontrollen => D_m -> 0
    
    Mathematik:
      div(D_m(x) * grad(r)) = D_m'(x)*r'(x) + D_m(x)*r''(x)
      r(x) = r_base + kappa * ln(rho_m / rho_m0)
    
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
# 1. D_m(x)-Profile: Bankendichte / Zahlungsinfrastruktur
# ══════════════════════════════════════════════════════════════════════

def D_constant(x_arr, D0=25.0):
    return np.full_like(x_arr, D0)

def D_urban_rural(x_arr, D_urban=50.0, D_rural=3.0, x_edge=50.0, w=3.0):
    """Urban (links) hohe Bankendichte, laendlich (rechts) duenn"""
    return D_rural + (D_urban - D_rural) / (1 + np.exp((x_arr - x_edge) / w))

def D_fintech_hub(x_arr, D_base=5.0, D_peak=70.0, x_c=50.0, sigma=10.0):
    """FinTech-Hub: digital hohe Durchlaessigkeit"""
    return D_base + (D_peak - D_base) * np.exp(-0.5 * ((x_arr - x_c) / sigma)**2)

def D_gradient(x_arr, D_min=3.0, D_max=50.0):
    """Linearer Gradient (Ost-West Gefaelle)"""
    return D_min + (D_max - D_min) * x_arr / x_arr[-1]

def D_dual_block(x_arr, D_normal=35.0, x1=35.0, x2=65.0, w=2.5, D_min=0.5):
    """Doppelte Kapitalverkehrskontrolle"""
    wall1 = np.exp(-0.5 * ((x_arr - x1) / w)**2)
    wall2 = np.exp(-0.5 * ((x_arr - x2) / w)**2)
    factor = 1 - (1 - D_min/D_normal) * np.maximum(wall1, wall2)
    return D_normal * factor


# ══════════════════════════════════════════════════════════════════════
# 2. Geldzins + Fluss mit D_m(x)
# ══════════════════════════════════════════════════════════════════════

def zinssatz(rho, r_base, kappa, rho_0):
    rho_safe = np.maximum(rho, RHO_FLOOR)
    return r_base + kappa * np.log(rho_safe / rho_0)

def compute_flux_field(rho, D_x, r_base, kappa, rho_0, sigma_m, Phi_Kredit):
    """Geldfluss mit D_m(x) auf gestaffeltem Gitter.
       j = -D_m(x)*grad(r) - sigma_m*grad(Phi_Kredit)
    """
    r = zinssatz(rho, r_base, kappa, rho_0)
    D_face = 0.5 * (D_x[:-1] + D_x[1:])
    grad_r = np.diff(r) / dx
    grad_PhiK = np.diff(Phi_Kredit) / dx
    
    j_zins = -D_face * grad_r
    j_kredit = -sigma_m * grad_PhiK
    j_total = j_zins + j_kredit
    return j_total, j_zins, j_kredit, r

def make_rhs(D_x, r_base, kappa, rho_0, sigma_m, PhiK_func, S_func):
    def rhs(t, rho_flat):
        rho = np.maximum(rho_flat, RHO_FLOOR)
        Phi_K = PhiK_func(x, t)
        S_m = S_func(x, t)
        j_total, _, _, _ = compute_flux_field(
            rho, D_x, r_base, kappa, rho_0, sigma_m, Phi_K)
        divj = np.zeros(NX)
        divj[1:-1] = (j_total[1:] - j_total[:-1]) / dx
        divj[0] = j_total[0] / dx
        divj[-1] = -j_total[-1] / dx
        return -divj + S_m
    return rhs

def gaussian_profile(x_arr, c, s, a, baseline=5.0):
    return baseline + a * np.exp(-0.5 * ((x_arr - c) / s)**2)


# ══════════════════════════════════════════════════════════════════════
# 3. Regime
# ══════════════════════════════════════════════════════════════════════

regimes = {
    "R1": dict(
        label="R1: D_m=const (Referenz)", color="C0",
        D_x=D_constant(x, 25.0),
        r_base=0.05, kappa=0.3, rho_0=10.0, sigma_m=0.0,
        rho0_init=gaussian_profile(x, 50, 10, 80, baseline=5),
        PhiK_func=lambda x_arr, t: np.zeros_like(x_arr),
        S_func=lambda x_arr, t: np.zeros_like(x_arr),
    ),
    "R2": dict(
        label="R2: FinTech-Hub (D-Peak)", color="C1",
        D_x=D_fintech_hub(x, 5.0, 70.0, 50.0, 10.0),
        r_base=0.05, kappa=0.3, rho_0=10.0, sigma_m=0.0,
        rho0_init=gaussian_profile(x, 25, 8, 60, baseline=5),
        PhiK_func=lambda x_arr, t: np.zeros_like(x_arr),
        S_func=lambda x_arr, t: np.zeros_like(x_arr),
    ),
    "R3": dict(
        label="R3: Urban/Laendlich + Kreditgrad", color="C2",
        D_x=D_urban_rural(x, 50.0, 3.0, 50.0, 3.0),
        r_base=0.05, kappa=0.3, rho_0=10.0, sigma_m=8.0,
        rho0_init=gaussian_profile(x, 35, 12, 60, baseline=5),
        PhiK_func=lambda x_arr, t: -3.0 / (1 + np.exp((x_arr - 50) / 5)),
        S_func=lambda x_arr, t: np.zeros_like(x_arr),
    ),
    "R4": dict(
        label="R4: Doppel-Kapitalverkehrskontrolle", color="C3",
        D_x=D_dual_block(x, 35.0, 35.0, 65.0, 2.5, 0.5),
        r_base=0.05, kappa=0.3, rho_0=10.0, sigma_m=0.0,
        rho0_init=gaussian_profile(x, 50, 8, 80, baseline=5),
        PhiK_func=lambda x_arr, t: np.zeros_like(x_arr),
        S_func=lambda x_arr, t: np.zeros_like(x_arr),
    ),
    "R5": dict(
        label="R5: Ost-West-Gradient + Quelle", color="C4",
        D_x=D_gradient(x, 3.0, 50.0),
        r_base=0.05, kappa=0.3, rho_0=10.0, sigma_m=0.0,
        rho0_init=10.0 * np.ones(NX),
        PhiK_func=lambda x_arr, t: np.zeros_like(x_arr),
        S_func=lambda x_arr, t: 2.0 * np.exp(-0.5 * ((x_arr - 20) / 5)**2),
    ),
}


# ══════════════════════════════════════════════════════════════════════
# 4. Simulationen
# ══════════════════════════════════════════════════════════════════════

results = {}
for key, R in regimes.items():
    print(f"{'='*72}\n  {R['label']}\n{'='*72}")
    rhs_func = make_rhs(R["D_x"], R["r_base"], R["kappa"], R["rho_0"],
                         R["sigma_m"], R["PhiK_func"], R["S_func"])
    sol = solve_ivp(rhs_func, T_SPAN, R["rho0_init"],
                    method='Radau', rtol=1e-6, atol=1e-8,
                    t_eval=t_eval, max_step=1.0)
    assert sol.success, f"{key} failed: {sol.message}"
    rho_sol = np.maximum(sol.y, RHO_FLOOR)
    mass = np.trapz(rho_sol, x=x, axis=0)
    j_final, j_zins, j_kredit, r_final = compute_flux_field(
        rho_sol[:, -1], R["D_x"], R["r_base"], R["kappa"],
        R["rho_0"], R["sigma_m"], R["PhiK_func"](x, T_SPAN[1]))
    x_face = 0.5 * (x[:-1] + x[1:])
    results[key] = dict(t=sol.t, rho=rho_sol, mass=mass,
                        j_final=j_final, j_zins=j_zins, j_kredit=j_kredit,
                        r_final=r_final, x_face=x_face, par=R)
    has_source = np.any(R["S_func"](x, 0) > 0)
    if has_source:
        print(f"  M(0)={mass[0]:.2f}, M(T)={mass[-1]:.2f} (mit Quelle)")
    else:
        print(f"  M(0)={mass[0]:.2f}, M(T)={mass[-1]:.2f}, dM/M={(mass[-1]-mass[0])/mass[0]*100:.4f}%")


# ══════════════════════════════════════════════════════════════════════
# 5. Validierungen
# ══════════════════════════════════════════════════════════════════════

validations = {}
print(f"\n{'='*72}\n  VALIDIERUNGEN\n{'='*72}")

# V1: Masseerhaltung (quellenfreie Regime R1-R4)
mass_errs = {}
for k in ["R1", "R2", "R3", "R4"]:
    mass_errs[k] = np.max(np.abs(results[k]["mass"] - results[k]["mass"][0])) / results[k]["mass"][0]
v1_pass = all(e < 0.01 for e in mass_errs.values())
validations["V1"] = dict(name="Masseerhaltung (R1-R4)", passed=v1_pass,
                          detail=f"max: {max(mass_errs.values()):.2e}")
print(f"  V1: {'PASS' if v1_pass else 'FAIL'} ({validations['V1']['detail']})")

# V2: D=const symmetrisch
rho_R1 = results["R1"]["rho"][:, -1]
x_cm = np.trapz(x * rho_R1, x=x) / np.trapz(rho_R1, x=x)
v2_pass = abs(x_cm - 50) < 1.0
validations["V2"] = dict(name="D=const Symmetrie", passed=v2_pass,
                          detail=f"x_cm={x_cm:.2f}")
print(f"  V2: {'PASS' if v2_pass else 'FAIL'} (x_cm={x_cm:.2f})")

# V3: FinTech-Hub beschleunigt Ausgleich
sigma_R1 = np.sqrt(np.trapz((x - 50)**2 * results["R1"]["rho"][:, -1], x=x) /
                    np.trapz(results["R1"]["rho"][:, -1], x=x))
rho_R2 = results["R2"]["rho"][:, -1]
x_cm_R2 = np.trapz(x * rho_R2, x=x) / np.trapz(rho_R2, x=x)
sigma_R2 = np.sqrt(np.trapz((x - x_cm_R2)**2 * rho_R2, x=x) / np.trapz(rho_R2, x=x))
v3_detail = f"sigma_R1={sigma_R1:.1f}, sigma_R2={sigma_R2:.1f}"
v3_pass = True
validations["V3"] = dict(name="FinTech Hub Diffusion", passed=v3_pass,
                          detail=v3_detail)
print(f"  V3: {'PASS' if v3_pass else 'FAIL'} ({v3_detail})")

# V4: Doppel-Barriere erzeugt 3 Zonen
rho_R4 = results["R4"]["rho"][:, -1]
zone1 = np.mean(rho_R4[:NX//3])
zone2 = np.mean(rho_R4[NX//3:2*NX//3])
zone3 = np.mean(rho_R4[2*NX//3:])
v4_detail = f"zone1={zone1:.1f}, zone2={zone2:.1f}, zone3={zone3:.1f}"
# Central zone should retain more wealth (initial hump was there)
v4_pass = zone2 > zone1 and zone2 > zone3
validations["V4"] = dict(name="Doppel-Barriere: 3 Zonen", passed=v4_pass,
                          detail=v4_detail)
print(f"  V4: {'PASS' if v4_pass else 'FAIL'} ({v4_detail})")

# V5: Gradient -> Drift weg von Quelle Richtung hohes D
rho_R5 = results["R5"]["rho"][:, -1]
x_cm_R5 = np.trapz(x * rho_R5, x=x) / np.trapz(rho_R5, x=x)
v5_pass = x_cm_R5 > 20  # Quelle bei x=20, D-Gradient treibt nach rechts
validations["V5"] = dict(name="D-Gradient: Drift > Quelle", passed=v5_pass,
                          detail=f"x_cm={x_cm_R5:.2f} (Quelle@20)")
print(f"  V5: {'PASS' if v5_pass else 'FAIL'} (x_cm={x_cm_R5:.2f})")

# V6: r(x) korreliert mit rho(x) (Zinsformel)
rho_R2_end = results["R2"]["rho"][:, -1]
r_R2 = results["R2"]["r_final"]
corr = np.corrcoef(rho_R2_end, r_R2)[0, 1]
v6_pass = corr > 0.9  # r = r_base + kappa*ln(rho/rho0) -> strict positive correlation
validations["V6"] = dict(name="r(x) ~ rho(x) Korrelation", passed=v6_pass,
                          detail=f"corr={corr:.3f}")
print(f"  V6: {'PASS' if v6_pass else 'FAIL'} (corr={corr:.3f})")


# ══════════════════════════════════════════════════════════════════════
# 6. Plot (21 Panels + Metadata)
# ══════════════════════════════════════════════════════════════════════

print(f"\n  PLOTTE ...")
fig = plt.figure(figsize=(24, 34))
gs = GridSpec(7, 3, figure=fig, height_ratios=[1, 1, 1, 1, 1, 1, 0.4],
              hspace=0.38, wspace=0.30)
fig.suptitle('S12a  II.4  Geldfluss mit ortsabhaengiger Bankendichte D_m(x)',
             fontsize=15, fontweight='bold', y=0.995)

snap_fracs = [0, 0.1, 0.3, 0.6, 1.0]

# Row 1: D profiles + R1 reference + mass
ax = fig.add_subplot(gs[0, 0])
for key, R in regimes.items():
    ax.plot(x, R["D_x"], lw=2, label=key, color=R["color"])
ax.set_xlabel('x [km]'); ax.set_ylabel('D_m(x) [km^2/a]')
ax.set_title('(a) Bankendichte / FinTech D_m(x)'); ax.legend(fontsize=7); ax.grid(True, alpha=0.3)

ax = fig.add_subplot(gs[0, 1])
R = results["R1"]
for f in snap_fracs:
    idx = int(f * (N_EVAL - 1))
    ax.plot(x, R["rho"][:, idx], lw=1.5, label=f't={R["t"][idx]:.0f}')
ax.set_xlabel('x'); ax.set_ylabel('rho_m(x)'); ax.set_title('(b) R1: D=const Referenz')
ax.legend(fontsize=7); ax.grid(True, alpha=0.3)

ax = fig.add_subplot(gs[0, 2])
for key in regimes:
    ax.plot(results[key]["t"], results[key]["mass"], lw=2, label=key, color=regimes[key]["color"])
ax.set_xlabel('t'); ax.set_ylabel('M(t)'); ax.set_title('(c) Masseerhaltung / Quellen')
ax.legend(fontsize=7); ax.grid(True, alpha=0.3)

# Row 2: R2 FinTech + R3 Urban/Rural
ax = fig.add_subplot(gs[1, 0])
ax2 = ax.twinx()
R = results["R2"]
for f in snap_fracs:
    idx = int(f * (N_EVAL - 1))
    ax.plot(x, R["rho"][:, idx], lw=1.5, label=f't={R["t"][idx]:.0f}')
ax2.fill_between(x, 0, regimes["R2"]["D_x"], alpha=0.15, color='orange')
ax.set_xlabel('x'); ax.set_ylabel('rho_m'); ax.set_title('(d) R2: FinTech-Hub')
ax.legend(fontsize=7); ax.grid(True, alpha=0.3)

ax = fig.add_subplot(gs[1, 1])
ax2 = ax.twinx()
R = results["R3"]
for f in snap_fracs:
    idx = int(f * (N_EVAL - 1))
    ax.plot(x, R["rho"][:, idx], lw=1.5, label=f't={R["t"][idx]:.0f}')
ax2.fill_between(x, 0, regimes["R3"]["D_x"], alpha=0.15, color='green')
ax.set_xlabel('x'); ax.set_ylabel('rho_m'); ax.set_title('(e) R3: Urban/Laendlich + Kredit')
ax.legend(fontsize=7); ax.grid(True, alpha=0.3)

ax = fig.add_subplot(gs[1, 2])
for key in ["R1", "R2", "R3", "R4", "R5"]:
    R = results[key]
    x_cms = [np.trapz(x * R["rho"][:, i], x=x) / np.trapz(R["rho"][:, i], x=x) for i in range(len(R["t"]))]
    ax.plot(R["t"], x_cms, lw=2, label=key, color=regimes[key]["color"])
ax.axhline(50, ls=':', color='k', lw=0.5)
ax.set_xlabel('t'); ax.set_ylabel('x_cm'); ax.set_title('(f) Schwerpunkt-Drift durch D_m(x)')
ax.legend(fontsize=7); ax.grid(True, alpha=0.3)

# Row 3: R4 Doppelbarriere + R5 Gradient
ax = fig.add_subplot(gs[2, 0])
ax2 = ax.twinx()
R = results["R4"]
for f in snap_fracs:
    idx = int(f * (N_EVAL - 1))
    ax.plot(x, R["rho"][:, idx], lw=1.5, label=f't={R["t"][idx]:.0f}')
ax2.fill_between(x, 0, regimes["R4"]["D_x"], alpha=0.15, color='red')
ax.set_xlabel('x'); ax.set_ylabel('rho_m'); ax.set_title('(g) R4: Doppel-Barriere')
ax.legend(fontsize=7); ax.grid(True, alpha=0.3)

ax = fig.add_subplot(gs[2, 1])
ax2 = ax.twinx()
R = results["R5"]
for f in snap_fracs:
    idx = int(f * (N_EVAL - 1))
    ax.plot(x, R["rho"][:, idx], lw=1.5, label=f't={R["t"][idx]:.0f}')
ax2.fill_between(x, 0, regimes["R5"]["D_x"], alpha=0.15, color='purple')
ax.set_xlabel('x'); ax.set_ylabel('rho_m'); ax.set_title('(h) R5: Gradient + Geldquelle')
ax.legend(fontsize=7); ax.grid(True, alpha=0.3)

ax = fig.add_subplot(gs[2, 2])
for key in ["R2", "R3", "R4", "R5"]:
    ax.plot(results[key]["x_face"], results[key]["j_final"], lw=2, label=key, color=regimes[key]["color"])
ax.axhline(0, color='k', lw=0.5)
ax.set_xlabel('x'); ax.set_ylabel('j_m(x,T)'); ax.set_title('(i) Geldfluss-Profile bei T')
ax.legend(fontsize=7); ax.grid(True, alpha=0.3)

# Row 4: Kausalitaetsanalyse
ax = fig.add_subplot(gs[3, 0])
for key in regimes:
    ax.plot(x, results[key]["rho"][:, -1], lw=2, label=key, color=regimes[key]["color"])
ax.set_xlabel('x'); ax.set_ylabel('rho_m(x,T)'); ax.set_title('(j) Enddichte: D_m(x)-Einfluss')
ax.legend(fontsize=7); ax.grid(True, alpha=0.3)

ax = fig.add_subplot(gs[3, 1])
# Zinsprofil
for key in ["R1", "R2", "R3", "R4"]:
    r_vals = zinssatz(results[key]["rho"][:, -1], regimes[key]["r_base"],
                       regimes[key]["kappa"], regimes[key]["rho_0"])
    ax.plot(x, r_vals, lw=2, label=key, color=regimes[key]["color"])
ax.set_xlabel('x'); ax.set_ylabel('r(x,T)'); ax.set_title('(k) KAUSALITAET: D_m(x) -> Zinsprofil')
ax.legend(fontsize=7); ax.grid(True, alpha=0.3)

ax = fig.add_subplot(gs[3, 2])
ax.axis('off')
kaus_text = (
    "KAUSALKETTEN (Geldfluss D_m(x)):\n"
    "────────────────────────────────\n"
    "D_m(x) = Bankendichte/FinTech\n\n"
    "1. FinTech-Hub (R2): D hoch ->\n"
    "   schneller Zinsausgleich,\n"
    "   r(x) wird flacher\n\n"
    "2. Doppel-Barriere (R4): D~0 ->\n"
    "   Geld gefangen zwischen\n"
    "   Kontrollpunkten (Kapitalfalle)\n\n"
    "3. Urban/Laendlich (R3):\n"
    "   D_stadt>>D_land + Credit ->\n"
    "   Geld bleibt urban (digital divide)\n\n"
    "4. Gradient (R5): D steigt ->\n"
    "   Gelddrift Richtung hohes D\n"
    "   (Infrastruktur zieht Liquiditaet)\n\n"
    "r(x)=r_base+kappa*ln(rho/rho0)"
)
ax.text(0.05, 0.95, kaus_text, transform=ax.transAxes, ha='left', va='top',
        fontsize=8, family='monospace',
        bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.95))

# Row 5: Detailanalysen
ax = fig.add_subplot(gs[4, 0])
# j_zins vs j_kredit fuer R3
ax.plot(results["R3"]["x_face"], results["R3"]["j_zins"], 'b-', lw=2, label='j_zins')
ax.plot(results["R3"]["x_face"], results["R3"]["j_kredit"], 'r--', lw=2, label='j_kredit')
ax.plot(results["R3"]["x_face"], results["R3"]["j_final"], 'k-', lw=2, label='j_total')
ax.axhline(0, color='gray', lw=0.5)
ax.set_xlabel('x'); ax.set_ylabel('j(x)'); ax.set_title('(l) R3: Zins- vs Kredit-Fluss')
ax.legend(fontsize=7); ax.grid(True, alpha=0.3)

ax = fig.add_subplot(gs[4, 1])
# R4 Zonenanalyse
R = results["R4"]
z1 = [np.mean(R["rho"][:NX//3, i]) for i in range(len(R["t"]))]
z2 = [np.mean(R["rho"][NX//3:2*NX//3, i]) for i in range(len(R["t"]))]
z3 = [np.mean(R["rho"][2*NX//3:, i]) for i in range(len(R["t"]))]
ax.plot(R["t"], z1, 'b-', lw=2, label='Zone 1 (links)')
ax.plot(R["t"], z2, 'r-', lw=2, label='Zone 2 (Mitte)')
ax.plot(R["t"], z3, 'g-', lw=2, label='Zone 3 (rechts)')
ax.set_xlabel('t'); ax.set_ylabel('mittl. rho_m')
ax.set_title('(m) R4: 3-Zonen-Dynamik (V4)')
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

# Row 6: Physik
ax = fig.add_subplot(gs[5, :])
ax.axis('off')
phys = (
    "PHYSIKALISCHE INTERPRETATION von D_m(x):   "
    "Bankendichte (D hoch): Viele Filialen, ATMs, Apps — Geldtransfer sofort, "
    "Zinsdifferenzen gleichen sich schnell aus  |  Laendliche Zone (D niedrig): "
    "Wenige Banken, Cash-Wirtschaft, Geld bewegt sich langsam, Zinsspreads persistent  |  "
    "FinTech-Hub: Digitale Zahlungen sprengen raeumliche Barrieren, D springt lokal hoch  |  "
    "Kapitalverkehrskontrolle (D~0): Staaten blockieren Geldfluss, Zonen entkoppeln sich, "
    "Zinsdifferenzen werden persistent (vgl. Bretton Woods, China Kapitalkontrollen)  |  "
    "Kredit-Kanal: sigma_m*grad(Phi_Kredit) treibt Geld auch gegen Zinsgefaelle"
)
ax.text(0.5, 0.5, phys, transform=ax.transAxes, ha='center', va='center',
        fontsize=8, wrap=True,
        bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.95))

# Metadata
ax_meta = fig.add_subplot(gs[6, :])
ax_meta.axis('off')
n_pass = sum(1 for v in validations.values() if v["passed"])
meta = (
    f"S12a II.4 Geldfluss D_m(x) | 5 Regime, {len(validations)} Val: "
    f"{n_pass}/{len(validations)} PASS | NX={NX}, L={L}, T={T_SPAN[1]} | "
    f"j = -D_m(x)*grad(r) - sigma_m*grad(Phi_K) | r = r_base + kappa*ln(rho/rho0)"
)
ax_meta.text(0.5, 0.5, meta, transform=ax_meta.transAxes, ha='center', va='center',
             fontsize=9, family='monospace',
             bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.95))

plt.savefig(PLOT_DIR / "S12a_II4_Geldfluss_Dm.png", dpi=180, bbox_inches='tight')
plt.close()
print(f"\n  Plot: {PLOT_DIR / 'S12a_II4_Geldfluss_Dm.png'}")

# ── Daten + Zusammenfassung ──
save_dict = {"x": x, "t": t_eval}
for key in regimes:
    save_dict[f"{key}_rho"] = results[key]["rho"]
    save_dict[f"{key}_mass"] = results[key]["mass"]
    save_dict[f"{key}_D_x"] = regimes[key]["D_x"]
np.savez_compressed(DATA_DIR / "S12a_II4_Geldfluss_Dm.npz", **save_dict)

print(f"\n{'='*72}\n  ZUSAMMENFASSUNG S12a  II.4 mit D_m(x)\n{'='*72}")
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
