# S12 – Geldfluss II.4 (§5.5) — ERGEBNIS

## Gleichung
$$\vec{j}_m = -D_m\,\nabla r + \sigma_m\,\vec{E}_{\mathrm{Kredit}}$$

mit $\vec{E}_{\mathrm{Kredit}} = -\nabla\Phi_{\mathrm{Kredit}}$ und lokalem Zinssatz
$r(x,t) = r_{\mathrm{base}} + \kappa\,\ln(\rho_m/\rho_0)$.

## Physik (§5.5)
- **Zinsgradient-Fluss**: $-D_m\nabla r$ — Carry Trade, Geld fließt zu höherem Zins
- **Kreditfeld-Fluss**: $-\sigma_m\nabla\Phi_{\mathrm{Kredit}}$ — Bankenkreditanreiz
- **Nullzinsgrenze**: $r\to 0 \Rightarrow \nabla r \approx 0$ → nur Kreditkanal wirkt → erklärt QE-Wirksamkeit
- **Credit Crunch**: $\Phi_{\mathrm{Kredit}}\to 0$ → Geldfluss versiegt

## Zwei Regime
| Regime | Bedingung | Beispiel |
|--------|-----------|----------|
| Zinsgetrieben | $D_m\nabla r \gg \sigma_m E$ | Carry Trade (normale Geldpolitik) |
| Kreditgetrieben | $\sigma_m E \gg D_m\nabla r$ | QE (2009–2022), Credit Crunch |

## 5 Regime simuliert

| # | Regime | Physik | Ergebnis |
|---|--------|--------|----------|
| R1 | Reiner Zinsgradient | $\sigma_m=0$: $j=-D\nabla r$, Carry Trade | $M$ erhalten, Zinsdispersion −84% |
| R2 | Kreditgetrieben | $D_m=1.5$, $\sigma_m=20$: Kreditkanal dominiert | $j_K/j_Z = 3.2$× |
| R3 | Nullzinsgrenze + QE | $r\to 0$ bei $t=60$, QE ab $t=80$ | $M$ +48.6% via Kreditkanal |
| R4 | Credit Crunch | $\Phi_{\mathrm{Kredit}}$ kollabiert bei $t=80$ | $\Phi$ →10%, Geldfluss versiegt |
| R5 | Voll stochastisch | OU-$D$, OU-$r$, OU-$\Phi$, Poisson-QE | Realistisch stochastische Dynamik |

## Validierungen (6/6 bestanden ✅)

| # | Test | Ergebnis | Status |
|---|------|----------|--------|
| V1 | Geldmengenerhaltung (R1, $Q_m=0$) | $\delta M/M = 3.3\times 10^{-3}$ | ✅ |
| V2 | Zinsdispersion sinkt (R1) | $-84\%$ Reduktion | ✅ |
| V3 | Kreditkanal-Dominanz (R2) | $j_K/j_Z = 3.2$× | ✅ |
| V4 | QE-Effekt (R3) | $M$ +48.6% nach QE | ✅ |
| V5 | Credit Crunch (R4) | $\Phi\to 10\%$ bestätigt | ✅ |
| V6 | Sensitivität $D_m\times\sigma_m$ (625pt) | $j_K/j_Z\in[0,27]$, monoton | ✅ |

## Numerik
- **Methode**: MOL (Method of Lines), NX=201, $\Delta x=0.5$km, Neumann BC
- **ODE-Solver**: Radau (implizit, steif), rtol=$10^{-6}$, atol=$10^{-8}$, max_step=1.0
- **Sparse Jacobi**: Tridiagonal CSC-Matrix für effiziente Radau-Lösung
- **Stochastik**: Euler-Maruyama (OU), Poisson-Pulse (QE-Injektionen)
- **Sensitivität**: 25×25 = 625 Punkte ($D_m \times \sigma_m$)

## Funktionalformen (7 Typen)
- **Räumlich**: Gaußprofil, Glatter Sprung (Logistik), Rampe
- **Zeitlich**: Ornstein-Uhlenbeck (D, r, Φ), Logistischer Übergang (r→0, QE), Poisson-Pulse (QE), Sinusoidal
- **Zinsmodell**: $r = r_{\mathrm{base}} + \kappa\ln(\rho/\rho_0)$ (stabile Diffusion, $\partial r/\partial\rho > 0$)

## Dateien
- `S12_II4_Geldfluss.py` — Simulation (5 Regime, 6 Validierungen)
- `S12_II4_Geldfluss.png` — Plot (15 Panels + Metadaten)
- `S12_II4_Geldfluss.npz` — Numerische Daten
- `S12_II4.js` — AxioLab Webapp-Konfiguration (NX=51, 5 Presets)
