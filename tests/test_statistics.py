import numpy as np
import pandas as pd
import pytest
from scipy import stats
from statsmodels.stats.multitest import multipletests
from ephys_stats import prepare, unit_means, pairwise, adjust_family, mixed_model
from ephys_io import read_table


def example():
    return pd.DataFrame({'value':[1.,2,4,7,4,6,7,12], 'condition':['A']*4+['B']*4,
                         'animal':['a','b','c','d','e','f','g','h']})


def test_welch_matches_reference_and_direction():
    d=example()
    r=pairwise(d,'value','condition','animal').iloc[0]
    expected=stats.ttest_ind([4,6,7,12],[1,2,4,7],equal_var=False)
    assert r.p_raw == pytest.approx(expected.pvalue)
    assert r.estimate == pytest.approx(3.75)
    ci=expected.confidence_interval()
    assert r.ci_low == pytest.approx(ci.low)
    assert r.ci_high == pytest.approx(ci.high)


def test_repeated_rows_do_not_inflate_independent_n():
    d=example(); r=pairwise(pd.concat([d,d.iloc[:4],d.iloc[:4]]),'value','condition','animal').iloc[0]
    assert r.n_reference==4
    assert r.p_raw==pytest.approx(pairwise(d,'value','condition','animal').iloc[0].p_raw)


def test_paired_alignment_by_identifier_and_complete_pairs():
    d=pd.DataFrame({'condition':['A']*4+['B']*3,'animal':['1','2','3','4','3','1','2'],'value':[1.,3,7,9,9,4,5]})
    r=pairwise(d,'value','condition','animal','paired_t').iloc[0]
    assert r.n_reference==3
    assert r.unmatched_units==1
    assert r.estimate==pytest.approx(np.mean([3,2,2]))
    assert r.p_raw==pytest.approx(stats.ttest_rel([4,5,9],[1,3,7]).pvalue)


def test_same_id_in_independent_conditions_rejected():
    d=example();d.loc[4,'animal']='a'
    with pytest.raises(ValueError,match='apparié'):
        prepare(d,'value','condition','animal',independent=True)


def test_holm_family_across_all_outcomes():
    d=pd.DataFrame({'p_raw':[.01,.04,np.nan,.03], 'status':['ok','ok','failed','ok']})
    r=adjust_family(d)
    np.testing.assert_allclose(r.p_adjusted.iloc[[0,1,3]],multipletests([.01,.04,.03],method='holm')[1])
    assert r.family_size.eq(3).all()
    assert np.isnan(r.p_adjusted.iloc[2])


def test_csv_semicolon_decimal_and_comma_preserve_values():
    d=read_table('Condition;Animal_ID;Mesure\nA;S1;2,5\nB;S2;4,2\n'.encode())
    assert d.Mesure.tolist()==[2.5,4.2]
    assert read_table(b'File,value\na,1\nb,2\n').value.tolist()==[1,2]


def test_degenerate_variance_not_reported_as_significant():
    d=example();d['value']=1.
    r=pairwise(d,'value','condition','animal').iloc[0]
    assert r.status=='zero_variance'
    assert np.isnan(r.p_raw)


def test_nested_mixed_model_recovers_known_condition_effect():
    rng=np.random.default_rng(113)
    rows=[]
    for animal in range(30):
        condition='A' if animal<15 else 'B'
        animal_effect=rng.normal(0, .7)
        for cell in range(3):
            cell_effect=rng.normal(0,.4)
            for x in [-1.,0.,1.]:
                y=5+2*(condition=='B')+.6*x+animal_effect+cell_effect+rng.normal(0,.25)
                rows.append((str(animal),str(cell),condition,x,y))
    d=pd.DataFrame(rows,columns=['animal','cell','condition','time','value'])
    r,c,diag,notes=mixed_model(d,'value','condition','animal',nested='cell',x='time')
    assert r.estimate.iloc[0]==pytest.approx(2., abs=.8)
    assert r.ci_low.iloc[0] < 2 < r.ci_high.iloc[0]
    assert len(diag)==len(d)
    assert 'C(condition)[T.B]:x' in c.term.tolist()
    assert np.isfinite(diag.residual).all()
