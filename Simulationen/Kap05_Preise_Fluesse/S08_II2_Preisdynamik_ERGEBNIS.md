# S08 – Fundamentale Preisdynamik II.2 (§5.1): Ergebnisbericht

## Gleichung (exakt aus Monographie)

$$\dot{p}_k = \frac{1}{\lambda_k}(D_k - S_k) + \eta_k \, p_k - \frac{\varphi_k}{\mathcal{I}_k + \varepsilon}$$

Drei Mechanismen:
1. **Walrasianische Anpassung** $(D-S)/\lambda$: Preis steigt bei Überschussnachfrage
2. **Inflationserwartung** $\eta \cdot p$: Selbstverstärkender Drift (Blase/Inflation)
3. **Illiquiditätsprämie** $-\varphi/(\mathcal{I}+\varepsilon)$: Preisdruck bei Informationsmangel

## Klassifikation

| Variable | Typ | Einheit | Modellierung |
|----------|-----|---------|-------------|
| $p_k(t)$ | **endogen** | Währung/ME | ODE-Lösung |
| $D_k(t)$ | exogen (→V.1) | ME/a | $D_0 + D_{\rm amp}\sin(\omega_D t)$ |
| $S_k(t)$ | exogen (→III.3) | ME/a | $S_0 + S_{\rm amp}\sin(\omega_S t + \varphi_{\rm shift})$ |
| $\eta_k(t)$ | exogen (→III.4) | 1/a | stückweise konstant |
| $\mathcal{I}_k(t)$ | exogen (→II.3) | dimlos | $I_0 \exp(-\gamma_I \max(t-t_c,0))$ |
| $\lambda_k$ | Parameter | ME·a/Wäh | 5–100 |
| $\varphi_k$ | Parameter | Wäh/a | 0.01–1.5 |
| $\varepsilon$ | Parameter | dimlos | 0.005–0.01 |

## Ergebnisse: 5 Regime

| Regime | Beschreibung | p(T) | Term-Dominanz | V1 |
|--------|-------------|------|---------------|-----|
| R1 Normal | Walras dominiert, I hoch | 10.16 | Walras 97% | ✅ 4.5e-6 |
| R2 Blase | η=5%/a, D>S | 446.9 | η·p 92% | ✅ 1.2e-7 |
| R3 Krise | I→0 ab t=25 | 0 (Floor) | -φ/I 100% | ✅ 1.9e-4 |
| R4 Stagflation | η>0 trotz D<S | 46.43 | η·p 79% | ✅ 2.1e-7 |
| R5 Gleichgewicht | D≈S, η=π*=2% | 32.62 | η·p 99% | ✅ 2.5e-8 |

### Ökonomische Interpretation

- **R1 (Normal)**: Preis oszilliert um Ausgangswert (~±8%), getrieben von D-S-Schwankungen. Illiquidity-Term vernachlässigbar (I=5 → φ/(I+ε) ≈ 0.004). *Typischer effizienter Markt.*
- **R2 (Blase)**: Exponentielles Wachstum p(60) ≈ 45× p₀. η·p-Term dominiert → positive Rückkopplung. D>S verstärkt. *Analogie: US-Immobilien 2003-07, Krypto 2020-21.*
- **R3 (Krise)**: Preis stabil bis t=25, dann rapider Kollaps. I fällt exponentiell → -φ/(I+ε) explodiert auf -140/a. *Analogie: Lehman 2008, Evergrande 2021 — Liquiditäts-Todesspirale.*
- **R4 (Stagflation)**: Trotz D<S (Angebotsüberschuss -10 ME/a) steigt p um Faktor 4.6 in 60 Jahren. η·p-Feedback überkompensiert Walras-Korrektur. *Analogie: 1970er Ölschock.*
- **R5 (Gleichgewicht)**: p(60)/p₀ = 3.26 ≈ exp(0.02×60) = 3.32. Fast reine 2%-Inflation. φ-Term ($\varphi/(I+\varepsilon) = 0.005$) vernachlässigbar. *Analogie: Fed-Inflationsziel.*

## Validierungen

| Test | Methode | Ergebnis |
|------|---------|----------|
| V1 | II.2-Identität (aktive Region) | Alle 5 Regime ✅ (rel. Fehler ≤ 1.9e-4) |
| V2 | Reine Blase: D=S, φ=0, η=0.05 → p = p₀·exp(ηt) | max rel. Fehler = 3.7e-15 ✅ |
| V3 | Walras-GG: η=0, φ=0, D=a-bp → p* = (D₀−S₀)/β | p(100) = 10.000000, ε = 1.1e-11 ✅ |
| V4 | Prop 5.1: 80-Punkt I-Sweep, 4 Regime sichtbar | Übergang bei I ≈ 0.3 (Stress), I < 0.05 (Krise) ✅ |
| V5 | 625-Punkt Sensitivität λ × φ | p(40)/p(0) ∈ [0, 6.84] ✅ |

## Numerik

- **Solver**: RK45 (Dormand-Prince), rtol=1e-10, atol=1e-12, max_step=0.05
- **Regularisierung**: p ≥ 1e-6 (Floor), ε ∈ {0.005, 0.01}
- **Singularitätsbehandlung**: I → 0 erzeugt -φ/ε, begrenzt durch Floor-Clipping
- **625-Punkt Sensitivität**: rtol=1e-8, max_step=0.5 (relaxiert für Performance)

## Prop 5.1 — Regime-Taxonomie (bestätigt)

Proposition 5.1 der Monographie definiert Regime durch $\mathcal{I}_k$:
- **Gleichgewicht** ($\mathcal{I} > 3$): φ-Term < 0.2, Walras konvergiert → ṗ ≈ 0
- **Normal** ($0.3 < \mathcal{I} < 3$): Alle Terme vergleichbar
- **Stress** ($0.05 < \mathcal{I} < 0.3$): φ-Term dominiert, p fällt
- **Krise** ($\mathcal{I} < 0.05$): -φ/(I+ε) divergiert → Preiskollaps

**Bestätigt**: Panel (h) zeigt den kontinuierlichen Übergang von p(30)≈10 (I=10) zu p(30)=0 (I<0.05).

## Kopplungen (für spätere Simulationen)

- $D_k, S_k$ → werden endogen in V.1 (§6.1) und III.3 (§6.6)
- $\eta_k$ → wird endogen in III.4 (§6.7) — Erwartungsbildung
- $\mathcal{I}_k$ → wird endogen in II.3 (§5.6) — Informationsdynamik
- Stochastische Erweiterung VIII.1 (§10.1): $dp = [\text{II.2}]dt + \sigma_k p\, dW$

## Dateien

- `S08_II2_Preisdynamik.py` — Simulation (523 Zeilen)
- `../../Ergebnisse/Plots/S08_II2_Preisdynamik.png` — 12 Panels + Metadaten
- `../../Ergebnisse/Daten/S08_II2_Preisdynamik.npz` — Rohdaten
