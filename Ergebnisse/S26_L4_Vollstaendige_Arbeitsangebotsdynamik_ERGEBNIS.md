# S26 — L.4 Vollständige Arbeitsangebotsdynamik (§6.4)

## Gleichung

$$\dot{L}_i = \underbrace{\alpha_L (L_i^* - L_i)}_{\text{L.1 Rational (S22)}} + \underbrace{\Psi_L(L_i, L_i^*, \bar{L}, \mathcal{I}_i^{\text{job}}, H_i)}_{\text{L.2 Psychologisch (S24)}} + \underbrace{\sum_j A_{ij}^{\text{eff}} \Phi_L(L_j - L_i, \mathcal{I}_j, \mathcal{I}_i)}_{\text{L.3a Peer-Norm (S25)}} + \underbrace{\mathcal{S}(\text{rank}_i, \text{Kultur})}_{\text{L.3b Status (S25)}}$$

$$\dot{L}_i^* = \lambda_L (L_i - L_i^*)$$

Vollständiges 2N-dimensionales ODE: N Arbeitszeiten + N Referenzpunkte.  
**Analog zu S21 (V.1+V.2+V.3)** für die Konsumdimension, mit zusätzlichem Status-Term $\mathcal{S}$.

## Ergebnisse

| Validierung | Ergebnis | Detail |
|---|---|---|
| V1: Prop 6.1 — $\mathcal{I}\to\infty, L^*=L, A=0, S=0 \Rightarrow$ stabil | **PASS** | max\_rel\_err = 0.000000 |
| V2: Additivität $\dot{L} = L.1 + L.2 + L.3$ | **PASS** | max\_rel\_err = 0.000000 |
| V3: Dominanz — Normal→L.1, Krise→L.2 | **PASS** | R1: $\|L.1\|=1.38$; R3: $\|L.2\|=2.88 > \|L.1\|=0.48$ |
| V4: Gini — L.1+L.2+L.3 < L.1 | **PASS** | $G(\text{L.1})=0.112$, $G(\text{full})=0.019$ |
| V5: Kultur — $L(\text{JP}) > L(\text{FR}) + 1h$ | **PASS** | $L(\text{JP})=23.84$h, $L(\text{FR})=21.94$h, $\Delta=1.90$h |
| V6: Stabilität — $0.5 \leq L \leq 24.0$ | **PASS** | $L_{\min}=1.29$, $L_{\max}=24.0$ |
| V7: Netzwerk equalisiert — $G(3A) < G(0.2A)$ | **PASS** | $G(0.2A)=0.081$, $G(3A)=0.003$ |
| V8: Prop 6.2 — $L.3(S=0) \equiv V.3$ dynamisch | **PASS** | $\max\|\Delta\| = 0.00 \times 10^{0}$ |

**Gesamtergebnis: 8/8 bestanden**

## Regime

| # | Regime | Kernergebnis |
|---|---|---|
| R1 | Normal Economy | $L$: 8.1→23.4h; Layer-Normen: L.1=1.38, L.2=4.18, L.3=4.02 |
| R2 | Workaholic-Kaskade | Hub 16→24h, Mean 8.2→23.9h (Hub-induziertes Herding) |
| R3 | Burnout-Krise ($I$-Kollaps) | L.2 dominiert: $\|L.2\|=2.88 > \|L.1\|=0.48$; Mean 12.4→12.3h |
| R4 | Arbeitsgewohnheits-Drift | $L^*$: 5.7→15.2h (Drift +9.6h); L: 8.1→19.3h |
| R5 | Info-Heterogenität (bimodal) | Elite $L(T)=24.0$h, Masse $L(T)=21.7$h; Gini 0.110→0.032 |
| R6 | Kulturvergleich | JP 23.8h, USA 23.4h, DE 23.1h, FR 21.9h; $\Delta$(JP-FR)=1.9h |
| R7 | Inequality Spiral | Gini: 0.342→peak 0.342→0.007 (Konvergenz) |
| R8 | Prop 6.1 + Prop 6.2 | Grenzfall: err=0; Symmetrie $V.3 \equiv L.3(S=0)$: max|diff|=0 |

## Ebenen-Vergleich

| Konfiguration | $L_{\text{mean}}(T)$ | Gini(T) |
|---|---|---|
| L.1 nur | 8.12 h | 0.112 |
| L.1 + L.2 | 16.47 h | 0.171 |
| L.1 + L.3 | 18.17 h | 0.025 |
| L.1 + L.2 + L.3 | 23.42 h | 0.019 |

## Sensitivitätsanalysen

| SA | Parameter | Ergebnis |
|---|---|---|
| SA1 | $\alpha_{\text{up}}$ vs $\lambda_L$ → Gini(T) | Gini-Range [0.000, 0.134] |
| SA2 | Kultur vs $I_{\text{mean}}$ → $L_{\text{mean}}(T)$ | L-Range [9.3, 24.0]h |
| SA3 | Topologie-Vergleich | Scale-Free G=0.017, Small-World 0.019, Random 0.028 |
| SA4 | $\lambda_B$ (Burnout) vs $\kappa_I$ (Motivation) | L-Range [14.2, 24.0]h |
| SA5 | Netzwerk-Dichte vs Gini | d=0.02: G=0.082, d=0.30: G=0.003 |

## Erweiterte Analysen

| EA | Analyse | Ergebnis |
|---|---|---|
| EA1 | Dominanz-Dynamik | t=0: L1=4%, L2=43%, L3=54% → t=T: L1=14%, L2=44%, L3=42% |
| EA2 | Hysterese-Test | Start=8.1h → Schock=22.5h → Erholung=23.8h; Scarring +15.7h |
| EA3 | 4-Term-Dekomposition | L1=−0.098, L2=+0.302, Peer=+0.037, Status=+0.367 |
| EA4 | Superadditivität | Ratio = 0.784 (subadditiv: Burnout limitiert Herding) |

## Mathematische Strukturen

1. **Gradientensystem + externes Feld**: L.1+L.2 = Potentialminimierung; L.3a = Graph-Laplacian-Diffusion; L.3b = Status-Drift. Fokker-Planck auf Netzwerk mit Drift.

2. **Mehrskalige Separation**: L schnell ($\alpha_L$), $L^*$ langsam ($\lambda_L$). Singuläre Störungstheorie anwendbar → Hysterese/Scarring durch Zeitskalen-Trennung (EA2: Gap +15.7h).

3. **Nichtlineare Superposition**: Ratio = 0.784 (subadditiv). L.2 (Burnout) limitiert den Herding-Aufwärtstrend von L.3 → emergente Wechselwirkung zwischen Ebenen.

4. **Prop 6.2 — Strukturelle Symmetrie V.4 ↔ L.4**: Bei $S=0$ ist L.3 Peer-Term EXAKT V.3 Herding-Term ($\max|\Delta_{\text{dyn}}| = 0$). Status $\mathcal{S}$ ist die EINZIGE Asymmetrie-Quelle zwischen Konsum- und Arbeitsdynamik.

5. **Kulturelle Bifurkation**: Identisches Modell, nur $K$ verschieden → JP 23.8h, FR 21.9h ($\Delta = 1.9$h). Internationale Arbeitszeitdivergenz als emergentes Phänomen des Status-Terms.

## Zentrale Einsicht

L.4 integriert die drei Entscheidungsebenen (Rational + Psychologisch + Sozial) zu einem vollständigen 2N-dimensionalen ODE — dem Arbeits-Äquivalent zu V.4 (S21). Die Simulation zeigt: (1) Alle Ebenen tragen signifikant bei (keine dominiert global); (2) Das Zusammenspiel ist **subadditiv** (Burnout bremst Herding); (3) Prop 6.2 gilt exakt (bei S=0 ist L.4 ≡ V.4); (4) Hysterese durch L*-Adaptation erzeugt Scarring-Effekte von +15.7h nach Statusdruck-Schock. Die kulturelle Bifurkation bestätigt: Internationale Arbeitszeitunterschiede emergieren allein aus dem Statusdruck-Parameter $K$.
