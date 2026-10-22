"""Statistical workspace: explicit experimental units and reproducible outputs."""
import io
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats
import streamlit as st
from ephys_io import read_table, digest, bundle
from ephys_stats import prepare, unit_means, descriptives, pairwise, adjust_family, mixed_model
from ephys_ui import session_compute

st.title('⚖️ Statistiques et figures de population')
st.caption('Définissez le plan expérimental avant de choisir le test. Les identifiants d’animaux doivent être uniques dans toute l’étude ; un identifiant commun aux conditions indique un appariement.')
mode = st.radio('Import', ['Table longue avec une colonne de condition', 'Deux groupes de fichiers'], horizontal=True)
frames, sources = [], []
if mode.startswith('Table'):
    uploads = st.file_uploader('CSV : une ligne par mesure, avec identifiants et condition', type=['csv','txt'], accept_multiple_files=True)
    batches = [(uploads, None)]
else:
    a, b = st.columns(2)
    name_a = a.text_input('Groupe 1', 'Contrôle')
    name_b = b.text_input('Groupe 2', 'Traitement')
    up_a = a.file_uploader('CSV du groupe 1', type=['csv'], accept_multiple_files=True)
    up_b = b.file_uploader('CSV du groupe 2', type=['csv'], accept_multiple_files=True)
    if not name_a.strip() or not name_b.strip() or name_a == name_b:
        st.info('Utilisez deux noms de groupes distincts et non vides.'); st.stop()
    batches = [(up_a, name_a), (up_b, name_b)]
seen = set()
for uploads, group in batches:
    for f in uploads or []:
        payload = f.getvalue()
        fingerprint = digest(payload)
        if fingerprint in seen:
            st.error(f'Fichier chargé deux fois : {f.name}. Retirez le doublon.'); st.stop()
        seen.add(fingerprint)
        try: frame = read_table(payload)
        except ValueError as exc: st.error(f'{f.name} : {exc}'); st.stop()
        if group is not None: frame['Condition'] = group
        frame['Source_File'] = f.name
        frames.append(frame)
        sources.append({'name':f.name, 'sha256':fingerprint, 'rows':len(frame)})
if not frames:
    st.info('Importez vos données. Les exports doivent contenir des identifiants Animal_ID ou Cell_ID, par exemple.')
    example = pd.DataFrame({'Condition':['Controle','Controle','Traitement','Traitement'], 'Animal_ID':['A01','A02','A03','A04'], 'Cell_ID':['C01','C02','C03','C04'], 'Rin_MOhms':[120,135,145,150]})
    st.download_button('Modèle de tableau CSV', example.to_csv(index=False), 'modele_statistiques.csv')
    st.stop()
data = pd.concat(frames, ignore_index=True, sort=False)
with st.expander('Données importées et identifiants', expanded=False):
    st.dataframe(data, use_container_width=True)
    st.caption('Les fichiers sont empilés sans fusion implicite ni suppression de colonnes. Importez uniquement les observations que vous souhaitez analyser ensemble.')
cols = [c for c in data.columns if c != 'Source_File']
condition = st.selectbox('Colonne de condition', cols, index=cols.index('Condition') if 'Condition' in cols else 0)
ids = [c for c in cols if c != condition]
if not ids: st.error('Il manque les colonnes de mesure et d’identifiant.'); st.stop()
preferred = next((c for c in ['Animal_ID','Mouse_ID','Cell_ID','File'] if c in ids), ids[0])
unit = st.selectbox('Unité indépendante / identifiant des paires ou de regroupement', ids, index=ids.index(preferred))
methods = {'Welch — groupes indépendants':'welch', 'Mann–Whitney — groupes indépendants':'mannwhitney', 'Test t apparié':'paired_t', 'Wilcoxon apparié':'wilcoxon', 'Modèle linéaire mixte':'mixed'}
method_label = st.selectbox('Plan et méthode', list(methods))
method = methods[method_label]
remaining = [c for c in ids if c != unit]
nested = st.selectbox('Sous-unité facultative (cellule dans l’animal)', ['Aucune']+remaining)
nested = None if nested == 'Aucune' else nested
x = None
random_slope = False
if method == 'mixed':
    x = st.selectbox('Facteur répété numérique (temps ou courant), facultatif', ['Aucun']+[c for c in remaining if c != nested])
    x = None if x == 'Aucun' else x
    if x:
        st.caption('Modèle condition × facteur numérique : tendance linéaire. Les différences de condition sont évaluées à la valeur moyenne du facteur. Pour une courbe non linéaire, ce modèle ne remplace pas une analyse par protocole.')
        random_slope = st.checkbox('Pente aléatoire par unité', value=False)
    st.caption('IC de Wald et p-valeurs asymptotiques. Les graphes de distribution montrent des moyennes par unité ; les effets ajustés sont dans le graphe des contrastes.')
else:
    st.caption('Les répétitions sont moyennées par unité avant le test. Avec une sous-unité, moyenne d’abord par cellule puis par animal. Les analyses appariées conservent uniquement les paires complètes pour chaque contraste.')
metrics_options = [c for c in remaining if c not in {nested, x} and pd.to_numeric(data[c], errors='coerce').notna().any()]
metrics = st.multiselect('Mesures à comparer (famille de tests)', metrics_options, default=metrics_options[:1])
correction_name = st.selectbox('Correction sur tous les contrastes de toutes les mesures sélectionnées', ['Holm (erreur familiale)', 'Benjamini–Hochberg (FDR exploratoire)'])
correction = 'holm' if correction_name.startswith('Holm') else 'fdr_bh'
if not metrics: st.stop()
settings = dict(method=method, condition=condition, unit=unit, nested=nested, repeated_factor=x,
                random_slope=random_slope, metrics=metrics, correction=correction, sources=sources,
                confidence_level=.95, confidence_intervals='pointwise, not multiplicity adjusted', exclusions='complete-case per metric; no automatic outlier removal')
signature = str(settings)

def calculate():
    results, descriptions, coefficients, diagnostics, retained, notes = [], {}, [], {}, {}, []
    for metric in metrics:
        try:
            d = prepare(data, metric, condition, unit, nested=nested, x=x, independent=method in ('welch','mannwhitney'))
            missing = len(data)-len(d)
            if missing: notes.append(f'{metric} : {missing} lignes incomplètes écartées.')
            if nested and method != 'mixed':
                d = d.groupby([condition, unit, nested], observed=True, as_index=False)[metric].mean()
            retained[metric] = d
            descriptions[metric] = descriptives(d, metric, condition, unit)
            if method == 'mixed':
                r, c, diag, warnings = mixed_model(d, metric, condition, unit, nested=nested, x=x, random_slope=random_slope)
                coefficients.append(c); diagnostics[metric] = diag
                notes.extend(f'{metric} : {message}' for message in warnings)
            else:
                r = pairwise(d, metric, condition, unit, method)
            results.append(r)
        except (ValueError, np.linalg.LinAlgError) as exc:
            notes.append(f'{metric} : analyse impossible — {exc}')
    if not results: return None, descriptions, None, diagnostics, retained, notes
    result = adjust_family(pd.concat(results, ignore_index=True), correction)
    coef = None
    if coefficients:
        coef = pd.concat(coefficients, ignore_index=True)
        # Fixed-effect terms form a separate, explicitly declared family (intercepts excluded).
        mask = coef.term.ne('Intercept')
        adjusted = adjust_family(coef.loc[mask], correction)
        coef['p_adjusted'] = np.nan
        coef.loc[mask,'p_adjusted'] = adjusted.p_adjusted
    return result, descriptions, coef, diagnostics, retained, notes

if st.button('Calculer et préparer les figures', type='primary'):
    with st.spinner('Calcul des statistiques…'):
        try:
            st.session_state['stats_result'] = (signature, calculate())
        except Exception as exc:
            st.error(f'Calcul interrompu : {exc}'); st.stop()
saved = st.session_state.get('stats_result')
if not saved or saved[0] != signature:
    st.info('Lancez le calcul pour ces données et paramètres.'); st.stop()
result, summaries, coef, diagnostics, retained, notes = saved[1]
for note in notes: st.warning(note)
if result is None: st.stop()
st.subheader('Contrastes : comparaison − référence')
st.dataframe(result, use_container_width=True)
st.caption('Les p-valeurs corrigées couvrent tous les contrastes estimables affichés. Les IC à 95 % sont ponctuels, sans correction de multiplicité. Pour les tests de rangs, l’effet rapporté est une corrélation bisérielle de rang ; aucun IC de différence de moyenne n’est présenté.')
if coef is not None:
    with st.expander('Coefficients des modèles et interactions'):
        st.dataframe(coef, use_container_width=True)
        st.caption('Famille de correction distincte : tous les termes fixes hors intercept, pour toutes les mesures sélectionnées.')
if method in ('paired_t','wilcoxon'):
    st.caption('Les points montrent toutes les unités disponibles ; chaque contraste utilise ses paires complètes, exportées dans un tableau dédié.')
figures, tables = {}, {'contrasts':result, 'input_data':data}
if coef is not None: tables['model_coefficients'] = coef
for index, metric in enumerate(metrics):
    if metric not in retained: continue
    d = retained[metric]
    u = unit_means(d, metric, condition, unit)
    levels = list(pd.unique(u[condition]))
    fig, axes = plt.subplots(1, 2, figsize=(11,4.5))
    rng = np.random.default_rng(42)
    if method in ('paired_t','wilcoxon'):
        pivot = u.pivot(index=unit, columns=condition, values=metric).reindex(columns=levels)
        for _, row in pivot.iterrows(): axes[0].plot(range(len(levels)), row.to_numpy(), color='.7', alpha=.5, lw=.7)
    for j, level in enumerate(levels):
        values = u.loc[u[condition]==level,metric]
        axes[0].scatter(j+rng.uniform(-.08,.08,len(values)), values, alpha=.75, s=22)
        axes[0].plot([j-.15,j+.15], [values.mean()]*2, color='black', lw=2)
    axes[0].set(xticks=range(len(levels)), xticklabels=levels, ylabel=metric, title=f'Moyennes par {unit}')
    contrasts = result.loc[result.metric.eq(metric) & result.status.eq('ok') & result.estimate.notna()]
    if len(contrasts):
        est = contrasts.estimate.to_numpy()
        axes[1].errorbar(est, np.arange(len(est)), xerr=np.array([est-contrasts.ci_low.to_numpy(), contrasts.ci_high.to_numpy()-est]), fmt='o', color='#176b87', capsize=3)
        axes[1].set(yticks=range(len(est)), yticklabels=contrasts.comparison.astype(str)+' − '+contrasts.reference.astype(str), xlabel='Différence et IC 95 %')
        axes[1].axvline(0, color='.5', ls='--')
    else:
        axes[1].axis('off')
        axes[1].text(.05,.5,'Tests de rangs : effets dans le tableau.', transform=axes[1].transAxes)
    fig.tight_layout()
    st.pyplot(fig)
    figures[f'metric_{index+1}'] = fig
    tables[f'metric_{index+1}_used'] = d
    tables[f'metric_{index+1}_unit_means'] = u
    if method in ('paired_t','wilcoxon'):
        from itertools import combinations
        for ia, ib in combinations(range(len(levels)), 2):
            pair_table = u.pivot(index=unit, columns=condition, values=metric)[[levels[ia],levels[ib]]].dropna().reset_index()
            tables[f'metric_{index+1}_pair_{ia+1}_{ib+1}'] = pair_table
    tables[f'metric_{index+1}_summary'] = summaries[metric]
    if metric in diagnostics:
        diag = diagnostics[metric]
        diagnostic, ax = plt.subplots(1,2,figsize=(10,4))
        ax[0].scatter(diag.fitted, diag.residual, s=10, alpha=.5)
        ax[0].axhline(0,color='.5'); ax[0].set(xlabel='Valeur ajustée', ylabel='Résidu')
        stats.probplot(diag.residual, plot=ax[1])
        diagnostic.tight_layout()
        with st.expander(f'Diagnostics — {metric}'): st.pyplot(diagnostic)
        figures[f'metric_{index+1}_diagnostics'] = diagnostic
        tables[f'metric_{index+1}_diagnostics'] = diag
settings['metric_file_mapping'] = {f'metric_{i+1}':m for i,m in enumerate(metrics)}
archive = session_compute('stats_archive', signature, lambda: bundle(tables, figures, settings))
st.download_button('Télécharger le dossier complet : figures PDF/SVG/PNG, CSV et paramètres', archive, 'ephys_statistics.zip', mime='application/zip')
for fig in figures.values(): plt.close(fig)
