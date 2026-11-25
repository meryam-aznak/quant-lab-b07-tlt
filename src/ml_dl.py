"""D05: chronological one-session return forecasts."""
from pathlib import Path
from time import perf_counter
import json
import numpy as np
import pandas as pd
import torch
from torch import nn
from sklearn.linear_model import Ridge
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'reports/D05'
SEED=42

def features(df):
    df=df.sort_index(); assert df.index.is_unique
    x=pd.DataFrame(index=df.index)
    for ticker in ['TLT','SPY']:
        r=df[ticker+'_return'].shift(1)
        for k in [1,2,3,5]: x[f'{ticker}_lag{k}']=r.shift(k-1)
        for w in [5,10,20]:
            x[f'{ticker}_mean{w}']=r.rolling(w).mean()
            x[f'{ticker}_vol{w}']=r.rolling(w).std()
        p=df[ticker+'_Adj_Close'].shift(1)
        x[f'{ticker}_momentum5']=p/p.shift(5)-1
        x[f'{ticker}_ma20']=p/p.rolling(20).mean()-1
    x['target']=df.TLT_return
    x['signal_date']=df.index.to_series().shift(1)
    return x.dropna()

class MLP:
    def __init__(self,hidden,epochs): self.hidden=hidden; self.epochs=epochs
    def fit(self,X,y):
        torch.manual_seed(SEED); torch.set_num_threads(1)
        self.s=StandardScaler().fit(X); self.sy=StandardScaler().fit(np.asarray(y).reshape(-1,1))
        a=torch.tensor(self.s.transform(X),dtype=torch.float32); b=torch.tensor(self.sy.transform(np.asarray(y).reshape(-1,1)),dtype=torch.float32)
        self.net=nn.Sequential(nn.Linear(a.shape[1],self.hidden),nn.ReLU(),nn.Linear(self.hidden,8),nn.ReLU(),nn.Linear(8,1))
        opt=torch.optim.Adam(self.net.parameters(),lr=.001,weight_decay=.001)
        g=torch.Generator().manual_seed(SEED)
        for _ in range(self.epochs):
            for i in torch.randperm(len(a),generator=g).split(64):
                opt.zero_grad(); loss=nn.functional.mse_loss(self.net(a[i]),b[i]); loss.backward(); opt.step()
        return self
    def predict(self,X):
        self.net.eval()
        with torch.no_grad(): p=self.net(torch.tensor(self.s.transform(X),dtype=torch.float32)).numpy()
        return self.sy.inverse_transform(p).ravel()

GRIDS={'Ridge':[{'alpha':a} for a in [1,10,100,1000]],'RandomForest':[{'max_depth':d,'min_samples_leaf':l,'n_estimators':100} for d in [3,6] for l in [10,30]],'MLP':[{'hidden':h,'epochs':e} for h in [8,16] for e in [20,60]]}
def make_model(n,p):
    if n=='Ridge': return make_pipeline(StandardScaler(),Ridge(**p))
    if n=='RandomForest': return RandomForestRegressor(**p,random_state=SEED,n_jobs=1)
    return MLP(**p)
def metrics(y,p):
    y=np.asarray(y); p=np.asarray(p)
    return dict(MAE=np.mean(abs(y-p)),RMSE=np.sqrt(np.mean((y-p)**2)),Direction_pct=100*np.mean(np.sign(y)==np.sign(p)))
def run():
    OUT.mkdir(parents=True,exist_ok=True)
    df=pd.read_csv(ROOT/'reports/20261119T182124Z/series_synchronisees.csv',parse_dates=['Date']).set_index('Date')
    data=features(df); train=data.loc[:'2022']; val=data.loc['2023':'2024']; test=data.loc['2025':'2026-10-30']; tv=pd.concat([train,val]); cols=list(data.drop(columns=['target','signal_date']))
    scores=[]; predictions=[]; tuning=[]; selected={}
    def record(split,part,name,p,ft=0.,pt=0.):
        scores.append(dict(split=split,model=name,**metrics(part.target,p),fit_seconds=ft,predict_seconds=pt))
        predictions.append(pd.DataFrame(dict(Date=part.index,signal_date=part.signal_date.values,split=split,model=name,actual=part.target.values,prediction=p)))
    d03=pd.read_csv(ROOT/'reports/D03/previsions_test.csv',parse_dates=['Date']).set_index('Date')
    assert test.index.equals(d03.index) and np.allclose(test.target,d03.TLT_return_reel,rtol=0,atol=1e-12)
    assert len(val)==502
    old=pd.read_csv(ROOT/'reports/D03/comparaison_validation.csv',index_col=0)
    scores.append(dict(split='validation',model='ARIMA',MAE=old.loc['ARIMA','MAE'],RMSE=old.loc['ARIMA','RMSE'],Direction_pct=old.loc['ARIMA','Direction (%)'],fit_seconds=np.nan,predict_seconds=np.nan))
    for split,part,hist in [('validation',val,train),('test',test,tv)]:
        record(split,part,'Naif',np.zeros(len(part)))
        record(split,part,'Moyenne historique',np.full(len(part),hist.target.mean()))
    def evaluate(n,p,hist,part):
        m=make_model(n,p); t=perf_counter(); m.fit(hist[cols],hist.target); ft=perf_counter()-t
        t=perf_counter(); pred=m.predict(part[cols]); pt=perf_counter()-t
        return pred,ft,pt
    for n,grid in GRIDS.items():
        candidates=[]
        for p in grid:
            pred,ft,pt=evaluate(n,p,train,val); met=metrics(val.target,pred)
            tuning.append(dict(model=n,params=json.dumps(p),**met,fit_seconds=ft,predict_seconds=pt)); candidates.append((met['RMSE'],p,pred,ft,pt))
        _,p,pred,ft,pt=min(candidates,key=lambda a:a[0]); selected[n]=p; record('validation',val,n,pred,ft,pt)
    champion=pd.DataFrame(scores).query("split == 'validation'").sort_values('RMSE').iloc[0].model
    config=dict(seed=SEED,selected=selected,champion_validation=champion,selection_metric='RMSE validation',features=cols,counts=dict(train=len(train),validation=len(val),test=len(test)),versions=dict(torch=torch.__version__,numpy=np.__version__,pandas=pd.__version__,sklearn=__import__('sklearn').__version__))
    (OUT/'configuration.json').write_text(json.dumps(config,indent=2),encoding='utf-8')
    record('test',test,'ARIMA',d03.prediction.values,np.nan,np.nan)
    for n,p in selected.items(): record('test',test,n,*evaluate(n,p,tv,test))
    s=pd.DataFrame(scores); f=pd.concat(predictions,ignore_index=True)
    s.to_csv(OUT/'comparaison.csv',index=False); f.to_csv(OUT/'previsions.csv',index=False); pd.DataFrame(tuning).to_csv(OUT/'hyperparametres.csv',index=False)
    ax=s.pivot(index='model',columns='split',values='RMSE').plot.bar(figsize=(10,5)); ax.set_ylabel('RMSE (rendement décimal)'); ax.set_title('TLT — comparaison hors échantillon'); plt.tight_layout(); plt.savefig(OUT/'comparaison.png',dpi=150); plt.close()
    fig,ax=plt.subplots(figsize=(12,5)); ax.plot(test.index,test.target*100,label='Réel',alpha=.35)
    for n in GRIDS:
        g=f[(f.split=='test')&(f.model==n)]; ax.plot(g.Date,g.prediction*100,label=n)
    ax.set_ylabel('Rendement (%)'); ax.set_title('TLT — prévisions à une séance'); ax.legend(); fig.tight_layout(); fig.savefig(OUT/'previsions_test.png',dpi=150); plt.close(fig)
    print(config); print(s.to_string(index=False))
if __name__=='__main__': run()
