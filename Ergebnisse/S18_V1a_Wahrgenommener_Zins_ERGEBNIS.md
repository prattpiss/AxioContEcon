# S18 — V.1a Wahrgenommener Zins — ERGEBNIS

## Gleichung
$$r_i^{\text{wahr}} = r + \eta_i \pi - \frac{\varphi_i}{\mathcal{I}_i + \varepsilon}$$

Drei Kanäle: Nominalzins r, Inflationserwartung η·π, Informationsfriction −φ/(I+ε)

## Validierungen: 8/8 PASS

| # | Test | Ergebnis |
|---|------|----------|
| V1 | Fisher: η=1 ⇒ r_real=const | max\|Δ\|=1.4e-17 |
| V2 | EMH: I→∞ ⇒ friction→0 | \|Δ\|=5.0e-9 |
| V3 | Monotonie: ∂r_wahr/∂I > 0 | alle steigend |
| V4 | Geldillusion: η=0 ⇒ r_wahr=r_nom | exakt |
| V5 | Transmission→100% bei I→∞ | α(1e8)=0.9999999950 |
| V6 | Bias≈0 für neutrale Population | mean=-0.004 |
| V7 | Gini(T) > Gini(0) | 0.160 → 0.793 |
| V8 | Illusion: gleiches r_real, versch. c(T) | Ratio=207× |

## 8 Regime — Kernergebnisse

### R1: Fisher-Effekt
- η=1.0: r_real_wahr unabhängig von π (Fisher-neutral, Spread=0.0000)
- η=0.5: Spread=0.06 (teilweise Geldillusion)
- η=0.0: Spread=0.12 (volle Geldillusion — Agent ignoriert Inflation komplett)

### R2: Informationsfriction-Sweep
- φ=0.5, I=0.1: Bias = −4.51 (katastrophale Fehleinschätzung)
- Kritisches I (|bias|>1%): φ=0.5 → I_crit=49.6, φ=2.0 → I_crit=198.5
- Friction dominiert für I < 10 bei moderatem φ

### R3: Heterogene Agenten (N=300)
- Heterogene (η, φ, I, β, γ)-Verteilungen
- Mean Bias = −0.309 (systematische Unterschätzung durch Friction)
- **Gini wächst endogen: 0.160 → 0.793** (massive Ungleichheit durch unterschiedliche Zinswahrnehmung)

### R4: Geldillusion
- η=0: Agent behandelt Nominalzins als Realzins → r_real_wahr=+0.02 statt +0.07
- Konsum: c(T, η=0)=37.9 vs c(T, η=1)=200.9 → **5.3× Wohlfahrtsverlust**
- Nichtlinearer Anstieg: meiste Gewinne zwischen η=0.6 und η=1.0

### R5: Geldpolitik-Transmission
- **Kernresultat: Transmission = α(I) = I/(I+φ)**
- Finanzsektor (I=50): 99% Transmission
- Mittelstand (I=5): 91%
- Haushalte (I=1): 67%
- Informeller Sektor (I=0.2): **nur 29%**
- → Geldpolitik erreicht informationsarme Akteure kaum

### R6: Informationskaskade
- Normales Wachstum: I steigt logistisch auf 12.3, r_wahr stabilisiert bei +0.025
- Info-Schock (t=25): I kollabiert auf 0.01 → r_wahr stürzt auf −24.9 → Konsum→0
- Zensur (ω=0.3): Information kann nie aufgebaut werden → permanente Fehleinschätzung

### R7: Systematischer Bias (N=5000)
- Optimisten (η=1.2): mean_bias=+0.000, 59% überschätzen → leicht optimistisch
- Neutrale (η=0.8): mean_bias=−0.004, sehr geringer Rest-Bias
- Pessimisten (η=0.3): mean_bias=−1.197 → **massive systematische Unterschätzung**

### R8: Realzins-Illusion
- Alle Kombinationen (r, π) mit identischem r_real=0.02
- Bei η=0.6: c(T) variiert von 1.0 (r=2%, π=0%) bis 201.7 (r=12%, π=10%)
- **Ratio 207×** — gleicher Realzins, aber 207× verschiedener Konsum durch Geldillusion+Friction

## 5 Sensitivitätsanalysen

1. **SA1: φ-Sweep** — r_wahr(φ=0)=+0.066, r_wahr(φ=3)=−1.43 → starke Nichtlinearität
2. **SA2: 50×50 Heatmap r_wahr(η, π)** — min=−0.040, max=+0.170; Isolinie r_wahr=0.05 trennt Regime
3. **SA3: 50×50 Friction-Landschaft (I, φ)** — Maximale Friction=27.3 bei (I_min, φ_max)
4. **SA4: Transmission(I, φ)** — I=0.1,φ=1: 9%, I=100,φ=1: 99% → S-förmiger Anstieg
5. **SA5: Wohlfahrtsverlust** — I=0.1: 100% Verlust, I=100: 15.4% Rest-Verlust

## Kernschlussfolgerungen

1. **Kein informationsunabhängiger Entscheidungskanal** — selbst Fisher-Effekt braucht η (Wissen über Inflation)
2. **Geldpolitik-Impotenz**: Bei I<1 kommt weniger als 67% der Zinsänderung an → Liquidity Trap durch Ignoranz
3. **Endogene Ungleichheit**: Heterogene Informationsausstattung → Gini 0.16→0.79 rein durch Wahrnehmungsdifferenzen
4. **Geldillusion × Friction = Multiplikator**: η<1 + φ/(I+ε) verstärken sich gegenseitig → 207× Konsumdivergenz
5. **Informationskaskade als Systemrisiko**: I-Schocks (Fake News, Zensur) propagieren über r_wahr in reale Ökonomie
