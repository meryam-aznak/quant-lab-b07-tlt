# D02 — Dictionnaire des données (B07 TLT)

| Colonne | Type | Définition | Contrôle |
|---|---|---|---|
| Date | date YYYY-MM-DD | Date de séance boursière américaine | Valide, unique par ticker, ordonnée après préparation |
| Ticker | texte | TLT ou SPY | Appartient à {TLT, SPY} |
| Open | float USD/part | Prix d'ouverture non ajusté | > 0 |
| High | float USD/part | Plus haut intrajournalier non ajusté | >= Open, Close, Low |
| Low | float USD/part | Plus bas intrajournalier non ajusté | <= Open, Close, High |
| Close | float USD/part | Prix de clôture non ajusté | > 0 |
| Adj Close | float USD/part | Prix de clôture ajusté fourni par la source | > 0, convention source à vérifier |
| Volume | nombre | Volume de parts échangées | >= 0 |
| TLT_return | float décimal | AdjClose(TLT,t) / AdjClose(TLT,t-1) - 1 | 0.01 = 1 % |
| SPY_return | float décimal | AdjClose(SPY,t) / AdjClose(SPY,t-1) - 1 | 0.01 = 1 % |

**Important :** `High`, `Low`, `Open` et `Close` sont non ajustés tandis que `Adj Close` est ajusté. Ne pas comparer directement les valeurs ajustées aux bornes OHLC non ajustées. Les distributions et changements de convention de la source doivent être documentés avant toute interprétation en rendement total.

**Moment de disponibilité :** les valeurs OHLCV de la séance t ne sont complètes qu'après sa clôture. Une décision produite après clôture t ne pourra être exécutée qu'au plus tôt à l'ouverture t+1.
