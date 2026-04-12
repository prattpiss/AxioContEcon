# S17 – Euler-Gleichung V.1: Rationaler Konsum (§6.3)

## Gleichung
$$\dot{c}_i = R_i \cdot c_i, \quad R_i = \frac{r - \beta_i}{\gamma_i}$$

Analytische Lösung: $c(t) = c_0 \exp(Rt)$

V.1a Wahrgenommener Zins: $r_i^{\text{wahr}} = r - \frac{\varphi}{I_i + \varepsilon}$

## 8 Regime

### R1: Ramsey-Euler Basis (3 Agentenklassen)
- **Geduldig** (β=0.02, γ=2): R=+0.015, c(50)=21.2 — wächst stetig
- **Neutral** (β=0.05, γ=1): R=0, c(50)=10.0 — exaktes Steady State
- **Ungeduldig** (β=0.08, γ=0.5): R=−0.06, c(50)=0.50 — schrumpft

### R2: Ramsey-Steady-State (S17a: r=β)
- 7 Zinssätze um β=0.05 gesweept
- r=β=0.05 → R=0, c=const (exakt auf Maschinengenauigkeit)
- r>β: Konsum wächst exponentiell, r<β: schrumpft

### R3: Risikoneutral (S17b: γ→0)
- γ=0.05: R=0.40, c(50)=4.85×10⁹ — explosive Dynamik
- γ=2.0: R=0.01, c(50)=16.5 — moderates Wachstum
- Risikoneutrale Agenten reagieren extrem auf r−β

### R4: Extreme Risikoaversion (S17c: γ→∞)
- γ=100: R=0.0002, c(50)=10.10 — quasi-konstant (|Δc/c|=1%)
- γ→∞ bedeutet perfekte Konsumglättung

### R5: Wahrgenommener Zins V.1a
- I=0.1: r_wahr=−4.50, c kollabiert → Info-Arme unterschätzen Zinsen massiv
- I=5: r_wahr=−0.05, c sinkt moderat
- I=20: r_wahr=+0.025, fast korrekt
- I→∞ (EMH): r_wahr→r=0.05, c(T)=19.5

### R6: Gekoppeltes Vermögen-Konsum-System
- dw/dt = rw + y − pc gekoppelt mit dc/dt = Rc
- **Sparer** (β=0.02): w(50)=36 — Vermögen bleibt positiv
- **Balanced** (β=0.04): w(50)=−297 — geht in Schulden
- **Verschwender** (β=0.08): w(50)=682 — paradox: Konsum schrumpft so stark, Vermögen akkumuliert

### R7: Heterogene Agenten (N=200)
- β ~ Lognormal(0.04, 0.3), γ ~ Lognormal(1.5, 0.5)
- **Gini-Dynamik**: 0.168 (t=0) → 0.244 (t=25) → 0.396 (t=50)
- Endogene Ungleichheit allein durch heterogene Präferenzen

### R8: Budget mit Info-Friction (V.1a gekoppelt)
- I=0.2: r_wahr=−3.76, Konsum→0, Vermögen akkumuliert ungenutzt (2289)
- I=50: r_wahr=+0.034, fast EMH-Verhalten (c(T)=8.2, w(T)=232)
- Info-Friction verzerrt Konsum-Spar-Entscheidung fundamental

## 8 Validierungen — ALLE BESTANDEN

| # | Test | Ergebnis |
|---|------|----------|
| V1 | Nullpunkt: r=β ⇒ c=const | PASS (Fehler=0) |
| V2 | Analytisch vs Numerisch | PASS (max_err=4.2×10⁻¹³) |
| V3 | Monotonie: ∂R/∂r>0, ∂R/∂β<0, ∂|R|/∂γ<0 | PASS (alle 3) |
| V4 | Klassen: Geduldig↑, Ungeduldig↓ | PASS (21.2>10, 0.5<10) |
| V5 | Risikoneutral: γ=0.05 >> γ=2 | PASS (4.9×10⁹ >> 16.5) |
| V6 | Risikoavers: γ=100 ⇒ c≈const | PASS (|Δc/c|=1%) |
| V7 | EMH: I→∞ ⇒ r_wahr→r | PASS (|Δr|=5×10⁻⁷) |
| V8 | Gini(T) > Gini(0) | PASS (0.168→0.396) |

## 5 Sensitivitätsanalysen

- **SA1**: R(γ) — R=0.20 bei γ=0.1, R≈0 bei γ=50
- **SA2**: R(β) — linear, Nullstelle bei β=r=0.05
- **SA3**: R(r) — inklusive negative Zinsen (r=−0.03: R=−0.047)
- **SA4**: c(T,I) — Info-Schwelle: c(T)≈0 für I<1, c(T)→19 für I→∞
- **SA5**: 50×50 Heatmap R(γ,r) — schwarze Nulllinie bei r=β=0.04

## Kausalketten

1. **r > β**: Geduld wird belohnt → exponentielles Konsumwachstum → Vermögensdivergenz
2. **r = β**: Ramsey-Goldene Regel → Steady State → intertemporale Indifferenz
3. **γ → 0**: Keine Glättung → explosive Reaktion auf r−β
4. **γ → ∞**: Perfekte Glättung → c≈const unabhängig von r−β
5. **I → 0**: r_wahr << r → systematische Fehleinschätzung → Unter-/Überkonsum
6. **(β,γ)-Heterogenität**: Endogene Ungleichheitsdynamik ohne externe Schocks

## Dateien
- `S17_V1_Euler_Gleichung.py` — Simulation
- `Ergebnisse/Plots/S17_V1_Euler_Gleichung.png` — 27-Panel-Plot
- `Ergebnisse/Daten/S17_V1_Euler_Gleichung.npz` — Numerische Daten
