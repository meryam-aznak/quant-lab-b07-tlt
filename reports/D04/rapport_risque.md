# D04 — Module de risque : TLT (B07)

## Protocole
Données synchronisées du snapshot D02 du 19 novembre 2026 ; mêmes observations que D03. ARIMA(1,0,1) pour la moyenne ; GARCH(1,1) sur ses résidus multipliés par 100, estimé par maximum de vraisemblance gaussienne avec SciPy. Validation 2023–2024 après estimation 2018–2022 ; test 2025–30/10/2026 après estimation 2018–2024. Paramètres fixes dans chaque période, état ARIMA et variance actualisés après chaque réalisation. La date de signal précède la date cible. Les prévisions de moyenne du test concordent avec D03 à 6e-14 près.

## Modèle et unités
h(t)=omega+alpha*epsilon(t-1)^2+beta*h(t-1). Les résidus internes sont en points de pourcentage, h en points de pourcentage au carré ; les exports reviennent aux rendements décimaux (volatilité = sqrt(h)/100). VaR et ES représentent des pertes signées sur une séance sous hypothèse normale : VaR=-mu-sigma*z_a, ES=-mu+sigma*phi(z_a)/a. Une violation survient si -rendement réel > VaR. Ces mesures concernent une exposition TLT, pas encore un portefeuille simulé.

## Diagnostics
ARCH-LM à 10 retards sur les résidus ARIMA d'entraînement : p=1,90e-86, donc rejet de l'absence d'effet ARCH. Après GARCH, p=0,9823 ; aucun effet ARCH résiduel détecté à ce seuil. Ljung-Box sur les résidus standardisés : p=0,00986, ce qui indique une dépendance linéaire résiduelle sur l'entraînement initial. Les paramètres du modèle final sont omega=0,01973, alpha=0,09353, beta=0,88787 ; persistance=0,98140. Les diagnostics du modèle final portent sur 2018–2024, non sur le test.

## Vérification hors échantillon
| Période | Niveau | Séances | Violations | Attendues | p binomiale | Perte moyenne lors des violations | ES moyenne lors des violations |
|---|---|---:|---:|---:|---:|---:|---:|
| Validation | 95% | 502 | 29 | 25,10 | 0,412 | 1,930% | 1,867% |
| Validation | 99% | 502 | 9 | 5,02 | 0,108 | 2,306% | 2,325% |
| Test | 95% | 459 | 15 | 22,95 | 0,107 | 1,607% | 1,490% |
| Test | 99% | 459 | 4 | 4,59 | 1,000 | 2,012% | 1,867% |

Le test binomial exact ne rejette pas la couverture nominale à 5%, sous hypothèse d'indépendance des violations ; il ne démontre ni indépendance ni calibration parfaite. La VaR 95% est plutôt conservatrice sur le test. La MSE de variance (proxy : carré de l'erreur de prévision ARIMA) est 6,823e-9 contre 9,983e-9 pour la variance constante estimée sur l'historique. La perte moyenne des violations dépasse l'ES moyenne correspondante sur le test ; prudence notamment à 99% (quatre violations). Ce contrôle descriptif ne constitue pas un test formel de calibration ES.

## Conclusion et limites
Le GARCH capture la dynamique de volatilité et améliore la prévision de variance face à une référence constante sur le test. L'hypothèse normale peut sous-estimer les queues ; les rendements au carré sont un proxy bruité du risque latent. La valeur économique d'un filtre de risque reste à démontrer au D06, en intégrant frais et exécution à l'ouverture suivante. Aucune règle de trading n'est sélectionnée sur le test.

Reproduction depuis la racine : `python -m pip install -r requirements_d04.txt`, `python -m src.risk`, `python -m pytest tests/test_risk.py -v`.
