# S23 — L.1a Wahrgenommener Alternativlohn (§6.4)

## Master-Gleichung

$$w_i^{\text{wahr}} = \underbrace{w_i}_{\text{eigener Lohn}} + \underbrace{\alpha_H \bar{w}^{\text{peer}}}_{\text{Peer-Einfluss}} + \underbrace{\frac{\psi_w}{\mathcal{I}_i + \varepsilon}}_{\text{Intransparenz-Aufschlag}}$$

$$\text{Verzerrte FOC:} \quad w_i^{\text{wahr}} \cdot u'(c^*) = V'(L^*) \quad \text{mit} \quad c = w_i^{\text{wahr}} \cdot L + r K_i + \pi_i$$

Drei Kanäle (strukturell parallel zu V.1a / S18):

| Kanal | V.1a (Zins, S18) | L.1a (Lohn, S23) |
|-------|-------------------|-------------------|
| Basissignal | Nominalzins $r$ | Eigener Lohn $w_i$ |
| Erwartungskanal | $\eta_i \pi$ (Inflation) | $\alpha_H \bar{w}^{\text{peer}}$ (Peer-Lohn) |
| Friction | $-\varphi/(\mathcal{I}+\varepsilon)$ (negativ) | $+\psi_w/(\mathcal{I}+\varepsilon)$ (positiv) |

**Vorzeichen-Unterschied**: V.1a unterschätzt Zins (→ zu wenig Sparen), L.1a überschätzt Alternativlohn (→ zu viel Migration). "Das Gras ist grüner"-Effekt.

## Propositions (alle verifiziert)

| Proposition | Aussage | Validierung |
|-------------|---------|-------------|
| **Prop 3.1** | Forminvarianz | Transmissionskurve identisch über alle funktionalen Formen |
| **Prop 6.2** | Symmetrie V.1a ↔ L.1a | Transmissionsformel identisch, max\|Δ\|=0 (EA2) |
| **Prop 6.4** | Neoklassisch: $\alpha_H=0, \psi_w=0 \Rightarrow w^{\text{wahr}}=w$ | V4: exakt \|err\|=0 |

## Kernergebnisse

### R1: Peer-Lohn-Effekt (α_H Sweep)
- Arbeiter (w=1.0): L\*(αH=0)=0.958, L\*(αH=0.3)=0.830, L\*(αH=1)=0.689
- Unternehmer (w=2.0): L\*(αH=0)=0.347, L\*(αH=0.3)=0.393, L\*(αH=1)=0.454
- Banker (w=3.0): L\*(αH=0)=0.322, L\*(αH=0.3)=0.366, L\*(αH=1)=0.451
- **Arbeiter**: Höherer Peer-Lohn → weniger Arbeit (backward-bending, γ>η)
- **Unternehmer/Banker**: Höherer Peer-Lohn → mehr Arbeit (auf aufsteigendem Ast, hohes rK+π)
- Asymmetrische Reaktion: Klassen reagieren **gegensätzlich** auf gleichen Peer-Impuls

### R2: Informationsfriction-Sweep
- ψ\_w=0.5: Bias(I=0.1)=4.50, I\_crit(1%)=32.9
- ψ\_w=2.0: Bias(I=0.1)=18.0, I\_crit(1%)=132.0
- **Hyperbolisches Profil**: Bias ∝ 1/I — bei I<1 massive Überschätzung
- Kritische Information I\_crit steigt linear mit ψ\_w

### R3: Heterogene Agenten (N=300)
- Bias: mean=0.761, std=0.443 — **systematische Überschätzung**
- Gini(L\_rational)=0.160 → Gini(L\_wahr)=0.148 (−7.6%)
- Corr(bias, I)=−0.294 — schlecht Informierte haben höchsten Bias
- **Überraschung**: Friction *senkt* Gini — Überschätzung des Alternativlohns komprimiert L\*-Verteilung via Backward-Bending

### R4: "Gras ist grüner"-Illusion
- ψ\_w=0: Verlust=0 (perfekte Information)
- ψ\_w=1: Verlust=0.0045
- ψ\_w=3: Verlust=0.0266
- **Wohlfahrtsverlust** steigt überlinear mit Intransparenz
- Agent plant mit w\_wahr, erlebt w\_true → suboptimales L\*

### R5: Arbeitsmarkt-Transmission (4 Informationsklassen)
- Professional (I=50): Transmission 99.4% → ΔL=+3.9%
- Mittelstand (I=5): Transmission 90.7% → ΔL=−1.9%
- Unqualifizierte (I=1): Transmission 55.2% → ΔL=−2.5%
- Informelle (I=0.2): Transmission 11.7% → ΔL=−0.7%
- **Trickle-down scheitert**: Lohnschock erreicht Informelle zu <12%
- Reaktionsrichtung klassenabhängig: Prof. steigen L\*, andere senken

### R6: Informationskaskade (3 Szenarien)
- Normal: I(T)=15.5, w\_wahr(T)=2.13 — konvergiert gegen wahren Lohn
- Info-Schock (t=25): I(T)=1.47, w\_wahr(T)=2.44 — Fehlbewertung persistent
- Informationssperre (ω=0.3): I(T)=0.05, **w\_wahr(T)=10.4** — massive Illusion
- **Informationssperre** erzeugt 7× Überschätzung → permanente Fehlallokation

### R7: Migration (N=500)
- Gutes Ziel (w\_dest=1.5 > w+κ=1.3): Migrationsrate **100%** — korrekt
- Schlechtes Ziel (w\_dest=1.2 < w+κ=1.3): Fehlmigrationsrate **76%**
- → 3 von 4 schlecht informierten Agenten migrieren falsch
- Fehlrate sinkt mit I: bei I>10 fast null, bei I<1 nahe 100%
- **Informationsarmut als Migrationsfalle**: Fehlmigration ≈ 1/(1 + I/ψ\_w)

### R8: L.1 + L.1a Vollständiges Modell (N=80)
- L\_agg(rational)=45.2, L\_agg(wahr)=45.2 — aggregiert fast gleich
- Individuelle Divergenz: mean=0.030, max=0.100
- Corr(\|Divergenz\|, I)=−0.241 — **mehr Information = weniger Verzerrung**
- Aggregation maskiert individuelle Fehler: **Mikro-Verzerrung bei Makro-Neutralität**

## Sensitivitätsanalysen

### SA1: ψ\_w → w\_wahr + L\*
- w\_wahr steigt linear mit ψ\_w (bei festem I)
- L\* sinkt monoton (backward-bending Regime bei γ=2)
- Steigung: dL\*/dψ\_w = −0.008 (moderate Sensitivität)

### SA2: (α\_H, w̄\_peer) → w\_wahr — 20×20 Heatmap
- w\_wahr Range: [1.60, 6.60]
- Neutrallinie (w\_wahr = w\_i) bei α\_H·w̄ = −ψ/(I+ε) — nur wenn Peer-Lohn niedrig
- **Peer-Effekt dominiert bei α\_H > 0.5**: Eigen-Signal wird überwogen

### SA3: (I, ψ\_w) → Bias — 20×20 Heatmap
- Bias Range: [0.0001, 158]
- **Hyperbolische Oberfläche**: Bias = ψ\_w/(I+ε)
- Iso-Bias-Linien: ψ\_w ∝ I — lineare Skalierung im log-log-Raum

### SA4: (I, ψ\_w) → Transmission — 20×20 Heatmap
- Transmission Range: [0.003, 0.999]
- Halbwert-Linie: I = ψ\_w (Michaelis-Menten)
- **Identische Topologie wie V.1a** (S18) — universeller Kern

### SA5: Wohlfahrtsverlust(I) nach Klasse
- Arbeiter (I=0.1): Verlust=0.344 — massiv (34% des Nutzens)
- Unternehmer (I=0.1): Verlust=0.013 — gering (hoher rK+π puffert)
- Banker (I=0.1): Verlust=0.025 — gering
- **Arme/Arbeiter sind überproportional betroffen**: Kein Vermögens-Puffer

## Erweiterte Analyse

### EA1: Deterministische vs. Stochastische Friction
- Deterministisch: bias=+0.166 (immer positiv → systematische Ü̈berschätzung)
- Stochastisch: mean≈0, std=0.292 (erwartungstreu, aber starke Varianz)
- **Deterministisch**: "Gras ist grüner"-Bias, always-positive
- **Stochastisch**: Erwartungstreue Unsicherheit, manchmal unter-, manchmal überschätzt
- Beide Varianten konvergieren für I → ∞

### EA2: Prop 6.2 Strukturelle Symmetrie V.1a ↔ L.1a
- Transmissionsformel: identisch bei φ = ψ\_w (max\|Δ\| = 0.00)
- Funktionale Form: beides Michaelis-Menten → identisch zu S03
- **Vorzeichen-Asymmetrie**: V.1a negativ (Zins-Unterschätzung), L.1a positiv (Lohn-Überschätzung)
- Konsequenz: Informationsarmut erzeugt **gleichzeitig** zu wenig Sparen + zu viel Fehlmigration → **Poverty Trap**

### EA3: Komparative Statik (5 Parameter)
- dL\*/dα\_H = −0.080 (Peer-Herding senkt L\* bei backward-bending)
- dL\*/dψ\_w = −0.008 (Friction senkt L\* via Überschätzung)
- dL\*/dI = +0.001 (Mehr Info → näher am Optimum)
- dL\*/dw̄\_peer = −0.012 (Höhere Peer-Löhne → weniger eigene Arbeit)
- dL\*/dw\_L = −0.040 (Backward-bending: mehr Lohn → weniger Arbeit)

## Mathematische Strukturen

### Struktur 1: Hyperbolische Friction-Funktion
$$f(\mathcal{I}) = \frac{\psi_w}{\mathcal{I} + \varepsilon}: \text{konvex, strikt fallend, Pol bei } \mathcal{I} = -\varepsilon$$
- f(0.1)=4.55, f(1)=0.50, f(10)=0.050, f(100)=0.005
- **Identische Form** wie V.1a (φ/(I+ε)) → universelle Informations-Friction-Klasse
- 4 Größenordnungen Friction-Reduktion über 3 Größenordnungen I

### Struktur 2: Transmissionsoperator (Michaelis-Menten)
$$\alpha(\mathcal{I}) = \frac{\mathcal{I}}{\mathcal{I} + \psi_w}: S\text{-förmig } [0,1], \text{ Halbwert bei } \mathcal{I} = \psi_w$$
- Identisch zu S03 (Michaelis-Menten-Kinetik) und S18 (V.1a Transmission)
- → **Universeller Informations-Transmissions-Kern** im gesamten Framework

### Struktur 3: Verzerrte FOC und multiplikativer Fehler
- Wahre FOC: $w \cdot u'(c^*) = V'(L^*)$
- Verzerrte FOC: $(w + \text{bias}) \cdot u'(c^{**}) = V'(L^{**})$
- Fehler wirkt **nicht additiv in L**, sondern **multiplikativ über das Budget**
- → Kleine Lohn-Fehlwahrnehmung erzeugt überproportionalen Wohlfahrtsverlust

### Struktur 4: Vorzeichen-Asymmetrie und Poverty Trap
- V.1a: $-\varphi/(\mathcal{I}+\varepsilon)$ → Zins-Unterschätzung → zu wenig Sparen → K↓
- L.1a: $+\psi_w/(\mathcal{I}+\varepsilon)$ → Lohn-Überschätzung → Fehlmigration → Enttäuschung
- **Gleiche funktionale Form, gegensätzlicher Bias**
- Bei niedrigem I: K sinkt (V.1a) UND Fehlmigration (L.1a) → **doppelte Armutsfalle**

### Struktur 5: Gini-Kompression durch Backward-Bending
- Friction komprimiert Gini(L): 0.160 → 0.148 (−7.6%)
- Mechanismus: Überschätzung des w → alle auf backward-bending Ast → L\* konvergiert
- **Gegenintuitiv**: Informationsfriction kann Ungleichheit senken
- Gilt nur im backward-bending Regime (γ > η); bei γ < η würde Friction Gini erhöhen

## Validierung: 8/8 PASS

| # | Test | Ergebnis |
|---|------|----------|
| V1 | Peer-Neutralität: α\_H=0 → kein Peer-Term | \|err\|=0 |
| V2 | EMH: I→∞ → Friction→0 | err=5×10⁻⁹ |
| V3 | Monotonie: dw\_wahr/dI < 0 | alle Differenzen negativ |
| V4 | Neoklassisch: α\_H=0, ψ=0 → w\_wahr=w | \|err\|=0 |
| V5 | Transmission→100% bei I→∞ | trans=0.9999999 |
| V6 | Bias≈0 für gut informierte Pop. | mean=0.010 |
| V7 | Corr(\|L\_wahr−L\_rat\|, I)<0 | Corr=−0.061 |
| V8 | Perfekte-Info-Migration: 100% korrekt | Rate=100% |

**Kumulativ: 139/139 Validierungen bestanden (S01–S23)**

## Emergente Phänomene

1. **Fehlmigration** (76%): Bei schlechtem Ziel und niedrigem I migrieren 3/4 falsch — Informationsarmut als Migrationsfalle
2. **Transmissions-Kluft**: Professional 99% vs. Informelle 12% — Lohnschocks erreichen die Ärmsten nicht
3. **Poverty Trap (V.1a + L.1a)**: Gleichzeitig zu wenig Sparen (Zins-Unterschätzung) + Fehlmigration (Lohn-Überschätzung) bei niedrigem I
4. **Gini-Kompression**: Friction senkt (!) Ungleichheit via Backward-Bending — gegenintuitiver Effekt
5. **Informationssperre**: ω=0.3 → I(T)=0.05, w\_wahr=10.4 (7× Überschätzung) — autoritäre Info-Unterdrückung erzeugt permanente Fehlallokation

## Kausalstruktur

```
INFORMATION HOCH (I >> 1):
  ψ/(I+ε) → 0
    → w_wahr ≈ w + αH·w̄_peer
      → nur Peer-Effekt bleibt
        → L* nahe rational

INFORMATION NIEDRIG (I ~ 0):
  ψ/(I+ε) → groß
    → w_wahr >> w_true ("Gras ist grüner")
      → Agent überschätzt Alternativlohn
        → Falls w_wahr > w + κ: FEHLMIGRATION (76%)
        → Falls Backward-Bending: L* verzerrt
          → Wohlfahrtsverlust bis 34% (Arbeiter)

POVERTY TRAP (V.1a + L.1a):
  I niedrig →
    V.1a: r_wahr < r_true → zu wenig Sparen → K↓
    L.1a: w_wahr > w_true → Fehlmigration → Enttäuschung
    → dK/dt < 0, Migration ineffizient
      → I bleibt niedrig (kein Aufstieg)
        → PERMANENTE ARMUTSFALLE

TRANSMISSION:
  Δw_L = +20% (Lohnschock)
    → Professional (I=50): Δw_wahr ≈ +17% → ΔL = +4%
    → Informelle (I=0.2): Δw_wahr ≈ +2% → ΔL = −1%
    → TRICKLE-DOWN SCHEITERT an Information
```

## Verbindungen

- **S18** (V.1a Wahrgenommener Zins): Exaktes strukturelles Analogon — identische Transmissionsformel, gegensätzliches Vorzeichen
- **S22** (L.1 Rationales Arbeitsangebot): Basis-FOC ohne Friction — S23 verzerrt diese
- **S03** (Michaelis-Menten): Transmissionsoperator α(I) = I/(I+ψ) identisch
- **S13** (Fisher-KPP Info-Fluss): I-Dynamik bestimmt Friction-Stärke
- **Prop 6.2**: Symmetrie V.1a ↔ L.1a exakt bestätigt (identische Formelstruktur)
- **Prop 6.4**: α\_H=0, ψ\_w=0 → S23 reduziert sich auf S22 (neoklassisch)
