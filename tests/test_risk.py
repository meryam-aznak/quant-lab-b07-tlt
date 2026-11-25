import numpy as np
from src.risk import variance, risk_limits

def test_causal_variance():
    p=[.1,.1,.8]; e=np.array([1.,2.,3.]); h=variance(e,p,1.)
    assert np.allclose(h,[1.,1.,1.3])
    e[-1]=100
    assert np.allclose(variance(e,p,1.),h)

def test_risk_units():
    v,es=risk_limits(0,.01,.05)
    assert np.isclose(v,.016448536,rtol=1e-6)
    assert es>v>0
    assert risk_limits(0,.01,.01)[0]>v
