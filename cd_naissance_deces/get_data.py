import json
from io import BytesIO
from urllib.request import urlopen
from zipfile import ZipFile

import dateutil as du
import pandas as pd

#from transform_data import *
import pandas as pd
import json

def replace_dep(x):
    if x == '2A':
        return 2.1
    if x == '2B':
        return 2.2
    return x

def unplace_dep(x):
    if x == 2.1:
        return '2A'
    if x == 2.2:
        return '2B'
    if x < 10.0:
        return str("0" + str(int(x)))
    return str(x.astype(int))

def fix_dep(df, cols):
    for col in cols:
        df[col] = list(map(unplace_dep, pd.to_numeric(list(map(replace_dep, df[col])))))
    return df

def do_tudom(dfn):
    tudom = dfn.groupby(['DEPNAIS', 'DEPDOM', 'TUDOM']).size().rename('SIZE').to_frame()
    tudom = tudom.reset_index()
    tudom = tudom[tudom['DEPNAIS'] == tudom['DEPDOM']]
    tudom = tudom.drop(columns=['DEPDOM'])
    return tudom

def do_dep(dfn, dfd):
    # Get geojson department name.
    with open('data/jcwg_departements.geojson') as f:
        dep = json.load(f)

    # Create a map between department code and department name.
    dep_map = {unplace_dep(pd.to_numeric(replace_dep(d['properties']['code']))): d['properties']['nom']
               for d in dep['features']}
    # Number of naissance/deces by department and date
    daten = dfn.groupby(['DEPNAIS', 'date']).size().rename(
        'SIZE').to_frame()
    dated = dfd.groupby(['DEPDEC', 'date']).size().rename(
        'SIZE').to_frame()

    # Number of naissance/deces by department
    depn = dfn.groupby('DEPNAIS').size().rename('SIZE').to_frame()
    depd = dfd.groupby('DEPDEC').size().rename('SIZE').to_frame()

    # Remove data about department not contained in the geojson
    depn['NAME'] = [dep_map[d]
                    if d in dep_map else 'NON'
                    for d in depn.index]
    depd['NAME'] = [dep_map[d]
                    if d in dep_map else 'NON'
                    for d in depd.index]

    depn = depn.drop(depn[depn['NAME'] == 'NON'].index)
    depd = depd.drop(depd[depd['NAME'] == 'NON'].index)
    return [daten, dated, depn, depd]

def do_agen_aged(dfn,dfd):
    # Data about naissance/deces of men/women by their age
    agemn = dfn.groupby(['DEPNAIS', 'AGEMERE']).size().rename('SIZEMEREN')
    agepn = dfn.groupby(['DEPNAIS', 'AGEPERE']).size().rename('SIZEPEREN')

    agemd = dfd.loc[dfd.SEXE == 2, ['DEPDEC', 'AGE']].groupby(
        ['DEPDEC', 'AGE']).size().rename('SIZEMERED')
    agepd = dfd.loc[dfd.SEXE == 1, ['DEPDEC', 'AGE']].groupby(
        ['DEPDEC', 'AGE']).size().rename('SIZEPERED')

    agen = pd.concat([agemn, agepn, ], axis=1)
    agen['SIZEMEREPEREN'] = agen['SIZEMEREN'] + agen[
        'SIZEPEREN']
    agen['MGMEREPEREN'] = (agen['SIZEMEREN'] + agen[
        'SIZEPEREN']) // 2

    aged = pd.concat([agemd, agepd, ], axis=1)
    aged['SIZEMEREPERED'] = aged['SIZEMERED'] + aged[
        'SIZEPERED']
    aged['MGMEREPERED'] = (aged['SIZEMERED'] + aged[
        'SIZEPERED']) // 2
    return agen, aged

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
    tudom = do_tudom(dfn)

    # Save to csv
    tudom.fillna(0).to_pickle('data/1/jcwg_tudom' + year + '.pkl')
    dep[0].fillna(0).to_pickle('data/1/jcwg_date_naissance' + year + '.pkl')
    dep[1].fillna(0).to_pickle('data/1/jcwg_date_deces' + year + '.pkl')

    dep[2].fillna(0).to_pickle('data/1/jcwg_department_naissance' + year + '.pkl')
    dep[3].fillna(0).to_pickle('data/1/jcwg_department_deces' + year + '.pkl')

    agen.fillna(0).to_pickle('data/1/jcwg_age_naissance' + year + '.pkl')
    aged.fillna(0).to_pickle('data/1/jcwg_age_deces' + year + '.pkl')


def convert_date(y, m):
    """Convert data to dataframe.datetime format.

    :param y: year.
    :param m: month.
    :return:
    """
    return du.parser.parse(f"15-{m}-{y}")


if __name__ == '__main__':
    url_naissance = ['https://www.insee.fr/fr/statistiques/fichier/4768335/etatcivil2019_nais2019_csv.zip', 
    "https://www.insee.fr/fr/statistiques/fichier/5419785/etatcivil2020_nais2020_csv.zip"]
    url_deces = ['https://www.insee.fr/fr/statistiques/fichier/4801913/etatcivil2019_dec2019_csv.zip',
    "https://www.insee.fr/fr/statistiques/fichier/5431034/etatcivil2020_dec2020_csv.zip"]
    save_data_as_pkl(url_naissance[0], url_deces[0], '19')
    save_data_as_pkl(url_naissance[1], url_deces[1], '20')
