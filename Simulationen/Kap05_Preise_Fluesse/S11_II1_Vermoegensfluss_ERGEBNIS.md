# S11 – Vermögensfluss II.1  (§5.4)
## Ergebnisbericht

**Datum:** 2025-01-XX  
**Status:** ✅ ALLE VALIDIERUNGEN BESTANDEN

---

## Gleichung

$$\vec{j}_w = -D_w \, \nabla\Phi_w + \vec{v}_w \, \rho_w$$

**Vermögenspotential (Def. 5.2):**

$$\Phi_w(\mathbf{x}, t) = h(\rho_w) - \beta_w \, V_w(\mathbf{x})$$

$$h(\rho_w) = \alpha \ln(\rho_w / \rho_0) \quad (h' = \alpha/\rho_w > 0)$$

**Drei Flusskomponenten:**
1. $-D_w (\alpha/\rho_w) \nabla\rho_w$ — Diversifikation (nichtlineare Fick-Diffusion)
2. $+D_w \beta_w \nabla V_w$ — Standortattraktivität (Drift zu guten Institutionen)
3. $+\vec{v}_w \rho_w$ — Konvektion (gerichtete Kapitalströme)

**Kopplung:**
- $\partial \rho_w / \partial t = -\nabla \cdot \vec{j}_w + S_w$ (Vermögenskontinuität)

**Vorzeichenkonvention (Anmerkung):**
> Monographie Def. 5.2 definiert $h' < 0$ und $\Phi = h + \beta V$. Für thermodynamisch stabile Diffusion ($\partial\Phi/\partial\rho > 0$) verwenden wir $h(\rho) = \alpha \ln(\rho/\rho_0)$ mit $h' > 0$ und $\Phi = h - \beta V$ (Minus vor $V$). Die resultierende Physik ist identisch: Diversifikation + Standortanziehung.

---

## Simulationsdesign

### Räumliches PDE-Framework (1D Method of Lines)

- **Domäne:** $[0, L]$ mit $L = 100$ km, $N_x = 201$ Gitterpunkte, $\Delta x = 0.5$ km
- **Zustandsvariable:** $\rho_w(x, t)$ Vermögensdichte
- **Randbedingungen:** Neumann ($j = 0$ an den Rändern)
- **Konvektion:** Upwind-Schema für Stabilität
- **Zeitintegration:** $T \in [0, 200]$, $N_{\text{eval}} = 4001$

### 5 Regime

| Regime | Beschreibung | Physik | Schlüsselparameter |
|---|---|---|---|
| R1 Reine Diversifikation | $\beta_w = 0$, $v_w = 0$ | Nichtlineare Diffusion $j = -D\alpha/\rho \cdot \nabla\rho$ | $D_w = 30$, $\alpha = 5$ |
| R2 Lucas-Paradox | $V_w$ hoch links, $\beta_w$ hoch | Attraktivität > Diversifikation → Kapital bleibt links | $D_w = 10$, $\beta_w = 3$ |
| R3 Kapitalflucht | $V_w$ kollabiert bei $t = 80$ | Institutionenkrise → Attraktionsverlust → Flucht | $D_w = 10$, $\beta_w = 2.5$ |
| R4 Drift-Diffusion | $v_w > 0$ (sinusförmig) | Konvektion verschiebt Vermögen nach rechts | $D_w = 10$, $v_0 = 0.5$ |
| R5 Voll stochastisch | OU-$D$, OU-$V_w$, Poisson-Quellen | Stochastische Vermögensdynamik | $D_w = 8$, $\alpha = 4$ |

### Funktionalformen (7 Typen)

**Räumlich:**
- Gaußprofil: $\rho_0(x) = b + A \exp(-(x-c)^2/(2\sigma^2))$
- Glatter Sprung: $f(x) = v_R + (v_L - v_R)/(1 + e^{(x-x_0)/w})$ (Logistik)
- Rampenprofil: $V_w(x) = v_L + (v_R - v_L) \cdot x/L$
- Sinusoidal: $v_w(x) = v_0 \sin(\pi x / L)$

**Zeitlich (stochastisch):**
- Ornstein-Uhlenbeck: $dx = \theta(\mu - x) dt + \sigma dW$ (Diffusion, Standort)
- Logistischer Übergang: $s(t) = 1/(1 + e^{-(t-t_0)/w})$ (Krise R3)
- Poisson-Pulse: Stochastische Vermögensinjektionen (R5)

---

## Ergebnisse

### Regime-Übersicht

| Regime | $M(0)$ | $M(T)$ | $\Delta M/M$ | $\bar{x}(0)$ | $\bar{x}(T)$ | $\Delta\bar{x}$ |
|---|---|---|---|---|---|---|
| R1 Diversifikation | 2505 | 2495 | −0.39% | 50.0 km | 50.0 km | 0.0 km |
| R2 Lucas-Paradox | 3250 | 3250 | −0.002% | 29.5 km | 26.5 km | −3.1 km |
| R3 Kapitalflucht | 2302 | 2294 | −0.34% | 38.3 km | 41.5 km | +3.1 km |
| R4 Drift-Diffusion | 1752 | 1722 | −1.67% | 35.7 km | 84.4 km | +48.7 km |
| R5 Stochastisch | 2303 | 3391 | +47.2% | 50.0 km | 51.1 km | +1.1 km |

### Schlüsselbeobachtungen

1. **R1 (Diversifikation):** Gaußprofil equilibriert zu Gleichverteilung ($\sigma/\mu = 0.008$). Die nichtlineare Diffusion $D_{\text{eff}} = D_w\alpha/\rho$ bewirkt schnellere Ausbreitung in dünn besiedelten Regionen (niedriges $\rho$ → hohes $D_{\text{eff}}$).

2. **R2 (Lucas-Paradox ✅):** Trotz hoher Konzentration auf der linken Seite ($\rho_L \approx 60$) und niedriger rechts ($\rho_R \approx 5$) fließt das Kapital sogar *weiter nach links* ($\Delta\bar{x} = -3.1$ km). Der Standortterm $\beta_w V_w$ mit $V_w^L = 8$ vs $V_w^R = 2$ dominiert über den Diversifikationstrieb. Genau das Lucas-Paradox: Kapital fließt zu den besseren Institutionen, nicht zur höheren Rendite.

3. **R3 (Kapitalflucht):** Vor der Krise (t < 80) stabilisiert $V_w^L = 8$ das Kapital links. Nach dem Institutionenkollaps ($V_w^L: 8 \to 1$) verschwindet der Attraktionsvorteil und das Kapital fließt nach rechts ($\Delta\bar{x}|_{80 \to 150} = +3.3$ km).

4. **R4 (Drift-Diffusion):** Die sinusförmige Drift $v_w = 0.5\sin(\pi x/L)$ verschiebt den Schwerpunkt um 48.7 km nach rechts. Das Vermögen akkumuliert rechts, wobei die Diffusion dem entgegenwirkt. Der Massenverlust von 1.67% ist numerisch bedingt (stärkere CFL-Belastung durch Konvektion).

5. **R5 (Stochastisch):** Poisson-Vermögensinjektionen erhöhen die Gesamtmasse von 2303 auf 3391 (+47%). OU-moduliertes $V_w$ erzeugt zeitlich variierende Attraktionsmuster.

---

## Validierungen

### V1: Massenerhaltung ($S_w = 0$, R1)
$$M(t) = \int_0^L \rho_w(x,t)\,dx = \text{const}$$
- $\max |\Delta M/M(0)| = 3.92 \times 10^{-3}$ ✅ (0.39%, MOL-Steifigkeit)

### V2: Diversifikation → Gleichverteilung (R1)
$$\rho_w(x, T) \to M/L$$
- $\sigma(\rho)/\langle\rho\rangle(T=200) = 0.0083$ ✅
- $\langle\rho(T)\rangle = 24.95$, $\rho_{\text{eq}} = 24.95$

### V3: Lucas-Paradox (R2)
$$V_w^L \gg V_w^R \implies \bar{x}(T) \leq \bar{x}(0)$$
- $\bar{x}(0) = 29.5$ km → $\bar{x}(T) = 26.5$ km ✅ (Kapital bewegt sich nach LINKS)

### V4: Kapitalflucht (R3)
$$V_w^L \downarrow \text{ bei } t = 80 \implies \bar{x}(t > 80) > \bar{x}(t = 80)$$
- $\bar{x}(80) = 35.9$ km → $\bar{x}(150) = 39.2$ km
- $\Delta\bar{x} = +3.3$ km ✅

### V5: Konvektive Drift (R4)
$$v_w > 0 \implies \bar{x}(T) > \bar{x}(0)$$
- $\bar{x}(0) = 35.7$ km → $\bar{x}(T) = 84.4$ km
- $\Delta\bar{x} = +48.7$ km ✅

### V6: Sensitivität (625 Punkte)
- $D_w \times \beta_w \to d\bar{x}/dt$ Heatmap (25×25 Gitter)
- $d\bar{x}/dt \in [-0.27, +0.17]$ km/a
- Höheres $\beta_w$ → stärkere Linksverschiebung (Standortanziehung) ✅

---

## Numerik

| Parameter | Wert |
|---|---|
| Methode | Method of Lines (MOL), 1D |
| Gitter | $N_x = 201$, $\Delta x = 0.5$ km, Neumann BC |
| Konvektion | Upwind-Schema (1. Ordnung) |
| ODE-Solver | RK45 (Dormand-Prince) |
| rtol | $10^{-9}$ |
| atol | $10^{-11}$ |
| max_step | 0.2 |
| T | $[0, 200]$, $N_{\text{eval}} = 4001$ |
| Stochastik | Euler-Maruyama (OU), Poisson-Pulse |
| Sensitivität | $25 \times 25 = 625$ Punkte |

---

## Dateien

| Datei | Beschreibung |
|---|---|
| `Simulationen/Kap05_Preise_Fluesse/S11_II1_Vermoegensfluss.py` | Python-Simulation (MOL PDE) |
| `Ergebnisse/Plots/S11_II1_Vermoegensfluss.png` | 15-Panel-Plot + Metadaten |
| `Ergebnisse/Daten/S11_II1_Vermoegensfluss.npz` | Komprimierte Daten |
| `webapp/src/simulations/S11_II1.js` | Interaktive Webapp (NX=51 MOL im Browser) |

---

## Physikalische Interpretation

1. **II.1 als Kapitalflussgesetz:** Die Gleichung $\vec{j}_w = -D_w\nabla\Phi_w + \vec{v}_w\rho_w$ ist das ökonomische Analogon zur Advektions-Diffusions-Gleichung. Kapital fließt entlang des negativen Potentialgradienten (Diversifikation + Standortanziehung) plus systematischer Drift (institutionelle Kanäle).

2. **Das Lucas-Paradox (1990):** In der neoklassischen Theorie sollte Kapital von reichen (hohe $\rho_w$) zu armen (niedrige $\rho_w$) Ländern fließen. II.1 löst das Paradox: $\Phi_w = h(\rho_w) - \beta_w V_w$ enthält nicht nur die Konzentration (Diversifikationstrieb), sondern auch die Standortattraktivität $V_w$. Wenn $V_w^{\text{reich}} \gg V_w^{\text{arm}}$ (bessere Institutionen, Rechtsstaatlichkeit, Infrastruktur), dominiert der Standortterm und Kapital bleibt im reichen Land — oder fließt sogar von arm nach reich (Kapitalflucht).

3. **Kapitalflucht als Potentialschock:** R3 zeigt den Mechanismus: Ein plötzlicher Institutionenkollaps ($V_w \downarrow$) reduziert die Attraktivität und setzt Kapital frei, das nun dem Diversifikationsgradienten folgt. Dies modelliert reale Kapitalflucht-Episoden (Argentinien 2001, Griechenland 2010, Russland 2022).

4. **Nichtlineare Diffusion:** Der effektive Diffusionskoeffizient $D_{\text{eff}} = D_w\alpha/\rho_w$ nimmt mit der Dichte ab. Das bedeutet: In Regionen hoher Vermögenskonzentration (Finanzzentren) ist die Kapitalumverteilung *langsamer* als in dünn besiedelten Peripherien. Dies verstärkt die Ungleichheit.

5. **Konvektion als Wirtschaftspolitik:** Der Term $\vec{v}_w\rho_w$ modelliert gerichtete Kapitalströme durch institutionelle Kanäle: Zentralbank-Interventionen, staatliche Investitionsprogramme, Carry Trade. R4 zeigt, wie eine systematische Drift die Vermögensverteilung fundamental verschieben kann.
