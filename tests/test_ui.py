"""UI-level regression for table imports, exports and cache invalidation."""
from pathlib import Path
from streamlit.testing.v1 import AppTest

ROOT=Path(__file__).resolve().parents[1]


def loaded(page, payloads):
    script=f'''
import streamlit as st
from streamlit.delta_generator import DeltaGenerator
from types import SimpleNamespace
from pathlib import Path
root=Path({str(ROOT)!r})
page={page!r}
uploads=[SimpleNamespace(name=n,getvalue=lambda p=p:p) for n,p in {payloads!r}]
old, old_dg=st.file_uploader, DeltaGenerator.file_uploader
st.file_uploader=lambda *a,**kw: uploads if kw.get('accept_multiple_files') else uploads[0]
DeltaGenerator.file_uploader=lambda self,*a,**kw: uploads if kw.get('accept_multiple_files') else uploads[0]
try:
    exec(compile((root/page).read_text(),str(root/page),'exec'),dict(__file__=str(root/page),__name__='__main__'))
finally:
    st.file_uploader, DeltaGenerator.file_uploader=old,old_dg
'''
    return AppTest.from_string(script,default_timeout=60).run()


def test_curve_uploads_and_student_intervals_render():
    curve=b'I_inj,Nb_Spikes,V_steady,Current_Unit\n-50,0,-75,pA\n0,0,-65,pA\n50,5,-45,pA\n'
    app=loaded('6_📈_Averaged_Curves.py',[('cell1.csv',curve),('cell2.csv',curve.replace(b',5,',b',8,'))])
    assert not app.exception
    assert not app.error
    summary=app.dataframe[-1].value
    assert summary.N.eq(2).all()
    assert summary.loc[summary.I_inj.eq(50),'Nb_Spikes_Mean'].iloc[0]==6.5
    assert len(app.get('download_button'))==1


def test_statistics_compute_then_changes_invalidate_results():
    payload=b'Condition,Animal_ID,Cell_ID,Rin_MOhms\nA,a,c1,100\nA,b,c2,110\nA,c,c3,130\nB,d,c4,150\nB,e,c5,120\nB,f,c6,160\n'
    app=loaded('7_⚖️_Statistical_Comparison.py',[('stats.csv',payload)])
    app.button[0].click().run()
    assert not app.exception
    assert not app.error
    assert len(app.get('download_button'))==1
    method=next(e for e in app.selectbox if e.label=='Plan et méthode')
    method.set_value('Mann–Whitney — groupes indépendants').run()
    assert not app.exception
    assert len(app.get('download_button'))==0
