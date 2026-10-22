"""Batch analysis using the same numerical functions as individual pages."""
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st
from ephys_analysis import read_abf, analyze_spikes, analyze_epsc, analyze_ipsc
from ephys_io import digest, bundle
from ephys_ui import session_compute
from ephys_tutorials import render_beginner_guide

lang = st.session_state.get("global_language", "Français")
en = lang == "English"
def tr(fr, english):
    return english if en else fr

render_beginner_guide("batch", lang)
st.title(tr("📦 Analyse de plusieurs enregistrements", "📦 Batch analysis"))
analysis_labels = {
    tr("Potentiels d’action", "Action potentials"): "spikes",
    "sEPSC AMPA": "ampa",
    "sIPSC GABA": "gaba",
}
analysis_label = st.selectbox(tr("Type d’analyse", "Analysis type"), list(analysis_labels))
analysis = analysis_labels[analysis_label]
files = st.file_uploader(tr("Fichiers ABF", "ABF files"), type=["abf"], accept_multiple_files=True)
if not files:
    st.info(tr("Chargez un ou plusieurs fichiers ABF.", "Upload one or more ABF files."))
    st.stop()
if len({f.name for f in files}) != len(files):
    st.error(tr("Les noms des fichiers doivent être distincts.", "File names must be unique."))
    st.stop()

metadata = st.data_editor(
    pd.DataFrame([dict(File=f.name, Condition=tr("Groupe 1", "Group 1"), Animal_ID="", Cell_ID=f.name.removesuffix(".abf")) for f in files]),
    disabled=["File"], hide_index=True, key="batch_metadata",
)
params = {}
if analysis == "spikes":
    params["spike_threshold"] = st.number_input(tr("Seuil de détection (mV)", "Detection threshold (mV)"), value=0.)
    params["dvdt_threshold"] = st.number_input(tr("Seuil dV/dt (mV/ms)", "dV/dt threshold (mV/ms)"), value=15.)
    st.caption(tr("Fenêtre d’injection : 100–600 ms, identique à la page individuelle.", "Injection window: 100–600 ms, matching the individual analysis page."))
else:
    outward = False
    if analysis == "gaba":
        polarities = [tr("Entrant", "Inward"), tr("Sortant", "Outward")]
        outward = st.radio(tr("Polarité du courant", "Current polarity"), polarities, horizontal=True) == polarities[1]
    params["dynamic"] = st.checkbox(tr("Retirer la ligne de base par médiane glissante (0,5 s)", "Remove baseline with a rolling median (0.5 s)"), True)
    params["use_bessel"] = st.checkbox(tr("Filtre Bessel", "Bessel filter"), True)
    params["cutoff"] = st.number_input(tr("Fréquence de coupure (Hz)", "Cutoff frequency (Hz)"), min_value=1, value=2000)
    params["threshold"] = st.number_input(tr("Seuil Z-score", "Z-score threshold"), min_value=.1, value=3. if analysis == "ampa" else 2.5)
    params["use_amp_filter"] = st.checkbox(tr("Filtrer l’amplitude", "Filter by amplitude"), True)
    params["amp_limit"] = st.number_input(tr("Amplitude minimale (pA)", "Minimum amplitude (pA)"), min_value=0., value=10. if analysis == "ampa" else (5. if outward else 7.))
    params["use_rise_filter"] = st.checkbox(tr("Filtrer le temps de montée", "Filter rise time"), True)
    params["rise_limit"] = st.number_input(tr("Temps de montée maximal (ms)", "Maximum rise time (ms)"), min_value=.01, value=4. if analysis == "ampa" else (5. if outward else 1.5))
    if analysis == "gaba":
        params["is_outward"] = outward
        params["use_decay_filter"] = st.checkbox(tr("Filtrer la durée équivalente charge/amplitude", "Filter charge/amplitude equivalent duration"), True)
        params["decay_limit"] = st.number_input(tr("Durée équivalente maximale (ms)", "Maximum equivalent duration (ms)"), min_value=.01, value=50. if outward else 4.)
    st.caption(tr(
        "Comme les pages individuelles, l’analyse spontanée utilise le premier sweep et le premier canal. Les résultats comprennent un résumé par cellule et les événements retenus.",
        "As on the individual pages, spontaneous-event analysis uses the first sweep and first channel. Results include a per-cell summary and retained events.",
    ))

identities = [dict(name=f.name, sha256=digest(f.getvalue())) for f in files]
settings = dict(analysis=analysis, parameters=params, metadata=metadata.to_dict("records"), sources=identities)
signature = str(settings)
if st.button(tr("Analyser le lot", "Analyze batch"), type="primary"):
    summaries, details, log = [], {}, []
    progress = st.progress(0.)
    for i, f in enumerate(files):
        meta = metadata.iloc[i].to_dict()
        try:
            abf = read_abf(f.getvalue())
            if analysis == "spikes":
                if abf.sweepUnitsY != "mV":
                    raise ValueError(tr("Cette analyse attend une tension en mV.", "This analysis expects voltage in mV."))
                r = analyze_spikes(abf, **params)
                summaries.append(dict(meta, Vrest_mV=r["v_rest_final"], Rin_MOhms=r["rin"], Tau_ms=r["tau"],
                                      Rheobase_I_pA=r["rheo_i"]*(1000 if r["unit_i"] == "nA" else 1), Rheobase_mV=r["rheo_v"]))
                d = pd.DataFrame({
                    "Sweep": abf.sweepList, "I_inj": r["courants"], "Nb_Spikes": r["n_spikes"], "V_steady": r["v_stat"],
                    "V_threshold": r["v_thresh_list"], "AP_Amp": r["ap_amps"], "AP_Width_ms": r["ap_widths"],
                    "AP_Rise_ms": r["ap_rise"], "AP_Decay_ms": r["ap_decay"],
                    "AP_AHP": np.array(r["v_thresh_list"])-np.array(r["ap_ahp"]),
                    "Excluded_Depolarization_Block": r["is_excluded_list"], "Current_Unit": r["unit_i"],
                    "Duration_s": .5, "Frequency_Hz": np.array(r["n_spikes"])/.5,
                }).assign(**meta)
                details[f"file_{i+1}_All_Sweeps"] = d
                details[f"file_{i+1}_Sweeps"] = d.loc[~d.Excluded_Depolarization_Block]
            else:
                if abf.sweepUnitsY != "pA":
                    raise ValueError(tr("Cette analyse attend un courant en pA.", "This analysis expects current in pA."))
                applied = dict(params, cutoff=min(params["cutoff"], max(1, int(.95*abf.dataRate/2))))
                if analysis == "ampa":
                    r = analyze_epsc(abf, **applied)
                    if not r["has_waveforms"]:
                        raise ValueError(tr("Trop peu d’événements pour construire le gabarit AMPA ; aucune fréquence n’est estimée.", "Too few events to build an AMPA template; event frequency was not estimated."))
                    events, amp, charge = r["valid_ev_iter"], "amp_scaled", "charge_scaled"
                else:
                    r = analyze_ipsc(abf, **applied)
                    events, amp, charge = r["valid_ev"], "amp", "area"
                d = pd.DataFrame(events)
                duration = len(r["times"])/r["fs"]
                summaries.append(dict(meta, N_Events=len(d), Frequency_Hz=len(d)/duration,
                                      Mean_Amplitude_pA=d[amp].mean() if len(d) else np.nan,
                                      Mean_Charge_fC=d[charge].mean() if len(d) else np.nan,
                                      Mean_Rise_ms=d["rise"].mean() if len(d) else np.nan,
                                      Applied_Cutoff_Hz=applied["cutoff"], Duration_s=duration))
                details[f"file_{i+1}_Events"] = d.assign(**meta)
            log.append(dict(File=f.name, status="ok", message=""))
        except Exception as exc:
            log.append(dict(File=f.name, status="failed", message=str(exc)))
        progress.progress((i+1)/len(files))

    st.session_state["batch_results"] = (signature, pd.DataFrame(summaries), details, pd.DataFrame(log))

saved = st.session_state.get("batch_results")
if not saved or saved[0] != signature:
    st.info(tr("Lancez l’analyse du lot pour ces paramètres.", "Run the batch analysis with these settings."))
    st.stop()
_, summary, details, log = saved
st.subheader(tr("Journal de traitement", "Processing log"))
st.dataframe(log, use_container_width=True)
if summary.empty:
    st.error(tr("Aucun enregistrement analysé avec succès.", "No recordings were analyzed successfully."))
    st.stop()
st.subheader(tr("Résumé des enregistrements", "Recording summary"))
st.dataframe(summary, use_container_width=True)
figures = {}
metric = "Rin_MOhms" if analysis == "spikes" else "Frequency_Hz"
fig, ax = plt.subplots(figsize=(max(6, min(14, len(summary)*.5)), 4))
ax.plot(np.arange(len(summary)), summary[metric], "o", color="#176b87")
ax.set(
    xticks=np.arange(len(summary)),
    xticklabels=summary.Cell_ID,
    ylabel=metric,
    title=tr("Résumé du lot — valeurs individuelles", "Batch summary — individual values"),
)
ax.tick_params(axis="x", rotation=60)
fig.tight_layout()
st.pyplot(fig)
figures["batch_summary"] = fig
archive = session_compute("batch_archive", signature, lambda: bundle(dict(details, summary=summary, processing_log=log), figures, settings))
st.download_button(
    tr("Télécharger le lot : résultats, figure et paramètres", "Download batch: results, figure, and settings"),
    archive, "ephys_batch.zip", mime="application/zip",
)
plt.close(fig)
