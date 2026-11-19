"""D02 B07: collecter, conserver, contrôler et visualiser les séries TLT/SPY."""
from __future__ import annotations
import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
FIELDS = ['Open', 'High', 'Low', 'Close', 'Adj Close', 'Volume']


def normalize(raw: pd.DataFrame, ticker: str) -> pd.DataFrame:
    """Uniformise un CSV Yahoo/yfinance ou un DataFrame yfinance."""
    df = raw.copy()
    if isinstance(df.columns, pd.MultiIndex):
        if ticker in df.columns.get_level_values(-1):
            df = df.xs(ticker, axis=1, level=-1)
        else:
            df.columns = df.columns.get_level_values(0)
    if 'Date' not in df.columns:
        df = df.reset_index()
    if 'Datetime' in df.columns and 'Date' not in df.columns:
        df = df.rename(columns={'Datetime':'Date'})
    if 'Date' not in df.columns:
        raise ValueError('Colonne Date introuvable')
    if 'Adj Close' not in df.columns:
        raise ValueError('Adj Close absent : conserver des prix ajustés est nécessaire pour le protocole choisi')
    missing = [x for x in FIELDS if x not in df.columns]
    if missing:
        raise ValueError(f'Colonnes manquantes pour {ticker}: {missing}')
    df = df[['Date'] + FIELDS].copy()
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce').dt.tz_localize(None).dt.normalize()
    for col in FIELDS:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    df['Ticker'] = ticker
    return df[['Date','Ticker'] + FIELDS]


def download(ticker: str, start: str, end_exclusive: str) -> pd.DataFrame:
    try:
        import yfinance as yf
    except ImportError as exc:
        raise RuntimeError('Installez les dépendances: pip install -r requirements.txt') from exc
    raw = yf.Ticker(ticker).history(start=start, end=end_exclusive, auto_adjust=False, actions=False, timeout=30)
    if raw.empty:
        raise RuntimeError(f'Aucune donnée reçue pour {ticker}')
    return normalize(raw, ticker)


def audit(df: pd.DataFrame, ticker: str) -> tuple[dict, pd.DataFrame]:
    d = df.copy()
    d['Date'] = pd.to_datetime(d['Date'], errors='coerce')
    invalid_date = d['Date'].isna()
    duplicates = d.duplicated('Date', keep=False) & ~invalid_date
    numeric = FIELDS
    missing_numeric = d[numeric].isna().any(axis=1)
    bad_prices = (d[['Open','High','Low','Close','Adj Close']] <= 0).any(axis=1)
    bad_volume = d['Volume'] < 0
    high_low = (d['High'] < d['Low']) | (d['High'] < d[['Open','Close']].max(axis=1)) | (d['Low'] > d[['Open','Close']].min(axis=1))
    ordered = d.sort_values('Date').copy()
    ordered['adjusted_return'] = ordered['Adj Close'].pct_change(fill_method=None)
    extreme = ordered['adjusted_return'].abs() > 0.20  # alerte de revue, pas suppression automatique
    flagged = pd.DataFrame({'Date':d['Date'], 'Ticker':ticker,
        'invalid_date':invalid_date, 'duplicate_date':duplicates,
        'missing_numeric':missing_numeric, 'nonpositive_price':bad_prices,
        'negative_volume':bad_volume, 'ohlc_inconsistent':high_low})
    extreme_dates = set(ordered.loc[extreme, 'Date'].dropna())
    flagged['extreme_adjusted_return_over_20pct'] = flagged['Date'].isin(extreme_dates)
    issue_cols = [c for c in flagged.columns if c not in ('Date','Ticker')]
    flagged = flagged.loc[flagged[issue_cols].any(axis=1)].copy()
    stats = {'ticker':ticker, 'rows':int(len(d)), 'first_date':str(d['Date'].min().date()) if d['Date'].notna().any() else None,
        'last_date':str(d['Date'].max().date()) if d['Date'].notna().any() else None,
        'missing_by_column':{c:int(d[c].isna().sum()) for c in numeric},
        'issue_counts':{c:int(flagged[c].sum()) for c in issue_cols},
        'flagged_rows':int(len(flagged)),
        'weekend_rows':int((d['Date'].dt.day_of_week >= 5).sum())}
    return stats, flagged


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def plot_series(dfs: dict[str,pd.DataFrame], dest: Path) -> None:
    fig, axes = plt.subplots(2, 1, figsize=(11, 8), sharex=True)
    for ticker, df in dfs.items():
        ordered = df.dropna(subset=['Date','Adj Close']).sort_values('Date').drop_duplicates('Date')
        if ordered.empty: continue
        base = ordered['Adj Close'].iloc[0]
        axes[0].plot(ordered['Date'], 100 * ordered['Adj Close'] / base, label=ticker)
        ret = ordered['Adj Close'].pct_change(fill_method=None)
        axes[1].plot(ordered['Date'], ret * 100, label=ticker, linewidth=.65, alpha=.8)
    axes[0].set_title('TLT et SPY — indices de prix ajustés (base 100)')
    axes[0].set_ylabel('Indice (base 100)')
    axes[1].set_title('Rendements journaliers calculés sur prix ajustés')
    axes[1].set_ylabel('Rendement (%)')
    axes[1].set_xlabel('Date')
    for ax in axes:
        ax.grid(alpha=.2); ax.legend()
    fig.tight_layout(); fig.savefig(dest, dpi=160); plt.close(fig)


def run(args: argparse.Namespace) -> Path:
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    folder = ROOT/'data'/'snapshots'/stamp
    folder.mkdir(parents=True, exist_ok=False)
    reports = ROOT/'reports'/stamp
    reports.mkdir(parents=True, exist_ok=True)
    frames = {}
    provenance = {'acquired_at_utc':stamp, 'source': 'Yahoo Finance via yfinance' if args.mode=='download' else 'CSV utilisateur (source à préciser)',
        'mode':args.mode, 'frequency':'daily', 'market_timezone':'America/New_York',
        'date_storage':'date de séance (YYYY-MM-DD)', 'adjustment':'Adj Close de la source pour rendements de prix ajustés; OHLC bruts',
        'start_inclusive':args.start, 'end_exclusive':args.end, 'files':{}}
    for ticker in ['TLT','SPY']:
        if args.mode=='download':
            df = download(ticker,args.start,args.end)
        else:
            path = ROOT/'data'/'raw'/f'{ticker.lower()}.csv'
            if not path.exists():
                raise FileNotFoundError(f'Fichier requis pour import : {path}')
            df = normalize(pd.read_csv(path), ticker)
        if df.empty: raise RuntimeError(f'Données vides pour {ticker}')
        frames[ticker] = df
        out = folder/f'{ticker.lower()}.csv'
        df.to_csv(out,index=False,date_format='%Y-%m-%d')
        provenance['files'][ticker]={'path':str(out.relative_to(ROOT)), 'sha256':sha256(out), 'rows':len(df)}
    (folder/'provenance.json').write_text(json.dumps(provenance,indent=2,ensure_ascii=False),encoding='utf-8')
    stats, issues = {}, []
    for ticker,df in frames.items():
        stat, flagged = audit(df,ticker)
        stats[ticker]=stat; issues.append(flagged)
    all_issues = pd.concat(issues,ignore_index=True)
    all_issues.to_csv(reports/'anomalies.csv',index=False)
    dates = [set(df['Date'].dropna()) for df in frames.values()]
    overlap = sorted(dates[0].intersection(dates[1]))
    only_tlt = len(dates[0]-dates[1]); only_spy = len(dates[1]-dates[0])
    stats['synchronisation']={'common_sessions':len(overlap),'only_tlt':only_tlt,'only_spy':only_spy}
    stats['snapshot']=stamp
    (reports/'audit.json').write_text(json.dumps(stats,indent=2,ensure_ascii=False),encoding='utf-8')
    plot_series(frames,reports/'coherence.png')
    # Série commune uniquement, sans imputation de séances absentes
    merged = frames['TLT'][['Date','Adj Close']].rename(columns={'Adj Close':'TLT_Adj_Close'}).merge(
        frames['SPY'][['Date','Adj Close']].rename(columns={'Adj Close':'SPY_Adj_Close'}),on='Date',how='inner')
    merged=merged.sort_values('Date').drop_duplicates('Date')
    merged['TLT_return']=merged['TLT_Adj_Close'].pct_change(fill_method=None)
    merged['SPY_return']=merged['SPY_Adj_Close'].pct_change(fill_method=None)
    merged.to_csv(reports/'series_synchronisees.csv',index=False,date_format='%Y-%m-%d')
    lines=['# D02 — Rapport automatique d’audit', '',f'Snapshot UTC : `{stamp}`','',
        '## Résultats','', '| Contrôle | TLT | SPY |','|---|---:|---:|',
        f"| Lignes | {stats['TLT']['rows']} | {stats['SPY']['rows']} |",
        f"| Lignes signalées | {stats['TLT']['flagged_rows']} | {stats['SPY']['flagged_rows']} |",
        f"| Dates du week-end | {stats['TLT']['weekend_rows']} | {stats['SPY']['weekend_rows']} |",
        '',f"Séances communes : **{len(overlap)}** ; dates TLT seules : **{only_tlt}** ; dates SPY seules : **{only_spy}**.",
        '', 'Les anomalies détaillées sont dans `anomalies.csv` et le graphique dans `coherence.png`.',
        '', 'Les rendements >20 % en valeur absolue sont des alertes à examiner, pas des erreurs confirmées.',
        'Les jours fériés et les week-ends ne sont pas automatiquement considérés comme des données manquantes.',
        'La vérification des distributions et ajustements de la source reste à documenter.',
        '', '## Conclusion à compléter après examen humain',
        'Indiquer les anomalies expliquées, corrections éventuelles, limites et décision de validation du snapshot.']
    (reports/'rapport_audit.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(f'Snapshot : {folder}\nRapport : {reports}\nLignes signalées : TLT={stats["TLT"]["flagged_rows"]}, SPY={stats["SPY"]["flagged_rows"]}')
    return reports

if __name__=='__main__':
    parser=argparse.ArgumentParser(description='D02: collecte, snapshot, audit et graphiques TLT/SPY')
    parser.add_argument('--mode',choices=['download','import'],default='download')
    parser.add_argument('--start',default='2018-01-01')
    parser.add_argument('--end',default='2026-10-31',help='Date de fin exclusive')
    run(parser.parse_args())
