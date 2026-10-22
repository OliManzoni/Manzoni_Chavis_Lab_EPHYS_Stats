"""Statistics independent of Streamlit. Contrasts are always comparison − reference."""
from itertools import combinations
import warnings
import numpy as np
import pandas as pd
from scipy import stats
import statsmodels.formula.api as smf
from statsmodels.stats.multitest import multipletests


def prepare(frame, metric, condition, unit, *, nested=None, x=None, independent=False):
    columns = list(dict.fromkeys([metric, condition, unit] + ([nested] if nested else []) + ([x] if x else [])))
    if len(columns) != 3 + bool(nested) + bool(x):
        raise ValueError('La mesure, la condition, les identifiants et le facteur répété doivent être des colonnes distinctes.')
    d = frame[columns].copy()
    d[metric] = pd.to_numeric(d[metric], errors='coerce').replace([np.inf, -np.inf], np.nan)
    if x:
        d[x] = pd.to_numeric(d[x], errors='coerce').replace([np.inf, -np.inf], np.nan)
    for c in [condition, unit] + ([nested] if nested else []):
        d[c] = d[c].replace(r'^\s*$', np.nan, regex=True)
    d = d.dropna()
    if d.empty:
        raise ValueError('Aucune observation complète pour cette mesure et ces identifiants.')
    for c in [condition, unit] + ([nested] if nested else []):
        d[c] = d[c].astype(str).str.strip()
    if d[condition].nunique() < 2:
        raise ValueError('Au moins deux conditions sont nécessaires.')
    if independent and d.groupby(unit)[condition].nunique().max() > 1:
        raise ValueError('Un même identifiant apparaît dans plusieurs conditions : choisissez une analyse appariée ou mixte, ou corrigez les identifiants.')
    return d


def unit_means(d, metric, condition, unit):
    """Each independent unit contributes once per condition, regardless of row count."""
    return d.groupby([condition, unit], observed=True, as_index=False)[metric].mean()


def descriptives(d, metric, condition, unit):
    u = unit_means(d, metric, condition, unit)
    out = u.groupby(condition, observed=True)[metric].agg(n='count', mean='mean', sd='std', sem='sem', median='median')
    half = stats.t.ppf(.975, out['n'] - 1) * out['sem']
    out['ci_low'] = out['mean'] - half
    out['ci_high'] = out['mean'] + half
    return out.reset_index()


def pairwise(d, metric, condition, unit, method='welch'):
    u = unit_means(d, metric, condition, unit)
    levels = list(pd.unique(u[condition]))
    rows = []
    for a, b in combinations(levels, 2):
        va = u.loc[u[condition] == a].set_index(unit)[metric]
        vb = u.loc[u[condition] == b].set_index(unit)[metric]
        paired = method in ('paired_t', 'wilcoxon')
        n_unpaired = 0
        if paired:
            both = pd.concat([va.rename('a'), vb.rename('b')], axis=1)
            n_unpaired = int(both.isna().any(axis=1).sum())
            both = both.dropna()
            va, vb = both.a, both.b
        aa, bb = va.to_numpy(), vb.to_numpy()
        row = dict(metric=metric, reference=a, comparison=b, method=method,
                   n_reference=len(aa), n_comparison=len(bb), unmatched_units=n_unpaired,
                   estimate=np.nan, ci_low=np.nan, ci_high=np.nan, effect=np.nan,
                   effect_name='', statistic=np.nan, p_raw=np.nan, status='ok')
        if min(len(aa), len(bb)) < 2:
            row['status'] = 'insufficient_units'
            rows.append(row)
            continue
        if method in ('welch', 'paired_t'):
            diff = bb.mean() - aa.mean()
            if method == 'welch':
                v1, v2 = aa.var(ddof=1) / len(aa), bb.var(ddof=1) / len(bb)
                if v1 + v2 <= 0:
                    row['status'] = 'zero_variance'
                    rows.append(row)
                    continue
                result = stats.ttest_ind(bb, aa, equal_var=False)
                df = (v1+v2)**2 / (v1*v1/(len(aa)-1)+v2*v2/(len(bb)-1))
                half = stats.t.ppf(.975, df) * np.sqrt(v1+v2)
                pooled = np.sqrt(((len(aa)-1)*aa.var(ddof=1)+(len(bb)-1)*bb.var(ddof=1))/(len(aa)+len(bb)-2))
                effect = diff / pooled * (1 - 3/(4*(len(aa)+len(bb))-9)) if pooled > 0 else np.nan
                effect_name = 'Hedges g (pooled SD)'
            else:
                differences = bb-aa
                if differences.std(ddof=1) <= 0:
                    row['status'] = 'zero_variance_of_differences'
                    rows.append(row)
                    continue
                result = stats.ttest_rel(bb, aa)
                half = stats.t.ppf(.975, len(aa)-1)*stats.sem(differences)
                effect, effect_name = diff/differences.std(ddof=1), 'Cohen dz (paired)'
            row.update(estimate=diff, ci_low=diff-half, ci_high=diff+half,
                       effect=effect, effect_name=effect_name, statistic=float(result.statistic), p_raw=float(result.pvalue))
        elif method == 'mannwhitney':
            result = stats.mannwhitneyu(bb, aa, alternative='two-sided', method='auto')
            row.update(statistic=float(result.statistic), p_raw=float(result.pvalue),
                       effect=2*result.statistic/(len(aa)*len(bb))-1, effect_name='rank-biserial (comparison > reference)')
        elif method == 'wilcoxon':
            diff = bb-aa
            if np.all(diff == 0):
                row.update(statistic=0., p_raw=1., effect=0., effect_name='paired rank-biserial')
            else:
                result = stats.wilcoxon(diff, zero_method='wilcox', alternative='two-sided', method='auto')
                nonzero = diff[diff != 0]
                ranks = stats.rankdata(np.abs(nonzero))
                effect = (ranks[nonzero > 0].sum()-ranks[nonzero < 0].sum())/ranks.sum()
                row.update(statistic=float(result.statistic), p_raw=float(result.pvalue), effect=effect, effect_name='paired rank-biserial')
        else:
            raise ValueError('Méthode inconnue.')
        rows.append(row)
    return pd.DataFrame(rows)


def adjust_family(results, method='holm'):
    """One family across every selected metric and every displayed contrast."""
    out = results.copy()
    out['p_adjusted'] = np.nan
    ok = np.isfinite(out.p_raw) & out.status.eq('ok')
    if ok.any():
        out.loc[ok, 'p_adjusted'] = multipletests(out.loc[ok, 'p_raw'], method=method)[1]
    out['correction'] = method
    out['family_size'] = int(ok.sum())
    return out


def mixed_model(d, metric, condition, unit, *, nested=None, x=None, random_slope=False):
    """Gaussian LMM, explicit unit intercept + optional nested intercept and slope.

    Categorical conditions are coded through safe internal column names. For a
    numeric repeated factor, each pairwise contrast is evaluated at mean(x).
    """
    cols = {metric:'y', condition:'condition', unit:'unit'}
    if nested: cols[nested] = 'nested'
    if x: cols[x] = 'x'
    m = d.rename(columns=cols)[list(cols.values())].copy()
    levels = list(pd.unique(m.condition))
    m['condition'] = pd.Categorical(m.condition, categories=levels)
    if m.unit.nunique() < 3:
        raise ValueError('Le modèle mixte nécessite ici au moins trois unités indépendantes.')
    if m.groupby('unit').size().max() < 2:
        raise ValueError('Une seule observation par unité : utilisez Welch ou ajoutez les mesures répétées.')
    if m.groupby('condition', observed=True).unit.nunique().min() < 2:
        raise ValueError('Chaque condition doit inclure au moins deux unités indépendantes.')
    vc = None
    if nested:
        if m.groupby(['unit','nested'], observed=True).size().max() < 2:
            raise ValueError('Un intercept cellule imbriqué nécessite des mesures répétées au sein des cellules ; sinon utilisez uniquement l’intercept animal.')
        vc = {'nested': '0 + C(nested)'}
    formula = 'y ~ C(condition)'
    x_center = None
    if x:
        if m.x.nunique() < 2:
            raise ValueError('Le facteur répété doit varier.')
        x_center = float(m.x.mean())
        m['x'] = m.x - x_center
        formula += ' * x'
    if random_slope and not x:
        raise ValueError('La pente aléatoire nécessite un facteur répété numérique.')
    if random_slope and (m.groupby('unit').x.nunique() < 2).any():
        raise ValueError('Chaque unité doit avoir au moins deux valeurs du facteur répété pour une pente aléatoire.')
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter('always')
        fit = smf.mixedlm(formula, m, groups=m.unit, re_formula='1 + x' if random_slope else '1', vc_formula=vc).fit(reml=True, method=['lbfgs','powell'], maxiter=500, disp=False)
    if not fit.converged:
        raise ValueError('Modèle non convergé : résultats inférentiels non affichés.')
    beta = fit.fe_params
    cov = fit.cov_params().loc[beta.index, beta.index]
    if not np.isfinite(cov.to_numpy()).all() or np.linalg.eigvalsh(cov.to_numpy()).min() <= 0:
        raise ValueError('Covariance des effets fixes non identifiable ; simplifiez le modèle.')
    from patsy import build_design_matrices
    prediction = pd.DataFrame({'condition': pd.Categorical(levels, categories=levels)})
    if x: prediction['x'] = 0.
    design = np.asarray(build_design_matrices([fit.model.data.design_info], prediction)[0])
    rows = []
    for ia, ib in combinations(range(len(levels)), 2):
        contrast = design[ib]-design[ia]
        estimate = float(contrast @ beta)
        se = float(np.sqrt(contrast @ cov @ contrast))
        if not np.isfinite(se) or se <= 0:
            raise ValueError('Erreur standard du contraste invalide.')
        z = estimate/se
        rows.append(dict(metric=metric, reference=levels[ia], comparison=levels[ib], method='mixed_LMM',
                         n_reference=m.loc[m.condition==levels[ia],'unit'].nunique(), n_comparison=m.loc[m.condition==levels[ib],'unit'].nunique(),
                         estimate=estimate, ci_low=estimate-1.96*se, ci_high=estimate+1.96*se,
                         effect=np.nan, effect_name='difference (original units)', statistic=z,
                         p_raw=float(2*stats.norm.sf(abs(z))), status='ok', x_reference=x_center))
    coefficients = pd.DataFrame({'term': beta.index, 'estimate': beta.to_numpy(),
                                  'se': np.sqrt(np.diag(cov)), 'p_raw': fit.pvalues.loc[beta.index].to_numpy()})
    coefficients['metric'] = metric
    coefficients['status'] = 'ok'
    coefficients['ci_low'] = coefficients.estimate-1.96*coefficients.se
    coefficients['ci_high'] = coefficients.estimate+1.96*coefficients.se
    diagnostics = pd.DataFrame({'fitted':fit.fittedvalues, 'residual':fit.resid, 'unit':m.unit})
    notes = list(dict.fromkeys(str(w.message) for w in caught))
    if m.unit.nunique() < 10:
        notes.append('Moins de dix unités : p-valeurs et IC du modèle mixte reposent sur une approximation asymptotique fragile.')
    random_variances = np.r_[np.diag(fit.cov_re), fit.vcomp]
    if (random_variances < 1e-6 * max(float(fit.scale), 1e-12)).any():
        notes.append('Variance aléatoire proche de zéro : modèle à la frontière, envisager une structure plus simple.')
    return pd.DataFrame(rows), coefficients, diagnostics, notes
