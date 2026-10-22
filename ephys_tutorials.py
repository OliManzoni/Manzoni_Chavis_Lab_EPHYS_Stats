"""Bilingual beginner guides shown at the top of each suite page."""

import streamlit as st

GUIDES = {
    "overview": {
        "Français": (
            "Bien démarrer",
            "Cette suite regroupe plusieurs outils indépendants. Choisissez une page dans le menu de gauche, puis lisez son guide avant de charger les données.",
            [
                "Choisissez **Français** ou **English** dans le sélecteur de langue, en haut du menu latéral.",
                "Ouvrez l’analyse correspondant à votre protocole : plasticité, excitabilité, événements spontanés, lots, courbes ou statistiques.",
                "Respectez les formats d’entrée indiqués par chaque outil. Les fichiers ABF sont utilisés pour les analyses de traces ; les outils de population et de statistiques lisent les tableaux CSV exportés.",
                "Renseignez les identifiants biologiques (**Condition**, **Animal_ID**, **Cell_ID**) lorsque l’outil le demande, puis vérifiez les tracés et les tableaux avant d’interpréter les résultats.",
                "Téléchargez les tableaux et figures depuis le bouton d’export de la page. Le README bilingue décrit les entrées, les sorties et les limites de la suite.",
            ],
        ),
        "English": (
            "Getting started",
            "The suite contains several independent tools. Choose a page from the left menu and read its guide before uploading data.",
            [
                "Choose **English** or **Français** from the language selector at the top of the sidebar.",
                "Open the analysis that matches your protocol: plasticity, excitability, spontaneous events, batch processing, curves, or statistics.",
                "Use the input format requested by each tool. ABF files are used for trace analyses; population and statistics tools read exported CSV tables.",
                "Enter biological identifiers (**Condition**, **Animal_ID**, **Cell_ID**) when requested, and inspect traces and tables before interpreting results.",
                "Download tables and figures from the page export button. The bilingual README describes inputs, outputs, and suite limitations.",
            ],
        ),
    },
    "ltp": {
        "Français": (
            "Guide débutant — Plasticité LTP/LTD",
            "Comparez un enregistrement de référence (baseline) à un enregistrement après induction.",
            [
                "Chargez les deux fichiers ABF correspondants. Les acquisitions doivent avoir la même fréquence d’échantillonnage et la même longueur de sweep pour la soustraction CNQX.",
                "Vérifiez l’identifiant de l’animal, l’intervalle des sweeps, la durée d’induction et la fenêtre de référence utilisée pour définir 100 %.",
                "Sélectionnez les sweeps baseline, post-induction et CNQX. Réglez ensuite le zoom et les fenêtres de mesure du niveau de base et du pic fEPSP.",
                "Dans l’onglet d’inspection, vérifiez visuellement les traces et les fenêtres. Revenez aux réglages si le pic ou la ligne de base sont mal définis.",
                "Lancez l’extraction, examinez les mesures brutes et normalisées, puis exportez le tableau CSV et les figures.",
            ],
        ),
        "English": (
            "Beginner guide — LTP/LTD plasticity",
            "Compare a baseline recording with a recording acquired after induction.",
            [
                "Upload the matching ABF files. Sampling rate and sweep length must match for CNQX subtraction.",
                "Check the animal identifier, sweep interval, induction duration, and reference window used to define 100%.",
                "Select baseline, post-induction, and CNQX sweeps. Then set the zoom and the measurement windows for baseline and the fEPSP peak.",
                "Inspect the traces and windows in the inspection tab. Adjust the settings if the peak or baseline is misplaced.",
                "Run extraction, review raw and normalized measurements, then export the CSV table and figures.",
            ],
        ),
    },
    "spikes": {
        "Français": (
            "Guide débutant — Potentiels d’action et excitabilité",
            "Analysez un enregistrement en current-clamp pour décrire l’excitabilité intrinsèque et la forme des potentiels d’action.",
            [
                "Chargez un fichier ABF en tension (mV) avec des sweeps de courant injecté. Vérifiez les unités et le protocole d’injection.",
                "Réglez le seuil de potentiel d’action et le seuil dV/dt. Ces réglages influencent la détection : inspectez toujours les sweeps.",
                "Examinez les mesures de repos, résistance d’entrée, constante de temps, rhéobase et morphologie des potentiels d’action.",
                "Vérifiez les sweeps exclus pour bloc de dépolarisation et les courbes f-I / I-V avant de retenir les résultats.",
                "Exportez le profil global et les résultats par sweep. Les fichiers par sweep peuvent ensuite alimenter l’outil de courbes de population.",
            ],
        ),
        "English": (
            "Beginner guide — Action potentials and excitability",
            "Analyze a current-clamp recording to describe intrinsic excitability and action-potential shape.",
            [
                "Upload an ABF file containing voltage (mV) and injected-current sweeps. Check the units and injection protocol.",
                "Set the action-potential voltage threshold and dV/dt threshold. These settings affect detection, so inspect the sweeps.",
                "Review resting properties, input resistance, time constant, rheobase, and action-potential morphology.",
                "Check sweeps excluded for depolarization block and inspect the f-I / I-V curves before using the results.",
                "Export the global profile and sweep-level results. Sweep exports can be used in the population-curves tool.",
            ],
        ),
    },
    "ampa": {
        "Français": (
            "Guide débutant — Événements spontanés AMPA",
            "Détectez et caractérisez les événements spontanés dans un enregistrement de courant.",
            [
                "Chargez un fichier ABF en courant (pA). L’outil analyse actuellement le premier sweep et le premier canal.",
                "Commencez par les réglages de ligne de base et de filtre, puis ajustez le seuil de détection et les filtres d’amplitude et de temps de montée.",
                "Inspectez les événements détectés et leurs formes d’onde. Un seuil trop bas peut retenir du bruit ; un seuil trop élevé peut manquer des événements.",
                "Vérifiez le nombre et la fréquence des événements ainsi que les mesures d’amplitude, de charge et de cinétique.",
                "Exportez les événements retenus, le résumé par cellule, les paramètres et les figures.",
            ],
        ),
        "English": (
            "Beginner guide — Spontaneous AMPA events",
            "Detect and characterize spontaneous events in a current recording.",
            [
                "Upload an ABF file recorded in current (pA). The tool currently analyzes the first sweep and first channel.",
                "Start with baseline and filter settings, then adjust the detection threshold and amplitude and rise-time filters.",
                "Inspect detected events and their waveforms. A threshold that is too low may retain noise; one that is too high may miss events.",
                "Review event count and frequency, as well as amplitude, charge, and kinetic measurements.",
                "Export retained events, the per-cell summary, analysis settings, and figures.",
            ],
        ),
    },
    "gaba": {
        "Français": (
            "Guide débutant — Événements spontanés GABA",
            "Détectez et caractérisez les événements spontanés GABA en tenant compte de leur polarité.",
            [
                "Chargez un fichier ABF en courant (pA). L’outil analyse actuellement le premier sweep et le premier canal.",
                "Choisissez la polarité observée dans vos conditions d’enregistrement (courants entrants ou sortants).",
                "Réglez la ligne de base, le filtre et le seuil, puis activez ou ajustez les filtres d’amplitude, de montée et de décroissance.",
                "Inspectez les événements retenus et les formes d’onde moyennes. Confirmez que la polarité et les filtres correspondent au signal attendu.",
                "Vérifiez les mesures par événement et le résumé, puis exportez les tableaux, paramètres et figures.",
            ],
        ),
        "English": (
            "Beginner guide — Spontaneous GABA events",
            "Detect and characterize spontaneous GABA events while accounting for signal polarity.",
            [
                "Upload an ABF file recorded in current (pA). The tool currently analyzes the first sweep and first channel.",
                "Choose the polarity observed under your recording conditions (inward or outward currents).",
                "Set baseline, filter, and threshold, then enable or adjust amplitude, rise-time, and decay filters.",
                "Inspect retained events and average waveforms. Confirm that polarity and filters match the expected signal.",
                "Review event-level measurements and the summary, then export tables, settings, and figures.",
            ],
        ),
    },
    "batch": {
        "Français": (
            "Guide débutant — Traitement par lots",
            "Appliquez le même type d’analyse à plusieurs fichiers ABF et obtenez un résumé regroupé.",
            [
                "Choisissez potentiels d’action, événements AMPA ou événements GABA. Un lot ne peut contenir qu’un seul type d’analyse.",
                "Chargez les fichiers ABF et renseignez Condition, Animal_ID et Cell_ID dans le tableau de métadonnées.",
                "Réglez les paramètres communs. Pour GABA, vérifiez aussi la polarité ; les paramètres sont appliqués à tous les fichiers du lot.",
                "Lancez l’analyse et consultez le journal fichier par fichier. Corrigez ou retirez les fichiers signalés en échec.",
                "Vérifiez le résumé et la figure, puis téléchargez l’archive contenant résultats, paramètres et journal de traitement.",
            ],
        ),
        "English": (
            "Beginner guide — Batch analysis",
            "Apply the same analysis to several ABF files and create a combined summary.",
            [
                "Choose action potentials, AMPA events, or GABA events. A batch can contain only one analysis type.",
                "Upload ABF files and enter Condition, Animal_ID, and Cell_ID in the metadata table.",
                "Set shared parameters. For GABA, also check polarity; the same settings are applied to every file in the batch.",
                "Run the analysis and review the per-file log. Fix or remove files marked as failed.",
                "Review the summary and figure, then download the archive containing results, settings, and processing log.",
            ],
        ),
    },
    "curves": {
        "Français": (
            "Guide débutant — Courbes de population",
            "Regroupez les résultats par sweep pour visualiser les courbes f-I et I-V de plusieurs cellules ou animaux.",
            [
                "Importez les fichiers CSV par sweep exportés par l’analyse des potentiels d’action.",
                "Complétez Condition, Animal_ID, Cell_ID et l’unité du courant dans le tableau. Les unités nA sont converties en pA.",
                "Choisissez l’unité de résumé : cellule ou animal. Le choix doit suivre le plan expérimental ; les cellules d’un même animal ne sont pas des animaux indépendants.",
                "Choisissez SEM ou IC à 95 % et décidez si les courbes individuelles doivent être affichées.",
                "Interprétez les bandes comme l’incertitude descriptive à chaque courant : elles ne constituent pas un test de différence entre conditions. Téléchargez l’archive pour conserver figures, tableaux et paramètres.",
            ],
        ),
        "English": (
            "Beginner guide — Population curves",
            "Group sweep-level results to visualize f-I and I-V curves across cells or animals.",
            [
                "Upload sweep-level CSV files exported by the action-potential analysis.",
                "Complete Condition, Animal_ID, Cell_ID, and current unit in the table. nA values are converted to pA.",
                "Choose the summary unit: cell or animal. Match this to the experimental design; cells from one animal are not independent animals.",
                "Choose SEM or 95% confidence intervals and decide whether to show individual curves.",
                "Interpret bands as descriptive uncertainty at each current; they are not a test of differences between conditions. Download the archive to retain figures, tables, and settings.",
            ],
        ),
    },
    "stats": {
        "Français": (
            "Guide débutant — Comparaisons statistiques",
            "Comparez des mesures en déclarant d’abord correctement les groupes, les unités expérimentales et le plan d’appariement.",
            [
                "Importez une table longue avec une colonne de condition, ou deux ensembles de fichiers représentant deux groupes.",
                "Choisissez la colonne de condition, puis l’identifiant de l’unité indépendante. Utilisez l’identifiant de l’animal si l’animal est l’unité expérimentale.",
                "Pour des mesures appariées, utilisez le même identifiant dans les deux conditions. Pour des cellules imbriquées dans les animaux, indiquez aussi la sous-unité.",
                "Choisissez une méthode adaptée au plan, sélectionnez les mesures et la correction des comparaisons multiples. Un modèle mixte est disponible pour les données regroupées ou répétées.",
                "Lisez les estimations, intervalles et p-valeurs corrigées ensemble ; examinez les diagnostics du modèle. Les sweeps ou cellules d’un même animal ne doivent pas être comptés comme des animaux indépendants.",
                "Téléchargez l’archive pour conserver les données utilisées, les résultats, les paramètres et les figures.",
            ],
        ),
        "English": (
            "Beginner guide — Statistical comparisons",
            "Compare measurements by first declaring groups, experimental units, and the pairing structure correctly.",
            [
                "Upload a long-format table with a condition column, or two sets of files representing two groups.",
                "Choose the condition column, then the independent-unit identifier. Use the animal identifier when the animal is the experimental unit.",
                "For paired measurements, use the same identifier in both conditions. For cells nested within animals, also specify the nested unit.",
                "Choose a method that matches the design, select outcomes, and choose a multiple-comparison correction. A mixed model is available for grouped or repeated data.",
                "Interpret estimates, intervals, and adjusted p-values together; inspect model diagnostics. Sweeps or cells from one animal must not be counted as independent animals.",
                "Download the archive to retain the analyzed data, results, settings, and figures.",
            ],
        ),
    },
}


def render_beginner_guide(tool: str, language: str) -> None:
    """Render a concise, localized workflow guide."""
    selected_language = language if language in ("Français", "English") else "Français"
    title, introduction, steps = GUIDES[tool][selected_language]
    with st.expander(f"📘 {title}", expanded=False):
        st.write(introduction)
        for index, step in enumerate(steps, start=1):
            st.markdown(f"{index}. {step}")
