"""Statistical workspace: explicit experimental units and reproducible outputs."""
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats
import streamlit as st
from ephys_io import read_table, digest, bundle
from ephys_stats import prepare, unit_means, descriptives, pairwise, adjust_family, mixed_model
from ephys_ui import session_compute
from ephys_tutorials import render_beginner_guide

lang = st.session_state.get("global_language", "Français")
en = lang == "English"
def tr(fr, english):
    return english if en else fr

render_beginner_guide("stats", lang)
st.title(tr("⚖️ Statistiques et figures de population", "⚖️ Statistics and population figures"))
st.caption(tr(
    "Définissez le plan expérimental avant de choisir le test. Les identifiants d’animaux doivent être uniques dans toute l’étude ; un identifiant commun aux conditions indique un appariement.",
    "Define the experimental design before choosing a test. Animal identifiers must be unique across the study; a shared identifier across conditions indicates pairing.",
))

mode_labels = {
    tr("Table longue avec une colonne de condition", "Long-format table with a condition column"): "long",
    tr("Deux groupes de fichiers", "Two groups of files"): "groups",
}
mode_label = st.radio(tr("Format des données", "Data format"), list(mode_labels), horizontal=True)
mode = mode_labels[mode_label]
frames, sources = [], []
if mode == "long":
    uploads = st.file_uploader(
        tr("CSV : une ligne par mesure, avec identifiants et condition",
           "CSV: one row per observation, with identifiers and condition"),
        type=["csv", "txt"], accept_multiple_files=True,
    )
    batches = [(uploads, None)]
else:
    a, b = st.columns(2)
    name_a = a.text_input(tr("Nom du groupe 1", "Group 1 name"), tr("Contrôle", "Control"))
    name_b = b.text_input(tr("Nom du groupe 2", "Group 2 name"), tr("Traitement", "Treatment"))
    up_a = a.file_uploader(tr("Fichiers CSV du groupe 1", "Group 1 CSV files"), type=["csv"], accept_multiple_files=True)
    up_b = b.file_uploader(tr("Fichiers CSV du groupe 2", "Group 2 CSV files"), type=["csv"], accept_multiple_files=True)
    if not name_a.strip() or not name_b.strip() or name_a == name_b:
        st.info(tr("Utilisez deux noms de groupes distincts et non vides.", "Enter two distinct, non-empty group names."))
        st.stop()
    batches = [(up_a, name_a), (up_b, name_b)]

seen = set()
for uploads, group in batches:
    for f in uploads or []:
        payload = f.getvalue()
        fingerprint = digest(payload)
        if fingerprint in seen:
            st.error(tr(f"Fichier chargé deux fois : {f.name}. Retirez le doublon.",
                        f"File uploaded twice: {f.name}. Remove the duplicate."))
            st.stop()
        seen.add(fingerprint)
        try:
            frame = read_table(payload)
        except ValueError as exc:
            st.error(tr(f"{f.name} : {exc}", f"{f.name}: {exc}"))
            st.stop()
        if group is not None:
            frame["Condition"] = group
        frame["Source_File"] = f.name
        frames.append(frame)
        sources.append({"name": f.name, "sha256": fingerprint, "rows": len(frame)})

if not frames:
    st.info(tr(
        "Importez vos données. Les exports doivent contenir des identifiants Animal_ID ou Cell_ID, par exemple.",
        "Upload your data. The table should include identifiers such as Animal_ID or Cell_ID.",
    ))
    example = pd.DataFrame({
        "Condition": [tr("Contrôle", "Control"), tr("Contrôle", "Control"), tr("Traitement", "Treatment"), tr("Traitement", "Treatment")],
        "Animal_ID": ["A01", "A02", "A03", "A04"],
        "Cell_ID": ["C01", "C02", "C03", "C04"],
        "Rin_MOhms": [120, 135, 145, 150],
    })
    st.download_button(tr("Télécharger un modèle CSV", "Download a CSV template"), example.to_csv(index=False),
                        "modele_statistiques.csv" if not en else "statistics_template.csv")
    st.stop()

data = pd.concat(frames, ignore_index=True, sort=False)
with st.expander(tr("Données importées et identifiants", "Imported data and identifiers"), expanded=False):
    st.dataframe(data, use_container_width=True)
    st.caption(tr(
        "Les fichiers sont empilés sans fusion implicite ni suppression de colonnes. Importez uniquement les observations à analyser ensemble.",
        "Files are stacked without implicit merging or column removal. Upload only observations that belong in the same analysis.",
    ))

cols = [c for c in data.columns if c != "Source_File"]
condition = st.selectbox(tr("Colonne indiquant la condition", "Condition column"), cols,
                          index=cols.index("Condition") if "Condition" in cols else 0)
ids = [c for c in cols if c != condition]
if not ids:
    st.error(tr("Il manque les colonnes de mesure et d’identifiant.", "Measurement and identifier columns are missing."))
    st.stop()
preferred = next((c for c in ["Animal_ID", "Mouse_ID", "Cell_ID", "File"] if c in ids), ids[0])
unit = st.selectbox(tr("Unité expérimentale indépendante / identifiant d’appariement", "Independent experimental unit / pairing identifier"),
                    ids, index=ids.index(preferred))
method_labels = {
    tr("Welch — groupes indépendants", "Welch — independent groups"): "welch",
    tr("Mann–Whitney — groupes indépendants", "Mann–Whitney — independent groups"): "mannwhitney",
    tr("Test t apparié", "Paired t-test"): "paired_t",
    tr("Wilcoxon apparié", "Paired Wilcoxon"): "wilcoxon",
    tr("Modèle linéaire mixte", "Linear mixed model"): "mixed",
}
method_label = st.selectbox(tr("Plan et méthode statistique", "Design and statistical method"), list(method_labels))
method = method_labels[method_label]
remaining = [c for c in ids if c != unit]
none_label = tr("Aucune", "None")
nested_label = st.selectbox(tr("Sous-unité facultative (ex. cellule dans l’animal)", "Optional nested unit (e.g. cell within animal)"),
                            [none_label]+remaining)
nested = None if nested_label == none_label else nested_label
x = None
random_slope = False
if method == "mixed":
    factor_label = tr("Aucun", "None")
    x_label = st.selectbox(tr("Facteur répété numérique (temps ou courant), facultatif", "Optional numeric repeated factor (time or current)"),
                           [factor_label]+[c for c in remaining if c != nested])
    x = None if x_label == factor_label else x_label
    if x:
        st.caption(tr(
            "Le modèle condition × facteur numérique estime une tendance linéaire. Les différences de condition sont évaluées à la valeur moyenne du facteur. Pour une courbe non linéaire, ce modèle ne remplace pas une analyse adaptée au protocole.",
            "The condition × numeric-factor model estimates a linear trend. Condition differences are evaluated at the mean factor value. For nonlinear curves, use a protocol-specific analysis.",
        ))
        random_slope = st.checkbox(tr("Pente aléatoire par unité", "Random slope by unit"), value=False)
    st.caption(tr(
        "IC de Wald et p-valeurs asymptotiques. Les graphes de distribution montrent les moyennes par unité ; les effets ajustés figurent dans le graphe des contrastes.",
        "Wald confidence intervals and asymptotic p-values are used. Distribution plots show unit-level means; adjusted effects appear in the contrast plot.",
    ))
else:
    st.caption(tr(
        "Les répétitions sont moyennées par unité avant le test. Avec une sous-unité, la moyenne est d’abord calculée par cellule puis par animal. Les tests appariés conservent uniquement les paires complètes pour chaque contraste.",
        "Repeated observations are averaged within each unit before testing. With a nested unit, values are averaged by cell and then by animal. Paired tests use complete pairs for each contrast.",
    ))

metrics_options = [c for c in remaining if c not in {nested, x} and pd.to_numeric(data[c], errors="coerce").notna().any()]
metrics = st.multiselect(tr("Mesures à comparer (famille de tests)", "Outcomes to compare (test family)"),
                         metrics_options, default=metrics_options[:1])
correction_labels = {
    tr("Holm (erreur familiale)", "Holm (family-wise error)"): "holm",
    tr("Benjamini–Hochberg (FDR exploratoire)", "Benjamini–Hochberg (exploratory FDR)"): "fdr_bh",
}
correction_label = st.selectbox(tr("Correction des comparaisons multiples", "Multiple-comparison correction"), list(correction_labels))
correction = correction_labels[correction_label]
if not metrics:
    st.stop()

settings = dict(method=method, condition=condition, unit=unit, nested=nested, repeated_factor=x,
                random_slope=random_slope, metrics=metrics, correction=correction, sources=sources,
                confidence_level=.95, confidence_intervals="pointwise, not multiplicity adjusted",
                exclusions="complete-case per metric; no automatic outlier removal")
signature = str(settings)

def calculate():
    results, descriptions, coefficients, diagnostics, retained, notes = [], {}, [], {}, {}, []
    for metric in metrics:
        try:
            d = prepare(data, metric, condition, unit, nested=nested, x=x,
                        independent=method in ("welch", "mannwhitney"))
            missing = len(data)-len(d)
            if missing:
                notes.append(tr(f"{metric} : {missing} lignes incomplètes écartées.",
                                f"{metric}: {missing} incomplete rows omitted."))
            if nested and method != "mixed":
                d = d.groupby([condition, unit, nested], observed=True, as_index=False)[metric].mean()
            retained[metric] = d
            descriptions[metric] = descriptives(d, metric, condition, unit)
            if method == "mixed":
                r, c, diag, warnings = mixed_model(d, metric, condition, unit, nested=nested, x=x,
                                                   random_slope=random_slope)
                coefficients.append(c)
                diagnostics[metric] = diag
                notes.extend(f"{metric}: {message}" for message in warnings)
            else:
                r = pairwise(d, metric, condition, unit, method)
            results.append(r)
        except (ValueError, np.linalg.LinAlgError) as exc:
            notes.append(tr(f"{metric} : analyse impossible — {exc}", f"{metric}: analysis failed — {exc}"))
    if not results:
        return None, descriptions, None, diagnostics, retained, notes
    result = adjust_family(pd.concat(results, ignore_index=True), correction)
    coef = None
    if coefficients:
        coef = pd.concat(coefficients, ignore_index=True)
        mask = coef.term.ne("Intercept")
        adjusted = adjust_family(coef.loc[mask], correction)
        coef["p_adjusted"] = np.nan
        coef.loc[mask, "p_adjusted"] = adjusted.p_adjusted
    return result, descriptions, coef, diagnostics, retained, notes

if st.button(tr("Calculer et préparer les figures", "Calculate and prepare figures"), type="primary"):
    with st.spinner(tr("Calcul des statistiques…", "Calculating statistics…")):
        try:
            st.session_state["stats_result"] = (signature, calculate())
        except Exception as exc:
            st.error(tr(f"Calcul interrompu : {exc}", f"Calculation stopped: {exc}"))
            st.stop()

saved = st.session_state.get("stats_result")
if not saved or saved[0] != signature:
    st.info(tr("Lancez le calcul pour ces données et paramètres.", "Run the calculation for these data and settings."))
    st.stop()
result, summaries, coef, diagnostics, retained, notes = saved[1]
for note in notes:
    st.warning(note)
if result is None:
    st.stop()

st.subheader(tr("Contrastes : comparaison − référence", "Contrasts: comparison − reference"))
st.dataframe(result, use_container_width=True)
st.caption(tr(
    "Les p-valeurs corrigées couvrent tous les contrastes estimables affichés. Les IC à 95 % sont ponctuels, sans correction de multiplicité. Pour les tests de rangs, l’effet rapporté est une corrélation bisérielle de rang ; aucun IC de différence de moyenne n’est présenté.",
    "Adjusted p-values cover all estimable contrasts shown. The 95% confidence intervals are pointwise and are not multiplicity-adjusted. For rank tests, the reported effect is a rank-biserial correlation; no mean-difference interval is shown.",
))
if coef is not None:
    with st.expander(tr("Coefficients des modèles et interactions", "Model coefficients and interactions")):
        st.dataframe(coef, use_container_width=True)
        st.caption(tr(
            "Famille de correction distincte : tous les termes fixes hors intercept, pour toutes les mesures sélectionnées.",
            "Separate correction family: all non-intercept fixed terms across the selected outcomes.",
        ))
if method in ("paired_t", "wilcoxon"):
    st.caption(tr(
        "Les points montrent toutes les unités disponibles ; chaque contraste utilise ses paires complètes, exportées dans un tableau dédié.",
        "Points show all available units; each contrast uses its complete pairs, which are included in a separate export table.",
    ))

figures, tables = {}, {"contrasts": result, "input_data": data}
if coef is not None:
    tables["model_coefficients"] = coef
for index, metric in enumerate(metrics):
    if metric not in retained:
        continue
    d = retained[metric]
    u = unit_means(d, metric, condition, unit)
    levels = list(pd.unique(u[condition]))
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))
    rng = np.random.default_rng(42)
    if method in ("paired_t", "wilcoxon"):
        pivot = u.pivot(index=unit, columns=condition, values=metric).reindex(columns=levels)
        for _, row in pivot.iterrows():
            axes[0].plot(range(len(levels)), row.to_numpy(), color=".7", alpha=.5, lw=.7)
    for j, level in enumerate(levels):
        values = u.loc[u[condition] == level, metric]
        axes[0].scatter(j+rng.uniform(-.08, .08, len(values)), values, alpha=.75, s=22)
        axes[0].plot([j-.15, j+.15], [values.mean()]*2, color="black", lw=2)
    axes[0].set(xticks=range(len(levels)), xticklabels=levels, ylabel=metric,
                title=tr(f"Moyennes par {unit}", f"Means by {unit}"))
    contrasts = result.loc[result.metric.eq(metric) & result.status.eq("ok") & result.estimate.notna()]
    if len(contrasts):
        est = contrasts.estimate.to_numpy()
        axes[1].errorbar(est, np.arange(len(est)),
                         xerr=np.array([est-contrasts.ci_low.to_numpy(), contrasts.ci_high.to_numpy()-est]),
                         fmt="o", color="#176b87", capsize=3)
        axes[1].set(yticks=range(len(est)),
                    yticklabels=contrasts.comparison.astype(str)+" − "+contrasts.reference.astype(str),
                    xlabel=tr("Différence et IC à 95 %", "Difference and 95% CI"))
        axes[1].axvline(0, color=".5", ls="--")
    else:
        axes[1].axis("off")
        axes[1].text(.05, .5, tr("Tests de rangs : effets dans le tableau.", "Rank-test effects are listed in the table."),
                     transform=axes[1].transAxes)
    fig.tight_layout()
    st.pyplot(fig)
    figures[f"metric_{index+1}"] = fig
    tables[f"metric_{index+1}_used"] = d
    tables[f"metric_{index+1}_unit_means"] = u
    if method in ("paired_t", "wilcoxon"):
        from itertools import combinations
        for ia, ib in combinations(range(len(levels)), 2):
            pair_table = u.pivot(index=unit, columns=condition, values=metric)[[levels[ia], levels[ib]]].dropna().reset_index()
            tables[f"metric_{index+1}_pair_{ia+1}_{ib+1}"] = pair_table
    tables[f"metric_{index+1}_summary"] = summaries[metric]
    if metric in diagnostics:
        diag = diagnostics[metric]
        diagnostic, ax = plt.subplots(1, 2, figsize=(10, 4))
        ax[0].scatter(diag.fitted, diag.residual, s=10, alpha=.5)
        ax[0].axhline(0, color=".5")
        ax[0].set(xlabel=tr("Valeur ajustée", "Fitted value"), ylabel=tr("Résidu", "Residual"))
        stats.probplot(diag.residual, plot=ax[1])
        ax[1].set_title(tr("Graphique Q-Q normal", "Normal Q-Q plot"))
        ax[1].set_xlabel(tr("Quantiles théoriques", "Theoretical quantiles"))
        ax[1].set_ylabel(tr("Quantiles observés des résidus", "Ordered residuals"))
        diagnostic.tight_layout()
        with st.expander(tr(f"Diagnostics — {metric}", f"Diagnostics — {metric}")):
            st.pyplot(diagnostic)
        figures[f"metric_{index+1}_diagnostics"] = diagnostic
        tables[f"metric_{index+1}_diagnostics"] = diag

settings["metric_file_mapping"] = {f"metric_{i+1}": m for i, m in enumerate(metrics)}
archive = session_compute("stats_archive", signature, lambda: bundle(tables, figures, settings))
st.download_button(
    tr("Télécharger le dossier complet : figures, CSV et paramètres",
       "Download full package: figures, CSV tables, and settings"),
    archive, "ephys_statistics.zip", mime="application/zip",
)
for fig in figures.values():
    plt.close(fig)
