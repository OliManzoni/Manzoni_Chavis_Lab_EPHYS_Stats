"""Shared presentation and per-session caches (no shared mutable ABF object)."""
import io
from pathlib import Path
import streamlit as st


def session_compute(namespace, signature, compute):
    key = '_ephys_cache_' + namespace
    entry = st.session_state.get(key)
    if entry is None or entry[0] != signature:
        value = compute()  # Failed computations never replace the last successful result.
        st.session_state[key] = (signature, value)
    return st.session_state[key][1]


def show_figure(fig, *, key):
    import matplotlib.pyplot as plt
    st.pyplot(fig)
    with st.expander('Exporter la figure'):
        fmt = st.selectbox('Format', ['pdf', 'svg', 'png'], key=key+'_format')
        data = io.BytesIO()
        fig.savefig(data, format=fmt, dpi=300, bbox_inches='tight')
        st.download_button('Télécharger la figure', data.getvalue(), file_name=key+'.'+fmt,
                           mime={'pdf':'application/pdf','svg':'image/svg+xml','png':'image/png'}[fmt], key=key+'_download')
    plt.close(fig)


def logo_path():
    return str(Path(__file__).resolve().parent / 'logo_chavis_final.png')


def recording_metadata(prefix, filename):
    with st.expander('Identifiants pour les statistiques et les exports'):
        condition = st.text_input('Condition', 'Groupe 1', key=prefix+'_condition')
        animal = st.text_input('Animal_ID', '', key=prefix+'_animal')
        cell = st.text_input('Cell_ID', Path(filename).stem, key=prefix+'_cell_'+filename)
    return {'Condition':condition, 'Animal_ID':animal, 'Cell_ID':cell, 'Source_File':filename}


def export_parameters(settings, *, key):
    import json
    st.download_button('Télécharger les paramètres de cette analyse',
                       json.dumps(settings, ensure_ascii=False, indent=2, default=str),
                       key+'_parameters.json', mime='application/json', key=key+'_parameters')
