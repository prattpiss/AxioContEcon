# S24 — L.2 Psychologische Arbeitsverzerrung (§6.4)

## Master-Gleichung

$$\Psi_L\bigl(L_i, L_i^*, \bar{L}, \mathcal{I}_i^{\text{job}}, H_i\bigr)$$

Zwei Mechanismen:

$$\Psi_L = \underbrace{\kappa_{\text{ref}} \cdot v(L_i^* - L_i) \cdot \frac{1}{1 + \kappa_{\text{info}} \mathcal{I}_i^{\text{job}}}}_{\text{Burnout/Referenz (gedämpft durch I)}} + \underbrace{\kappa_I \cdot \frac{\mathcal{I}_i^{\text{job}}}{\mathcal{I}_i^{\text{job}} + \psi_I} \cdot \frac{H_i}{H_{\text{norm}}}}_{\text{Intrinsische Motivation (verstärkt durch I)}}$$

mit Burnout-Asymmetrie (Prospect-Theory-analog):

$$v(x) = \begin{cases} x & \text{falls } x \geq 0 \quad (L < L^*: \text{Unterarbeit, schwach}) \\ \lambda_B \cdot x & \text{falls } x < 0 \quad (L > L^*: \text{Überarbeit, Burnout, stark}) \end{cases}$$

Referenzpunkt-Adaptation: $\dot{L}_i^* = \lambda_{L^*}(L_i - L_i^*)$ — langsamer als Konsum ($\lambda_{L^*}=0.1$ vs. $\lambda_{c^*}=0.2$)

## Strukturelle Symmetrie V.2 ↔ L.2 (Prop 6.2)

| Dimension | Konsum V.2 (S19) | Arbeit L.2 (S24) |
|-----------|------------------|-------------------|
| Referenzpunkt | $c_i^*$ (Konsumgewohnheit) | $L_i^*$ (Arbeitsgewohnheit) |
| Asymmetrie | Verlustaversion $\lambda=2.25$ | Burnout-Asymmetrie $\lambda_B=2.25$ |
| Verstärkung | Relative Deprivation (Gini) | Intrinsische Motivation ($\mathcal{I}^{\text{job}} \cdot H$) |
| Info-Rolle | **Dämpft** ($1/(1+\kappa I)$) | **Dual**: Dämpft Burnout, **verstärkt** Motivation |
| Nullpunkt | $\Psi_c(c^*,c^*,0,0,\cdot)=0$ | $\Psi_L(L^*,L^*,\bar{L},0,H_{\text{norm}})=0$ |

**Zentraler Unterschied**: In V.2 verschwindet Psychologie mit Information. In L.2 hat Information eine **duale Rolle** — sie dämpft Burnout (rational agents avoid overwork) aber **verstärkt** intrinsische Motivation (Jobidentifikation). Crossover bei $\mathcal{I}^{\text{job}} \approx 0.62$.

## Propositions (alle verifiziert)

| Proposition | Aussage | Validierung |
|-------------|---------|-------------|
| **Prop 3.1** | Forminvarianz | Burnout-Ratio exakt $\lambda_B=2.25$ über alle Distanzen |
| **Prop 6.2** | Symmetrie V.2 ↔ L.2 | max\|Ψ\_L2 − Ψ\_V2\| = 8.3×10⁻¹⁷ bei I\_job=0 |
| **Prop 6.4** | L=L\*, I\_job=0 → Ψ\_L=0 | V1: exakt \|Ψ\|=0 |

## Kernergebnisse

### R1: Referenzpunktanziehung
- Ψ\_L > 0 für L < L\*: Agent wird zur Referenz hochgezogen
- Ψ\_L < 0 für L > L\*: Burnout zieht Agent zurück
- Ψ(L=0.2, L\*=0.5) = +0.090, Ψ(L=0.8, L\*=0.5) = −0.203
- **Asymmetrie sichtbar**: Burnout (−0.203) > Unterarbeit (+0.090) bei gleichem Abstand

### R2: Burnout-Asymmetrie (λ\_B=2.25)
- Unterarbeit (d=0.15): Ψ = +0.045 (schwache Anziehung)
- Überarbeit (d=0.15): Ψ = −0.101 (starker Burnout-Rückzug)
- **|Burnout/Unterarbeit| = 2.25 exakt** — identisch zu Verlustaversion in V.2
- Ratio konstant über alle Distanzen (Prospect-Theory-Eigenschaft)

### R3: Dynamische Referenzpunkt-Adaptation
- λ\_adapt=0.02: Gap(T)=−0.001 — sehr langsame Adaptation, fast kein Tracking
- λ\_adapt=0.10: Gap(T)=−0.001 — Arbeitsnorm folgt tatsächlicher Arbeit
- λ\_adapt=0.20: Gap(T)=−0.000 — schnelle Adaptation, Gleichgewicht erreicht
- **Langsamer als Konsum**: Arbeitsnormen (L\*) ändern sich träger als Konsumgewohnheiten (c\*)
- "Workaholic Treadmill": Chronische Überarbeit normalisiert sich — L\* steigt zum Überlast-Niveau

### R4: Intrinsische Motivation (I\_job Sweep)
- H=0.5: Ψ(I=10)=0.215, Ψ(I=100)=0.553 — moderater Motivationsschub
- H=1.0: Ψ(I=10)=0.430, Ψ(I=100)=1.106 — Standard
- H=2.0: Ψ(I=10)=0.859, Ψ(I=100)=2.000 — an Ψ\_max gesättigt
- H=3.0: Ψ(I=10)=1.289, Ψ(I=100)=2.000 — Sättigung bereits bei niedrigerem I
- **Michaelis-Menten-Sättigung**: I/(I+ψ\_I) mit ψ\_I=8.5
- **H-Multiplikator**: Hochqualifizierte (H=3) erreichen Ψ\_max bei I≈30, Unqualifizierte (H=0.5) nie

### R5: Informations-Dualität
- **Vorzeichenwechsel bei I\_job=0.62** (bei L=0.7, L\*=0.5)
- I < 0.62: Burnout dominiert → Ψ\_total < 0 (Agent reduziert Arbeit)
- I > 0.62: Motivation dominiert → Ψ\_total > 0 (Agent erhöht Arbeit über rational)
- Ψ\_burn(I=0.01) = −0.134, Ψ\_burn(I=100) = −0.0001 (verschwindet)
- Ψ\_intr(I=0.01) = +0.001, Ψ\_intr(I=100) = +1.190 (dominiert)
- **Einzigartig im Framework**: Kein anderer Psi-Operator hat diese duale I-Abhängigkeit

### R6: Heterogene Agenten (N=300)
- Gini(0)=0.205 → Gini(T)=0.039 — massive Kompression (−81%)
- L\_mean(0)=0.497 → L\_mean(T)=0.946 — Motivation treibt alle nach oben
- Corr(I\_job, L\_final)=+0.267 — hohe Jobinfo → mehr Arbeit
- Corr(H, L\_final)=+0.247 — hoher Humankapital → mehr Arbeit
- **Motivation-Effekt dominiert**: Intrinsische Motivation drückt alle Agenten zum Ceiling

### R7: Negativer Arbeitsschock + Erholung
- λ\_B=2.25: L\_min=0.100, L(T)=0.494, t\_recov(90%)=4.4
- λ\_B=1.00: L(T)=0.498, t\_recov=4.4 — gleiche Erholungszeit
- λ\_B=4.00: L(T)=0.487, t\_recov=4.4 — stärkerer Burnout verlangsamt leicht
- **Erholung robust**: Alle λ\_B-Werte konvergieren innerhalb 5 Perioden
- **Burnout-Asymmetrie verzögert**: Höheres λ\_B → L(T) etwas unter Ziel (0.487 vs 0.498)

### R8: Drei-Ebenen-Vergleich
- L.1 Rational (kein Ψ): L(T)=0.500 — reiner FOC
- L.1+L.2 (I\_job=0): L(T)=0.495 — Burnout-Referenz senkt leicht
- L.1+L.2 (I\_job=5): L(T)=0.990 — **Motivation verdoppelt Arbeit**
- L.1+L.2 (I\_job=20): L(T)=0.990 — gesättigt
- L.1+L.2 (I\_job=5, H=3): L(T)=0.990 — Humankapital-Multiplikator an Ceiling
- **Motivation ist der dominante Kanal**: Bereits I\_job=5 reicht für Ceiling-Effekt

## Sensitivitätsanalysen

### SA1: λ\_B Sweep (Burnout-Sensitivität)
- |Ψ\_over|(λ=1)=0.060, |Ψ\_over|(λ=5)=0.300
- Burnout-Term skaliert linear mit λ\_B
- Unterarbeit-Term **unabhängig** von λ\_B (nur Überarbeit wird verstärkt)

### SA2: κ\_I Sweep (Motivation-Stärke)
- Ψ(κ=0.1, H=1)=0.054, Ψ(κ=3.0, H=1)=1.622
- H=3 verstärkt um Faktor 3: Ψ(κ=3.0, H=3)→Ψ\_max=2.0
- **Keine Sättigung in κ\_I**: Linear skalierend (im Gegensatz zu I\_job)

### SA3: 50×50 Heatmap Ψ\_L(L, I\_job)
- min=−0.232, max=+1.107
- Nulllinie verschiebt sich: Bei I\_job=0 liegt sie bei L=L\*; bei hohem I nach links
- **Motivation verschiebt Gleichgewicht**: L\*\_eff > L\*\_rational bei hohem I\_job

### SA4: 50×50 Heatmap Ψ\_L(H, I\_job) bei L=L\*
- min=0.004, max=2.000 — immer positiv (nur Motivation am Referenzpunkt)
- **Sättigungs-Band**: H>3 ∧ I\_job>30 → Ψ=Ψ\_max=2.0
- Iso-Motivation-Linien: H·I/(I+ψ\_I) = const → hyperbolisch

### SA5: Erholungszeit vs λ\_adapt
- λ\_adapt=0.01: t\_recov=3.5 — schnelle Erholung (Referenz bleibt hoch → starke Nachholung)
- λ\_adapt=0.50: t\_recov=10.7 — langsamere Erholung (Referenz fällt mit → weniger Antrieb)
- **Gegenintuitiv**: Schnellere L\*-Adaptation → LANGSAMERE Erholung
- Mechanismus: Wenn L\* dem fallenden L folgt, schrumpft der Gap → weniger Referenzpunktanziehung

## Erweiterte Analyse

### EA1: Burnout-Motivation Gleichgewicht
- Bei L=0.55 (leichte Überarbeit): I\_eq=0.20 (wenig Info nötig)
- Bei L=0.65: I\_eq=0.50
- Bei L=0.70: I\_eq=0.63
- Bei L=0.80 (starke Überarbeit): I\_eq=0.85 (mehr Info nötig)
- **Monotone Beziehung**: Je stärker die Überarbeit, desto mehr Jobinfo nötig für Kompensation
- **"Flow-State-Bedingung"**: I\_job > I\_eq → Motivation > Burnout → Agent arbeitet freiwillig über

### EA2: Prop 6.2 Strukturelle Symmetrie V.2 ↔ L.2
- max|Ψ\_L2 − Ψ\_V2\_analog| = 8.3×10⁻¹⁷ (bei I\_job=0, H=1) → **exakte Identität**
- Burnout-Dämpfung 1/(1+I) identisch zu V.2 Info-Dämpfung: max|Δ|=0
- Motivation I/(I+ψ\_I) ist das **duale Michaelis-Menten** zu V.2-Dämpfung
- **Strukturelle Symmetrie perfekt bestätigt**: V.2 und L.2 sind dasselbe Objekt mit verschiedenen Eingängen

### EA3: Komparative Statik (5 Parameter)
- dΨ/dL = −0.113 (negativ: mehr Arbeit → mehr Burnout-Druck)
- dΨ/dL\* = +0.113 (positiv: höhere Referenz → stärkere Anziehung)
- dΨ/dI\_job = +0.058 (positiv netto: Motivation > Burnout-Dämpfung bei L=0.6)
- dΨ/dH = +0.444 (stark positiv: Humankapital-Multiplikator)
- dΨ/dλ\_B = −0.005 (negativ: stärkerer Burnout bei Überarbeit)
- **H ist dominanter Gradient**: dΨ/dH = 0.444 >> alle anderen

## Mathematische Strukturen

### Struktur 1: Duale Informationsrolle
$$\frac{\partial \Psi_L}{\partial \mathcal{I}} = \underbrace{-\kappa_{\text{ref}} \cdot v \cdot \frac{\kappa_{\text{info}}}{(1+\kappa_{\text{info}}\mathcal{I})^2}}_{\text{Burnout-Dämpfung } < 0} + \underbrace{\kappa_I \cdot \frac{\psi_I}{(\mathcal{I}+\psi_I)^2} \cdot H}_{\text{Motivation-Verstärkung } > 0}$$
- **Vorzeichen ambig**: Bei niedrigem I dominiert Burnout-Dämpfung, bei hohem I dominiert Motivation
- Crossover bei I\_cross ≈ 0.62 (für L=0.7) — **topologischer Fixpunkt** im (L, I)-Raum

### Struktur 2: Prospect-Theory-Isomorphismus
- V.2 Verlustaversion: $v(c^*-c)$ mit $\lambda=2.25$ — Verlust "wiegt schwerer" im Konsum
- L.2 Burnout-Asymmetrie: $v(L^*-L)$ mit $\lambda_B=2.25$ — Überarbeit "wiegt schwerer" als Unterarbeit
- **Exakt identische funktionale Form** → gleiche mathematische Klasse (Kahneman-Tversky)
- Unterschied: Im Konsum ist "unter Referenz" schlecht; in Arbeit ist "über Referenz" (Burnout) schlecht

### Struktur 3: Michaelis-Menten Dualität
- V.2 Dämpfung: $1/(1+\kappa I)$ — strikt fallend, $[1, 0]$
- L.2 Motivation: $I/(I+\psi_I)$ — strikt steigend, $[0, 1]$
- **Summe**: $1/(1+I) + I/(I+\psi)$ → bei $\psi=1$: exakt $= 1$ (perfekte Komplementarität)
- Identisch zu S03 (Michaelis-Menten Kinetik) → **universelle Informationsarchitektur**

### Struktur 4: Workaholic Treadmill
- $\dot{L}^* = \lambda_{L^*}(L - L^*)$: Chronische Überarbeit hebt Referenz
- Kombination mit Motivation: $L > L^* \to L^*\uparrow \to$ Burnout verschwindet → L steigt weiter
- **Positive Rückkopplung**: Motivation + Adaptation = Workaholic-Spirale
- Nur Ψ\_max=2.0 als Bound verhindert Explosion

### Struktur 5: Flow-State als ökonomisches Gleichgewicht
- Gleichgewicht Burnout = Motivation definiert I\_eq(L): **Flow-State-Mannigfaltigkeit**
- Auf dieser Mannigfaltigkeit: Ψ\_L = 0 trotz L ≠ L\* → Agent arbeitet freiwillig über
- I\_eq steigt monoton mit |L − L\*|: Mehr Überarbeit erfordert mehr Jobidentifikation
- **Ökonomische Interpretation**: Ärzte, Forscher, Künstler — hohe I\_job erlaubt L >> L\*\_rational

## Validierung: 8/8 PASS

| # | Test | Ergebnis |
|---|------|----------|
| V1 | Nullpunkt: Ψ(L\*,L\*,L̄,0,H\_norm)=0 | \|Ψ\|=0 |
| V2 | Referenzpunkt: Ψ>0(L<L\*), Ψ<0(L>L\*) | below\_pos=True, above\_neg=True |
| V3 | Burnout-Asymmetrie: \|Ψ(L>L\*)\|>\|Ψ(L<L\*)\| | Ratios=[2.25, 2.25, 2.25, 2.25, 2.25] |
| V4 | Beschränktheit: \|Ψ\|≤Ψ\_max | max\|Ψ\|=2.0 |
| V5 | Info-Dualität: Burnout↓, Motivation↑ | burn: 0.134→0, intr: 0.001→1.200 |
| V6 | Gesundheitskopplung: dΨ/dH>0 | monoton, Ψ(H=0.3)=0.19→Ψ(H=5)=2.0 |
| V7 | Prop 6.2: Burnout-Ratio=λ\_B exakt | ratio=2.2500 |
| V8 | Schock-Erholung: L konvergiert | \|L(T)−L\_target\|/L=1.3% |

**Kumulativ: 147/147 Validierungen bestanden (S01–S24)**

## Emergente Phänomene

1. **Info-Dualität** (I\_cross=0.62): Information hat gegensätzliche Effekte auf Burnout vs. Motivation — einzigartig im gesamten Framework
2. **Flow-State-Mannigfaltigkeit**: Bei I\_job > I\_eq arbeiten Agenten freiwillig über dem rationalen Niveau — Burnout wird durch Jobfreude kompensiert
3. **Workaholic Treadmill**: Motivation + Referenzpunkt-Adaptation → positive Rückkopplung, nur durch Ψ\_max begrenzt
4. **Gegenintuitive Erholung**: Schnellere L\*-Adaptation → langsamere Schock-Erholung (Referenz fällt mit → weniger Antrieb)
5. **Humankapital-Verstärkung**: H ist der dominante Gradient (dΨ/dH=0.444) — Bildung verstärkt Motivation überproportional

## Kausalstruktur

```
INFORMATION NIEDRIG (I_job ~ 0):
  Motivation ≈ 0 (kein Motivationsschub)
  Burnout-Dämpfung = 1 (volle Stärke)
    → Nur Burnout/Referenz aktiv
      → L > L*: starker Rückzug (Burnout dominiert)
      → L < L*: schwache Anziehung
      → DOPPELTE BENACHTEILIGUNG: kein Motivationsbonus + volles Burnout-Risiko

INFORMATION HOCH (I_job >> 1):
  Motivation → κ_I · H (gesättigt, stark)
  Burnout-Dämpfung → 0 (verschwindet)
    → Nur Motivation aktiv
      → Agent arbeitet ÜBER rationalem Niveau
      → Flow-State wenn I > I_eq
      → WORKAHOLIC-RISIKO: L* steigt → Burnout-Schwelle steigt → Spirale

CROSSOVER (I_job ≈ 0.62 bei L=0.7):
  Burnout = Motivation (exaktes Gleichgewicht)
    → Psi_L = 0 trotz L ≠ L*
    → Agent in stabilem Überarbeitungszustand
    → FLOW-STATE-MANNIGFALTIGKEIT

PROP 6.2 SYMMETRIE:
  V.2 (Konsum): Info → weniger Psychologie (rational)
  L.2 (Arbeit): Info → DUAL (weniger Burnout, mehr Motivation)
    → Konsum wird "rationaler" mit Info
    → Arbeit wird "motivierter" mit Info
    → FUNDAMENTALE ASYMMETRIE Konsum ↔ Arbeit
```

## Verbindungen

- **S19** (V.2 Psychologische Konsumverzerrung): Exaktes strukturelles Analogon — identische Prospect-Theory-Form, duale Info-Rolle
- **S22** (L.1 Rationales Arbeitsangebot): Basis-FOC — S24 addiert psychologische Verzerrung
- **S23** (L.1a Wahrgenommener Alternativlohn): Informationsfilter — S24 addiert Motivation
- **S03** (Michaelis-Menten): I/(I+ψ) identisch in Motivationsterm
- **Prop 6.2**: Symmetrie V.2 ↔ L.2 perfekt bestätigt (max|Δ|=8.3×10⁻¹⁷)
- **Prop 6.4**: I\_job=0, H=H\_norm → S24 zeigt nur Referenzpunkt → bei L=L\*: Ψ\_L=0
