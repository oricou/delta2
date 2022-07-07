import sys
import dash
import flask
from dash import dcc
from dash import html
import pandas as pd
import numpy as np
import plotly.graph_objs as go
import plotly.express as px
import dateutil as du


class Energies():
    mois = {'janv': 1, 'févr': 2, 'mars': 3, 'avr': 4, 'mai': 5, 'juin': 6, 'juil': 7, 'août': 8, 'sept': 9, 'oct': 10,
            'nov': 11, 'déc': 12}

    quoi = {"Prix d'une tonne de propane": [1000, 'Propane','cyan'], "Bouteille de butane de 13 kg": [13, 'Butane','blue'],
            "100 litres de FOD au tarif C1": [100, 'Fioul','black'], 
            "Un litre de super carburant ARS": [1, 'Essence','tomato'], "Un litre de super sans plomb 95": [1, 'Essence','orange'],
            "Un litre de super sans plomb 98": [1, 'Essence','red'], "Un litre de gazole": [1, 'Gazole','gray'],
            "Un litre de GPLc": [1, 'GPL','lightgreen'], "1 kWh (contrat 3 kW)": [1, 'Electricité','pink'],
            "1 kWh (contrat 9 kW)": [1, 'Electricité','magenta'],
            "Une tonne de granulés de bois en vrac": [1000, 'Bois', 'brown'],
            "100 kWh PCI de bois en vrac": [100, 'Electricité','tan']}

    densité = {'Essence': 0.75, 'Gazole': 0.85, 'Fioul': 0.85, 'GPL': 0.55}  # kg / l

    # https://fr.wikipedia.org/wiki/Pouvoir_calorifique
    calor = {'Essence': 47.3, 'Gazole': 44.8, 'Fioul': 42.6, 'Propane': 50.35, 'Butane': 49.51, 'GPL': 46, 'Bois': 15,
             'Charbon': 20,
             'Electricité': 3.6}  # en MJ / kg sauf électicité en MJ / kWh

    def __init__(self, application = None):
        self.dir = 'nrj_energies/'
        self.energie = pd.read_pickle(self.dir + 'data/energies.pkl')
        self.petrole = self.energie[ list(self.quoi.keys())[:8] ] # les comburants 
        self.years = np.arange(self.petrole.index.min().year, self.petrole.index.max().year + 1)

        self.main_layout = html.Div(children=[
            html.H3(children='Évolution des prix de différentes énergies en France'),
            html.Div([dcc.Graph(id='nrg-main-graph'), ], style={'width': '100%', }),
            html.Div([
                html.Div([html.Div('Prix'),
                          dcc.RadioItems(
                              id='nrg-price-type',
                              options=[{'label': 'Absolu', 'value': 0},
                                       {'label': 'Équivalent J', 'value': 1},
                                       {'label': 'Relatif : 1 en ', 'value': 2}],
                              value=1,
                              labelStyle={'display': 'block'},
                          )
                          ], style={'width': '9em'}),
                html.Div([html.Div('Mois ref.'),
                          dcc.Dropdown(
                              id='nrg-which-month',
                              options=[{'label': i, 'value': Energies.mois[i]} for i in Energies.mois],
                              value=1,
                              disabled=True,
                          ),
                          ], style={'width': '6em', 'padding': '2em 0px 0px 0px'}),  # bas D haut G
                html.Div([html.Div('Annee ref.'),
                          dcc.Dropdown(
                              id='nrg-which-year',
                              options=[{'label': i, 'value': i} for i in self.years],
                              value=2000,
                              disabled=True,
                          ),
                          ], style={'width': '6em', 'padding': '2em 0px 0px 0px'}),
                html.Div(style={'width': '2em'}),
                html.Div([html.Div('Échelle en y'),
                          dcc.RadioItems(
                              id='nrg-xaxis-type',
                              options=[{'label': i, 'value': i} for i in ['Linéaire', 'Logarithmique']],
                              value='Logarithmique',
                              labelStyle={'display': 'block'},
                          )
                          ], style={'width': '15em', 'margin': "0px 0px 0px 40px"}),  # bas D haut G
            ], style={
                'padding': '10px 50px',
                'display': 'flex',
                'flexDirection': 'row',
                'justifyContent': 'flex-start',
            }),
            html.Br(),
            dcc.Markdown("""
                Le graphique est interactif. En passant la souris sur les courbes vous avez une infobulle. 
                En cliquant ou double-cliquant sur les lignes de la légende, vous choisissez les courbes à afficher.
                
                Notes :
                   * FOD est le fioul domestique.
                   * Pour les prix relatifs, seules les énergies fossiles sont prises en compte par manque de données pour les autres.

                #### À propos

                * Sources : 
                   * [base Pégase](http://developpement-durable.bsocom.fr/Statistiques/) du ministère du développement durable
                   * [tarifs réglementés de l'électricité](https://www.data.gouv.fr/en/datasets/historique-des-tarifs-reglementes-de-vente-delectricite-pour-les-consommateurs-residentiels/) sur data.gouv.fr
                * (c) 2022 Olivier Ricou
                """)
        ], style={
            'backgroundColor': 'white',
            'padding': '10px 50px 10px 50px',
        }
        )

        if application:
            self.app = application
            # application should have its own layout and use self.main_layout as a page or in a component
        else:
            self.app = dash.Dash(__name__)
            self.app.layout = self.main_layout

        self.app.callback(
            dash.dependencies.Output('nrg-main-graph', 'figure'),
            [dash.dependencies.Input('nrg-price-type', 'value'),
             dash.dependencies.Input('nrg-which-month', 'value'),
             dash.dependencies.Input('nrg-which-year', 'value'),
             dash.dependencies.Input('nrg-xaxis-type', 'value')])(self.update_graph)
        self.app.callback(
            [dash.dependencies.Output('nrg-which-month', 'disabled'),
             dash.dependencies.Output('nrg-which-year', 'disabled')],
            dash.dependencies.Input('nrg-price-type', 'value'))(self.disable_month_year)

    def update_graph(self, price_type, month, year, xaxis_type):
        if price_type == 0 or month == None or year == None:
            df = self.energie
        elif price_type == 1:
            df = self.energie.copy()
            for c in df.columns:
                alias = Energies.quoi[c][1]
                try:
                    df[c] = df[c] / (Energies.quoi[c][0] * Energies.densité[alias] * Energies.calor[alias])
                except:  # l'unité est déjà en kg et donc densité n'existe pas
                    df[c] = df[c] / (Energies.quoi[c][0] * Energies.calor[alias])
        else:
            df = self.petrole.copy()
            df.loc[f"{year}-{month}-15"]
            cols = df.loc[f"{year}-{month}-15"].dropna().index
            df = df[cols] / df.loc[f"{year}-{month}-15", cols]
        fig = px.line(df[df.columns[0]], template='plotly_white', color_discrete_sequence=[self.quoi[df.columns[0]][2]])
        for i,c in enumerate(df.columns[1:]):
            fig.add_scatter(x=df.index, y=df[c], mode='lines', name=c, text=c, hoverinfo='x+y+text',
                            marker_color=self.quoi[c][2])
        ytitle = ['Prix en €', 'Prix en € pour 1 mégajoule', 'Prix relative (sans unité)']
        fig.update_layout(
            # title = 'Évolution des prix de différentes énergies',
            yaxis=dict(title=ytitle[price_type],
                       type='linear' if xaxis_type == 'Linéaire' else 'log', ),
            height=450,
            hovermode='closest',
            legend={'title': 'Énergie'},
        )
        return fig

    def disable_month_year(self, price_type):
        if price_type == 2:
            return False, False
        else:
            return True, True


if __name__ == '__main__':
    nrg = Energies()
    nrg.app.run_server(debug=True, port=8052)
