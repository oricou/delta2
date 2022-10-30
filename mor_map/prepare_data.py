import sys
import pandas as pd
import numpy as np
import dateutil as du


mois = {'janv': 1, 'févr': 2, 'mars': 3, 'avr': 4, 'mai': 5, 'juin': 6, 'juil': 7, 'août': 8, 'sept': 9, 'oct': 10,
        'nov': 11, 'déc': 12}

quoi = {"Prix d'une tonne de propane": [1000, 'Propane'], "Bouteille de butane de 13 kg": [13, 'Butane'],
        "100 litres de FOD au tarif C1": [100, 'Fioul'], "Un litre d'essence ordinaire": [1, 'Essence'],
        "Un litre de super carburant ARS": [1, 'Essence'], "Un litre de super sans plomb 95": [1, 'Essence'],
        "Un litre de super sans plomb 98": [1, 'Essence'], "Un litre de gazole": [1, 'Gazole'],
        "Un litre de GPLc": [1, 'GPL'], "1 kWh (contrat 3 kW)": [1, 'Electricité'],
        "1 kWh (contrat 9 kW)": [1, 'Electricité'],
        "Une tonne de granulés de bois en vrac": [1000 * 4.8, 'Electricité'],
        "100 kWh PCI de bois en vrac": [100, 'Electricité']}

densité = {'Essence': 0.75, 'Gazole': 0.85, 'Fioul': 0.85, 'GPL': 0.55}  # kg / l

# https://fr.wikipedia.org/wiki/Pouvoir_calorifique
calor = {'Essence': 47.3, 'Gazole': 44.8, 'Fioul': 42.6, 'Propane': 50.35, 'Butane': 49.51, 'GPL': 46, 'Bois': 15,
         'Charbon': 20,
         'Electricité': 3.6}  # en MJ / kg sauf électicité en MJ / kWh

def _conv_date(d):
    ma = d.split('-')  # coupe la chaine au - et ainsi ma[0] est le mois et ma[1] l'année
    return du.parser.parse(
        f"15-{mois[ma[0].lower()]}-{ma[1]}")  # parfois le mois a une majuscule d'où lower()

def _make_dataframe_from_pegase(filename):
    df = pd.read_csv(filename, sep=";", encoding="latin1", skiprows=[0, 1, 3], header=None)
    df = df.set_index(0).T
    df['date'] = df['Période'].apply(_conv_date)
    df = df.set_index('date')
    df.drop(columns=['Période'], inplace=True)
    df = df.replace('-', np.nan).astype('float64')
    return df

bois = _make_dataframe_from_pegase("data/pegase_prix_bois_particulier.csv")
petrole = _make_dataframe_from_pegase("data/pegase_prix_petrole_particulier.csv")

bois.drop(columns=['Une tonne de granulés de bois en sacs', '100 kWh PCI de bois en sacs'], inplace=True)
petrole.drop(columns=["Tarif d'une tonne de propane en citerne", "100 kWh PCI de propane en citerne",
                      "100 kWh PCS de propane",
                      "Un litre d'essence ordinaire",
                      "100 kWh PCI de propane", "100 kWh PCI de FOD au tarif C1"], inplace=True)  # doublons

electricite = pd.read_csv('data/prix_reglemente_electricite.csv', sep=';', decimal=',', parse_dates=['DATE_DEBUT'], infer_datetime_format=True)
electricite = electricite.set_index(['P_SOUSCRITE',"DATE_DEBUT"])
electricite.drop(columns=['DATE_FIN', 'PART_FIXE_HT', 'PART_FIXE_TTC', 'PART_VARIABLE_HT'], inplace=True)
electricite.dropna(inplace=True)
electricite = electricite.unstack().T.reset_index(0, drop=True)
electricite = electricite.rename(columns={i: f"1 kWh (contrat {i:.0f} kW)" for i in electricite.columns})
duration = pd.DatetimeIndex(electricite.index.values)
new_index = pd.DatetimeIndex(
    [f"{y}-{m:02d}-15" for y in range(duration[0].year, duration[-1].year + 1) for m in range(1, 13)])
electricite = electricite.reindex(np.concatenate([electricite.index.values, new_index.values]))
electricite.sort_index(inplace=True)
electricite = electricite.fillna(method='ffill')
electricite = electricite.loc[new_index]
electricite = electricite.reindex(bois.index)
electricite.drop(columns=["1 kWh (contrat 6 kW)", "1 kWh (contrat 12 kW)", "1 kWh (contrat 15 kW)"],
                 inplace=True)

energie = petrole.join(bois, how='outer').join(electricite, how='outer')
#energie = pd.concat([petrole, bois, electricite])  # cela devrait faire comme ci-dessus mais j'ai 3 lignes par index...
energie.to_pickle('data/energies.pkl')
