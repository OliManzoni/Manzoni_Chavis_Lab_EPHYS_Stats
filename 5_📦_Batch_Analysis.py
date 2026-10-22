"""Batch analysis using exactly the same numerical functions as individual pages."""
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st
from ephys_analysis import read_abf, analyze_spikes, analyze_epsc, analyze_ipsc
from ephys_io import digest, bundle
from ephys_ui import session_compute

st.title('📦 Analyse de plusieurs enregistrements')
analysis=st.selectbox('Analyse', ['Potentiels d’action', 'sEPSC AMPA', 'sIPSC GABA'])
files=st.file_uploader('Fichiers ABF', type=['abf'],accept_multiple_files=True)
if not files: st.stop()
if len({f.name for f in files})!=len(files): st.error('Les noms des fichiers doivent être distincts.'); st.stop()
metadata=st.data_editor(pd.DataFrame([dict(File=f.name,Condition='Groupe 1',Animal_ID='',Cell_ID=f.name.removesuffix('.abf')) for f in files]),disabled=['File'],hide_index=True)
params={}
if analysis.startswith('Potentiels'):
    params['spike_threshold']=st.number_input('Seuil de détection (mV)',value=0.)
    params['dvdt_threshold']=st.number_input('Seuil dV/dt (mV/ms)',value=15.)
    st.caption('Fenêtre d’injection : 100–600 ms, identique à la page individuelle.')
else:
    outward = False
    if 'GABA' in analysis:
        outward=st.radio('Polarité',['Entrant','Sortant'],horizontal=True)=='Sortant'
    params['dynamic']=st.checkbox('Retirer la ligne de base par médiane glissante (0,5 s)',True)
    params['use_bessel']=st.checkbox('Filtre Bessel',True)
    params['cutoff']=st.number_input('Coupure (Hz)',min_value=1,value=2000)
    params['threshold']=st.number_input('Seuil Z-score',min_value=.1,value=3. if 'AMPA' in analysis else 2.5)
    params['use_amp_filter']=st.checkbox('Filtrer l’amplitude',True)
    params['amp_limit']=st.number_input('Amplitude minimale (pA)',min_value=0.,value=10. if 'AMPA' in analysis else (5. if outward else 7.))
    params['use_rise_filter']=st.checkbox('Filtrer le temps de montée',True)
    params['rise_limit']=st.number_input('Temps de montée maximal (ms)',min_value=.01,value=4. if 'AMPA' in analysis else (5. if outward else 1.5))
    if 'GABA' in analysis:
        params['is_outward']=outward
        params['use_decay_filter']=st.checkbox('Filtrer la durée équivalente charge/amplitude',True)
        params['decay_limit']=st.number_input('Durée équivalente maximale (ms)',min_value=.01,value=50. if outward else 4.)
    st.caption('Comme les pages individuelles, l’analyse spontanée utilise le premier sweep et le premier canal. Les résultats comprennent un résumé par cellule et les événements retenus.')
identities=[dict(name=f.name,sha256=digest(f.getvalue())) for f in files]
settings=dict(analysis=analysis,parameters=params,metadata=metadata.to_dict('records'),sources=identities)
signature=str(settings)
if st.button('Analyser le lot',type='primary'):
    summaries, details, log=[],{},[]
    progress=st.progress(0.)
    for i,f in enumerate(files):
        meta=metadata.iloc[i].to_dict()
        try:
            abf=read_abf(f.getvalue())
            if analysis.startswith('Potentiels'):
                if abf.sweepUnitsY!='mV': raise ValueError('Cette analyse attend une tension en mV.')
                r=analyze_spikes(abf,**params)
                summaries.append(dict(meta,Vrest_mV=r['v_rest_final'],Rin_MOhms=r['rin'],Tau_ms=r['tau'],Rheobase_I_pA=r['rheo_i']*(1000 if r['unit_i']=='nA' else 1),Rheobase_mV=r['rheo_v']))
                d=pd.DataFrame({'Sweep':abf.sweepList,'I_inj':r['courants'],'Nb_Spikes':r['n_spikes'],'V_steady':r['v_stat'],
                                'V_threshold':r['v_thresh_list'],'AP_Amp':r['ap_amps'],'AP_Width_ms':r['ap_widths'],
                                'AP_Rise_ms':r['ap_rise'],'AP_Decay_ms':r['ap_decay'],
                                'AP_AHP':np.array(r['v_thresh_list'])-np.array(r['ap_ahp']),
                                'Excluded_Depolarization_Block':r['is_excluded_list'], 'Current_Unit':r['unit_i'],
                                'Duration_s':.5,'Frequency_Hz':np.array(r['n_spikes'])/.5})
                d=d.assign(**meta)
                details[f'file_{i+1}_All_Sweeps']=d
                details[f'file_{i+1}_Sweeps']=d.loc[~d.Excluded_Depolarization_Block]
            else:
                if abf.sweepUnitsY!='pA': raise ValueError('Cette analyse attend un courant en pA.')
                applied=dict(params,cutoff=min(params['cutoff'],max(1,int(.95*abf.dataRate/2))))
                if 'AMPA' in analysis:
                    r=analyze_epsc(abf,**applied)
                    if not r['has_waveforms']: raise ValueError('Trop peu d’événements pour construire le gabarit AMPA ; aucune fréquence n’est estimée.')
                    events=r['valid_ev_iter']; amp,charge='amp_scaled','charge_scaled'
                else:
                    r=analyze_ipsc(abf,**applied)
                    events=r['valid_ev']; amp,charge='amp','area'
                d=pd.DataFrame(events)
                duration=len(r['times'])/r['fs']
                summaries.append(dict(meta,N_Events=len(d),Frequency_Hz=len(d)/duration,
                                      Mean_Amplitude_pA=d[amp].mean() if len(d) else np.nan,
                                      Mean_Charge_fC=d[charge].mean() if len(d) else np.nan,
                                      Mean_Rise_ms=d['rise'].mean() if len(d) else np.nan,
                                      Applied_Cutoff_Hz=applied['cutoff'],Duration_s=duration))
                details[f'file_{i+1}_Events']=d.assign(**meta)
            log.append(dict(File=f.name,status='ok',message=''))
        except Exception as exc:
            log.append(dict(File=f.name,status='failed',message=str(exc)))
        progress.progress((i+1)/len(files))
    st.session_state['batch_results']=(signature,pd.DataFrame(summaries),details,pd.DataFrame(log))
saved=st.session_state.get('batch_results')
if not saved or saved[0]!=signature: st.info('Lancez l’analyse du lot pour ces paramètres.'); st.stop()
_,summary,details,log=saved
st.dataframe(log,use_container_width=True)
if summary.empty: st.error('Aucun enregistrement analysé avec succès.'); st.stop()
st.dataframe(summary,use_container_width=True)
figures={}
metric='Rin_MOhms' if analysis.startswith('Potentiels') else 'Frequency_Hz'
fig,ax=plt.subplots(figsize=(max(6,min(14,len(summary)*.5)),4))
ax.plot(np.arange(len(summary)),summary[metric],'o',color='#176b87')
ax.set(xticks=np.arange(len(summary)),xticklabels=summary.Cell_ID,ylabel=metric,title='Résumé du lot — valeurs individuelles')
ax.tick_params(axis='x',rotation=60);fig.tight_layout();st.pyplot(fig)
figures['batch_summary']=fig
archive=session_compute('batch_archive',signature,lambda:bundle(dict(details,summary=summary,processing_log=log),figures,settings))
st.download_button('Télécharger le lot : résultats, figure et paramètres',archive,'ephys_batch.zip',mime='application/zip')
plt.close(fig)
