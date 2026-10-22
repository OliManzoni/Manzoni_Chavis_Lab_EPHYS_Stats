from ephys_ui import recording_metadata, export_parameters
from ephys_ui import show_figure, logo_path as get_logo_path
from ephys_analysis import read_abf, analyze_spikes
from ephys_io import digest
from ephys_ui import session_compute
import streamlit as st
from ephys_tutorials import render_beginner_guide
import pyabf
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.signal import find_peaks
from scipy.ndimage import gaussian_filter1d
import tempfile
import os

# --- CONFIGURATION DE LA PAGE ---

# --- GESTION DU BILINGUISME ---
lang = st.session_state.get("global_language", "Français")
render_beginner_guide("spikes", lang)

T = {
    "title": {"Français": "Pipeline Expert : Excitabilité & Morphométrie", "English": "Expert Pipeline: Excitability & Morphometry"},
    "subtitle": {"Français": "Analyse de la Plasticité Synaptique | Standard de Publication", "English": "Synaptic Plasticity Analysis | Publication Standard"},
    "load": {"Français": "📂 1. Chargement", "English": "📂 1. Upload File"},
    "upload_btn": {"Français": "Charger un fichier ABF", "English": "Upload an ABF file"},
    "settings": {"Français": "⚙️ 2. Réglages de Détection", "English": "⚙️ 2. Detection Settings"},
    "spike_th": {"Français": "Seuil de détection (mV)", "English": "Spike detection threshold (mV)"},
    "dvdt_th": {"Français": "Seuil dV/dt (mV/ms)", "English": "dV/dt threshold (mV/ms)"},
    "global_metrics": {"Français": "📊 Propriétés Intrinsèques Globales", "English": "📊 Global Intrinsic Properties"},
    "rheo_th": {"Français": "Rhéobase (Seuil)", "English": "Rheobase (Threshold)"},
    "visuals": {"Français": "📈 Visualisations des Traces & Courbes", "English": "📈 Trace & Curve Visualizations"},
    "select_sweep": {"Français": "Sélectionner un Sweep individuel", "English": "Select individual Sweep"},
    "select_overlay": {"Français": "Sélectionner les sweeps pour l'Overlay", "English": "Select sweeps for Overlay"},
    "morph_title": {"Français": "⚡ Morphologie du 1er PA pour le Sweep", "English": "⚡ 1st AP Morphometry for Sweep"},
    "no_ap": {"Français": "Trace Passive : Aucun Potentiel d'Action détecté.", "English": "Passive Trace: No Action Potential detected."},
    "export": {"Français": "📥 Exportation des Résultats", "English": "📥 Export Results"},
    "exp_global": {"Français": "💾 Exporter le Profil Global (CSV)", "English": "💾 Export Global Profile (CSV)"},
    "exp_sweeps": {"Français": "💾 Exporter les Données par Sweep (CSV)", "English": "💾 Export Sweep Data (CSV)"},
    "readme_title": {"Français": "📚 README, Formalisme & Citation", "English": "📚 README, Formalism & Citation"}
}

# --- EN-TÊTE INSTITUTIONNEL ---
col_l, col_r = st.columns([2, 5]) 
with col_l:
    try: st.image(get_logo_path(), width=360) 
    except: st.info("Chavis-Manzoni Lab") 
with col_r:
    st.markdown(f"# {T['title'][lang]}")
    st.markdown(f"### {T['subtitle'][lang]}")

st.divider()

# --- BLOC ACCÈS RAPIDE : MÉTHODES ET INFORMATION BIOPHYSIQUE ---
with st.expander("ℹ️ **Information Biophysique, Méthodologie & Raccourcis / Biophysical Methods & Shortcuts**", expanded=False):
    if lang == "Français":
        st.markdown("""
        ### 🔬 Résumé Méthodologique
        * **Seuil d'initiation (Threshold) :** Calculé sur le premier potentiel d'action via la méthode de la première dérivée ($dV/dt \\ge 15$ mV/ms).
        * **AHP (Post-hyperpolarisation) :** Mesurée de manière robuste à l'aide d'une fenêtre glissante de 50 ms après le pic, protégée contre le bruit de crête par une période réfractaire de 3 ms. L'amplitude est calculée relativement au seuil du PA.
        * **Résistance d'entrée ($R_{in}$) :** Déterminée par régression linéaire sur la courbe Courant-Voltage des échelons hyperpolarisants.
        * **Bloc de dépolarisation (*Depolarization Block*) :** Détecté automatiquement si le potentiel stationnaire d'un échelon dépolarisation dépasse $-45$ mV et provoque un arrêt de la décharge. Ces traces anormales sont automatiquement écartées des analyses et des fichiers d'exports. **Ne s'applique qu'après avoir atteint la rhéobase.**
        
        👉 **[Aller directement au README complet au bas de la page](#readme-formalise-citation)**
        """)
    else:
        st.markdown("""
        ### 🔬 Methodological Summary
        * **Spike Initiation Threshold:** Calculated on the first action potential using the first derivative method ($dV/dt \\ge 15$ mV/ms).
        * **AHP (After-Hyperpolarization):** Measured robustly using a 50 ms sliding window post-peak, protected against crest noise via a 3 ms refractory period. Amplitude is computed relative to the spike threshold.
        * **Input Resistance ($R_{in}$):** Determined by linear regression on the hyperpolarizing current-voltage relationship steps.
        * **Depolarization Block:** Automatically flagged if the steady-state potential during a depolarizing step exceeds $-45$ mV and causes cessation of firing. These traces are automatically excluded from curves and exports. **Only applies after rheobase is reached.**
        
        👉 **[Jump directly to the comprehensive README at the bottom](#readme-formalise-citation)**
        """)

# --- BARRE LATÉRALE ---
st.sidebar.header(T["load"][lang])
uploaded_file = st.sidebar.file_uploader(T["upload_btn"][lang], type=["abf"])

st.sidebar.header(T["settings"][lang])
spike_threshold = st.sidebar.number_input(T["spike_th"][lang], value=0.0)
dvdt_threshold = st.sidebar.number_input(T["dvdt_th"][lang], value=15.0)

if uploaded_file is not None:
    metadata = recording_metadata('spikes', uploaded_file.name)
    payload = uploaded_file.getvalue()
    identity = digest(payload)
    try:
        abf = session_compute('spike_abf', identity, lambda: read_abf(payload))
        result = session_compute('spike_results', (identity, spike_threshold, dvdt_threshold), lambda: analyze_spikes(abf, spike_threshold, dvdt_threshold))
        unit_i = result['unit_i']
        unit_v = result['unit_v']
        sr = result['sr']
        dt_ms = result['dt_ms']
        idx_start = result['idx_start']
        idx_end = result['idx_end']
        courants = result['courants']
        v_stat = result['v_stat']
        v_peak = result['v_peak']
        v_rest_list = result['v_rest_list']
        n_spikes = result['n_spikes']
        v_thresh_list = result['v_thresh_list']
        ap_amps = result['ap_amps']
        ap_widths = result['ap_widths']
        ap_rise = result['ap_rise']
        ap_decay = result['ap_decay']
        ap_ahp = result['ap_ahp']
        sweep_all_ahps_indices = result['sweep_all_ahps_indices']
        excluded_sweeps = result['excluded_sweeps']
        is_excluded_list = result['is_excluded_list']
        valid_indices = result['valid_indices']
        v_rest_final = result['v_rest_final']
        rin = result['rin']
        tau = result['tau']
        rheo_idx_global = result['rheo_idx_global']
        rheo_v = result['rheo_v']
        rheo_i = result['rheo_i']
        # --- INDICATION DES TRACES EXCLUES (DEPOLARIZATION BLOCK) ---
        if excluded_sweeps:
            st.warning(f"⚠️ **Depolarization Block détecté !** Les sweeps suivants ont été exclus de l'analyse globale et des courbes : {', '.join([str(s) for s in excluded_sweeps])}" if lang == "Français" else f"⚠️ **Depolarization Block detected!** The following sweeps have been excluded from global analysis and curves: {', '.join([str(s) for s in excluded_sweeps])}")
        else:
            st.success("✅ Aucun Depolarization Block détecté." if lang == "Français" else "✅ No Depolarization Block detected.")

        # --- DASHBOARD ---
        st.subheader(T["global_metrics"][lang])
        c1, c2, c4, c5 = st.columns(4)
        c1.metric("Vrest", f"{v_rest_final:.1f} mV")
        c2.metric("Rin", f"{rin:.1f} MΩ")
        c4.metric("Tau_m", f"{tau:.1f} ms")
        c5.metric(T["rheo_th"][lang], f"{rheo_v:.1f} mV" if not np.isnan(rheo_v) else "N/A")

        st.divider()

        # --- VISUALISATION INTERACTIVE ---
        st.subheader(T["visuals"][lang])
        
        col_v1, col_v2 = st.columns(2)
        with col_v1:
            if abf.sweepCount > 1:
                default_sw = int(rheo_idx_global) if rheo_idx_global is not None else 0
                default_sw = min(max(default_sw, 0), abf.sweepCount - 1) 
                sw_idx = st.slider(T["select_sweep"][lang], 0, abf.sweepCount-1, default_sw)
            else:
                sw_idx = 0
                st.info("Fichier à Sweep unique (Gap-free).")
                
        with col_v2:
            if abf.sweepCount == 1:
                default_stk = [0]
            elif abf.sweepCount == 2:
                default_stk = [0, 1]
            else:
                default_stk = [0, abf.sweepCount//2, abf.sweepCount-1]
                
            stk_indices = st.multiselect(T["select_overlay"][lang], list(range(abf.sweepCount)), default=default_stk)
        
        # Warning visuel individuel si l'utilisateur regarde une trace exclue
        if sw_idx in excluded_sweeps:
            st.warning(f"⚠️ **Attention : Le sweep {sw_idx} sélectionné est marqué comme Depolarization Block et est exclu des analyses macro.**")
            
        st.markdown(f"**{T['morph_title'][lang]} {sw_idx} ({courants[sw_idx]:.1f} {unit_i})**")
        
        if n_spikes[sw_idx] > 0:
            c_ap1, c_ap2, c_ap3, c_ap4, c_ap5 = st.columns(5)
            c_ap1.metric("Amplitude", f"{ap_amps[sw_idx]:.1f} mV")
            c_ap2.metric("Half-Width", f"{ap_widths[sw_idx]:.2f} ms")
            c_ap3.metric("Rise (10-90%)", f"{ap_rise[sw_idx]:.2f} ms")
            c_ap4.metric("Decay (90-10%)", f"{ap_decay[sw_idx]:.2f} ms")
            ahp_relative = v_thresh_list[sw_idx] - ap_ahp[sw_idx] if not np.isnan(v_thresh_list[sw_idx]) else np.nan
            c_ap5.metric("AHP Amplitude", f"{ahp_relative:.1f} mV" if not np.isnan(ahp_relative) else "N/A")
        else:
            st.info(T["no_ap"][lang])
            
        st.write("") 
        
        plt.style.use('seaborn-v0_8-white')
        fig = plt.figure(figsize=(16, 10))
        gs = fig.add_gridspec(2, 2)
        
        ax1 = fig.add_subplot(gs[0, 0])
        abf.setSweep(sw_idx)
        ax1.plot(abf.sweepX, abf.sweepY, color='black', lw=1)
        
        if not np.isnan(v_thresh_list[sw_idx]):
            ax1.axhline(v_thresh_list[sw_idx], color='red', ls='--', alpha=0.6, label="Threshold dV/dt")
            
            indices_to_plot = sweep_all_ahps_indices[sw_idx]
            if indices_to_plot:
                ax1.plot(abf.sweepX[indices_to_plot], abf.sweepY[indices_to_plot], 'bx', markersize=8, markeredgewidth=2, label="AHP Min")
                
            ax1.legend(loc='upper right')
            
        ax1.set_title(f"Sweep {sw_idx} " + ("(EXCLU - Depolarization Block)" if sw_idx in excluded_sweeps else ""), fontweight='bold')
        ax1.set_ylabel("mV")

        ax2 = fig.add_subplot(gs[0, 1])
        cmap = plt.colormaps.get_cmap('viridis')
        for i, s in enumerate(stk_indices):
            abf.setSweep(s)
            ax2.plot(abf.sweepX, abf.sweepY, color=cmap(i/max(1, len(stk_indices))), alpha=0.8, lw=0.8)
        ax2.set_title(f"Overlay ({len(stk_indices)} traces)", fontweight='bold')
        ax2.set_ylabel("mV")

        # Extraction des tableaux propres sans traces aberrantes pour les courbes
        valid_courants = [courants[idx] for idx in valid_indices]
        valid_v_stat = [v_stat[idx] for idx in valid_indices]
        valid_v_peak = [v_peak[idx] for idx in valid_indices]
        valid_n_spikes = [n_spikes[idx] for idx in valid_indices]

        ax3 = fig.add_subplot(gs[1, 0])
        ax3.plot(valid_courants, valid_v_stat, 'o-', color='tab:blue', label="Steady-state")
        ax3.plot(valid_courants, valid_v_peak, 'x--', color='tab:blue', alpha=0.5, label="Peak (Sag)")
        if sw_idx in valid_indices:
            ax3.plot(courants[sw_idx], v_stat[sw_idx], 'ro', markersize=9, zorder=5) 
        ax3.set_title("I-V Curve (Cleaned)", fontweight='bold')
        ax3.set_xlabel(f"Current ({unit_i})"); ax3.set_ylabel("mV"); ax3.legend()

        ax4 = fig.add_subplot(gs[1, 1])
        ax4.plot(valid_courants, valid_n_spikes, 's-', color='tab:orange')
        if sw_idx in valid_indices:
            ax4.plot(courants[sw_idx], n_spikes[sw_idx], 'ro', markersize=9, zorder=5) 
        ax4.set_title("f-I Curve (Cleaned)", fontweight='bold')
        ax4.set_xlabel(f"Current ({unit_i})"); ax4.set_ylabel("Spike count")
        
        show_figure(fig, key="spikes_1")

        # --- EXPORT ---
        st.divider()
        st.subheader(T["export"][lang])
        col_exp1, col_exp2 = st.columns(2)
        
        # Fichier d'exportation global mis à jour avec l'unité de courant
        df_global = pd.DataFrame({
            "File": [uploaded_file.name], 
            "Vrest_mV": [v_rest_final], 
            "Rin_MOhms": [rin],
            "Tau_ms": [tau], 
            f"Rheobase_I_{unit_i}": [rheo_i], 
            "Rheobase_mV": [rheo_v]
        })
        for name, value in metadata.items(): df_global[name] = value
        col_exp1.download_button(T["exp_global"][lang], df_global.to_csv(index=False).encode('utf-8'), f"{uploaded_file.name}_Global.csv", use_container_width=True)

        ap_ahp_relative = [v_t - a if not np.isnan(v_t) and not np.isnan(a) else np.nan for v_t, a in zip(v_thresh_list, ap_ahp)]

        df_sweeps_all = pd.DataFrame({
            "Sweep": abf.sweepList, "I_inj": courants, "Nb_Spikes": n_spikes,
            "Current_Unit": unit_i,
            "V_steady": v_stat, "V_threshold": v_thresh_list, "AP_Amp": ap_amps, 
            "AP_Width_ms": ap_widths, "AP_Rise_ms": ap_rise, "AP_Decay_ms": ap_decay, "AP_AHP": ap_ahp_relative
        })
        
        for name, value in metadata.items(): df_sweeps_all[name] = value
        df_sweeps_all['File'] = uploaded_file.name
        df_sweeps_all['Duration_s'] = (idx_end-idx_start)/sr
        df_sweeps_all['Frequency_Hz'] = df_sweeps_all.Nb_Spikes / df_sweeps_all.Duration_s
        df_sweeps_all['Excluded_Depolarization_Block'] = is_excluded_list
        export_parameters(dict(metadata=metadata, file_sha256=identity, spike_threshold=spike_threshold,
                               dvdt_threshold=dvdt_threshold, window_s=[.1,.6], excluded_sweeps=excluded_sweeps), key='spikes')
        st.download_button('Exporter tous les sweeps avec les exclusions', df_sweeps_all.to_csv(index=False), f'{uploaded_file.name}_All_Sweeps.csv')
        # Filtrer le tableau des sweeps pour exclure les traces concernées de l'exportation
        df_sweeps_filtered = df_sweeps_all[~df_sweeps_all['Sweep'].isin(excluded_sweeps)].reset_index(drop=True)
        col_exp2.download_button(T["exp_sweeps"][lang], df_sweeps_filtered.to_csv(index=False).encode('utf-8'), f"{uploaded_file.name}_Sweeps.csv", use_container_width=True)

        # --- README, FORMALISME & CITATION ---
        st.divider()
        st.markdown("<div id='readme-formalise-citation'></div>", unsafe_allow_html=True)
        with st.expander(T["readme_title"][lang]):
            if lang == "Français":
                st.markdown("""
                ### 📄 README (Mode d'emploi)
                Cet outil est conçu pour le traitement par lots et l'extraction biophysique de traces *Current-Clamp* (.abf).
                1. Chargez votre fichier via le panneau latéral.
                2. Réglez le **Seuil dV/dt (15 mV/ms par défaut)**. C'est l'étalon-or pour détecter l'ouverture massive des canaux sodiques.
                3. Inspectez visuellement la qualité du *seal* et les potentiels instabilités de Vrest.
                4. Les blocs de dépolarisation (*Depolarization Blocks*) sont écartés pour éviter de fausser les moyennes de population.
                5. Exportez le profil biophysique global et les données métriques par échelons pour vos analyses statistiques.

                ### 🧠 Formalisme & Limites
                * **Decay Time (NaN) :** Si la métrique `Decay` indique `NaN`, c'est que le neurone n'a pas repolarisé sous les 10% de son amplitude dans une fenêtre de 100 ms (bloc de dépolarisation, inactivation $K^+$). C'est un paramètre biologique pertinent.

                ### 🎓 Citation
                Si vous utilisez ce code ou cette pipeline pour une publication scientifique, merci d'inclure la citation et le DOI suivants :
                > **Chavis-Manzoni Lab (2026).** *Expert Pipeline: Neural Excitability & Morphometry.*
                > **DOI :** [10.5281/zenodo.19912621](https://doi.org/10.5281/zenodo.19912621)
                > **Github :** [github.com/ManzoniLab/ElectrophyPipeline](https://github.com)
                """)
            else:
                st.markdown("""
                ### 📄 README (Instructions)
                This tool is designed for batch processing and biophysical extraction of *Current-Clamp* traces (.abf).
                1. Upload your file via the sidebar.
                2. Adjust the **dV/dt Threshold (default 15 mV/ms)**. This is the gold standard for detecting massive sodium channel opening.
                3. Visually inspect the seal quality and any potential Vrest instabilities.
                4. Depolarization Blocks are systematically filtered out to protect population averages from distortion.
                5. Export the global biophysical profile and sweep-by-sweep metric data for statistical analysis.

                ### 🧠 Formalism & Limitations
                * **Decay Time (NaN) :** If the `Decay` metric shows `NaN`, it means the neuron did not repolarize below 10% of its amplitude within a 100 ms window (depolarization block, $K^+$ inactivation). This is a biologically relevant parameter.

                ### 🎓 Citation
                If you use this code or pipeline for a scientific publication, please include the following citation and DOI:
                > **Chavis-Manzoni Lab (2026).** *Expert Pipeline: Neural Excitability & Morphometry.*
                > **DOI:** [10.5281/zenodo.19912621](https://doi.org/10.5281/zenodo.19912621)
                > **Github:** [github.com/ManzoniLab/ElectrophyPipeline](https://github.com)
                """)

    except Exception as exc:
        st.error(f"Analyse interrompue : {exc}")
