# D02 — Rapport automatique d’audit

Snapshot UTC : `20261119T182124Z`

## Résultats

| Contrôle | TLT | SPY |
|---|---:|---:|
| Lignes | 2220 | 2220 |
| Lignes signalées | 0 | 0 |
| Dates du week-end | 0 | 0 |

Séances communes : **2220** ; dates TLT seules : **0** ; dates SPY seules : **0**.

Les anomalies détaillées sont dans `anomalies.csv` et le graphique dans `coherence.png`.

Les rendements >20 % en valeur absolue sont des alertes à examiner, pas des erreurs confirmées.
Les jours fériés et les week-ends ne sont pas automatiquement considérés comme des données manquantes.

**Conclusion de l'audit D02**

L'audit a été effectué sur les données journalières du TLT et du SPY, du 2 janvier 2018 au 30 octobre 2026.

Les contrôles automatiques n'ont détecté aucune anomalie parmi les 2 220 observations de chaque actif : aucune date en double ou invalide, aucune valeur numérique manquante, aucun prix non positif et aucune incohérence OHLC.

Les deux séries sont également synchronisées sur les mêmes 2 220 séances.

Les données sont donc retenues pour la modélisation du D03, sous réserve des limites de l'audit automatique. La convention des prix ajustés fournis par Yahoo Finance reste notamment à documenter plus précisément.
