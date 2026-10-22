from ephys_analysis import analyze_epsc
from ephys_ui import recording_metadata, export_parameters
from ephys_ui import show_figure, logo_path as get_logo_path
from ephys_analysis import read_abf
from ephys_ui import session_compute
import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from scipy import signal, integrate, ndimage
import tempfile
import os
import hashlib
import pandas as pd

try:
    import pyabf
except ImportError:
    st.error("Le module pyabf n'est pas installé. Exécutez : pip install pyabf")

# --- CONFIGURATION ---

root_dir = os.path.dirname(os.path.abspath(__file__))
if os.path.basename(root_dir) == "pages":
    root_dir = os.path.dirname(root_dir)
logo_path = os.path.join(root_dir, "logo_chavis_final.png")

# --- INITIALISATIONS SÉCURISÉES ---
if 'ampa_fs_nyquist' not in st.session_state: st.session_state.ampa_fs_nyquist = 5000.0
if 'ampa_x_start' not in st.session_state: st.session_state.ampa_x_start = 0.0
if 'ampa_x_end' not in st.session_state: st.session_state.ampa_x_end = 2.0
if 'ampa_cutoff_val' not in st.session_state: st.session_state.ampa_cutoff_val = 2000
if 'ampa_analysis_results' not in st.session_state: st.session_state.ampa_analysis_results = None
if 'ampa_last_analysis_params' not in st.session_state: st.session_state.ampa_last_analysis_params = {}

# --- FONCTIONS MATHÉMATIQUES EXPERTES ---
def scroll_left():
    window = st.session_state.ampa_x_end - st.session_state.ampa_x_start
    shift = window * 0.8
    new_start = max(0.0, st.session_state.ampa_x_start - shift)
    st.session_state.ampa_x_end = new_start + window
    st.session_state.ampa_x_start = new_start

def scroll_right():
    window = st.session_state.ampa_x_end - st.session_state.ampa_x_start
    shift = window * 0.8
    st.session_state.ampa_x_start += shift
    st.session_state.ampa_x_end += shift




# --- TRADUCTION DE L'INTERFACE ---
lang = st.sidebar.selectbox("Language / Langue", ["Français", "English"])
T = {
    "Français": {
        "title": "sEPSC : Template Matching Itératif",
        "subtitle": "Double passe avec recentrage biologique et extraction du courant et de la charge synaptique.",
        "readme": "📖 Lire le README",
        "sb_1": "1. Prétraitement",
        "baseline": "Ligne de base",
        "dyn": "Detrending Dynamique",
        "stat": "Médiane Statique",
        "cutoff": "Coupure Bessel (Hz)",
        "sb_2": "2. Seuil de Détection",
        "zscore": "Seuil Z-Score (Robuste)",
        "sb_3": "3. Filtres Tier 1 (Empreinte)",
        "tier1_cap": "Sert à construire l'empreinte cellulaire.",
        "filt_amp": "Filtrer Amplitude",
        "min_amp": "Amplitude Min (pA)",
        "filt_rise": "Filtrer Rise Time",
        "max_rise": "Rise Time Max (ms)",
        "sb_4": "4. Visualisation",
        "zoom": "Zoom Y (pA)",
        "autoz": "Auto-ajustement axe Z",
        "nav": "**Navigation Temporelle X (s)**",
        "left": "⬅️ Gauche",
        "right": "Droite ➡️",
        "start": "Début (s)",
        "end": "Fin (s)",
        "up_btn": "Charger .abf",
        "msg_p2": "**Analyse Réussie !** Empreinte créée avec {} EPSC parfaits. **{} EPSC totaux détectés.**",
        "err_p1": "Pas assez d'événements clairs (<5) en Passe 1. Baissez le Seuil Z-Score.",
        "viz_tr": "Trace & Détections Itératives",
        "fp": "Empreinte Alignée",
        "norm": "Normalisé",
        "stat_glob": "Statistiques Globales",
        "freq": "Fréquence",
        "mean_amp": "Amplitude Moyenne (Scaled)",
        "mean_charge": "Charge Moyenne (pA·ms / fC)",
        "mean_rise": "Rise Time Moyen",
        "export_title": "💾 Exportation des Données (CSV)",
        "export_wait": "Les boutons de téléchargement CSV apparaîtront ici."
    },
    "English": {
        "title": "sEPSC: Iterative Template Matching",
        "subtitle": "Double pass with biological snapping and extraction of current and synaptic charge.",
        "readme": "📖 Read the README",
        "sb_1": "1. Preprocessing",
        "baseline": "Baseline Mode",
        "dyn": "Dynamic Detrending",
        "stat": "Static Median",
        "cutoff": "Bessel Cutoff (Hz)",
        "sb_2": "2. Detection Threshold",
        "zscore": "Robust Z-Score Threshold",
        "sb_3": "3. Tier 1 Filters (Fingerprint)",
        "tier1_cap": "Builds the cell fingerprint.",
        "filt_amp": "Filter Amplitude",
        "min_amp": "Min Amplitude (pA)",
        "filt_rise": "Filter Rise Time",
        "max_rise": "Max Rise Time (ms)",
        "sb_4": "4. Visualization",
        "zoom": "Y Zoom (pA)",
        "autoz": "Auto-scale Z axis",
        "nav": "**Temporal Navigation X (s)**",
        "left": "⬅️ Left",
        "right": "Right ➡️",
        "start": "Start (s)",
        "end": "End (s)",
        "up_btn": "Upload .abf",
        "msg_p2": "**Analysis Successful!** Fingerprint built with {} perfect EPSCs. **{} total EPSCs detected.**",
        "err_p1": "Not enough clear events (<5) in Tier 1. Lower the Z-Score Threshold.",
        "viz_tr": "Trace & Iterative Detections",
        "fp": "Aligned Fingerprint",
        "norm": "Normalized",
        "stat_glob": "Global Statistics",
        "freq": "Frequency",
        "mean_amp": "Mean Amplitude (Scaled)",
        "mean_charge": "Mean Charge (pA·ms / fC)",
        "mean_rise": "Mean Rise Time",
        "export_title": "💾 Data Export (CSV)",
        "export_wait": "CSV download buttons will appear here."
    }
}[lang]

# --- AFFICHAGE EN-TÊTE ---
col_logo, col_title = st.columns([1, 4])
with col_logo:
    if os.path.exists(logo_path): st.image(logo_path, width=150)
    else: st.write("🟢")
with col_title:
    st.title(f"🟢 {T['title']}")
    st.markdown(f"*{T['subtitle']}*")
st.divider()

# =========================================================================
# INTERCEPTION DU FICHIER (Pour synchroniser Nyquist et purger le cache)
# =========================================================================
file = st.file_uploader(T["up_btn"], type=["abf"])
st.caption("Analyse du premier sweep et du premier canal. Les exports des traces suivent la fenêtre de zoom affichée.")

if file:
    metadata = recording_metadata('ampa', file.name)
    file_bytes = file.getvalue()
    current_file_digest = hashlib.sha256(file_bytes).hexdigest()
    if st.session_state.get('ampa_current_file_digest') != current_file_digest:
        st.session_state.ampa_current_file_digest = current_file_digest
        try:
            abf_init = session_compute('ampa_abf', current_file_digest, lambda: read_abf(file_bytes))
            st.session_state.ampa_fs_nyquist = abf_init.dataRate / 2
            st.session_state.ampa_x_start = 0.0
            st.session_state.ampa_x_end = min(2.0, abf_init.sweepX[-1])
            st.session_state.ampa_analysis_results = None
        except Exception as exc:
            st.error(f'Fichier ABF illisible : {exc}')
            st.session_state.ampa_current_file_digest = None
            st.stop()

# --- CONFIGURATION INTERFACE SIDEBAR ---
st.sidebar.header(T["sb_1"])
baseline_mode = st.sidebar.radio(T["baseline"], [T["dyn"], T["stat"]], index=0)
use_bessel = st.sidebar.checkbox("Bessel Filter", value=True)

# SÉCURITÉ 1 : Bridage strict du slider Bessel par rapport au nouveau fichier
max_safe_cutoff = max(2, int(st.session_state.ampa_fs_nyquist * 0.95))
min_cutoff = min(100, max_safe_cutoff - 1)
st.session_state.ampa_cutoff_val = int(np.clip(st.session_state.ampa_cutoff_val, min_cutoff, max_safe_cutoff))
cutoff = st.sidebar.slider(T["cutoff"], min_cutoff, max_safe_cutoff, key="ampa_cutoff_val")
if file is not None and st.session_state.ampa_fs_nyquist < 105:
    st.sidebar.warning("Fréquence d'échantillonnage faible : la plage de coupure du filtre est limitée.")

st.sidebar.header(T["sb_2"])
threshold = st.sidebar.slider(T["zscore"], 1.0, 8.0, 3.0)

st.sidebar.header(T["sb_3"])
use_amp_filter = st.sidebar.checkbox(T["filt_amp"], value=True)
amp_limit = st.sidebar.number_input(T["min_amp"], min_value=0.0, value=10.0, step=1.0)
use_rise_filter = st.sidebar.checkbox(T["filt_rise"], value=True)
rise_limit = st.sidebar.number_input(T["max_rise"], value=4.0, step=0.1)

st.sidebar.header(T["sb_4"])
# Amplitude agrandie au cas où pour les très gros sEPSC
y_zoom = st.sidebar.slider(T["zoom"], -1000, 200, (-80, 20))
auto_z = st.sidebar.checkbox(T["autoz"], value=True)

st.sidebar.markdown(T["nav"])
col_b1, col_b2 = st.sidebar.columns(2)
col_b1.button(T["left"], on_click=scroll_left, use_container_width=True)
col_b2.button(T["right"], on_click=scroll_right, use_container_width=True)
col_x1, col_x2 = st.sidebar.columns(2)
col_x1.number_input(T["start"], step=0.1, key="ampa_x_start")
col_x2.number_input(T["end"], step=0.1, key="ampa_x_end")

# SÉCURITÉ 2 : Empêcher le crash Matplotlib si l'utilisateur inverse le Start et le End
if st.session_state.ampa_x_start >= st.session_state.ampa_x_end:
    st.error("Le début doit précéder la fin de la fenêtre.")
    st.stop()
x_zoom = (st.session_state.ampa_x_start, st.session_state.ampa_x_end)

export_container = st.container()

# =========================================================================
# TRAITEMENT ALGORITHMIQUE SÉCURISÉ EN CACHE (Ne s'exécute pas au zoom Y)
# =========================================================================
if file:
    current_analysis_params = {
        'file_name': file.name, 'baseline_mode': baseline_mode, 'use_bessel': use_bessel,
        'cutoff': st.session_state.ampa_cutoff_val, 'threshold': threshold, 
        'use_amp_filter': use_amp_filter, 'amp_limit': amp_limit, 
        'use_rise_filter': use_rise_filter, 'rise_limit': rise_limit
    }
    
    need_recomputation = (st.session_state.ampa_analysis_results is None or 
                          st.session_state.ampa_last_analysis_params != current_analysis_params)

    if need_recomputation:
        with st.spinner("Analyse et détection itérative en cours..."):
            st.session_state.ampa_analysis_results = None
            try:
                abf = session_compute('ampa_abf', current_file_digest, lambda: read_abf(file_bytes))
                computed = analyze_epsc(abf, baseline_mode == T['dyn'], use_bessel, cutoff, threshold,
                                        use_amp_filter, amp_limit, use_rise_filter, rise_limit)
                computed['msg'] = T['msg_p2'].format(len(computed['valid_ev_base']),len(computed['valid_ev_iter'])) if computed['has_waveforms'] else T['err_p1']
                st.session_state.ampa_analysis_results = computed
                st.session_state.ampa_last_analysis_params = current_analysis_params

            except Exception as e:
                st.error(f"Error during analysis: {e}")


    # =========================================================================
    # AFFICHAGE ULTRA-RAPIDE (S'exécute en quelques ms lors d'un zoom Y ou X)
    # =========================================================================
    res = st.session_state.ampa_analysis_results
    if res:
        if res['has_waveforms']:
            st.success(res['msg'])
            col_graph1, col_graph2 = st.columns([3, 1])
            with col_graph1:
                st.subheader(T["viz_tr"])
                fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 6), sharex=True, gridspec_kw={'height_ratios':[2,1]})
                
                visible = (res['times'] >= x_zoom[0]) & (res['times'] <= x_zoom[1])
                ax1.plot(res['times'][visible], res['f_data'][visible], color='black', lw=0.5)
                ax1.plot([e['time'] for e in res['valid_ev_iter']], [res['f_data'][e['idx']] for e in res['valid_ev_iter']], 'o', color='#FF8C00', markersize=5)
                ax1.set_ylim(y_zoom)
                ax1.set_xlim(x_zoom)
                ax1.set_ylabel("Amplitude (pA)")

                ax2.plot(res['times'][visible], res['corr_z_iter'][visible], color='blue', alpha=0.6)
                ax2.axhline(threshold, color='red', ls='--')
                ax2.set_ylabel("Robust Z-Score")
                ax2.set_xlim(x_zoom)
                
                if auto_z:
                    mask = (res['times'] >= st.session_state.ampa_x_start) & (res['times'] <= st.session_state.ampa_x_end)
                    if np.any(mask):
                        z_local = res['corr_z_iter'][mask]
                        z_min, z_max = np.min(z_local), np.max(z_local)
                        margin = abs(z_max - z_min) * 0.15 if z_max != z_min else 1.0
                        ax2.set_ylim(z_min - margin, z_max + margin)
                show_figure(fig, key="ampa_1")
                plt.close(fig) # SÉCURITÉ : Empêche la fuite de mémoire RAM

            with col_graph2:
                st.subheader(T["fp"])
                fig_avg, ax_avg = plt.subplots(figsize=(4, 6))
                t_avg = np.arange(len(res['avg_waveform'])) * res['dt']
                ax_avg.plot(t_avg, -res['avg_waveform'], color='red', lw=2)
                ax_avg.set_title(f"n={len(res['valid_ev_base'])}")
                ax_avg.set_xlabel("Time (ms)" if lang=="English" else "Temps (ms)")
                ax_avg.set_ylabel(T["norm"])
                ax_avg.grid(True, alpha=0.3)
                show_figure(fig_avg, key="ampa_2")
                plt.close(fig_avg)
        else:
            st.error(res['msg'])

        if res['has_waveforms'] and not res['valid_ev_iter']:
            st.info('Aucun événement retenu en seconde passe avec ces paramètres.')
            empty_summary = pd.DataFrame([dict(metadata, Frequency_Hz=0., N_Events=0, Mean_Amplitude_pA=np.nan, Mean_Charge_fC=np.nan, Mean_Rise_ms=np.nan)])
            st.download_button('Exporter le résumé par cellule', empty_summary.to_csv(index=False), file.name+'_Summary.csv')
            export_parameters(dict(metadata=metadata, sha256=current_file_digest, analysis=current_analysis_params, sweep=0), key='ampa')
        if len(res['valid_ev_iter']) > 0:
            df_iter = pd.DataFrame(res['valid_ev_iter'])
            st.divider()
            
            duration_s = len(res['times']) / res['fs']
            freq_hz = len(df_iter) / duration_s if duration_s > 0 else np.nan
            export_parameters(dict(metadata=metadata, sha256=current_file_digest, analysis=current_analysis_params, sweep=0, duration_s=duration_s), key='ampa')
            summary = pd.DataFrame([dict(metadata, Frequency_Hz=freq_hz, N_Events=len(df_iter), Mean_Amplitude_pA=df_iter.amp_scaled.mean(), Mean_Charge_fC=df_iter.charge_scaled.mean(), Mean_Rise_ms=df_iter.rise.mean())])
            st.download_button('Exporter le résumé par cellule', summary.to_csv(index=False), file.name+'_Summary.csv')
            st.subheader(f"{T['stat_glob']} | n={len(df_iter)}")
            
            c1, c2, c3, c4 = st.columns(4)
            c1.metric(T["freq"], f"{freq_hz:.2f} Hz")
            c2.metric(T["mean_amp"], f"{df_iter['amp_scaled'].mean():.2f} pA")
            c3.metric(T["mean_charge"], f"{df_iter['charge_scaled'].mean():.2f}")
            c4.metric(T["mean_rise"], f"{df_iter['rise'].mean():.2f} ms")
            
            with export_container:
                st.subheader(T["export_title"])
                col_exp1, col_exp2, col_exp3 = st.columns(3)
                
                df_base = pd.DataFrame(res['valid_ev_base'])
                csv_base = df_base.assign(**metadata).to_csv(index=False).encode('utf-8')
                col_exp1.download_button(label="📁 CSV - Base (Tier 1)", data=csv_base, file_name='sEPSC_Base.csv', mime='text/csv')

                csv_iter = df_iter[['time', 'amp_scaled', 'charge_scaled', 'rise', 'iei']].assign(**metadata).to_csv(index=False).encode('utf-8')
                col_exp2.download_button(label="📁 CSV - Iterative (Tier 2)", data=csv_iter, file_name='sEPSC_Iterative_Results.csv', mime='text/csv')
                
                n_bins = 25
                counts_amp, bins_amp = np.histogram(df_iter['amp_scaled'], bins=n_bins)
                counts_rise, bins_rise = np.histogram(df_iter['rise'], bins=n_bins)
                iei_clean = df_iter['iei'].dropna()
                counts_iei, bins_iei = np.histogram(iei_clean, bins=n_bins) if not iei_clean.empty else (np.zeros(n_bins), np.zeros(n_bins+1))

                df_export_summary = pd.DataFrame({
                    'Amp_Bin_Center_pA': (bins_amp[:-1] + bins_amp[1:]) / 2, 'Amp_Counts': counts_amp,
                    'Rise_Bin_Center_ms': (bins_rise[:-1] + bins_rise[1:]) / 2, 'Rise_Counts': counts_rise,
                    'IEI_Bin_Center_ms': (bins_iei[:-1] + bins_iei[1:]) / 2, 'IEI_Counts': counts_iei
                })
                csv_summary = df_export_summary.to_csv(index=False).encode('utf-8')
                col_exp3.download_button(label="📊 CSV - Distributions", data=csv_summary, file_name='sEPSC_distributions.csv', mime='text/csv')

            fig2, (ha, hb, hc) = plt.subplots(1, 3, figsize=(15, 4))
            ha.bar((bins_amp[:-1] + bins_amp[1:]) / 2, counts_amp, width=(bins_amp[1]-bins_amp[0])*0.9, color='gray')
            ha.set_title("Amplitude Scaled (pA)")
            hb.bar((bins_rise[:-1] + bins_rise[1:]) / 2, counts_rise, width=(bins_rise[1]-bins_rise[0])*0.9, color='#FF8C00')
            hb.set_title("Rise Time 10-90% (ms)")
            if not iei_clean.empty:
                hc.bar((bins_iei[:-1] + bins_iei[1:]) / 2, counts_iei, width=(bins_iei[1]-bins_iei[0])*0.9, color='salmon')
                hc.set_title("IEI (ms)")
            show_figure(fig2, key="ampa_3")
            plt.close(fig2)

else:
    with export_container:
        st.subheader(T["export_title"])
        st.info(T["export_wait"])
