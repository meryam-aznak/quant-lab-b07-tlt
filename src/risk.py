"""D04: one-day conditional risk, with fixed parameters and causal updates."""
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.optimize import minimize
from scipy.stats import norm, chi2, binomtest
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.stats.diagnostic import het_arch, acorr_ljungbox
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
CSV = ROOT / 'reports/20261119T182124Z/series_synchronisees.csv'
OUT = ROOT / 'reports/D04'

def variance(e, p, initial):
    w,a,b = p
    h = np.empty(len(e)); h[0] = initial
    for i in range(1,len(e)):
        h[i] = w+a*e[i-1]**2+b*h[i-1]
    return h

def fit_garch(e):
    initial = float(np.var(e))
    def loss(p):
        h = variance(e,p,initial)
        return .5*np.sum(np.log(h)+e**2/h)
    fits = [minimize(loss,[initial*.05,a,b],method='SLSQP',bounds=[(1e-8,None),(0,.999),(0,.999)],constraints=[{'type':'ineq','fun':lambda p:.999-p[1]-p[2]}],options={'maxiter':1000,'ftol':1e-9}) for a,b in [( .05,.9),(.1,.8),(.2,.6)]]
    good = [f for f in fits if f.success and np.isfinite(f.fun)]
    if not good: raise RuntimeError('GARCH optimization failed')
    return min(good,key=lambda f:f.fun).x, initial

def risk_limits(mu,sigma,alpha):
    z=norm.ppf(alpha)
    return -mu-sigma*z, -mu+sigma*norm.pdf(z)/alpha

def run():
    OUT.mkdir(parents=True,exist_ok=True)
    df=pd.read_csv(CSV,parse_dates=['Date']).set_index('Date').sort_index()
    # Same sample as D03: SPY lag removes one additional initial row.
    df['SPY_lag1']=df.SPY_return.shift(1)
    y=df.dropna(subset=['TLT_return','SPY_lag1']).TLT_return
    scores=[]; diagnostics=[]; params=[]; outputs=[]
    for split,cut,end in [('validation','2022-12-31','2024-12-31'),('test','2024-12-31','2026-10-30')]:
        hist=y.loc[:cut]; future=y.loc[(y.index>cut)&(y.index<=end)]
        fit=ARIMA(hist.reset_index(drop=True),order=(1,0,1),trend='c').fit()
        if not fit.mle_retvals.get('converged',False): print('Warning: ARIMA convergence',split)
        e=np.asarray(fit.resid)*100
        p,initial=fit_garch(e)
        h=variance(e,p,initial); z=e/np.sqrt(h)
        for label,series in [('ARIMA',e),('GARCH_standardises',z)]:
            lm,pv,_,_=het_arch(series,nlags=10,ddof=2 if label=='ARIMA' else 0)
            diagnostics.append(dict(split=split,residus=label,ARCH_LM=lm,ARCH_p=pv,LB_p=acorr_ljungbox(series,lags=[10],return_df=True).lb_pvalue.iloc[0],LB_carres_p=acorr_ljungbox(series**2,lags=[10],return_df=True).lb_pvalue.iloc[0]))
        params.append(dict(split=split,omega_pct2=p[0],alpha=p[1],beta=p[2],persistance=p[1]+p[2],arima_converged=fit.mle_retvals.get('converged',False)))
        # Fixed ARIMA parameters; each one-step forecast is produced before observing the return.
        state=fit; prev_e=e[-1]; prev_h=h[-1]; rows=[]
        for date,r in future.items():
            mu=float(state.forecast(1).iloc[0]); ht=p[0]+p[1]*prev_e**2+p[2]*prev_h
            sigma=np.sqrt(ht)/100; v95,es95=risk_limits(mu,sigma,.05); v99,es99=risk_limits(mu,sigma,.01)
            rows.append(dict(Date=date,split=split,signal_date=y.index[y.index.get_loc(date)-1],return_actual=r,mean_forecast=mu,volatility=sigma,variance_forecast=sigma**2,variance_proxy=(r-mu)**2,constant_variance=initial/10000,VaR95=v95,ES95=es95,VaR99=v99,ES99=es99,breach95=int(-r>v95),breach99=int(-r>v99)))
            prev_e=(r-mu)*100; prev_h=ht
            state=state.extend(pd.Series([r],index=[state.nobs if state is fit else len(hist)+len(rows)-1]))
        f=pd.DataFrame(rows); outputs.append(f)
        for level,prob in [(95,.05),(99,.01)]:
            hit=f[f[f'breach{level}']==1]; n=len(f); k=len(hit)
            scores.append(dict(split=split,level=level,n=n,violations=k,expected=n*prob,rate=k/n,binomial_p=binomtest(k,n,prob).pvalue,mean_realized_tail_loss=(-hit.return_actual).mean(),mean_ES_on_breaches=hit[f'ES{level}'].mean(),variance_MSE=((f.variance_forecast-f.variance_proxy)**2).mean(),constant_MSE=((f.constant_variance-f.variance_proxy)**2).mean()))
    allf=pd.concat(outputs,ignore_index=True)
    for name,frame in [('previsions_risque',allf),('diagnostics',pd.DataFrame(diagnostics)),('parametres',pd.DataFrame(params)),('verification',pd.DataFrame(scores))]: frame.to_csv(OUT/f'{name}.csv',index=False)
    f=allf[allf.split=='test']; fig,ax=plt.subplots(2,1,figsize=(12,7),sharex=True)
    ax[0].plot(f.Date,np.sqrt(f.variance_proxy)*100,alpha=.35,label='Erreur absolue observée'); ax[0].plot(f.Date,f.volatility*100,label='Volatilité prévue'); ax[0].set_ylabel('% par séance'); ax[0].legend()
    ax[1].plot(f.Date,-f.return_actual*100,alpha=.5,label='Perte réalisée'); ax[1].plot(f.Date,f.VaR95*100,label='VaR 95%'); ax[1].plot(f.Date,f.ES95*100,label='ES 95%'); ax[1].set_ylabel('% du capital exposé'); ax[1].legend(); fig.suptitle('TLT — risque hors échantillon, test 2025–2026'); fig.tight_layout(); fig.savefig(OUT/'risque_test.png',dpi=150); plt.close(fig)
    print(pd.DataFrame(diagnostics).to_string(index=False)); print(pd.DataFrame(scores).to_string(index=False))

if __name__=='__main__': run()
