import json
from io import BytesIO
from urllib.request import urlopen
from zipfile import ZipFile

import dateutil as du
import pandas as pd
import ssl
ssl._create_default_https_context = ssl._create_unverified_context

from transform_data import *
def get_data_from_url(url, as_str):
    """Unzip the data and return the dataframe.

    :param url: url of the zip.
    :param as_str: columns to parse as string.
    :return:
    """
    data = urlopen(url)
    zipfile = ZipFile(BytesIO(data.read()))
    files = []
    with zipfile as f:
        for name in f.namelist():
            with f.open(name) as zd:
                files.append(
                    pd.read_csv(zd, delimiter=';', dtype={as_str: str}))
    return files[0]

def save_data_as_pkl(urlsn, urlsd, year):
    """Download online data and save it as pickle.

    :param urlsn: URL of naissance data.
    :param urlsd: URL of deces data.
    """
    dfn = fix_dep(get_data_from_url(urlsn, 'DEPNAIS'), ['DEPNAIS', 'DEPDOM'])
    dfd = fix_dep(get_data_from_url(urlsd, 'DEPDEC'), ['DEPDEC'])

    # Set 'date' from Month And Year information.
    dfn['date'] = dfn.apply(lambda x: convert_date(x.ANAIS, x.MNAIS), axis=1)
    dfn.set_index('date', inplace=True)

    # Set 'date' from Month And Year information.
    dfd['date'] = dfd.apply(lambda x: convert_date(x.ADEC, x.MDEC), axis=1)
    dfd['AGE'] = dfd['ADEC'] - dfd['ANAIS']
    dfd.set_index('date', inplace=True)

    dep = do_dep(dfn, dfd)
    agen, aged = do_agen_aged(dfn, dfd)
    tudom = dfn.groupby(['DEPDOM', 'TUDOM']).size().rename('SIZE').to_frame()

    # Save to csv
    tudom.fillna(0).to_pickle('ndf_naissance_deces/data/tudom' + year + '.pkl')
    dep[0].fillna(0).to_pickle('ndf_naissance_deces/data/date_naissance' + year + '.pkl')
    dep[1].fillna(0).to_pickle('ndf_naissance_deces/data/date_deces' + year + '.pkl')
    agen.to_pickle('ndf_naissance_deces/data/age_naissance' + year + '.pkl')
    aged.to_pickle('ndf_naissance_deces/data/age_deces' + year + '.pkl')


def convert_date(y, m):
    """Convert data to dataframe.datetime format.

    :param y: year.
    :param m: month.
    :return:
    """
    return du.parser.parse(f"15-{m}-{y}")


if __name__ == '__main__':
    url_naissance = ['https://www.insee.fr/fr/statistiques/fichier/4215180/etatcivil2018_nais2018_csv.zip',
                     'https://www.insee.fr/fr/statistiques/fichier/4768335/etatcivil2019_nais2019_csv.zip', 
                     "https://www.insee.fr/fr/statistiques/fichier/5419785/etatcivil2020_nais2020_csv.zip"]
    url_deces = ['https://www.insee.fr/fr/statistiques/fichier/4216603/etatcivil2018_dec2018_csv.zip',
                 'https://www.insee.fr/fr/statistiques/fichier/4801913/etatcivil2019_dec2019_csv.zip',
                 "https://www.insee.fr/fr/statistiques/fichier/5431034/etatcivil2020_dec2020_csv.zip"]
    save_data_as_pkl(url_naissance[0], url_deces[0], '18')
    save_data_as_pkl(url_naissance[1], url_deces[1], '19')
    save_data_as_pkl(url_naissance[2], url_deces[2], '20')
