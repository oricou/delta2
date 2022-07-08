import sys
import dash
import flask
from dash import dcc
from dash import html
import pandas as pd
import numpy as np
import plotly.graph_objs as go
import plotly.express as px
import json

class WorldPopulationStats():
    START = 'Start'
    STOP  = 'Stop'

    def __init__(self, application = None):
        self.dir = 'wfr_fertilite_revenus/'
        self.df = pd.read_pickle(self.dir + 'data/subWDIdata.pkl')
        self.df['Population'] /= 1E6
        self.continent_colors = {'Asie':'gold', 'Europe':'green', 'Afrique':'brown', 'Océanie':'red', 'Amerique':'navy'}
        self.years = sorted(set(self.df.index.values))
        self.max_incomes = self.df["Revenus"].max()
        self.max_childs = self.df["Nb d'enfants par femme"].max()
        self.max_pop = self.df["Population"].max()

        self.main_graph = px.scatter(self.df, x='Revenus', y="Nb d'enfants par femme", color="Continent",
                                        hover_name="Nom",
                                        hover_data = {'Année':True, 'Revenus':":.2f", "Nb d'enfants par femme":":.1f", \
                                                      'Continent':False, 'Population':':.2f'},
                                        color_discrete_map=self.continent_colors,
                                        # title="Évolution du taux de fertilité vs le revenu moyen par pays",
                                        labels={'Revenus':"Revenus nets par personne",
                                                "Population":"Population (millions)"},
                                        size = 'Population',  size_max=60,
                                        animation_frame=self.df["Année"], animation_group=self.df['Nom'],
                                        range_x=[10, self.df["Revenus"].max()], log_x = True,
                                        range_y=[0, int(self.df["Nb d'enfants par femme"].max()) + 1],
                                        # height = 600,  # j'aimerais mettre un % de la hauteur comme '40vh' 
                                       )

        self.main_layout = html.Div(children=[
            html.H3(children='Évolution du taux de fertilité vs le niveau moyen de revenu par pays'),

            html.Div('Déplacez la souris sur une bulle pour avoir les graphiques du pays en bas.'), 

            html.Div([ dcc.Graph(id='wps-main-graph', figure=self.main_graph), ], 
                     style={'width':'100%', }), 
            html.Br(),
            html.Div(id='wps-div-country'),

            html.Div([
                dcc.Graph(id='wps-income-time-series', 
                          style={'width':'33%', 'display':'inline-block'}),
                dcc.Graph(id='wps-fertility-time-series',
                          style={'width':'33%', 'display':'inline-block', 'padding-left': '0.5%'}),
                dcc.Graph(id='wps-pop-time-series',
                          style={'width':'33%', 'display':'inline-block', 'padding-left': '0.5%'}),
            ], style={ # 'display':'flex', 
                       'width':'98%',
                       #'textAlign':'center',
                       'borderTop': 'thin lightgrey solid',
                       'borderBottom': 'thin lightgrey solid',
                        # 'justifyContent':'center', 
                     }),
            html.Br(),
            dcc.Markdown("""

            La remarque la plus importante est que la majorité des pays ont vu leur taux de fertilité violemment chuter pour
            être autour de 2 enfants par femme en 2020. La relation entre les revenus et le taux de fertilité exsite toujours
            mais qu'aujourd'hui, la majorité des femmes n'ont que 2 enfants quelque soit leur revenus.
            Seule l'Afrique a encore des taux supérieurs taux qui ont aussi
            baissé avec le temps. Sachant qu'il faut 2,1 enfants par femme pour garder une population stable, on peut en
            conclure que le nombre d'humains sur terre devrait se stabiliser dans un avenir relativement proche
            (cf [cet article](https://www.futura-sciences.com/planete/actualites/population-mondiale-jusquou-va-grimper-population-mondiale-39860/) pour des projections chiffrées).

            #### Sources

            * Inspiration initiale : [conférence de Hans Rosling](https://www.ted.com/talks/hans_rosling_new_insights_on_poverty)
            * [Version Plotly](https://plotly.com/python/v3/gapminder-example/)
            * Données : [Banque mondiale](https://databank.worldbank.org/source/world-development-indicators)
            * (c) 2022 Olivier Ricou
            """),

        ], style={
                #'backgroundColor': 'rgb(240, 240, 240)',
                 'padding': '10px 50px 10px 50px',
                 }
        )
        
        if application:
            self.app = application
            # application should have its own layout and use self.main_layout as a page or in a component
        else:
            self.app = dash.Dash(__name__)
            self.app.layout = self.main_layout

        # I link callbacks here since @app decorator does not work inside a class
        # (somhow it is more clear to have here all interaction between functions and components)
        self.app.callback(
            dash.dependencies.Output('wps-div-country', 'children'),
            dash.dependencies.Input('wps-main-graph', 'hoverData'))(self.country_chosen)
        self.app.callback(
            dash.dependencies.Output('wps-income-time-series', 'figure'),
            [dash.dependencies.Input('wps-main-graph', 'hoverData')])(self.update_income_timeseries)
            # dash.dependencies.Input('wps-crossfilter-xaxis-type', 'value')])(self.update_income_timeseries)
        self.app.callback(
            dash.dependencies.Output('wps-fertility-time-series', 'figure'),
            [dash.dependencies.Input('wps-main-graph', 'hoverData')])(self.update_fertility_timeseries)
            #dash.dependencies.Input('wps-crossfilter-xaxis-type', 'value')])(self.update_fertility_timeseries)
        self.app.callback(
            dash.dependencies.Output('wps-pop-time-series', 'figure'),
            [dash.dependencies.Input('wps-main-graph', 'hoverData')])(self.update_pop_timeseries)
            #dash.dependencies.Input('wps-crossfilter-xaxis-type', 'value')])(self.update_pop_timeseries)

    # graph incomes vs years

    def create_time_series(self, country, what, axis_type='log', title='', maxy=None):
        return {
            'data': [go.Scatter(
                x = self.years,
                y = self.df[self.df["Nom"] == country][what],
                mode = 'lines+markers',
            )],
            'layout': {
                'height': 225,
                'margin': {'l': 50, 'b': 20, 'r': 10, 't': 20},
                'yaxis': {'title':title,
                          'range':[0, maxy],
                          'type': axis_type,
                          'exponentformat':'SI',
                         },
                'xaxis': {'showgrid': False}
            }
        }


    def get_country(self, hoverData):
        if hoverData == None:
            return 'France'
        return hoverData['points'][0]['hovertext']

    def country_chosen(self, hoverData):
        return self.get_country(hoverData)

    # graph incomes vs years
    def update_income_timeseries(self, hover_data):
        country = self.get_country(hover_data)
        return self.create_time_series(country, 'Revenus', 'log', 'PIB par personne (US $ 2020)', maxy = np.log10(self.max_incomes))

    # graph children vs years
    def update_fertility_timeseries(self, hover_data):
        country = self.get_country(hover_data) 
        return self.create_time_series(country, "Nb d'enfants par femme", 'linear', "Nombre d'enfants par femme", maxy=self.max_childs)

    # graph population vs years self.get_country(hover_data)
    def update_pop_timeseries(self, hover_data):
        country = self.get_country(hover_data) 
        return self.create_time_series(country, 'Population', 'linear', 'Population (millions)')

    def run(self, debug=False, port=8050):
        self.app.run_server(host="0.0.0.0", debug=debug, port=port)


if __name__ == '__main__':
    ws = WorldPopulationStats()
    ws.run(port=8055, debug=True)
