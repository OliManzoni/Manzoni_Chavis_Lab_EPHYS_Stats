# 🧬 Synaptic Plasticity Analysis Suite
### *Chavis Lab & Manzoni Lab | Preprocessing & Biophysics*

Cette plateforme a été conçue pour standardiser le traitement des données d'électrophysiologie, de la trace brute (`.abf`) aux statistiques prêtes pour la publication. Elle permet de s'affranchir des biais de mesure manuelle en automatisant l'extraction des paramètres biophysiques et la normalisation temporelle.

---

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

