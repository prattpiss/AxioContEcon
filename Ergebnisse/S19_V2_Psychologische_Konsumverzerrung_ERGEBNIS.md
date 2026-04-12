# S19 — V.2 Psychologische Konsumverzerrung — ERGEBNIS

## Gleichung
$$\Psi_c(c_i, c_i^*, \dot{c}_i^{\text{hist}}, \text{Gini}, \mathcal{I}_i)$$

Prospect-Theory-Korrektur der rationalen Euler-Konsumregel (V.1). Zweite Ebene der Drei-Ebenen-Architektur:
$$\frac{dc_i}{dt} = \underbrace{R_i \cdot c_i}_{\text{V.1 Rational}} + \underbrace{\Psi_c(\ldots)}_{\text{V.2 Psychologie}} + \underbrace{\sum_j A_{ij}\Phi(\ldots)}_{\text{V.3 Sozial}}$$

## Validierungen: 8/8 PASS

| # | Test | Ergebnis |
|---|------|----------|
| V1 | Nullpunkt: Ψ(c*,c*,0,0,·)=0 | \|Ψ\|=0 (exakt) |
| V2 | Referenzpunktanziehung: Ψ>0 für c<c*, Ψ<0 für c>c* | bestätigt |
| V3 | Verlustaversion: \|Ψ(loss)\|>\|Ψ(gain)\| | Ratio=2.25 für alle Abstände |
| V4 | Beschränktheit: \|Ψ\|≤Ψ_max | max\|Ψ\|=2.0=Ψ_max |
| V5 | Ramsey-Limit: I→∞ ⇒ Ψ→0 | \|Ψ(I=10⁸)\|=3.6e-8 |
| V6 | Gini-Monotonie: \|Ψ\| steigt mit Gini | alle nicht-fallend |
| V7 | λ=2.25 exakt: Loss/Gain Ratio | 2.2500 |
| V8 | Schock-Erholung: gap<5% am Ende | \|c-c*\|/c*=3.3% |

## 8 Regime — Kernergebnisse

### R1: Referenzpunktanziehung
- Ψ>0 wenn c<c* (Konsum wird hochgezogen), Ψ<0 wenn c>c* (runtergedrückt)
- Symmetrischer Schnitt bei c=c* — Fixpunkt des psychologischen Terms
- Bei I→∞: Effekt verschwindend klein (info_mod≈0)

### R2: Verlustaversion (λ=2.25)
- **\|Ψ(Verlust)\| / \|Ψ(Gewinn)\| = 2.25 exakt** — Kahneman-Tversky bestätigt
- Ratio konstant über alle Abstände d∈[0.1, 8] — lineare Prospect-Theory-Wertfunktion
- Verlustbereich: stärkere Anziehung → schnellere Erholung nach Schocks

### R3: Referenzpunkt-Adaptation (Hedonisches Laufband)
- Startpunkt: c=14, c*=10 (Agent über Referenz)
- λ_adapt=0.05: Gap nach T=50 noch 0.98 (langsame Anpassung)
- λ_adapt=0.50: Gap nur noch 0.22 → **hedonisches Laufband**: c* nähert sich c
- Höhere Adaptation → höherer Endkonsum (c*-Drift erlaubt weiteres Wachstum)

### R4: Relative Deprivation (Gini-Effekt)
- **dΨ/dGini > 0 für c<c***: Höhere Ungleichheit verstärkt Referenzpunktanziehung
- Armer Agent (c=6): Ψ(G=0)=0.45, Ψ(G=0.5)=0.50, Ψ(G=0.7)=0.51
- Reicher Agent (c=14): Negativer Ψ wird ebenfalls durch Gini verstärkt (symmetrisch)
- → Ungleichheit treibt Arme zum „Über-Verhältnisse-Konsumieren"

### R5: Informations-Modulation
- Ψ(I=0.01)=2.00 (Maximum, Beschränktheit greift)
- Ψ(I=10)=0.51, Ψ(I=1000)=0.002
- **Ramsey-Limit**: Ψ(I=10⁶)≈2×10⁻⁶ → perfekt informierte Agenten sind rational

### R6: Heterogene Agenten (N=300)
- Diverse (c₀, c*, I, β, γ)-Verteilungen
- **Gini sinkt leicht**: 0.272→0.250 — Ψ-Anziehung hat equalisierende Wirkung
- c_mean wächst 11.25→15.01 (Euler+Ψ gemeinsam)
- Prospect Theory stabilisiert Heterogenität (anders als V.1 allein)

### R7: Negativer Konsumschock + Erholung
- Schock c: 10→5 bei t=10, Referenzpunkt c*≈10 bleibt
- **λ=2.25 (Standard)**: Erholung in 8.0 Zeiteinheiten (95%-Schwelle)
- **λ=1.00 (neutral)**: Erholung in 10.5 (33% langsamer)
- **λ=4.00 (extrem avers)**: Erholung in 6.0 (25% schneller)
- → Stärkere Verlustaversion beschleunigt Erholung

### R8: Drei-Ebenen-Vergleich
- V.1 Rational: c(T)=11.16
- V.1+V.2 (Ψ, G=0): c(T)=11.35 → Ψ-Korrektur +1.7%
- V.1+V.2 (Ψ, G=0.3-0.5): c(T)=11.35 (Gini-Effekt marginal bei c₀≈c*)
- V.1+V.2 (Ψ, I=0.5): c(T)=11.00 → **starke Info-Friction drückt unter Rational**

## 5 Sensitivitätsanalysen

1. **SA1: λ-Sweep** — Verlustaversion von 1.0 bis 5.0; Verlust-Ψ steigt linear mit λ
2. **SA2: κ_ref-Sweep** — Referenzpunkt-Stärke: Ψ(κ=0.05)=0.06 bis Ψ(κ=1.0)=1.19 (20× Spread)
3. **SA3: 50×50 Heatmap Ψ(c, I)** — Ψ∈[−2.0, +2.0]; Nulllinie bei c=c*=10
4. **SA4: 50×50 Heatmap Ψ(Gini, I)** — Doppelte Modulation: Gini verstärkt, I dämpft
5. **SA5: Erholungszeit vs λ_adapt** — λ=0.01: 14.1t, λ=1.0: 2.5t → **6× schnellere Erholung bei starker Adaptation**

## Kernschlussfolgerungen

1. **Prospect Theory als axiomatisch konsistente Erweiterung**: Alle 5 axiomatischen Eigenschaften (Nullpunkt, Anziehung, Asymmetrie, Deprivation, Beschränktheit) numerisch verifiziert
2. **Verlustaversion λ=2.25 beschleunigt Erholung**: Stärkere Reaktion auf Verluste → schnellere Rückkehr zum Referenzpunkt (6.0 vs 10.5 Zeiteinheiten)
3. **Information dämpft Psychologie**: I→∞ eliminiert Prospect-Theory-Effekte vollständig → neoklassisches Ramsey-Ergebnis als Grenzfall
4. **Gini-Verstärkung erzwingt Über-Konsum**: Arme Agenten in ungleichen Gesellschaften konsumieren über ihre Verhältnisse (Ψ>0 verstärkt)
5. **Hedonisches Laufband bestätigt**: Schnelle Adaptation (λ_adapt=0.5) → Referenzpunkt folgt Konsum → Surplus→0.22 → Zufriedenheitsgewinn ist vergänglich
6. **Ψ stabilisiert statt destabilisiert**: Gini sinkt leicht (0.272→0.250) — Prospect Theory ist inherent equalisierend
