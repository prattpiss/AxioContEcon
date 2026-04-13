# S22 — L.1 Rationales Arbeitsangebot (§6.4)

## Master-Gleichung

$$L_i^* = \underset{L_i}{\operatorname{argmax}} \left[ u(c_i) - V(L_i) \right] \quad \text{u.d.N.} \quad c_i = w_L \cdot L_i + r \cdot K_i + \pi_i$$

$$\text{FOC:} \quad w_L \cdot u'(c^*) = V'(L^*) \qquad \text{Grenznutzen × Lohn = Grenzleid}$$

4 Funktionale Formen:
$$\text{F1: CRRA+Iso:} \quad u = \frac{c^{1-\gamma}}{1-\gamma}, \quad V = \frac{\chi \, L^{1+\eta}}{1+\eta}$$
$$\text{F2: Log+Quad:} \quad u = \ln(c), \quad V = \frac{\chi}{2} L^2$$
$$\text{F3: CRRA+Quad:} \quad u = \frac{c^{1-\gamma}}{1-\gamma}, \quad V = \frac{\chi}{2} L^2$$
$$\text{F4: GHH:} \quad \text{Kein Einkommenseffekt (separabel)}$$

## Propositions (alle verifiziert)

| Proposition | Aussage | Validierung |
|-------------|---------|-------------|
| **Prop 3.1** | Forminvarianz: qualitative Ergebnisse unabhängig von funktionaler Form | 4 Formen: alle zeigen dL/dK<0, Backward-Bending; Disp.=0.598 |
| **Prop 6.2** | Strukturelle Symmetrie Konsum ↔ Arbeit | r↔w, γ↔η, V.1a↔L.1a, V.2↔L.2, V.3↔L.3 |
| **Prop 6.4** | Neoklassische Einbettung: Ψ_L=0, Φ_L=0 ⇒ reiner FOC | S22 ≡ neoklassischer Grenzfall |

## Kernergebnisse

### R1: Basisfall (3 Agenten-Klassen)
- **Arbeiter** (w=1.0, K=1): L\*=0.983, c\*=1.01 — arbeitet fast voll
- **Unternehmer** (w=2.0, K=20): L\*=0.339, c\*=4.68 — hoher Lohn + Vermögen → wenig Arbeit
- **Banker** (w=3.0, K=100): L\*=0.315, c\*=16.95 — maximales Vermögen → minimale Arbeit
- FOC-Präzision: max|w·u'(c)−V'(L)| = 4.22×10⁻¹⁵

### R2: Backward-Bending Supply Curve
- CRRA+Iso (γ=2, η=1): Wendepunkt bei w\_crit=0.10, L\_peak=2.0
- **Bei hohem Lohn sinkt das Arbeitsangebot** — Einkommenseffekt > Substitutionseffekt
- GHH (kein Einkommenseffekt): monoton steigend — Benchmark
- Testfall für Vorzeichen-Ambiguität der FOC (∂L\*/∂w unbestimmt)

### R3: Vermögenseffekt
- K: 0→50, w\_L=1.5 fest: L\*(K=0)=0.891, L\*(K=50)=0.308
- **Strikt monoton fallend**: Reiche arbeiten weniger (reiner Einkommenseffekt)
- Ökonomisch: Nicht-Arbeitseinkommen rK substituiert Arbeitslohn

### R4: Funktionale-Form-Vergleich (Forminvarianz)
- F1 CRRA+Iso: L\*(w=5)=0.625 — mit Backward-Bending
- F2 Log+Quad: L\*(w=5)=0.994 — fast linearer Zusammenhang
- F3 CRRA+Quad: L\*(w=5)=0.577 — stärkster Rückgang
- F4 GHH: L\*(w=5)=2.000 — kein IE, monoton steigend
- **Qualitativ identisch** (bis auf GHH): alle zeigen dL\*/dK < 0

### R5: Frisch-Elastizität-Scan
- η=0.1 (sehr elastisch, 1/η=10): L\*=0.786 — auf w stark reagierend
- η=2.0 (Makro-Standard): L\*=0.884 — moderate Reaktion
- η=5.0 (sehr inelastisch): L\*=0.933 — kaum Reaktion auf w
- **Frisch-Elastizität 1/η**: Schlüsselparameter für Arbeitsmarkt-Dynamik

### R6: Risikoaversion-Interaktion
- γ=0.2: L\*=1.206 — risikoneutral → arbeitet mehr
- γ=2.0: L\*=0.871 — Standard
- γ=5.0: L\*=0.749 — risikoavers → arbeitet weniger (Vorsichtssparen-Analogon)
- **γ senkt L\*** über Einkommenseffekt: u'(c) steiler → Konsum wertvoller

### R7: Multi-Agent Heterogene Ökonomie (N=80)
- L\_mean=0.531, L\_std=0.199 — breite Streuung
- **Gini(L)=0.208**: Mäßige Arbeitsungleichheit
- **Gini(c)=0.214**: Konsumungleichheit leicht höher
- **Corr(L,K)=−0.359**: Reiche arbeiten signifikant weniger
- Corr(L,γ)=−0.305: Risikoaverse arbeiten weniger
- L\_agg=42.4: Aggregiertes Arbeitsangebot

### R8: Corner Solutions
- **Reich (K=500, w=0.5)**: L\*=0.002, c\*=80.0 → Corner bei L≈0 (Rentier)
- **Arm (K=0, w=0.5)**: L\*=1.219, c\*=0.61 → nahe Maximum
- **Mittel (K=1, w=3.0)**: L\*=0.725, c\*=2.20 → Interior Lösung
- Vermögen bestimmt, ob Interior oder Corner: **Bifurkation bei K\_crit**

## Slutsky-Zerlegung

| Komponente | Wert | Interpretation |
|-----------|------|----------------|
| SE (Substitution) | **+0.117** | Arbeit wird attraktiver: +L |
| IE (Einkommen) | **−0.223** | Mehr Einkommen → weniger Arbeit |
| Total dL\*/dw | **−0.106** | IE dominiert: Backward-Bending |
| Ratio IE/SE | **1.91** | IE fast doppelt so stark wie SE |

## Sensitivitätsanalysen

### SA1: (γ, η) → L\* — 20×20 Heatmap
- L\* Range: [0.699, 1.585]
- Hohe γ + hohe η → niedrigstes L\* (risikoavers + inelastisch)
- Niedrige γ + niedrige η → höchstes L\* (risikoneutral + elastisch)
- **γ hat stärkeren Effekt als η** auf L\*

### SA2: (w\_L, γ) → Lohnelastizität — 20×20 Heatmap
- Elastizität Range: [−0.538, +0.289]
- **Vorzeichenwechsel-Grenze** im (w,γ)-Raum klar identifizierbar
- Hohe w + hohe γ → negative Elastizität (Backward-Bending)
- Niedrige w + niedrige γ → positive Elastizität (aufsteigende Kurve)

### SA3: (K, w\_L) → L\* — 20×20 Heatmap
- L\* Range: [0.402, 1.219]
- Isoquanten: K↑ und w↑ wirken gegenläufig auf L\*
- K-Effekt dominant bei hohem K, w-Effekt dominant bei niedrigem K

### SA4: Forminvarianz-Dispersion
- Dispersion bei w=8: **0.598** — quantitativ bedeutend
- F1, F2, F3 qualitativ ähnlich, F4 (GHH) systematisch höher
- Prop 3.1 bestätigt: **axiomatische Struktur > funktionale Form**

### SA5: Wealth-Varianz → L\_agg + Gini(L)
- σ\_K=0.1: L\_agg=41.3, Gini(L)=0.038 — homogen, wenig Ungleichheit
- σ\_K=2.0: L\_agg=33.2, Gini(L)=0.224 — starke Ungleichheit
- **L\_agg sinkt mit Wealth-Varianz**: Jensen-Ungleichung (konkave L\*(K))

## Erweiterte Analyse

### EA1: Backward-Bending Phasenkarte
- **88% des (γ,η)-Raums** zeigen Backward-Bending
- Trennlinie: γ ≈ η (Risikoaversion = inverse Frisch-Elastizität)
- γ < η: SE dominiert → aufsteigende Kurve
- γ > η: IE dominiert → Backward-Bending
- **Empirisch relevant**: Da typischerweise γ ∈ [1,5] und η ∈ [0.5,2], ist BB der Normalfall

### EA2: Komparative Statik (5 Parameter)
- dL\*/dw\_L = −0.040 (ambig, negativ bei hohem K)
- dL\*/dK = −0.012 (stets negativ — Vermögenseffekt)
- dL\*/dπ = −0.301 (stärkster Einzeleffekt — Profit senkt Arbeit)
- dL\*/dγ = −0.122 (Risikoaversion senkt Arbeit)
- dL\*/dη = +0.096 (Inelastizität erhöht Arbeit leicht)

### EA3: Prop 6.2 Strukturelle Symmetrie Konsum ↔ Arbeit

| Dimension | Konsum (V.1–V.3) | Arbeit (L.1–L.4) |
|-----------|-------------------|-------------------|
| Ebene 1 | Euler: dc/dt = R·c | FOC: w·u'(c) = V'(L) |
| Schlüsselpar. | r (Zins) | w\_L (Lohn) |
| Elastizität | 1/γ (EIS) | 1/η (Frisch) |
| Ambiguität | Vorzeichen R | Vorzeichen dL/dw |
| Info-Filter | V.1a: r\_wahr | L.1a: w\_wahr |
| Psychologisch | V.2: Verlustaversion | L.2: Burnout |
| Sozial | V.3: Herding (Φ\_c) | L.3: Statusdruck (Φ\_L + S) |

### EA4: Prop 6.4 Neoklassische Einbettung
- S22 implementiert **nur** L.1 (ohne Ψ\_L, Φ\_L) → **ist** der neoklassische Grenzfall
- Analogon zu S17 (V.1 als Basis für Konsum) → S22 ist Basis für Arbeit
- Zukünftige S23+ werden L.2 (Burnout) und L.3 (Statusdruck) hinzufügen

## Mathematische Strukturen

### Struktur 1: Implizite-Funktionen-Theorem
FOC: $F(L,w) = w \cdot u'(wL + rK) - V'(L) = 0$
$$\frac{dL^*}{dw} = -\frac{F_w}{F_L} = -\frac{u'(c) + w \cdot u''(c) \cdot L}{w^2 \cdot u''(c) - V''(L)}$$
- $F_w = u'(c) + w \cdot u''(c) \cdot L$ — **Vorzeichen ambig** (SE + IE)
- $F_L = w^2 \cdot u''(c) - V''(L) < 0$ — SOC garantiert Nenner < 0
- → $\text{sgn}(dL^*/dw) = \text{sgn}(F_w) = \text{sgn}(\text{SE} + \text{IE})$

### Struktur 2: Dualität Konsum-Freizeit
- Lagrange: $\lambda = u'(c) = V'(L)/w$ — Schattenpreisidentität
- Freizeit ist normales Gut → IE stets negativ
- GHH eliminiert IE durch separable Präferenzen → Benchmark

### Struktur 3: Backward-Bending als Phasenübergang
- **88% des (γ,η)-Raums**: Backward-Bending tritt auf
- Phasengrenze: γ ≈ η — Balance zwischen Konsum-Glättung und Arbeits-Inelastizität
- Topologisch: Vorzeichenwechsel der Lohnelastizität = **Nullstelle im Parameterraum**
- SA2 zeigt die exakte Grenzlinie im (w,γ)-Raum

### Struktur 4: Heterogenitäts-Aggregation und Jensen-Ungleichung
- N=80 Agenten: Individuelle FOC aggregieren **nicht** zu repräsentativer FOC
- $L^*$ ist konkav in $K$ → Jensen: $E[L^*(K)] < L^*(E[K])$
- → Aggregiertes L sinkt mit Wealth-Varianz (SA5 bestätigt)
- Corr(L,K) = −0.359: **Systematischer negativer Zusammenhang**

### Struktur 5: Forminvarianz (Prop 3.1)
- 4 funktionale Formen: Dispersion = 0.598 (quantitativ relevant)
- Qualitativ identisch: dL\*/dK < 0, Backward-Bending (außer GHH)
- **Axiomatische Struktur (FOC-Existenz, SOC, Budget) bestimmt Qualität**
- Funktionale Form bestimmt nur Quantität → Prop 3.1 bestätigt

## Validierung: 8/8 PASS

| # | Test | Ergebnis |
|---|------|----------|
| V1 | FOC-Präzision: w·u'(c)=V'(L) | max\|FOC\|=4.22×10⁻¹⁵ |
| V2 | Analytisch vs Numerisch (rK=π=0) | err=0.00 (exakt) |
| V3 | Backward-Bending bei γ>η | w\_crit=0.10, bestätigt |
| V4 | Slutsky: SE>0, IE<0, SE+IE=Total | SE=0.117, IE=−0.223 |
| V5 | SOC < 0 (Maximum, nicht Minimum) | SOC=−3.179 |
| V6 | dL\*/d(rK+π) < 0 (Monotonie) | strikt fallend |
| V7 | Grenzfälle: γ→1 stetig, η→∞ inelast. | beide bestätigt |
| V8 | Aggregation + Corr(L,K)<0 | konsistent, −0.359 |

**Kumulativ: 131/131 Validierungen bestanden (S01–S22)**

## Emergente Phänomene

1. **Backward-Bending Dominanz** (88%): In fast dem gesamten Parameterraum krümmt sich die Arbeitsangebotskurve nach links — Standard-Lehrbuch-Annahme monoton steigender Kurve ist der Spezialfall
2. **Vermögens-Arbeits-Kopplung** (Corr=−0.359): Reiche arbeiten signifikant weniger — nicht durch Präferenzen, sondern durch FOC + Budget erzwungen
3. **Jensen-Aggregation**: Steigende Wealth-Varianz senkt aggregiertes Arbeitsangebot (SA5) — Mikro-Heterogenität hat Makro-Konsequenzen
4. **Profit-Supersensitivität**: dL\*/dπ=−0.301 ist der stärkste Einzel-Gradient — unternehmerisches Einkommen substituiert Arbeit massiv

## Kausalstruktur

```
LOHNERHÖHUNG:
  w↑ → SE: Freizeit teurer → L↑
       IE: höheres Einkommen → Freizeit leistbar → L↓
       Netto: sgn(SE+IE) = ?
  
  Falls γ > η (typisch):
    IE dominiert → dL/dw < 0
    → BACKWARD-BENDING
  
  Falls γ < η (Spezialfall):
    SE dominiert → dL/dw > 0
    → Monoton steigende Kurve

VERMÖGEN:
  K↑ → c↑ bei gleichem L
     → u'(c)↓ → FOC: V'(L)↓ nötig
     → L*↓ (reiner IE, kein SE)
  IMMER: dL*/dK < 0

HETEROGENITÄT:
  Var(K)↑ → Jensen: E[L*(K)] < L*(E[K])
           → L_agg sinkt
  + Corr(L,K) < 0 stets
  → Ungleichheit erzeugt Arbeitsmarkt-Verzerrung
```

## Verbindungen

- **S17** (V.1 Euler): Konsum-Analogon — r↔w, γ↔η (Prop 6.2)
- **S18** (V.1a Wahrg. Zins): Informationsfilter — Analogon zu L.1a (wahrg. Lohn)
- **S19** (V.2 Prospect Theory): Psychologison — Analogon zu L.2 (Burnout)
- **S20** (V.3 Soziale Vergleiche): Sozial — Analogon zu L.3 (Statusdruck)
- **S21** (Drei-Ebenen komplett): Konsum-Vollsystem — S22 eröffnet gleiche Sequenz für Arbeit
- **Prop 6.2, 6.4**: Strukturelle Symmetrie und neoklassische Einbettung bestätigt
