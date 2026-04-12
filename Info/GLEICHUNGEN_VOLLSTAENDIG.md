# Vollständige Gleichungsreferenz — Ökonoaxiomatik

> **Quelle:** `Monographie_v2.md`, Anhang A + Kapitel 3–10  
> **Gesamtzahl:** 74 explizite Gleichungen (75 inkl. struktureller Duplikate)  
> **System:** 10 Axiome (A1–A10) → 7 Gleichungsgruppen + Netzwerk

---

## Variablenverzeichnis (Kernvariablen)

| Symbol | Bedeutung | Einheit/Typ |
|---|---|---|
| $w_i$ | Individuelles Vermögen von Agent $i$ | Geldeinheiten |
| $W$ | Aggregiertes Vermögen $\sum_i w_i$ | Geldeinheiten |
| $y_i$ | Einkommen von Agent $i$ | Geldeinheiten/Zeit |
| $c_i$ | Konsum von Agent $i$ | Geldeinheiten/Zeit |
| $Y, C$ | Aggregiertes Einkommen / Konsum | Geldeinheiten/Zeit |
| $p_k$ | Preis von Gut $k$ | Geldeinheiten/Mengeneinheit |
| $p_k^*$ | Gleichgewichtspreis (Grenzkosten) | Geldeinheiten/Mengeneinheit |
| $n_k^{(\alpha)}$ | Bestand von Gut $k$ in Klasse $\alpha$ | Mengeneinheit |
| $q_k$ | Produktion von Gut $k$ | Mengeneinheit/Zeit |
| $\theta_{ik}$ | Portfolioanteil Agent $i$ in Asset $k$ | Dimensionslos $\in [0,1]$ |
| $\hat{p}_{ik}$ | Erwarteter Preis von $k$ durch Agent $i$ | Geldeinheiten |
| $b_i$ | Netto-Finanzposition (Guthaben − Schulden) | Geldeinheiten |
| $r$ | Zinssatz | 1/Zeit |
| $T_i$ | Steuern für Agent $i$ | Geldeinheiten/Zeit |
| $M$ | Geldmenge | Geldeinheiten |
| $m$ | Gelddichtefeld | Geldeinheiten/Ort |
| $K_k$ | Kapitalbestand für Gut $k$ | Mengeneinheit |
| $I_k$ | Investition in Gut $k$ | Mengeneinheit/Zeit |
| $\delta_k$ | Abschreibungsrate für Gut $k$ | 1/Zeit |
| $\mathcal{I}_k$ | Informationsfeld für Gut $k$ | Dimensionslos |
| $D_{\mathcal{I}}$ | Informationsdiffusionskoeffizient | Fläche/Zeit |
| $\omega$ | Informationszerfallsrate | 1/Zeit |
| $\lambda_k$ | Markttiefe für Gut $k$ | Mengeneinheit·Zeit |
| $D_k, S_k$ | Nachfrage / Angebot für Gut $k$ | Mengeneinheit/Zeit |
| $\eta_k$ | Inflationserwartungsdrift | 1/Zeit |
| $\varphi_k$ | Informations-Preis-Kopplungskonstante | Geldeinheiten/Zeit |
| $\varepsilon$ | Regularisierungsparameter (verhindert Division durch 0) | Dimensionslos |
| $\alpha_H$ | Herding-Parameter | Dimensionslos |
| $\bar{p}^H$ | Peer-Durchschnittspreis | Geldeinheiten |
| $\psi$ | Intransparenz-Kosten | Geldeinheiten |
| $\mu^{\text{eff}}$ | Effektives chemisches Potential | Geldeinheiten |
| $\gamma_i$ | Risikoaversion von Agent $i$ | Dimensionslos |
| $\beta_i$ | Zeitpräferenzrate von Agent $i$ | 1/Zeit |
| $c_i^*$ | Referenzpunkt (Habit/Aspiration) | Geldeinheiten/Zeit |
| $\ell_i$ | Arbeitsangebot von Agent $i$ | Zeiteinheiten |
| $w_\ell$ | Lohnsatz | Geldeinheiten/Zeiteinheit |
| $A_{ij}^{(\ell)}$ | Adjazenzmatrix Ebene $\ell$ | $\in [0,1]$ |
| $A^{\text{eff}}$ | Effektive Adjazenzmatrix | $\in [0,1]$ |
| $N_X$ | Population der Klasse $X$ | Agenten |
| $N$ | Gesamtpopulation | Agenten |
| $R$ | Ressourcenbestand | Mengeneinheit |
| $\mathcal{T}$ | Vertrauen / Sozialkapital | Dimensionslos |
| $H$ | Humankapital | Dimensionslos |
| $E$ | Kumulierte Emissionen | Mengeneinheit |
| $\kappa_{\text{eco}}$ | Ökologische Kapazität | Dimensionslos |
| $\sigma$ | Volatilität | Dimensionslos |
| $\lambda_J$ | Sprungrate (Jump-Intensität) | 1/Zeit |
| $J$ | Sprunggröße | Dimensionslos |
| $Z(t)$ | Regimezustand $\in \{1,\dots,R\}$ | Ganzzahl |
| $f$ | Verteilungsfunktion (Boltzmann) | Dichte |

---

## A.1 — Erhaltungsgleichungen (Kapitel 4) — 7 Gleichungen

### I.1 — Individuelle Vermögensbilanz (§4.1)
**Axiom:** A1 — **Status:** Identität

$$\frac{dw_i}{dt} = y_i - c_i + \sum_{k \in \mathcal{K}} \theta_{ik}\,\dot{p}_k + r\,b_i$$

| Term | Bedeutung |
|---|---|
| $y_i$ | Einkommen (Arbeit, Profit, Zinsen, Transfers) |
| $c_i$ | Konsum |
| $\sum_k \theta_{ik}\dot{p}_k$ | Bewertungsgewinne/-verluste |
| $r\,b_i$ | Netto-Zinserträge |

**Spezialisierungen:**
- Arbeiter ($i \in \mathcal{W}$): $\dot{w}_i = w_\ell \ell_i - c_i + \sum_k \theta_{ik}\dot{p}_k + r b_i$, mit $b_i \geq 0$
- Unternehmer ($j \in \mathcal{U}$): $\dot{w}_j = (p_k q_{jk} - w_\ell L_j - r K_j) - c_j + \sum_k \theta_{jk}\dot{p}_k + r b_j$
- Banken ($b \in \mathcal{B}$): $\dot{w}_b = (r_L L_b - r_D D_b) - c_b^{\text{Betrieb}} + \sum_k \theta_{bk}\dot{p}_k$
- Staaten ($g \in \mathcal{G}$): $\dot{w}^{\mathcal{G}} = T - G - \text{Tr} - r_G B^{\mathcal{G}}$

**Nebenbedingungen:**
- NB.1: $c_i \geq c_i^{\min} > 0$ (Subsistenzkonsum)
- NB.2: $E_b \geq \alpha_{\text{Basel}} \cdot \text{RWA}_b$ (Eigenkapitalanforderung für Banken)

---

### I.2 — Aggregierte Vermögenserhaltung (§4.2)
**Axiom:** A1 (Summation) — **Status:** Abgeleitete Identität

$$\frac{dW}{dt} = Y - C$$

wobei $W = \sum_i w_i$, $Y = \sum_i y_i$, $C = \sum_i c_i$.

Folgt aus Summation von I.1: Die Bewertungsterme ($\sum_i \sum_k \theta_{ik}\dot{p}_k = 0$) und Zinsterme ($\sum_i r b_i = 0$) heben sich aggregiert auf.

---

### P.3 — Güterbestandsdynamik (§4.3)
**Axiom:** A2 + A9 + K.1 — **Status:** Identität mit Quellen/Senken

$$\frac{dn_k^{(\alpha)}}{dt} = \underbrace{q_k^{(\alpha)}}_{\text{Produktion}} - \underbrace{c_k^{(\alpha)}}_{\text{Konsum}} - \underbrace{\delta_\alpha n_k^{(\alpha)}}_{\text{Zerfall}} - \underbrace{\nabla \cdot \vec{j}_{n_k}^{(\alpha)}}_{\text{Handelsfluss}} - \underbrace{\sum_{\beta \neq \alpha} \lambda_{\alpha\beta} n_k^{(\alpha)}}_{\text{Konversion hinaus}} + \underbrace{\sum_{\beta \neq \alpha} \lambda_{\beta\alpha} n_k^{(\beta)}}_{\text{Konversion hinein}}$$

6 Güterklassen $\alpha \in \{\mathcal{K}_1,\dots,\mathcal{K}_6\}$: Maschinen, Land/Gold, Nahrung, Patente, Geld, Information.

---

### I.4 — Gelderhaltung (§4.4)
**Axiom:** A3 — **Status:** Identität

$$\frac{\partial m}{\partial t} + \nabla \cdot \vec{j}_m = g - \tau$$

Kompaktform: $\dot{M} = g_Z + g_B \cdot \text{Kredit} - \tau_{\mathcal{G}}$

| Term | Bedeutung |
|---|---|
| $g_Z$ | Zentralbank-Basisgeldschöpfung |
| $g_B \cdot \text{Kredit}$ | Geschäftsbanken-Kreditschöpfung |
| $\tau_{\mathcal{G}}$ | Geldvernichtung durch Schuldentilgung |

---

### M.1 — Geldschöpfung (§8.1)
**Status:** Institutionelle Aufschlüsselung von I.4

$$\Delta M^{\text{endo}} = m_{\text{mult}} \cdot \Delta B$$

wobei $m_{\text{mult}}$ der Geldmultiplikator und $\Delta B$ die Netto-Kreditausweitung.

**Bilanzsymmetrie:** $\Delta M = \Delta L$ — Geldschöpfung = Schuldenaufbau (einzige perfekt symmetrische Transaktion im System).

---

### M.2 — Kreditmarkt-Clearing (§4.3)
**Status:** Identität (Netto-Null)

$$\sum_{i \in \mathcal{A}} b_i = 0$$

Das Guthaben des einen ist die Schuld des anderen.

---

### K.1 — Kapitalakkumulation (§3.2 / §4.5)
**Status:** Identität

$$\dot{K}_k = I_k - \delta_k K_k$$

Allgemeine Güterkonversion:
$$\frac{dn_k^{(\alpha)}}{dt} = \text{[intrinsische Dynamik]} - \sum_{\beta \neq \alpha} \lambda_{\alpha\beta} n_k^{(\alpha)} + \sum_{\beta \neq \alpha} \lambda_{\beta\alpha} n_k^{(\beta)}$$

wobei $\lambda_{\alpha\beta} \geq 0$ die Konversionsrate von Klasse $\alpha$ nach $\beta$.

---

## A.2 — Preise und Flüsse (Kapitel 5) — 6 Gleichungen

### II.1 — Langfristiger Preisanker (§5.1)

$$p_k^* = MC_k(q_k^*, w, r)$$

Gleichgewichtspreis = Grenzkosten der kostenminimalen Produktion.

---

### II.2 — Preisdynamik (§5.2)

$$\dot{p}_k = \lambda_k^{-1}(D_k - S_k) + \eta_k p_k - \frac{\varphi_k}{\mathcal{I}_k + \varepsilon}$$

| Term | Bedeutung |
|---|---|
| $\lambda_k^{-1}(D_k - S_k)$ | Überschussnachfrage / Markttiefe |
| $\eta_k p_k$ | Inflationserwartungsdrift (Momentum) |
| $-\varphi_k/(\mathcal{I}_k + \varepsilon)$ | Informationsreibung (bei niedriger Info: hohe Volatilität) |

---

### II.3 — Informationsfluss (§5.3, Kurzform)

$$\dot{\mathcal{I}}_k = D_{\mathcal{I}}\nabla^2\mathcal{I}_k - \omega\mathcal{I}_k + S_k$$

Kurzform; vollständig in I.1 (Info, Kap. 7).

---

### II.4 — Relative Preise (§5.4)

$$\dot{p}_{k/j} = \left(\frac{\dot{p}_k}{p_k} - \frac{\dot{p}_j}{p_j}\right) \cdot p_{k/j}$$

Dynamik des Preisverhältnisses zweier Güter.

---

### F.1 — Güterfluss (§5.5)

$$j_{n,k} = -D_k \nabla \mu_k^{\text{eff}}$$

Güter fließen entlang des Gradienten des effektiven Potentials (Axiom A4).

---

### F.2 — Effektives Potential (§5.6)

$$\mu^{\text{eff}} = p + \alpha_H \bar{p}^H + \frac{\psi}{\mathcal{I} + \varepsilon}$$

| Term | Bedeutung |
|---|---|
| $p$ | Nominaler Preis |
| $\alpha_H \bar{p}^H$ | Herding-Einfluss (Peer-Durchschnittspreis) |
| $\psi/(\mathcal{I} + \varepsilon)$ | Intransparenz-Kosten (steigen bei geringer Information) |

---

## A.3 — Entscheidungen (Kapitel 6) — 25 Gleichungen

### Nutzenarchitektur

#### U.1 — Nutzenordnung (§6.1)

$$u_i = u(c_i, l_i;\, \gamma_i, c_i^*)$$

mit $u' > 0$, $u'' < 0$ (monoton steigend, konkav). CRRA-Form: $u(c) = \frac{(c - c^*)^{1-\gamma}}{1-\gamma}$.

---

#### U.2 — Aufmerksamkeitsgewicht (§6.2)

$$\omega_{ik} = \omega(\mathcal{I}_{ik}), \quad \sum_k \omega_{ik} = 1, \quad \frac{\partial\omega}{\partial\mathcal{I}} > 0$$

Aufmerksamkeit für Gut $k$ steigt mit Informationsstand.

---

#### U.3 — Effektiver Preis (§6.2)

$$p_k^{\text{eff}} = p_k\left(1 + \frac{\psi_k}{\mathcal{I}_k + \varepsilon}\right)$$

Der wahrgenommene Preis enthält Intransparenz-Aufschlag.

---

### Konsumdynamik (3 Ebenen)

#### V.1 — Konsum (Ebene 1: Rational) (§6.3)

$$\dot{c}_i = R_i \cdot c_i$$

Euler-Gleichung: $R_i = \frac{1}{\gamma_i}(r - \beta_i)$ (Differenz zwischen Zins und Zeitpräferenz, skaliert mit Risikoaversion).

---

#### V.1a — Wahrgenommener Zins (§6.3)

$$r_i^{\text{wahr}} = r + \eta_i p - \frac{\varphi_i}{\mathcal{I}_i + \varepsilon}$$

Der Zins, den Agent $i$ effektiv wahrnimmt: Nominalzins + Inflationserwartung − Informationsreibung.

---

#### V.2 — Konsum (Ebene 2: Psychologisch) (§6.3)

$$\Psi_c(c_i, c_i^*, \text{Gini}, \mathcal{I}_i)$$

Prospect-Theory-Korrekturen: Verlustaversion um Referenzpunkt $c_i^*$, Ungleichheitsaversion, Informationseffekte.

---

#### V.3 — Konsum (Ebene 3: Sozial) (§6.3)

$$\Phi_c(c_j - c_i, \mathcal{I}_j, \mathcal{I}_i, Z)$$

Soziale Vergleiche: Herding (Peer-Mittelwert), regimeabhängige Stärke, Netzwerkeffekte.

---

### Arbeitsdynamik (6 Gleichungen)

#### L.1 — Arbeit (Ebene 1: Rational) (§6.4)

$$l_i^* = l(w_i^{\text{real}}, r_i, \gamma_i)$$

Optimales Arbeitsangebot bei nutzenmaximaler Trade-off Konsum vs. Freizeit.

---

#### L.1a — Wahrgenommener Alternativlohn (§6.4)

$$w_i^{\text{wahr}} = w_i + \alpha_H \bar{w}^{\text{peer}} + \frac{\psi_w}{\mathcal{I}_i + \varepsilon}$$

Enthält Peer-Einfluss und Intransparenz-Aufschlag.

---

#### L.2 — Arbeit (Ebene 2: Psychologisch) (§6.4)
$\Psi_l(\cdot)$ — Psychologische Korrekturen zur Arbeitsangebotsentscheidung.

---

#### L.3 — Arbeit (Ebene 3: Sozial) (§6.4)
$\Phi_l(\cdot)$ — Soziale Korrekturen (Peer-Arbeitszeiten, soziale Normen).

---

#### L.4 — Arbeit (Integral) (§6.4)

$$l_i = l_i^* + \Psi_l + \Phi_l$$

Gesamtarbeitsangebot = rational + psychologisch + sozial.

---

#### L.5 — Unternehmerrisiko (§6.8)

$$\dot{n}_{\text{ent}} = f(E[R], \sigma_R, \mathcal{I})$$

Gründungsrate als Funktion erwarteter Rendite, Risiko und Information.

---

### Kernentscheidungen

#### III.2 — Portfolioentscheidung (§6.6)

$$\dot{\theta}_{ik} = \lambda_\theta \frac{\partial u}{\partial\theta_{ik}} + \alpha_H \sum_j A_{ij}(\theta_{jk} - \theta_{ik}) + \sigma_\theta\,\xi_i$$

| Term | Bedeutung |
|---|---|
| $\lambda_\theta \partial u / \partial\theta_{ik}$ | Nutzenmaximierende Portfolioanpassung |
| $\alpha_H \sum_j A_{ij}(\theta_{jk} - \theta_{ik})$ | Herding (Netzwerk-Laplacian) |
| $\sigma_\theta \xi_i$ | Stochastische Exploration |

---

#### III.3 — Produktion (§6.5)

$$q_k = F_k(K_k, L_k, R_k, \mathcal{I}_k), \quad F_K > 0,\; F_{KK} < 0$$

Neoklassische Produktionsfunktion mit abnehmenden Grenzerträgen. Dynamische Anpassung:
$$\dot{q}_k = \lambda_q \frac{p_k - MC_k(q_k)}{p_k} q_k - \delta_q q_k$$

---

#### III.4 — Erwartungsbildung (§6.7)

$$\dot{\hat{p}}_k = \alpha_t(\dot{p}_k - \dot{\hat{p}}_k) + \omega_a(p_k^A - \hat{p}_k)$$

| Term | Bedeutung |
|---|---|
| $\alpha_t(\dot{p}_k - \dot{\hat{p}}_k)$ | Adaptives Lernen an reale Preisdynamik |
| $\omega_a(p_k^A - \hat{p}_k)$ | Ankereffekt (Anziehung zum Fundamentalwert $p_k^A$) |

---

### Endogene Verhaltensparameter (VI.1–VI.9) (§6.9)

#### VI.1 — Zinspolitik (Taylor-Regel)

$$r = r^* + \phi_\pi(\pi - \pi^*) + \phi_y\hat{y}$$

mit Taylor-Prinzip $\phi_\pi > 1$.

---

#### VI.2 — Endogene Risikoaversion

$$\dot{\gamma}_i = \alpha_\gamma(\gamma^* - \gamma_i) + \beta_\gamma \cdot \text{Verlust}_i$$

Mean-Reversion + Steigerung durch Verluste.

---

#### VI.3 — Endogene Zeitpräferenz

$$\dot{\beta}_i = \alpha_\beta(\beta^* - \beta_i) + f(\text{Einkommen}_i)$$

---

#### VI.4 — Endogener Referenzpunkt (Habit)

$$\dot{c}_i^* = \lambda_c(c_i - c_i^*)$$

Referenzpunkt passt sich langsam an den aktuellen Konsum an.

---

#### VI.5 — Endogener Herding-Parameter

$$\dot{\alpha}_{H,i} = g(\text{Marktphase}, \mathcal{I}_i)$$

Herding steigt in Blasen und Krisen; sinkt in ruhigen Phasen.

---

#### VI.6 — Technologiedynamik

$$\dot{A} = \theta_A A - \delta_A A + s_A Y$$

Technologie wächst endogen (Romer-Typ), zerfällt und wird durch F&E-Ausgaben getrieben.

---

#### VI.7 — Endogene Erwartungsadaptation

$$\dot{\alpha}_{t,i} = h(\text{Prognoseerfolg}_i)$$

Gute Prognosen → langsame Adaptation; schlechte → schnelle Korrektur.

---

#### VI.8 — Endogene Vertrauensanpassung

$$\dot{T}_i = k(\text{Erfahrung}_i, \text{Netzwerk}_i)$$

---

#### VI.9 — Endogene Aufmerksamkeitsallokation

$$\dot{a}_{ik} = \lambda_a(\omega_{ik} - a_{ik})$$

Aufmerksamkeit konvergiert langsam zum Informations-Gewicht.

---

## A.4 — Information (Kapitel 7) — 5 Gleichungen

### I.1 (Info) — Informationsdynamik (§7.1)

$$\dot{\mathcal{I}}_k = D_{\mathcal{I}}\nabla^2\mathcal{I}_k + \sigma_{\text{adv}}E_{\text{adv},k} + \mathcal{W}(\mathcal{I}_k) + \sigma_{\text{use}}\frac{c_k}{n_k} - \omega\mathcal{I}_k$$

| Term | Bedeutung |
|---|---|
| $D_{\mathcal{I}}\nabla^2\mathcal{I}_k$ | Räumliche Diffusion (Information breitet sich aus) |
| $\sigma_{\text{adv}}E_{\text{adv},k}$ | Werbung erzeugt Information |
| $\mathcal{W}(\mathcal{I}_k)$ | Nichtlinearer Selbstverstärkungsterm (Ginzburg-Landau: $a\mathcal{I} - b\mathcal{I}^3$) |
| $\sigma_{\text{use}}c_k/n_k$ | Nutzungsintensität erzeugt Information |
| $-\omega\mathcal{I}_k$ | Vergessen / Informationszerfall |

**Hinweis:** Label "I" kollidiert mit Erhaltung (Kap. 4). Kontextunterscheidung: Erhaltung betrifft $w, W, M$; Information betrifft $\mathcal{I}$.

---

### I.2 (Info) — Optimale Werbung / Dorfman-Steiner (§7.2)

$$\frac{\partial\Pi}{\partial a} = p \cdot \frac{\partial D}{\partial\mathcal{I}} \cdot \frac{\partial\mathcal{I}}{\partial a} - 1 = 0$$

Optimaler Werbeeinsatz: Grenzerlös der Werbung = Grenzkosten.

---

### I.3 (Info) — Aufmerksamkeitsbeschränkung (§7.3)

$$\sum_k \mathcal{I}_{ik} \leq A_{\max}$$

Begrenzte kognitive Ressourcen: Gesamtaufmerksamkeit ist limitiert.

---

### I.5 (Info) — Informationsnutzen (§7.4)

$$\Pi^{\text{info}} = \Delta v_6 - C(\mathcal{I})$$

Netto-Nutzen der Information = Entscheidungsverbesserung − Suchkosten.

---

### Ent.2 — Entropieproduktion (§7.5)

$$\dot{S}_{\text{irr}} = \sum_k \delta_k q_k \geq 0$$

Irreversible Entropieproduktion durch ökonomische Prozesse (Zweiter Hauptsatz-Analogon).

---

## A.5 — Geld und Aggregation (Kapitel 8) — 9 Gleichungen

### M.3 — Geldmultiplikator (§8.1)

$$m_{\text{mult}} = \frac{1}{1 - (1 - r_k)(1 - c_B)}$$

wobei $r_k$ = Reservekoeffizient, $c_B$ = Bargeldhaltungsquote.

---

### M.4 — Steuertilgung (§8.1)

$\tau_{\mathcal{G}}$: Nur Schuldentilgung vernichtet Geld (Steuereinnahmen für laufende Ausgaben sind neutral).

---

### E.1 — Fisher-Arbitrage (§8.2)

$$r_{\text{real}} = r_{\text{nom}} - \pi^e$$

Realzins = Nominalzins − erwartete Inflationsrate.

---

### P.4 — Konversionsprofit (§8.3)

$$\Pi_k = (p_k - MC_k)\,q_k$$

Bruttoprofit = (Preis − Grenzkosten) × Menge.

---

### V.9 — BIP-Identität (§8.4)

$$Y = C + I + G + NX$$

Standard makroökonomische Verwendungsgleichung.

---

### IV.1 — Boltzmann-Transportgleichung (§8.5)

$$\partial_t f + \nabla \cdot (f\,\dot{x}) = C[f]$$

Mesoskopische Beschreibung: Zeitentwicklung der Agenten-Verteilungsfunktion $f(x,t)$ mit Kollisionsterm $C[f]$.

---

### IV.2 — Momentengleichungen (§8.5)

$$\dot{\mu}_n = \langle x^n \rangle_f$$

$n$-te Momente der Verteilung: Mittelwert ($n=1$), Varianz ($n=2$), Schiefe ($n=3$).

---

### IV.3 — Mean-Field-Limit (§8.5)

$$N \to \infty: \quad f \to \delta(x - \bar{x})$$

Im Limes unendlich vieler Agenten kollabiert die Verteilung auf den Mittelwert (repräsentativer Agent).

---

### IV.4 — Varianz-/Ungleichheitsdynamik (§8.5)

$$\frac{d\text{Var}(w)}{dt} = 2\,\text{Cov}(w, \dot{w}) + \text{Var}(\dot{w})$$

Ungleichheit wächst, wenn Reichtum korreliert mit Vermögenswachstum ($\text{Cov}(w,\dot{w}) > 0$).

---

## A.6 — Population und Struktur (Kapitel 9) — 9 Gleichungen

### N.1 — Klassen-Populationsdynamik (§9.1)

$$\dot{N}_X = g_X N_X + M_X + C_X$$

| Term | Bedeutung |
|---|---|
| $g_X N_X$ | Natürliches Wachstum (Geburten − Todesfälle) |
| $M_X$ | Migration (Zuwanderung − Abwanderung) |
| $C_X$ | Klassenwechsel (Aufstieg/Abstieg) |

Klassen: $X \in \{\mathcal{W}, \mathcal{U}, \mathcal{B}, \mathcal{G}, \mathcal{Z}\}$

---

### N.2 — Gesamtpopulation (§9.1)

$$\dot{N} = \sum_X \dot{N}_X = gN + M$$

---

### N.3 — Endogene Tragfähigkeit (§9.2)

$$K_{\text{trag}} = K_{\text{trag}}(R, A, \mathcal{Q})$$

Tragfähigkeit hängt von Ressourcen $R$, Technologie $A$ und institutioneller Qualität $\mathcal{Q}$ ab.

---

### N.4 — Ressourcendynamik (§9.2)

$$\dot{R} = r_R\,R\left(1 - \frac{R}{R_{\max}}\right) - \varepsilon_R\,Y$$

Logistisches Wachstum − ökonomische Extraktion. Übernutzung wenn $\varepsilon_R Y > r_R R(1 - R/R_{\max})$.

---

### N.5 — Fertilitätsfunktion (§9.1)

$$g_B = g_B(\text{Einkommen}, \text{Bildung}, \text{Mortalität})$$

Demographischer Übergang: Fertilität sinkt mit Einkommen und Bildung.

---

### VII.1 — Vertrauen / Sozialkapital (§9.3)

$$\dot{\mathcal{T}} = \alpha_T(\bar{\mathcal{T}} - \mathcal{T}) - \beta_T \cdot \text{Krise} + \gamma_T \cdot \mathcal{Q}$$

Mean-Reversion + Zerstörung durch Krisen + Aufbau durch institutionelle Qualität.

---

### VII.2 — Humankapital (§9.3)

$$\dot{H} = s_H\,Y - \delta_H\,H + \theta_H\,\mathcal{I}$$

| Term | Bedeutung |
|---|---|
| $s_H Y$ | Bildungsinvestitionen (Anteil des BIP) |
| $-\delta_H H$ | Zerfall (Vergessen, Veraltung) |
| $\theta_H \mathcal{I}$ | Spillovers aus dem Informationsfeld |

---

### VII.3 — Emissionen (§9.3)

$$E = \varepsilon \cdot \frac{Y}{A_E}$$

Emissionsintensität sinkt mit Umwelttechnologie $A_E$.

---

### VII.4 — Ökologisches Kapital (§9.3)

$$\dot{Z} = r_Z\,Z\left(1 - \frac{Z}{Z_{\max}}\right) - E$$

Logistische Regeneration − Emissionsbelastung. Ökologischer Kollaps wenn $E > r_Z Z(1 - Z/Z_{\max})$.

---

## A.7 — Sprünge und Regime (Kapitel 10) — 10 Gleichungen

### VIII.1 — Jump-Diffusion (§10.1)

$$dp = \mu\,dt + \sigma\,dW + J\,dN_t$$

Preisdynamik mit deterministischem Trend ($\mu$), Brownschem Rauschen ($\sigma\,dW$) und Poisson-Sprüngen ($J\,dN_t$).

---

### VIII.2 — Zustandsabhängige Sprungrate (§10.2)

$$\lambda_J = \lambda_0 + \frac{\alpha_J}{\mathcal{I} + \varepsilon} + \beta_J H_{\text{herd}}$$

| Term | Bedeutung |
|---|---|
| $\lambda_0$ | Basis-Sprungrate |
| $\alpha_J / (\mathcal{I} + \varepsilon)$ | Informationsmangel erhöht Sprungrisiko |
| $\beta_J H_{\text{herd}}$ | Herding-Intensität erhöht Sprungrisiko |

---

### VIII.3 — Lévy-Sprungverteilung (§10.1)

$$J \sim p(J \mid s)$$

Regimeabhängige Sprunggrößenverteilung. In Krisen: fat-tailed; in Normalphasen: schmaler.

---

### VIII.4 — Regimewechsel (§10.2)

$$q_{ij}(X) = q_{ij}^{(0)} \exp\!\left(\sum_m \beta_m^{(ij)} X_m\right)$$

Übergangsraten zwischen Regimes als exponentiell-lineare Funktion des Systemzustands $X$.

---

### VIII.5 — Regimespezifische Parameter (§10.2)

$$\Theta^{(s)} = \left(\gamma^{(s)}, \alpha_H^{(s)}, \sigma^{(s)}, \dots\right)$$

In jedem Regime $s$ gelten andere Verhaltensparameter.

---

### VIII.6 — Bankrott (§10.3)

$$w_i < w_{\min} \;\Rightarrow\; \text{Austritt} + \text{Restrukturierung}$$

Agenten mit Vermögen unter Mindestgrenze: Exit + ggf. Neugründung.

---

### VIII.7 — Innovation / Schumpeter-Destruktion (§10.3)

Neue Firma ersetzt alte — kreative Zerstörung.

---

### Schw.1 — Schwellenwertfunktion (§10.4)

$$P(\text{flip}_i) = \sigma\!\left(\sum_j A_{ij} s_j - \theta_i,\; \tau\right)$$

Wahrscheinlichkeit eines diskreten Zustandswechsels (Bankrun-Auslösung, Kauf-/Verkauf-Entscheidung). Sigmoidale Funktion des Netzwerk-Einflusses minus individuelle Schwelle.

---

### Schw.2 — Endogene Schwellen (§10.5)

$$\dot{\theta}_i = -\alpha_\theta(\theta_i - \bar{\theta}) + \beta_\theta(\text{Stress})$$

Schwellen sinken unter Stress (leichtere Auslösung) und kehren in Ruhephasen zum Mittelwert zurück.

---

### RS.1 — Endogener Regimeübergang (§10.6)

$$q_{ij}(X) = q_{ij}^{(0)} \exp\!\left(\sum_m \beta_m^{(ij)} X_m\right)$$

**Hinweis:** Strukturell identisch mit VIII.4. RS.1 betont die Endogenität (Zustandsvektor $X$ bestimmt Übergangsraten).

---

## Netzwerk-Gleichungen (Kapitel 3) — 3 Gleichungen

### V.6 — Multiplex-Netzwerk (§3.4.1)

$$\mathcal{G} = \left(A^{(1)}, A^{(2)}, A^{(3)}, A^{(4)}, A^{(5)}\right)$$

5 Ebenen: Handel, Information, Kredit, Sozial, Politisch. $A^{(\ell)} \in [0,1]^{N \times N}$.

**Linkdynamik (V.8):**
$$\dot{A}_{ij}^{(\ell)} = \alpha_\ell^+\,g(z_i, z_j)\,(1 - A_{ij}^{(\ell)}) - \alpha_\ell^-\,A_{ij}^{(\ell)}$$

| Term | Bedeutung |
|---|---|
| $\alpha_\ell^+ g(z_i,z_j)(1-A_{ij}^{(\ell)})$ | Linkbildung (Ähnlichkeit + Sättigung) |
| $-\alpha_\ell^- A_{ij}^{(\ell)}$ | Linkzerfall |

---

### V.7 — Effektive Adjazenz (§3.4.2)

$$A^{\text{eff}} = \sum_{\ell=1}^{5} \omega_\ell\,A^{(\ell)}$$

Gewichtete Superposition aller Netzwerkebenen. Gewichte $\omega_\ell$ zustandsabhängig (in Kreditkrise: $\omega_3$ steigt).

**Graph-Laplacian:**
$$L_{ij}^{\text{eff}} = \begin{cases} \sum_k A_{ik}^{\text{eff}} & i = j \\ -A_{ij}^{\text{eff}} & i \neq j \end{cases}$$

---

### V.8 — Linkdynamik (§3.4.3)

$$\dot{A}_{ij}^{(\ell)} = \alpha_\ell^+\,g(z_i, z_j)\,(1 - A_{ij}^{(\ell)}) - \alpha_\ell^-\,A_{ij}^{(\ell)}$$

(Siehe V.6 für Vollbeschreibung.)

---

## Gleichungszählung

| Gruppe | Gleichungen | Anzahl |
|---|---|---|
| **A.1** Erhaltung | I.1, I.2, P.3, I.4, M.1, M.2, K.1 | **7** |
| **A.2** Preise/Flüsse | II.1–II.4, F.1, F.2 | **6** |
| **A.3** Entscheidungen | U.1–U.3, V.1–V.3, V.1a, L.1–L.5, L.1a, III.2–III.4, VI.1–VI.9 | **25** |
| **A.4** Information | I.1–I.3, I.5, Ent.2 | **5** |
| **A.5** Geld/Aggregation | M.3, M.4, E.1, P.4, V.9, IV.1–IV.4 | **9** |
| **A.6** Population/Struktur | N.1–N.5, VII.1–VII.4 | **9** |
| **A.7** Sprünge/Regime | VIII.1–VIII.7, Schw.1, Schw.2, RS.1 | **10** |
| Netzwerk | V.6–V.8 | **3** |
| **Summe** | | **74** |

> Die Differenz zu "75" ergibt sich daraus, dass VIII.4 ≡ RS.1 (strukturell identisch), V.9 eine Identität ist, und Sub-Gleichungen (V.1a, L.1a) teils separat gezählt werden.

---

## Kopplungsstruktur

```
Axiome A1–A10
    │
    ├─► Erhaltung (Kap. 4): I.1, I.2, P.3, I.4, M.1, M.2, K.1
    │       │
    │       ▼
    ├─► Preise/Flüsse (Kap. 5): II.1–II.4, F.1, F.2
    │       │
    │       ▼
    ├─► Entscheidungen (Kap. 6): U.*, V.*, L.*, III.*, VI.*
    │       │
    │       ▼
    ├─► Information (Kap. 7): I.1–I.5(Info), Ent.2
    │       │
    │       ▼
    ├─► Geld/Aggregation (Kap. 8): M.3, M.4, E.1, P.4, V.9, IV.*
    │       │
    │       ▼
    ├─► Population/Struktur (Kap. 9): N.*, VII.*
    │       │
    │       ▼
    └─► Sprünge/Regime (Kap. 10): VIII.*, Schw.*, RS.1
    
    Netzwerk (Kap. 3): V.6–V.8 (koppelt an alle Gruppen via A_ij)
```

---

*Generiert aus Monographie_v2.md — alle Gleichungen mit Anhang A verifiziert.*
