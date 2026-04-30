import streamlit as st
import pyabf
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import tempfile
import os

# --- CONFIGURATION ---
st.set_page_config(page_title="Synaptic Plasticity Analysis", layout="wide")

# --- INITIALISATION DE LA MÉMOIRE (SÉCURISÉE) ---
if 'extracted_data' not in st.session_state:
    st.session_state.extracted_data = None

# --- LANGUAGE SELECTION ---
lang = st.sidebar.selectbox("Language / Langue", ["English", "Français"])

# Translation Dictionary & README Content
T = {
    "English": {
        "lab_title": "Synaptic Plasticity Analysis",
        "lab_subtitle": "Chavis Lab",
        "reactive_note": "Synaptic Plasticity (LTP/LTD) Analysis",
        "loading": "📂 1. Loading",
        "f_base": "Baseline File (.abf)",
        "f_post": "Post File (including CNQX)",
        "protocol": "⏳ 2. Protocol & Analysis",
        "unknown_litter": "Unknown Litter",
        "litter_id": "🧬 Litter ID / Animal",
        "sweep_int": "Sweep interval (s)",
        "induc_dur": "Induction Duration (min)",
        "norm_per": "Normalization Period (min)",
        "ref_start": "Ref. Start",
        "ref_end": "Ref. End",
        "bin_size": "Bin Size (min)",
        "stats": "Statistics (Normalized Plot)",
        "err_bars": "Error Bars:",
        "sweep_sel": "📊 3. Sweep Selection",
        "base_s": "Base: Start",
        "base_e": "Base: End",
        "post_s": "Post: Start",
        "post_e": "Post: End",
        "cnqx_ref": "CNQX Reference",
        "cnqx_s": "CNQX: Start Sweep",
        "cnqx_e": "CNQX: End Sweep",
        "zoom": "🔍 4. Zoom & Inspection",
        "zoom_x": "Zoom Time X (s)",
        "zoom_y": "Zoom Amp Y",
        "measure": "📏 5. Measurement Windows (s)",
        "zero_s": "Zero: Start",
        "zero_e": "Zero: End",
        "peak_s": "fEPSP Peak: Start",
        "peak_e": "fEPSP Peak: End",
        "btn_extract": "🚀 EXTRACT RAW DATA",
        "tabs": ["📌 Inspection", "📉 Raw Dynamics", "📈 Normalized Analysis", "📖 Documentation"],
        "inspect_sub": "Validation (CNQX subtraction included)",
        "trace_cnqx": "CNQX Trace",
        "trace_bsl": "Baseline",
        "trace_post": "Post-Induction",
        "zone_zero": "Zero Zone",
        "zone_peak": "Peak & Area Window",
        "raw_sub": "1. Raw Data (Sweep by Sweep)",
        "amp_raw": "Amplitude (Raw)",
        "charge_raw": "Charge/Area (Raw)",
        "time_min": "Time (min)",
        "induction": "Induction",
        "norm_sub": "2. Normalized Plots",
        "mean_label": "Mean",
        "norm_period_label": "Normalization Period",
        "amp_pct": "Amplitude (% Baseline)",
        "charge_pct": "Charge (% Baseline)",
        "export_header": "Export",
        "export_name": "Export filename:",
        "export_btn": "💾 EXPORT FULL CSV",
        "readme_link": "📖 [View the official README on GitHub](https://github.com/OliManzoni/Manzoni_Chavis_Lab_EPHYS_Stats/blob/main/README.md)",
        "readme_content": """
## 🧬 Synaptic Plasticity Analysis Suite
**Chavis Lab & Manzoni Lab | Preprocessing & Biophysics**

This platform is engineered to standardize the processing of electrophysiological data, transitioning from raw traces (.abf) to publication-ready statistical outputs. It eliminates manual measurement bias by automating the extraction of biophysical parameters and temporal normalization.

### 🔬 Rationale and Core Objectives
In synaptic plasticity research (LTP/LTD), the precision of "Time 0" and the stability of the baseline are paramount. This suite enables:
* **Mitigation of Inter-operator Variability:** The algorithm provides objective peak detection and integral calculations consistently across all recordings.
* **T=0 Standardization:** Automatic alignment based on induction timing to accurately compare maintenance kinetics.
* **Dynamic Scaling:** Normalization relative to a user-defined reference period.

### 📖 User Manual (Workflow)
**1. Data Loading:** Import your Baseline and Post-Induction traces.
**2. Protocol Definition:** Specify the onset of induction (t=0) and the normalization window (reference period for 100%).
**3. Biophysical Analysis:** The algorithm extracts the Peak Amplitude and Charge for every sweep.
**4. Normalization and Binning:** Raw data are normalized relative to the baseline mean.
Data points are subsequently grouped into temporal bins (typically 1-minute averages) to suppress stochastic noise and facilitate population-level visualization.

> **Expert Guidance:** Do not overlook visual inspection. Use the interactive plots in the 'Inspection' tab to validate each cell prior to export, ensuring excessive background noise or unstable series resistance does not compromise normalization.
"""
    },
    "Français": {
        "lab_title": "Synaptic Plasticity Analysis",
        "lab_subtitle": "Chavis Lab",
        "reactive_note": "Analyse Synaptic Plasticity (LTP/LTD)",
        "loading": "📂 1. Chargement",
        "f_base": "Fichier Baseline (.abf)",
        "f_post": "Fichier Post (incluant CNQX)",
        "protocol": "⏳ 2. Protocole & Analyse",
        "unknown_litter": "Portée Inconnue",
        "litter_id": "🧬 ID Portée / Animal",
        "sweep_int": "Intervalle sweeps (s)",
        "induc_dur": "Durée Induction (min)",
        "norm_per": "Période de Normalisation (min)",
        "ref_start": "Début Réf.",
        "ref_end": "Fin Réf.",
        "bin_size": "Taille Bin (min)",
        "stats": "Statistiques (Graphe Normalisé)",
        "err_bars": "Barres d'erreur :",
        "sweep_sel": "📊 3. Sélection des Sweeps",
        "base_s": "Base: Début",
        "base_e": "Base: Fin",
        "post_s": "Post: Début",
        "post_e": "Post: Fin",
        "cnqx_ref": "Référence CNQX",
        "cnqx_s": "CNQX: Début Sweep",
        "cnqx_e": "CNQX: Fin Sweep",
        "zoom": "🔍 4. Zoom & Inspection",
        "zoom_x": "Zoom Temps X (s)",
        "zoom_y": "Zoom Amp Y",
        "measure": "📏 5. Fenêtres de Mesure (s)",
        "zero_s": "Zéro: Début",
        "zero_e": "Zéro: Fin",
        "peak_s": "fEPSP Pic: Début",
        "peak_e": "fEPSP Pic: Fin",
        "btn_extract": "🚀 EXTRAIRE LES DONNÉES BRUTES",
        "tabs": ["📌 Inspection", "📉 Dynamique Brute", "📈 Analyse Normalisée", "📖 Documentation"],
        "inspect_sub": "Validation (Soustraction CNQX incluse)",
        "trace_cnqx": "Trace CNQX",
        "trace_bsl": "Baseline",
        "trace_post": "Post-Induction",
        "zone_zero": "Zone Zéro",
        "zone_peak": "Fenêtre Pic & Aire",
        "raw_sub": "1. Données Brutes (Sweep par Sweep)",
        "amp_raw": "Amplitude (Brute)",
        "charge_raw": "Charge/Aire (Brute)",
        "time_min": "Temps (min)",
        "induction": "Induction",
        "norm_sub": "2. Graphes Normalisés",
        "mean_label": "Moyenne",
        "norm_period_label": "Période de Normalisation",
        "amp_pct": "Amplitude (% Baseline)",
        "charge_pct": "Charge (% Baseline)",
        "export_header": "Exportation",
        "export_name": "Nom du fichier à exporter :",
        "export_btn": "💾 EXPORTER CSV COMPLET",
        "readme_link": "📖 [Consulter le README officiel sur GitHub](https://github.com/OliManzoni/Manzoni_Chavis_Lab_EPHYS_Stats/blob/main/README.md)",
        "readme_content": """
## 🧬 Synaptic Plasticity Analysis Suite
**Chavis Lab & Manzoni Lab | Preprocessing & Biophysics**

Cette plateforme a été conçue pour standardiser le traitement des données d'électrophysiologie, de la trace brute (.abf) aux statistiques prêtes pour la publication. Elle permet de s'affranchir des biais de mesure manuelle en automatisant l'extraction des paramètres biophysiques et la normalisation temporelle.

### 🔬 Pourquoi utiliser cette application ?
En recherche sur la plasticité synaptique (LTP/LTD), la précision du "Temps 0" et la stabilité de la ligne de base sont cruciales. Cette application permet de :
* **Éviter la variabilité inter-opérateur :** L'algorithme détecte les pics et calcule les intégrales (charge) de la même manière pour chaque cellule.
* **Standardiser le T=0 :** Calage automatique de l'induction pour comparer les cinétiques de maintenance.
* **Gérer les échelles :** Normalisation dynamique par rapport à une période de référence définie par l'utilisateur.

### 📖 Manuel de l'Utilisateur (Workflow)
**1. Chargement des données :** Importez votre trace de contrôle (Baseline) et votre trace post-induction.
**2. Définition du Protocole :** Indiquez à quelle minute l'induction a commencé (t=0) et sélectionnez la plage de temps qui servira de référence 100%.
**3. Analyse Biophysique :** L'algorithme extrait l'Amplitude maximale et la Charge pour chaque sweep.
**4. Normalisation et Binning :** Les données brutes sont normalisées par rapport à la moyenne de la baseline.
Les points sont ensuite regroupés par bins temporels pour lisser le bruit stochastique et faciliter la visualisation.

> **Une petite astuce :** Ne négligez pas l'inspection visuelle ! Même si l'algorithme est robuste, une trace avec un bruit de fond excessif ou un accès série instable peut fausser votre normalisation. Utilisez les graphiques interactifs pour valider chaque cellule.
"""
    }
}[lang]

# --- EN-TÊTE INSTITUTIONNEL ---
col_l, col_r = st.columns([2, 5]) 
with col_l:
    try: st.image("logo_chavis_final.png", width=360) 
    except: st.info("Logo Chavis Lab")
with col_r:
    st.markdown(f"# {T['lab_title']}")
    st.markdown(f"### {T['lab_subtitle']}")
    st.markdown(f"#### *{T['reactive_note']}*")
    st.markdown(T['readme_link']) # <-- LIEN DIRECT SOUS LE TITRE PRINCIPAL

st.divider()

# --- BARRE LATÉRALE ---
st.sidebar.markdown(T['readme_link']) # <-- LIEN DIRECT DANS LA BARRE LATÉRALE
st.sidebar.divider()

st.sidebar.header(T['loading'])
f_base = st.sidebar.file_uploader(T['f_base'], type=['abf'])
f_post = st.sidebar.file_uploader(T['f_post'], type=['abf'])

if f_base and f_post:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".abf") as tmp_b, \
         tempfile.NamedTemporaryFile(delete=False, suffix=".abf") as tmp_p:
        tmp_b.write(f_base.getvalue()); tmp_p.write(f_post.getvalue())
        path_b, path_p = tmp_b.name, tmp_p.name
    
    abf_b = pyabf.ABF(path_b); abf_p = pyabf.ABF(path_p)

    st.sidebar.header(T['protocol'])
    
    portee_inconnue = st.sidebar.checkbox(T['unknown_litter'], value=False)
    if portee_inconnue:
        id_defaut = f"Inconnu_{f_base.name.split('.')[0]}"
        final_portee_id = st.sidebar.text_input(T['litter_id'], value=id_defaut, disabled=True)
    else:
        final_portee_id = st.sidebar.text_input(T['litter_id'], value="WT_L1")

    delta_t = st.sidebar.number_input(T['sweep_int'], value=10.0)
    duree_induction = st.sidebar.number_input(T['induc_dur'], value=10.0)
    
    st.sidebar.subheader(T['norm_per'])
    col_n1, col_n2 = st.sidebar.columns(2)
    norm_start = col_n1.number_input(T['ref_start'], value=-10.0)
    norm_end = col_n2.number_input(T['ref_end'], value=0.0)
    
    bin_min = st.sidebar.number_input(T['bin_size'], value=1.0, step=0.5)

    st.sidebar.subheader(T['stats'])
    error_type = st.sidebar.radio(T['err_bars'], ["SEM", "95% CI"])

    st.sidebar.header(T['sweep_sel'])
    c_s1, c_s2 = st.sidebar.columns(2)
    bsl_s = c_s1.number_input(T['base_s'], 0, abf_b.sweepCount-1, abf_b.sweepCount-5)
    bsl_e = c_s2.number_input(T['base_e'], 0, abf_b.sweepCount-1, abf_b.sweepCount-1)
    
    c_s3, c_s4 = st.sidebar.columns(2)
    pst_s = c_s3.number_input(T['post_s'], 0, abf_p.sweepCount-1, 0)
    pst_e = c_s4.number_input(T['post_e'], 0, abf_p.sweepCount-1, 4)

    st.sidebar.subheader(T['cnqx_ref'])
    cnqx_s = st.sidebar.number_input(T['cnqx_s'], 0, abf_p.sweepCount-1, abf_p.sweepCount-5)
    cnqx_e = st.sidebar.number_input(T['cnqx_e'], 0, abf_p.sweepCount-1, abf_p.sweepCount-1)

    sigs_cnqx = []
    for s in range(cnqx_s, cnqx_e + 1):
        abf_p.setSweep(s); sigs_cnqx.append(abf_p.sweepY)
    trace_cnqx_ref = np.mean(sigs_cnqx, axis=0)

    st.sidebar.header(T['zoom'])
    x_range = st.sidebar.slider(T['zoom_x'], 0.0, abf_b.sweepLengthSec, (0.05, 0.15))
    y_range = st.sidebar.slider(T['zoom_y'], -2.0, 0.5, (-1.0, 0.1))

    st.sidebar.header(T['measure'])
    t_bsl_start = st.sidebar.number_input(T['zero_s'], value=0.030, format="%.3f")
    t_bsl_end = st.sidebar.number_input(T['zero_e'], value=0.100, format="%.3f")
    p_start = st.sidebar.number_input(T['peak_s'], value=0.108, format="%.3f")
    p_end = st.sidebar.number_input(T['peak_e'], value=0.140, format="%.3f")

    # --- FONCTIONS MATHÉMATIQUES ---
    def get_metrics(abf, idx, cnqx, f_bsl, f_peak):
        abf.setSweep(idx)
        min_l = min(len(abf.sweepY), len(cnqx))
        t, s = abf.sweepX[:min_l], abf.sweepY[:min_l] - cnqx[:min_l]
        v_base = np.mean(s[(t >= f_bsl[0]) & (t <= f_bsl[1])])
        sn = s - v_base
        mask = (t >= f_peak[0]) & (t <= f_peak[1])
        if len(sn[mask]) > 0:
            amp = float(np.abs(np.min(sn[mask])))
            try: area = float(np.abs(np.trapezoid(sn[mask], x=t[mask])))
            except AttributeError: area = float(np.abs(np.trapz(sn[mask], x=t[mask])))
            return amp, area
        return 0.0, 0.0

    def get_avg(abf, idxs, cnqx, f_bsl):
        sigs = []
        for i in idxs:
            abf.setSweep(i)
            min_l = min(len(abf.sweepY), len(cnqx))
            s = abf.sweepY[:min_l] - cnqx[:min_l]
            sigs.append(s - np.mean(s[(abf.sweepX[:min_l] >= f_bsl[0]) & (abf.sweepX[:min_l] <= f_bsl[1])]))
        return abf.sweepX[:min_l], np.mean(sigs, axis=0)

    # --- AFFICHAGE DES ONGLETS ---
    tab1, tab2, tab3, tab4 = st.tabs(T['tabs'])

    with tab1:
        st.subheader(T['inspect_sub'])
        t_b, s_b = get_avg(abf_b, range(bsl_s, bsl_e+1), trace_cnqx_ref, (t_bsl_start, t_bsl_end))
        t_p, s_p = get_avg(abf_p, range(pst_s, pst_e+1), trace_cnqx_ref, (t_bsl_start, t_bsl_end))
        
        fig, ax = plt.subplots(figsize=(12, 4))
        mask_cnqx_zero = (abf_p.sweepX >= t_bsl_start) & (abf_p.sweepX <= t_bsl_end)
        cnqx_centered = trace_cnqx_ref - np.mean(trace_cnqx_ref[mask_cnqx_zero])
        ax.plot(abf_p.sweepX, cnqx_centered, label=T['trace_cnqx'], color="gray", ls="--", alpha=0.4)
        ax.plot(t_b, s_b, label=T['trace_bsl'], color="#1f77b4", lw=2)
        ax.plot(t_p, s_p, label=T['trace_post'], color="#d62728", alpha=0.8, lw=2)
        ax.axvspan(t_bsl_start, t_bsl_end, color='gray', alpha=0.1, label=T['zone_zero'])
        ax.axvspan(p_start, p_end, color='purple', alpha=0.1, label=T['zone_peak'])
        ax.set_xlim(x_range[0], x_range[1]); ax.set_ylim(y_range[0], y_range[1])
        ax.axhline(0, color='black', lw=1); ax.legend(); st.pyplot(fig)

    if st.button(T['btn_extract'], use_container_width=True):
        m_b = [get_metrics(abf_b, i, trace_cnqx_ref, (t_bsl_start, t_bsl_end), (p_start, p_end)) for i in abf_b.sweepList]
        m_p = [get_metrics(abf_p, i, trace_cnqx_ref, (t_bsl_start, t_bsl_end), (p_start, p_end)) for i in range(0, cnqx_s)]
        amp_b_tuple, area_b_tuple = zip(*m_b) if m_b else ([], [])
        amp_p_tuple, area_p_tuple = zip(*m_p) if m_p else ([], [])
        st.session_state.extracted_data = {
            'amp_b': np.array(amp_b_tuple, dtype=float),
            'area_b': np.array(area_b_tuple, dtype=float),
            'amp_p': np.array(amp_p_tuple, dtype=float),
            'area_p': np.array(area_p_tuple, dtype=float)
        }

    if st.session_state.extracted_data is not None:
        data = st.session_state.extracted_data
        dt_m = delta_t / 60.0
        tm_b = np.arange(-len(data['amp_b']) + 1, 1) * dt_m
        tm_p = duree_induction + np.arange(1, len(data['amp_p']) + 1) * dt_m
        df = pd.DataFrame({
            'Time_min': np.concatenate([tm_b, tm_p]), 
            'Amp_raw': np.concatenate([data['amp_b'], data['amp_p']]),
            'Charge_raw': np.concatenate([data['area_b'], data['area_p']])
        })
        mask_norm = (df['Time_min'] >= norm_start) & (df['Time_min'] <= norm_end)
        ref_amp = df[mask_norm]['Amp_raw'].mean()
        ref_ch = df[mask_norm]['Charge_raw'].mean()
        df['Amp_norm'] = (df['Amp_raw'] / ref_amp) * 100
        df['Charge_norm'] = (df['Charge_raw'] / ref_ch) * 100
        df['Bin_id'] = np.floor(df['Time_min'] / bin_min)
        df_bin = df.groupby('Bin_id').agg({'Time_min':'mean', 'Amp_norm':['mean','sem'], 'Charge_norm':['mean','sem']})
        df_bin.columns = ['Time_avg', 'Amp_m', 'Amp_sem', 'Ch_m', 'Ch_sem']
        df_bin.fillna(0, inplace=True)
        df_bin['Amp_ci95'] = df_bin['Amp_sem'] * 1.96
        df_bin['Ch_ci95'] = df_bin['Ch_sem'] * 1.96

        with tab2:
            st.subheader(T['raw_sub'])
            fig_r, (ax_r1, ax_r2) = plt.subplots(2, 1, figsize=(12, 10), sharex=True)
            ax_r1.scatter(tm_b, data['amp_b'], color='#1f77b4', s=15, alpha=0.5, label=T['trace_bsl'])
            ax_r1.scatter(tm_p, data['amp_p'], color='black', s=15, alpha=0.5, label="Post")
            ax_r1.axvspan(0, duree_induction, color='gray', alpha=0.1, label=T['induction'])
            ax_r1.set_ylabel(T['amp_raw']); ax_r1.legend()
            ax_r2.scatter(tm_b, data['area_b'], color='#2ca02c', s=15, alpha=0.5)
            ax_r2.scatter(tm_p, data['area_p'], color='black', s=15, alpha=0.5)
            ax_r2.axvspan(0, duree_induction, color='gray', alpha=0.1)
            ax_r2.set_ylabel(T['charge_raw']); ax_r2.set_xlabel(T['time_min'])
            st.pyplot(fig_r)

        with tab3:
            st.subheader(f"{T['norm_sub']} ({T['mean_label']} ± {error_type})")
            err_amp = df_bin['Amp_sem'] if error_type == "SEM" else df_bin['Amp_ci95']
            err_ch = df_bin['Ch_sem'] if error_type == "SEM" else df_bin['Ch_ci95']
            fig_n, (ax_n1, ax_n2) = plt.subplots(2, 1, figsize=(12, 10), sharex=True)
            ax_n1.scatter(df['Time_min'], df['Amp_norm'], color='lightgray', s=8, alpha=0.3)
            ax_n1.errorbar(df_bin['Time_avg'], df_bin['Amp_m'], yerr=err_amp, fmt='o', color='black', capsize=3, label=f"{T['mean_label']} ({error_type})")
            ax_n1.axvspan(norm_start, norm_end, color='#1f77b4', alpha=0.1, label=T['norm_period_label'])
            ax_n1.axvspan(0, duree_induction, color='gray', alpha=0.15, label=T['induction'])
            ax_n1.axhline(100, color='red', ls='--', lw=1)
            ax_n1.set_ylabel(T['amp_pct']); ax_n1.legend()
            ax_n2.scatter(df['Time_min'], df['Charge_norm'], color='lightblue', s=8, alpha=0.3)
            ax_n2.errorbar(df_bin['Time_avg'], df_bin['Ch_m'], yerr=err_ch, fmt='s', color='blue', capsize=3)
            ax_n2.axvspan(norm_start, norm_end, color='#1f77b4', alpha=0.1)
            ax_n2.axvspan(0, duree_induction, color='gray', alpha=0.15)
            ax_n2.axhline(100, color='red', ls='--', lw=1)
            ax_n2.set_ylabel(T['charge_pct']); ax_n2.set_xlabel(T['time_min'])
            st.pyplot(fig_n)
            
            st.markdown(f"### {T['export_header']}")
            nom_export = st.text_input(T['export_name'], value=f"{final_portee_id}_{f_base.name.split('.')[0]}.csv")
            if not nom_export.endswith(".csv"): nom_export += ".csv"
            df_export = df_bin.copy().reset_index()
            df_export.insert(0, 'Portee', final_portee_id)
            df_export.insert(1, 'Source', f_base.name)
            st.download_button(T['export_btn'], df_export.to_csv(index=False), nom_export)

        with tab4:
            st.markdown(T['readme_content'])

    if os.path.exists(path_b): os.remove(path_b)
    if os.path.exists(path_p): os.remove(path_p)
