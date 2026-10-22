"""Entry point for the Chavis-Manzoni Lab electrophysiology analysis suite."""

import streamlit as st

st.set_page_config(page_title="Chavis-Manzoni Lab — Électrophysiologie", page_icon="🧠", layout="wide")

pages = {
    "Accueil": [
        st.Page("home.py", title="Accueil", icon="🏠", default=True),
    ],
    "Analyses électrophysiologiques": [
        st.Page("1_📊_LTP_LTD.py", title="Plasticité synaptique", icon="📊"),
        st.Page("2_⚡_Spike_Analysis.py", title="Potentiels d'action et excitabilité", icon="⚡"),
        st.Page("3_🟢_sEPSC_AMPA.py", title="Événements spontanés AMPA", icon="🟢"),
        st.Page("4_🟣_sIPSC_GABA.py", title="Événements spontanés GABA", icon="🟣"),
        st.Page("5_📦_Batch_Analysis.py", title="Traitement par lots", icon="📦"),
        st.Page("6_📈_Averaged_Curves.py", title="Courbes de population", icon="📈"),
        st.Page("7_⚖️_Statistical_Comparison.py", title="Comparaisons et modèles mixtes", icon="⚖️"),
    ],
}

navigation = st.navigation(pages)
navigation.run()
