# S15 — U.2 Aufmerksamkeitsgewichte + U.3 Effektiver Preis

## Gleichungen

**U.2 Aufmerksamkeitsgewicht:**
$$\omega_{k,i} = \omega(\mathcal{I}_i) : \mathbb{R}_+^K \to \Delta^{K-1}$$

| Form | Formel |
|---|---|
| Softmax | $\omega_k = \frac{\mathcal{I}_k^\eta}{\sum_j \mathcal{I}_j^\eta}$ |
| Probit | $\omega_k = \frac{\Phi(\mathcal{I}_k/\sigma)}{\sum_j \Phi(\mathcal{I}_j/\sigma)}$ |
| Linear | $\omega_k = \frac{\mathcal{I}_k}{\sum_j \mathcal{I}_j}$ (= Softmax η=1) |

**U.3 Effektiver Preis:**
$$p_k^{\text{eff}} = p_k \cdot \left(1 + \frac{\psi_k}{\mathcal{I}_k + \varepsilon}\right)$$

## Regime (7)

| Regime | Beschreibung |
|---|---|
| R1 | Softmax η-Sweep (η = 0.3, 0.5, 1, 2, 5, 10) |
| R2 | Probit σ-Sweep (σ = 0.3, 0.5, 1, 2, 5, 10) |
| R3 | Funktionalform-Vergleich (K=2, I₂=5 fest, I₁ variiert) |
| R4 | Effektiver Preis p_eff(I) fuer 5 Gueter |
| R5 | Konzentrations-Sweep: η → HHI + Gini |
| R6 | Heterogene Agenten (N=200, exponential-verteilte I) |
| R7 | Aufmerksamkeits-Dynamik VI.9 + Info-Schock |

## Validierungen (8/8 PASS)

| Val | Test | Ergebnis |
|---|---|---|
| V1 | Normierung Σω=1 | PASS — max|Σω-1| = 1.1e-16 |
| V2 | Monotonie dω/dI ≥ 0 | PASS — alle Formen, alle Gueter |
| V3 | Exklusion I=0 ⇒ ω=0 | PASS — ω_sm = ω_li = 0 |
| V4 | η→∞: Winner-Takes-All | PASS — ω₁(η=50) = 1.000000 |
| V5 | η→0: Gleichverteilung | PASS — max-min = 0.006 |
| V6 | p_eff ≥ p + dp/dI < 0 | PASS |
| V7 | I→∞: p_eff→p (Arrow-Debreu) | PASS — |p_eff-p|/p = 3e-6 |
| V8 | Dynamik: a(T) → ω* | PASS — max|a-ω*| = 0.004 |

## Sensitivitaetsanalysen

| SA | Analyse | Ergebnis |
|---|---|---|
| SA1 | Wohlfahrtsverlust ψ/(I+ε) | 4 Szenarien: ψ=1,3,5,10 → Aufschlag bis 200% |
| SA2 | Dominanzwechsel-Schwelle | Immer bei I₁=I₂ (Softmax-Symmetrie) |
| SA3 | Probit σ → HHI | σ=0.1: HHI≈0.2, σ=20: HHI→1/K |
| SA4 | Gini(p_eff) pro Gut | 0.44–0.64 (starke Preisungleichheit) |

## Inhomogenitaets-Analyse (R6)

- 200 Agenten mit exponentialverteilten I-Vektoren (scale=3, Gut 1 doppelt)
- Softmax η=2: Boxplot zeigt starke Streuung der ω-Gewichte
- p_eff-Verteilung: Informationsarme Agenten zahlen bis 5x den Marktpreis
- Gini(p_eff) = 0.44–0.64 → "Poverty Premium" quantifiziert

## Kausalketten

```
I_k  ──U.2──►  ω_k  ──U.1──►  Nutzen  ──►  Nachfrage
I_k  ──U.3──►  p_eff  ──►  effektive Kosten  ──►  Wohlfahrtsverlust

η hoch  ──►  Winner-Takes-All  ──►  Markenmacht, Lock-in
η niedrig  ──►  Diversifikation  ──►  Exploration
ψ hoch  ──►  p_eff >> p  ──►  Info-Arme zahlen mehr
I → ∞  ──►  p_eff → p  ──►  Arrow-Debreu-Limit (friktionslos)
```

## Dateien

- `Simulationen/Kap06_Entscheidungen/S15_U2_Aufmerksamkeitsgewichte.py`
- `Ergebnisse/Plots/S15_U2_Aufmerksamkeitsgewichte.png`
- `Ergebnisse/Daten/S15_U2_Aufmerksamkeitsgewichte.npz`
