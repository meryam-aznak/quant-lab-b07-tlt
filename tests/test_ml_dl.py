import numpy as np
import pandas as pd
from src.ml_dl import features,make_model

def test_causal_features():
    idx=pd.date_range('2020-01-01',periods=70); r=np.random.default_rng(42).normal(0,.01,70)
    df=pd.DataFrame({'TLT_return':r,'SPY_return':r/2,'TLT_Adj_Close':100*np.cumprod(1+r),'SPY_Adj_Close':100*np.cumprod(1+r/2)},index=idx)
    t=idx[40]; changed=df.copy(); changed.loc[t:]*=2
    pd.testing.assert_series_equal(features(df).loc[t].drop('target'),features(changed).loc[t].drop('target'))
    assert features(df).loc[t,'signal_date']<t

def test_scaling():
    x=np.arange(20).reshape(10,2); m=make_model('Ridge',{'alpha':10}).fit(x,np.arange(10)); np.testing.assert_allclose(m[0].mean_,x.mean(axis=0))

def test_mlp_seed():
    x=np.arange(40).reshape(20,2); y=np.arange(20)/1000; p={'hidden':8,'epochs':2}
    np.testing.assert_allclose(make_model('MLP',p).fit(x,y).predict(x),make_model('MLP',p).fit(x,y).predict(x))
