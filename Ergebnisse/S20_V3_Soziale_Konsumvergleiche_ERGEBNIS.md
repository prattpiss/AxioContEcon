# S20 — V.3 Soziale Konsumvergleiche (§6.3)

## Gleichung

$$S_i = \sum_{j=1}^{N} A_{ij}^{\text{eff}} \, \Phi_c\!\left(c_j - c_i,\; \mathcal{I}_j,\; \mathcal{I}_i\right)$$

Drei-Ebenen-Architektur (komplett):
$$\frac{dc_i}{dt} = \underbrace{R_i \cdot c_i}_{\text{V.1 Rational}} + \underbrace{\Psi_c(\ldots)}_{\text{V.2 Psychologie}} + \underbrace{S_i}_{\text{V.3 Sozial}}$$

Multiplex-Aggregation:
$$A_{ij}^{\text{eff}} = \sum_{\ell=1}^{5} \omega_\ell \, A_{ij}^{(\ell)} \quad \text{(Trade, Info, Sozial, Finanz, Institut)}$$

## Axiome (alle verifiziert)

| Axiom | Eigenschaft | Validierung |
|-------|-------------|-------------|
| A1 | Nullpunkt: Φ(0,·,·) = 0 | \|Φ\| = 0.00 |
| A2 | Monotonie: ∂Φ/∂(Δc) > 0 | strikt steigend |
| A3 | Asymmetrie: \|Φ(+)\| > \|Φ(−)\| | Ratio = 2.50 (exakt α_up/α_down) |
| A4 | Beschränktheit: \|Φ\| ≤ Φ_max | max\|Φ\| = 3.00 |
| A5 | Info-Modulation: ∂\|Φ\|/∂I_j > 0 | strikt steigend |
| A6 | Ramsey-Limit: I_i→∞ ⇒ Φ→0 | \|Φ(I_i=10⁸)\| = 2.37×10⁻⁴ |

## Kernergebnisse

### R1: Φ-Funktion
- Φ(+5) = +0.374, Φ(−5) = −0.150
- **Asymmetrie-Ratio 2.50**: Aufwärtsherding 2.5× stärker als Abwärts
- Ökonomisch: Bubble-Aufbau dominant, Crash-Übertragung gedämpft

### R2: Multiplex-Netzwerk (N=100, Scale-Free)
- 5 Layer mit ω = (0.15, 0.30, 0.20, 0.25, 0.10)
- Density 29.9%, Mean degree 4.2, Max degree 10.4
- **Fiedler-Wert (algebraische Konnektivität): 1.977**
- Spektral-Ratio λ₂/λ_N = 0.181

### R3: Herding-Kaskade (Bubble)
- Ein Hub (c₀=20, Rest c₀=10) → komplette Konvergenz auf c(T)=11.45
- Spread: 10.0 → 0.03 (99.7% Reduktion)
- Hub-Konsum sinkt, Peripherie steigt → **emergenter Konsens**

### R4: Info-Asymmetrie
- I_i=0.1 → Φ(I_j=100) = 0.726 (maximal beeinflussbar)
- I_i=100 → Φ(I_j=100) = 0.375 (50% reduziert)
- **Influencer-Effekt**: Informierter Nachbar + uninformierter Agent = maximaler Einfluss
- **Emanzipation**: Eigene Information reduziert Fremd-Einfluss monoton

### R5: Drei-Ebenen-System (V.1+V.2+V.3)
| Konfiguration | c_mean(T) | Gini(T) |
|--------------|-----------|---------|
| V.1 nur | 14.04 | 0.179 |
| V.1+V.2 | 13.25 | 0.123 |
| V.1+V.3 | 17.11 | **0.009** |
| V.1+V.2+V.3 | 15.25 | **0.010** |

**Zentrales Ergebnis**: V.3 ist der stärkste Gleichheitstreiber:
- Gini-Reduktion V.1→V.1+V.3: **95%** (0.179→0.009)
- V.2 (Psychologie) senkt Gini um 31%, V.3 (Sozial) um 95%
- V.3 dominiert V.2 im Ungleichheitseffekt um Faktor 6

### R6: Topologie-Vergleich
| Topologie | Konvergenzzeit | Gini(T) |
|-----------|---------------|---------|
| Scale-Free | 19.2 | 0.000 |
| Small-World | 26.0 | 0.004 |
| Random | 43.4 | 0.004 |

- **Scale-Free 2.3× schneller als Random** (Hubs als Superspreader)
- Small-World Zwischenposition (Clustering + Shortcuts)

### R7: Crash-Kaskade
- 10 Crash-Agenten (c=5, Rest c=20)
- **0% Contagion** (kein Agent unter c=10 am Ende)
- c_mean: 18.5 → 19.6 (Crash-Agenten werden rehabilitiert)
- **Asymmetrie bestätigt**: Abwärtsherding zu schwach für Kaskade

### R8: Neoklassischer Grenzfall (Prop 6.1)
| Netzwerk | Gini(T) | c_std |
|----------|---------|-------|
| A=0 | 0.198 | 5.93 |
| A=normal | 0.001 | 0.02 |
| A=2× | 0.000 | 0.00 |

- **A=0 reproduziert reinen Euler-Pfad** (Prop 6.1 bestätigt)
- Netzwerk-Stärke monoton anti-korreliert mit Ungleichheit

## Sensitivitätsanalysen

### SA1: Asymmetrie-Sweep (α_up/α_down = 1…5)
- Bei Ratio=1 (symmetrisch): Bubble = Crash → kein Anreicherungseffekt
- Bei Ratio=5: |Φ(+5)| = 0.748, |Φ(−5)| weiter 0.150
- → Starke Asymmetrie verstärkt Bubble-Tendenz bei konstantem Crash-Schutz

### SA2: Heatmap Φ(Δc, I_j) — 50×50
- Φ ∈ [−0.49, +1.22]
- Klare Separation bei Δc=0 (Nullpunkt-Axiom)
- I_j verstärkt Φ monoton (bei Δc>0)

### SA3: Heatmap Φ(I_j, I_i) — 50×50
- Maximum bei (I_j hoch, I_i niedrig): 0.726
- Minimum bei (I_j niedrig, I_i hoch): 0.023
- **31× Einflussunterschied** zwischen Best/Worst Info-Kombination

### SA4: Konvergenzzeit vs Netzwerk-Dichte
- d=0.02 → keine Konvergenz (t>50)
- d=0.30 → t_conv=13.5
- **Kritische Dichte ~0.05**: Unterhalb kein Herding-Konsens

### SA5: Herding-Stärke vs Gini
- α_up=0.01 → Gini=0.123 (kaum Herding, Euler dominiert)
- α_up=0.50 → Gini=0.000 (perfekte Gleichverteilung)
- **Monotone Anti-Korrelation**: Mehr Herding = weniger Ungleichheit

## Erweiterte Analyse

### EA1: Mean-Field Bifurkation
- Bifurkationspunkt: R_crit = −α_eff · info_mod
- α_eff=0.01: R_crit = −0.003 (instabil bei schwacher Rezession)
- α_eff=0.20: R_crit = −0.060 (stabil bis tiefe Rezession)
- **Herding stabilisiert**: Stärkeres Herding verschiebt Instabilitätsgrenze

### EA2: Netzwerk-Spektralanalyse
- Fiedler-Wert λ₂ = 1.977 → hohe algebraische Konnektivität
- Ratio λ₂/λ_N = 0.181 → moderate Heterogenität
- **Fiedler-Vektor** trennt Netzwerk in zwei Communities (Vorzeichen-Partition)

### EA3: Phasendiagramm (α_up, α_down)
- Phasengrenze: α_eff · ⟨k⟩ · info = |R_Euler| = 0.0067
- **Gesamte (α_up, α_down)-Ebene** im konvergenten Regime
- Divergenz nur bei extrem negativem R (Kontraktion > Herding)

### EA4: Shannon-Entropie
- S(0) = 4.601, S(T) = 4.605, S_max = 4.605
- **S(T)/S_max = 1.000** → perfekte Gleichverteilung im Gleichgewicht
- Herding maximiert die Informationsentropie der Konsumverteilung

## Mathematische Strukturen

### Struktur 1: Graph-Diffusionsoperator
V.3 hat die Form $\frac{dc_i}{dt} = \sum_j L_{ij} f(c_j)$ — ein **verallgemeinerter Laplace-Operator** auf gewichtetem Graphen. Bei linearem Φ reduziert sich dies exakt auf die Wärmeleitungsgleichung $\frac{dc}{dt} = -Lc$ auf dem Netzwerk. Die Spektrallücke λ₂ = 1.977 bestimmt die Mischzeit (~0.5 ZE).

### Struktur 2: Gebrochene Onsager-Symmetrie
Klassische Transporttheorie erfordert $L_{ij} = L_{ji}$ (Onsager-Reziprozität). Die Asymmetrie α_up ≠ α_down **bricht** dieses Prinzip:
- Ratio = 2.50 → **Nicht-Gleichgewichts-Thermodynamik**
- Broken detailed balance → Netto-Entropieproduktion > 0
- Ökonomisch: Bubble-Aufbau dominiert, Crash-Schutz emergent

### Struktur 3: Kuramoto-Synchronisation
V.3 ist formal analog zum **Kuramoto-Modell** der Synchronisation:
$$\frac{d\theta_i}{dt} = \omega_i + \frac{K}{N} \sum_j \sin(\theta_j - \theta_i)$$
mit $\theta_i \leftrightarrow c_i$, $\omega_i \leftrightarrow R_i c_i$ und $\sin(\cdot) \leftrightarrow \Phi(\cdot)$.
- Phasensynchronisation ↔ Konsumkonvergenz
- Kritische Kopplung K_c: unter K_c keine vollständige Synchronisation
- Fiedler-Wert als Synchronisierbarkeitsmaß

### Struktur 4: Lyapunov-Funktion
Für symmetrisches Φ ist $V = \frac{1}{2}\sum_{ij} A_{ij}(c_i - c_j)^2$ eine Lyapunov-Funktion (dV/dt ≤ 0).
Die Asymmetrie **bricht** dies → keine garantierte Konvergenz. Aber: Entropie S(0)→S(T) steigend zeigt faktische Konvergenz trotz fehlender Lyapunov-Garantie.

### Struktur 5: Verbindung zu S13 (Info-Fluss)
Fisher-KPP-Welle (S13) + V.3 Herding = **gekoppeltes Reaktions-Diffusionssystem auf Netzwerk**. Information propagiert via Welle (S13), Konsum folgt via Herding (S20) — zwei verschränkte Diffusionsprozesse auf demselben Graphen.

## Validierung: 8/8 PASS

| # | Test | Ergebnis |
|---|------|----------|
| V1 | Nullpunkt Φ(0)=0 | \|Φ\|=0.00 |
| V2 | Monotonie ∂Φ/∂Δc>0 | strikt steigend |
| V3 | Asymmetrie \|Φ(+)\|>\|Φ(−)\| | Ratio=2.50 |
| V4 | Beschränktheit \|Φ\|≤Φ_max | max=3.00 |
| V5 | Info-Modulation ∂\|Φ\|/∂I_j>0 | strikt steigend |
| V6 | Ramsey-Limit I_i→∞⇒Φ→0 | 2.37×10⁻⁴ |
| V7 | Herding-Konvergenz | Spread 10.0→0.03 |
| V8 | Netzwerk equalisiert | Gini 0.198→0.001 |

**Kumulativ: 115/115 Validierungen bestanden (S01–S20)**

## Kausalstruktur

```
c_j steigt
  → Δc = c_j-c_i > 0
    → Φ > 0 (V.3 Axiom A2: Monotonie)
      → dc_i/dt > 0 (Agent i folgt)
        → Nachbar k von i: Δc_k > 0
          → Kaskade über Netzwerk
            → Bubble-Formation
              → ABER: Asymmetrie (α_up >> α_down)
                → Crash-Kaskade 2.5× schwächer
                  → Markt-asymmetrie: schneller Aufstieg, langsamer Fall
```

Reverse (Crash initiiert):
```
c_j sinkt → Φ < 0, aber |Φ| nur 40% des Aufwärts
  → Crash-Contagion gedämpft (R7: 0% angesteckt)
    → "Sticky consumption" emergent durch Netzwerk-Asymmetrie
```
