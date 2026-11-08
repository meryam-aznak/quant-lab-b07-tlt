# QUANT LAB — B07 : TLT

**Projet intégrateur — Trading Intelligent**  
**Département d'informatique, Faculté des Sciences, Université Mohammed V de Rabat**  
**Encadrant :** Pr. Tawfik Masrour

## Équipe

| Membre | Nom | Responsabilités principales prévues |
|---|---|---|
| 1 | Meryam Aznak | Collecte et audit des données, analyse exploratoire, économétrie de la moyenne et du risque |
| 2 | Nouhaila Elbouhali | Machine Learning / Deep Learning, interface Streamlit, intégration des stratégies et du backtest |

La définition des hypothèses, la gestion du risque, la validation scientifique, les tests, la documentation et la soutenance sont des responsabilités communes. La répartition pourra évoluer selon les besoins du projet.

## Présentation du projet

**QUANT LAB — B07 : TLT** est un projet intégrateur de Trading Intelligent dont l'objectif est de concevoir et de développer progressivement une application Web interactive, basée sur **Python**, dédiée à l'analyse des marchés financiers et à l'évaluation de stratégies de trading quantitatives.

L'application vise à mettre en place une chaîne de traitement complète, allant de la collecte et de l'analyse des données de marché jusqu'à la prévision des rendements et des risques, la génération de signaux de trading et l'évaluation des stratégies en simulation.

Le projet combine des approches statistiques, économétriques et de Machine Learning / Deep Learning afin d'étudier la relation entre la qualité des prévisions et la pertinence des décisions d'investissement. Une attention particulière sera accordée à la gestion du risque, à la maîtrise des coûts de transaction et à la reproductibilité des expériences.

L'objectif est de développer un **outil intégré, modulaire et reproductible**, permettant de comparer différentes approches de trading dans un environnement de simulation réaliste, plutôt que de se limiter à une collection de notebooks indépendants.

### Actifs financiers étudiés

- **Actif principal — TLT :** ETF exposé aux obligations à long terme du Trésor américain (*iShares 20+ Year Treasury Bond ETF*), particulièrement sensible aux variations des taux d'intérêt et aux évolutions du marché obligataire.
- **Actif de comparaison — SPY :** ETF répliquant l'indice S&P 500 (*SPDR S&P 500 ETF Trust*), utilisé comme référence pour mettre en perspective les comportements et les performances des stratégies étudiées.

## Question scientifique

**Une bonne prévision de l'évolution de TLT suffit-elle pour prendre de bonnes décisions de trading ?**

L'objectif de notre projet est d'étudier si prévoir correctement la hausse ou la baisse de TLT permet réellement d'obtenir de meilleures performances en trading.

Nous souhaitons comparer deux approches :
- **Stratégie directionnelle :** prendre des décisions d'investissement uniquement à partir de la direction du rendement prévu.
- **Stratégie avec filtre de risque :** utiliser la même prévision, tout en adaptant le niveau d'investissement selon le risque estimé.

**Notre hypothèse :** prendre en compte le risque en plus des prévisions pourrait permettre de mieux gérer les investissements et d'obtenir un meilleur équilibre entre rendement et risque. Cette hypothèse sera vérifiée à travers des simulations et une comparaison des deux stratégies.


## Périmètre fonctionnel prévu

L'application devra comporter six espaces :

1. **Market Data :** collecte, mise à jour contrôlée, qualité et visualisation des prix, volumes et rendements.
2. **Model Laboratory :** références naïves, ARIMA/SARIMA/SARIMAX, modèles ML/DL, prévisions et diagnostics.
3. **Risk Management :** ARCH/GARCH, volatilité prévue, VaR, Expected Shortfall et contraintes d'exposition.
4. **Trading Strategy :** signaux datés, règles explicites et positions cibles.
5. **Backtesting :** simulation historique, frais, drawdown et comparaison buy-and-hold / cash.
6. **Paper Trading :** signaux et ordres fictifs sur de nouvelles séances réelles, journal exportable.

Le parcours est : **données → variables → modèles de rendement et de risque → décision → backtest → paper trading**.

## Données et protocole envisagés

- Données journalières OHLCV de TLT, avec SPY synchronisé pour la comparaison.
- Prix ajustés ou convention de total return documentée ; provenance, dates et éventuelles lacunes conservées.
- Décision après clôture du jour *t*, exécution au plus tôt à l'ouverture de *t+1*.
- Périodes proposées par le cahier : apprentissage **2018–2022**, validation **2023–2024**, test final **du 1er janvier 2025 au 30 octobre 2026**, sous réserve de disponibilité et validation par l'enseignant.
- Aucune donnée future ne devra être utilisée pour produire un signal passé.

## Contraintes de simulation

- Capital initial : **100 000 USD virtuels**.
- Position **long/cash** uniquement, exposition comprise entre 0 % et 100 %, sans vente à découvert ni levier.
- Coûts du backtest : **0,05 % de frais + 0,05 % de glissement par côté**, soit **0,10 % par achat ou vente** ; scénario à coûts doublés.
- Mesures prévues : rendement, volatilité, Sharpe, drawdown maximal, turnover, frais, transactions et mesures de risque.
- Paper trading sur au moins cinq nouvelles séances documentées ; aucun argent réel.


### Architecture technique prévue

| Fichier / Dossier | Rôle |
|---|---|
| `app.py` | Point d'entrée de l'application Streamlit |
| `src/data.py` | Acquisition, préparation et contrôle des données |
| `src/features.py` | Création des variables explicatives et des cibles |
| `src/models/` | Implémentation des modèles de prévision |
| `src/risk.py` | Estimation du risque et calcul des indicateurs |
| `src/strategy.py` | Génération des signaux et positions cibles |
| `src/backtest.py` | Simulation historique et prise en compte des coûts |
| `src/paper.py` | Gestion du Paper Trading et du journal des simulations |
| `configs/` | Paramètres et configurations du projet |
| `tests/` | Tests et vérifications du fonctionnement |
| `reports/` | Rapports, résultats et analyses |

---

## Répartition des tâches — Binôme B07

La répartition des responsabilités est organisée par livrable afin de faciliter le suivi du développement et de garantir une contribution équilibrée des deux membres.

| Domaine | Meryam Aznak | Nouhaila Elbouhali |
|---|---|---|
| Cadrage et README (D01) | Co-rédaction | Co-rédaction |
| Collecte, provenance et qualité (D02) | Responsable principale | Relecture et tests |
| Économétrie de la moyenne (D03) | Responsable principale | Relecture et intégration |
| Économétrie du risque (D04) | Responsable principale | Intégration des indicateurs |
| Machine Learning et Deep Learning (D05) | Validation du protocole | Responsable principale |
| Stratégies et Backtesting (D06) | Règles de risque et validation | Implémentation principale |
| Interface Streamlit (D07) | Contrôle des affichages | Implémentation principale |
| Paper Trading (D08) | Contrôle du journal | Intégration principale |
| Tests et reproductibilité (D09) | Partagé | Partagé |
| Rapport et soutenance (D10) | Partagé | Partagé |

Cette répartition est prévisionnelle et pourra évoluer en fonction de l'avancement du projet.

---

## Organisation du dépôt

La structure du dépôt GitHub est prévue comme suit :

```text
quant-lab-b07-tlt/
│
├── README.md
├── app.py
├── requirements.txt
├── .gitignore
├── .env.example
│
├── data/
│   └── README.md
│
├── src/
│   ├── __init__.py
│   ├── data.py
│   ├── features.py
│   ├── risk.py
│   ├── strategy.py
│   ├── backtest.py
│   ├── paper.py
│   │
│   └── models/
│       └── __init__.py
│
├── notebooks/
│   └── .gitkeep
│
├── configs/
│   └── .gitkeep
│
├── tests/
│   └── test_structure.py
│
└── reports/
    └── .gitkeep
```
