import streamlit as st

st.title("🧠 Chavis-Manzoni Lab — Suite d’analyse électrophysiologique")
st.markdown(
    "Une application pour analyser les potentiels d’action et l’excitabilité, les événements synaptiques "
    "spontanés, la plasticité et les données de population à partir des fichiers **Axon Binary Format (.abf)**."
)

with st.container(border=True):
    st.subheader("🌍 Langues / Languages")
    french, english = st.columns(2)
    with french:
        st.markdown("**Français**")
        st.write("Interface en français. Pour les pages bilingues, choisissez la langue dans le menu latéral de l’analyse.")
    with english:
        st.markdown("**English**")
        st.write("An English interface is available for LTP/LTD, action potentials and excitability, spontaneous AMPA, and spontaneous GABA analyses. Select **English** in the analysis page sidebar.")
    st.caption(
        "Les pages Traitement par lots, Courbes de population et Comparaisons statistiques sont actuellement en français. "
        "The batch, population curves, and statistical comparison pages are currently in French."
    )

st.subheader("Choisir une analyse")
st.markdown(
    "- **Plasticité synaptique** : mesures fEPSP, normalisation temporelle et export des sweeps.\n"
    "- **Potentiels d'action et excitabilité** : propriétés intrinsèques, courbes f-I et I-V.\n"
    "- **Événements spontanés AMPA / GABA** : détection et export des événements.\n"
    "- **Analyse par lots** : plusieurs fichiers ABF, résumé par cellule et journal de traitement.\n"
    "- **Courbes de population** : moyennes par cellule ou animal, intervalles et figures exportables.\n"
    "- **Comparaisons statistiques** : groupes indépendants, appariement ou modèle mixte, tailles d’effet et corrections multiples."
)

st.info(
    "Renseignez Condition, Animal_ID et Cell_ID pour relier vos mesures aux analyses de population. "
    "Les graphiques s’exportent en PDF, SVG ou PNG ; les paramètres accompagnent les résultats."
)

with st.expander("Démarrage local"):
    st.code("python -m pip install -r requirements.txt\nstreamlit run streamlit_app.py", language="bash")
