# Analyse de plasticité synaptique | Synaptic Plasticity Analysis

**Chavis Lab & Manzoni Lab** · Application Streamlit pour analyser les enregistrements de plasticité synaptique à long terme (LTP/LTD).

**Chavis Lab & Manzoni Lab** · A Streamlit application for long-term synaptic plasticity (LTP/LTD) recordings.

Application en ligne / Live app: [chavislab-plasticity.streamlit.app](https://chavislab-plasticity.streamlit.app/)

## Français

### Fonctionnalités

L’application lit deux fichiers Axon Binary Format (.abf) : un enregistrement baseline et un enregistrement post-induction. Elle permet de régler les sweeps à analyser, la durée d’induction, la fenêtre de normalisation et la taille des bins. Les tracés peuvent être inspectés avant l’extraction.

Pour chaque sweep, l’outil calcule l’amplitude du fEPSP et sa charge (aire sous la courbe), avec soustraction de la trace de référence CNQX lorsque celle-ci est fournie. Les mesures peuvent être exportées en CSV, puis visualisées après normalisation et regroupement temporel.

### Utilisation

1. Ouvrir l’application Streamlit et charger les fichiers baseline et post-induction.
2. Vérifier la sélection des sweeps, la référence CNQX et les fenêtres de mesure.
3. Régler l’origine temporelle de l’induction, la période de normalisation et la taille des bins.
4. Inspecter les tracés, lancer l’extraction et télécharger le CSV.

Pour un usage local, installer les dépendances listées dans requirements.txt, puis lancer l’application :

    python -m pip install -r requirements.txt
    streamlit run app_biophysique.py

### Interprétation

Les mesures sont calculées par sweep. Les barres d’erreur affichées décrivent la dispersion des sweeps dans cet enregistrement ; elles ne remplacent pas une analyse statistique entre animaux ou cellules indépendants. Vérifier les tracés, la stabilité de la ligne de base et la cohérence des unités avant d’interpréter les résultats.

### Citation

Si vous utilisez ce logiciel dans vos travaux, veuillez citer le dépôt et son enregistrement Zenodo : [DOI 10.5281/zenodo.19910815](https://doi.org/10.5281/zenodo.19910815).

## English

### Features

The application reads two Axon Binary Format (.abf) files: a baseline recording and a post-induction recording. Users can select sweeps, set the induction duration, choose a normalization window, and set the time-bin size. Traces can be inspected before extraction.

For each sweep, the tool measures fEPSP amplitude and charge (area under the curve), with subtraction of the CNQX reference trace when provided. Results can be exported to CSV and visualized after normalization and time binning.

### Workflow

1. Open the Streamlit app and upload the baseline and post-induction files.
2. Check sweep selection, the CNQX reference, and measurement windows.
3. Set induction timing, the normalization period, and the bin size.
4. Inspect the traces, run the extraction, and download the CSV.

To run locally, install the dependencies listed in requirements.txt and start the application:

    python -m pip install -r requirements.txt
    streamlit run app_biophysique.py

### Interpretation

Measurements are calculated per sweep. Error bars describe sweep-to-sweep variation within that recording; they do not replace statistical analysis across independent animals or cells. Inspect the traces and check baseline stability and units before interpreting results.

### Citation

If you use this software in your research, please cite the repository and its Zenodo record: [DOI 10.5281/zenodo.19910815](https://doi.org/10.5281/zenodo.19910815).
