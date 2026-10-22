import io
import json
import zipfile
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd
from ephys_io import bundle


def test_reproducible_bundle_contains_tables_settings_and_real_figures():
    fig,ax=plt.subplots();ax.plot([1,2],[3,4])
    payload=bundle({'used':pd.DataFrame({'x':[1,2]})},{'curve':fig},{'unit':'Animal_ID'})
    with zipfile.ZipFile(io.BytesIO(payload)) as z:
        assert z.read('curve.pdf').startswith(b'%PDF')
        assert b'<svg' in z.read('curve.svg')
        assert z.read('curve.png').startswith(b'\x89PNG')
        assert json.loads(z.read('parameters.json'))['unit']=='Animal_ID'
        assert pd.read_csv(z.open('used.csv')).x.tolist()==[1,2]
    plt.close(fig)
