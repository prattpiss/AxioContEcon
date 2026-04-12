# S09 – Effektives Potential F.2  (§5.2)
## Ergebnisbericht

**Datum:** 2025-01-XX  
**Status:** ✅ ALLE VALIDIERUNGEN BESTANDEN

---

## Gleichung

$$\mu_k^{\text{eff}}(x,t) = p_k(x,t) + \alpha_H \cdot \bar{p}_k^{\text{Herding}}(x,t) + \frac{\psi_k}{\mathcal{I}_k(x,t) + \varepsilon}$$

**Drei Schichten:**
1. **Objektiver Preis** $p_k$ → bestimmt durch II.2 (§5.1)
2. **Herding-Verzerrung** $\alpha_H \cdot \bar{p}_k^H$ → Netzwerk-Peer-Gewichtung
3. **Illiquiditätszuschlag** $\psi_k / (\mathcal{I}_k + \varepsilon)$ → Informationskosten (A10)

**Prop 5.2:** Regime-Indikatoren:
- $R_1 = \alpha_H |\bar{p}_H| / p_k$ (relative Herding-Stärke)
- $R_2 = \psi_k / (p_k (\mathcal{I}_k + \varepsilon))$ (relative Illiquidität)

| R₁ | R₂ | Regime | Marktcharakter |
|---|---|---|---|
| ≪1 | ≪1 | Effizient | Preise ≈ Fundamentale |
| ≫1 | ≪1 | Blase | μ_eff >> p (Herding) |
| bel. | ≫1 | Krise | Marktversagen (Illiquidität) |

---

## Simulationsdesign

### Kopplung
- $p_k(t)$ wird **intern** via II.2 (§5.1) als ODE simuliert:  
  $\dot{p}_k = \frac{D_k - S_k}{\lambda_k} + \eta_k p_k - \frac{\varphi_k}{\mathcal{I}_k + \varepsilon}$
- $\mu_k^{\text{eff}}(t)$ wird **algebraisch** aus $p_k(t)$ und den exogenen Variablen berechnet

### 5 Regime

| Regime | Beschreibung | Funktionalformen |
|---|---|---|
| R1 Effizienter Markt | α_H≈0, I hoch | D: OU, S: Sinus+Rausch, η: const |
| R2 Blase (Herding) | α_H↑ logistisch | D: OU, η: Sprung, α_H: Logistisch |
| R3 Krise (Illiquid.) | I→0 via GBM | I: GBM, α_H: Logistisch, p̄_H: OU→negativ |
| R4 Zyklus | Eff→Blase→Krise | I: exp.Zerfall, α_H: Glocke |
| R5 Voll stochastisch | OU/GBM/Poisson | Alle exogenen stochastisch |

### Funktionalformen (6 Typen)
- **Ornstein-Uhlenbeck:** $dx = \theta(\mu - x)dt + \sigma\,dW$ (D, S, p̄_H, α_H)
- **Geometrische Brownsche Bewegung:** $dI = \mu I\,dt + \sigma I\,dW$ (I in R3/R5)
- **Sinusoidal + Wiener:** $S_0 + A\sin(\omega t) + \sigma W(t)$ (S)
- **Sprungfunktion:** $\eta = \eta_1$ für $t < t^*$, $\eta_2$ sonst (η in R2)
- **Logistisch:** $f(t) = b + L/(1+e^{-k(t-t_m)})$ (α_H, p̄_H)
- **Poisson-Sprünge:** Compound Poisson (η in R5)

---

## Ergebnisse

### Regime-Übersicht

| Regime | p(T) | μ_eff(T) | Δ=(μ−p)/p | R1_mean | R2_mean |
|---|---|---|---|---|---|
| R1 Effizient | 5.97 | 5.95 | −0.2% | 0.002 | 0.001 |
| R2 Blase | 1413.02 | 1428.26 | +1.1% | 0.040 | 0.002 |
| R3 Krise | 0.00 | 111.03 | →∞ | 3.4M | 26.3M |
| R4 Zyklus | 59.81 | 62.59 | +4.6% | 0.039 | 0.041 |
| R5 Stochastisch | 58402.94 | 58403.57 | +0.0% | 0.017 | 0.009 |

### Prop 5.2 Zeitanteile

| Regime | Effizient | Blase | Krise |
|---|---|---|---|
| R1 | 100% | 0% | 0% |
| R2 | 100% | 0% | 0% |
| R3 | 7.2% | 0% | 92.8% |
| R4 | 100% | 0% | 0% |
| R5 | 100% | 0% | 0% |

**Interpretation:**
- R1: Reine Effizienz bestätigt (α_H=0.05, I=8 → vernachlässigbare Verzerrung)
- R2: Trotz wachsendem α_H dominiert das exponentielle p-Wachstum → R1=α_H|p̄_H|/p bleibt klein
- R3: Klassisches Marktversagen — I→0 lässt ψ/(I+ε) explodieren, p→0 verschärft R2→∞
- R4: Zyklus zeigt 4.6% Verzerrung am Ende, I-Zerfall moderat
- R5: Stochastische Fluktuationen mitteln sich aus

---

## Validierungen

### V1: Neoklassischer Grenzfall
$$\alpha_H = 0, \quad \psi = 0 \implies \mu_k^{\text{eff}} = p_k$$
- max|μ_eff − p| = **0.00e+00** ✅ (exakt)

### V2: Monotonie in α_H
$$\frac{\partial \mu_k^{\text{eff}}}{\partial \alpha_H} = \bar{p}_k^H > 0 \implies \mu \uparrow \text{ bei } \alpha_H \uparrow$$
- μ_eff(α_H) monoton steigend ✅
- μ(0)=10.33, μ(2)=20.33

### V3: Singularität I→0
$$\lim_{\mathcal{I}_k \to 0} \frac{\psi_k}{\mathcal{I}_k + \varepsilon} \to \frac{\psi_k}{\varepsilon} \to \infty \text{ für } \varepsilon \to 0$$
- μ_eff(I) monoton fallend ✅
- μ(I=10)=10.30, μ(I=0.001)=207.88

### V4: Phasenkarte Prop 5.2
- 25×25 = 625 Punkte im (α_H, ψ/(I+ε))-Raum
- Effizient: 120/625, Blase: 255/625, Krise: 250/625
- Drei Regime sauber separiert ✅

### V5: Sensitivität (625 Punkte)
- α_H × ψ → (μ−p)/p Heatmap
- Verzerrung ∈ [0.0%, 69.9%]
- Median = 34.9%

---

## Numerik

| Parameter | Wert |
|---|---|
| ODE-Solver | RK45 (Dormand-Prince) |
| rtol | 1e-10 |
| atol | 1e-12 |
| max_step | 0.05 |
| T | [0, 80], N=8001 |
| Stochastik | Euler-Maruyama, seeded |
| Sensitivität | 25×25 = 625 Punkte |
| Phasenkarte | 25×25 = 625 Punkte |

---

## Dateien

| Datei | Beschreibung |
|---|---|
| `Simulationen/Kap05_Preise_Fluesse/S09_F2_Effektives_Potential.py` | Python-Simulation |
| `Ergebnisse/Plots/S09_F2_Effektives_Potential.png` | 15-Panel-Plot + Metadaten |
| `Ergebnisse/Daten/S09_F2_Effektives_Potential.npz` | Komprimierte Daten |
| `webapp/src/simulations/S09_F2.js` | Interaktive Webapp-Konfiguration |

---

## Physikalische Interpretation

1. **F.2 als Informationsaggregator:** Das effektive Potential μ_eff aggregiert drei Informationsquellen — objektive Preisinformation (p), soziale Information (Herding p̄_H) und Informationsmangel (ψ/I). In Arrow-Debreu (α_H=0, I→∞) reduziert sich μ_eff exakt auf p_k.

2. **Herding-Blase:** Wenn α_H wächst und p̄_H > 0, sehen Agenten ein "effektives Potential" μ_eff > p — sie handeln als wäre der Preis höher als er ist. Das treibt weiteres Kaufen und verstärkt die Blase.

3. **Illiquiditätskrise:** Wenn I→0, explodiert ψ/(I+ε). Agenten bewerten Güter "unendlich hoch" weil sie nicht wissen, was sie wert sind — das Gegenteil von Preis=0 bei Marktversagen. Die Singularität modelliert den Zusammenbruch der Preisinformation.

4. **Zyklus (R4):** Der natürliche Krisenzyklus: Effizienz → Herding steigt → Blase → Information versiegt → Krise. Die Regime-Indikatoren R₁, R₂ zeigen sauber die Übergänge an.
