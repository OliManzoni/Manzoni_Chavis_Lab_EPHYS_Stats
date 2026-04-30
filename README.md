[![DOI](https://zenodo.org/badge/1222314509.svg)](https://doi.org/10.5281/zenodo.19910815)

**Description:** v1.0.0 Fast analysis of synaptic plasticity LTP/LTD.


# 🧬 Synaptic Plasticity Analysis Suite
### Chavis Lab & Manzoni Lab | Preprocessing & Biophysics[cite: 1]

This platform is engineered to standardize the processing of electrophysiological data, transitioning from raw traces (.abf) to publication-ready statistical outputs[cite: 1]. It eliminates manual measurement bias by automating the extraction of biophysical parameters and temporal normalization[cite: 1].

---

## 🚀 Rapid Access
The application is available via open access on Streamlit Cloud:  
👉 [https://chavislab-plasticity.streamlit.app/](https://chavislab-plasticity.streamlit.app/)[cite: 1]

---

## 🔬 Rationale and Core Objectives
In synaptic plasticity research (LTP/LTD), the precision of "Time 0" and the stability of the baseline are paramount[cite: 1]. This suite enables:
*   **Mitigation of Inter-operator Variability:** The algorithm provides objective peak detection and integral (charge) calculations consistently across all recordings[cite: 1].
*   **T=0 Standardization:** Automatic alignment based on induction timing to accurately compare maintenance kinetics[cite: 1].
*   **Dynamic Scaling:** Normalization relative to a user-defined reference period[cite: 1].
*   **Real-time Visualization:** High-speed rendering of experimental results[cite: 1].

---

## 📖 User Manual (Workflow)

### 1. Data Loading
*   **Baseline File:** Import the control trace (pre-induction)[cite: 1].
*   **Post-Induction File:** Import the post-induction trace, including the maintenance phase and, if applicable, pharmacological washout[cite: 1].
*   **Technical Note:** The application leverages the `pyabf` library for native parsing of Axon Binary Format files[cite: 1].

### 2. Protocol Definition
*   **Induction Timing:** Specify the onset of induction in minutes. This point is defined as the origin ($t=0$)[cite: 1].
*   **Normalization Window:** Select the time range (in minutes) within the baseline to serve as the $100\%$ reference[cite: 1].

### 3. Biophysical Analysis
The algorithm extracts two primary metrics for every sweep:
*   **Peak Amplitude ($Amp_m$):** The maximum current peak (EPSC/IPSC)[cite: 1].
*   **Charge ($Ch_m$):** The area under the curve (integral), capturing the total ionic flux[cite: 1].

### 4. Normalization and Binning
Raw data are normalized according to the following formula[cite: 1]:
$$Value_{norm} = \left( \frac{Value_{observed}}{\bar{x}_{baseline}} \right) \times 100$$

Data points are subsequently grouped into temporal bins (typically 1-minute averages) to suppress stochastic noise and facilitate population-level visualization[cite: 1].

---

## 🛠️ Local Installation (Development)
To run the application locally or modify the source code:
1.  **Clone the repository:** `git clone [https://github.com/your-account/chavislab-plasticity.git](https://github.com/your-account/chavislab-plasticity.git)`[cite: 1]
2.  **Install dependencies:** `pip install streamlit pyabf pandas numpy matplotlib scipy statsmodels`[cite: 1]
3.  **Launch the interface:** `streamlit run app_biophysique.py`[cite: 1]

---

## 📊 Towards Population Analysis (Next Steps)
Individual files exported as `.csv` from this suite can be integrated into our secondary tool dedicated to **Population Statistics (Nested Mixed Models / GLMM)**[cite: 1]. This allows for rigorous group comparisons (e.g., WT vs. Mutant, Sham vs. Drug) while accounting for biological hierarchy (e.g., cells nested within mice, mice nested within litters)[cite: 1].

---

## 📑 Citations and Credits
When utilizing this tool for publication, please cite the Chavis Lab and the associated biophysical processing scripts[cite: 1].

**Developed for the Neuroscience Community | 2026**  
**Contact:** olivier.manzoni@inserm.fr[cite: 1]

> **Expert Guidance:** Do not overlook visual inspection. While the algorithm is robust, recordings with excessive background noise or unstable series resistance ($R_s$) can compromise normalization. Use the interactive plots to validate each cell prior to export[cite: 1].# 🧬 Synaptic Plasticity Analysis Suite
### *Chavis Lab & Manzoni Lab | Preprocessing & Biophysics*

-----------------------------------------------------------------------------------------------------------
-----------------------------------------------------------------------------------------------------------
-----------------------------------------------------------------------------------------------------------

Cette plateforme a été conçue pour standardiser le traitement des données d'électrophysiologie, de la trace brute (`.abf`) aux statistiques prêtes pour la publication. Elle permet de s'affranchir des biais de mesure manuelle en automatisant l'extraction des paramètres biophysiques et la normalisation temporelle.



## 🚀 Accès Rapide
L'application est disponible en libre accès via Streamlit Cloud :
👉 **[https://chavislab-plasticity.streamlit.app/](https://chavislab-plasticity.streamlit.app/)**

---

## 🔬 Pourquoi utiliser cette application ?

En recherche sur la plasticité synaptique (LTP/LTD), la précision du "Temps 0" et la stabilité de la ligne de base sont cruciales. Cette application permet de :
1. **Éviter la variabilité inter-opérateur** : L'algorithme détecte les pics et calcule les intégrales (charge) de la même manière pour chaque cellule.
2. **Standardiser le T=0** : Calage automatique de l'induction pour comparer les cinétiques de maintenance.
3. **Gérer les échelles** : Normalisation dynamique par rapport à une période de référence définie par l'utilisateur.
4. **Visualisation ultra rapide de vos expériences**

---

## 📖 Manuel de l'Utilisateur (Workflow)

### 1. Chargement des données
* **Fichier Baseline** : Importez votre trace de contrôle (avant induction).
* **Fichier Post** : Importez votre trace post-induction (incluant la phase de maintenance et, si applicable, le lavage pharmacologique).
* *Note : L'application utilise la bibliothèque `pyabf` pour lire nativement les fichiers Axon Binary Format.*

### 2. Définition du Protocole

* **Temps d'induction** : Indiquez à quelle minute l'induction a commencé. Cette minute deviendra le point d'origine ($t=0$).
* **Fenêtre de Normalisation** : Sélectionnez la plage de temps (en minutes) de la baseline qui servira de référence $100\%$.

### 3. Analyse Biophysique
L'algorithme extrait deux métriques clés pour chaque sweep :
* **L'Amplitude maximale ($Amp_m$)** : Le pic de courant (EPSC/IPSC).
* **La Charge ($Ch_m$)** : L'aire sous la courbe, capturant le flux ionique total.


### 4. Normalisation et Binning
Les données brutes sont normalisées selon la formule :
$$Value_{norm} = \left( \frac{Value_{observed}}{\bar{x}_{baseline}} \right) \times 100$$
Les points sont ensuite regroupés par **bins temporels** (moyennes par minute) pour lisser le bruit stochastique et faciliter la visualisation de la population.

---

## 🛠️ Installation Locale (Développeurs)

Si vous souhaitez faire tourner l'application sur votre machine ou modifier le code :

1.  **Cloner le dépôt** :
    ```bash
    git clone https://github.com/votre-compte/chavislab-plasticity.git
    ```
2.  **Installer les dépendances** :
    ```bash
    pip install streamlit pyabf pandas numpy matplotlib scipy statsmodels
    ```
3.  **Lancer l'interface** :
    ```bash
    streamlit run app_biophysique.py
    ```

---

## 📊 Vers l'Analyse de Population (Next Steps)

Une fois vos fichiers individuels exportés en `.csv` via cette application, vous pouvez les injecter dans notre second outil dédié aux **Statistiques de Population** (Modèles Mixtes Emboîtés / Nested GLMM). 

Cela permet de comparer vos groupes (WT vs Mutant, Sham vs Drug) en tenant compte de la hiérarchie biologique (nombre de cellules par souris, nombre de souris par portée).

---

## 📑 Citations et Crédits
Si vous utilisez cet outil pour vos publications, merci de mentionner le **Chavis Lab** et les scripts de traitement biophysique associés.

*Développé pour la communauté des neurosciences | 2026*
*Contact : olivier.manzoni@inserm.fr*

---

### Une petite astuce pour les étudiants :
> *Ne négligez pas l'inspection visuelle ! Même si l'algorithme est robuste, une trace avec un bruit de fond excessif ou un accès série (Rs) instable peut fausser votre normalisation. Utilisez les graphiques interactifs pour valider chaque cellule avant l'export.*

