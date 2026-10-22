from ephys_ui import recording_metadata, export_parameters
from ephys_ui import show_figure, logo_path as get_logo_path
from ephys_analysis import read_abf, analyze_ipsc
from ephys_io import digest
from ephys_ui import session_compute
import streamlit as st
from ephys_tutorials import render_beginner_guide
import numpy as np
import matplotlib.pyplot as plt
from scipy import signal, optimize, integrate, ndimage
import tempfile
import os
import pandas as pd

try:
    import pyabf
except ImportError:
    st.error("Le module pyabf n'est pas installé. Exécutez : pip install pyabf")

# --- CONFIGURATION ---

# Initialisation de la mémoire (Session State) pour la navigation temporelle
if 'gaba_fs_nyquist' not in st.session_state:
    st.session_state.gaba_fs_nyquist = 5000.0
if 'gaba_x_start' not in st.session_state:
    st.session_state.gaba_x_start = 0.0
if 'gaba_x_end' not in st.session_state:
    st.session_state.gaba_x_end = 2.0
if 'gaba_cutoff_val' not in st.session_state:
    st.session_state.gaba_cutoff_val = 2000

# --- FONCTIONS DE NAVIGATION (Callbacks) ---
def scroll_left():
    window = st.session_state.gaba_x_end - st.session_state.gaba_x_start
    shift = window * 0.8
    new_start = max(0.0, st.session_state.gaba_x_start - shift)
    st.session_state.gaba_x_end = new_start + window
    st.session_state.gaba_x_start = new_start

def scroll_right():
    window = st.session_state.gaba_x_end - st.session_state.gaba_x_start
    shift = window * 0.8
    st.session_state.gaba_x_start += shift
    st.session_state.gaba_x_end += shift

# --- LANGUAGE SELECTION ---
lang = st.session_state.get("global_language", "Français")
render_beginner_guide("gaba", lang)

T = {
    "English": {
        "title": "# Expert Electrophysiology Pipeline",
        "sb_preproc": "1. Preprocessing & Polarity",
        "polarity": "Signal Polarity",
        "pol_out": "Outward (Positive, e.g. IPSC at 0mV)",
        "pol_in": "Inward (Negative, e.g. EPSC or IPSC high Cl-)",
        "baseline_method": "Baseline Mode",
        "dyn_detrend": "Dynamic Detrending (Median)",
        "stat_detrend": "Static Global Median",
        "cutoff": "Bessel Cutoff (Hz)",
        "sb_detec": "2. Detection Threshold",
        "threshold": "Z-Score Threshold",
        "sb_kinetics": "3. Kinetics Filters",
        "decay_thresh": "Max Decay (ms)",
        "rise_thresh": "Max Rise Time (ms)",
        "amp_filter": "Min Absolute Amplitude (pA)",
        "sb_viz": "4. Visualization & Navigation",
        "zoom_y": "Zoom Y (pA)",
        "gaba_x_start": "Start (s)",
        "gaba_x_end": "End (s)",
        "auto_z": "Auto-scale Z-score axis",
        "viz_header": "Visualization & Detection",
        "btn_left": "⬅️ Left",
        "btn_right": "Right ➡️"
    },
    "Français": {
        "title": "# Pipeline Expert Électrophysiologie",
        "sb_preproc": "1. Prétraitement & Polarité",
        "polarity": "Polarité du Signal",
        "pol_out": "Sortant (Positif, ex: IPSC à 0mV)",
        "pol_in": "Entrant (Négatif, ex: EPSC ou IPSC haut Cl-)",
        "baseline_method": "Mode de Ligne de Base",
        "dyn_detrend": "Detrending Dynamique (Médiane)",
        "stat_detrend": "Médiane Globale Statique",
        "cutoff": "Coupure Bessel (Hz)",
        "sb_detec": "2. Seuil de Détection",
        "threshold": "Seuil Z-Score",
        "sb_kinetics": "3. Filtres Cinétiques",
        "decay_thresh": "Decay Max (ms)",
        "rise_thresh": "Rise Time Max (ms)",
        "amp_filter": "Amplitude Absolue Min (pA)",
        "sb_viz": "4. Visualisation & Navigation",
        "zoom_y": "Zoom Y (pA)",
        "gaba_x_start": "Début (s)",
        "gaba_x_end": "Fin (s)",
        "auto_z": "Auto-ajustement axe Z",
        "viz_header": "Visualisation & Détection",
        "btn_left": "⬅️ Gauche",
        "btn_right": "Droite ➡️"
    }
}[lang]

st.title(T["title"])
st.divider()

file = st.file_uploader("Charger .abf", type=["abf"])
if file:
    payload = file.getvalue()
    identity = digest(payload)
    try:
        abf = session_compute('ipsc_abf', identity, lambda: read_abf(payload))
    except Exception as exc:
        st.error(f'Lecture ABF impossible : {exc}'); st.stop()
    if st.session_state.get('gaba_file_digest') != identity:
        st.session_state.gaba_file_digest = identity
        st.session_state.gaba_fs_nyquist = abf.dataRate / 2
        st.session_state.gaba_x_start = 0.0
        st.session_state.gaba_x_end = min(2.0, abf.sweepX[-1])
st.caption('Analyse du premier sweep et du premier canal. Les exports des traces suivent la fenêtre de zoom affichée.')

# --- SIDEBAR ---
st.sidebar.header(T["sb_preproc"])
polarity = st.sidebar.radio(T["polarity"], [T["pol_out"], T["pol_in"]], index=1)
is_outward = (polarity == T["pol_out"])
baseline_mode = st.sidebar.radio(T["baseline_method"], [T["dyn_detrend"], T["stat_detrend"]], index=0)
use_bessel = st.sidebar.checkbox("Bessel Filter", value=True)
max_cutoff = max(2, int(st.session_state.gaba_fs_nyquist * 0.95))
min_cutoff = min(100, max_cutoff - 1)
st.session_state.gaba_cutoff_val = int(np.clip(st.session_state.gaba_cutoff_val, min_cutoff, max_cutoff))
cutoff = st.sidebar.slider(T["cutoff"], min_cutoff, max_cutoff, key="gaba_cutoff_val")

st.sidebar.header(T["sb_detec"])
threshold = st.sidebar.slider(T["threshold"], 1.0, 8.0, 2.5)

st.sidebar.header(T["sb_kinetics"])
use_amp_filter = st.sidebar.checkbox("Filter Amplitude", value=True)
# CORRECTION ICI : min_value=0.0 et libellé "Amplitude Absolue"
amp_limit = st.sidebar.number_input(T["amp_filter"], min_value=0.0, value=5.0 if is_outward else 7.0, step=1.0)

use_decay_filter = st.sidebar.checkbox("Filter Decay", value=True)
decay_limit = st.sidebar.number_input(T["decay_thresh"], value=50.0 if is_outward else 4.0, step=1.0)

use_rise_filter = st.sidebar.checkbox("Filter Rise Time", value=True)
rise_limit = st.sidebar.number_input(T["rise_thresh"], value=5.0 if is_outward else 1.5, step=0.1)

st.sidebar.header(T["sb_viz"])
y_default = (-50, 200) if is_outward else (-200, 50)
y_zoom = st.sidebar.slider(T["zoom_y"], -400, 400, y_default)

auto_z = st.sidebar.checkbox(T["auto_z"], value=True)

# Navigation Temporelle (Boutons + Inputs)
st.sidebar.markdown("**Navigation Temporelle X (s)**")
col_b1, col_b2 = st.sidebar.columns(2)
col_b1.button(T["btn_left"], on_click=scroll_left, use_container_width=True)
col_b2.button(T["btn_right"], on_click=scroll_right, use_container_width=True)

col_x1, col_x2 = st.sidebar.columns(2)
col_x1.number_input(T["gaba_x_start"], step=0.1, key="gaba_x_start")
col_x2.number_input(T["gaba_x_end"], step=0.1, key="gaba_x_end")

if st.session_state.gaba_x_start >= st.session_state.gaba_x_end:
    st.sidebar.error("Le début doit être inférieur à la fin.")
    st.stop()
x_zoom = (st.session_state.gaba_x_start, st.session_state.gaba_x_end)


# --- ANALYSE ---


if file:
    metadata = recording_metadata('gaba', file.name)
    payload = file.getvalue()
    identity = digest(payload)
    try:
        abf = session_compute('ipsc_abf', identity, lambda: read_abf(payload))
        st.session_state.gaba_fs_nyquist = abf.dataRate / 2
        params = (identity, baseline_mode == T['dyn_detrend'], use_bessel, cutoff, is_outward, threshold,
                  use_amp_filter, amp_limit, use_decay_filter, decay_limit, use_rise_filter, rise_limit)
        res = session_compute('ipsc_results', params, lambda: analyze_ipsc(abf, *params[1:]))
        fs, times, dt = res['fs'], res['times'], res['dt']
        f_data, corr_z, valid_ev = res['f_data'], res['corr_z'], res['valid_ev']
        # --- PLOTTING ---
        st.subheader(T["viz_header"])
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), sharex=True, gridspec_kw={'height_ratios':[2,1]})
        
        visible = (times >= x_zoom[0]) & (times <= x_zoom[1])
        ax1.plot(times[visible], f_data[visible], color='black', lw=0.5)
        
        if valid_ev:
            ax1.plot([e['time'] for e in valid_ev], [f_data[e['idx']] for e in valid_ev], 'o', color='purple' if is_outward else '#FF8C00', markersize=5)

        ax1.set_ylim(y_zoom)
        ax1.set_xlim(x_zoom)
        ax1.set_ylabel("pA")

        ax2.plot(times[visible], corr_z[visible], color='blue', alpha=0.6)
        ax2.axhline(threshold, color='red', ls='--')
        ax2.set_ylabel("Z-Score")
        
        if auto_z:
            mask = (times >= st.session_state.gaba_x_start) & (times <= st.session_state.gaba_x_end)
            if np.any(mask):
                z_local = corr_z[mask]
                z_min, z_max = np.min(z_local), np.max(z_local)
                margin = abs(z_max - z_min) * 0.15 if z_max != z_min else 1.0
                ax2.set_ylim(z_min - margin, z_max + margin)

        show_figure(fig, key="gaba_1")
        
        # --- EXPORT ---
        if not valid_ev:
            st.info('Aucun événement retenu avec ces paramètres.')
            empty_summary = pd.DataFrame([dict(metadata, Frequency_Hz=0., N_Events=0, Mean_Amplitude_pA=np.nan, Mean_Charge_fC=np.nan, Mean_Rise_ms=np.nan)])
            st.download_button('Exporter le résumé par cellule', empty_summary.to_csv(index=False), file.name+'_Summary.csv')
            export_parameters(dict(metadata=metadata, sha256=identity, parameters=params, sweep=0), key='gaba')
        if valid_ev:
            df = pd.DataFrame(valid_ev)
            st.divider()
            
            duration_s = len(times) / fs
            freq_hz = len(df) / duration_s if duration_s > 0 else np.nan
            export_parameters(dict(metadata=metadata, sha256=identity, parameters=params, sweep=0, duration_s=duration_s), key='gaba')
            summary = pd.DataFrame([dict(metadata, Frequency_Hz=freq_hz, N_Events=len(df), Mean_Amplitude_pA=df.amp.mean(), Mean_Charge_fC=df.area.mean(), Mean_Rise_ms=df.rise.mean())])
            st.download_button('Exporter le résumé par cellule', summary.to_csv(index=False), file.name+'_Summary.csv')
            st.subheader(f"Total Events: {len(valid_ev)} | Freq: {freq_hz:.2f} Hz")
            
            col_exp1, col_exp2 = st.columns(2)
            df_export = df[['time', 'amp', 'rise', 'decay', 'area', 'iei']].assign(**metadata)
            col_exp1.download_button(label="📁 Download Events (CSV)", data=df_export.to_csv(index=False).encode('utf-8'), file_name='events.csv', mime='text/csv')

    except Exception as e: st.error(f"Error: {e}")

