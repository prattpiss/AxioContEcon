# S21 — Drei-Ebenen-Konsumsystem komplett (§6.3)

## Master-Gleichung

$$\frac{dc_i}{dt} = \underbrace{\frac{r_i^{\text{wahr}} - \beta_i}{\gamma_i}\,c_i}_{\text{V.1 Rational}} + \underbrace{\Psi_c(c_i, c_i^*, G, \mathcal{I}_i)}_{\text{V.2 Psychologie}} + \underbrace{\sum_j A_{ij}^{\text{eff}}\,\Phi_c(c_j - c_i, \mathcal{I}_j, \mathcal{I}_i)}_{\text{V.3 Sozial}}$$

$$\frac{dc_i^*}{dt} = \lambda_c\,(c_i - c_i^*) \qquad \text{(VI.4 Referenzpunkt-Dynamik)}$$

$$r_i^{\text{wahr}} = r + \eta_i\,\pi - \frac{\varphi_i}{\mathcal{I}_i + \varepsilon} \qquad \text{(V.1a Wahrgenommener Zins)}$$

$$A_{ij}^{\text{eff}} = \sum_{\ell=1}^{5} \omega_\ell\,A_{ij}^{(\ell)} \qquad \text{(V.7 Multiplex)}$$

Vollständige **2N-dimensionale ODE**: N Konsum + N Referenzpunkte.

## Propositions (alle verifiziert)

| Proposition | Aussage | Validierung |
|-------------|---------|-------------|
| **Prop 6.1** | $\mathcal{I}\to\infty,\,c^*=c,\,A=0 \Rightarrow$ reiner Euler-Pfad | max\_rel\_err = 1.52×10⁻⁴ |
| **Prop 6.3** | Dominanzwechsel: Normal→R, Krise→Ψ+S | Normal: \|R\|>Ψ+S, Krise: Ψ+S>\|R\| |
| **Prop 6.4** | $\Psi=0,\,\Phi=0 \Rightarrow$ Standardmodell | V.1 nur ≡ Euler-Pfad |

## Kernergebnisse

### R1: Normal Economy (V.1 dominiert)
- c_mean: 10.8 → 8.32, Gini: 0.278 → 0.120
- Layer-Normen (t=T): **\|R\|=5.63** > \|Ψ\|=0.53, \|S\|=5.05
- V.1 (Euler) dominiert — rationale Agenten folgen dem Zinspfad
- V.3 (Herding) als zweitstärkste Kraft equalisiert die Verteilung

### R2: Bubble Build-up (Hub-Kaskade via V.3)
- Hub-Agent (c₀=50, gut informiert I=60) → Netzwerk-Ansteckung
- Hub c: 50 → 17.44 (sinkt), Mean c: 11.2 → 14.72 (steigt)
- Gini: 0.299 → 0.085 — **Konvergenz zum Konsens**
- α_up=0.25 (erhöht) treibt Aufwärts-Kaskade

### R3: Financial Crisis (V.2+V.3 dominieren)
- 50% Konsumschock + Info-Kollaps (I·0.05) + erhöhte Friktion
- c_mean: 5.4 → 0.14, Gini: 0.278 → 0.635
- Layer (t=T): R=0.93, **Ψ=0.71, S=0.41** → Ψ+S (1.12) > R (0.93)
- **Dominanzwechsel bestätigt** (Prop 6.3): In der Krise dominieren
  psychologische und soziale Kräfte über rationale Optimierung

### R4: Lifestyle Creep (Referenzpunkt-Drift)
- c* startet 30% unter c → adaptiert langsam aufwärts (λ_c=0.05)
- c*_mean: 7.6 → 8.26 (Drift +0.69)
- c_mean: 10.8 → 7.70 — Konsum sinkt trotz steigender Referenz
- **Hedonische Tretmühle**: Steigende Ansprüche bei sinkendem Konsum

### R5: Information Heterogeneity (Klassen-Bifurkation)
- Bimodale I-Verteilung: 50% uninformiert (I=0.5), 50% Elite (I=50)
- **Elite c(T)=21.31 vs Masse c(T)=9.12** → Ratio 2.34
- Gini: 0.278 → 0.250 — nur leichte Reduktion
- **Einziger Parameter I spaltet System in 2 Klassen**

### R6: Post-Pandemic Caution (erhöhte Risikoaversion)
- φ·3 (Friktion), γ·2.5 (Risikoaversion), λ=3.5 (Verlustaversion)
- c_mean: 10.8 → 5.88, Gini: 0.278 → 0.118
- Vorsichtsverhalten senkt Konsum ~50%, aber equalisiert (Gini −57%)

### R7: Inequality Spiral (Gini-Nicht-Monotonie)
- Breite Anfangsverteilung (Lognormal σ=1.0)
- Gini: 0.519 → peak 0.519 (t=0) → 0.123 (monoton fallend)
- Herding-Kraft equalisiert selbst extreme Anfangsungleichheit
- Konvergenzzeit abhängig von Netzwerk-Topologie

### R8: Neoklassischer Grenzfall (Prop 6.1)
- I=10⁸, c*=c, A=0 → reiner Euler-Pfad
- **max|c_num − c_euler|/c_euler = 1.52×10⁻⁴** ≪ 2% Toleranz
- Numerisch exakte Reproduktion des Ramsey-Modells
- Bestätigt: Drei-Ebenen-System enthält Standardmodell als Spezialfall

### Ebenen-Vergleich

| Konfiguration | c_mean(T) | Gini(T) | Interpretation |
|--------------|-----------|---------|----------------|
| V.1 nur | 5.15 | **0.638** | Reiner Euler — maximale Ungleichheit |
| V.1+V.2 | 6.47 | 0.502 | +Psychologie senkt Gini um 21% |
| V.1+V.3 | 6.92 | **0.130** | +Sozial senkt Gini um 80% |
| V.1+V.2+V.3 | 8.32 | **0.120** | Komplett: Gini um 81% reduziert |

**Zentrales Ergebnis**: V.3 (Netzwerk-Herding) ist der dominierende
Gleichheitstreiber — um Faktor 4 stärker als V.2 (Psychologie).

## Sensitivitätsanalysen

### SA1: α_up × λ_c → Gini(T) — 15×15 Heatmap
- Gini-Range: [0.022, 0.342]
- Hohes α_up + hohes λ_c → minimale Ungleichheit
- **Herding-Stärke dominiert**: α_up-Achse hat stärkeren Effekt als λ_c

### SA2: φ × I → Dominanz-Ratio |Ψ+S|/|R| — 15×15 Heatmap
- Dominanz-Range: [0.665, 13.659]
- Hohe Friktion + niedrige Information → V.2+V.3 dominieren
- **Phasengrenze bei Ratio=1**: Wechsel von R-Dominanz zu Ψ+S-Dominanz

### SA3: Netzwerk-Dichte × Topologie → Gini(T)
- G(d=0)=0.410 → G(d=0.35)=0.132 (Scale-Free)
- **Kritische Dichte ~0.05**: Unterhalb keine signifikante Equalisierung
- Scale-Free > Small-World > Random (Hub-Effekt beschleunigt)

### SA4: λ (Loss-Aversion) × α_up (Herding) → Konvergenzzeit — 15×15
- t_conv-Range: [8.1, 30.0]
- Starkes Herding (α_up>0.3) → schnelle Konvergenz (<10 ZE)
- Loss-Aversion hat schwachen Effekt auf Konvergenzgeschwindigkeit

### SA5: η (Fisher-Adaptation) → Gini(T)
- η=0: G=0.057, η=1: G=0.062
- **Schwacher Effekt**: Fisher-Adaptation ändert Gini minimal (±10%)
- Inflation-Illusion hat untergeordnete Rolle im Drei-Ebenen-System

## Erweiterte Analyse

### EA1: Dominanz-Dynamik (Normal vs Krise)
- **R1 (Normal)**: V.1 stabil dominant (~50%), V.3 ~45%, V.2 ~5%
- **R3 (Krise)**: Ψ steigt auf >50%, R sinkt, S instabil
- **Dominanzwechsel ist dynamisch** — nicht abrupt sondern gradual
- Krisenbeginn: Alle drei Kräfte vergleichbar (Trifurkationspunkt)

### EA2: Gini-Nicht-Monotonie
- R7: Gini monoton fallend (0.519 → 0.123)
- Kein Overshoot bei dieser Parametrierung
- Herding-Kraft konvergiert-monoton bei starker Anfangsungleichheit

### EA3: Hysterese-Test
- **Hysterese-Maß: 0.3149** (31.5% Abweichung nach Schock)
- Phase 1: Normal bis T/2 → Phase 2: 50% Schock → Weiterlauf
- System kehrt **NICHT** zum ungestörten Pfad zurück
- c*(t) als **Gedächtnisvariable**: Vergangene Krisen hinterlassen Spuren
- Ökonomisch: **Scarring Effect** quantifiziert

### EA4: Informations-Klassen-Bifurkation
- Elite (I>10): c(T) = 21.31 ± 2.36
- Masse (I<10): c(T) = 9.12 ± 3.18
- **Gap: 12.19, Ratio: 2.34**
- Information als einziger Parameter erzeugt persistente Zweiklassengesellschaft
- Verbindung zu S13: I-Diffusion (Fisher-KPP) bestimmt Klassenmobilität

## Mathematische Strukturen

### Struktur 1: Gradientensystem mit dreifacher Symmetriebrechung
$\frac{dc}{dt} = R(c) + \Psi(c,c^*) + S(c)$ ist ein **Nicht-Gradienten-System**:
- V.1: Exponentielles Wachstum bricht Stationarität
- V.2: λ≠1 (Verlustaversion) bricht Zeitumkehr-Symmetrie
- V.3: α_up≠α_down bricht Onsager-Reziprozität

→ Dreifache Symmetriebrechung erzeugt **permanente Entropieproduktion**.

### Struktur 2: Mehrskalige Separation
Drei Zeitskalen:
1. **Schnell**: c_i (Konsum, Euler-Rate ~0.01/dt)
2. **Mittel**: S_i (Netzwerk-Diffusion, ~α·⟨k⟩ ≈ 0.6)
3. **Langsam**: c*_i (Referenzpunkt, λ_c = 0.15)

→ **Tikhonov-Zerlegung** möglich: c quasi-stationär bezüglich c*.
→ Adiabatische Elimination: c*(t) als langsamer Parameter.

### Struktur 3: Nichtlineare Superposition
- Interaktions-Ratio = **0.816 (subadditiv)**
- V.2 und V.3 kompensieren sich teilweise
- V.2 zieht zu c* (individuell), V.3 zieht zum Netzwerk-Mittel (kollektiv)
- **Konkurrenz der Attraktoren**: Wenn c* ≠ ⟨c⟩_Nachbarn entsteht Frustration

### Struktur 4: Hysterese und Pfadabhängigkeit
- Hysterese-Maß = **0.3149**
- c*(t) trägt **Gedächtnis** vergangener Konsum-Niveaus (VI.4)
- System ist **nicht-autonom**: Zukunft hängt vom gesamten Pfad ab
- Mathematisch: Endlich-dimensionaler Attraktor mit Memory-Kernel

### Struktur 5: Informations-induzierte Klassen-Bifurkation
- Elite/Masse-Ratio = **2.34**
- I hoch → V.2, V.3 unterdrückt → fast reiner Euler-Pfad
- I niedrig → V.2, V.3 dominant → Herding + Psychologie steuern
- **Einziger Parameter I bifurziert** das System in 2 Klassen
- Topologischer Defekt im Parameterraum: I_crit ≈ 10

## Validierung: 8/8 PASS

| # | Test | Ergebnis |
|---|------|----------|
| V1 | Prop 6.1: I→∞, c*=c, A=0 ⇒ Euler | rel\_err=1.52×10⁻⁴ |
| V2 | Additivität: dc = R + Ψ + S | rel\_err=0.00 |
| V3 | Dominanz: Normal→R, Krise→Ψ+S | Prop 6.3 bestätigt |
| V4 | Gini: V.1+V.2+V.3 < V.1 | 0.120 < 0.638 |
| V5 | Ramsey-Limit: Elite~Euler trotz Netzwerk | err=0.53 |
| V6 | Stabilität: c>0, keine Explosion | c∈[0.01, 100] |
| V7 | Netzwerk equalisiert: G(3A)<G(0.2A) | 0.049 < 0.299 |
| V8 | Emergenz: Interaktionseffekt vorhanden | Ratio=0.816≠1 |

**Kumulativ: 123/123 Validierungen bestanden (S01–S21)**

## Emergente Phänomene

1. **Hysterese** (0.3149): Krisen hinterlassen permanente Spuren via c*-Gedächtnis
2. **Subadditivität** (0.816): V.2+V.3 kompensieren sich teilweise (Attraktor-Konkurrenz)
3. **Klassen-Bifurkation** (Ratio 2.34): Information allein erzeugt persistente Zweiklassengesellschaft
4. **Dominanzwechsel**: Normal→Krise verschiebt Balance von R zu Ψ+S
5. **Scarring Effects**: Quantifiziert durch Hysterese-Maß — Erholungspfad ≠ Vorkrisen-Pfad

## Kausalstruktur

```
NORMAL ECONOMY:
  r_wahr hoch + I hoch
    → R = (r_wahr-β)/γ · c dominiert
      → Euler-Pfad + schwaches Herding
        → Gradueller Gini-Rückgang

KRISE:
  I-Kollaps + Konsumschock (c→0.5c)
    → r_wahr sinkt (φ/(I+ε) steigt)
      → R sinkt / wird negativ
    → c < c* (Referenz noch beim alten Niveau)
      → Ψ > 0 (Verlustaversion treibt Konsum hoch)
    → Netzwerk-Effekte: S zieht zu sinkendem Mittel
      → Ψ + S > R (DOMINANZWECHSEL, Prop 6.3)
        → Psychologie + Soziales dominieren über Rationalität

HYSTERESE:
  Schock bei T/2 → c sinkt
    → c* adaptiert langsam (λ_c · (c-c*) · dt)
      → Nach Erholung: c* ≠ c*_vorher
        → Ψ(c,c*_neu) ≠ Ψ(c,c*_alt)
          → Pfadabhängigkeit: System "erinnert" die Krise
```

## Verbindungen

- **S17** (V.1 Euler): R-Komponente des Drei-Ebenen-Systems
- **S18** (V.1a Wahrgenommener Zins): r_wahr als Input für R
- **S19** (V.2 Prospect Theory): Ψ-Komponente
- **S20** (V.3 Soziale Vergleiche): S-Komponente + Netzwerk
- **S13** (Info-Fluss, Fisher-KPP): I-Dynamik bestimmt Klassenmobilität
- **Prop 6.1, 6.3, 6.4**: Alle drei Propositionen numerisch bestätigt
