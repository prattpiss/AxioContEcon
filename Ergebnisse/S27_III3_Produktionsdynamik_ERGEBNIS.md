# S27 — III.3 Produktionsdynamik (§6.5)

## Gleichung

$$\dot{q}_k = \lambda_q \cdot \frac{p_k - MC_k(q_k)}{p_k} \cdot q_k \;-\; \delta_q \cdot q_k$$

Gewinnmargengesteuerte Expansion mit physischer Abschreibung.  
Grenzkosten: $MC_k(q) = c_0 + c_1 \cdot q^{\alpha}$ (konvex, $MC' > 0$, $\alpha \geq 1$).  
Lerner-Index $(p-MC)/p$ steuert Produktionsanpassung.

## Ergebnisse

| Validierung | Ergebnis | Detail |
|---|---|---|
| V1: Konvergenz $q \to q^*$ (von unten + oben) | **PASS** | err\_below = 0.000000, err\_above = 0.000000 |
| V2: Axiom $p > MC \Rightarrow \dot{q} > 0$, $p < MC \Rightarrow \dot{q} < 0$ | **PASS** | $\dot{q}(p{=}20) = 1.860 > 0$, $\dot{q}(p{=}1) = -5.545 < 0$ |
| V3: GG-Bedingung $(p-MC)/p = \delta_q/\lambda_q$ | **PASS** | margin = 0.1000, target = 0.1000 |
| V4: Abschreibung $p < MC \Rightarrow q \to 0$ | **PASS** | $q(T) = 0.001 < 0.01$ |
| V5: Konvexität $\alpha \uparrow \Rightarrow q^* \downarrow$ | **PASS** | $q^* = [70.0, 17.0, 8.4, 4.1]$ (monoton fallend) |
| V6: $\lambda_q \uparrow \Rightarrow$ Konvergenzzeit $\downarrow$ | **PASS** | conv\_t = [50.0, 11.1, 5.3, 1.7] (monoton fallend) |
| V7: Effizienz $c_0 \downarrow \Rightarrow$ Marktanteil $\uparrow$ | **PASS** | shares = [0.44, 0.30, 0.26] |
| V8: Neoklassisch $\lambda_q \to \infty \Rightarrow$ sofortige Konvergenz | **PASS** | conv\_t($\lambda{=}50$) = 0.061 |

**Gesamtergebnis: 8/8 bestanden**

## Regime

| # | Regime | Kernergebnis |
|---|---|---|
| R1 | Einfache Konvergenz (fester Preis) | $q$: 5.0→17.0 (unten), 51.0→17.0 (oben); $q^* = 16.98$ |
| R2 | Multi-Gut (K=5, endogener Preis) | Alle Margen → GG = 0.10; $p_{\text{mean}}$: 12.2→5.5 |
| R3 | Boom & Crash (Preisschock) | $q$: 20→peak→14.2; $p$: 10→12.2→8.2 |
| R4 | Abschreibungs-Dominanz ($p < MC$) | $q$: 50→0.001 (exp. Zerfall, $t_{1/2} = 0.1$) |
| R5 | MC-Konvexität ($\alpha = 1, 1.5, 2, 3$) | $q^* = 70.0, 17.0, 8.4, 4.1$ (steiler MC = weniger Produktion) |
| R6 | Anpassungsgeschwindigkeit ($\lambda_q$-Sweep) | conv\_t: 50.0 ($\lambda{=}0.1$) → 1.7 ($\lambda{=}3.0$) |
| R7 | Oligopol (3 Firmen, heterogene Kosten) | Firma 0 (c₀=1.0): 43.9%, Firma 1 (c₀=2.5): 30.0%, Firma 2 (c₀=3.0): 26.1% |
| R8 | Neoklassischer Grenzfall ($\lambda \to \infty$) | conv\_t = 0.061 ($\lambda{=}50$) vs conv\_t > 5 ($\lambda{=}0.1$) |

## Sensitivitätsanalysen

| SA | Parameter | Ergebnis |
|---|---|---|
| SA1 | $\lambda_q$ vs $\delta_q$ → $q^*$(GG) | $q^*$-Range [0.0, 18.5] |
| SA2 | Preis $p$ vs $\alpha_{\text{MC}}$ → $q^*$ | $q^*$-Range [1.9, 205.0] |
| SA3 | $c_0$ (Fixkosten) vs $c_1$ (variable) → $q^*$ | $q^*$-Range [1.6, 89.7] |
| SA4 | Nachfrageelastizität $\epsilon$ vs $p_{\text{eq}}$ | $p_{\text{eq}}$-Range [3.0, 16.1] |
| SA5 | Anfangs-$q_0$ Sensitivität | Spread = 0.000000 (globale Stabilität) |

## Erweiterte Analysen

| EA | Analyse | Ergebnis |
|---|---|---|
| EA1 | Phasenporträt ($\dot{q}$ vs $q$) | Nullstellen bei $q = 3.7$ ($p{=}3$) bis $q = 29.5$ ($p{=}20$) |
| EA2 | Statisch vs Dynamisch | Wedge dyn/stat = 0.910 ($q^*_{\text{dyn}} < q^*_{\text{stat}}$ wegen $\delta > 0$) |
| EA3 | Stabilitätsanalyse (Eigenwert) | $f'(q^*) = -0.5250$; Range $[-5.93, -0.05]$; alle $< 0$ |
| EA4 | Natürliche Selektion (10 Firmen) | 10/10 überlebt; $q(T)$ korreliert negativ mit $c_0$ |

## Mathematische Strukturen

1. **Gradientendynamik**: $q^*$ ist GLOBAL stabiler Fixpunkt. Eigenwert $f'(q^*) = -\lambda_q \cdot MC'(q^*) \cdot q^*/p < 0$ stets negativ (da $MC' > 0$, $q^* > 0$, $p > 0$). Eindeutigkeit durch streng monoton steigenden Lerner-Index als Funktion von $q$.

2. **Gibrat-artiges Wachstum**: $\dot{q} \propto q$ transient — größere Firmen expandieren absolut schneller. Aber steigende MC begrenzen Wachstum → Gibrat gilt nur kurz, nicht im Gleichgewicht.

3. **Lerner-Index als Steuervariable**: $L = (p-MC)/p$. GG-Bedingung: $L^* = \delta/\lambda = 0.10$. $L > L^*$: Expansion; $L < L^*$: Kontraktion; $L < 0$: Verlust → Firmenausschied. Marktstruktur determiniert durch Kostenstruktur + Preisniveau.

4. **Separation Preis-/Mengendynamik**: III.3 bestimmt $q_k(t)$ bei gegebenem $p_k(t)$; II.2 bestimmt $p_k(t)$ bei gegebenem $q_k(t)$. Kopplung ergibt Tâtonnement-artigen Fixpunkt-Mechanismus.

5. **Natürliche Selektion**: Heterogene Kostenstrukturen → effizientere Firmen (niedriges $c_0$) expandieren auf Kosten ineffizienter. III.3 als Replikatordynamik der Firmengrößen — emergente Marktkonzentration ohne explizite Interaktion (Oligopol: Firma mit $c_0 = 1.0$ hält 43.9% Marktanteil).

## Zentrale Einsicht

III.3 beschreibt Produktion als gewinnmargengesteuerte Expansion mit Abschreibung — einfacher als Konsum (V.1-V.4) und Arbeit (L.1-L.4), weil primär von der Gewinnmarge $(p-MC)/p$ gesteuert. Der Lerner-Index fungiert als universelle Steuervariable: positiv = Expansion, negativ = Kontraktion. Das stationäre Gleichgewicht $MC(q^*) = p(1 - \delta/\lambda)$ ist global stabil (Eigenwert stets negativ bei konvexen Kosten). Die Simulation bestätigt: (1) Konvexe MC erzwingen endliche Produktion; (2) die Anpassungsgeschwindigkeit $\lambda_q$ steuert Konvergenzzeit monoton; (3) im Oligopol emergiert Marktkonzentration allein aus Kostenheterogenität; (4) der neoklassische Grenzfall ($\lambda \to \infty$) liefert sofortige Walrasianische Anpassung.
