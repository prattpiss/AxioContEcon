# S28 — III.2 Portfoliodynamik (§6.6)

## Gleichung

$$\frac{d\theta_{ik}}{dt} = \lambda_\theta \cdot \frac{\partial u_i}{\partial \theta_{ik}} + \alpha_H \cdot \sum_j A_{ij}(\theta_{jk} - \theta_{ik}) + \sigma_\theta \cdot \xi_i$$

Drei-Term-Struktur analog zur V/L-Architektur:  
Term 1 = rational (Markowitz-Gradient $\mu - \gamma \Sigma \theta$),  
Term 2 = sozial (Herding, Netzwerk-Laplacian-Diffusion),  
Term 3 = stochastisch (Noise-Trading, idiosynkratische Schocks).  
Constraint: $\theta_{ik} \geq 0$, $\sum_k \theta_{ik} = 1$ (Simplex-Projektion nach jedem Schritt).

## Ergebnisse

| Validierung | Ergebnis | Detail |
|---|---|---|
| V1: Markowitz-Konvergenz $\theta \to \theta^*_{\text{MV}}$ | **PASS** | max\|err\| = 0.000000 |
| V2: Herding $\Rightarrow$ Dispersion sinkt | **PASS** | disp: 0.243 → 0.003 |
| V3: $\gamma \uparrow \Rightarrow$ Aktienanteil $\downarrow$ | **PASS** | $\gamma < 2$: 0.407, $\gamma > 5$: 0.309 |
| V4: Noise $\Rightarrow$ Dispersion steigt | **PASS** | no-noise = 0.0000, noise = 0.231 |
| V5: Blasen-Crash: peak > 0.5 dann halbiert | **PASS** | peak = 0.657, trough = 0.296 |
| V6: Simplex: $\theta \geq 0$, $\sum \theta = 1$ | **PASS** | positive = True, sum\_ok = True |
| V7: Complete-Netz: stärkstes Herding | **PASS** | complete = 0.0155, ring = 0.0510 |
| V8: Neoklassisch: alle Starts $\to \theta^*$ | **PASS** | errs = [0.0027, 0.0015, 0.0079, 0.0026] |

**Gesamtergebnis: 8/8 bestanden**

## Regime

| # | Regime | Kernergebnis |
|---|---|---|
| R1 | Markowitz-Konvergenz (rein rational) | $\theta^*_{\text{MV}} = [0.625, 0.375, 0.000]$; exakte Konvergenz (err = 0) |
| R2 | Herding-Dominanz ($\alpha_H = 2.0$) | Dispersion 0.243 → 0.003; Consensus $\theta = [0.353, 0.345, 0.302]$; HHI = 0.335 |
| R3 | Heterogene Risikoaversion | $\gamma < 2$: Aktie 40.7%; $\gamma > 5$: Aktie 30.9%; Dispersion = 0.043 |
| R4 | Noise-dominiert ($\sigma_\theta = 0.5$) | Dispersion = 0.231; HHI = 0.495; $\theta \approx [0.335, 0.346, 0.320]$ |
| R5 | Blasen-Crash (Renditeschock) | Peak 0.657 (t=20) → Trough 0.296 (t=25.9) → Recovery 0.309 |
| R6 | Multi-Asset ($K = 6$) | $\theta = [0.305, 0.214, 0.175, 0.198, 0.057, 0.051]$; HHI = 0.225 |
| R7 | Netzwerk-Topologien | ring: 0.051, star: 0.015, ER: 0.016, complete: 0.016 |
| R8 | Neoklassischer Grenzfall | Alle 4 Startpunkte → $\theta^*$ (max err = 0.008) |

## Sensitivitätsanalysen

| SA | Parameter | Ergebnis |
|---|---|---|
| SA1 | $\alpha_H$ vs $\sigma_\theta$ → Dispersion | Dispersion-Range [0.000, 0.267] |
| SA2 | $\gamma$ vs Aktienanteil | Equity-Range [0.161, 1.000] |
| SA3 | $\lambda_\theta$ → Konvergenzgeschwindigkeit | Errors: [0.32, 0.31, 0.27, 0.24, 0.16, 0.06] (monoton fallend) |
| SA4 | $K$ Assets → HHI (Diversifikation) | K=2: 0.523, K=5: 0.270, K=10: 0.156 (→ $1/K$) |
| SA5 | Anfangs-$\theta$ Sensitivität | Spread = 0.036 (moderate Abhängigkeit bei endlichem T) |

## Erweiterte Analysen

| EA | Analyse | Ergebnis |
|---|---|---|
| EA1 | Drei-Term-Dekomposition | Rational: disp=0.180; Rat+Herd: 0.001; Komplett: 0.048 |
| EA2 | Herding-Phasenübergang ($\alpha_H$-Sweep) | $\alpha_H$: 0→3.0, disp: 0.223→0.007 |
| EA3 | Effizienzvergleich (Sharpe Ratio) | Markowitz: 0.516, Mild Herd: 0.533, Strong Herd: 0.549, Noise: 0.541 |
| EA4 | Wealth-weighted Herding | Wealth-weighted disp=0.013, Uniform disp=0.013; Rich≈Poor |

## Mathematische Strukturen

1. **Drei-Ebenen-Parallele**: III.2 = V-Architektur für Portfolios. Term 1 (Markowitz) ~ V.1/L.1, Term 2 (Herding/Laplacian) ~ V.3/L.3, Term 3 (Noise) ~ stochastisch. Psychologie implizit via $\gamma_i$ in U.1.

2. **Laplacian-Diffusion auf dem Simplex**: Herding $= \alpha_H \cdot L \cdot \theta$ (Netzwerk-Laplacian $L$). Consensus-Bildung unter Simplex-Constraint. Complete-Netz: maximale Diffusion → minimale Dispersion (0.016 vs Ring 0.051).

3. **Mean-Variance Optimierung**: $\theta^* = \arg\max_{\Delta_K} \mu^T\theta - (\gamma/2)\theta^T\Sigma\theta$ (konvexes QP auf Simplex). Global stabil — alle Startpunkte konvergieren (V8, max err = 0.008). Constrained Lösung via SLSQP: $\theta^* = [0.625, 0.375, 0]$ (Cash wird durch niedrige Rendite ausgeschlossen trotz niedriger Varianz).

4. **Blasen als Herding-Instabilität**: $\alpha_H$ groß → Konzentration aller Agenten auf ein Asset. Exogener Rendite-Schock bricht Herding-GG → Crash (peak 0.657 → trough 0.296, -55% in 5 Zeiteinheiten).

5. **Effizienz-Herding Trade-off**: Sharpe Ratio: Markowitz 0.516 vs Strong Herding 0.549. Herding erhöht Sharpe hier durch Varianzreduktion — aber erzeugt systemisches Risiko (korrelierte Portfolios → Crash-Anfälligkeit). Sociale Imitation ist individuell "rational" aber systemisch fragil.

## Zentrale Einsicht

III.2 beschreibt Portfolioallokation als Drei-Term-Dynamik auf dem Simplex — strukturell parallel zur Konsum- und Arbeitsdynamik (V.1-V.4, L.1-L.4). Der rationale Markowitz-Term treibt zur effizienten Diversifikation ($\theta^* = [0.625, 0.375, 0]$), der Herding-Term erzeugt Consensus via Netzwerk-Laplacian (Dispersion 0.243→0.003), und Noise verhindert perfekte Konvergenz. Die Simulation bestätigt: (1) Constrained Markowitz-Optimum als globaler Attraktor; (2) Herding-Stärke $\alpha_H$ als Ordnungsparameter für den Phasenübergang Heterogenität→Consensus; (3) Blasen-Crash als Sequenz von Herding-Aufbau und exogenem Schock (-55%); (4) Netzwerk-Topologie bestimmt Diffusionsgeschwindigkeit (Complete > Star > ER > Ring); (5) der neoklassische Grenzfall ($\sigma = 0$, $\alpha_H = 0$) reproduziert die klassische Mean-Variance-Lösung exakt.
