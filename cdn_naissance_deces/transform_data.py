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