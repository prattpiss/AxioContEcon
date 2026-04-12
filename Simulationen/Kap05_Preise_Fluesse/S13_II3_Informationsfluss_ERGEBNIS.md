# S13 – Informationsfluss II.3 (§5.6, Vorschau Kap. 7) — ERGEBNIS

## Gleichung
$$\dot{\mathcal{I}}_k = D_{\mathcal{I}}\nabla^2\mathcal{I}_k - \omega\mathcal{I}_k + \mathcal{S}_k - \mu\mathcal{I}_k^3 + \beta|\dot{p}_k|$$

## Physik (§5.6)
- **Diffusion** $D_{\mathcal{I}}\nabla^2\mathcal{I}$: Nachrichten breiten sich räumlich aus (Kommunikationsinfrastruktur)
- **Zerfall** $-\omega\mathcal{I}$: Information ist *verderblich* — Vergessen, Veralten
- **Quellen** $\mathcal{S}_k$: Werbung + Word-of-Mouth + Nutzungserfahrung
- **Sättigung** $-\mu\mathcal{I}^3$: Ginzburg-Landau-Nichtlinearität, verhindert unbegrenztes Wachstum
- **Preis-Feedback** $\beta|\dot{p}|$: "Events create news" — Preisbewegungen erzeugen Information

## Kausalkette (bidirektionale Kopplung)
| Richtung | Mechanismus | Gleichung |
|----------|-------------|-----------|
| Preis → Info | $|\dot{p}_k| > 0 \Rightarrow \beta|\dot{p}| \Rightarrow \mathcal{I}$ steigt | II.3 Term 5 |
| Info → Preis | $\mathcal{I}$ sinkt $\Rightarrow \psi/(\mathcal{I}+\varepsilon)$ steigt $\Rightarrow \mu^{\mathrm{eff}}$ steigt | F.2 + II.2 |

## Zwei Spiralen
| Spirale | Bedingung | Ergebnis |
|---------|-----------|----------|
| **Stabilisierend** | $\beta|\dot{p}| / (\omega\mathcal{I}) > 1$ | Crash erzeugt News → I↑ → Illiquidität↓ → Selbstkorrektur |
| **Destabilisierend** | $\beta|\dot{p}| / (\omega\mathcal{I}) < 1$ | Analysten fliehen → I↓ → Illiquiditätsprämie↑ → Abwärtsspirale |

## Analytische Ergebnisse
- **Informationsreichweite**: $\ell = \sqrt{D_{\mathcal{I}}/\omega}$ (bestätigt: 2.83 km Theorie vs. 3.03 km Numerik)
- **Fisher-KPP Travelling Wave**: $v_{\mathrm{front}} = 2\sqrt{D_{\mathcal{I}}(r_I - \omega)}$ (existiert falls $r_I > \omega$)
- **Stationäre Punktquelle**: $\mathcal{I}^*(x) = \frac{S_0}{2\sqrt{D\omega}} e^{-|x-x_0|/\ell}$ (exponentieller Abfall)

## 6 Regime simuliert

| # | Regime | Physik | Ergebnis |
|---|--------|--------|----------|
| R1 | Diffusion + Zerfall | $S=0$, $\mu=0$: reiner exponentieller Massezerfall | $M(T)/M(0) = 4.5 \times 10^{-5}$, Fehler $3 \times 10^{-3}$ |
| R2 | Punktquelle stationär | $S=\delta(x-50)$: analytischer Vergleich | NRMSE = 0.116, $\ell_{\mathrm{fit}} = 3.03$ km |
| R3 | Fisher-KPP Front | WoM aktiv ($r_I > \omega$): Travelling Wave | $v = 0.57$ km/a (Theorie: 0.72), Front wandert x=14→100 |
| R4 | Preis-Feedback (stabil) | Crash bei $t=50$ erzeugt Informationswelle | I steigt: 0.25 → 0.69 im Zentrum |
| R5 | Illiquiditätsspirale | Hoher Zerfall, schwaches Feedback: I kollabiert | I-Verlust 93.9%, Illiq.prämie ×14 |
| R6 | Voll stochastisch | OU-$D_{\mathcal{I}}$, Poisson-Medienevents | Realistische Schwankungen, 4 Events |

## Validierungen (7/7 bestanden ✅)

| # | Test | Ergebnis | Status |
|---|------|----------|--------|
| V1 | Exponentieller Massezerfall (R1) | Fehler $3.0 \times 10^{-3}$ vs. $e^{-\omega T}$ | ✅ |
| V2 | Punktquelle analytisch (R2) | NRMSE = 0.116 (Zentral x∈[20,80]) | ✅ |
| V3 | Fisher-KPP Frontgeschwindigkeit (R3) | $v = 0.57$ km/a, Theorie 0.72, Fehler 21% | ✅ |
| V4 | Stabilisierende Spirale (R4) | I nach Crash > I vor Crash (0.69 > 0.25) | ✅ |
| V5 | Illiquiditätsspirale (R5) | I < 10% des Startwerts ($6.1\%$) | ✅ |
| V6 | Informationsreichweite $\ell$ (R2) | $\ell_{\mathrm{fit}} = 3.03$ vs. 2.83 Theorie, Fehler 7.3% | ✅ |
| V7 | Sensitivität $D \times \omega$ (625pt) | $\ell$ monoton: steigt mit D, fällt mit $\omega$ | ✅ |

## Kausalitätsanalyse (NEU)
Jedes Regime zeigt eine **Term-Zerlegung** (welcher der 5 Terme ∂I/∂t dominiert):
- **R1**: Zerfall dominiert überall, Diffusion glättet nur → exponentieller Abfall
- **R2**: Stationäre Balance: Quelle = Zerfall + Diffusion (Total ≈ 0)
- **R3**: An der Front: WoM treibt Wachstum, Diffusion breitet die Front aus
- **R4**: Preis-Feedback $\beta|\dot{p}|$ treibt I temporär hoch → stabilisierend
- **R5**: Zerfall dominiert WoM + Feedback → I kollabiert → Illiquiditätsprämie explodiert
- **R4 vs R5**: Identischer Mechanismus, unterschiedliches Gleichgewicht — **Parameterabhängig**

## Phasendiagramm
- $r_I > \omega$: Information breitet sich als Travelling Wave aus (grüne Zone)
- $r_I < \omega$: Information stirbt exponentiell (rote Zone)
- Grenze $r_I = \omega$: Kritische Schwelle — Bistabilität

## Numerik
- **Methode**: MOL (Method of Lines), NX=201, $\Delta x = 0.5$ km, Neumann BC
- **ODE-Solver**: Radau (implizit, steif), rtol=$10^{-6}$, atol=$10^{-8}$, max_step=1.0
- **Sparse Jacobi**: Tridiagonal CSC-Matrix
- **Stochastik**: OU-Prozess (D_I zeitlich), Poisson-Medienevents

## Funktionalformen (8 Typen)
- **Räumlich**: Gaußprofil, Punktquelle (Gaußapprox), Sigmoid-Front, Rampe
- **Zeitlich**: OU-Prozess (Diffusion), Poisson-Pulse (Medienevents), Gaußpuls (Crash), Sinusoidal, Smooth Step

## Dateien
- `S13_II3_Informationsfluss.py` — Simulation (6 Regime, 7 Validierungen, Kausalitätsanalyse)
- `S13_II3_Informationsfluss.png` — Plot (21 Panels + Metadaten + Phasendiagramm)
- `S13_II3_Informationsfluss.npz` — Numerische Daten
- `S13_II3.js` — AxioLab Webapp-Konfiguration
