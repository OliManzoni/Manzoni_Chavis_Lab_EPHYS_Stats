# Suite d’analyse électrophysiologique | Electrophysiology Analysis Suite

**Chavis-Manzoni Lab** — Application Streamlit pour l’analyse des enregistrements électrophysiologiques, l’enseignement et la préparation des résultats.

This Streamlit application brings together electrophysiology analyses for laboratory use, teaching, and reproducible result export.

**DOI Zenodo / Zenodo DOI**: [10.5281/zenodo.19910815](https://doi.org/10.5281/zenodo.19910815) — DOI concept, qui renvoie vers la dernière version publiée / concept DOI, which resolves to the latest published version.

## Français

### Modules

- **Plasticité LTP/LTD** : mesures baseline/post-induction, amplitude et charge, normalisation, bins temporels, mesures brutes par sweep et figures.
- **Potentiels d’action et excitabilité** : propriétés intrinsèques, mesures par sweep et courbes f-I / I-V.
- **Événements spontanés AMPA et GABA** : détection, amplitude, cinétique, charge, événements retenus et résumé par cellule.
- **Analyse par lots** : traitement de plusieurs fichiers ABF pour les potentiels d’action, AMPA ou GABA, avec journal des erreurs et export groupé.
- **Courbes de population** : moyenne par cellule puis, au besoin, par animal ; courbes individuelles et bandes SEM ou IC à 95 %.
- **Statistiques** : Welch, Mann–Whitney, t apparié, Wilcoxon et modèles linéaires mixtes, tailles d’effet, intervalles, correction des comparaisons multiples et diagnostics.

### Installation et démarrage

Depuis le dossier `EPHYS SUITE`, dans un environnement Python dédié :

```bash
python -m pip install -r requirements.txt
streamlit run streamlit_app.py
```

Pour exécuter les contrôles automatisés :

```bash
python -m pip install -r requirements-dev.txt
python -m pytest tests -q
```

### Données et identifiants

Les pages d’analyse lisent les fichiers Axon `.abf`. Renseigner **Condition**, **Animal_ID** et **Cell_ID** pour garder les identifiants biologiques dans les exports et relier correctement les mesures répétées.

L’analyse spontanée traite le premier sweep du premier canal et attend un courant en pA. L’analyse d’excitabilité attend une tension en mV, un courant de commande en pA ou nA, et une fenêtre d’injection de 100 à 600 ms. Les courbes de population acceptent les fichiers `_Sweeps.csv` issus de cette analyse ; l’unité du courant est convertie en pA avant regroupement.

La page statistique accepte une table longue ou plusieurs fichiers de groupes. Elle distingue l’unité expérimentale indépendante des mesures répétées, aligne les paires sur leur identifiant et signale les lignes manquantes. Le modèle mixte est gaussien : condition catégorielle et, en option, facteur numérique linéaire, interaction, pente aléatoire et niveau imbriqué. Les corrections Holm ou Benjamini–Hochberg sont appliquées à la famille des contrastes sélectionnés. Les intervalles affichés pour les contrastes sont ponctuels.

### Résultats et limites

Les graphiques peuvent être téléchargés en PDF, SVG ou PNG. Les pages de statistiques, courbes et lots proposent également des archives ZIP avec tableaux et paramètres d’analyse. Les images sont exportées à 300 dpi.

Les sweeps d’un enregistrement décrivent la variabilité de cet enregistrement ; ils ne remplacent pas les unités biologiques indépendantes. Les mesures automatisées restent inspectables dans les pages de tracés. Les détecteurs spontanés utilisent actuellement le premier sweep et le premier canal. Le traitement par lots couvre potentiels d’action, AMPA et GABA ; la plasticité est analysée par paire d’enregistrements.

Les résultats de régression et les tests locaux sont décrits dans [POINT_PROJET.md](POINT_PROJET.md). Le projet LMT et les anciennes copies de scripts ne font pas partie de la navigation de cette suite.

### Citation

Citez la version utilisée avec le DOI concept Zenodo : [10.5281/zenodo.19910815](https://doi.org/10.5281/zenodo.19910815).

## English

### Modules

- **LTP/LTD plasticity**: baseline and post-induction measurements, amplitude and charge, normalization, time bins, sweep-level raw measurements, and figures.
- **Action potentials and intrinsic excitability**: intrinsic properties, sweep-level measurements, and f-I / I-V curves.
- **Spontaneous AMPA and GABA events**: event detection, amplitude, kinetics, charge, retained-event tables, and per-cell summaries.
- **Batch analysis**: process multiple ABF recordings for action potentials, AMPA, or GABA, with a per-file log and bundled exports.
- **Population curves**: average by cell and optionally by animal; show individual curves and SEM or 95% Student-t confidence bands.
- **Statistics**: Welch, Mann–Whitney, paired t-test, Wilcoxon, and linear mixed models, with effect sizes, intervals, multiple-comparison correction, and diagnostics.

### Install and run

From the `EPHYS SUITE` directory, using a dedicated Python environment:

```bash
python -m pip install -r requirements.txt
streamlit run streamlit_app.py
```

Run the automated checks with:

```bash
python -m pip install -r requirements-dev.txt
python -m pytest tests -q
```

### Data and identifiers

The analysis pages read Axon `.abf` files. Enter **Condition**, **Animal_ID**, and **Cell_ID** so biological identifiers remain in the exports and repeated measurements can be matched correctly.

Spontaneous-event analysis currently uses the first sweep and first channel and expects current in pA. Intrinsic-excitability analysis expects voltage in mV, command current in pA or nA, and a 100–600 ms injection window. Population curves accept `_Sweeps.csv` files exported by this analysis; current is converted to pA before grouping.

The statistics page accepts a long-format table or multiple group files. It distinguishes the independent experimental unit from repeated observations, matches paired observations by identifier, and reports missing rows. The mixed model is Gaussian, with a categorical condition and optional linear numeric factor, interaction, random slope, and nested level. Holm or Benjamini–Hochberg correction is applied across the selected contrast family. Contrast intervals are pointwise.

### Results and scope

Figures can be downloaded as PDF, SVG, or PNG. Statistics, population-curve, and batch pages also provide ZIP archives containing tables and analysis settings. Figures are exported at 300 dpi.

Sweeps from one recording describe within-recording variability; they do not replace independent biological units. Automated measurements remain inspectable in the trace views. Spontaneous-event detectors currently use the first sweep and channel. Batch processing covers action potentials, AMPA, and GABA; plasticity is analyzed from a baseline/post recording pair.

Regression checks and local tests are documented in [POINT_PROJET.md](POINT_PROJET.md). The LMT project and archived script copies are outside this suite's navigation.

### Citation

Cite the version you used with the Zenodo concept DOI: [10.5281/zenodo.19910815](https://doi.org/10.5281/zenodo.19910815).
