# D04 — Module de risque | Quant Lab B07 – TLT

## 1. Objectif

Ce livrable prolonge D03 (économétrie de la moyenne) par la modélisation du risque de l’ETF TLT, exposé aux obligations du Trésor américain à duration longue. Il vise à prévoir la volatilité à une séance, à estimer la Value at Risk (VaR) et l’Expected Shortfall (ES), puis à vérifier ces prévisions hors échantillon.

**Question B07 :** Une bonne prévision statistique conduit-elle nécessairement à un meilleur trading d’un actif sensible aux taux ?

Le module prépare la comparaison entre une stratégie directionnelle et une stratégie filtrée par le risque (D06). Il ne constitue pas encore un moteur de trading.

## 2. Installation et exécution

Prérequis : Python 3.11+, livrables D02 et D03 intégrés au dépôt, notamment `requirements_d03.txt` et le snapshot `reports/20261119T182124Z/series_synchronisees.csv`.

Depuis la racine du dépôt :

```bash
python -m pip install -r requirements_d04.txt
python -m src.risk
python -m pytest tests/test_risk.py -v
```

Le module fonctionne sur le snapshot local, sans téléchargement de nouvelles données ni connexion à un courtier. Les résultats sont régénérés dans `reports/D04/`.

## 3. Structure des fichiers

```text
src/risk.py                         # Modélisation et évaluation du risque
tests/test_risk.py                   # Tests automatisés
requirements_d04.txt                # Dépendances (inclut D03)
reports/D04/
├── README.md                       # Ce document (emplacement conseillé)
├── diagnostics.csv                 # ARCH-LM et Ljung-Box
├── parametres.csv                   # Paramètres GARCH
├── previsions_risque.csv            # Prévisions datées et réalisations
├── verification.csv                # MSE, couverture VaR et contrôle ES
├── risque_test.png                  # Graphiques hors échantillon
└── rapport_risque.md                # Analyse scientifique détaillée
```

## 4. Méthodologie

1. Charger les rendements journaliers TLT du snapshot D02 du 19/11/2026, avec le même échantillon que D03.
2. Estimer ARIMA(1,0,1) pour la moyenne et récupérer ses résidus.
3. Appliquer le test ARCH-LM à 10 retards pour détecter une variance conditionnelle non constante.
4. Estimer GARCH(1,1) par maximum de vraisemblance gaussienne avec SciPy : `h[t] = omega + alpha * e[t-1]² + beta * h[t-1]`.
5. Calculer la volatilité conditionnelle ainsi que la VaR et l’ES à 95 % et 99 %, sous hypothèse normale.
6. Vérifier les résidus standardisés, comparer la variance prévue à un proxy observé (erreur ARIMA au carré) et contrôler les violations de VaR et la sévérité des pertes.

### Protocole temporel

| Phase | Historique d’estimation | Évaluation | Séances évaluées |
|---|---|---|---:|
| Validation | 2018–2022 | 2023–2024 | 502 |
| Test final | 2018–2024 | 01/01/2025–30/10/2026 | 459 |

Les paramètres restent fixes dans chaque fenêtre d’évaluation. L’état ARIMA et la variance sont actualisés après observation du rendement réalisé. Chaque prévision à une séance est produite avant la réalisation correspondante ; `signal_date` précède `Date`.

### Unités et conventions

Les résidus utilisés pour GARCH sont exprimés en points de pourcentage ; la variance interne est en points de pourcentage au carré. Les exports utilisent des rendements décimaux : 0,01 correspond à 1 %. La VaR et l’ES sont exprimées en pertes signées à une séance sur une exposition TLT. Une violation survient lorsque `-return_actual > VaR`. Ces mesures ne représentent pas encore le risque d’un portefeuille simulé.

## 5. Résultats

### Diagnostics ARCH-LM

Les libellés validation et test désignent ici les historiques d’estimation associés, et non des diagnostics calculés sur les observations futures.

| Historique | p-value ARIMA | p-value GARCH standardisé |
|---|---:|---:|
| 2018–2022 | 1,896 × 10⁻⁸⁶ | 0,9823 |
| 2018–2024 | 3,083 × 10⁻¹⁰⁹ | 0,9738 |

L’effet ARCH significatif des résidus ARIMA n’est plus détecté après standardisation GARCH au seuil de 5 %. Le test Ljung-Box des résidus standardisés indique toutefois une dépendance linéaire résiduelle sur l’historique initial (p = 0,00986).

### Paramètres GARCH finaux

| Paramètre | Valeur approximative |
|---|---:|
| Omega (points de pourcentage²) | 0,01973 |
| Alpha | 0,09353 |
| Beta | 0,88787 |
| Alpha + Beta | 0,98140 |

La persistance élevée indique que les chocs de volatilité se dissipent progressivement.

### Prévision de variance

| Période | MSE GARCH | MSE variance constante |
|---|---:|---:|
| Validation | 2,409496 × 10⁻⁸ | 2,423887 × 10⁻⁸ |
| Test | 6,822984 × 10⁻⁹ | 9,982741 × 10⁻⁹ |

Sur le test final, GARCH réduit la MSE d’environ 31,65 % par rapport à la référence constante. Le gain est plus faible en validation.

### Couverture VaR et contrôle ES

| Période | Niveau | Violations | Attendues | p binomiale | ES moyenne* | Perte moyenne* |
|---|---:|---:|---:|---:|---:|---:|
| Validation | 95 % | 29 | 25,10 | 0,411859 | 1,867 % | 1,930 % |
| Validation | 99 % | 9 | 5,02 | 0,107512 | 2,325 % | 2,306 % |
| Test | 95 % | 15 | 22,95 | 0,106636 | 1,490 % | 1,607 % |
| Test | 99 % | 4 | 4,59 | 1,000000 | 1,867 % | 2,012 % |

*Sur les jours de violation de la VaR correspondante.*

Le test binomial ne rejette pas la couverture nominale au seuil de 5 %, sous hypothèse d’indépendance. L’ES sous-estime légèrement la perte moyenne observée lors des violations sur le test final.

### Visualisation

![Prévisions de volatilité, VaR et ES sur le test final](risque_test.png)

## 6. Tests et reproductibilité

Exécution locale confirmée : **2 tests réussis** en 4,64 s.

- `test_causal_variance` : vérification de la causalité du calcul de variance.
- `test_risk_units` : vérification des unités des mesures de risque.

Les 22 avertissements `Pandas4Warning` observés proviennent de fonctions dépréciées utilisées par statsmodels ; ils n’ont pas empêché l’exécution. Un environnement virtuel avec des versions compatibles et figées est recommandé pour la reproductibilité finale (D09).

## 7. Conclusion et limites

GARCH(1,1) complète ARIMA en modélisant la dynamique du risque. Les résultats soutiennent son utilisation comme composante d’une future stratégie filtrée par le risque. Ils ne démontrent pas encore une amélioration de la performance économique du trading.

L’hypothèse normale peut sous-estimer les pertes extrêmes. Le carré de l’erreur ARIMA est un proxy bruité de la variance latente. Le contrôle ES est descriptif et le test binomial ne vérifie pas l’indépendance des violations. Le faible nombre de violations à 99 % limite également la portée des conclusions.

La valeur économique du filtre sera évaluée au D06 avec des règles de décision fixées hors test, les coûts de transaction, les contraintes long/cash et l’exécution au plus tôt à l’ouverture suivante.

Pour l’analyse détaillée, consulter [rapport_risque.md](rapport_risque.md).
