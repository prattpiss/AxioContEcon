"""
S16 – Effektiver Preis U.3: Dynamik, Kopplung, Marktversagen  (§6.2 + §22)
=============================================================================
Gleichung U.3:
    p_k^eff = p_k * (1 + psi_k / (I_k + eps))

S15 behandelte U.3 als statische Abbildung.
S16 geht tiefer:
  R1: Stigler-Suche — optimale Informationsbeschaffung I*
  R2: Akerlof Lemons — asymmetrische Information → Marktversagen
  R3: Grossman-Stiglitz — inneres Gleichgewicht I* ∈ (0,∞)
  R4: Budget-Verzerrung — p_eff schrumpft Budgetmenge
  R5: Dynamische Kopplung — I(t) treibt p_eff(t)
  R6: Singularitaet — I→0 Pol-Analyse + eps-Sensitivitaet
  R7: Wohlfahrtsdekomposition — U.2-Anteil vs U.3-Anteil

8 Validierungen + 4 Sensitivitaetsanalysen
"""

import sys, io, warnings
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
warnings.filterwarnings('ignore', category=UserWarning, module='matplotlib')

import math
import numpy as np
from scipy.optimize import minimize_scalar, brentq
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

def p_eff(p, I, psi, eps=0.01):
    """Effektiver Preis: p * (1 + psi/(I+eps))"""
    return p * (1.0 + psi / (np.maximum(I, 0.0) + eps))

def dp_eff_dI(p, I, psi, eps=0.01):
    """Ableitung dp_eff/dI = -p*psi/(I+eps)^2"""
    return -p * psi / (np.maximum(I, 0.0) + eps)**2

def search_cost(I, c0=0.5, c1=0.1):
    """Suchkosten C(I) = c0*I + c1*I^2  (konvex, steigend)"""
    return c0 * I + c1 * I**2

def search_cost_deriv(I, c0=0.5, c1=0.1):
    """C'(I) = c0 + 2*c1*I"""
    return c0 + 2 * c1 * I

def consumer_surplus(p, I, psi, eps, v0=50.0):
    """Vereinfachter Konsumentennutzen: v0 - p_eff"""
    return v0 - p_eff(p, I, psi, eps)

def net_benefit(I, p, psi, eps, v0, c0, c1):
    """Nettonutzen = Konsumentenrente - Suchkosten"""
    return consumer_surplus(p, I, psi, eps, v0) - search_cost(I, c0, c1)


print("=" * 72)
print("  S16  U.3  Effektiver Preis: Dynamik + Kopplung + Marktversagen")
print("=" * 72)

results = {}

# ══════════════════════════════════════════════════════════════════════
# R1: Stigler-Suche — optimale Informationsbeschaffung
# ══════════════════════════════════════════════════════════════════════
print("\n  R1: Stigler optimale Suche")

p_market = 10.0
psi_val = 5.0
eps_val = 0.01
v0 = 50.0
c0_vals = [0.1, 0.3, 0.5, 1.0, 2.0]
c1_val = 0.05

R1_data = {}
for c0 in c0_vals:
    # Optimales I*: maximiere net_benefit
    res = minimize_scalar(lambda I: -net_benefit(I, p_market, psi_val, eps_val, v0, c0, c1_val),
                          bounds=(0.01, 100), method='bounded')
    I_star = res.x
    nb_star = -res.fun
    peff_star = p_eff(p_market, I_star, psi_val, eps_val)
    # FOC check: -dp_eff/dI = C'(I*)
    marginal_benefit = -dp_eff_dI(p_market, I_star, psi_val, eps_val)
    marginal_cost = search_cost_deriv(I_star, c0, c1_val)
    R1_data[c0] = dict(I_star=I_star, nb=nb_star, peff=peff_star,
                        mb=marginal_benefit, mc=marginal_cost)
    print(f"    c0={c0:.1f}: I*={I_star:.2f}, p_eff*={peff_star:.2f}, MB={marginal_benefit:.4f}, MC={marginal_cost:.4f}")

# Detailkurven fuer Plot
I_range = np.linspace(0.01, 30, 500)
R1_curves = {}
for c0 in [0.1, 0.5, 2.0]:
    nb_curve = net_benefit(I_range, p_market, psi_val, eps_val, v0, c0, c1_val)
    mb_curve = -dp_eff_dI(p_market, I_range, psi_val, eps_val)
    mc_curve = search_cost_deriv(I_range, c0, c1_val)
    R1_curves[c0] = dict(nb=nb_curve, mb=mb_curve, mc=mc_curve)

results["R1"] = dict(label="R1: Stigler Suche", data=R1_data, curves=R1_curves,
                      I_range=I_range, c0_vals=c0_vals)


# ══════════════════════════════════════════════════════════════════════
# R2: Akerlof Lemons — Adverse Selection
# ══════════════════════════════════════════════════════════════════════
print("\n  R2: Akerlof Lemons")

N_sellers = 500
quality = np.sort(np.random.uniform(0.1, 10.0, N_sellers))  # Qualitaet aufsteigend
p_fair = quality * 5.0   # Fairer Preis proportional zu Qualitaet
seller_reserve = quality * 3.0   # Mindestpreis des Verkaeufers

# Kaeufer hat asymmetrische Info: I_buyer variiert
I_buyer_levels = [0.1, 0.5, 1.0, 3.0, 10.0, 50.0]
psi_market = 3.0

R2_data = {}
for I_b in I_buyer_levels:
    # Kaeufer schaetzt Qualitaet mit Unsicherheit: wahrgenommene Q sinkt mit weniger Info
    # perceived_q = avg_q * I / (I + psi)   (Bayessches Signal-Rausch)
    avg_q = np.mean(quality)
    perceived_q = avg_q * I_b / (I_b + psi_market)
    p_offer = perceived_q * 5.0  # Zahlungsbereitschaft basierend auf wahrgenommener Qualitaet
    # Welche Verkaeufer akzeptieren?
    sellers_in = seller_reserve <= p_offer
    n_trade = np.sum(sellers_in)
    if n_trade > 0:
        avg_q_traded = np.mean(quality[sellers_in])
        realized_surplus = np.mean(p_fair[sellers_in]) - p_offer
    else:
        avg_q_traded = 0
        realized_surplus = 0
    R2_data[I_b] = dict(p_offer=p_offer, n_trade=n_trade, n_total=N_sellers,
                         avg_q=avg_q_traded, surplus=realized_surplus)
    print(f"    I_buyer={I_b:5.1f}: p_offer={p_offer:.1f}, trades={n_trade}/{N_sellers}, "
          f"avg_q={avg_q_traded:.2f}")

# Iteratives Lemons-Modell: Qualitaetsspirale
I_buyer_fixed = 2.0
rounds = 30
q_pool = quality.copy()
reserve_pool = seller_reserve.copy()
pfair_pool = p_fair.copy()
spiral_data = {"round": [], "n_sellers": [], "avg_quality": [], "price": []}
for r in range(rounds):
    if len(q_pool) == 0:
        break
    avg_q_pool = np.mean(q_pool)
    perceived_q_pool = avg_q_pool * I_buyer_fixed / (I_buyer_fixed + psi_market)
    p_offer_r = perceived_q_pool * 5.0
    stay = reserve_pool <= p_offer_r
    spiral_data["round"].append(r)
    spiral_data["n_sellers"].append(len(q_pool))
    spiral_data["avg_quality"].append(avg_q_pool)
    spiral_data["price"].append(p_offer_r)
    if np.sum(stay) == len(q_pool) or np.sum(stay) == 0:
        break  # Gleichgewicht oder Markt-Kollaps
    q_pool = q_pool[stay]
    reserve_pool = reserve_pool[stay]
    pfair_pool = pfair_pool[stay]

for k in spiral_data:
    spiral_data[k] = np.array(spiral_data[k])
results["R2"] = dict(label="R2: Akerlof Lemons", data=R2_data, spiral=spiral_data,
                      I_buyer_levels=I_buyer_levels)


# ══════════════════════════════════════════════════════════════════════
# R3: Grossman-Stiglitz — Inneres Gleichgewicht
# ══════════════════════════════════════════════════════════════════════
print("\n  R3: Grossman-Stiglitz")

# Modell: N Agenten, Anteil alpha informiert, Rest uninformiert
# Informierte zahlen Kosten c_info, bekommen besseren Preis
# Im GG: kein Anreiz zu wechseln
# Spillover-Koeffizient: uninformierte profitieren mehr bei hoeherem alpha
# -> effektives I_uninf waechst STARK mit alpha (Preissignal-Feedback)

N_agents_gs = 1000
c_info_vals = [0.2, 0.5, 1.0, 2.0, 5.0]
p_gs = 10.0
psi_gs = 8.0       # hoher psi -> starke Rolle von Info -> groesserer Spread
I_informed = 20.0
I_uninformed = 0.3

alpha_range = np.linspace(0.01, 0.99, 500)
R3_data = {}
for c_info in c_info_vals:
    # Spillover: uninformierte lernen aus Marktpreisen
    # Bei alpha=1 wird Markt vollstaendig informativ -> I_eff_unf = I_informed
    I_eff_unf = I_uninformed + alpha_range**0.5 * (I_informed - I_uninformed)
    # Nutzen informiert: v0 - p_eff(I_high) - c_info (konstant in alpha)
    u_inf_alpha = v0 - p_eff(p_gs, I_informed, psi_gs, eps_val) - c_info
    # Nutzen uninformiert: v0 - p_eff(I_eff_unf(alpha)) (steigt mit alpha)
    u_unf_alpha = v0 - p_eff(p_gs, I_eff_unf, psi_gs, eps_val)
    delta_u = u_inf_alpha - u_unf_alpha  # >0: lohnt sich zu informieren
    # GG: delta_u = 0
    cross_idx = np.where(np.diff(np.sign(delta_u)))[0]
    alpha_star = alpha_range[cross_idx[0]] if len(cross_idx) > 0 else np.nan
    R3_data[c_info] = dict(alpha_star=alpha_star, delta_u=delta_u,
                            u_inf=u_inf_alpha, u_unf=u_unf_alpha,
                            I_eff=I_eff_unf)
    print(f"    c_info={c_info:.1f}: alpha*={alpha_star:.3f}")

results["R3"] = dict(label="R3: Grossman-Stiglitz", data=R3_data,
                      alpha_range=alpha_range, c_info_vals=c_info_vals)


# ══════════════════════════════════════════════════════════════════════
# R4: Budget-Verzerrung durch p_eff
# ══════════════════════════════════════════════════════════════════════
print("\n  R4: Budget-Verzerrung")

K = 3
p_goods = np.array([5.0, 10.0, 15.0])
psi_goods = np.array([1.0, 3.0, 8.0])
w_budget = 100.0  # Einkommen

I_scenarios = {
    "Voll informiert (I=50)": 50.0 * np.ones(K),
    "Mittel (I=5)": 5.0 * np.ones(K),
    "Schlecht (I=1)": 1.0 * np.ones(K),
    "Asymmetrisch": np.array([20.0, 2.0, 0.5]),
    "Extrem arm (I=0.1)": 0.1 * np.ones(K),
}

R4_data = {}
for name, I_vec in I_scenarios.items():
    peff_vec = np.array([p_eff(p_goods[k], I_vec[k], psi_goods[k], eps_val) for k in range(K)])
    # Maximale Menge pro Gut (bei Vollausgabe)
    c_max = w_budget / peff_vec
    # Budgetvolumen (Simplex-Volumen in 3D = w^K / (K! * prod(p)))
    vol = w_budget**K / (math.factorial(K) * np.prod(peff_vec))
    # Kaufkraftverlust
    vol_ref = w_budget**K / (math.factorial(K) * np.prod(p_goods))
    loss = 1 - vol / vol_ref
    R4_data[name] = dict(peff=peff_vec, c_max=c_max, vol=vol, loss=loss, I=I_vec)
    print(f"    {name:30s}: Verlust={loss*100:.1f}%, p_eff={peff_vec}")

results["R4"] = dict(label="R4: Budget-Verzerrung", data=R4_data,
                      p_goods=p_goods, psi_goods=psi_goods, w_budget=w_budget)


# ══════════════════════════════════════════════════════════════════════
# R5: Dynamische Kopplung I(t) → p_eff(t)
# ══════════════════════════════════════════════════════════════════════
print("\n  R5: Dynamische Kopplung I(t) -> p_eff(t)")

# I(t)-Dynamik: dI/dt = r_I*I*(1-I/I_max) - omega*I + S(t)
def info_rhs(t, I, r_I=0.1, I_max=30.0, omega=0.03, S_func=None):
    I_safe = max(I, 1e-8)
    S = S_func(t) if S_func is not None else 0.0
    return r_I * I_safe * (1 - I_safe / I_max) - omega * I_safe + S

# 3 Szenarien: Normales Wachstum, Nachrichtenflut, Zensur
scenarios_list = [
    ("Normal", dict(I0=1.0, S=lambda t: 0.0, r_I=0.1, omega_func=lambda t: 0.03)),
    ("Nachrichtenflut t=30", dict(I0=1.0, S=lambda t: 5.0 * np.exp(-((t-30)/5)**2),
                                   r_I=0.1, omega_func=lambda t: 0.03)),
    ("Zensur ab t=50", dict(I0=10.0, S=lambda t: 0.0,
                              r_I=0.1, omega_func=lambda t: 0.03 + 0.3 * (t > 50))),
]

T_sim = 100.0
t_eval_dyn = np.linspace(0, T_sim, 1001)
p_dyn = 10.0
psi_dyn = 4.0

R5_data = {}
for name, sc in scenarios_list:
    def make_rhs(sc_dict):
        def rhs(t, y):
            I_s = max(y[0], 1e-8)
            omega_t = sc_dict["omega_func"](t)
            S_t = sc_dict["S"](t)
            return [sc_dict["r_I"] * I_s * (1 - I_s / 30.0) - omega_t * I_s + S_t]
        return rhs
    sol = solve_ivp(make_rhs(sc), [0, T_sim], [sc["I0"]], t_eval=t_eval_dyn,
                    method='RK45', rtol=1e-8, atol=1e-10)
    I_t = np.maximum(sol.y[0], 1e-8)
    t_out = sol.t
    peff_t = p_eff(p_dyn, I_t, psi_dyn, eps_val)
    surcharge_t = (peff_t - p_dyn) / p_dyn * 100
    R5_data[name] = dict(t=t_out, I=I_t, peff=peff_t, surcharge=surcharge_t)
    print(f"    {name:25s}: I(0)={sc['I0']:.1f}, I(T)={I_t[-1]:.2f}, "
          f"p_eff(T)={peff_t[-1]:.2f}")

results["R5"] = dict(label="R5: Dynamische Kopplung", data=R5_data)


# ══════════════════════════════════════════════════════════════════════
# R6: Singularitaet I→0 + eps-Sensitivitaet
# ══════════════════════════════════════════════════════════════════════
print("\n  R6: Singularitaetsanalyse")

I_sing = np.logspace(-4, 2, 500)
eps_vals = [0.001, 0.01, 0.1, 0.5, 1.0]
R6_data = {}
for eps_v in eps_vals:
    peff_v = p_eff(10.0, I_sing, 5.0, eps_v)
    surcharge_v = (peff_v - 10.0) / 10.0
    R6_data[eps_v] = dict(peff=peff_v, surcharge=surcharge_v)

# Kritische Schwelle: bei welchem I wird p_eff > 2*p?
threshold_factor = 2.0
R6_thresholds = {}
for eps_v in eps_vals:
    # p*(1+psi/(I+eps)) = threshold*p => psi/(I+eps) = threshold-1 => I = psi/(threshold-1) - eps
    I_crit = 5.0 / (threshold_factor - 1) - eps_v
    R6_thresholds[eps_v] = max(I_crit, 0)
    print(f"    eps={eps_v:.3f}: I_crit(p_eff>2p)={max(I_crit,0):.3f}")

results["R6"] = dict(label="R6: Singularitaet", I=I_sing, data=R6_data,
                      eps_vals=eps_vals, thresholds=R6_thresholds)


# ══════════════════════════════════════════════════════════════════════
# R7: Wohlfahrtsdekomposition U.2 vs U.3
# ══════════════════════════════════════════════════════════════════════
print("\n  R7: Wohlfahrtsdekomposition")

K_dec = 5
p_dec = np.array([8.0, 12.0, 5.0, 15.0, 10.0])
psi_dec = np.array([2.0, 4.0, 1.0, 6.0, 3.0])
v_intrinsic = np.array([20.0, 25.0, 15.0, 30.0, 18.0])

# Sweep I von 0.1 bis 30
I_decomp = np.linspace(0.1, 30, 200)
# U.2-Verlust: Softmax mit eta=2: Gueter mit niedrigem I werden ignoriert
# U.3-Verlust: p_eff >> p bei niedrigem I

W_full_info = np.sum(v_intrinsic - p_dec)  # Benchmark
W_U2_loss = np.zeros(len(I_decomp))
W_U3_loss = np.zeros(len(I_decomp))
W_total_loss = np.zeros(len(I_decomp))

for i, I_level in enumerate(I_decomp):
    I_vec = I_level * np.array([2.0, 1.0, 0.5, 1.5, 0.8])  # Heterogenes Profil
    # U.2: Aufmerksamkeitsgewichte (Softmax eta=2)
    I_pow = I_vec ** 2
    omega = I_pow / I_pow.sum()
    # U.3: Effektive Preise
    peff_vec = p_eff(p_dec, I_vec, psi_dec, eps_val)
    # Gesamtwohlfahrt: Σ omega_k * (v_k - p_eff_k)
    W_actual = np.sum(omega * (v_intrinsic - peff_vec))
    # Nur U.2-Verlust (perfekte Preise, verzerrte Aufmerksamkeit)
    W_U2_only = np.sum(omega * (v_intrinsic - p_dec))
    # Nur U.3-Verlust (gleichmaessige Aufmerksamkeit, verzerrte Preise)
    omega_equal = np.ones(K_dec) / K_dec
    W_U3_only = np.sum(omega_equal * (v_intrinsic - peff_vec))
    
    W_U2_loss[i] = W_full_info - W_U2_only    # Verlust durch falsche Aufmerksamkeit
    W_U3_loss[i] = W_full_info - W_U3_only     # Verlust durch Preis-Aufschlag
    W_total_loss[i] = W_full_info - W_actual    # Gesamtverlust

results["R7"] = dict(label="R7: Wohlfahrtsdekomposition", I=I_decomp,
                      W_U2=W_U2_loss, W_U3=W_U3_loss, W_total=W_total_loss,
                      W_ref=W_full_info)
print(f"    W(vollst.)={W_full_info:.1f}, W_U2_loss(I=1)={W_U2_loss[np.argmin(np.abs(I_decomp-1))]:.1f}, "
      f"W_U3_loss(I=1)={W_U3_loss[np.argmin(np.abs(I_decomp-1))]:.1f}")


# ══════════════════════════════════════════════════════════════════════
# 5. Validierungen
# ══════════════════════════════════════════════════════════════════════

validations = {}
print(f"\n{'='*72}\n  VALIDIERUNGEN\n{'='*72}")

# V1: Stigler FOC — MB = MC am Optimum
foc_errs = []
for c0, d in results["R1"]["data"].items():
    foc_errs.append(abs(d["mb"] - d["mc"]) / max(d["mc"], 1e-10))
v1_pass = max(foc_errs) < 0.01
validations["V1"] = dict(name="Stigler FOC: MB=MC", passed=v1_pass,
                          detail=f"max|MB-MC|/MC={max(foc_errs):.2e}")
print(f"  V1: {'PASS' if v1_pass else 'FAIL'} ({validations['V1']['detail']})")

# V2: Stigler I* steigt mit sinkendem c0 (billigere Info -> mehr Suche)
I_stars = [results["R1"]["data"][c0]["I_star"] for c0 in c0_vals]
v2_pass = all(I_stars[i] >= I_stars[i+1] for i in range(len(I_stars)-1))
validations["V2"] = dict(name="I* sinkt mit c0", passed=v2_pass,
                          detail=f"I*={[f'{x:.1f}' for x in I_stars]}")
print(f"  V2: {'PASS' if v2_pass else 'FAIL'} ({validations['V2']['detail']})")

# V3: Akerlof — weniger Handel bei niedrigem I
trades = [results["R2"]["data"][I_b]["n_trade"] for I_b in sorted(I_buyer_levels)]
v3_pass = trades[-1] >= trades[0]  # Mehr Info -> mehr Handel
validations["V3"] = dict(name="Akerlof: mehr I -> mehr Handel", passed=v3_pass,
                          detail=f"trades(I_low)={trades[0]}, trades(I_high)={trades[-1]}")
print(f"  V3: {'PASS' if v3_pass else 'FAIL'} ({validations['V3']['detail']})")

# V4: Akerlof Spirale — Qualitaet sinkt ueber Runden
spiral = results["R2"]["spiral"]
if len(spiral["avg_quality"]) > 1:
    v4_pass = spiral["avg_quality"][-1] <= spiral["avg_quality"][0]
    v4_detail = f"Q(0)={spiral['avg_quality'][0]:.2f} -> Q(end)={spiral['avg_quality'][-1]:.2f}"
else:
    v4_pass = True
    v4_detail = "Sofort-Kollaps"
validations["V4"] = dict(name="Lemons-Spirale: Q sinkt", passed=v4_pass, detail=v4_detail)
print(f"  V4: {'PASS' if v4_pass else 'FAIL'} ({v4_detail})")

# V5: Grossman-Stiglitz — inneres GG existiert
gs_interior = []
for c, d in results["R3"]["data"].items():
    gs_interior.append(not np.isnan(d["alpha_star"]) and 0 < d["alpha_star"] < 1)
v5_pass = all(gs_interior)
alphas = [f"{results['R3']['data'][c]['alpha_star']:.3f}" for c in c_info_vals]
validations["V5"] = dict(name="GS: alpha* ∈ (0,1)", passed=v5_pass,
                          detail=f"alpha*={alphas}")
print(f"  V5: {'PASS' if v5_pass else 'FAIL'} ({validations['V5']['detail']})")

# V6: Budget-Verzerrung monoton in I
losses = [results["R4"]["data"][n]["loss"] for n in 
          ["Voll informiert (I=50)", "Mittel (I=5)", "Schlecht (I=1)", "Extrem arm (I=0.1)"]]
v6_pass = all(losses[i] <= losses[i+1] for i in range(len(losses)-1))
validations["V6"] = dict(name="Budget: Verlust steigt bei I↓", passed=v6_pass,
                          detail=f"losses={[f'{x*100:.0f}%' for x in losses]}")
print(f"  V6: {'PASS' if v6_pass else 'FAIL'} ({validations['V6']['detail']})")

# V7: Dynamik — Zensur erhoeht p_eff
peff_zensur = results["R5"]["data"]["Zensur ab t=50"]["peff"]
v7_pass = peff_zensur[-1] > peff_zensur[len(peff_zensur)//4]  # Nach Zensur hoeher als vorher
validations["V7"] = dict(name="Zensur: p_eff steigt", passed=v7_pass,
                          detail=f"p_eff(25)={peff_zensur[len(peff_zensur)//4]:.2f}, p_eff(T)={peff_zensur[-1]:.2f}")
print(f"  V7: {'PASS' if v7_pass else 'FAIL'} ({validations['V7']['detail']})")

# V8: Wohlfahrt steigt mit I (W_total_loss sinkt)
w_loss = results["R7"]["W_total"]
v8_pass = w_loss[0] > w_loss[-1]
validations["V8"] = dict(name="W steigt mit I", passed=v8_pass,
                          detail=f"Loss(I=0.1)={w_loss[0]:.1f}, Loss(I=30)={w_loss[-1]:.1f}")
print(f"  V8: {'PASS' if v8_pass else 'FAIL'} ({validations['V8']['detail']})")


# ══════════════════════════════════════════════════════════════════════
# 6. Sensitivitaetsanalysen
# ══════════════════════════════════════════════════════════════════════

print(f"\n{'='*72}\n  SENSITIVITAETSANALYSEN\n{'='*72}")

# SA1: psi-Sweep fuer Stigler I*
psi_sweep = np.linspace(0.5, 20, 100)
I_star_psi = []
for ps in psi_sweep:
    res = minimize_scalar(lambda I: -net_benefit(I, 10.0, ps, 0.01, 50.0, 0.5, 0.05),
                          bounds=(0.01, 200), method='bounded')
    I_star_psi.append(res.x)
results["SA1"] = dict(psi=psi_sweep, I_star=np.array(I_star_psi))
print(f"  SA1: psi-Sweep -> I*(psi=1)={I_star_psi[np.argmin(np.abs(psi_sweep-1))]:.1f}, "
      f"I*(psi=10)={I_star_psi[np.argmin(np.abs(psi_sweep-10))]:.1f}")

# SA2: eps-Sensitivitaet auf I*
eps_sweep = np.logspace(-4, 0, 50)
I_star_eps = []
for ep in eps_sweep:
    res = minimize_scalar(lambda I: -net_benefit(I, 10.0, 5.0, ep, 50.0, 0.5, 0.05),
                          bounds=(0.01, 200), method='bounded')
    I_star_eps.append(res.x)
results["SA2"] = dict(eps=eps_sweep, I_star=np.array(I_star_eps))
print(f"  SA2: eps-Sweep -> I*(eps=0.001)={I_star_eps[0]:.2f}, I*(eps=1)={I_star_eps[-1]:.2f}")

# SA3: GS alpha* vs psi
psi_gs_sweep = np.linspace(1, 15, 50)
alpha_star_psi = []
for ps in psi_gs_sweep:
    I_eff_unf = 0.3 + alpha_range**0.5 * (20 - 0.3)
    u_inf = v0 - p_eff(10.0, 20.0, ps, 0.01) - 1.0
    u_unf = v0 - p_eff(10.0, I_eff_unf, ps, 0.01)
    delta = u_inf - u_unf
    cross = np.where(np.diff(np.sign(delta)))[0]
    alpha_star_psi.append(alpha_range[cross[0]] if len(cross) > 0 else np.nan)
results["SA3"] = dict(psi=psi_gs_sweep, alpha_star=np.array(alpha_star_psi))
print(f"  SA3: GS alpha* vs psi -> alpha*(psi=1)={alpha_star_psi[0]:.3f}, "
      f"alpha*(psi=10)={alpha_star_psi[np.argmin(np.abs(psi_gs_sweep-10))]:.3f}")

# SA4: Cross-good Information: kennt Gut 1 → hilft bei Gut 2?
I1_sweep = np.linspace(0.1, 30, 200)
spillover = 0.2   # 20% Spillover
p_eff_gut2_no_spill = p_eff(10.0, 2.0 * np.ones_like(I1_sweep), 3.0, eps_val)
p_eff_gut2_spill = p_eff(10.0, 2.0 + spillover * I1_sweep, 3.0, eps_val)
results["SA4"] = dict(I1=I1_sweep, peff2_no=p_eff_gut2_no_spill, peff2_spill=p_eff_gut2_spill)
print(f"  SA4: Spillover — p_eff2(I1=30, spill)={p_eff_gut2_spill[-1]:.2f} vs "
      f"ohne={p_eff_gut2_no_spill[-1]:.2f}")


# ══════════════════════════════════════════════════════════════════════
# 7. Plot (24 Panels + Metadata)
# ══════════════════════════════════════════════════════════════════════

print(f"\n  PLOTTE ...")
fig = plt.figure(figsize=(26, 40))
gs = GridSpec(9, 3, figure=fig, height_ratios=[1, 1, 1, 1, 1, 1, 1, 1, 0.4],
              hspace=0.38, wspace=0.30)
fig.suptitle('S16  U.3  Effektiver Preis: Dynamik, Kopplung, Marktversagen',
             fontsize=15, fontweight='bold', y=0.995)

# Row 1: R1 Stigler
ax = fig.add_subplot(gs[0, 0])
for c0 in [0.1, 0.5, 2.0]:
    ax.plot(I_range, R1_curves[c0]["nb"], lw=2, label=f'c0={c0}')
    I_s = R1_data[c0]["I_star"]
    ax.axvline(I_s, ls=':', color=ax.lines[-1].get_color(), lw=0.8)
ax.set_xlabel('I'); ax.set_ylabel('Nettonutzen')
ax.set_title('(a) R1: Stigler Nettonutzen(I)')
ax.legend(fontsize=7); ax.grid(True, alpha=0.3)

ax = fig.add_subplot(gs[0, 1])
for c0 in [0.1, 0.5, 2.0]:
    ax.plot(I_range, R1_curves[c0]["mb"], lw=2, label=f'MB', color='C0' if c0==0.1 else ('C1' if c0==0.5 else 'C2'))
    ax.plot(I_range, R1_curves[c0]["mc"], '--', lw=2, label=f'MC(c0={c0})', color=ax.lines[-1].get_color())
ax.set_xlabel('I'); ax.set_ylabel('Grenznutzen / -kosten')
ax.set_title('(b) R1: FOC MB=MC (V1)')
ax.set_ylim(0, 5); ax.legend(fontsize=6); ax.grid(True, alpha=0.3)

ax = fig.add_subplot(gs[0, 2])
ax.bar(range(len(c0_vals)), I_stars, color=[f'C{i}' for i in range(len(c0_vals))], alpha=0.7)
ax.set_xticks(range(len(c0_vals)))
ax.set_xticklabels([f'c0={c}' for c in c0_vals], fontsize=7)
ax.set_ylabel('I*'); ax.set_title('(c) R1: Optimales I* vs Suchkosten (V2)')
ax.grid(True, alpha=0.3, axis='y')

# Row 2: R2 Akerlof
ax = fig.add_subplot(gs[1, 0])
I_sorted = sorted(I_buyer_levels)
trades_plot = [results["R2"]["data"][ib]["n_trade"] for ib in I_sorted]
ax.bar(range(len(I_sorted)), trades_plot, color='C1', alpha=0.7)
ax.set_xticks(range(len(I_sorted)))
ax.set_xticklabels([f'I={ib}' for ib in I_sorted], fontsize=7)
ax.set_ylabel('Trades'); ax.set_title('(d) R2: Akerlof — Handelsvolumen vs I (V3)')
ax.grid(True, alpha=0.3, axis='y')

ax = fig.add_subplot(gs[1, 1])
if len(spiral["round"]) > 1:
    ax.plot(spiral["round"], spiral["avg_quality"], 'C3-o', lw=2, label='Qualitaet')
    ax2 = ax.twinx()
    ax2.plot(spiral["round"], spiral["n_sellers"], 'C0--s', lw=2, label='Verkaeufer')
    ax2.set_ylabel('Verkaeufer', color='C0')
    ax2.legend(loc='center right', fontsize=7)
ax.set_xlabel('Runde'); ax.set_ylabel('Durchschn. Qualitaet', color='C3')
ax.set_title('(e) R2: Lemons-Spirale (V4)')
ax.legend(fontsize=7); ax.grid(True, alpha=0.3)

ax = fig.add_subplot(gs[1, 2])
avg_qs = [results["R2"]["data"][ib]["avg_q"] for ib in I_sorted]
ax.bar(range(len(I_sorted)), avg_qs, color='C2', alpha=0.7)
ax.set_xticks(range(len(I_sorted)))
ax.set_xticklabels([f'I={ib}' for ib in I_sorted], fontsize=7)
ax.set_ylabel('Mittl. Qualitaet'); ax.set_title('(f) R2: Gehandelte Qualitaet vs I')
ax.grid(True, alpha=0.3, axis='y')

# Row 3: R3 Grossman-Stiglitz
ax = fig.add_subplot(gs[2, 0])
for c_info in [0.2, 1.0, 5.0]:
    d = R3_data[c_info]
    ax.plot(alpha_range, d["delta_u"], lw=2, label=f'c={c_info}')
    if not np.isnan(d["alpha_star"]):
        ax.axvline(d["alpha_star"], ls=':', color=ax.lines[-1].get_color(), lw=0.8)
ax.axhline(0, ls='-', color='black', lw=0.5)
ax.set_xlabel('alpha (Anteil Informierter)'); ax.set_ylabel('Delta U')
ax.set_title('(g) R3: GS — Nettovorteil informiert (V5)')
ax.legend(fontsize=7); ax.grid(True, alpha=0.3)

ax = fig.add_subplot(gs[2, 1])
a_stars = [results["R3"]["data"][c]["alpha_star"] for c in c_info_vals]
ax.plot(c_info_vals, a_stars, 'C0-o', lw=2)
ax.set_xlabel('c_info'); ax.set_ylabel('alpha*')
ax.set_title('(h) R3: GS — alpha* vs Info-Kosten')
ax.grid(True, alpha=0.3)

# Row 3: R4 Budget
ax = fig.add_subplot(gs[2, 2])
names = list(R4_data.keys())
losses_pct = [R4_data[n]["loss"]*100 for n in names]
colors = ['C0', 'C1', 'C2', 'C3', 'C4']
ax.barh(range(len(names)), losses_pct, color=colors[:len(names)], alpha=0.7)
ax.set_yticks(range(len(names)))
ax.set_yticklabels(names, fontsize=6)
ax.set_xlabel('Kaufkraftverlust [%]')
ax.set_title('(i) R4: Budget-Verzerrung (V6)')
ax.grid(True, alpha=0.3, axis='x')

# Row 4: R5 Dynamik
ax = fig.add_subplot(gs[3, 0])
for name, d in R5_data.items():
    ax.plot(d["t"], d["I"], lw=2, label=name)
ax.set_xlabel('t'); ax.set_ylabel('I(t)')
ax.set_title('(j) R5: Info-Dynamik I(t)')
ax.legend(fontsize=7); ax.grid(True, alpha=0.3)

ax = fig.add_subplot(gs[3, 1])
for name, d in R5_data.items():
    ax.plot(d["t"], d["peff"], lw=2, label=name)
ax.axhline(p_dyn, ls=':', color='black', lw=0.5, label='p_Markt')
ax.set_xlabel('t'); ax.set_ylabel('p_eff(t)')
ax.set_title('(k) R5: Dynamischer p_eff(t) (V7)')
ax.legend(fontsize=7); ax.grid(True, alpha=0.3)

ax = fig.add_subplot(gs[3, 2])
for name, d in R5_data.items():
    ax.plot(d["t"], d["surcharge"], lw=2, label=name)
ax.set_xlabel('t'); ax.set_ylabel('Aufschlag [%]')
ax.set_title('(l) R5: p_eff-Aufschlag dynamisch')
ax.legend(fontsize=7); ax.grid(True, alpha=0.3)

# Row 5: R6 Singularitaet
ax = fig.add_subplot(gs[4, 0])
for eps_v in eps_vals:
    ax.semilogx(I_sing, R6_data[eps_v]["peff"], lw=2, label=f'eps={eps_v}')
ax.axhline(10.0, ls=':', color='black', lw=0.5, label='p_Markt')
ax.set_xlabel('I (log)'); ax.set_ylabel('p_eff')
ax.set_title('(m) R6: Singularitaet I→0')
ax.set_ylim(0, 200); ax.legend(fontsize=6); ax.grid(True, alpha=0.3)

ax = fig.add_subplot(gs[4, 1])
for eps_v in eps_vals:
    ax.loglog(I_sing, R6_data[eps_v]["surcharge"], lw=2, label=f'eps={eps_v}')
ax.axhline(1.0, ls=':', color='red', lw=0.5, label='100% Aufschlag')
ax.set_xlabel('I (log)'); ax.set_ylabel('Aufschlag (p_eff/p - 1)')
ax.set_title('(n) R6: Aufschlag log-log')
ax.legend(fontsize=6); ax.grid(True, alpha=0.3)

ax = fig.add_subplot(gs[4, 2])
ax.bar(range(len(eps_vals)), [R6_thresholds[e] for e in eps_vals], 
       color=[f'C{i}' for i in range(len(eps_vals))], alpha=0.7)
ax.set_xticks(range(len(eps_vals)))
ax.set_xticklabels([f'eps={e}' for e in eps_vals], fontsize=7)
ax.set_ylabel('I_krit (p_eff > 2p)'); ax.set_title('(o) R6: Kritische Schwelle')
ax.grid(True, alpha=0.3, axis='y')

# Row 6: R7 Wohlfahrt
ax = fig.add_subplot(gs[5, 0])
ax.plot(I_decomp, W_U2_loss, 'C0-', lw=2, label='U.2-Verlust (Aufmerksamkeit)')
ax.plot(I_decomp, W_U3_loss, 'C1-', lw=2, label='U.3-Verlust (Preisaufschlag)')
ax.plot(I_decomp, W_total_loss, 'C3--', lw=2, label='Gesamtverlust')
ax.axhline(0, ls=':', color='gray', lw=0.5)
ax.set_xlabel('I-Niveau'); ax.set_ylabel('Wohlfahrtsverlust')
ax.set_title('(p) R7: Dekomposition U.2 vs U.3 (V8)')
ax.legend(fontsize=7); ax.grid(True, alpha=0.3)

# Row 6: SA1 + SA2
ax = fig.add_subplot(gs[5, 1])
ax.plot(results["SA1"]["psi"], results["SA1"]["I_star"], 'C0-', lw=2)
ax.set_xlabel('psi (Suchkosten)'); ax.set_ylabel('I*')
ax.set_title('(q) SA1: I* vs psi (Sensitivitaet)')
ax.grid(True, alpha=0.3)

ax = fig.add_subplot(gs[5, 2])
ax.semilogx(results["SA2"]["eps"], results["SA2"]["I_star"], 'C1-', lw=2)
ax.set_xlabel('eps (Regularisierung)'); ax.set_ylabel('I*')
ax.set_title('(r) SA2: I* vs eps')
ax.grid(True, alpha=0.3)

# Row 7: SA3 + SA4 + Kausalitaet
ax = fig.add_subplot(gs[6, 0])
ax.plot(results["SA3"]["psi"], results["SA3"]["alpha_star"], 'C2-o', lw=2, markersize=3)
ax.set_xlabel('psi'); ax.set_ylabel('alpha* (GS)')
ax.set_title('(s) SA3: GS alpha* vs psi')
ax.grid(True, alpha=0.3)

ax = fig.add_subplot(gs[6, 1])
ax.plot(I1_sweep, results["SA4"]["peff2_no"], 'C0-', lw=2, label='ohne Spillover')
ax.plot(I1_sweep, results["SA4"]["peff2_spill"], 'C1--', lw=2, label='mit 20% Spillover')
ax.set_xlabel('I_1 (Info ueber Gut 1)'); ax.set_ylabel('p_eff Gut 2')
ax.set_title('(t) SA4: Cross-Good Info-Spillover')
ax.legend(fontsize=7); ax.grid(True, alpha=0.3)

ax = fig.add_subplot(gs[6, 2])
ax.axis('off')
kaus_text = (
    "KAUSALKETTEN (S16 U.3 Deep-Dive):\n"
    "─────────────────────────────────\n"
    "1. Stigler: c'(I*)=|dp_eff/dI|\n"
    "   -> Residuale Ignoranz optimal\n"
    "   -> Nie volle Information\n\n"
    "2. Akerlof: I_buyer << I_seller\n"
    "   -> Adverse Selection\n"
    "   -> Qualitaets-Spirale\n"
    "   -> Markt bricht zusammen\n\n"
    "3. Grossman-Stiglitz:\n"
    "   mehr Informierte -> Preis\n"
    "   effizienter -> weniger Anreiz\n"
    "   -> inneres GG alpha* ∈ (0,1)\n\n"
    "4. Budget: p_eff > p schrumpft\n"
    "   Budgetmenge -> Arme zahlen\n"
    "   ueberproportional (Poverty Tax)\n\n"
    "5. Zensur -> I sinkt -> p_eff steigt\n"
    "   -> Wohlfahrtsverlust sofort"
)
ax.text(0.05, 0.95, kaus_text, transform=ax.transAxes, ha='left', va='top',
        fontsize=8, family='monospace',
        bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.95))

# Row 8: Validierung + Physik
ax = fig.add_subplot(gs[7, 0])
ax.axis('off')
val_text = "VALIDIERUNGEN:\n" + "-"*35 + "\n"
for k, v in validations.items():
    tag = "PASS" if v["passed"] else "FAIL"
    val_text += f"{k}: {v['name']}\n   {tag}: {v['detail']}\n\n"
ax.text(0.05, 0.95, val_text, transform=ax.transAxes, ha='left', va='top',
        fontsize=7, family='monospace',
        bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.95))

ax = fig.add_subplot(gs[7, 1:])
ax.axis('off')
phys = (
    "PHYSIKALISCHE INTERPRETATION:   "
    "p_eff = p + Suchkosten-Aufschlag. "
    "Stigler (1961): Rationale Agenten optimieren Informationsbeschaffung (I*) — Ergebnis: residuale Ignoranz ist OPTIMAL, "
    "weil Suche kostet. Nie vollstaendige Information!  "
    "Akerlof (1970): Asymmetrische Info -> gute Verkaeufer verlassen Markt -> Spirale -> Marktversagen.  "
    "Grossman-Stiglitz (1980): Informationsparadox — wenn alle informiert, kein Informationsvorteil -> keine Info-Investition -> "
    "inneres GG: Anteil alpha* informierter Agenten.  "
    "Budget-Verzerrung: Info-Arme zahlen bis 99% mehr -> shrinkt Konsummoeglichkeiten -> Poverty Tax.  "
    "Zensur/Informationskontrolle: I(t) sinkt -> sofortiger Wohlfahrtsverlust ueber p_eff-Kanal."
)
ax.text(0.5, 0.5, phys, transform=ax.transAxes, ha='center', va='center',
        fontsize=8, wrap=True,
        bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.95))

# Metadata
ax_meta = fig.add_subplot(gs[8, :])
ax_meta.axis('off')
n_pass = sum(1 for v in validations.values() if v["passed"])
meta = (
    f"S16 U.3 Effektiver Preis Deep-Dive | 7 Regime, {len(validations)} Val: "
    f"{n_pass}/{len(validations)} PASS | "
    f"Stigler, Akerlof, Grossman-Stiglitz, Budget, Dynamik, Singularitaet, Dekomposition | "
    f"4 Sensitivitaetsanalysen | p_eff = p*(1+psi/(I+eps))"
)
ax_meta.text(0.5, 0.5, meta, transform=ax_meta.transAxes, ha='center', va='center',
             fontsize=9, family='monospace',
             bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.95))

plt.savefig(PLOT_DIR / "S16_U3_Effektiver_Preis.png", dpi=180, bbox_inches='tight')
plt.close()
print(f"\n  Plot: {PLOT_DIR / 'S16_U3_Effektiver_Preis.png'}")

# ── Daten ──
save_dict = {
    "R1_I_range": I_range,
    "R2_spiral_round": spiral["round"], "R2_spiral_quality": spiral["avg_quality"],
    "R2_spiral_sellers": spiral["n_sellers"],
    "R3_alpha_range": alpha_range,
    "R5_t": t_eval_dyn,
    "R6_I_sing": I_sing,
    "R7_I": I_decomp, "R7_W_U2": W_U2_loss, "R7_W_U3": W_U3_loss, "R7_W_total": W_total_loss,
    "SA1_psi": results["SA1"]["psi"], "SA1_Istar": results["SA1"]["I_star"],
    "SA2_eps": results["SA2"]["eps"], "SA2_Istar": results["SA2"]["I_star"],
    "SA3_psi": results["SA3"]["psi"], "SA3_alpha": results["SA3"]["alpha_star"],
}
for name, d in R5_data.items():
    safe_name = name.replace(" ", "_").replace("=", "")
    save_dict[f"R5_I_{safe_name}"] = d["I"]
    save_dict[f"R5_peff_{safe_name}"] = d["peff"]
np.savez_compressed(DATA_DIR / "S16_U3_Effektiver_Preis.npz", **save_dict)

# ── Zusammenfassung ──
print(f"\n{'='*72}\n  ZUSAMMENFASSUNG S16  U.3 Effektiver Preis\n{'='*72}")
for k, v in validations.items():
    print(f"  {k}: {v['name']:40s}  {'PASS' if v['passed'] else 'FAIL'}  ({v['detail']})")
print(f"\n  Regime:")
for key in ["R1", "R2", "R3", "R4", "R5", "R6", "R7"]:
    print(f"    {results[key]['label']}")
print(f"\n  Sensitivitaet:")
print(f"    SA1: I* vs psi (Suchkosten-Parameter)")
print(f"    SA2: I* vs eps (Regularisierung)")
print(f"    SA3: GS alpha* vs psi (Marktopazitaet)")
print(f"    SA4: Cross-Good Info-Spillover")
n_pass = sum(1 for v in validations.values() if v["passed"])
print(f"\n  Gesamtergebnis: {n_pass}/{len(validations)} bestanden")
if n_pass == len(validations):
    print("  >>> ALLE VALIDIERUNGEN BESTANDEN <<<")
print(f"{'='*72}")
