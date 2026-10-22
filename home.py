import streamlit as st
from ephys_tutorials import render_beginner_guide

lang = st.session_state.get("global_language", "Français")
english = lang == "English"

if english:
    st.title("🧠 Chavis-Manzoni Lab — Electrophysiology Analysis Suite")
    st.markdown(
        "Analyze action potentials and intrinsic excitability, spontaneous synaptic events, "
        "synaptic plasticity, and population data from **Axon Binary Format (.abf)** files."
    )
    st.subheader("Choose an analysis")
    st.markdown(
        "- **Synaptic plasticity (LTP/LTD):** fEPSP measurements, time normalization, and sweep-level exports.\n"
        "- **Action potentials and excitability:** intrinsic properties, f-I and I-V curves.\n"
        "- **Spontaneous AMPA / GABA events:** event detection and export.\n"
        "- **Batch analysis:** process multiple ABF files, summarize by cell, and review the processing log.\n"
        "- **Population curves:** averages by cell or animal, uncertainty bands, and exportable figures.\n"
        "- **Statistics:** independent or paired groups, mixed models, effect sizes, and multiple-comparison corrections."
    )
    st.info("For population analyses, provide Condition, Animal_ID, and Cell_ID. Figures can be exported as PDF, SVG, or PNG; analysis settings are included with results.")
    with st.expander("Run the app locally"):
        st.code("python -m pip install -r requirements.txt\nstreamlit run streamlit_app.py", language="bash")
else:
    st.title("🧠 Chavis-Manzoni Lab — Suite d’analyse électrophysiologique")
    st.markdown(
        "Analysez les potentiels d’action et l’excitabilité intrinsèque, les événements synaptiques spontanés, "
        "la plasticité synaptique et les données de population à partir de fichiers **Axon Binary Format (.abf)**."
    )
    st.subheader("Choisir une analyse")
    st.markdown(
        "- **Plasticité synaptique (LTP/LTD)** : mesures fEPSP, normalisation temporelle et export par sweep.\n"
        "- **Potentiels d’action et excitabilité** : propriétés intrinsèques, courbes f-I et I-V.\n"
        "- **Événements spontanés AMPA / GABA** : détection et export des événements.\n"
        "- **Traitement par lots** : analyse de plusieurs fichiers ABF, résumé par cellule et journal de traitement.\n"
        "- **Courbes de population** : moyennes par cellule ou animal, intervalles d’incertitude et figures exportables.\n"
        "- **Statistiques** : groupes indépendants ou appariés, modèles mixtes, tailles d’effet et corrections multiples."
    )
    st.info("Pour les analyses de population, renseignez Condition, Animal_ID et Cell_ID. Les figures s’exportent en PDF, SVG ou PNG ; les paramètres sont joints aux résultats.")
    with st.expander("Démarrage local"):
        st.code("python -m pip install -r requirements.txt\nstreamlit run streamlit_app.py", language="bash")

render_beginner_guide("overview", lang)
