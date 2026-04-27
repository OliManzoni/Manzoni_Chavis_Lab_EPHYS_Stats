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

# --- EN-TÊTE INSTITUTIONNEL ---
col_l, col_r = st.columns([2, 5]) 
with col_l:
    try: st.image("logo_chavis_final.png", width=360) 
    except: st.info("Logo Chavis Lab")
with col_r:
    st.markdown("# Synaptic Plasticity Analysis")
    st.markdown("### Chavis Lab | Axe T=0 & Normalisation Dynamique")
    st.markdown("#### *Réactivité totale sans rechargement*")

st.divider()

# --- BARRE LATÉRALE ---
st.sidebar.header("📂 1. Chargement")
f_base = st.sidebar.file_uploader("Fichier Baseline (.abf)", type=['abf'])
f_post = st.sidebar.file_uploader("Fichier Post (incluant CNQX)", type=['abf'])

if f_base and f_post:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".abf") as tmp_b, \
         tempfile.NamedTemporaryFile(delete=False, suffix=".abf") as tmp_p:
        tmp_b.write(f_base.getvalue()); tmp_p.write(f_post.getvalue())
        path_b, path_p = tmp_b.name, tmp_p.name
    
    abf_b = pyabf.ABF(path_b); abf_p = pyabf.ABF(path_p)

    st.sidebar.header("⏳ 2. Protocole & Analyse")
    
    # --- LOGIQUE PORTÉE ---
    portee_inconnue = st.sidebar.checkbox("Portée Inconnue", value=False)
    if portee_inconnue:
        id_defaut = f"Inconnu_{f_base.name.split('.')[0]}"
        final_portee_id = st.sidebar.text_input("🧬 ID Portée / Animal", value=id_defaut, disabled=True)
    else:
        final_portee_id = st.sidebar.text_input("🧬 ID Portée / Animal", value="WT_L1")

    # Paramètres qui modifient l'axe du temps et le binning (Réactifs)
    delta_t = st.sidebar.number_input("Intervalle sweeps (s)", value=10.0)
    duree_induction = st.sidebar.number_input("Durée Induction (min)", value=10.0)
    
    st.sidebar.subheader("Période de Normalisation (min)")
    col_n1, col_n2 = st.sidebar.columns(2)
    norm_start = col_n1.number_input("Début Réf.", value=-10.0)
    norm_end = col_n2.number_input("Fin Réf.", value=0.0)
    
    bin_min = st.sidebar.number_input("Taille Bin (min)", value=1.0, step=0.5)

    st.sidebar.subheader("Statistiques (Graphe Normalisé)")
    error_type = st.sidebar.radio("Barres d'erreur :", ["SEM", "95% CI"])

    st.sidebar.header("📊 3. Sélection des Sweeps")
    c_s1, c_s2 = st.sidebar.columns(2)
    bsl_s = c_s1.number_input("Base: Début", 0, abf_b.sweepCount-1, abf_b.sweepCount-5)
    bsl_e = c_s2.number_input("Base: Fin", 0, abf_b.sweepCount-1, abf_b.sweepCount-1)
    
    c_s3, c_s4 = st.sidebar.columns(2)
    pst_s = c_s3.number_input("Post: Début", 0, abf_p.sweepCount-1, 0)
    pst_e = c_s4.number_input("Post: Fin", 0, abf_p.sweepCount-1, 4)

    st.sidebar.subheader("Référence CNQX")
    cnqx_s = st.sidebar.number_input("CNQX: Début Sweep", 0, abf_p.sweepCount-1, abf_p.sweepCount-5)
    cnqx_e = st.sidebar.number_input("CNQX: Fin Sweep", 0, abf_p.sweepCount-1, abf_p.sweepCount-1)

    sigs_cnqx = []
    for s in range(cnqx_s, cnqx_e + 1):
        abf_p.setSweep(s); sigs_cnqx.append(abf_p.sweepY)
    trace_cnqx_ref = np.mean(sigs_cnqx, axis=0)

    st.sidebar.header("🔍 4. Zoom & Inspection")
    x_range = st.sidebar.slider("Zoom Temps X (s)", 0.0, abf_b.sweepLengthSec, (0.05, 0.15))
    y_range = st.sidebar.slider("Zoom Amp Y", -2.0, 0.5, (-1.0, 0.1))

    st.sidebar.header("📏 5. Fenêtres de Mesure (s)")
    t_bsl_start = st.sidebar.number_input("Zéro: Début", value=0.030, format="%.3f")
    t_bsl_end = st.sidebar.number_input("Zéro: Fin", value=0.100, format="%.3f")
    p_start = st.sidebar.number_input("fEPSP Pic: Début", value=0.108, format="%.3f")
    p_end = st.sidebar.number_input("fEPSP Pic: Fin", value=0.140, format="%.3f")

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
    tab1, tab2, tab3 = st.tabs(["📌 Inspection", "📉 Dynamique Brute", "📈 Analyse Normalisée"])

    # ONGLET 1 : INSPECTION (S'affiche tout de suite, réactif aux curseurs de fenêtres)
    with tab1:
        st.subheader("Validation (Soustraction CNQX incluse)")
        t_b, s_b = get_avg(abf_b, range(bsl_s, bsl_e+1), trace_cnqx_ref, (t_bsl_start, t_bsl_end))
        t_p, s_p = get_avg(abf_p, range(pst_s, pst_e+1), trace_cnqx_ref, (t_bsl_start, t_bsl_end))
        
        fig, ax = plt.subplots(figsize=(12, 4))
        
        mask_cnqx_zero = (abf_p.sweepX >= t_bsl_start) & (abf_p.sweepX <= t_bsl_end)
        cnqx_centered = trace_cnqx_ref - np.mean(trace_cnqx_ref[mask_cnqx_zero])
        ax.plot(abf_p.sweepX, cnqx_centered, label="Trace CNQX", color="gray", ls="--", alpha=0.4)

        ax.plot(t_b, s_b, label="Baseline", color="#1f77b4", lw=2)
        ax.plot(t_p, s_p, label="Post-Induction", color="#d62728", alpha=0.8, lw=2)
        
        ax.axvspan(t_bsl_start, t_bsl_end, color='gray', alpha=0.1, label="Zone Zéro")
        ax.axvspan(p_start, p_end, color='purple', alpha=0.1, label="Fenêtre Pic & Aire")
        
        ax.set_xlim(x_range[0], x_range[1]); ax.set_ylim(y_range[0], y_range[1])
        ax.axhline(0, color='black', lw=1); ax.legend(); st.pyplot(fig)

    # --- BOUTON D'EXTRACTION (Fait le gros calcul une seule fois) ---
    if st.button("🚀 EXTRAIRE LES DONNÉES BRUTES", use_container_width=True):
        m_b = [get_metrics(abf_b, i, trace_cnqx_ref, (t_bsl_start, t_bsl_end), (p_start, p_end)) for i in abf_b.sweepList]
        m_p = [get_metrics(abf_p, i, trace_cnqx_ref, (t_bsl_start, t_bsl_end), (p_start, p_end)) for i in range(0, cnqx_s)]
        
        amp_b_tuple, area_b_tuple = zip(*m_b) if m_b else ([], [])
        amp_p_tuple, area_p_tuple = zip(*m_p) if m_p else ([], [])
        
        # Sauvegarde stricte dans la mémoire pour la réactivité
        st.session_state.extracted_data = {
            'amp_b': np.array(amp_b_tuple, dtype=float),
            'area_b': np.array(area_b_tuple, dtype=float),
            'amp_p': np.array(amp_p_tuple, dtype=float),
            'area_p': np.array(area_p_tuple, dtype=float)
        }

    # --- CALCULS DYNAMIQUES & AFFICHAGE (Onglets 2 et 3) ---
    if st.session_state.extracted_data is not None:
        data = st.session_state.extracted_data
        
        # 1. Recalcul dynamique du temps
        dt_m = delta_t / 60.0
        tm_b = np.arange(-len(data['amp_b']) + 1, 1) * dt_m
        tm_p = duree_induction + np.arange(1, len(data['amp_p']) + 1) * dt_m
        
        df = pd.DataFrame({
            'Time_min': np.concatenate([tm_b, tm_p]), 
            'Amp_raw': np.concatenate([data['amp_b'], data['amp_p']]),
            'Charge_raw': np.concatenate([data['area_b'], data['area_p']])
        })
        
        # 2. Recalcul dynamique de la normalisation
        mask_norm = (df['Time_min'] >= norm_start) & (df['Time_min'] <= norm_end)
        ref_amp = df[mask_norm]['Amp_raw'].mean()
        ref_ch = df[mask_norm]['Charge_raw'].mean()
        
        df['Amp_norm'] = (df['Amp_raw'] / ref_amp) * 100
        df['Charge_norm'] = (df['Charge_raw'] / ref_ch) * 100
        
        # 3. Recalcul dynamique du Binning
        df['Bin_id'] = np.floor(df['Time_min'] / bin_min)
        df_bin = df.groupby('Bin_id').agg({
            'Time_min':'mean', 
            'Amp_norm':['mean','sem'], 
            'Charge_norm':['mean','sem']
        })
        df_bin.columns = ['Time_avg', 'Amp_m', 'Amp_sem', 'Ch_m', 'Ch_sem']
        df_bin.fillna(0, inplace=True)
        
        df_bin['Amp_ci95'] = df_bin['Amp_sem'] * 1.96
        df_bin['Ch_ci95'] = df_bin['Ch_sem'] * 1.96

        # ONGLET 2 : DYNAMIQUE BRUTE
        with tab2:
            st.subheader("1. Données Brutes (Sweep par Sweep)")
            fig_r, (ax_r1, ax_r2) = plt.subplots(2, 1, figsize=(12, 10), sharex=True)
            
            ax_r1.scatter(tm_b, data['amp_b'], color='#1f77b4', s=15, alpha=0.5, label="Baseline")
            ax_r1.scatter(tm_p, data['amp_p'], color='black', s=15, alpha=0.5, label="Post")
            ax_r1.axvspan(0, duree_induction, color='gray', alpha=0.1, label="Induction")
            ax_r1.set_ylabel("Amplitude (Brute)"); ax_r1.legend()
            
            ax_r2.scatter(tm_b, data['area_b'], color='#2ca02c', s=15, alpha=0.5)
            ax_r2.scatter(tm_p, data['area_p'], color='black', s=15, alpha=0.5)
            ax_r2.axvspan(0, duree_induction, color='gray', alpha=0.1)
            ax_r2.set_ylabel("Charge/Aire (Brute)"); ax_r2.set_xlabel("Temps (min)")
            
            st.pyplot(fig_r)

        # ONGLET 3 : ANALYSE NORMALISÉE & EXPORT
        with tab3:
            st.subheader(f"2. Graphes Normalisés (Moyenne ± {error_type})")
            
            err_amp = df_bin['Amp_sem'] if error_type == "SEM" else df_bin['Amp_ci95']
            err_ch = df_bin['Ch_sem'] if error_type == "SEM" else df_bin['Ch_ci95']

            fig_n, (ax_n1, ax_n2) = plt.subplots(2, 1, figsize=(12, 10), sharex=True)
            
            # Graphe Amplitude
            ax_n1.scatter(df['Time_min'], df['Amp_norm'], color='lightgray', s=8, alpha=0.3)
            ax_n1.errorbar(df_bin['Time_avg'], df_bin['Amp_m'], yerr=err_amp, fmt='o', color='black', capsize=3, label=f"Moyenne ({error_type})")
            ax_n1.axvspan(norm_start, norm_end, color='#1f77b4', alpha=0.1, label="Période de Normalisation")
            ax_n1.axvspan(0, duree_induction, color='gray', alpha=0.15, label="Induction")
            ax_n1.axhline(100, color='red', ls='--', lw=1)
            ax_n1.set_ylabel("Amplitude (% Baseline)"); ax_n1.legend()
            
            # Graphe Aire
            ax_n2.scatter(df['Time_min'], df['Charge_norm'], color='lightblue', s=8, alpha=0.3)
            ax_n2.errorbar(df_bin['Time_avg'], df_bin['Ch_m'], yerr=err_ch, fmt='s', color='blue', capsize=3)
            ax_n2.axvspan(norm_start, norm_end, color='#1f77b4', alpha=0.1)
            ax_n2.axvspan(0, duree_induction, color='gray', alpha=0.15)
            ax_n2.axhline(100, color='red', ls='--', lw=1)
            ax_n2.set_ylabel("Charge (% Baseline)"); ax_n2.set_xlabel("Temps (min)")
            
            st.pyplot(fig_n)
            
            st.markdown("### Exportation")
            nom_export = st.text_input("Nom du fichier à exporter :", value=f"{final_portee_id}_{f_base.name.split('.')[0]}.csv")
            if not nom_export.endswith(".csv"):
                nom_export += ".csv"
                
            df_export = df_bin.copy().reset_index()
            df_export.insert(0, 'Portee', final_portee_id)
            df_export.insert(1, 'Source', f_base.name)
            
            st.download_button("💾 EXPORTER CSV COMPLET", df_export.to_csv(index=False), nom_export)

    if os.path.exists(path_b): os.remove(path_b)
    if os.path.exists(path_p): os.remove(path_p)