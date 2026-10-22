"""Population curves with explicit units, consistent tables/figures and vector exports."""
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats
import streamlit as st
from ephys_io import read_table, digest, bundle
from ephys_ui import session_compute

st.title('📈 Courbes de population f-I et I-V')
files = st.file_uploader('Exports CSV des sweeps — plusieurs cellules et conditions', type=['csv'], accept_multiple_files=True)
if not files:
    st.info('Chargez les exports de la page Potentiels d’action. Les courants seront exprimés en pA.'); st.stop()
frames, metadata, sources, seen = [], [], [], set()
for f in files:
    fingerprint = digest(f.getvalue())
    if fingerprint in seen:
        st.error(f'Fichier identique chargé plusieurs fois : {f.name}'); st.stop()
    seen.add(fingerprint)
    try: d = read_table(f.getvalue())
    except ValueError as exc: st.error(str(exc)); st.stop()
    required = ['I_inj','Nb_Spikes','V_steady']
    if not all(c in d for c in required):
        st.error(f'{f.name} : colonnes requises {required}'); st.stop()
    def first(column, fallback):
        if column in d and d[column].notna().any(): return str(d[column].dropna().iloc[0])
        return fallback
    metadata.append(dict(Source_File=f.name, Condition=first('Condition','Groupe 1'),
                         Animal_ID=first('Animal_ID',''), Cell_ID=first('Cell_ID',f.name.removesuffix('_Sweeps.csv')),
                         Current_Unit=first('Current_Unit','pA')))
    d['Source_File'] = f.name
    frames.append(d)
    sources.append({'name':f.name,'sha256':fingerprint})
st.caption('Complétez les identifiants et les conditions. Pour les anciens CSV sans unité, vérifiez pA/nA dans le tableau ci-dessous.')
metadata = st.data_editor(pd.DataFrame(metadata), disabled=['Source_File'], hide_index=True, key='curve_metadata')
if metadata.Source_File.duplicated().any():
    st.error('Les fichiers doivent avoir des noms distincts.'); st.stop()
unit = st.radio('Unité des moyennes et des barres d’erreur', ['Cell_ID','Animal_ID'], horizontal=True)
error = st.radio('Incertitude', ['IC 95 % (Student)', 'SEM'], horizontal=True)
individual = st.checkbox('Afficher les courbes individuelles', True)
raw = pd.concat(frames, ignore_index=True)
raw = raw.drop(columns=['Condition','Animal_ID','Cell_ID','Current_Unit'], errors='ignore').merge(metadata, on='Source_File', validate='many_to_one')
for c in required:
    raw[c] = pd.to_numeric(raw[c],errors='coerce')
if raw[['Cell_ID','Condition',unit]].replace(r'^\s*$',np.nan,regex=True).isna().any().any():
    st.error('Renseignez les identifiants et les conditions de toutes les lignes.'); st.stop()
scale = raw.Current_Unit.str.strip().map({'pA':1.,'nA':1000.})
if scale.isna().any():
    st.error('Unité de courant inconnue : seules pA et nA sont acceptées.'); st.stop()
raw['I_inj'] = (raw.I_inj*scale).round(6)
raw['Current_Unit'] = 'pA'
raw = raw.replace([np.inf,-np.inf],np.nan)
bad = raw[required].isna().any(axis=1)
if bad.any(): st.warning(f'{bad.sum()} lignes numériques incomplètes écartées.')
raw = raw.loc[~bad].copy()
if raw.empty: st.error('Aucune donnée exploitable.'); st.stop()
# Every cell has equal weight within an animal, regardless of sweep count.
cell_keys = ['Condition','Animal_ID','Cell_ID','I_inj']
cells = raw.groupby(cell_keys, observed=True, as_index=False, dropna=False)[['Nb_Spikes','V_steady']].mean()
if unit == 'Animal_ID':
    units = cells.groupby(['Condition','Animal_ID','I_inj'], observed=True, as_index=False)[['Nb_Spikes','V_steady']].mean()
else:
    units = cells.copy()
    units['Cell_ID'] = units['Animal_ID'].fillna('')+' / '+units['Cell_ID']
summary = units.groupby(['Condition','I_inj'], observed=True).agg(
    N=(unit,'nunique'), Nb_Spikes_Mean=('Nb_Spikes','mean'), Nb_Spikes_SEM=('Nb_Spikes','sem'),
    V_steady_Mean=('V_steady','mean'), V_steady_SEM=('V_steady','sem')).reset_index()
factor = stats.t.ppf(.975, summary.N-1)
for metric in ['Nb_Spikes','V_steady']:
    summary[metric+'_95CI_halfwidth'] = factor*summary[metric+'_SEM']
fig, axes = plt.subplots(1,2,figsize=(12,4.8))
colors = plt.get_cmap('tab10')
for k, condition in enumerate(pd.unique(units.Condition)):
    for ax, metric, ylabel in zip(axes,['Nb_Spikes','V_steady'],['Nombre de PA / sweep','Potentiel stationnaire (mV)']):
        d = units.loc[units.Condition.eq(condition)]
        sums = summary.loc[summary.Condition.eq(condition)].sort_values('I_inj')
        if metric=='Nb_Spikes': d=d.loc[d.I_inj>=0]; sums=sums.loc[sums.I_inj>=0]
        if individual:
            for _, trace in d.groupby(unit):
                trace=trace.sort_values('I_inj'); ax.plot(trace.I_inj,trace[metric],color=colors(k%10),alpha=.18,lw=.7)
        xx=sums.I_inj.to_numpy(); yy=sums[metric+'_Mean'].to_numpy()
        ee=sums[metric+('_SEM' if error=='SEM' else '_95CI_halfwidth')].to_numpy()
        ax.plot(xx,yy,'o-',color=colors(k%10),label=str(condition),lw=2,ms=4)
        ax.fill_between(xx,yy-ee,yy+ee,color=colors(k%10),alpha=.15)
        ax.set(xlabel='Courant injecté (pA)',ylabel=ylabel)
        ax.spines[['top','right']].set_visible(False)
for ax in axes: ax.legend(frameon=False)
fig.tight_layout(); st.pyplot(fig)
st.caption(f'Une contribution par {unit} et par courant. Les bandes décrivent l’incertitude de la moyenne à chaque courant ; elles ne sont pas des comparaisons statistiques entre conditions. Avec une seule unité, aucune bande n’est calculée.')
st.dataframe(summary,use_container_width=True)
settings=dict(unit=unit,error=error,individual_curves=individual,sources=sources,metadata=metadata.to_dict('records'),current_unit='pA',aggregation='sweeps within cell, then equal cell means within animal')
archive=session_compute('curves_archive',str(settings),lambda:bundle({'raw':raw,'cells':cells,'units':units,'summary':summary},{'population_curves':fig},settings))
st.download_button('Télécharger les figures PDF/SVG/PNG et les tableaux',archive,'population_curves.zip',mime='application/zip')
plt.close(fig)
