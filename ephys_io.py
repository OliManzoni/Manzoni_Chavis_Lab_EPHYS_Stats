"""Lossless table ingestion and reproducible download bundles."""
import io
import json
import hashlib
import zipfile
from importlib.metadata import version, PackageNotFoundError
import pandas as pd


def read_table(payload):
    last = None
    for encoding in ('utf-8-sig','cp1252'):
        try:
            text = payload.decode(encoding)
        except UnicodeDecodeError as exc:
            last = exc
            continue
        lines = text.splitlines()
        start = 2 if lines and lines[0].lstrip().startswith('Tableau') else 0
        header = lines[start] if len(lines) > start else ''
        sep = '\t' if '\t' in header else (';' if header.count(';') > header.count(',') else ',')
        try:
            frame = pd.read_csv(io.StringIO('\n'.join(lines[start:])), sep=sep, decimal=',' if sep==';' else '.', dtype=None)
            frame.columns = frame.columns.astype(str).str.strip()
            if frame.columns.duplicated().any():
                raise ValueError('Noms de colonnes dupliqués.')
            return frame.loc[:, ~frame.columns.str.match(r'^Unnamed')].dropna(how='all')
        except (pd.errors.ParserError, pd.errors.EmptyDataError) as exc:
            last = exc
    raise ValueError(f'CSV illisible : {last}')


def digest(payload):
    return hashlib.sha256(payload).hexdigest()


def bundle(tables, figures, settings):
    """Archive with source tables, settings, dependency versions and vector figures."""
    versions = {}
    for package in ('numpy','pandas','scipy','statsmodels','matplotlib','streamlit','pyabf'):
        try: versions[package] = version(package)
        except PackageNotFoundError: versions[package] = 'unavailable'
    meta = dict(settings, software_versions=versions)
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as z:
        for name, table in tables.items():
            z.writestr(name+'.csv', table.to_csv(index=False).encode('utf-8-sig'))
        for name, fig in figures.items():
            for fmt in ('pdf','svg','png'):
                image = io.BytesIO()
                fig.savefig(image, format=fmt, dpi=300, bbox_inches='tight')
                z.writestr(name+'.'+fmt, image.getvalue())
        z.writestr('parameters.json', json.dumps(meta, ensure_ascii=False, indent=2, default=str))
    return buffer.getvalue()
