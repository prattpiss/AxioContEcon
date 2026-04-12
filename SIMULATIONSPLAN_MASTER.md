# Ökonoaxiomatik — Vollständiger Simulationsplan

> **Ziel:** Jede Gleichung, jede Kombination, jeden Sonderfall, jede Parameterwahl systematisch testen und validieren.  
> **Methode:** Chronologisch durch die Monographie, dann Kombinationen, dann Empirie.  
> **Regel:** Genau EINE Simulation pro Schritt. Absolute Korrektheit.

---

## Verzeichnisstruktur

```
AxioContEcon/
├── Info/                        ← Quelldokumente (Monographie, Gleichungen, Exploration)
├── Simulationen/
│   ├── Kap04_Erhaltung/         ← S01–S07: Erhaltungsgleichungen
│   ├── Kap05_Preise_Fluesse/    ← S08–S13: Preise und Flüsse
│   ├── Kap06_Entscheidungen/    ← S14–S38: Drei-Ebenen-Architektur
│   ├── Kap07_Information/       ← S39–S43: Informationsdynamik
│   ├── Kap08_Geld_Aggregation/  ← S44–S52: Geld, Kredit, Boltzmann
│   ├── Kap09_Population_Struktur/ ← S53–S61: Population, Ökologie
│   ├── Kap10_Spruenge_Regime/   ← S62–S71: Sprünge, Schwellenwerte
│   ├── Kap15_24_Spezialfaelle/  ← S72–S102: Klassische Modelle als Grenzfälle
│   ├── N_Neuartige_Systeme/     ← S103–S112: N1–N10
│   ├── Kombinationen/           ← S113+: Mehrachsen-Kopplungen
│   └── Validierung_Empirie/     ← V01+: Vergleich mit realen Daten
├── Ergebnisse/
│   ├── Zusammenfassungen/       ← Textberichte pro Simulation
│   ├── Plots/                   ← Alle Abbildungen
│   └── Daten/                   ← Numerische Ergebnisse (.npz, .csv)
└── SIMULATIONSPLAN_MASTER.md    ← Dieses Dokument
```

Jede Simulationsdatei: `S{NR}_{LABEL}_{Kurztitel}.py`  
Jeder Ergebnisbericht: `S{NR}_{LABEL}_ERGEBNIS.md`

---

## PHASE 1: Einzelgleichungen und Basis-Systeme (Kap. 4–10)

### Kap. 4 — Erhaltung (7 Gleichungen)

| Nr | ID | Gleichung(en) | Typ | Beschreibung | Status |
|----|----|--------------|-----|--------------|--------|
| S01 | I.1 | $\dot{w}_i = y_i - c_i + \sum_k \theta_{ik}\dot{p}_k + rb_i$ | ODE | Individuelle Vermögensbilanz: 3 Agentenklassen (W, U, B), Prüfung Nullsumme Bewertungsterme | ✅ |
| S02 | I.2 | $\dot{W} = Y - C$ | ODE | Aggregierte Vermögenserhaltung: Summation von S01, Prüfung $\sum\theta\dot{p}=0$, $\sum rb=0$ | ✅ |
| S03 | P.3 | $\dot{n}_k^{(\alpha)} = q_k - c_k - \delta_\alpha n_k - \nabla\cdot j + \text{Konversion}$ | PDE/ODE | Güterbestandsdynamik für alle 6 Klassen, Konversionsmatrix $\lambda_{\alpha\beta}$ | ✅ |
| S04 | I.4 | $\partial m/\partial t + \nabla\cdot j_m = g - \tau$ | PDE | Gelderhaltung: Kompaktform $\dot{M} = g_Z + g_B\cdot\text{Kredit} - \tau$ | ✅ |
| S05 | M.1 | $\Delta M^{\text{endo}} = m_{\text{mult}}\cdot\Delta B$ | Algebraisch | Geldschöpfung + Bilanzsymmetrie $\Delta M = \Delta L$ | ✅ (in S04) |
| S06 | M.2 | $\sum_i b_i = 0$ | Identität | Kreditmarkt-Clearing: Prüfung in S01+S04 | ✅ (in S04) |
| S07 | K.1 | $\dot{K}_k = I_k - \delta_k K_k$ | ODE | Kapitalakkumulation mit Konversion | ✅ |

**Sonderfälle Kap. 4:**
| Nr | Basiert auf | Sonderfall | Beschreibung |
|----|------------|------------|--------------|
| S01a | S01 | $\theta_{ik}=0, b_i=0$ | Reine Arbeiterhaushalte (kein Portfolio, keine Schulden) |
| S01b | S01 | $y_i=0$, nur Bewertung | Rentierszenario (nur Kapitalerträge) |
| S01c | S01 | NB.1: $c_i \geq c_i^{\min}$ | Subsistenz-Constraint aktiv |
| S01d | S01 | NB.2: Basel-Anforderung | Bankenszenario mit Eigenkapitalregel |
| S03a | S03 | $\alpha = \mathcal{K}_2$ (Land/Gold) | Reine Erhaltung ($q=0, d=0$, nur Handel) |
| S03b | S03 | Ohne Konversion ($\lambda_{\alpha\beta}=0$) | Isolierte Güterklassen |
| S07a | S07 | Solow-Spezialfall $I=sY$ | Exogene Sparquote |

### Kap. 5 — Preise und Flüsse (6 Gleichungen, Reihenfolge exakt nach Monographie §5.1–§5.6)

| Nr | ID | Gleichung(en) | Typ | Monographie § | Beschreibung | Status |
|----|----|--------------|-----|--------------|--------------|--------|
| S08 | II.2 | $\dot{p}_k = \lambda_k^{-1}(D_k-S_k) + \eta_k p_k - \varphi_k/(\mathcal{I}_k+\varepsilon)$ | ODE | §5.1 | Fundamentale Preisdynamik: 5 Regime (Normal/Blase/Krise/Stagflation/GG), Prop 5.1 bestätigt, V2 Blase ε=3.7e-15, V3 Walras ε=1.1e-11, 625-Pt Sensitivität, Metadaten-Panel | ✅ |
| S09 | F.2 | $\mu_k^{\text{eff}} = p_k + \alpha_H\bar{p}_k^{\text{Herding}} + \psi_k/(\mathcal{I}_k+\varepsilon)$ | Algebraisch | §5.2 | Effektives Potential: 3 Schichten (objektiv + Herding + Illiquidität), Prop. 5.2 | ✅ |
| S10 | F.1 | $\vec{j}_{n_k} = -D_k\,\nabla\mu_k^{\text{eff}}$ | PDE/Fluss | §5.3 | Allgemeiner Güterfluss (A4-Anwendung): Füllt $\nabla\cdot\vec{j}$ in P.3. Expandiert: $\vec{j} = -D_k[\nabla p_k + \alpha_H\nabla\bar{p}^H + \nabla(\psi/(\mathcal{I}+\varepsilon))]$ | ☐ |
| S11 | II.1 | $\vec{j}_w = -D_w\,\nabla\Phi_w + \vec{v}_w\,\rho_w$ | PDE/Fluss | §5.4 | Vermögensfluss: Diffusion auf $\Phi_w(h(\rho_w), V_w)$ + Konvektion. Lucas-Paradox | ☐ |
| S12 | II.4 | $\vec{j}_m = -D_m\,\nabla r + \sigma_m\,\vec{E}_{\text{Kredit}}$ | PDE/Fluss | §5.5 | Geldfluss: Zinsgradient + Kreditfeld. Füllt $\nabla\cdot\vec{j}_m$ in I.4. Zwei Regime (zins- vs. kreditgetrieben) | ☐ |
| S13 | II.3 | $\dot{\mathcal{I}}_k = D_\mathcal{I}\nabla^2\mathcal{I}_k - \omega\mathcal{I}_k + \mathcal{S}_k - \mu\mathcal{I}_k^3 + \beta|\dot{p}_k|$ | PDE | §5.6 | Informationsfluss: Diffusion + Zerfall + Quellen + Sättigung + Preis-Feedback. Vorschau Kap. 7 | ☐ |

**Sonderfälle Kap. 5:**
| Nr | Basiert auf | Sonderfall | Beschreibung |
|----|------------|------------|--------------|
| S08a | S08 | $\eta_k=0, \varphi_k=0$ | Reiner Walras-Tâtonnement |
| S08b | S08 | $\mathcal{I}\to\infty$ | EMH-Limit (keine Informationsfriktionen) |
| S08c | S08 | $D_k=S_k$ | Gleichgewichtsprüfung: $\dot{p}=\eta p$ (reine Inflationsdrift) |
| S10a | S10+F.2 | $\alpha_H=0, \psi=0$ | Neoklassischer Arbitragefluss (A4 pur) |
| S10b | S10+F.2 | Nur Herding ($\alpha_H\gg 1$) | Herdenfluss ohne Fundamentals |
| S10c | S10+P.3 | Gekoppelt: F.1 → $\nabla\cdot\vec{j}$ in P.3 | **Volle räumliche Gütererhaltung** (das fehlende ∇·j aus S03) |
| S12a | S12+I.4 | Gekoppelt: II.4 → $\nabla\cdot\vec{j}_m$ in I.4 | **Volle räumliche Gelderhaltung** (das fehlende ∇·j aus S04) |

### Kap. 6 — Entscheidungen (25 Gleichungen)

| Nr | ID | Gleichung(en) | Beschreibung | Status |
|----|----|--------------|--------------|--------|
| S14 | U.1 | $u_i = u(c_i, l_i; \gamma_i, c_i^*)$ | Nutzenfunktion: CRRA, CARA, Log, Epstein-Zin vergleichen | ☐ |
| S15 | U.2 | $\omega_{ik} = \omega(\mathcal{I}_{ik})$ | Aufmerksamkeitsgewichte: Softmax, Probit, Linear | ☐ |
| S16 | U.3 | $p_k^{\text{eff}} = p_k(1 + \psi_k/(\mathcal{I}_k+\varepsilon))$ | Effektiver Preis vs. Information | ☐ |
| S17 | V.1 | $\dot{c}_i = R_i \cdot c_i$, $R_i = (r-\beta_i)/\gamma_i$ | Euler-Gleichung (rationaler Konsum) | ☐ |
| S18 | V.1a | $r_i^{\text{wahr}} = r + \eta_i p - \varphi_i/(\mathcal{I}_i+\varepsilon)$ | Wahrgenommener Zins | ☐ |
| S19 | V.2 | $\Psi_c(c_i, c_i^*, \text{Gini}, \mathcal{I}_i)$ | Psychologische Konsumverzerrung: Prospect Theory | ☐ |
| S20 | V.3 | $\Phi_c(c_j - c_i, \mathcal{I}_j, \mathcal{I}_i, Z)$ | Soziale Konsumvergleiche | ☐ |
| S21 | V.1+V.2+V.3 | Drei-Ebenen-Konsumsystem komplett | Komposition aller drei Ebenen | ☐ |
| S22 | L.1 | $l_i^* = l(w_i^{\text{real}}, r_i, \gamma_i)$ | Rationales Arbeitsangebot | ☐ |
| S23 | L.1a | $w_i^{\text{wahr}} = w_i + \alpha_H\bar{w}^{\text{peer}} + \psi_w/(\mathcal{I}_i+\varepsilon)$ | Wahrgenommener Alternativlohn | ☐ |
| S24 | L.2+L.3 | $\Psi_l + \Phi_l$ | Psychologische + Soziale Arbeitskorrekturen | ☐ |
| S25 | L.4 | $l_i = l_i^* + \Psi_l + \Phi_l$ | Gesamtarbeitsangebot (3 Ebenen) | ☐ |
| S26 | L.5 | $\dot{n}_{\text{ent}} = f(E[R], \sigma_R, \mathcal{I})$ | Unternehmerrisiko und Gründungsrate | ☐ |
| S27 | III.2 | $\dot{\theta}_{ik} = \lambda_\theta\partial u/\partial\theta + \alpha_H\sum_j A_{ij}(\theta_j-\theta_i) + \sigma_\theta\xi$ | Portfolio mit Herding und Rauschen | ☐ |
| S28 | III.3 | $q_k = F_k(K,L,R,\mathcal{I})$; $\dot{q}_k$-Anpassung | Produktion: CD, CES, Leontief | ☐ |
| S29 | III.4 | $\dot{\hat{p}}_k = \alpha_t(\dot{p}_k-\dot{\hat{p}}_k) + \omega_a(p_k^A - \hat{p}_k)$ | Erwartungsbildung (4 Komponenten) | ☐ |
| S30 | VI.1 | $r = r^* + \phi_\pi(\pi-\pi^*) + \phi_y\hat{y}$ | Taylor-Regel Zinspolitik | ☐ |
| S31 | VI.2 | $\dot{\gamma}_i = \alpha_\gamma(\gamma^*-\gamma_i) + \beta_\gamma\cdot\text{Verlust}$ | Endogene Risikoaversion | ☐ |
| S32 | VI.3 | $\dot{\beta}_i = \alpha_\beta(\beta^*-\beta_i) + f(\text{Einkommen})$ | Endogene Zeitpräferenz | ☐ |
| S33 | VI.4 | $\dot{c}_i^* = \lambda_c(c_i - c_i^*)$ | Endogener Referenzpunkt (Habit) | ☐ |
| S34 | VI.5 | $\dot{\alpha}_{H,i} = g(\text{Marktphase}, \mathcal{I}_i)$ | Endogener Herding-Parameter | ☐ |
| S35 | VI.6 | $\dot{A} = \theta_A A - \delta_A A + s_A Y$ | Technologiedynamik (Romer-Typ) | ☐ |
| S36 | VI.7 | $\dot{\alpha}_{t,i} = h(\text{Prognoseerfolg})$ | Endogene Erwartungsadaptation | ☐ |
| S37 | VI.8 | $\dot{T}_i = k(\text{Erfahrung}, \text{Netzwerk})$ | Endogene Vertrauensanpassung | ☐ |
| S38 | VI.9 | $\dot{a}_{ik} = \lambda_a(\omega_{ik} - a_{ik})$ | Endogene Aufmerksamkeitsallokation | ☐ |

**Sonderfälle Kap. 6:**
| Nr | Basiert auf | Sonderfall |
|----|------------|------------|
| S17a | S17 | $r=\beta$ → $\dot{c}=0$ (Ramsey-Steady-State) |
| S17b | S17 | $\gamma\to 0$ → risikoneutral |
| S17c | S17 | $\gamma\to\infty$ → unendliche Risikoaversion |
| S21a | S21 | Nur V.1 (rational, kein Psycho/Sozial) |
| S21b | S21 | V.1+V.2 (rational + psychologisch, kein Netzwerk) |
| S27a | S27 | $\alpha_H=0, \sigma_\theta=0$ → reines CAPM-Portfolio |
| S27b | S27 | Nur Herding ($\lambda_\theta=0$) → reine Nachahmung |
| S28a | S28 | Cobb-Douglas: $q = AK^\alpha L^{1-\alpha}$ |
| S28b | S28 | CES: $q = A[\alpha K^\rho + (1-\alpha)L^\rho]^{1/\rho}$ |
| S28c | S28 | Leontief: $q = A\min(K/a, L/b)$ |
| S29a | S29 | Rationale Erwartungen: $\omega_f=1$, Rest $=0$ |
| S29b | S29 | Chartist: $\alpha_t\gg\omega_a, \omega_f$ |
| S29c | S29 | Perfekte Voraussicht: $\hat{p}=p$ |

### Kap. 7 — Information (5 Gleichungen)

| Nr | ID | Gleichung(en) | Beschreibung | Status |
|----|----|--------------|--------------|--------|
| S39 | I.1(Info) | $\dot{\mathcal{I}} = D_\mathcal{I}\nabla^2\mathcal{I} + \sigma_{\text{adv}}E + \mathcal{W}(\mathcal{I}) + \sigma_{\text{use}}c/n - \omega\mathcal{I}$ | Vollständige Informationsdynamik (PDE) | ☐ |
| S40 | I.2(Info) | $\partial\Pi/\partial a = p\cdot\partial D/\partial\mathcal{I}\cdot\partial\mathcal{I}/\partial a - 1 = 0$ | Optimale Werbung (Dorfman-Steiner) | ☐ |
| S41 | I.3(Info) | $\sum_k \mathcal{I}_{ik} \leq A_{\max}$ | Aufmerksamkeitsbeschränkung | ☐ |
| S42 | I.5(Info) | $\Pi^{\text{info}} = \Delta v_6 - C(\mathcal{I})$ | Netto-Informationsnutzen | ☐ |
| S43 | Ent.2 | $\dot{S}_{\text{irr}} = \sum_k \delta_k q_k \geq 0$ | Entropieproduktion | ☐ |

**Sonderfälle Kap. 7:**
| Nr | Basiert auf | Sonderfall |
|----|------------|------------|
| S39a | S39 | Ohne Diffusion ($D_\mathcal{I}=0$) → rein lokale Dynamik |
| S39b | S39 | Ohne WoM ($\mathcal{W}=0$) → lineare Dynamik |
| S39c | S39 | Ginzburg-Landau: $\mathcal{W}=a\mathcal{I}-b\mathcal{I}^3$ → Phasenübergang |
| S39d | S39 | 1D-Diffusion auf räumlichem Gitter |

### Kap. 8 — Geld und Aggregation (9 Gleichungen)

| Nr | ID | Gleichung(en) | Beschreibung | Status |
|----|----|--------------|--------------|--------|
| S44 | M.3 | $m_{\text{mult}} = 1/(1-(1-r_k)(1-c_B))$ | Geldmultiplikator: Sensitivität Reservequote, Bargeldhaltung | ☐ |
| S45 | M.4 | $\tau_\mathcal{G}$ | Steuertilgung als Geldvernichtung | ☐ |
| S46 | E.1 | $r_{\text{real}} = r_{\text{nom}} - \pi^e$ | Fisher-Arbitrage | ☐ |
| S47 | P.4 | $\Pi_k = (p_k - MC_k)q_k$ | Konversionsprofit | ☐ |
| S48 | V.9 | $Y = C + I + G + NX$ | BIP-Identität: Konsistenzprüfung | ☐ |
| S49 | IV.1 | $\partial_t f + \nabla\cdot(f\dot{x}) = C[f]$ | Boltzmann-Transportgleichung | ☐ |
| S50 | IV.2 | $\dot{\mu}_n = \langle x^n\rangle_f$ | Momentengleichungen (1., 2., 3. Moment) | ☐ |
| S51 | IV.3 | $N\to\infty: f\to\delta(x-\bar{x})$ | Mean-Field-Limit | ☐ |
| S52 | IV.4 | $d\text{Var}(w)/dt = 2\text{Cov}(w,\dot{w}) + \text{Var}(\dot{w})$ | Varianz-/Ungleichheitsdynamik | ☐ |

### Kap. 9 — Population und Struktur (9 Gleichungen)

| Nr | ID | Gleichung(en) | Beschreibung | Status |
|----|----|--------------|--------------|--------|
| S53 | N.1 | $\dot{N}_X = g_X N_X + M_X + C_X$ | Klassen-Populationsdynamik | ☐ |
| S54 | N.2 | $\dot{N} = \sum\dot{N}_X = gN+M$ | Gesamtpopulation | ☐ |
| S55 | N.3 | $K_{\text{trag}} = K_{\text{trag}}(R,A,\mathcal{Q})$ | Endogene Tragfähigkeit | ☐ |
| S56 | N.4 | $\dot{R} = r_R R(1-R/R_{\max}) - \varepsilon_R Y$ | Ressourcendynamik (logistisch + Extraktion) | ☐ |
| S57 | N.5 | $g_B = g_B(\text{Einkommen, Bildung, Mortalität})$ | Fertilitätsfunktion | ☐ |
| S58 | VII.1 | $\dot{\mathcal{T}} = \alpha_T(\bar{\mathcal{T}}-\mathcal{T}) - \beta_T\cdot\text{Krise} + \gamma_T\mathcal{Q}$ | Vertrauen/Sozialkapital | ☐ |
| S59 | VII.2 | $\dot{H} = s_H Y - \delta_H H + \theta_H\mathcal{I}$ | Humankapital | ☐ |
| S60 | VII.3 | $E = \varepsilon\cdot Y/A_E$ | Emissionen | ☐ |
| S61 | VII.4 | $\dot{Z} = r_Z Z(1-Z/Z_{\max}) - E$ | Ökologisches Kapital | ☐ |

### Kap. 10 — Sprünge und Regime (10 Gleichungen)

| Nr | ID | Gleichung(en) | Beschreibung | Status |
|----|----|--------------|--------------|--------|
| S62 | VIII.1 | $dp = \mu dt + \sigma dW + J dN_t$ | Jump-Diffusion | ☐ |
| S63 | VIII.2 | $\lambda_J = \lambda_0 + \alpha_J/(\mathcal{I}+\varepsilon) + \beta_J H_{\text{herd}}$ | Zustandsabhängige Sprungrate | ☐ |
| S64 | VIII.3 | $J \sim p(J|s)$ | Lévy-Sprungverteilung (regime-abhängig) | ☐ |
| S65 | VIII.4 | $q_{ij}(X) = q_{ij}^{(0)}\exp(\sum\beta_m X_m)$ | Regimewechsel-Übergangsraten | ☐ |
| S66 | VIII.5 | $\Theta^{(s)}$ | Regimespezifische Parameter | ☐ |
| S67 | VIII.6 | $w_i < w_{\min}$ → Bankrott | Bankrott-Mechanik + Restrukturierung | ☐ |
| S68 | VIII.7 | Schumpeter-Destruktion | Innovation ersetzt Firmen | ☐ |
| S69 | Schw.1 | $P(\text{flip})=\sigma(\sum A_{ij}s_j - \theta_i, \tau)$ | Schwellenwertfunktion (Kaskaden) | ☐ |
| S70 | Schw.2 | $\dot{\theta}_i = -\alpha_\theta(\theta_i-\bar{\theta}) + \beta_\theta\text{Stress}$ | Endogene Schwellen | ☐ |
| S71 | RS.1 | $q_{ij}(X)$ endogen | Endogener Regimeübergang | ☐ |

### Netzwerk (Kap. 3, 3 Gleichungen)

| Nr | ID | Gleichung(en) | Beschreibung | Status |
|----|----|--------------|--------------|--------|
| S71b | V.6 | $\mathcal{G} = (A^{(1)},\ldots,A^{(5)})$ | Multiplex-Netzwerk (5 Ebenen) | ☐ |
| S71c | V.7 | $A^{\text{eff}} = \sum\omega_\ell A^{(\ell)}$ | Effektive Adjazenz + Graph-Laplacian | ☐ |
| S71d | V.8 | $\dot{A}_{ij}^{(\ell)}$ | Linkdynamik | ☐ |

---

## PHASE 2: Klassische Modelle als Spezialfälle (Kap. 15–24)

| Nr | Modell | Kapitel | Gleichungen (aus System) | Vereinfachungen |
|----|--------|---------|--------------------------|-----------------|
| S72 | Solow (1956) | §15 | K.1 + III.3 + I.2 | 1 Gut, 1 Agent, $I=sY$, exogene Sparquote |
| S73 | Ramsey (1928) | §15 | K.1 + V.1 + III.3 | 1 Gut, 1 Agent, endogener Konsum |
| S74 | AK-Modell | §15 | K.1 + III.3 ($\alpha=1$) | Lineare Produktion |
| S75 | Solow+Technik | §15 | K.1 + III.3 + VI.6 | Endogener technischer Fortschritt |
| S76 | Arrow-Debreu | §16 | I.1, II.1, V.1, III.3 | $N$ Güter, perfekte Info, kein Herding |
| S77 | IS-LM (Hicks) | §17 | I.2, M.1, VI.1, V.1, K.1 | Geschlossene VW, feste Preise |
| S78 | AS-AD | §17 | IS-LM + II.2 | Phillips-Kurve + Preisanpassung |
| S79 | Mundell-Fleming | §19 | IS-LM + F.1 (Kapitalfluss) | Offene VW, Wechselkurs |
| S80 | CAPM (Sharpe) | §18 | III.2, V.1 | 1 Periode, Mean-Variance |
| S81 | Black-Scholes | §18 | VIII.1 ($J=0$) | GBM, risikoneutral |
| S82 | Minsky-Zyklus | §20 | M.1, I.1, II.2, VIII.4 | Kredit-Boom-Bust |
| S83 | Fisher-Spirale | §20 | I.1, II.2, M.1 | Schulden-Deflation |
| S84 | Piketty ($r>g$) | §21 | I.1, IV.4 | Vermögensungleichheit |
| S85 | Akerlof (Lemons) | §22 | I.1(Info), U.3, II.2 | Adverse Selection |
| S86 | Grossman-Stiglitz | §22 | I.1(Info), II.2, U.2 | Informationsparadoxon |
| S87 | Stigler (Suchtheorie) | §22 | I.5(Info), U.1, I.3(Info) | Optimale Suche |
| S88 | Prospect Theory | §23 | V.2, VI.4 | Psychologische Verzerrung |
| S89 | Granovetter (Schwellenwerte) | §23 | Schw.1, V.6 | Soziale Kaskaden |
| S90 | Quantitätstheorie | §24 | I.4, II.2 | $MV = PY$ |
| S91 | Tobin's q | §24 | K.1, II.1, III.3 | Investitionsentscheidung |
| S92 | Hotelling-Regel | §24 | N.4, II.1 | Erschöpfbare Ressourcen |
| S93 | Permanent Income | §24 | V.1, I.1 | Konsumglättung |
| S94 | Ricardianische Äquivalenz | §24 | I.1, I.4 | Staatsverschuldung neutral |
| S95 | Okun's Law | §24 | III.3, L.1, N.1 | Output-Gap vs. Arbeitslosigkeit |
| S96 | Phillips-Kurve | §24 | II.2, L.1 | Inflation vs. Arbeitslosigkeit |
| S97 | Taylor-Regel | §24 | VI.1 | Zinspolitik |
| S98 | Diamond-Dybvig | §24 | Schw.1, M.1 | Bank Runs |
| S99 | Spence-Signaling | §22 | I.1(Info), U.3 | Signaling-Gleichgewicht |
| S100 | Kaldor-Verteilung | §21 | I.1, I.2, IV.4 | Funktionale Einkommensverteilung |
| S101 | Harrod-Domar | §15 | K.1, III.3 (Leontief) | Feste Koeffizienten |
| S102 | Mundell-Tobin | §24 | E.1, K.1, I.4 | Inflation und Kapitalakkumulation |

---

## PHASE 3: Neuartige Systeme (N1–N10, Exploration)

| Nr | System | Gleichungen | Dimension | Kernresultat |
|----|--------|-------------|-----------|-------------|
| S103 | N1: Info-Preis | I.1(Info)+II.2 | 2×2 | Stabilitätsbedingung: $\omega_{\text{eff}} > \eta - \beta_S/\lambda$ |
| S104 | N2: Info-Ungleichheit | I.1(Info)+IV.4+I.1(Kap4) | 3×3 | Piketty-Verstärker $\alpha_r s_w/\omega_{\text{eff}}$ |
| S105 | N3: Habit-Konsum | VI.4+V.1+V.2 | 2×2 stückw. | Konsumfalle $\kappa_- > \lambda_c$ |
| S106 | N4: Vertrauens-Info | VII.1+I.1(Info) | 2×2 nichtlin. | Vertrauensfalle |
| S107 | N5: Öko-Ökonomie | VII.4+N.4+III.3+K.1 | 2×2 nichtlin. | Kipppunkt; $T\sim 50$–100 J |
| S108 | N6: Endo. Risikoaversion | VI.2+III.2+II.2 | 2×2 eff. | Panik-Multiplikator $M_{\text{Panik}}$ |
| S109 | N7: Kredit-Preis | M.1+II.2+K.1 | 2×2 | Minsky-Stabilität geschlossen |
| S110 | N8: Endo. Herding | III.4+VI.5+II.2 | Selbsterregung | $\alpha_H^{\max,\text{krit}}$ |
| S111 | N9: Info-Sprungrate | VIII.2+I.1(Info) | SDE | Dauerkrise-Schwelle $\lambda_I^{\text{krit}}$ |
| S112 | N10: Netzwerk-Kaskade | V.6+Schw.1+I.1(Info) | MF | $S_0^{\text{Kaskade}}$ |

---

## PHASE 4: Systematische Kombinationen

### 4a — Zweier-Kopplungen (kapitülbergreifend)

| Nr | Kopplung | Gleichungen | Beschreibung |
|----|----------|-------------|--------------|
| S113 | Erhaltung + Preis | I.1 + II.2 | Vermögen reagiert auf Preisdynamik |
| S114 | Preis + Konsum | II.2 + V.1 | Preis-Konsum-Rückkopplung |
| S115 | Konsum + Portfolio | V.1 + III.2 | Budget-Allokation Konsum vs. Investment |
| S116 | Portfolio + Erwartung | III.2 + III.4 | Portfolioanpassung an Erwartungen |
| S117 | Erwartung + Preis | III.4 + II.2 | Erwartungsgetriebene Preise |
| S118 | Info + Konsum | I.1(Info) + V.1 + U.2 | Information beeinflusst Konsum über Aufmerksamkeit |
| S119 | Info + Portfolio | I.1(Info) + III.2 | Informierte vs. uninformierte Portfolios |
| S120 | Kredit + Produktion | M.1 + III.3 + K.1 | Kreditfinanzierte Investition |
| S121 | Population + Kapital | N.1 + K.1 + III.3 | Demografische Dividende |
| S122 | Population + Ressourcen | N.1 + N.4 | Malthusianische Dynamik |
| S123 | Technologie + Ungleichheit | VI.6 + IV.4 | Skill-biased technical change |
| S124 | Herding + Kreditmarkt | V.3/Schw.1 + M.1 | Herding-getriebene Kreditblase |
| S125 | Vertrauen + Netzwerk | VII.1 + V.6 | Vertrauensbasierte Netzwerkbildung |
| S126 | Emissionen + Produktion | VII.3+VII.4 + III.3 | Umwelt-Produktions-Trade-off |
| S127 | Risikoaversion + Sprünge | VI.2 + VIII.1 | Verlustreaktionen auf Crashes |
| S128 | Schwellen + Netzwerk | Schw.1+Schw.2 + V.6 | Endogene Kaskadenschwellen |

### 4b — Dreier- und Mehrsysteme

| Nr | System | Gleichungen |
|----|--------|-------------|
| S129 | Preis-Info-Konsum | II.2 + I.1(Info) + V.1 |
| S130 | Kredit-Preis-Bankrott | M.1 + II.2 + VIII.6 |
| S131 | Solow + Information | K.1 + III.3 + I.1(Info) |
| S132 | Minsky + Netzwerk | M.1 + Schw.1 + V.6 + VIII.6 |
| S133 | Ramsey + Habit + Verlustaversion | V.1 + VI.4 + V.2 (= N3 erweitert) |
| S134 | Vollständiges Kap. 4 | I.1+I.2+P.3+I.4+M.1+M.2+K.1 |
| S135 | Vollständiges Kap. 6 | Alle V.*, L.*, III.*, VI.* |
| S136 | Krisenmodell (Kap. 10 komplett) | VIII.1–VIII.7 + Schw.1+Schw.2 + RS.1 |

### 4c — Exogenitätsvariationen

Für jede zentrale Gleichung testen wir verschiedene Wahlen der Exogenität:

| System | Endogen machen | Exogen halten | Erwartetes Verhalten |
|--------|---------------|---------------|---------------------|
| II.2 | $p, \mathcal{I}$ | $D, S, \eta$ | Standard-Preis |
| II.2 | $p, \mathcal{I}, D, S$ | $\eta$ | Voll-endogener Markt |
| V.1+V.2+V.3 | $c, c^*$ | $r, \text{Gini}, Z$ | Basis-Konsum |
| V.1+V.2+V.3 | $c, c^*, r, Z$ | $\text{Gini}$ | Konsum mit endogenem Regime |
| III.2 | $\theta, p$ | $\gamma, A_{ij}$ | Portfolio mit fester Risikoaversion |
| III.2 | $\theta, p, \gamma, A_{ij}$ | nichts | Vollkopplung |

---

## PHASE 5: Empirische Validierung

| Nr | Test | Datenquelle | Gleichungen | Methode |
|----|------|-------------|-------------|---------|
| V01 | Solow-Residuum | Penn World Tables | K.1+III.3 | Kalibrierung, $R^2$ |
| V02 | Gini-Zeitreihen | World Bank WDI | IV.4, N2 | Fit Ungleichheitsdynamik |
| V03 | Blasen-Crash-Muster | S&P 500, Nikkei | VIII.1, N6 | Verteilung der Renditen |
| V04 | Phillips-Kurve empirisch | FRED | II.2, L.1 | Panel-Regression |
| V05 | Fisher-Gleichung | FRED, ECB | E.1 | Zeitreihen-Kointegrationstest |
| V06 | Kreditzyklen | BIS-Daten | M.1, N7 | Zyklusidentifikation |
| V07 | Informationsdiffusion | Google Trends | I.1(Info) | Fit an Suchvolumen-Daten |
| V08 | Bankrun-Häufigkeit | IMF Financial Crises DB | Schw.1, N10 | Poisson-Regression |
| V09 | Demografischer Übergang | UN Population Division | N.1, N.5 | Cross-Country-Panel |
| V10 | Umwelt-Kuznets-Kurve | WDI Emissionsdaten | VII.3, VII.4 | Nichtlinearer Fit |

---

## Gesamtzählung

| Phase | Simulationen | Beschreibung |
|-------|-------------|--------------|
| Phase 1 | ~71 + ~30 Sonderfälle | Einzelgleichungen + Varianten |
| Phase 2 | ~31 | Klassische Spezialfälle |
| Phase 3 | 10 | Neuartige Systeme |
| Phase 4 | ~24 | Kombinationen + Exogenitätsvariationen |
| Phase 5 | ~10 | Empirische Validierung |
| **Gesamt** | **~176** | |

---

## Reihenfolge (strikt chronologisch)

**Wir beginnen mit S01 (Gleichung I.1) und arbeiten uns strikt durch.**

Nächster Schritt: **S01 — Individuelle Vermögensbilanz I.1**

---

*Erstellt: 2026-04-12 | Letzte Aktualisierung: 2026-04-12*
