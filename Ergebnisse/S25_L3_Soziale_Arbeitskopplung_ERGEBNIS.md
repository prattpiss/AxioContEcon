# S25 — L.3 Soziale Arbeitskopplung (§6.4)

## Gleichung

$$\Sigma_i = \sum_{j=1}^N A_{ij}^{\text{eff}} \, \Phi_L\bigl(L_j - L_i, \mathcal{I}_j, \mathcal{I}_i\bigr) + \mathcal{S}\bigl(\text{rank}_i, \text{Kultur}\bigr)$$

Zwei Komponenten:
- **L.3a Peer-Normkonvergenz** $\Phi_L$ — strukturell identisch zu V.3 ($\Phi_c$, S20)
- **L.3b Statusdruck** $\mathcal{S}$ — einzigartig für L.3 (Arbeit sichtbar, Konsum verborgen)

## Ergebnisse

| Validierung | Ergebnis | Detail |
|---|---|---|
| V1: Nullpunkt $\Phi_L(0,\cdot,\cdot)=0$ | **PASS** | $|\Phi_L| = 0.00 \times 10^{0}$ |
| V2: Monotonie $\partial\Phi_L/\partial(L_j-L_i) > 0$ | **PASS** | all_increasing=True |
| V3: Asymmetrie $|\Phi_L(+)| > |\Phi_L(-)|$ | **PASS** | Ratio = 2.50 (alle d) |
| V4: Beschränktheit $|\Phi_L| \leq \Phi_{\max}$ | **PASS** | $\max|\Phi_L| = 3.0000$ |
| V5: Info-Modulation $\partial|\Phi_L|/\partial I_j > 0$ | **PASS** | all_increasing=True |
| V6: Statusmonotonie $\partial S/\partial\text{rank} > 0$ | **PASS** | $S(0)=0, S(1)=0.40$ |
| V7: Kultursensitivität $S(\text{JP}) \gg S(\text{FR})$ | **PASS** | Ratio = 8.3 |
| V8: Prop 6.2 $L.3(S=0) \equiv V.3$ | **PASS** | $\max|\Delta| = 0.00 \times 10^{0}$ |

**Gesamtergebnis: 8/8 bestanden**

## Regime

| # | Regime | Kernergebnis |
|---|---|---|
| R1 | Φ_L-Grundeigenschaften | $\Phi_L(+5)=+0.374$, $\Phi_L(-5)=-0.150$, Asymmetrie 2.50 |
| R2 | Status-Operator S(rank, Kultur) | Japan $S(0.5)=0.669$, FR $S(0.5)=0.080$, Integral JP=0.614 |
| R3 | Multiplex-Netzwerk (N=100) | Scale-Free, density=0.299, Fiedler=1.977 |
| R4 | Norm-Kaskade (Aufwärts) | Hub L=14→24h, Mean 8.1→23.8h, Spread 6.0→1.5 |
| R5 | Kulturvergleich | Japan 24.0h, USA 23.1h, DE 18.9h, FR 12.8h; ΔL(JP-FR)=11.2h |
| R6 | Vier-Ebenen (L.1+L.2+L.3) | Komplett: L=23.5h, Gini=0.014 (maximale Konvergenz) |
| R7 | Overwork-Kaskade (Japan) | 10 Workaholics → 100% über 12h (volle Contagion) |
| R8 | Prop 6.2 Symmetrie | $\max|V.3_{\text{dyn}} - L.3_{\text{dyn}}(S=0)| = 0$ (perfekt) |

## Sensitivitätsanalysen

| SA | Parameter | Ergebnis |
|---|---|---|
| SA1 | Kultur-Sweep (k=0.1–4.0) | S(rank=0.5): 0.027 → 1.067 (linear in k) |
| SA2 | 50×50 Heatmap Φ_L(dL, I_j) | min = −0.490, max = 1.225 |
| SA3 | Peer/Status-Dekomposition | Peer ≈ 8.4h (konstant), Status bis +15.6h (k=3) |
| SA4 | Topologie-Konvergenz | Scale-Free (spread=2.1) < Small-World (3.1) < Random (4.5) |
| SA5 | Herding-Stärke vs Gini | α=0.01: G=0.085, α=0.5: G=0.000 (volle Homogenisierung) |

## Erweiterte Analysen

| EA | Analyse | Ergebnis |
|---|---|---|
| EA1 | Peer/Status zeitlich | Peer: 0.21→0.00 (Konvergenz), Status: 0.37 (konstant) |
| EA2 | Spektralanalyse | Fiedler=1.977, gap_ratio=0.181 |
| EA3 | Entropie-Evolution | S(0)=4.603, S(T)=4.605, S(T)/S_max=1.000 |
| EA4 | Phasendiagramm (Kultur, α_up) | L_mean: 9.3h–24.0h, Überarbeit ab k≈1.5 |

## Mathematische Strukturen

1. **Duale Sozialoperatoren**: L.3 = Φ_L (Graph-Diffusion, konvergierend) + S (Status-Lift, immer positiv → Gleichgewicht nach oben verschoben). Fokker-Planck auf Netzwerk: Diffusion + Drift.

2. **Status-induzierter Symmetriebruch**: V.3 hat nur Φ → Gleichgewicht bei Mittelwert. L.3 hat Φ_L + S → Gleichgewicht ÜBER Mittelwert. Kulturparameter steuert Bruchstärke (Japan: stark, Frankreich: schwach).

3. **Kuramoto mit externem Feld**: S wirkt wie externes Feld in Spin-Systemen → bricht Rotationssymmetrie des Kuramoto-Modells. Fiedler-Wert = 1.977 (Synchronisierbarkeitsmaß).

4. **Prop 6.2 — Strukturelle Symmetrie**: Bei S = 0 ist L.3 EXAKT V.3 (numerisch: max|Δ| = 0). Der Status-Term S ist die EINZIGE Quelle der Asymmetrie zwischen Konsum- und Arbeitsdynamik. Ökonomisch: „Konsum kann man verbergen — Arbeitszeit nicht."

## Zentrale Einsicht

L.3 enthält im Gegensatz zu V.3 einen *zusätzlichen* Statusdruck-Operator $\mathcal{S}$. Arbeit ist sozial sichtbarer als Konsum — die Peer-Konvergenz (Φ_L) wird durch eine hierarchische Status-Komponente ergänzt, die das Gleichgewicht systematisch nach oben verschiebt. Im japanischen Szenario (k=2.5) führt dies zu L_eq ≈ 24h/Tag (vollständige Überarbeitung durch sozialen Druck), während in Frankreich (k=0.3) L_eq ≈ 12.8h bleibt. Die Dekomposition (SA3) zeigt: Peer-Effekte sind kulturunabhängig (~8.4h), der gesamte Kulturunterschied kommt aus dem Status-Term.
