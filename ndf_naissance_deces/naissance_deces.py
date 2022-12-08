from dash import dcc
from dash import html
import dash
import json
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.subplots as sp
import plotly.express as px
from ndf_naissance_deces.transform_data import *

N_DEP_METROPOLE = 96
YEARS = ['2018', '2019', '2020']

class Naissance():
    '''
    SIZE: amount of death/birth per given reference

    daten = date (yyyy-mm-dd), SIZE, Id DepaNais - Amount of births (SIZE) per month (date) per deparment (DepNais)
    dated = date (yyyy-mm-dd), SIZE, Id DepaDec - Amount of deaths (SIZE) per month (date) per deparment (DepDec)
    
    depn = SIZE, VARIATION, Id DepNais - Amount of births and change in % in each french department
    depd = SIZE, VARIATION, Id DepNais - Amount of deaths and change in % in each french department

    agen = age, SIZEMEREN, SIZEPEREN - age of giving birth
    aged = age, SIZEMEREN, SIZEPEREN - age of death

    '''
    def __init__(self, application=None):
        with open('ndf_naissance_deces/data/departements.geojson') as f:
            self.dep_json = json.load(f)                                        # contours des départements
        self.dep = pd.read_pickle('ndf_naissance_deces/data/departements.pkl')  # num et nom des départements
        self.tudom = {}  # taille de la ville de la mère lors de la naissance
        self.daten = {}  # nombre de naissance par département et par mois
        self.dated = {}  # nombre de décès par département et par mois
        self.depn = {}
        self.depd = {}
        self.agen = {}  # âges des parents à la naissance de leur enfant
        self.aged = {}  # âge du décès pour les hommes et femmes

        # Load pkl and create dataframe
        for year in YEARS:
            self.tudom[year] = pd.read_pickle(f'ndf_naissance_deces/data/tudom{year[-2:]}.pkl')
            self.daten[year] = pd.read_pickle(f'ndf_naissance_deces/data/date_naissance{year[-2:]}.pkl')
            self.dated[year] = pd.read_pickle(f'ndf_naissance_deces/data/date_deces{year[-2:]}.pkl')
            self.depn[year] = self.daten[year].groupby('DEPNAIS').sum()[:N_DEP_METROPOLE]
            self.depd[year] = self.dated[year].groupby('DEPDEC').sum()[:N_DEP_METROPOLE]
            if year == YEARS[0]:
                self.depn[year]['VARIATION'] = np.nan
                self.depd[year]['VARIATION'] = np.nan
            else:
                self.depn[year]['VARIATION'] = self.depn[year]['SIZE'] /  self.depn[str(int(year)-1)]['SIZE'] - 1
                self.depd[year]['VARIATION'] = self.depd[year]['SIZE'] /  self.depd[str(int(year)-1)]['SIZE'] - 1
            self.agen[year] = pd.read_pickle(f'ndf_naissance_deces/data/age_naissance{year[-2:]}.pkl')
            self.aged[year] = pd.read_pickle(f'ndf_naissance_deces/data/age_deces{year[-2:]}.pkl')

        # Set info for maps
        self.tickval = {}
        for year in YEARS:
            zmax = max(self.depn[year]['SIZE'].max(), self.depd[year]['SIZE'].max())
            zmin = min(self.depn[year]['SIZE'].min(), self.depd[year]['SIZE'].min())
            self.tickval[year] = [zmin, 1000, 2000, 5000, 10000, 20000, zmax]

        self.color_sequence= px.colors.qualitative.D3  # cf https://plotly.com/python/discrete-color/

        self.date_axis = {}
        for year in YEARS:
            self.date_axis[year] = [pd.to_datetime(d) for d in sorted(set(self.daten[year].reset_index()['date']))]

        self.age_naissances_axis = list(range(17, 47))  # 17 -> 17 et moins, 46 -> 46 et plus
        self.tudom_axis = ['< 2k', '2k-5k', '5k-10k', '10k-20k', '20k-50k', '50k-100k', '100k-200k', '200k-2M', 'Aglo Paris']
        self.age_deces_axis = {}
        for year in YEARS:
            self.age_deces_axis[year] = list(sorted(set(self.aged[year].reset_index()['AGE'])))

        self.dep_map = {unplace_dep(pd.to_numeric(replace_dep(d['properties']['code']))): d['properties']['nom']
               for d in self.dep_json['features']}
        self.dep_idx_map = {d: i for i, d in enumerate(sorted(self.dep_map))}

        # Double map Naissance/Deces
        self.fig = sp.make_subplots(
            rows=1,
            cols=2,
            subplot_titles=('Nombre de naissances', 'Nombre de décès'),
            specs=[[{"type": "mapbox"}, {"type": "mapbox"}]],
        )

        # Enable multi-element selection
        self.fig.update_layout(
            clickmode='event+select',
            hovermode='closest',
            margin=dict(l=0, r=0, t=30, b=0),
        )

        #self.fig.add_trace(self.create_map_naissances(self.depn, self.depd, '2019'), row=1, col=1)
        #self.fig.add_trace(self.create_map_deces(self.depn, self.depd, '2019'), row=1, col=2)

        self.fig.update_mapboxes(
            style='carto-positron',
            center={"lat": 47.0353, "lon": 2.2928},
            zoom=4.42,
        )

        # main layout
        self.main_layout = html.Div(children=[
            html.H3(children='Naissances et décès en France'),
            html.Div([
                # Il faudrait afficher les variations tant sur les cartes que dans les courbes
#                dcc.RadioItems( id='val_or_var',
#                                options=[{'label': 'Valeurs', 'value': 'Valeurs'},
#                                         {'label': 'Variations', 'value': 'Variations'}],
#                                value='Valeurs',
#                                inline=True,
#                                labelStyle={'display': 'block','font-size': 15},
#                            ),
#                html.Label("en", style={'margin-left':'15px','margin-right':'15px'}),
                dcc.RadioItems( id='year',
                                options=[{'label': i, 'value': i} for i in YEARS],
                                value='2020',
                                inline=True,
                                labelStyle={'display': 'block','font-size': 15},
                            ),
            ], style={'display': 'flex'}),
            # Map div.
            html.Div([
                    dcc.Graph(
                        id='map',
                        figure=self.fig,
                        style={'width': '100%', 'display': 'inline-block'},
                    )
                ],
                style={
                    'display': 'flex',
                    'justifycontent': 'center',
                }
            ),

            # List of department name.
            html.Div([
                html.Plaintext(id='list_department',
                               style={
                                   'width': '50%',
                                   'whiteSpace': 'normal',
                                   'height': 'auto',
                                   'overflow-wrap': 'break-word',
                               }),
            ],
                style={
                    'display': 'flex',
                    'justifycontent': 'center',
                    'height': 'auto',
                }
            ),

            html.Br(),

            # Double graph with Naissance/Deces
            html.Div([
                dcc.Graph(id='courbe_naissances_deces',
                          style={'width': '95%', 'display': 'inline-block'}),
                html.Div([
                    html.Br(),
                    html.Br(),
                    html.Br(),
                    html.Br(),
                    dcc.Checklist(
                        id='wps-naissance-deces-1',
                        options=[{'label': i, 'value': i} for i in
                                 ['Naissance', 'Décès']],
                        value=['Naissance', 'Décès'],
                        labelStyle={'display': 'block', 'font-size': 12},
                    ),
                    html.Br(),
                    html.Div("Départements", style={'font-size': 12}),
                    dcc.RadioItems(
                        id='wps-uni-mg-1',
                        options=[{'label': i, 'value': i} for i in ['Chacun', 'Somme', ]],
                        value='Somme',
                        labelStyle={'display': 'block', 'font-size': 12},
                    ),
                ], style={'width': '10%', 'display': 'inline-block'}),
                # TODO ville_naissance
                dcc.Graph(id='ville_naissance',
                          style={'width': '95%', 'display': 'inline-block'}),
                html.Div([
                    html.Br(),
                    html.Br(),
                    html.Br(),
                    html.Br(),
                    html.Div("Départements", style={'font-size': 12}),
                    dcc.RadioItems(
                        id='wps-uni-mg-11',
                        options=[{'label': i, 'value': i} for i in ['Chacun', 'Somme', ]],
                        value='Somme',
                        labelStyle={'display': 'block', 'font-size': 12},
                    ),
                ], style={'width': '10%', 'display': 'inline-block'}),
            ], style={'display': 'flex',
                      'borderTop': 'thin lightgrey solid',
                      'justifyContent': 'center', }),
            html.Br(),

            html.Div([
                dcc.Graph(id='courbe_naissance',
                          style={'width': '90%', 'display':
                              'inline-block', }),
                html.Div([
                    html.Br(),
                    html.Br(),
                    html.Br(),
                    dcc.Checklist(
                        id='wps-hf-2',
                        options=[{'label': i, 'value': i} for i in ['Mère', 'Père', 'Moyenne M/P']],
                        value=['Mère', 'Père'],
                        labelStyle={'display': 'block', 'font-size': 12},
                    ),
                    html.Br(),
                    html.Div("Départements", style={'font-size': 12}),
                    dcc.RadioItems(
                        id='wps-uni-mg-2',
                        options=[{'label': i, 'value': i} for i in ['Chacun', 'Somme', ]],
                        value='Somme',
                        labelStyle={'display': 'block', 'font-size': 12},
                    ),
                ], style={'width': '10%', 'display': 'inline-block', }),

                dcc.Graph(id='courbe_deces',
                          style={'width': '90%',
                                 'display': 'inline-block', }),

                html.Div([
                    html.Br(),
                    html.Br(),
                    html.Br(),
                    dcc.Checklist(
                        id='wps-hf-3',
                        options=[{'label': i, 'value': i} for i in ['Femme', 'Homme', 'H + F', 'Moyenne H/F']],
                        value=['Femme', 'Homme'],
                        labelStyle={'display': 'block', 'font-size': 12},
                    ),
                    html.Br(),
                    html.Div("Départements", style={'font-size': 12}),
                    dcc.RadioItems(
                        id='wps-uni-mg-3',
                        options=[{'label': i, 'value': i} for i in
                                 ['Chacun', 'Somme', ]],
                        value='Somme',
                        labelStyle={'display': 'block', 'font-size': 12},
                    ),
                ], style={'width': '10%', 'display': 'inline-block'}),

            ], style={'display': 'flex',
                      'borderTop': 'thin lightgrey solid',
                      'borderBottom': 'thin lightgrey solid',
                      'justifyContent': 'center', }),
            html.Br(),
            dcc.Markdown("""
            Les cartes sont interactives. En passant la souris sur les départements vous avez une infobulle.
            De plus, en sélectionnant plusieurs départements (shift et clic), on peut avoir plus d'info sur ceux-ci à l'aide des graphiques.
            En utilisant les icônes en haut à droite, on peut agrandir une zone, déplacer la carte, réinitialiser avec un double clic et utiliser le lasso pour sélectionner plusieurs départements.

            #### Quelques remarques
               * Les grandes villes ont un important nombre de naissances et un plus faible nombre de décès.
                Les français finissent leur vie en régions plutôt que dans les grandes villes.
               * Cela se confirme en étudiant les départements, les zones à forte population ont plus de naissances que de décès.
                On observe le phénomène inverse dans les départements moins peuplés.
               * Il y a plus de naissances que de décès au niveau national.
               * On repère les hivers avec un nombre plus important de mort durant ces périodes.
               * Les hommes ont en moyenne des enfants 2 ans tard que les femmes,
               * Les femmes vivent plus longtemps que les hommes.
               * Les variations d'âge de décès varient beaucoup d'un département à un autre. Personne ne meure après 60 ans dans le Cantal, soit il n'y a pas de personne de plus de 60 ans, soit elles vont mourrir ailleurs. À Paris ou Lyon la courbe est décalée de 40 ans !
               * En 2020, à cause du Covid, le nombre de décès a considérablement augmenté, 20 % de morts en plus dans certains département. Globalement on note un éclaircissement de la carte des décès lorsqu'on passe de 2019 à 20202.

            #### Notes :
               * L'agglomération parisienne englobe Paris, la petite couronne (92, 93, 94) et une part significative de la grande couronne (288 communes sur 1 157), notamment les villes nouvelles.

            #### À propos

            * Sources : https://www.data.gouv.fr/fr/datasets/population/
            * (c) 2022 William Grolleau, Jeremy Croiset, Olivier Ricou
            """)
        ], style={
            'backgroundColor': 'white',
            'padding': '10px 50px 10px 50px',
        })

        if application:
            self.app = application
            # application should have its own layout and use self.main_layout as a page or in a component
        else:
            self.app = dash.Dash(__name__)
            self.app.layout = self.main_layout

        # Update subgraph when the selected department are updated.
        self.app.callback(
            dash.dependencies.Output('courbe_naissances_deces', 'figure'),
            dash.dependencies.Input('map', 'selectedData'),
            dash.dependencies.Input('wps-naissance-deces-1', 'value'),
            dash.dependencies.Input('wps-uni-mg-1', 'value'),
            dash.dependencies.Input('year', 'value'),
        )(self.courbe_naissances_deces)
        self.app.callback(
            dash.dependencies.Output('ville_naissance', 'figure'),
            dash.dependencies.Input('map', 'selectedData'),
            dash.dependencies.Input('wps-uni-mg-11', 'value'),
            dash.dependencies.Input('year', 'value'),
        )(self.ville_naissance)
        self.app.callback(
            dash.dependencies.Output('courbe_naissance', 'figure'),
            dash.dependencies.Input('map', 'selectedData'),
            dash.dependencies.Input('wps-uni-mg-2', 'value'),
            dash.dependencies.Input('wps-hf-2', 'value'),
            dash.dependencies.Input('year', 'value'),
        )(self.courbe_naissance)
        self.app.callback(
            dash.dependencies.Output('courbe_deces', 'figure'),
            dash.dependencies.Input('map', 'selectedData'),
            dash.dependencies.Input('wps-uni-mg-3', 'value'),
            dash.dependencies.Input('wps-hf-3', 'value'),
            dash.dependencies.Input('year', 'value'),
        )(self.courbe_deces)
        
        # Update list of department names upon map selection.
        self.app.callback(
            dash.dependencies.Output('list_department', 'children'),
            dash.dependencies.Input('map', 'selectedData'),
        )(self.list_dep)
        # Sync mapboxes layout and selection.
        self.app.callback(
            dash.dependencies.Output('map', 'figure'),
            dash.dependencies.Input('map', 'relayoutData'),
            dash.dependencies.Input('map', 'selectedData'),
            dash.dependencies.Input('year', 'value'),
        )(self.map_sync)
        self.app.callback(
            dash.dependencies.Output('wps-uni-mg-11', 'options'),
            dash.dependencies.Input('map', 'selectedData'),
        )(self.update_thing)
        self.app.callback(
            dash.dependencies.Output('wps-uni-mg-2', 'options'),
            dash.dependencies.Input('map', 'selectedData'),
        )(self.update_thing)
        self.app.callback(
            dash.dependencies.Output('wps-uni-mg-3', 'options'),
            dash.dependencies.Input('map', 'selectedData'),
        )(self.update_thing)
        self.app.callback(
            dash.dependencies.Output('wps-uni-mg-1', 'options'),
            dash.dependencies.Input('map', 'selectedData'),
        )(self.update_thing)
        self.app.callback(
            dash.dependencies.Output('wps-uni-mg-1', 'value'),
            dash.dependencies.Input('wps-uni-mg-1', 'value'),
            dash.dependencies.Input('map', 'selectedData'),
        )(self.update_things2)
        self.app.callback(
            dash.dependencies.Output('wps-uni-mg-11', 'value'),
            dash.dependencies.Input('wps-uni-mg-11', 'value'),
            dash.dependencies.Input('map', 'selectedData'),
        )(self.update_things2)
        self.app.callback(
            dash.dependencies.Output('wps-uni-mg-2', 'value'),
            dash.dependencies.Input('wps-uni-mg-2', 'value'),
            dash.dependencies.Input('map', 'selectedData'),
        )(self.update_things2)
        self.app.callback(
            dash.dependencies.Output('wps-uni-mg-3', 'value'),
            dash.dependencies.Input('wps-uni-mg-3', 'value'),
            dash.dependencies.Input('map', 'selectedData'),
        )(self.update_things2)

    def get_mapbox_layout_params(self, relayout_data):
        """Get the layout data from any mapbox in the figure.

        :param relayout_data: Update relayout of the map
        :return: dict of the relayout data sanitized.
        """
        keys = ['center', 'zoom', 'bearing', 'pitch']

        params = dict()
        for data_key in relayout_data.keys():
            params.update({ k: relayout_data[data_key] for k in keys if k in data_key })

        return params

    def map_sync(self, relayout_data, selected_data, year):
        """Update the layout and selection of other maps.

        :param relayout_data: layout of the updated map.
        :param selected_data: select data of the updated map.
        :return: New figure with all maps synced.
        """
        deps = self.get_selected_department(selected_data)
        depn = self.depn[year]
        depd = self.depd[year]
        self.fig = {}
        self.fig = sp.make_subplots(
            rows=1,
            cols=2,
            subplot_titles=('Nombre de naissances', 'Nombre de décès'),
            specs=[[{"type": "mapbox"}, {"type": "mapbox"}]],
        )

        # Enable multi-element selection
        self.fig.update_layout(
            clickmode='event+select',
            hovermode='closest',
            margin=dict(l=0, r=0, t=30, b=0),
        )

        self.fig.add_trace(self.create_map_naissances(depn, depd, year), row=1, col=1)
        self.fig.add_trace(self.create_map_deces(depn, depd, year), row=1, col=2)

        self.fig.update_mapboxes(
            style='carto-positron',
            center={"lat": 47.0353, "lon": 2.2928},
            zoom=4.42,
        )

        # upate selected elements to reflect on both maps
        self.fig.update_traces(
            selectedpoints=[self.dep_idx_map[d] for d in deps])

        if relayout_data is not None:
            params = self.get_mapbox_layout_params(relayout_data)

            # update layout to reflect on both maps
            self.fig.update_mapboxes(params)

        return self.fig

    def list_dep(self, selected_data):
        """List the department selected, if all are selected return
        'Toute la France'

        :param selected_data: selected data on the map.
        :return: String of departments.
        """
        deps = self.get_selected_department(selected_data)

        if len(deps) == N_DEP_METROPOLE:
            return 'Sélection : toute la France'
        else:
            return 'Sélection : ' + ', '.join([self.dep_map[d] for d in deps])

    def create_map_naissances(self, depn, depd, year):
        """Setup `Naissances` figure.

        :return: new figure
        """
        customdata=np.stack((self.dep['NAME'], depn['SIZE'], depn['VARIATION'],
                             depd['SIZE'],depd['VARIATION']),
                             axis=1)
        #hovertemplate="<b>Departement : %{customdata[1]}</b><br><br>" + "Nom : %{customdata[0]}<br>" + "Naissance : %{customdata[2]}<br>"
        if year == YEARS[0]:
            hovertemplate="<b>Dep. : %{customdata[0]}<br> Naissance : %{customdata[1]}<br> Décès : %{customdata[3]}<br>"
        else:
            hovertemplate="<b>Dep. : %{customdata[0]}<br> Naissance : %{customdata[1]} (%{customdata[2]:+0.2%})<br> Décès : %{customdata[3]} (%{customdata[4]:+.2%})<br>"
        return go.Choroplethmapbox(
            geojson=self.dep_json,
            name='',
            colorscale='Inferno',
            colorbar=dict(
                tickvals=[np.log10(i) for i in self.tickval[year]],
                ticktext=self.tickval[year],
                thickness=20,
                x=0.46,
            ),
            locations=self.depn[year].index,
            customdata=customdata,
            hovertemplate=hovertemplate,
            z=np.log10(depn['SIZE']),
            zmin=np.log10(self.tickval[year][0]),
            zmax=np.log10(self.tickval[year][-1]),
        )

    def create_map_deces(self, depn, depd, year):
        """Setup `Décès` figure.

        :return: new figure
        """
        customdata=np.stack((self.dep['NAME'], depn['SIZE'], depn['VARIATION'],
                             depd['SIZE'],depd['VARIATION']),
                             axis=1)
        if year == YEARS[0]:
            hovertemplate="<b>Dep. : %{customdata[0]}<br> Naissance : %{customdata[1]}<br> Décès : %{customdata[3]}<br>"
        else:
            hovertemplate="<b>Dep. : %{customdata[0]}<br> Naissance : %{customdata[1]} (%{customdata[2]:+0.2%})<br> Décès : %{customdata[3]} (%{customdata[4]:+.2%})<br>"
        return go.Choroplethmapbox(
            geojson=self.dep_json,
            name='',
            colorscale='Inferno',
            colorbar=dict(
                tickvals=[np.log10(i) for i in self.tickval[year]],
                ticktext=self.tickval[year],
                thickness=20,
                x=0.46,
            ),
            locations=self.depd[year].index,
            customdata=customdata,
            hovertemplate=hovertemplate,
            z=np.log10(depd['SIZE']),
            zmin=np.log10(self.tickval[year][0]),
            zmax=np.log10(self.tickval[year][-1]),
        )

    def get_selected_department(self, selected_data):
        """Get department id of all selected departments. By default, return
        every department in France.

        :param selected_data: selected department data.
        :return: List of department id.
        """
        if selected_data is None or selected_data['points'] == []:
            return list(self.dep_map.keys())
        return [p['location'] for p in selected_data['points']]

    def courbe_naissances_deces(self, selected_data, unit_mean, type, year):
        """Graph about size of Naissance and Deces of every department.

        :param selected_data: selected department.
        :param unit_mean: 'Naissance' or 'Deces'.
        :param type: 'Chacun' or 'Somme'.
        :return: figure of the graph.
        """
        deps = self.get_selected_department(selected_data)
        dfn = self.daten[year]
        dfd = self.dated[year]
        date_axis = self.date_axis[year]
        what = []
        if type == 'Chacun':
            if 'Naissance' in unit_mean:
                what += [(d, dfn.loc[d,'SIZE'], 'Naissance ' + self.dep_map[d], None) for d in deps]

            if 'Décès' in unit_mean:
                what += [(d, dfd.loc[d,'SIZE'], 'Décès ' + self.dep_map[d], 'dash') for d in deps]
        else:
            if 'Naissance' in unit_mean:
                data = dfn.loc[deps].groupby('date').sum()
                what += [(None, data['SIZE'], 'Naissance', None)]
            if 'Décès' in unit_mean:
                data = dfd.loc[deps].groupby('date').sum()
                what += [(None, data['SIZE'], 'Décès', 'dash')]

        return self.cts(date_axis, what,
                        "Nombre de naissances et décès par mois")
    
    def ville_naissance(self, selected_data, type, year):
        """Graph about size of Naissance and Deces of every department.

        :param selected_data: selected department.
        :param type: 'Chacun' or 'Somme'.
        :return: figure of the graph.
        """
        deps = self.get_selected_department(selected_data)
        tudom = self.tudom[year]
        what = []
        if type == 'Chacun':
            for d in deps:
                tud_dep = np.zeros(9)
                for city_size in tudom.loc[d].index:
                    tud_dep[city_size] = tudom.loc[(d,city_size), 'SIZE']
                what.append((d, tud_dep, self.dep_map[d], 'dot'))
        else:
            data = tudom.loc[deps].groupby('TUDOM').sum()
            what += [(None, data['SIZE'], 'Naissance', 'dot')]
        fig = self.cts(self.tudom_axis, what,
                        "Nombre de naissances en fonction de la taille de la ville de la mère")
        for sca in fig.data:
            if type == "Chacun":
                sca['mode'] = 'lines+markers'
            else:
                sca['mode'] = 'markers'
            sca['marker'] = {'size':20, 'symbol':'diamond-wide'}
        return fig

    def courbe_naissance(self, selected_data, unit_mean, type, year):
        """Graph about parents age when they have a child of every department.

        :param selected_data: selected department.
        :param unit_mean: 'Naissance' or 'Deces'.
        :param type: 'Homme, 'Femme, 'Chacun' or 'Somme'.
        :return: figure of the graph.
        """
        dep = self.get_selected_department(selected_data)
        agen = self.agen[year]
        what = []

        if unit_mean == 'Chacun':
            data = agen.loc[dep].groupby('AGE').max()  # pour l'annotation
            if 'Mère' in type:
                what += [(d, agen.loc[d,'SIZEMEREN'], 'Mère ' + self.dep_map[d], None) for d in dep]
            if 'Père' in type:
                what += [(d, agen.loc[d,'SIZEPEREN'], 'Père ' + self.dep_map[d], 'dash') for d in dep]
            if 'Moyenne M/P' in type:
                what += [(d, agen.loc[d,'MGMEREPEREN'], 'Moyenne H/F ' + self.dep_map[d], 'dashdot') for d in dep]

        else:
            data = agen.loc[dep].groupby('AGE').sum()
            if 'Mère' in type:
                what += [(None, data['SIZEMEREN'], 'Mère', None)]
            if 'Père' in type:
                what += [(None, data['SIZEPEREN'], 'Père', 'dash')]
            if 'Moyenne M/P' in type:
                what += [(None, data['MGMEREPEREN'], 'Moyenne M/P', 'dashdot')]

        fig = self.cts(self.age_naissances_axis, what,
                        "Nombre de naissances en fonction de l'âge des parents")
        fig.add_annotation(x=17, y=round(data['SIZEMEREN'][17]), xshift=10, yshift=10, text="17 et -", showarrow=False)
        fig.add_annotation(x=46, y=round(data['SIZEPEREN'][46]), xshift=-10, yshift=10, text="46 et +", showarrow=False)
        return fig

    def courbe_deces(self, selected_data, unit_mean, type, year):
        """Graph about age of death of male and female of every department.

        :param selected_data: selected department.
        :param unit_mean: 'Naissance' or 'Deces'.
        :param type: 'Homme, 'Femme, 'Chacun' or 'Somme'.
        :return: figure of the graph.
        """
        dep = self.get_selected_department(selected_data)
        what = []
        aged = self.aged[year]
        age_deces_axis = self.age_deces_axis[year]

        if unit_mean == 'Chacun':
            if 'Femme' in type:
                what += [(d, aged.loc[d,'SIZEMERED'], 'Femme ' + self.dep_map[d], None) for d in dep]
            if 'Homme' in type:
                what += [(d, aged.loc[d,'SIZEPERED'], 'Homme ' + self.dep_map[d], 'dash') for d in dep]
            if 'H + F' in type:
                what += [(d, aged.loc[d,'SIZEMERED'] + aged['SIZEPERED'], 'H + F ' + self.dep_map[d], 'dot') for d in dep]
            if 'Moyenne H/F' in type:
                what += [(d,  (aged.loc[d,'SIZEMERED'] + aged['SIZEPERED'])/2, 'Moyenne H/F ' + self.dep_map[d], 'dashdot') for d in dep]
        else:
            data = aged.loc[dep].groupby("AGE").sum()
            if 'Femme' in type:
                what += [(None, data['SIZEMERED'], 'Femmes', None)]
            if 'Homme' in type:
                what += [(None, data['SIZEPERED'], 'Hommes', 'dash')]
            if 'H + F' in type:
                what += [(None, data['SIZEMERED'] + data['SIZEPERED'], 'H + F', 'dot')]
            if 'Moyenne H/F' in type:
                what += [(None, (data['SIZEMERED'] + data['SIZEPERED'])/2, 'Moyenne H/F', 'dashdot')]

        return self.cts(age_deces_axis, what,
                        "Nombre de décès en fonction de l'âge")

    def cts(self, x_axis, what, title):
        scatters = []
        color_id = {}
        for dep, dataframe, name, dashed in what:
            line = {'color':self.color_sequence[0]}
            if dep != None:
                if dep not in color_id:
                    color_id[dep] = self.color_sequence[len(color_id) % len(self.color_sequence)]
                line['color'] = color_id[dep]
            line['dash'] = 'solid' if dashed is None else dashed
            scatters.append(go.Scatter(
                x=x_axis,
                y=dataframe,
                name=name,
                mode='lines',
                line = line,
            ))

        return go.Figure(
            data= scatters,
            layout= {
                'height': 300,
                'margin': {'l': 50, 'b': 30, 'r': 10, 't': 70},
                'yaxis': {'type': 'linear',
                          # 'font': {'size': 15}
                          },
                'title': {'text': title,
                          # 'font': {'size': 15}
                          },
                'legend': {'title': {'font': {'size': 5}},
                #    'font': {'size': 11}},
                },
                'xaxis': {'showgrid': False},
                #'font': {'size': 10},
            }
        )

    # pas propre !
    def update_thing(self, selected_data):
        deps = self.get_selected_department(selected_data)
        if len(deps) == 1:
            return [{"label": "Chacun", "value": "Chacun"},
            {"label": "Somme", "value": "Somme", "disabled": True},]
        else:
            return [{"label": "Chacun", "value": "Chacun"},
            {"label": "Somme", "value": "Somme"},]

    def update_things2(self, value, selected_data):
        deps = self.get_selected_department(selected_data)
        if len(deps) == 1:
            return 'Chacun'
        else:
            return value

if __name__ == '__main__':
    mpj = Naissance()
    mpj.app.run_server(debug=True, port=8051)
