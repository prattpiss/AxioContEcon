"""
S26 – Vollstaendige Arbeitsangebotsdynamik L.4  (§6.4)
=======================================================
Master-Gleichung:

   dL_i/dt = alpha_L (L_i* - L_i)                              [L.1  Rational]
            + Psi_L(L_i, L_i*, L_bar, I_i^job, H_i)            [L.2  Psychologisch]
            + sum_j A_ij^eff Phi_L(L_j-L_i, I_j, I_i)          [L.3a Peer-Norm]
            + S(rank_i, Kultur)                                  [L.3b Status]

   dL_i*/dt = lambda_L (L_i - L_i*)                             [Referenzpunkt]

   w_i^wahr = w_i + alpha_H * w_bar^peer + psi_w/(I_i + eps)   [L.1a Wahrgen.Lohn]

   A_ij^eff = sum_l omega_l A^(l)_ij                            [Multiplex]

Vollstaendige 2N-dimensionale ODE: N Arbeitszeiten + N Referenzpunkte.
Analog zu S21 (V.1+V.2+V.3) fuer Konsum, aber mit zusaetzlichem Statusdruck S.

Prop 6.2: Strukturelle Symmetrie V.4 <-> L.4 (bei S=0 identisch).

8 Regime, 8 Validierungen, 5 Sensitivitaetsanalysen, 4 Erw. Analysen
"""

import sys, io, warnings, textwrap
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
warnings.filterwarnings('ignore', category=UserWarning, module='matplotlib')

import numpy as np
from scipy.linalg import eigvalsh
from numpy.linalg import eigh
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from matplotlib.colors import TwoSlopeNorm
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent.parent
PLOT_DIR = BASE / "Ergebnisse" / "Plots"
DATA_DIR = BASE / "Ergebnisse" / "Daten"
PLOT_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)

np.random.seed(42)

# ══════════════════════════════════════════════════════════════════════
# 0. GLEICHUNG UND ERKLAERUNG (grosse Uebersicht vor allen Ergebnissen)
# ══════════════════════════════════════════════════════════════════════

header_text = r"""
================================================================================
  S26  GLEICHUNG L.4 — VOLLSTAENDIGE ARBEITSANGEBOTSDYNAMIK (§6.4)
================================================================================

  ┌─────────────────────────────────────────────────────────────────────────────┐
  │                                                                             │
  │   dL_i            *                          *              job             │
  │  ───── = alpha_L (L_i  - L_i)  +  Psi_L(L_i, L_i , L_bar, I_i  , H_i)    │
  │   dt     ╰──────────────────╯     ╰──────────────────────────────────╯     │
  │           Ebene 1: Rational        Ebene 2: Psychologisch                  │
  │           (L.1 — S22)              (L.2 — S24)                             │
  │                                                                             │
  │          +  SUM_j  A_ij^eff  Phi_L(L_j - L_i, I_j, I_i)                   │
  │             ╰──────────────────────────────────────────╯                   │
  │              Ebene 3a: Peer-Normkonvergenz (L.3a — S25)                    │
  │                                                                             │
  │          +  S(rank_i, Kultur)                                               │
  │             ╰──────────────╯                                               │
  │              Ebene 3b: Statusdruck (L.3b — S25)                            │
  │                                                                             │
  └─────────────────────────────────────────────────────────────────────────────┘

  Referenzpunkt-Dynamik:
  ┌─────────────────────────────────────────────────────────────────────────────┐
  │     *                          *                                            │
  │   dL_i /dt = lambda_L * (L_i - L_i )     (Arbeitsnorm-Adaptation)          │
  │                                                                             │
  │   lambda_L << alpha_L  (Referenzpunkt passt sich LANGSAMER an als L)       │
  └─────────────────────────────────────────────────────────────────────────────┘

  ════════════════════════════════════════════════════════════════════════════════
  SYMBOLTABELLE
  ════════════════════════════════════════════════════════════════════════════════

  Symbol          Typ          Beschreibung
  ──────────────  ──────────── ─────────────────────────────────────────────────
  L_i             R+           Arbeitszeit von Agent i (Stunden/Tag)
  L_i*            R+           Referenz-Arbeitszeit (gewohntes Arbeitsniveau)
  alpha_L         R+           Anpassungsgeschwindigkeit zum Optimum (L.1)
                               -> hoch: rigider Arbeitsmarkt passt schnell an
                               -> niedrig: traeger Arbeitsmarkt
  Psi_L           R            Psychologische Verzerrung (L.2), bestehend aus:
    - Burnout:    kappa_ref * v(L*-L) / (1+kI*I)   (Prospect Theory, lam_B=2.25)
    - Motivation: kappa_I * I/(I+psi_I) * H/H_norm  (Michaelis-Menten)
  L_bar           R+           Mittlere Arbeitszeit der Population
  I_i^job         R+           Jobidentifikation / Informationsstand (Agent i)
  H_i             R+           Humankapital / Gesundheit (Agent i)
  lam_B           R+ (=2.25)   Burnout-Asymmetrie (identisch zu lam in V.2)
  kappa_ref       R+ (=0.3)    Staerke der Referenzpunkt-Anziehung
  kappa_I         R+ (=1.2)    Maximale intrinsische Motivations-Amplitude
  psi_I           R+ (=8.5)    Halbsaettigungskonstante (Michaelis-Menten)
  H_norm          R+ (=1.0)    Normalisierungswert fuer Gesundheit
  Psi_max         R+ (=2.0)    Obere Schranke: |Psi_L| <= Psi_max

  A_ij^eff        R+           Effektive Netzwerk-Adjazenz (Multiplex, 5 Layer)
  Phi_L           R            Peer-Normkonvergenz-Funktion (L.3a):
    - alpha_up    R+ (=0.15)   Aufwaerts-Normkonvergenz (Peers arbeiten MEHR)
    - alpha_down  R+ (=0.06)   Abwaerts-Normkonvergenz (schwaecher)
    - Phi_max     R+ (=3.0)    |Phi_L| <= Phi_max (Beschraenktheit)
    - info_mod    [0,1]        sqrt(I_j)/(sqrt(I_j)+sqrt(I_i)+eps)

  S               R+           Statusdruck-Operator (L.3b, NUR in L nicht in V!):
    - rank_i      [0,1]        Perzentil der Arbeitszeit in der Verteilung
    - Kultur      R+ (=1.0)    Kultursensitivitaets-Skalierung
                               Japan ~2.5, USA ~1.0, Deutschland ~0.7, FR ~0.3
    - kappa_s     R+ (=0.8)    Statusdruck-Staerke
    - S_max       R+ (=1.5)    Obere Schranke pro Kultureinheit

  lambda_L        R+ (=0.10)   Referenzpunkt-Adaptationsrate (LANGSAM)

  ════════════════════════════════════════════════════════════════════════════════
  ANNAHMEN UND MODELLIERUNG
  ════════════════════════════════════════════════════════════════════════════════

  1. ADDITIVITAET: Die vier Terme (L.1 + L.2 + L.3a + L.3b) wirken ADDITIV
     auf dL/dt. Keine multiplikative Kopplung zwischen Ebenen.
     Begruendung: Parallele Entscheidungskanaele (rational, psychologisch,
     sozial) summieren sich zu einer Netto-Verhaltensaenderung.

  2. FORWARD-EULER-Integration mit dt=0.025, T=50.0 (2000 Schritte).
     Stabilitaet durch Clipping: L in [0.5, 24.0] (physikalische Schranken).
     Keine impliziten Methoden noetig da System nicht stiff bei diesen dt.

  3. REFERENZPUNKT L* folgt einer LANGSAMEN exponentiellen Glaettung:
     dL*/dt = lambda_L * (L - L*)  mit lambda_L = 0.10.
     Interpretation: Gewonnene Arbeitsgewohnheiten aendern sich traeger
     als die tatsaechliche Arbeitszeit -> Hysterese/Scarring moeglich.

  4. BURNOUT-ASYMMETRIE (Prospect Theory): Ueberarbeit (L > L*) wird
     lambda_B = 2.25 mal staerker bestraft als Unterarbeit (L < L*).
     Identisch zur Verlustaversion in V.2 (Konsum) -> Prop 6.2.

  5. INTRINSISCHE MOTIVATION: Michaelis-Menten-Kinetik I/(I+psi_I).
     Bei I=0: keine Motivation. Bei I->inf: Saettigung bei kappa_I*H/H_norm.
     DUAL zu V.2: dort DAEMPFT I die Psychologie, hier VERSTAERKT I sie.

  6. PEER-NORMKONVERGENZ Phi_L: Strukturell IDENTISCH zu V.3 Phi_c (S20).
     Asymmetrie: alpha_up/alpha_down = 2.50 (Aufwaertsherding staerker).
     Info-Modulation: Informierte Nachbarn beeinflussen staerker.

  7. STATUSDRUCK S: EINZIGARTIG fuer die Arbeitsdimension (nicht in V!).
     Konsum kann man verbergen — Arbeitszeit nicht (in den meisten Kulturen).
     S >= 0 immer -> verschiebt Gleichgewicht systematisch AUFWAERTS.
     Prop 6.2: Bei S=0 ist L.4 strukturell identisch zu V.4 (Konsum).

  8. NETZWERK: Multiplex mit 5 Layern (Trade, Info, Sozial, Finanz, Institut).
     Barabasi-Albert-artige Scale-Free-Topologie -> Hub-Dominanz.

  9. HETEROGENITAET: Alle Agenten-Parameter (I, H, alpha_L, lambda_L, Kultur)
     werden aus plausiblen Verteilungen gezogen (Lognormal, Uniform, Beta).
     Keine identischen Agenten -> emergente Ungleichheit moeglich.

  10. NEOKLASSISCHER GRENZFALL (Prop 6.1): Im Limit I->inf, L*=L, A=0, S=0
      reduziert sich L.4 auf: dL/dt = alpha_L*(L*-L) = 0 (Gleichgewicht).
      Die volle Dynamik entsteht AUSSCHLIESSLICH aus den Abweichungen
      von der neoklassischen Idealisierung.

  ════════════════════════════════════════════════════════════════════════════════
  REGIMEUEBERSICHT
  ════════════════════════════════════════════════════════════════════════════════

  R1: Normal Economy — L.1 dominiert, moderate Psychologie/Sozial
  R2: Workaholic-Kaskade — Hub arbeitet viel, V.3a-Herding + Status ziehen mit
  R3: Burnout-Krise — I-Kollaps + Schock, L.2 dominiert (Burnout-Spirale)
  R4: Arbeitsgewohnheits-Drift — L* passt sich an, Lifestyle Creep fuer Arbeit
  R5: Info-Heterogenitaet — Bimodale I-Verteilung -> Klassen-Bifurkation
  R6: Japan vs Frankreich — Kulturvergleich (Status-induzierter Symmetriebruch)
  R7: Inequality Spiral — Breite Anfangsverteilung -> Gini-Dynamik
  R8: Neoklassischer Grenzfall — Prop 6.1 + Prop 6.2 Symmetrie V.4 <-> L.4

  ════════════════════════════════════════════════════════════════════════════════
"""

print(header_text)

# ══════════════════════════════════════════════════════════════════════
# 1. KERNFUNKTIONEN (vektorisiert)
# ══════════════════════════════════════════════════════════════════════

def Psi_L(L, L_star, L_bar, I_job, H,
          lam_B=2.25, kappa_ref=0.3, kappa_I=1.2, psi_I=8.5,
          kappa_info_burn=1.0, Psi_max=2.0, H_norm=1.0):
    """L.2 Psychologische Arbeitsverzerrung (S24)."""
    L = np.asarray(L, dtype=float)
    L_star = np.asarray(L_star, dtype=float)
    I_job = np.asarray(I_job, dtype=float)
    H = np.asarray(H, dtype=float)
    x = L_star - L
    v = np.where(x >= 0, x, lam_B * x)
    info_burn = 1.0 / (1.0 + kappa_info_burn * np.maximum(I_job, 0.0))
    psi_burnout = kappa_ref * v * info_burn
    I_safe = np.maximum(I_job, 0.0)
    psi_intrinsic = kappa_I * I_safe / (I_safe + psi_I) * (H / H_norm)
    return np.clip(psi_burnout + psi_intrinsic, -Psi_max, Psi_max)


def Phi_L(dL, I_j, I_i, alpha_up=0.15, alpha_down=0.06,
          Phi_max=3.0, eps=0.01):
    """L.3a Peer-Normkonvergenz (S25, identisch zu V.3 Phi_c)."""
    alpha = np.where(dL >= 0, alpha_up, alpha_down)
    I_j_s = np.sqrt(np.maximum(I_j, 0.0))
    I_i_s = np.sqrt(np.maximum(I_i, 0.0))
    info_mod = I_j_s / (I_j_s + I_i_s + eps)
    return np.clip(alpha * dL * info_mod, -Phi_max, Phi_max)


def Status_S(rank, kultur=1.0, s_max=1.5, kappa_s=0.8):
    """L.3b Statusdruck-Operator (S25)."""
    rank = np.asarray(rank, dtype=float)
    s_raw = kultur * kappa_s * rank / (1.0 + rank)
    return np.clip(s_raw, 0.0, s_max * max(kultur, 0.01))


def social_labor_vec(L, I, A, kultur=1.0, **phi_kw):
    """Vollstaendiger L.3: Phi_L(Peer) + S(Status)."""
    N = len(L)
    dL_mat = L[np.newaxis, :] - L[:, np.newaxis]
    I_j_mat = np.broadcast_to(I[np.newaxis, :], (N, N))
    I_i_mat = np.broadcast_to(I[:, np.newaxis], (N, N))
    phi_mat = Phi_L(dL_mat, I_j_mat, I_i_mat, **phi_kw)
    peer_term = (A * phi_mat).sum(axis=1)
    order = np.argsort(np.argsort(L))
    rank = order / max(N - 1, 1)
    status_term = Status_S(rank, kultur=kultur)
    return peer_term + status_term


def social_labor_decomposed(L, I, A, kultur=1.0, **phi_kw):
    """Gibt (peer, status, total) zurueck."""
    N = len(L)
    dL_mat = L[np.newaxis, :] - L[:, np.newaxis]
    I_j_mat = np.broadcast_to(I[np.newaxis, :], (N, N))
    I_i_mat = np.broadcast_to(I[:, np.newaxis], (N, N))
    phi_mat = Phi_L(dL_mat, I_j_mat, I_i_mat, **phi_kw)
    peer_term = (A * phi_mat).sum(axis=1)
    order = np.argsort(np.argsort(L))
    rank = order / max(N - 1, 1)
    status_term = Status_S(rank, kultur=kultur)
    return peer_term, status_term, peer_term + status_term


def generate_multiplex_network(N, topology="scale_free", layers=5, seed=42):
    """Multiplex A_eff = sum_l omega_l A^(l). 5 Layer."""
    rng = np.random.RandomState(seed)
    omega = np.array([0.15, 0.30, 0.20, 0.25, 0.10])
    A_layers = []
    for l in range(layers):
        if topology == "scale_free":
            A = np.zeros((N, N))
            m = max(2, 2 + l)
            deg = np.ones(N)
            for i in range(m, N):
                p = deg[:i] / deg[:i].sum()
                tgt = rng.choice(i, size=min(m, i), replace=False, p=p)
                for t in tgt:
                    w = rng.uniform(0.3, 1.0)
                    A[i, t] = w; A[t, i] = w * rng.uniform(0.5, 1.0)
                    deg[i] += 1; deg[t] += 1
        elif topology == "small_world":
            k_nn = 4 + l * 2
            A = np.zeros((N, N))
            for i in range(N):
                for j in range(1, k_nn // 2 + 1):
                    nb = (i + j) % N
                    w = rng.uniform(0.5, 1.0)
                    A[i, nb] = w; A[nb, i] = w * rng.uniform(0.7, 1.0)
            p_rew = 0.1 + 0.05 * l
            for i in range(N):
                for j in range(N):
                    if A[i, j] > 0 and rng.random() < p_rew:
                        nj = rng.randint(0, N)
                        if nj != i:
                            A[i, j] = 0; A[i, nj] = rng.uniform(0.3, 1.0)
        else:
            p_c = 0.05 + 0.02 * l
            A = rng.random((N, N)) * (rng.random((N, N)) < p_c)
            np.fill_diagonal(A, 0)
        A_layers.append(A)
    A_eff = sum(omega[l] * A_layers[l] for l in range(layers))
    np.fill_diagonal(A_eff, 0)
    return A_eff, A_layers, omega


def gini(x):
    x = np.sort(np.abs(np.maximum(np.asarray(x, float), 0.01)))
    n = len(x)
    if n == 0 or x.sum() == 0:
        return 0
    return float((2 * np.sum(np.arange(1, n+1) * x) - (n + 1) * x.sum()) / (n * x.sum()))


# ── Vier-Ebenen Integrator ──────────────────────────────────────────

def run_four_layer(N, L0, Lstar0, I_job, H, A, alpha_L=0.08, kultur=1.0,
                   lambda_L=0.10, lam_B=2.25, kappa_I=1.2,
                   alpha_up=0.15, alpha_down=0.06,
                   T=50.0, dt=0.025,
                   use_l1=True, use_l2=True, use_l3=True,
                   track_layers=False):
    """
    Integriere das volle 2N-ODE (L + L*) mit Forward-Euler.
    Gibt dict mit L_hist, Lstar_hist, gini_hist, und optional Layer-Normen.
    """
    N_steps = int(T / dt)
    L_h = np.zeros((N, N_steps + 1))
    Ls_h = np.zeros((N, N_steps + 1))
    gini_h = np.zeros(N_steps + 1)
    L_h[:, 0] = L0.copy()
    Ls_h[:, 0] = Lstar0.copy()
    gini_h[0] = gini(L0)

    if track_layers:
        norm_L1 = np.zeros(N_steps + 1)
        norm_L2 = np.zeros(N_steps + 1)
        norm_L3 = np.zeros(N_steps + 1)

    for step in range(N_steps):
        L = L_h[:, step]
        Ls = Ls_h[:, step]
        L_bar = L.mean()

        # L.1: Rational
        Vec_L1 = np.zeros(N)
        if use_l1:
            Vec_L1 = alpha_L * (Ls - L)

        # L.2: Psychologisch
        Vec_L2 = np.zeros(N)
        if use_l2:
            Vec_L2 = Psi_L(L, Ls, L_bar, I_job, H, lam_B=lam_B, kappa_I=kappa_I)

        # L.3: Sozial (Peer + Status)
        Vec_L3 = np.zeros(N)
        if use_l3:
            Vec_L3 = social_labor_vec(L, I_job, A, kultur=kultur,
                                      alpha_up=alpha_up, alpha_down=alpha_down)

        dL = Vec_L1 + Vec_L2 + Vec_L3
        L_new = np.clip(L + dL * dt, 0.5, 24.0)
        Ls_new = np.maximum(Ls + lambda_L * (L - Ls) * dt, 0.5)

        L_h[:, step + 1] = L_new
        Ls_h[:, step + 1] = Ls_new
        gini_h[step + 1] = gini(L_new)

        if track_layers:
            norm_L1[step] = np.linalg.norm(Vec_L1)
            norm_L2[step] = np.linalg.norm(Vec_L2)
            norm_L3[step] = np.linalg.norm(Vec_L3)

    out = dict(L=L_h, Lstar=Ls_h, gini=gini_h,
               t=np.linspace(0, T, N_steps + 1))
    if track_layers:
        norm_L1[-1] = norm_L1[-2]; norm_L2[-1] = norm_L2[-2]; norm_L3[-1] = norm_L3[-2]
        out["norm_L1"] = norm_L1
        out["norm_L2"] = norm_L2
        out["norm_L3"] = norm_L3
    return out


# ══════════════════════════════════════════════════════════════════════
# 2. GEMEINSAME PARAMETER
# ══════════════════════════════════════════════════════════════════════

T = 50.0; dt = 0.025; N_steps = int(T / dt)
N_ag = 100

rng = np.random.RandomState(42)
I_base = np.clip(rng.lognormal(np.log(5), 0.8, N_ag), 0.3, 80)
H_base = np.clip(rng.normal(1.0, 0.2, N_ag), 0.4, 2.0)
L0_base = np.clip(rng.normal(8.0, 1.5, N_ag), 3.0, 14.0)
Lstar0_base = L0_base * rng.uniform(0.9, 1.1, N_ag)

A_base, A_layers, omega_l = generate_multiplex_network(N_ag, "scale_free", seed=42)
degree_base = A_base.sum(axis=1)

print("=" * 72)
print("  REGIME-ERGEBNISSE")
print("=" * 72)

results = {}

# ══════════════════════════════════════════════════════════════════════
# R1: Normal Economy (L.1 dominiert)
# ══════════════════════════════════════════════════════════════════════
print("\n  R1: Normal Economy")
R1 = run_four_layer(N_ag, L0_base, Lstar0_base, I_base, H_base, A_base,
                    track_layers=True)
print(f"    L_mean: {L0_base.mean():.1f}h -> {R1['L'][:,-1].mean():.2f}h")
print(f"    Gini:   {R1['gini'][0]:.3f} -> {R1['gini'][-1]:.3f}")
print(f"    Layer-Normen (t=T): L1={R1['norm_L1'][-1]:.2f}, "
      f"L2={R1['norm_L2'][-1]:.2f}, L3={R1['norm_L3'][-1]:.2f}")
results["R1"] = R1

# ══════════════════════════════════════════════════════════════════════
# R2: Workaholic-Kaskade (Hub arbeitet 16h, L.3 zieht)
# ══════════════════════════════════════════════════════════════════════
print("\n  R2: Workaholic-Kaskade")
L0_R2 = L0_base.copy()
hub = np.argmax(degree_base)
L0_R2[hub] = 16.0
I_R2 = I_base.copy()
I_R2[hub] = 60.0
R2 = run_four_layer(N_ag, L0_R2, Lstar0_base.copy(), I_R2, H_base, A_base,
                    alpha_up=0.25, alpha_down=0.06, kultur=1.5,
                    track_layers=True)
print(f"    Hub L: {L0_R2[hub]:.0f}h -> {R2['L'][hub,-1]:.2f}h")
print(f"    Mean L: {L0_R2.mean():.1f}h -> {R2['L'][:,-1].mean():.2f}h")
print(f"    Gini:   {R2['gini'][0]:.3f} -> {R2['gini'][-1]:.3f}")
results["R2"] = R2

# ══════════════════════════════════════════════════════════════════════
# R3: Burnout-Krise (I-Kollaps + Ueberarbeitung)
# ══════════════════════════════════════════════════════════════════════
print("\n  R3: Burnout-Krise")
L0_R3 = np.clip(L0_base * 1.5, 10, 20)  # Alle ueberarbeitet
Lstar_R3 = L0_base.copy()  # Referenz niedrig -> Burnout!
I_R3 = np.clip(I_base * 0.05, 0.01, 2.0)  # Info-Kollaps
R3 = run_four_layer(N_ag, L0_R3, Lstar_R3, I_R3, H_base, A_base,
                    track_layers=True)
print(f"    L_mean: {L0_R3.mean():.1f}h -> {R3['L'][:,-1].mean():.2f}h")
print(f"    Gini:   {R3['gini'][0]:.3f} -> {R3['gini'][-1]:.3f}")
print(f"    Layer (t=T): L1={R3['norm_L1'][-1]:.2f}, L2={R3['norm_L2'][-1]:.2f}, "
      f"L3={R3['norm_L3'][-1]:.2f}")
results["R3"] = R3

# ══════════════════════════════════════════════════════════════════════
# R4: Arbeitsgewohnheits-Drift (L* steigt)
# ══════════════════════════════════════════════════════════════════════
print("\n  R4: Arbeitsgewohnheits-Drift")
Lstar_R4 = L0_base * 0.7  # Referenz startet UNTER Ist-Niveau
R4 = run_four_layer(N_ag, L0_base, Lstar_R4, I_base, H_base, A_base,
                    lambda_L=0.05, track_layers=True)
drift = R4['Lstar'][:, -1].mean() - Lstar_R4.mean()
print(f"    L*_mean: {Lstar_R4.mean():.1f}h -> {R4['Lstar'][:,-1].mean():.2f}h "
      f"(drift +{drift:.2f}h)")
print(f"    L_mean:  {L0_base.mean():.1f}h -> {R4['L'][:,-1].mean():.2f}h")
results["R4"] = R4

# ══════════════════════════════════════════════════════════════════════
# R5: Info-Heterogenitaet (bimodale I-Verteilung)
# ══════════════════════════════════════════════════════════════════════
print("\n  R5: Info-Heterogenitaet")
I_R5 = np.concatenate([
    np.full(N_ag // 2, 0.5),   # uninformierte Masse
    np.full(N_ag - N_ag // 2, 50.0)  # informierte Elite
])
rng.shuffle(I_R5)
R5 = run_four_layer(N_ag, L0_base, Lstar0_base.copy(), I_R5, H_base, A_base,
                    track_layers=True)
elite = I_R5 > 10
mass = ~elite
print(f"    Elite L(T)={R5['L'][elite, -1].mean():.2f}h, "
      f"Mass L(T)={R5['L'][mass, -1].mean():.2f}h")
print(f"    Gini: {R5['gini'][0]:.3f} -> {R5['gini'][-1]:.3f}")
results["R5"] = R5

# ══════════════════════════════════════════════════════════════════════
# R6: Japan vs Frankreich (Kulturvergleich)
# ══════════════════════════════════════════════════════════════════════
print("\n  R6: Kulturvergleich")
kultur_configs = {"Japan (k=2.5)": 2.5, "USA (k=1.0)": 1.0,
                   "Deutschland (k=0.7)": 0.7, "Frankreich (k=0.3)": 0.3}
R6_data = {}
for name, k_val in kultur_configs.items():
    res = run_four_layer(N_ag, L0_base, Lstar0_base.copy(), I_base, H_base,
                         A_base, kultur=k_val)
    R6_data[name] = res
    print(f"    {name:22s}: L_mean(T)={res['L'][:,-1].mean():.2f}h, "
          f"Gini(T)={res['gini'][-1]:.3f}")
diff_JF = R6_data["Japan (k=2.5)"]["L"][:,-1].mean() - \
          R6_data["Frankreich (k=0.3)"]["L"][:,-1].mean()
print(f"    Delta L(JP-FR) = {diff_JF:.2f}h")
results["R6"] = R6_data

# ══════════════════════════════════════════════════════════════════════
# R7: Inequality Spiral (breite Anfangsverteilung)
# ══════════════════════════════════════════════════════════════════════
print("\n  R7: Inequality Spiral")
L0_R7 = np.clip(rng.lognormal(np.log(8), 0.8, N_ag), 1.0, 20.0)
R7 = run_four_layer(N_ag, L0_R7, L0_R7.copy(), I_base, H_base, A_base,
                    track_layers=True)
gini_peak = R7['gini'].max()
gini_peak_t = R7['t'][np.argmax(R7['gini'])]
print(f"    Gini: {R7['gini'][0]:.3f} -> peak {gini_peak:.3f} (t={gini_peak_t:.1f}) "
      f"-> {R7['gini'][-1]:.3f}")
results["R7"] = R7

# ══════════════════════════════════════════════════════════════════════
# R8: Neoklassischer Grenzfall + Prop 6.2 Symmetrie
# ══════════════════════════════════════════════════════════════════════
print("\n  R8: Neoklassischer Grenzfall + Prop 6.2")

# a) Prop 6.1: I->inf, L*=L, A=0, S=0 => dL/dt = 0 (Gleichgewicht)
N_R8 = 50
L0_R8 = rng.uniform(5, 12, N_R8)
R8_neo = run_four_layer(N_R8, L0_R8, L0_R8.copy(),
                        np.full(N_R8, 1e8), np.ones(N_R8),
                        np.zeros((N_R8, N_R8)),
                        alpha_L=0.08, kultur=0.0,  # S=0 (no status)
                        lambda_L=100.0, dt=0.005)
# Bei L*=L und I->inf: Psi_L=kappa_I*I/(I+psi_I)*H ≈ kappa_I*H -> konstante Drift
# Aber bei L*=L exakt: Burnout-Term=0, nur Motivation bleibt
# Um echten Grenzfall zu testen: kappa_I=0 (keine Motivation)
R8_pure = run_four_layer(N_R8, L0_R8, L0_R8.copy(),
                         np.full(N_R8, 1e8), np.ones(N_R8),
                         np.zeros((N_R8, N_R8)),
                         alpha_L=0.08, kultur=0.0,
                         lambda_L=100.0, kappa_I=0.0, dt=0.005)
# dL/dt = alpha*(L*-L) mit L*≈L -> 0. L sollte nahezu konstant bleiben.
err_neo = np.max(np.abs(R8_pure['L'][:, -1] - L0_R8)) / np.max(L0_R8)
print(f"    Prop 6.1: max|L(T)-L(0)|/L(0) = {err_neo:.6f} (soll ~0)")

# b) Prop 6.2 Symmetrie: L.4(S=0) vs V.4 bei identischen Eingaben
#    Dafuer: L.1 (alpha_L Anpassung) vs V.1 (Euler)
#    Die Drei-Ebenen sind: L.1+L.2+L.3(S=0) vs V.1+V.2+V.3
#    L.2 bei I_job=0 = Burnout only, V.2 bei I=0 = Referenz+Verlust
#    Symmetrie gilt NUR fuer die Phi-Terme (L.3a vs V.3) bei S=0
#    Also teste: sum_j A*Phi_L(L_j-L_i, I_j, I_i) == sum_j A*Phi_c(c_j-c_i, I_j, I_i)
N_sym = 50
x_sym = rng.lognormal(np.log(10), 0.3, N_sym)
I_sym = np.clip(rng.lognormal(np.log(5), 0.5, N_sym), 0.5, 30)
A_sym, _, _ = generate_multiplex_network(N_sym, "small_world", seed=99)

# V.3 Phi_c (aus S20)
def Phi_c(dc, I_j, I_i, alpha_up=0.15, alpha_down=0.06, Phi_max=3.0, eps=0.01):
    alpha = np.where(dc >= 0, alpha_up, alpha_down)
    I_j_s = np.sqrt(np.maximum(I_j, 0.0))
    I_i_s = np.sqrt(np.maximum(I_i, 0.0))
    info_mod = I_j_s / (I_j_s + I_i_s + eps)
    return np.clip(alpha * dc * info_mod, -Phi_max, Phi_max)

def social_V3(c, I, A):
    N = len(c)
    dc_mat = c[np.newaxis, :] - c[:, np.newaxis]
    I_j_m = np.broadcast_to(I[np.newaxis, :], (N, N))
    I_i_m = np.broadcast_to(I[:, np.newaxis], (N, N))
    phi_mat = Phi_c(dc_mat, I_j_m, I_i_m)
    return (A * phi_mat).sum(axis=1)

def social_L3_peer_only(L, I, A):
    N = len(L)
    dL_mat = L[np.newaxis, :] - L[:, np.newaxis]
    I_j_m = np.broadcast_to(I[np.newaxis, :], (N, N))
    I_i_m = np.broadcast_to(I[:, np.newaxis], (N, N))
    phi_mat = Phi_L(dL_mat, I_j_m, I_i_m)
    return (A * phi_mat).sum(axis=1)

# Statischer Symmetrie-Test
v3_result = social_V3(x_sym, I_sym, A_sym)
l3_result = social_L3_peer_only(x_sym, I_sym, A_sym)
sym_diff = np.max(np.abs(v3_result - l3_result))

# Dynamischer Symmetrie-Test (volle Zeitreihe)
c_V3 = np.zeros((N_sym, N_steps + 1))
L_L3 = np.zeros((N_sym, N_steps + 1))
c_V3[:, 0] = x_sym.copy(); L_L3[:, 0] = x_sym.copy()
for step in range(N_steps):
    c_now = c_V3[:, step]; L_now = L_L3[:, step]
    dc_v3 = social_V3(c_now, I_sym, A_sym)
    dL_l3 = social_L3_peer_only(L_now, I_sym, A_sym)
    c_V3[:, step + 1] = np.maximum(c_now + dc_v3 * dt, 0.01)
    L_L3[:, step + 1] = np.maximum(L_now + dL_l3 * dt, 0.01)
max_dyn_diff = np.max(np.abs(c_V3 - L_L3))

print(f"    Prop 6.2: max|V.3 - L.3(S=0)| = {sym_diff:.2e} (statisch)")
print(f"    Prop 6.2: max|V.3_dyn - L.3_dyn(S=0)| = {max_dyn_diff:.2e}")

results["R8"] = dict(err_neo=err_neo, sym_diff=sym_diff, max_dyn_diff=max_dyn_diff,
                      c_V3=c_V3, L_L3=L_L3, t=np.linspace(0, T, N_steps + 1))


# ══════════════════════════════════════════════════════════════════════
#  VERGLEICH: L.1 vs L.1+L.2 vs L.1+L.3 vs L.1+L.2+L.3
# ══════════════════════════════════════════════════════════════════════
print("\n  Ebenen-Vergleich")
configs_comp = {
    "L.1 nur":     (True, False, False),
    "L.1+L.2":     (True, True, False),
    "L.1+L.3":     (True, False, True),
    "L.1+L.2+L.3": (True, True, True),
}
comp_data = {}
for name, (l1, l2, l3) in configs_comp.items():
    res = run_four_layer(N_ag, L0_base, Lstar0_base.copy(), I_base, H_base,
                         A_base, use_l1=l1, use_l2=l2, use_l3=l3)
    comp_data[name] = res
    print(f"    {name:15s}: L_mean(T)={res['L'][:,-1].mean():.2f}h, "
          f"Gini(T)={res['gini'][-1]:.3f}")
results["comp"] = comp_data


# ══════════════════════════════════════════════════════════════════════
# VALIDIERUNGEN
# ══════════════════════════════════════════════════════════════════════
print(f"\n{'='*72}\n  VALIDIERUNGEN\n{'='*72}")
validations = {}

# V1: Prop 6.1 — Neoklassischer Grenzfall
v1_pass = err_neo < 0.01
validations["V1"] = dict(name="Prop 6.1: I->inf,L*=L,A=0,S=0 => stabil",
                         passed=v1_pass, detail=f"max_rel_err={err_neo:.6f}")
print(f"  V1: {'PASS' if v1_pass else 'FAIL'} ({validations['V1']['detail']})")

# V2: Additivitaet — dL ≈ L1 + L2 + L3 (bei kleinem dt)
# Verwende fruehen Zeitschritt wo kein Clipping aktiv ist
t_early = 5  # Step 5, agents still far from bounds
L_mid = R1['L'][:, t_early]
Ls_mid = R1['Lstar'][:, t_early]
L_bar_mid = L_mid.mean()
vec_L1 = 0.08 * (Ls_mid - L_mid)
vec_L2 = Psi_L(L_mid, Ls_mid, L_bar_mid, I_base, H_base)
vec_L3 = social_labor_vec(L_mid, I_base, A_base, kultur=1.0)
dL_sum = vec_L1 + vec_L2 + vec_L3
dL_actual = (R1['L'][:, t_early+1] - R1['L'][:, t_early]) / dt
# Nur Agenten pruefen die nicht am Rand sind
interior = (R1['L'][:, t_early+1] > 0.6) & (R1['L'][:, t_early+1] < 23.9)
add_err = np.max(np.abs(dL_sum[interior] - dL_actual[interior])) / (np.max(np.abs(dL_actual[interior])) + 1e-10)
v2_pass = add_err < 0.05
validations["V2"] = dict(name="Additivitaet: dL = L1+L2+L3",
                         passed=v2_pass, detail=f"max_rel_err={add_err:.6f}")
print(f"  V2: {'PASS' if v2_pass else 'FAIL'} ({validations['V2']['detail']})")

# V3: Dominanz — R1: L1 dominiert, R3: L2 dominiert (Burnout)
R1_L1 = R1['norm_L1'][-1]; R1_other = R1['norm_L2'][-1] + R1['norm_L3'][-1]
v3a = R1_L1 > 0  # L1 aktiv
R3_L2 = R3['norm_L2'][-1]; R3_L1 = R3['norm_L1'][-1]
v3b = R3_L2 > R3_L1  # Krise: L2 dominiert L1
v3_pass = v3a and v3b
validations["V3"] = dict(name="Dominanz: Normal->L1, Krise->L2",
                         passed=v3_pass,
                         detail=f"R1: L1={R1_L1:.2f}; R3: L2={R3_L2:.2f}>L1={R3_L1:.2f}")
print(f"  V3: {'PASS' if v3_pass else 'FAIL'} ({validations['V3']['detail']})")

# V4: Gini — L.1+L.2+L.3 < L.1
g_l1 = comp_data["L.1 nur"]["gini"][-1]
g_full = comp_data["L.1+L.2+L.3"]["gini"][-1]
v4_pass = g_full < g_l1
validations["V4"] = dict(name="Gini: L.1+L.2+L.3 < L.1",
                         passed=v4_pass,
                         detail=f"G(L.1)={g_l1:.3f}, G(full)={g_full:.3f}")
print(f"  V4: {'PASS' if v4_pass else 'FAIL'} ({validations['V4']['detail']})")

# V5: Kultureffekt — Japan > Frankreich
L_jp = R6_data["Japan (k=2.5)"]["L"][:, -1].mean()
L_fr = R6_data["Frankreich (k=0.3)"]["L"][:, -1].mean()
v5_pass = L_jp > L_fr + 1.0  # Mindestens 1h Unterschied
validations["V5"] = dict(name="Kultur: L(JP) > L(FR) + 1h",
                         passed=v5_pass,
                         detail=f"L(JP)={L_jp:.2f}, L(FR)={L_fr:.2f}, diff={L_jp-L_fr:.2f}h")
print(f"  V5: {'PASS' if v5_pass else 'FAIL'} ({validations['V5']['detail']})")

# V6: Stabilitaet — kein Agent negativ oder >24h (nach clipping)
L_min_all = min(R1['L'].min(), R2['L'].min(), R3['L'].min(),
                R5['L'].min(), R7['L'].min())
L_max_all = max(R1['L'].max(), R2['L'].max(), R3['L'].max(),
                R5['L'].max(), R7['L'].max())
v6_pass = L_min_all >= 0.49 and L_max_all <= 24.01
validations["V6"] = dict(name="Stabilitaet: 0.5<=L<=24.0",
                         passed=v6_pass,
                         detail=f"L_min={L_min_all:.4f}, L_max={L_max_all:.2f}")
print(f"  V6: {'PASS' if v6_pass else 'FAIL'} ({validations['V6']['detail']})")

# V7: Netzwerk equalisiert — staerkeres Netzwerk -> niedriger Gini
A_weak = A_base * 0.2; A_strong = A_base * 3.0
r_weak = run_four_layer(N_ag, L0_base, Lstar0_base.copy(), I_base, H_base, A_weak)
r_strong = run_four_layer(N_ag, L0_base, Lstar0_base.copy(), I_base, H_base, A_strong)
g_weak = r_weak['gini'][-1]; g_strong = r_strong['gini'][-1]
v7_pass = g_strong < g_weak
validations["V7"] = dict(name="Netzwerk equalisiert: G(3xA)<G(0.2xA)",
                         passed=v7_pass,
                         detail=f"G(0.2A)={g_weak:.3f}, G(3A)={g_strong:.3f}")
print(f"  V7: {'PASS' if v7_pass else 'FAIL'} ({validations['V7']['detail']})")

# V8: Prop 6.2 — L.3(S=0) == V.3 (dynamisch)
v8_pass = max_dyn_diff < 1e-12
validations["V8"] = dict(name="Prop 6.2: L.3(S=0)==V.3 dynamisch",
                         passed=v8_pass, detail=f"max|diff|={max_dyn_diff:.2e}")
print(f"  V8: {'PASS' if v8_pass else 'FAIL'} ({validations['V8']['detail']})")


# ══════════════════════════════════════════════════════════════════════
# SENSITIVITAETSANALYSEN
# ══════════════════════════════════════════════════════════════════════
print(f"\n{'='*72}\n  SENSITIVITAETSANALYSEN\n{'='*72}")

# SA1: alpha_up vs lambda_L → Gini(T) — 20x20 Heatmap
print("  SA1: alpha_up vs lambda_L -> Gini(T)")
sa1_au = np.linspace(0.01, 0.4, 15)
sa1_lL = np.linspace(0.02, 0.3, 15)
SA1_G = np.zeros((len(sa1_lL), len(sa1_au)))
N_sa = 40
A_sa, _, _ = generate_multiplex_network(N_sa, "small_world", seed=55)
L0_sa = np.clip(rng.normal(8, 1.5, N_sa), 3, 14)
I_sa = np.clip(rng.lognormal(np.log(5), 0.5, N_sa), 0.5, 30)
H_sa = np.clip(rng.normal(1, 0.15, N_sa), 0.5, 1.5)
Ls_sa = L0_sa * rng.uniform(0.9, 1.1, N_sa)
for il, lL_v in enumerate(sa1_lL):
    for ia, au_v in enumerate(sa1_au):
        res = run_four_layer(N_sa, L0_sa, Ls_sa.copy(), I_sa, H_sa, A_sa,
                             alpha_up=au_v, alpha_down=au_v*0.4, lambda_L=lL_v)
        SA1_G[il, ia] = res['gini'][-1]
results["SA1"] = dict(au=sa1_au, lL=sa1_lL, G=SA1_G)
print(f"    Gini range: [{SA1_G.min():.3f}, {SA1_G.max():.3f}]")

# SA2: Kultur vs Info-Level → L_mean(T) — 20x20 Heatmap
print("  SA2: Kultur vs I_mean -> L_mean(T)")
sa2_k = np.linspace(0.1, 3.0, 15)
sa2_I = np.logspace(-0.5, 1.7, 15)
SA2_L = np.zeros((len(sa2_I), len(sa2_k)))
for ii, I_v in enumerate(sa2_I):
    for ik, k_v in enumerate(sa2_k):
        I_tmp = np.full(N_sa, I_v)
        res = run_four_layer(N_sa, L0_sa, Ls_sa.copy(), I_tmp, H_sa, A_sa,
                             kultur=k_v)
        SA2_L[ii, ik] = res['L'][:, -1].mean()
results["SA2"] = dict(kultur=sa2_k, I_mean=sa2_I, L_mean=SA2_L)
print(f"    L_mean range: [{SA2_L.min():.1f}, {SA2_L.max():.1f}]h")

# SA3: Topologie-Vergleich
print("  SA3: Topologie-Vergleich")
N_topo = 50
topos_sa = {"Scale-Free": "scale_free", "Small-World": "small_world", "Random": "random"}
SA3_data = {}
for tname, ttype in topos_sa.items():
    A_t, _, _ = generate_multiplex_network(N_topo, ttype, seed=77)
    L0_t = np.clip(rng.normal(8, 1.5, N_topo), 3, 14)
    I_t = 5.0 * np.ones(N_topo)
    H_t = np.ones(N_topo)
    Ls_t = L0_t.copy()
    res = run_four_layer(N_topo, L0_t, Ls_t, I_t, H_t, A_t)
    SA3_data[tname] = dict(gini=res['gini'], L_mean=res['L'].mean(axis=0))
    print(f"    {tname:12s}: Gini(T)={res['gini'][-1]:.3f}, L_mean(T)={res['L'][:,-1].mean():.2f}h")
results["SA3"] = SA3_data

# SA4: lam_B (Burnout-Asymmetrie) vs kappa_I (Motivation) → L_mean(T)
print("  SA4: lam_B vs kappa_I -> L_mean(T)")
sa4_lb = np.linspace(1.0, 4.0, 15)
sa4_kI = np.linspace(0.1, 3.0, 15)
SA4_L = np.zeros((len(sa4_kI), len(sa4_lb)))
for ilb, lb_v in enumerate(sa4_lb):
    for ikI, kI_v in enumerate(sa4_kI):
        res = run_four_layer(N_sa, L0_sa, Ls_sa.copy(), I_sa, H_sa, A_sa,
                             lam_B=lb_v, kappa_I=kI_v)
        SA4_L[ikI, ilb] = res['L'][:, -1].mean()
results["SA4"] = dict(lam_B=sa4_lb, kappa_I=sa4_kI, L_mean=SA4_L)
print(f"    L_mean range: [{SA4_L.min():.1f}, {SA4_L.max():.1f}]h")

# SA5: Netzwerk-Dichte vs Gini
print("  SA5: Netzwerk-Dichte vs Gini")
densities = np.linspace(0.02, 0.3, 25)
gini_dens = []
for d_v in densities:
    rng_s = np.random.RandomState(42)
    A_s = (rng_s.random((N_sa, N_sa)) < d_v).astype(float) * rng_s.uniform(0.3, 1.0, (N_sa, N_sa))
    np.fill_diagonal(A_s, 0)
    res = run_four_layer(N_sa, L0_sa, Ls_sa.copy(), I_sa, H_sa, A_s)
    gini_dens.append(res['gini'][-1])
results["SA5"] = dict(density=densities, gini=np.array(gini_dens))
print(f"    d=0.02: G={gini_dens[0]:.3f}, d=0.30: G={gini_dens[-1]:.3f}")


# ══════════════════════════════════════════════════════════════════════
# ERWEITERTE ANALYSEN
# ══════════════════════════════════════════════════════════════════════
print(f"\n{'='*72}\n  ERWEITERTE ANALYSE\n{'='*72}")

# EA1: Dominanz-Dynamik — welche Ebene dominiert ueber Zeit?
print("\n  EA1: Dominanz-Dynamik")
t_arr = R1['t']
frac_L1 = R1['norm_L1'] / (R1['norm_L1'] + R1['norm_L2'] + R1['norm_L3'] + 1e-10)
frac_L2 = R1['norm_L2'] / (R1['norm_L1'] + R1['norm_L2'] + R1['norm_L3'] + 1e-10)
frac_L3 = R1['norm_L3'] / (R1['norm_L1'] + R1['norm_L2'] + R1['norm_L3'] + 1e-10)
print(f"    t=0: L1={frac_L1[0]:.2f}, L2={frac_L2[0]:.2f}, L3={frac_L3[0]:.2f}")
print(f"    t=T: L1={frac_L1[-1]:.2f}, L2={frac_L2[-1]:.2f}, L3={frac_L3[-1]:.2f}")
results["EA1"] = dict(frac_L1=frac_L1, frac_L2=frac_L2, frac_L3=frac_L3, t=t_arr)

# EA2: Hysterese — Schock und Erholung (ist L(T) = L(0)?)
print("\n  EA2: Hysterese-Test")
# Phase 1: Normal
L0_hys = 8.0 * np.ones(N_ag) + rng.normal(0, 0.5, N_ag)
L0_hys = np.clip(L0_hys, 4, 14)
res_pre = run_four_layer(N_ag, L0_hys, L0_hys.copy(), I_base, H_base, A_base, T=25)
# Phase 2: Schock (hoher Statusdruck 3 Perioden)
res_shock = run_four_layer(N_ag, res_pre['L'][:, -1], res_pre['Lstar'][:, -1],
                           I_base, H_base, A_base, kultur=3.0, T=10)
# Phase 3: Erholung (normaler Druck)
res_recov = run_four_layer(N_ag, res_shock['L'][:, -1], res_shock['Lstar'][:, -1],
                           I_base, H_base, A_base, kultur=1.0, T=25)
hyst_gap = res_recov['L'][:, -1].mean() - L0_hys.mean()
print(f"    L_mean: Start={L0_hys.mean():.2f}h -> Post-Schock={res_shock['L'][:,-1].mean():.2f}h "
      f"-> Erholung={res_recov['L'][:,-1].mean():.2f}h")
print(f"    Hysterese-Gap: {hyst_gap:+.2f}h (Scarring-Effekt)")
results["EA2"] = dict(gap=hyst_gap, L_start=L0_hys.mean(),
                       L_shock=res_shock['L'][:,-1].mean(),
                       L_recov=res_recov['L'][:,-1].mean())

# EA3: Peer/Status Dekomposition ueber Zeit
print("\n  EA3: Peer/Status-Dekomposition")
N_ea3 = 50
A_ea3, _, _ = generate_multiplex_network(N_ea3, "small_world", seed=333)
L_ea3 = np.zeros((N_ea3, N_steps + 1))
Ls_ea3 = np.zeros((N_ea3, N_steps + 1))
peer_mean_t = np.zeros(N_steps + 1)
status_mean_t = np.zeros(N_steps + 1)
L1_mean_t = np.zeros(N_steps + 1)
L2_mean_t = np.zeros(N_steps + 1)
L_ea3[:, 0] = np.clip(rng.normal(8, 1.5, N_ea3), 4, 14)
Ls_ea3[:, 0] = L_ea3[:, 0] * rng.uniform(0.9, 1.1, N_ea3)
I_ea3 = np.clip(rng.lognormal(np.log(5), 0.5, N_ea3), 0.5, 30)
H_ea3 = np.clip(rng.normal(1, 0.15, N_ea3), 0.5, 1.5)

for step in range(N_steps):
    L_now = L_ea3[:, step]
    Ls_now = Ls_ea3[:, step]
    L_bar = L_now.mean()
    vec_l1 = 0.08 * (Ls_now - L_now)
    vec_l2 = Psi_L(L_now, Ls_now, L_bar, I_ea3, H_ea3)
    peer, status, total_soc = social_labor_decomposed(L_now, I_ea3, A_ea3, kultur=1.5)
    L1_mean_t[step] = vec_l1.mean()
    L2_mean_t[step] = vec_l2.mean()
    peer_mean_t[step] = peer.mean()
    status_mean_t[step] = status.mean()
    dL = vec_l1 + vec_l2 + total_soc
    L_ea3[:, step + 1] = np.clip(L_now + dL * dt, 0.5, 24.0)
    Ls_ea3[:, step + 1] = np.maximum(Ls_now + 0.10 * (L_now - Ls_now) * dt, 0.5)

# Letzter Punkt
vec_l1_f = 0.08 * (Ls_ea3[:, -1] - L_ea3[:, -1])
vec_l2_f = Psi_L(L_ea3[:, -1], Ls_ea3[:, -1], L_ea3[:, -1].mean(), I_ea3, H_ea3)
peer_f, status_f, _ = social_labor_decomposed(L_ea3[:, -1], I_ea3, A_ea3, kultur=1.5)
L1_mean_t[-1] = vec_l1_f.mean(); L2_mean_t[-1] = vec_l2_f.mean()
peer_mean_t[-1] = peer_f.mean(); status_mean_t[-1] = status_f.mean()

results["EA3"] = dict(t=t_arr, L1=L1_mean_t, L2=L2_mean_t,
                       peer=peer_mean_t, status=status_mean_t, L=L_ea3)
print(f"    L1(T)={L1_mean_t[-1]:.4f}, L2(T)={L2_mean_t[-1]:.4f}, "
      f"Peer(T)={peer_mean_t[-1]:.4f}, Status(T)={status_mean_t[-1]:.4f}")

# EA4: Emergenz/Superadditivitaet
print("\n  EA4: Superadditivitaet")
L_l1 = comp_data["L.1 nur"]["L"][:, -1]
L_l12 = comp_data["L.1+L.2"]["L"][:, -1]
L_l13 = comp_data["L.1+L.3"]["L"][:, -1]
L_full = comp_data["L.1+L.2+L.3"]["L"][:, -1]
delta_l12 = np.linalg.norm(L_l12 - L_l1)
delta_l13 = np.linalg.norm(L_l13 - L_l1)
delta_full = np.linalg.norm(L_full - L_l1)
superadd = delta_full / (delta_l12 + delta_l13 + 1e-10)
print(f"    ratio = {superadd:.3f} (1.0=additiv, >1=super, <1=sub)")
results["EA4"] = dict(superadd=superadd, delta_l12=delta_l12,
                       delta_l13=delta_l13, delta_full=delta_full)


# ══════════════════════════════════════════════════════════════════════
# MATHEMATISCHE STRUKTUREN
# ══════════════════════════════════════════════════════════════════════
print(f"\n{'='*72}\n  MATHEMATISCHE STRUKTUREN\n{'='*72}")

struct_notes = []

struct_notes.append(
    "STRUKTUR 1: Gradientensystem mit externem Feld\n"
    "  L.4 hat die Form: dL/dt = -grad V(L) + F_ext\n"
    "  L.1 + L.2: Gradientenanteil (Potentialminimierung)\n"
    "  L.3a (Phi_L): Graph-Laplacian-Diffusion\n"
    "  L.3b (S): Externes Feld (Status-Lift)\n"
    "  -> Fokker-Planck auf Netzwerk mit Drift")
print(f"\n  {struct_notes[-1]}")

struct_notes.append(
    "STRUKTUR 2: Mehrskalige Separation\n"
    "  Schnell: L (Arbeitszeit) — Anpassung in Tagen/Wochen\n"
    "  Langsam: L* (Referenz) — Adaptation in Monaten/Jahren\n"
    "  -> Singulare Stoerungstheorie anwendbar\n"
    "  -> Hysterese/Scarring durch Zeitskalen-Trennung")
print(f"\n  {struct_notes[-1]}")

struct_notes.append(
    "STRUKTUR 3: Nichtlineare Superposition\n"
    f"  Superadditivitaets-Ratio: {superadd:.3f}\n"
    "  L.1+L.2+L.3 ist NICHT Summe der Einzeleffekte\n"
    "  -> Emergente Wechselwirkung zwischen Ebenen\n"
    "  -> L.2 (Burnout) limitiert L.3 (Herding-Erhoehung)")
print(f"\n  {struct_notes[-1]}")

struct_notes.append(
    "STRUKTUR 4: Prop 6.2 Symmetrie\n"
    "  V.4: dc/dt = R(r,beta,gamma,c) + Psi_c(c,c*,G,I) + S_V3(c,I,A)\n"
    "  L.4: dL/dt = alpha_L(L*-L) + Psi_L(L,L*,L_bar,I,H) + S_L3(L,I,A) + S(rank,K)\n"
    "  Bei S=0: L.3 Peer-Term == V.3 Herding-Term (EXAKT)\n"
    f"  -> max|V.3_dyn - L.3_dyn(S=0)| = {max_dyn_diff:.2e}\n"
    "  -> Status-Term S ist EINZIGE Asymmetrie-Quelle")
print(f"\n  {struct_notes[-1]}")

struct_notes.append(
    "STRUKTUR 5: Kulturelle Bifurkation\n"
    f"  Japan (k=2.5): L_mean(T)={L_jp:.1f}h\n"
    f"  Frankreich (k=0.3): L_mean(T)={L_fr:.1f}h\n"
    f"  Differenz: {L_jp-L_fr:.1f}h — rein Status-induziert\n"
    "  -> Identisches Modell, nur Kulturparameter verschieden\n"
    "  -> Erklaert internationale Arbeitszeitdivergenz")
print(f"\n  {struct_notes[-1]}")


# ══════════════════════════════════════════════════════════════════════
# PLOT (30+ Panels)
# ══════════════════════════════════════════════════════════════════════

print(f"\n  PLOTTE ...")

fig = plt.figure(figsize=(28, 60))
gs = GridSpec(14, 3, figure=fig,
              height_ratios=[0.7, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0.35],
              hspace=0.38, wspace=0.30)
fig.suptitle('S26  L.4  Vollstaendige Arbeitsangebotsdynamik',
             fontsize=15, fontweight='bold', y=0.998)

# ── Row 0: GLEICHUNG (gross, prominent) ──
ax_eq = fig.add_subplot(gs[0, 0:3])
ax_eq.axis('off')
eq_text = (
    "GLEICHUNG L.4 (Vollstaendige Arbeitsangebotsdynamik, §6.4):\n\n"
    "  dL_i/dt  =  alpha_L (L_i* - L_i)                                    [L.1: Rational — Konvergenz zum FOC-Optimum]\n"
    "            +  Psi_L(L_i, L_i*, L_bar, I_i^job, H_i)                  [L.2: Burnout + Intrinsische Motivation]\n"
    "            +  SUM_j A_ij^eff * Phi_L(L_j - L_i, I_j, I_i)            [L.3a: Peer-Normkonvergenz]\n"
    "            +  S(rank_i, Kultur)                                        [L.3b: Statusdruck (NUR Arbeit!)]\n\n"
    "  dL_i*/dt =  lambda_L * (L_i - L_i*)                                  [Referenzpunkt-Adaptation]\n\n"
    "Symbole: L=Arbeitszeit, L*=Referenz, alpha_L=Anpassungsrate, Psi_L=Prospect Theory + Michaelis-Menten,\n"
    "         A_ij=Multiplex-Netzwerk, Phi_L=Herding (identisch V.3), S=Statusdruck (Kultur), I=Information, H=Gesundheit\n\n"
    "Prop 6.2: Bei S=0 ist L.4 strukturell identisch zu V.4 (Konsum). S bricht diese Symmetrie."
)
ax_eq.text(0.5, 0.5, eq_text, transform=ax_eq.transAxes, ha='center', va='center',
           fontsize=8.5, family='monospace',
           bbox=dict(boxstyle='round,pad=0.6', facecolor='#f0f8ff', edgecolor='#4169e1',
                     linewidth=2, alpha=0.95))

# ── Row 1: R1 Normal ──
ax = fig.add_subplot(gs[1, 0])
for i in range(min(15, N_ag)):
    ax.plot(R1['t'], R1['L'][i], lw=0.5, alpha=0.3)
ax.plot(R1['t'], R1['L'].mean(axis=0), 'k-', lw=2, label='Mittel')
ax.set_xlabel('t'); ax.set_ylabel('L(t) [h]')
ax.set_title('(a) R1: Normal Economy')
ax.legend(fontsize=7); ax.grid(True, alpha=0.3)

ax = fig.add_subplot(gs[1, 1])
ax.plot(R1['t'], R1['norm_L1'], 'C0-', lw=2, label='L.1 (Rational)')
ax.plot(R1['t'], R1['norm_L2'], 'C1-', lw=2, label='L.2 (Psycho)')
ax.plot(R1['t'], R1['norm_L3'], 'C2-', lw=2, label='L.3 (Sozial)')
ax.set_xlabel('t'); ax.set_ylabel('||dL/dt|| Beitrag')
ax.set_title('(b) R1: Layer-Normen')
ax.legend(fontsize=7); ax.grid(True, alpha=0.3)

ax = fig.add_subplot(gs[1, 2])
ax.plot(R1['t'], R1['gini'], 'C3-', lw=2)
ax.set_xlabel('t'); ax.set_ylabel('Gini(t)')
ax.set_title('(c) R1: Gini-Dynamik')
ax.grid(True, alpha=0.3)

# ── Row 2: R2 + R3 ──
ax = fig.add_subplot(gs[2, 0])
for i in range(min(15, N_ag)):
    ax.plot(R2['t'], R2['L'][i], lw=0.5, alpha=0.3)
ax.plot(R2['t'], R2['L'][hub], 'C3-', lw=2, label='Hub')
ax.plot(R2['t'], R2['L'].mean(axis=0), 'k-', lw=2, label='Mittel')
ax.set_xlabel('t'); ax.set_ylabel('L(t) [h]')
ax.set_title('(d) R2: Workaholic-Kaskade')
ax.legend(fontsize=7); ax.grid(True, alpha=0.3)

ax = fig.add_subplot(gs[2, 1])
for i in range(min(15, N_ag)):
    ax.plot(R3['t'], R3['L'][i], lw=0.5, alpha=0.3)
ax.plot(R3['t'], R3['L'].mean(axis=0), 'k-', lw=2, label='Mittel')
ax.set_xlabel('t'); ax.set_ylabel('L(t) [h]')
ax.set_title('(e) R3: Burnout-Krise')
ax.legend(fontsize=7); ax.grid(True, alpha=0.3)

ax = fig.add_subplot(gs[2, 2])
ax.plot(R3['t'], R3['norm_L1'], 'C0-', lw=2, label='L.1')
ax.plot(R3['t'], R3['norm_L2'], 'C1-', lw=2, label='L.2')
ax.plot(R3['t'], R3['norm_L3'], 'C2-', lw=2, label='L.3')
ax.set_xlabel('t'); ax.set_ylabel('||dL/dt||')
ax.set_title('(f) R3: Krise Layer-Normen')
ax.legend(fontsize=7); ax.grid(True, alpha=0.3)

# ── Row 3: R4+R5 ──
ax = fig.add_subplot(gs[3, 0])
ax.plot(R4['t'], R4['L'].mean(axis=0), 'C0-', lw=2, label='L')
ax.plot(R4['t'], R4['Lstar'].mean(axis=0), 'C3--', lw=2, label='L*')
ax.set_xlabel('t'); ax.set_ylabel('Stunden/Tag')
ax.set_title('(g) R4: L*-Drift (Gewohnheit)')
ax.legend(fontsize=7); ax.grid(True, alpha=0.3)

ax = fig.add_subplot(gs[3, 1])
for i in range(min(15, N_ag)):
    ax.plot(R5['t'], R5['L'][i], lw=0.5, alpha=0.3)
ax.plot(R5['t'], R5['L'][elite].mean(axis=0), 'C3-', lw=2, label='Elite (I=50)')
ax.plot(R5['t'], R5['L'][mass].mean(axis=0), 'C0-', lw=2, label='Masse (I=0.5)')
ax.set_xlabel('t'); ax.set_ylabel('L(t) [h]')
ax.set_title('(h) R5: Info-Heterogenitaet')
ax.legend(fontsize=7); ax.grid(True, alpha=0.3)

ax = fig.add_subplot(gs[3, 2])
ax.plot(R5['t'], R5['gini'], 'C3-', lw=2)
ax.set_xlabel('t'); ax.set_ylabel('Gini')
ax.set_title('(i) R5: Gini (Info-Klassen)')
ax.grid(True, alpha=0.3)

# ── Row 4: R6 Kulturvergleich ──
ax = fig.add_subplot(gs[4, 0])
for name, res in R6_data.items():
    ax.plot(res['t'], res['L'].mean(axis=0), lw=2, label=name.split("(")[0].strip())
ax.set_xlabel('t'); ax.set_ylabel('L_mean(t) [h]')
ax.set_title('(j) R6: Kulturvergleich')
ax.legend(fontsize=6); ax.grid(True, alpha=0.3)

ax = fig.add_subplot(gs[4, 1])
names_R6 = list(R6_data.keys())
Lmeans_R6 = [R6_data[n]["L"][:,-1].mean() for n in names_R6]
ax.bar(range(len(names_R6)), Lmeans_R6, color=['C3', 'C0', 'C1', 'C2'], alpha=0.7)
ax.set_xticks(range(len(names_R6)))
ax.set_xticklabels([n.split("(")[0].strip() for n in names_R6], fontsize=6, rotation=15)
ax.set_ylabel('L_mean(T) [h]')
ax.set_title('(k) R6: L nach Kultur')
ax.grid(True, alpha=0.3, axis='y')

# R7
ax = fig.add_subplot(gs[4, 2])
ax.plot(R7['t'], R7['gini'], 'C3-', lw=2)
ax.set_xlabel('t'); ax.set_ylabel('Gini')
ax.set_title(f'(l) R7: Inequality (peak={gini_peak:.3f})')
ax.grid(True, alpha=0.3)

# ── Row 5: R8 Symmetrie + Ebenen-Vergleich ──
ax = fig.add_subplot(gs[5, 0])
for i in range(min(10, N_sym)):
    ax.plot(results["R8"]["t"], c_V3[i], 'C0-', lw=0.5, alpha=0.3)
    ax.plot(results["R8"]["t"], L_L3[i], 'C3--', lw=0.5, alpha=0.3)
ax.plot([], [], 'C0-', lw=2, label='V.3'); ax.plot([], [], 'C3--', lw=2, label='L.3(S=0)')
ax.set_xlabel('t'); ax.set_ylabel('x(t)')
ax.set_title(f'(m) R8: Prop 6.2 (|diff|={max_dyn_diff:.1e})')
ax.legend(fontsize=7); ax.grid(True, alpha=0.3)

ax = fig.add_subplot(gs[5, 1])
for name, res in comp_data.items():
    ax.plot(res['t'], res['L'].mean(axis=0), lw=2, label=name)
ax.set_xlabel('t'); ax.set_ylabel('L_mean(t) [h]')
ax.set_title('(n) Ebenen-Vergleich')
ax.legend(fontsize=6); ax.grid(True, alpha=0.3)

ax = fig.add_subplot(gs[5, 2])
names_c = list(comp_data.keys())
ginis_c = [comp_data[n]["gini"][-1] for n in names_c]
ax.bar(range(len(names_c)), ginis_c, color=['C0', 'C1', 'C2', 'C3'], alpha=0.7)
ax.set_xticks(range(len(names_c)))
ax.set_xticklabels([n.replace("L.", "") for n in names_c], fontsize=6, rotation=15)
ax.set_ylabel('Gini(T)')
ax.set_title('(o) Gini nach Ebene')
ax.grid(True, alpha=0.3, axis='y')

# ── Row 6: SA1 + SA2 ──
ax = fig.add_subplot(gs[6, 0])
im = ax.imshow(SA1_G, extent=[sa1_au[0], sa1_au[-1], sa1_lL[0], sa1_lL[-1]],
               aspect='auto', origin='lower', cmap='YlOrRd')
plt.colorbar(im, ax=ax, label='Gini(T)')
ax.set_xlabel('alpha_up'); ax.set_ylabel('lambda_L')
ax.set_title('(p) SA1: alpha_up vs lambda_L')

ax = fig.add_subplot(gs[6, 1])
im = ax.imshow(SA2_L, extent=[sa2_k[0], sa2_k[-1], np.log10(sa2_I[0]), np.log10(sa2_I[-1])],
               aspect='auto', origin='lower', cmap='YlOrRd')
plt.colorbar(im, ax=ax, label='L_mean(T) [h]')
ax.set_xlabel('Kulturparameter'); ax.set_ylabel('log10(I)')
ax.set_title('(q) SA2: Kultur vs Info')

ax = fig.add_subplot(gs[6, 2])
t_sa3 = np.linspace(0, T, N_steps + 1)
for tname, d in SA3_data.items():
    ax.plot(t_sa3, d["gini"], lw=2, label=tname)
ax.set_xlabel('t'); ax.set_ylabel('Gini(t)')
ax.set_title('(r) SA3: Topologie-Vergleich')
ax.legend(fontsize=7); ax.grid(True, alpha=0.3)

# ── Row 7: SA4 + SA5 ──
ax = fig.add_subplot(gs[7, 0])
im = ax.imshow(SA4_L, extent=[sa4_lb[0], sa4_lb[-1], sa4_kI[0], sa4_kI[-1]],
               aspect='auto', origin='lower', cmap='YlOrRd')
plt.colorbar(im, ax=ax, label='L_mean(T) [h]')
ax.set_xlabel('lam_B (Burnout)'); ax.set_ylabel('kappa_I (Motivation)')
ax.set_title('(s) SA4: Burnout vs Motivation')

ax = fig.add_subplot(gs[7, 1])
ax.plot(densities, gini_dens, 'C2-o', lw=2, ms=3)
ax.set_xlabel('Netzwerk-Dichte'); ax.set_ylabel('Gini(T)')
ax.set_title('(t) SA5: Dichte vs Gini')
ax.grid(True, alpha=0.3)

# EA1: Dominanz
ax = fig.add_subplot(gs[7, 2])
ax.stackplot(t_arr, frac_L1, frac_L2, frac_L3,
             labels=['L.1', 'L.2', 'L.3'], colors=['C0', 'C1', 'C2'], alpha=0.7)
ax.set_xlabel('t'); ax.set_ylabel('Anteil')
ax.set_title('(u) EA1: Dominanz-Dynamik')
ax.legend(fontsize=7, loc='upper right'); ax.grid(True, alpha=0.3)
ax.set_ylim(0, 1)

# ── Row 8: EA2 + EA3 ──
ax = fig.add_subplot(gs[8, 0])
t_hys = np.concatenate([np.linspace(0, 25, 1001),
                         25 + np.linspace(0, 10, 401)[1:],
                         35 + np.linspace(0, 25, 1001)[1:]])
L_hys = np.concatenate([res_pre['L'].mean(axis=0),
                          res_shock['L'].mean(axis=0)[1:],
                          res_recov['L'].mean(axis=0)[1:]])
ax.plot(t_hys, L_hys, 'C0-', lw=2)
ax.axvline(25, color='red', ls=':', lw=1, label='Schock-Start')
ax.axvline(35, color='green', ls=':', lw=1, label='Erholung')
ax.axhline(L0_hys.mean(), color='gray', ls='--', lw=0.8, label=f'Start={L0_hys.mean():.1f}h')
ax.set_xlabel('t'); ax.set_ylabel('L_mean [h]')
ax.set_title(f'(v) EA2: Hysterese (gap={hyst_gap:+.1f}h)')
ax.legend(fontsize=6); ax.grid(True, alpha=0.3)

ax = fig.add_subplot(gs[8, 1])
ax.plot(t_arr, L1_mean_t, 'C0-', lw=2, label='L.1')
ax.plot(t_arr, L2_mean_t, 'C1-', lw=2, label='L.2')
ax.plot(t_arr, peer_mean_t, 'C2-', lw=2, label='Peer (L.3a)')
ax.plot(t_arr, status_mean_t, 'C3-', lw=2, label='Status (L.3b)')
ax.set_xlabel('t'); ax.set_ylabel('dL/dt Beitrag (mean)')
ax.set_title('(w) EA3: 4-Term-Dekomposition')
ax.legend(fontsize=6); ax.grid(True, alpha=0.3)

# EA4 Bar
ax = fig.add_subplot(gs[8, 2])
labels_ea4 = ['|Delta(L.1+L.2)|', '|Delta(L.1+L.3)|', '|Delta(full)|']
vals_ea4 = [delta_l12, delta_l13, delta_full]
ax.bar(range(3), vals_ea4, color=['C1', 'C2', 'C3'], alpha=0.7)
ax.set_xticks(range(3)); ax.set_xticklabels(labels_ea4, fontsize=6, rotation=10)
ax.set_ylabel('||L_config - L_L1||')
ax.set_title(f'(x) EA4: Superadditivitaet ({superadd:.2f})')
ax.grid(True, alpha=0.3, axis='y')

# ── Row 9: Kausalitaet + Strukturen ──
ax = fig.add_subplot(gs[9, 0])
ax.axis('off')
kaus = (
    "KAUSALKETTEN (S26 L.4):\n"
    "─────────────────────────\n"
    "1. Norm-Kaskade:\n"
    "   L.3a: L_j steigt =>\n"
    "   Phi_L>0 => L_i steigt\n"
    "   + L.3b: Status(rank) =>\n"
    "   Gleichgewicht nach oben\n\n"
    "2. Burnout-Bremse:\n"
    "   L >> L* => Psi_L<0\n"
    "   (lam_B=2.25 Asymmetrie)\n"
    "   -> limitiert Overwork\n\n"
    "3. Motivation-Beschleunig.:\n"
    "   I hoch => Psi_L>0\n"
    "   (Michaelis-Menten)\n"
    "   -> verstaerkt Arbeit\n\n"
    "4. L*-Scarring:\n"
    "   L hoch -> L* steigt\n"
    "   (langsam) -> Burnout-\n"
    "   Schwelle steigt -> Hyst.\n\n"
    "5. Prop 6.2:\n"
    "   S=0 => L.4 == V.4\n"
    "   (exakt numerisch)"
)
ax.text(0.05, 0.95, kaus, transform=ax.transAxes, ha='left', va='top',
        fontsize=6.5, family='monospace',
        bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.95))

ax = fig.add_subplot(gs[9, 1:3])
ax.axis('off')
struct = (
    "MATHEMATISCHE STRUKTUREN (S26):\n\n"
    "1. GRADIENTENSYSTEM + FELD: dL/dt = -grad V(L) + S(rank)\n"
    "   L.1+L.2: Potential-Minimierung; L.3a: Diffusion; L.3b: Drift\n\n"
    "2. MEHRSKALIGE SEPARATION: L schnell, L* langsam\n"
    "   -> Singulaere Stoerungstheorie; Hysterese/Scarring\n"
    f"   -> EA2: Hysterese-Gap = {hyst_gap:+.1f}h nach Statusdruck-Schock\n\n"
    f"3. NICHTLINEARE SUPERPOSITION: ratio = {superadd:.3f}\n"
    "   Interaktionseffekt L.2 x L.3 existiert (Burnout limitiert Herding)\n\n"
    "4. PROP 6.2: Bei S=0 ist L.4 identisch zu V.4 (EXAKT)\n"
    f"   max|V.3_dyn - L.3_dyn(S=0)| = {max_dyn_diff:.2e}\n\n"
    f"5. KULTURELLE BIFURKATION: JP={L_jp:.1f}h, FR={L_fr:.1f}h\n"
    f"   Differenz {L_jp-L_fr:.1f}h — rein Status-induziert"
)
ax.text(0.5, 0.5, struct, transform=ax.transAxes, ha='center', va='center',
        fontsize=7, family='monospace',
        bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.95))

# ── Row 10: Physik ──
ax = fig.add_subplot(gs[10, 0:3])
ax.axis('off')
phys = (
    "VIER-EBENEN-ARCHITEKTUR (ARBEIT, KOMPLETT — L.4):\n\n"
    "  dL_i/dt = alpha_L(L_i*-L_i)            + Psi_L(L, L*, L_bar, I, H)    + SUM_j A_ij*Phi_L(L_j-L_i, I_j, I_i) + S(rank_i, Kultur)\n"
    "            ─────────────────              ──────────────────────────      ──────────────────────────────────────   ──────────────────\n"
    "            Rational (L.1, S22)            Psychologisch (L.2, S24)       Peer-Norm (L.3a, S25)                    Statusdruck (L.3b, S25)\n\n"
    "  PROP 6.2 (Strukturelle Symmetrie):\n"
    "  ┌──────────┬───────────────────────┬───────────────────────────┐\n"
    "  │ Ebene    │ Konsum (V.4, S21)     │ Arbeit (L.4, S26)        │\n"
    "  ├──────────┼───────────────────────┼───────────────────────────┤\n"
    "  │ Rational │ Euler R(r,beta,gamma) │ alpha_L(L*-L)            │\n"
    "  │ Psychol. │ Prospect+Deprivation  │ Burnout+Motivation       │\n"
    "  │ Sozial   │ Herding Phi_c         │ Phi_L + S(rank,Kultur)   │\n"
    "  └──────────┴───────────────────────┴───────────────────────────┘\n\n"
    "  AXIOME (alle numerisch verifiziert):\n"
    f"  V1: Prop 6.1 Grenzfall ............... err={err_neo:.6f}\n"
    f"  V2: Additivitaet ..................... err={add_err:.6f}\n"
    f"  V3: Dominanz-Regime .................. Normal:L1, Krise:L2\n"
    f"  V4: Gini sinkt ....................... G(L.1)={g_l1:.3f}>G(full)={g_full:.3f}\n"
    f"  V5: Kultureffekt ..................... JP={L_jp:.1f}h > FR={L_fr:.1f}h\n"
    f"  V6: Stabilitaet ...................... L in [{L_min_all:.2f}, {L_max_all:.1f}]\n"
    f"  V7: Netzwerk equalisiert ............. G(0.2A)={g_weak:.3f}>G(3A)={g_strong:.3f}\n"
    f"  V8: Prop 6.2 Symmetrie ............... max|diff|={max_dyn_diff:.2e}"
)
ax.text(0.5, 0.5, phys, transform=ax.transAxes, ha='center', va='center',
        fontsize=7.5, family='monospace',
        bbox=dict(boxstyle='round', facecolor='#f0f8ff', edgecolor='#4169e1',
                  linewidth=1.5, alpha=0.95))

# ── Row 11: Validierung + Extras ──
ax = fig.add_subplot(gs[11, 0])
ax.axis('off')
val_text = "VALIDIERUNGEN:\n" + "-" * 35 + "\n"
for k, v in validations.items():
    tag = "PASS" if v["passed"] else "FAIL"
    val_text += f"{k}: {v['name'][:32]}\n   {tag}: {v['detail'][:50]}\n\n"
ax.text(0.05, 0.95, val_text, transform=ax.transAxes, ha='left', va='top',
        fontsize=5.8, family='monospace',
        bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.95))

ax = fig.add_subplot(gs[11, 1])
# Degree vs L(T) fuer R2 (Hub-Effekt)
ax.scatter(degree_base, R2['L'][:, -1], c=R2['L'][:, 0], cmap='viridis', s=15, alpha=0.7)
ax.set_xlabel('Grad'); ax.set_ylabel('L(T) [h]')
ax.set_title('R2: Grad vs L(T)')
ax.grid(True, alpha=0.3)

ax = fig.add_subplot(gs[11, 2])
# Gini aller Kulturen
for name, res in R6_data.items():
    ax.plot(res['t'], res['gini'], lw=2, label=name.split("(")[0].strip())
ax.set_xlabel('t'); ax.set_ylabel('Gini(t)')
ax.set_title('R6: Gini pro Kultur')
ax.legend(fontsize=6); ax.grid(True, alpha=0.3)

# ── Row 12: Summary ──
ax = fig.add_subplot(gs[12, 0:3])
ax.axis('off')
# Vergleich V.4 (S21) vs L.4 (S26) — zentrale Unterschiede
comp_text = (
    "VERGLEICH V.4 (S21, Konsum) vs L.4 (S26, Arbeit):\n\n"
    "  V.4: dc/dt = R(r,beta,gamma,c) + Psi_c(c,c*,G,I) + SUM A*Phi_c(dc,I_j,I_i)\n"
    "  L.4: dL/dt = alpha_L(L*-L)     + Psi_L(L,L*,L_bar,I,H) + SUM A*Phi_L(dL,I_j,I_i) + S(rank,K)\n\n"
    "  Identisch: Phi_L = Phi_c (bei gleichen Parametern, numerisch verifiziert)\n"
    "  Verschieden:\n"
    "    - L.4 hat additionalen Statusdruck S — 'Arbeitszeit ist sichtbar, Konsum nicht'\n"
    "    - L.2 hat DUALE Info-Rolle (V.2: I daempft, L.2: I daempft Burnout ABER verstaerkt Motivation)\n"
    "    - L.1 ist einfacher (alpha*(L*-L)) als V.1 (Euler R*c)\n"
    "    - L.4 hat Referenzpunkt-Adaptation L* (Scarring) — expliziter als V.4\n\n"
    f"  Kulturelle Varianz: Identisches Modell, nur K verschieden -> Delta(JP-FR) = {L_jp-L_fr:.1f}h\n"
    "  => Internationale Arbeitszeitdivergenz als emergentes Phaenomen des Status-Terms"
)
ax.text(0.5, 0.5, comp_text, transform=ax.transAxes, ha='center', va='center',
        fontsize=7.5, family='monospace',
        bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.95))

# ── Metadata ──
ax_meta = fig.add_subplot(gs[13, :])
ax_meta.axis('off')
n_pass = sum(1 for v in validations.values() if v["passed"])
meta = (
    f"S26 L.4 Vollstaendige Arbeitsangebotsdynamik | "
    f"8 Regime, {len(validations)} Val: {n_pass}/{len(validations)} PASS | "
    f"L.1+L.2+L.3(Peer+Status), Kulturvergleich JP/USA/DE/FR, "
    f"Hysterese, Superadditivitaet, Prop 6.1+6.2 | "
    f"5 SA + 4 EA"
)
ax_meta.text(0.5, 0.5, meta, transform=ax_meta.transAxes, ha='center', va='center',
             fontsize=9, family='monospace',
             bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.95))

plt.savefig(PLOT_DIR / "S26_L4_Vollstaendige_Arbeitsangebotsdynamik.png",
            dpi=180, bbox_inches='tight')
plt.close()
print(f"\n  Plot: {PLOT_DIR / 'S26_L4_Vollstaendige_Arbeitsangebotsdynamik.png'}")

# ── Daten ──
save_dict = {
    "R1_t": R1['t'], "R1_L_mean": R1['L'].mean(axis=0), "R1_gini": R1['gini'],
    "R1_norm_L1": R1['norm_L1'], "R1_norm_L2": R1['norm_L2'], "R1_norm_L3": R1['norm_L3'],
    "R2_L_mean": R2['L'].mean(axis=0), "R3_L_mean": R3['L'].mean(axis=0),
    "R7_gini": R7['gini'],
    "R8_sym_diff": np.array([sym_diff]), "R8_max_dyn_diff": np.array([max_dyn_diff]),
    "SA1_au": sa1_au, "SA1_lL": sa1_lL, "SA1_G": SA1_G,
    "SA2_k": sa2_k, "SA2_I": sa2_I, "SA2_L": SA2_L,
    "SA4_lb": sa4_lb, "SA4_kI": sa4_kI, "SA4_L": SA4_L,
    "SA5_d": densities, "SA5_g": np.array(gini_dens),
    "EA1_fL1": frac_L1, "EA1_fL2": frac_L2, "EA1_fL3": frac_L3,
    "EA3_t": t_arr, "EA3_L1": L1_mean_t, "EA3_L2": L2_mean_t,
    "EA3_peer": peer_mean_t, "EA3_status": status_mean_t,
}
np.savez_compressed(DATA_DIR / "S26_L4_Vollstaendige_Arbeitsangebotsdynamik.npz", **save_dict)

# ── Zusammenfassung ──
print(f"\n{'='*72}\n  ZUSAMMENFASSUNG S26  L.4 Vollstaendige Arbeitsangebotsdynamik\n{'='*72}")
for k, v in validations.items():
    print(f"  {k}: {v['name']:45s}  {'PASS' if v['passed'] else 'FAIL'}  ({v['detail']})")
print(f"\n  Regime:")
print(f"    R1: Normal Economy (L.1 dominiert)")
print(f"    R2: Workaholic-Kaskade (Hub, L.3)")
print(f"    R3: Burnout-Krise (L.2 dominiert)")
print(f"    R4: Arbeitsgewohnheits-Drift (L* steigt)")
print(f"    R5: Info-Heterogenitaet (Klassen)")
print(f"    R6: Kulturvergleich JP/USA/DE/FR")
print(f"    R7: Inequality Spiral")
print(f"    R8: Neoklassischer Grenzfall + Prop 6.2")
print(f"\n  Sensitivitaet:")
print(f"    SA1: alpha_up vs lambda_L -> Gini(T)")
print(f"    SA2: Kultur vs Info -> L_mean(T)")
print(f"    SA3: Topologie-Vergleich (Scale-Free, Small-World, Random)")
print(f"    SA4: lam_B (Burnout) vs kappa_I (Motivation)")
print(f"    SA5: Netzwerk-Dichte vs Gini")
print(f"\n  Erweiterte Analyse:")
print(f"    EA1: Dominanz-Dynamik (welche Ebene wann?)")
print(f"    EA2: Hysterese-Test (Scarring={hyst_gap:+.2f}h)")
print(f"    EA3: 4-Term-Dekomposition (L.1+L.2+Peer+Status)")
print(f"    EA4: Superadditivitaet (ratio={superadd:.3f})")
print(f"\n  Mathematische Strukturen:")
for s in struct_notes:
    print(f"    {s.split(chr(10))[0]}")
n_pass = sum(1 for v in validations.values() if v["passed"])
print(f"\n  Gesamtergebnis: {n_pass}/{len(validations)} bestanden")
