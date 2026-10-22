"""Entry point for the Chavis-Manzoni Lab electrophysiology analysis suite."""

import streamlit as st

st.set_page_config(page_title="Chavis-Manzoni Lab — Electrophysiology Suite", page_icon="🧠", layout="wide")

language = st.sidebar.selectbox("🌍 Language / Langue", ["Français", "English"], key="global_language")
english = language == "English"

home_title = "Home" if english else "Accueil"
section_title = "Electrophysiology analyses" if english else "Analyses électrophysiologiques"
page_titles = {
    "ltp": "Synaptic plasticity (LTP/LTD)" if english else "Plasticité synaptique (LTP/LTD)",
    "spikes": "Action potentials & excitability" if english else "Potentiels d'action et excitabilité",
    "ampa": "Spontaneous AMPA events" if english else "Événements spontanés AMPA",
    "gaba": "Spontaneous GABA events" if english else "Événements spontanés GABA",
    "batch": "Batch analysis" if english else "Traitement par lots",
    "curves": "Population curves" if english else "Courbes de population",
    "stats": "Statistics & mixed models" if english else "Statistiques et modèles mixtes",
}

pages = {
    home_title: [st.Page("home.py", title=home_title, icon="🏠", default=True)],
    section_title: [
        st.Page("1_📊_LTP_LTD.py", title=page_titles["ltp"], icon="📊"),
        st.Page("2_⚡_Spike_Analysis.py", title=page_titles["spikes"], icon="⚡"),
        st.Page("3_🟢_sEPSC_AMPA.py", title=page_titles["ampa"], icon="🟢"),
        st.Page("4_🟣_sIPSC_GABA.py", title=page_titles["gaba"], icon="🟣"),
        st.Page("5_📦_Batch_Analysis.py", title=page_titles["batch"], icon="📦"),
        st.Page("6_📈_Averaged_Curves.py", title=page_titles["curves"], icon="📈"),
        st.Page("7_⚖️_Statistical_Comparison.py", title=page_titles["stats"], icon="⚖️"),
    ],
}

navigation = st.navigation(pages)
navigation.run()
