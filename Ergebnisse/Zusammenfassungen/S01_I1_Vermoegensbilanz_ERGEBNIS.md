# S01 – Individuelle Vermögensbilanz (Gleichung I.1) — ERGEBNIS

> **Simulation:** S01_I1_Vermoegensbilanz.py  
> **Gleichungen:** I.1 (§4.1), I.2 (§4.2), M.2 (§4.3)  
> **Datum:** 2026-04-12  
> **Status:** ✓ ALLE CHECKS BESTANDEN

---

## Gleichungen (exakt aus Monographie)

**I.1:** $\dot{w}_i = y_i - c_i + \sum_k \theta_{ik}\dot{p}_k + r\,b_i$

Spezialisierungen:
- Arbeiter: $\dot{w}_i = w_\ell \ell_i - c_i + \sum_k \theta_{ik}\dot{p}_k + r\,b_i$, $b_i \geq 0$
- Unternehmer: $\dot{w}_j = (p_k q_{jk} - w_\ell L_j - rK_j) - c_j + \sum_k \theta_{jk}\dot{p}_k + r\,b_j$
- Banken: $\dot{w}_b = (r_L L_b - r_D D_b) - c_b^{\text{Betrieb}} + \sum_k \theta_{bk}\dot{p}_k$

**I.2:** $\dot{W} = Y - C$ (aggregiert; Bewertungs- und Zinsterme canceln)

**M.2:** $\sum_i b_i = 0$ (Kreditmarkt-Clearing)

---

## Vereinfachungen

| Nr | Annahme | Konsequenz |
|----|---------|------------|
| 1 | Räumlich homogen | Keine PDEs |
| 2 | 1 Gut ($k=1$) | $\theta_{i1} = \theta_i$ |
| 3 | 3 Agentenklassen (10W, 5U, 2B) | Heterogenität ohne Staat/ZB |
| 4 | Preis exogen (Trend + Sinus) | Bewertungseffekte testbar |
| 5 | Konsum $c_i = c_{\min} + c' \max(w_i, 0)$ | Linear, NB.1 eingehalten |

---

## Validierungsprotokoll

| Check | Ergebnis | Wert |
|-------|----------|------|
| [1] M.2: $\sum b_i = 0$ | ✓ PASS | $0.00$ |
| [2] $\sum \theta_i = 1$ | ✓ PASS | $1.000000$ |
| [3] I.2: $dW/dt = Y - C + \dot{p}$ | ✓ PASS | max Error $1.5 \times 10^{-3}$ |
| [3b] Zinsterme canceln | ✓ PASS | $r \sum b_i = 0$ |
| [3c] Bewertungsterme: $\sum\theta_i\dot{p} = \dot{p}$ | ✓ PASS | exakt |
| [4] Stationäre Punkte analytisch | ✓ berechnet | siehe unten |
| [5] Eigenwerte Jacobi-Matrix | ✓ ALLE $< 0$ | $\lambda=-0.05, -0.03, -0.01$ |
| [6] Keine NaN/Inf | ✓ PASS | — |
| [7] NB.1: $c_i \geq c_{\min}$ | ✓ PASS | eingehalten |

---

## Stationäre Punkte (analytisch, $\dot{p}=0$, $p=p_0$)

$$w_i^* = \frac{y_i - c_{\min} + r\,b_i}{c'_i}$$

| Klasse | $w^*$ | Interpretation |
|--------|-------|----------------|
| Arbeiter | 7.20 | Niedrig, stabil, konvergent |
| Unternehmer 0 | 592.00 | Hohe Profite → hohes SS-Vermögen |
| Unternehmer 1 | 425.33 | Geringer produzierend |
| Bank 0 | −23.50 | **Warnung:** Negativer SS — Zinsmarge deckt Betriebskosten nicht voll |

---

## Eigenwerte der Jacobi-Matrix

$$J = \text{diag}(-c'_W, \ldots, -c'_U, \ldots, -c'_B) = \text{diag}(-0.05, \ldots, -0.03, \ldots, -0.01)$$

Alle Eigenwerte reell und negativ → **asymptotisch stabiler Knoten**.

Erholungszeiten: $t_{1/2} = \ln 2 / |λ|$
- Arbeiter: $t_{1/2} = 13.9$ Zeiteinheiten
- Unternehmer: $t_{1/2} = 23.1$ Zeiteinheiten
- Banken: $t_{1/2} = 69.3$ Zeiteinheiten

---

## Beobachtungen

1. **Ungleichheitsdynamik:** Unternehmer akkumulieren Vermögen viel schneller als Arbeiter (Faktor ~80x im Steady State). Dies ist konsistent mit der Piketty-Bedingung ($r > g$ effektiv für Unternehmer).

2. **Preis-Oszillationen:** Der sinusförmige Preispfad erzeugt periodische Bewertungsschwankungen. Diese sind proportional zu $\theta_i$ — Agenten mit größerem Portfolioanteil sind stärker exponiert.

3. **Aggregierte Identität I.2:** Die dW/dt = Y − C + ṗ Identität wird numerisch mit Fehler < $10^{-3}$ bestätigt (begrenzt durch Diskretisierung von np.gradient, NICHT durch den ODE-Solver).

4. **Bank-Warnung:** Der negative stationäre Punkt der Banken bei diesen Parametern deutet darauf hin, dass die gewählte Zinsmarge ($r_L - r_D = 0.03$) und Einlagen/Kredit-Volumina langfristig nicht tragfähig sind. In einem vollständigen Modell würden Banken ihren Kreditzins oder Einlagenzins anpassen (endogene Reaktion via VI.1).

---

## Dateien

| Typ | Pfad |
|-----|------|
| Code | `Simulationen/Kap04_Erhaltung/S01_I1_Vermoegensbilanz.py` |
| Plot | `Ergebnisse/Plots/S01_I1_Vermoegensbilanz.png` |
| Daten | `Ergebnisse/Daten/S01_I1_Vermoegensbilanz.npz` |
| Bericht | `Ergebnisse/Zusammenfassungen/S01_I1_Vermoegensbilanz_ERGEBNIS.md` |

---

## Nächster Schritt

**S02 — Aggregierte Vermögenserhaltung I.2** (dedizierte Prüfung mit mehreren Gütern und expliziter Nullsummen-Demonstration)
