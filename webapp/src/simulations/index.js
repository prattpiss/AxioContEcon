/**
 * Simulation registry — all available simulations.
 * Import and register each simulation config here.
 * The Explorer component reads this to build the sidebar.
 */

import S08_II2 from './S08_II2.js';
import S09_F2 from './S09_F2.js';
import S10_F1 from './S10_F1.js';
import S11_II1 from './S11_II1.js';

// All simulations, grouped by chapter
export const chapters = [
  {
    id: 4,
    title: 'Kap. 4: Erhaltungssätze',
    sims: [
      { id: 'S01', eqId: 'I.1', title: 'Individuelle Vermögensbilanz', section: '§4.1', available: false },
      { id: 'S02', eqId: 'I.2', title: 'Aggregierte Vermögenserhaltung', section: '§4.2', available: false },
      { id: 'S03', eqId: 'P.3', title: 'Güterbestandsdynamik', section: '§4.3', available: false },
      { id: 'S04', eqId: 'I.4', title: 'Gelderhaltung', section: '§4.4', available: false },
      { id: 'S07', eqId: 'K.1', title: 'Kapitalakkumulation', section: '§4.6', available: false },
    ],
  },
  {
    id: 5,
    title: 'Kap. 5: Preise & Flüsse',
    sims: [
      { id: 'S08', eqId: 'II.2', title: 'Fundamentale Preisdynamik', section: '§5.1', available: true, config: S08_II2 },
      { id: 'S09', eqId: 'F.2', title: 'Effektives Potential', section: '§5.2', available: true, config: S09_F2 },
      { id: 'S10', eqId: 'F.1', title: 'Allgemeiner Güterfluss', section: '§5.3', available: true, config: S10_F1 },
      { id: 'S11', eqId: 'II.1', title: 'Vermögensfluss', section: '§5.4', available: true, config: S11_II1 },
      { id: 'S12', eqId: 'II.4', title: 'Geldfluss', section: '§5.5', available: false },
      { id: 'S13', eqId: 'II.3', title: 'Informationsfluss', section: '§5.6', available: false },
    ],
  },
  {
    id: 6,
    title: 'Kap. 6: Quellen & Reaktionen',
    sims: [
      { id: 'S14', eqId: 'V.1', title: 'Konsum-/Nachfragefunktion', section: '§6.1', available: false },
      { id: 'S15', eqId: 'V.2', title: 'Sparfunktion', section: '§6.2', available: false },
    ],
  },
];

/** Flat list of all available simulation configs */
export const allSimulations = chapters.flatMap(ch =>
  ch.sims.filter(s => s.available && s.config).map(s => s.config)
);

/** Lookup by simulation ID */
export function getSimulation(id) {
  for (const ch of chapters) {
    const sim = ch.sims.find(s => s.id === id);
    if (sim?.config) return sim.config;
  }
  return null;
}

export default chapters;
