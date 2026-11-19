import pandas as pd
from src.data import audit, normalize

def sample():
    return pd.DataFrame({'Date':['2026-01-05','2026-01-06'],'Open':[100,101],'High':[102,102],
        'Low':[99,100],'Close':[101,101.5],'Adj Close':[100.8,101.3],'Volume':[1000,1100]})

def test_normalize():
    result=normalize(sample(),'TLT')
    assert len(result)==2 and set(result.Ticker)=={'TLT'}

def test_duplicate_detection():
    d=normalize(pd.concat([sample(),sample().iloc[[0]]],ignore_index=True),'TLT')
    stats,issues=audit(d,'TLT')
    assert stats['issue_counts']['duplicate_date']==2
    assert len(issues)>=2

def test_bad_ohlc():
    d=sample();d.loc[0,'High']=98
    stats,_=audit(normalize(d,'TLT'),'TLT')
    assert stats['issue_counts']['ohlc_inconsistent']==1
