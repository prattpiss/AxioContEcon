# S14 – Nutzenordnung U.1 (§6.1) — Ergebnisbericht

## Gleichung

$$u_i = u(c_i, l_i;\, \gamma_i, c_i^*)$$

Axiomatisch: $u' > 0$ (Monotonie), $u'' < 0$ (Konkavität).

Vier Funktionalformen verglichen:
- **CRRA**: $u(c) = \frac{(c-c^*)^{1-\gamma}-1}{1-\gamma}$, $\gamma \neq 1$
- **Logarithmisch**: $u(c) = \ln(c-c^*)$ (Spezialfall CRRA $\gamma \to 1$)
- **CARA**: $u(c) = -e^{-\alpha c}$
- **Epstein-Zin**: $V = (1-\delta)c^{1-\rho} + \delta(\mathbb{E}[V^{1-\alpha}])^{(1-\rho)/(1-\alpha)}$

## Kopplung / Kausalitätsketten

| Kette | Mechanismus | Wirkung |
|-------|------------|---------|
| U.1 → V.1 | $\gamma$ bestimmt Euler: $\dot{c}/c = (r-\beta)/\gamma$ | Höhere Risikoaversion → langsameres Konsumwachstum |
| U.1 → III.2 | Merton: $w^* = (\mu-r)/(\gamma\sigma^2)$ | Höhere RA → kleinerer Aktienanteil |
| II.3 → U.3 | $p_k^{\text{eff}} = p_k(1+\psi/(\mathcal{I}+\varepsilon))$ | Weniger Information → teurere Güter → weniger Konsum |
| VI.4 → U.1 | $\dot{c}^* = \lambda_c(c-c^*)$ | Referenzpunkt verfolgt Konsum → Hedonic Treadmill |
| VI.2 → U.1 | $\dot{\gamma} = \alpha_\gamma(\gamma^*-\gamma) + \beta_\gamma \cdot \text{Verlust}$ | Endogene RA: Verluste → $\gamma\uparrow$ → stabilisierend |
| Stabilisierend | Verlust → $\gamma\uparrow$ → weniger Risiko → Erholung | Negativer Feedback Loop |
| Destabilisierend | Gewinn → $\gamma\downarrow$ → mehr Risiko → Blase | Positiver Feedback Loop |

## Regime und Ergebnisse

### R1: CRRA-Vergleich ($\gamma$ = 0.5, 1, 2, 5)
- Alle Formen strikt monoton ($u'>0$) und konkav ($u''<0$) ✅
- $u(1) = 0$ für alle $\gamma$ (normierte Form mit $-1$ im Zähler)
- $u'(1) = 1$ universell (Grenznutzen am Referenzpunkt gleich)
- Relative Risikoaversion **exakt konstant**: $-c \cdot u''/u' = \gamma$ (Fehler < $10^{-15}$)

### R2: CARA-Vergleich ($\alpha$ = 0.5, 1, 2, 5)
- Absolute Risikoaversion **exakt konstant**: $-u''/u' = \alpha$ (Fehler < $10^{-15}$)
- CARA sättigt schneller als CRRA bei hohem $c$ (exponentielle Begrenzung)

### R3: Prospect Theory ($\lambda$ = 1, 1.5, 2.25, 3)
- Referenzpunkt $c^* = 1.0$, Kahneman-Tversky $\gamma = 0.88$
- **Knick bei $c = c^*$**: Steigungsverhältnis Verlust/Gewinn = $\lambda$ exakt (2.250 gemessen)
- $\lambda = 2.25$ (empirischer K-T-Wert): Verluste wiegen 2.25× schwerer als Gewinne
- Implikation: Konsumenten vermeiden Abweichungen unter den Referenzpunkt überproportional

### R4: Euler-Dynamik ($r = 4\%$, $\beta = 3\%$)
| $\gamma$ | $(r-\beta)/\gamma$ | $c(T=50)$ |
|-----------|-------------------|-----------|
| 0.5 | 2.0%/a | 2.718 |
| 1.0 | 1.0%/a | 1.649 |
| 2.0 | 0.5%/a | 1.284 |
| 5.0 | 0.2%/a | 1.105 |

**Kausalität**: $\gamma$ steuert Konsumwachstum hyperbolisch. Verdopplung der RA halbiert die Wachstumsrate.

### R5: Habitformation ($\lambda_c$ = 0, 0.05, 0.2, 0.5)
| $\lambda_c$ | Surplus $c(T)-c^*(T)$ | Interpretation |
|-------------|----------------------|----------------|
| 0 (kein Habit) | 1.426 | Steigendes Wohlbefinden |
| 0.05 (langsam) | 0.372 | Referenzpunkt holt auf |
| 0.20 (mittel) | 0.106 | Hedonic Treadmill aktiv |
| 0.50 (schnell) | 0.044 | Fast vollständige Adaptation |

**Kausalität**: Hohe $\lambda_c$ → Referenzpunkt passt sich schnell an → Surplus konvergiert gegen $(r-\beta)/(\gamma\lambda_c) \cdot c$ → hedonistische Tretmühle.

### R6: Epstein-Zin
- **Kernidee**: Trennung von Risikoaversion ($\alpha$) und EIS ($1/\rho$)
- Standard-CRRA erzwingt $\text{EIS} = 1/\gamma$; EZ erlaubt unabhängige Kalibrierung
- Unter Sicherheit reduziert sich EZ auf CRRA mit $\rho$ statt $\gamma$
- Relevanz: Löst Equity-Premium-Puzzle (hohe RA + hohe EIS gleichzeitig möglich)

## Validierungen (7/7 bestanden)

| Nr | Test | Ergebnis | Kriterium |
|----|------|----------|-----------|
| V1 | Axiom $u'>0, u''<0$ | ✅ PASS | Alle CRRA-Formen monoton + konkav |
| V2 | CRRA $\gamma \to 1 \to \ln(c)$ | ✅ PASS | max\|u-ln\| = 6.0e-4 |
| V3 | CRRA RRA = $\gamma$ | ✅ PASS | max\|RRA-$\gamma$\| = 8.9e-16 |
| V4 | CARA ARA = $\alpha$ | ✅ PASS | max\|ARA-$\alpha$\| = 8.9e-16 |
| V5 | Euler $r=\beta \to \dot{c}=0$ | ✅ PASS | max\|c(t)-c₀\| = 0 |
| V6 | Euler Monotonie | ✅ PASS | $r>\beta \to c\uparrow$, $r<\beta \to c\downarrow$ |
| V7 | Knick + Verlustaversion | ✅ PASS | Ratio = 2.250 (erwartet 2.25) |

## Dateien

| Datei | Beschreibung |
|-------|-------------|
| `S14_U1_Nutzenfunktion.py` | Python-Simulation (6 Regime, 7 Validierungen) |
| `S14_U1_Nutzenfunktion.png` | 21-Panel Plot mit Kausalitätsanalyse |
| `S14_U1_Nutzenfunktion.npz` | Numerische Daten (CRRA, CARA, Prospect, Euler, Habit) |
| `S14_U1.js` | Webapp-Konfiguration (interaktive Exploration) |

## Fazit

Die Nutzenordnung U.1 ist **forminvariant**: Alle qualitativen Ergebnisse (Monotonie, Konkavität, Euler-Dynamik) gelten unabhängig von der konkreten Funktionalform. Die **Kausalketten** zeigen:
1. **$\gamma$ als Schlüsselparameter**: Steuert sowohl Konsum ($\dot{c}/c$) als auch Portfolio ($w^*$) hyperbolisch
2. **Referenzabhängigkeit** (Prospect Theory): Verlustaversion $\lambda > 1$ erzeugt asymmetrische Reaktionen
3. **Habitformation** (VI.4): Hedonic Treadmill — steigende $c$ erzeugen nur temporär höheres Wohlbefinden
4. **Information-Preis-Kopplung** (U.3): $\mathcal{I} \to 0$ treibt effektive Preise → ∞ (Marktversagen)
5. **Bidirektionale Spiralen**: VI.2 macht $\gamma$ endogen, erzeugt stabilisierende/destabilisierende Zyklen
