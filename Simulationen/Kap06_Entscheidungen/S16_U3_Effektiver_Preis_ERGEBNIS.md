# S16 – Effektiver Preis U.3: Dynamik, Kopplung, Marktversagen

## Gleichung
$$p_k^{\text{eff}} = p_k \cdot \left(1 + \frac{\psi_k}{I_k + \varepsilon}\right)$$

## Abgrenzung zu S15
S15 behandelte U.3 als statische Abbildung I→p_eff. S16 geht tiefer:
dynamische Kopplung, Marktversagen (Stigler, Akerlof, Grossman-Stiglitz),
Budget-Verzerrung, Singularitätsanalyse, Wohlfahrtsdekomposition U.2 vs U.3.

## 7 Regime

### R1: Stigler-Suche — Optimale Informationsbeschaffung
- **Modell**: Agent maximiert Nettonutzen = (v₀ - p_eff(I)) - C(I), mit C(I) = c₀I + c₁I²
- **FOC**: C'(I*) = |∂p_eff/∂I| → Grenzkosten = Grenznutzen
- **Ergebnis**: I* sinkt mit steigenden Suchkosten c₀ (7.6 → 4.5)
  - Residuale Ignoranz ist OPTIMAL (Stigler 1961)
  - p_eff* steigt von 16.6 (billige Suche) auf 21.1 (teure Suche)

### R2: Akerlof Lemons — Adverse Selection
- **Modell**: 500 Verkäufer mit Qualität q ∈ [0.1, 10], Käufer mit asymmetrischer Info
- **Wahrgenommene Qualität**: q_perceived = q_avg · I/(I+ψ)  (Bayes-Signal)
- **Ergebnis**: I=0.1 → 10 Trades (avg_q=0.21), I=50 → 389 Trades (avg_q=3.91)
- **Lemons-Spirale** (I_buyer=2.0):
  - Runde 0: 500 Verkäufer, avg_q=5.04
  - Endrunde: avg_q=0.16 — fast vollständiger Qualitätskollaps
  - Gute Verkäufer verlassen sukzessiv den Markt

### R3: Grossman-Stiglitz — Inneres Gleichgewicht
- **Modell**: Anteil α informiert (Kosten c_info), Rest uninformiert
- **Spillover**: I_eff_uninf(α) = I_uninf + α^0.5 · (I_inf - I_uninf)
  - Bei α→1: Marktpreise voll informativ → I_eff → I_inf
- **GS-Paradox**: Mehr Informierte → Preis effizienter → weniger Anreiz
- **alpha***: c=0.2→0.91, c=0.5→0.79, c=1→0.64, c=2→0.44, c=5→0.19
  - Teurere Info → weniger Informierte im GG

### R4: Budget-Verzerrung
- 3 Güter: p = [5, 10, 15], ψ = [1, 3, 8]
- **Kaufkraftverlust**: I=50→20%, I=5→80%, I=1→99%, I=0.1→100%
- Asymmetrisches Profil [20, 2, 0.5]: 98% Verlust — Gut 3 mit ψ=8, I=0.5 dominiert
- **Poverty Tax**: Info-Arme zahlen überproportional mehr

### R5: Dynamische Kopplung I(t) → p_eff(t)
- **ODE**: dI/dt = r_I·I·(1-I/I_max) - ω(t)·I + S(t)
- Normal: I(0)=1 → I(100)=20.6, p_eff: 50→11.9 (logistisches Wachstum)
- Nachrichtenflut t=30: Gauss-Puls S(t), temporärer I-Sprung
- **Zensur ab t=50**: ω steigt 10× → I kollabiert → p_eff=3947 (Markt bricht zusammen)

### R6: Singularität I→0
- p_eff ~ pψ/ε bei I→0 (Pol erster Ordnung)
- **Kritische Schwelle** (p_eff > 2p): I_crit ≈ ψ/(threshold-1) - ε
  - ε=0.001: I_crit=5.00, ε=1.0: I_crit=4.00
- ε-Regularisierung bestimmt maximalen effektiven Preis bei völliger Uninformiertheit

### R7: Wohlfahrtsdekomposition U.2 vs U.3
- 5 Güter mit heterogenem Profil
- **U.2-Verlust** (Aufmerksamkeitsverzerrung): Softmax ignoriert I-arme Güter
- **U.3-Verlust** (Preisaufschlag): p_eff >> p bei niedrigem I
- Bei I=1: U.2-Verlust=45.4, U.3-Verlust=78.7 → **U.3 dominiert**
- Bei hohem I konvergieren beide → 0 (Arrow-Debreu-Limit)

## 8 Validierungen — ALLE BESTANDEN

| # | Test | Ergebnis |
|---|------|----------|
| V1 | Stigler FOC: MB=MC | PASS (max\|ΔF\|/MC=2.81e-07) |
| V2 | I* sinkt mit c₀ | PASS (7.6 → 4.5) |
| V3 | Akerlof: mehr I → mehr Handel | PASS (10 → 389) |
| V4 | Lemons-Spirale: Q sinkt | PASS (5.04 → 0.16) |
| V5 | GS: α* ∈ (0,1) | PASS (alle 5 c_info) |
| V6 | Budget: Verlust steigt bei I↓ | PASS (20% → 100%) |
| V7 | Zensur: p_eff steigt | PASS (12.3 → 3947) |
| V8 | Wohlfahrt steigt mit I | PASS (321 → 46) |

## 4 Sensitivitätsanalysen

- **SA1**: I*(ψ) — stärkere Marktopazität → mehr Suche (I* steigt 3.6→8.6)
- **SA2**: I*(ε) — Regularisierung kaum Einfluss auf optimale Suche (6.57→5.80)
- **SA3**: GS α*(ψ) — höheres ψ → mehr Informierte im GG (0.10→0.69)
- **SA4**: Cross-Good Spillover — 20% Info-Transfer: p_eff₂ sinkt von 24.9 auf 13.8

## Kausalketten

1. **Stigler**: Suchkosten → residuale Ignoranz optimal → nie volle Information
2. **Akerlof**: I_buyer << I_seller → adverse Selektion → Qualitätsspirale → Marktkollaps
3. **Grossman-Stiglitz**: Mehr Informierte → effizienterer Preis → weniger Anreiz → inneres GG
4. **Budget**: p_eff > p schrumpft Konsummenge → Info-Arme zahlen „Poverty Tax"
5. **Zensur**: I↓ → sofortiger p_eff-Anstieg → Wohlfahrtsverlust

## Dateien
- `S16_U3_Effektiver_Preis.py` — Simulation
- `Ergebnisse/Plots/S16_U3_Effektiver_Preis.png` — 24-Panel-Plot
- `Ergebnisse/Daten/S16_U3_Effektiver_Preis.npz` — Numerische Daten
