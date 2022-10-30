from dash import dcc
from dash import html
import dash
import json
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.subplots as sp
from cd_naissance_deces.transform_data import *

class Naissance():
    '''
    SIZE: amount of death/birth per given reference

    daten = date (yyyy-mm-dd), SIZE, Id DepaNais - Amount of births (SIZE) per month (date) per deparment (DepNais)
    dated = date (yyyy-mm-dd), SIZE, Id DepaDec - Amount of deaths (SIZE) per month (date) per deparment (DepDec)
    
    depn = SIZE, NAME, Id DepNais - Amount of births in each french depatment
    depd = SIZE, NAME, Id DepNais - Amount of deaths in each french depatment

    agen = age, SIZEMEREN, SIZEPEREN, SIZEMEREPEREN, MGMEREPEREN - age of giving birth
    aged = age, SIZEMEREN, SIZEPEREN, SIZEMEREPEREN, MGMEREPEREN - age of death

    zmax / zmin = 
    '''
    def __init__(self, application=None):
        with open('cd_naissance_deces/data/jcwg_departements.geojson') as f:
            self.dep = json.load(f)

        # Load pkl
        self.tudom = pd.read_pickle('cd_naissance_deces/data/1/jcwg_tudom19.pkl')
        self.tudom = self.tudom.set_index(['DEPNAIS', 'TUDOM'])
        self.daten = pd.read_pickle('cd_naissance_deces/data/1/jcwg_date_naissance19.pkl')
        self.dated = pd.read_pickle('cd_naissance_deces/data/1/jcwg_date_deces19.pkl')

        self.depn = pd.read_pickle('cd_naissance_deces/data/1/jcwg_department_naissance19.pkl')
        self.depd = pd.read_pickle('cd_naissance_deces/data/1/jcwg_department_deces19.pkl')

        self.agen = pd.read_pickle('cd_naissance_deces/data/1/jcwg_age_naissance19.pkl')
        self.aged = pd.read_pickle('cd_naissance_deces/data/1/jcwg_age_deces19.pkl')

        self.tudom_20 = pd.read_pickle('cd_naissance_deces/data/1/jcwg_tudom20.pkl')
        self.tudom_20 = self.tudom_20.set_index(['DEPNAIS', 'TUDOM'])
        self.daten_20 = pd.read_pickle('cd_naissance_deces/data/1/jcwg_date_naissance20.pkl')
        self.dated_20 = pd.read_pickle('cd_naissance_deces/data/1/jcwg_date_deces20.pkl')

        self.depn_20 = pd.read_pickle('cd_naissance_deces/data/1/jcwg_department_naissance20.pkl')
        self.depd_20 = pd.read_pickle('cd_naissance_deces/data/1/jcwg_department_deces20.pkl')

        self.agen_20 = pd.read_pickle('cd_naissance_deces/data/1/jcwg_age_naissance20.pkl')
        self.aged_20 = pd.read_pickle('cd_naissance_deces/data/1/jcwg_age_deces20.pkl')

        self.zmax = max(self.depn['SIZE'].max(), self.depd['SIZE'].max())
        self.zmin = min(self.depn['SIZE'].min(), self.depd['SIZE'].min())

        # Set info for graph
        self.tickval = [self.zmin, 1000, 2000, 5000, 10000, 20000, 30000,
                        self.zmax]
        #TODO change date_axis from 2019-01-15 to 2021-12-15
        self.date_axis = [pd.to_datetime(d) for d in sorted(set(
            self.daten.reset_index()['date']))]
        self.date_axis_20 = [pd.to_datetime(d) for d in sorted(set(
            self.daten_20.reset_index()['date']))]
        #TODO change age_naissance_axis from min to max
        self.age_naissances_axis = list(range(17, 46))
        self.tudom_axis = ['< 2k', '2k-5k', '5k-10k', '10k-20k', '20k-50k', '50k-100k', '100k-200k', '200k-2Mi', '> 2Mi']
        self.age_deces_axis = list(sorted(set(self.aged.reset_index()['AGE'])))
        self.age_deces_axis_20 = list(sorted(set(self.aged_20.reset_index()['AGE'])))
        self.dep_map = {unplace_dep(pd.to_numeric(replace_dep(d['properties']['code']))): d['properties']['nom']
               for d in self.dep['features']}
        self.dep_idx_map = {d: i for i, d in enumerate(sorted(self.dep_map))}

        # Double map Naissance/Deces
        self.fig = sp.make_subplots(
            rows=1,
            cols=2,
            subplot_titles=('Naissances', 'Décès'),
            specs=[[{"type": "mapbox"}, {"type": "mapbox"}]],
        )

        # Enable multi-element selection
        self.fig.update_layout(
            clickmode='event+select',
            hovermode='closest',
            margin=dict(l=0, r=0, t=30, b=0),
        )

        self.fig.add_trace(self.create_fig_naissances(), row=1, col=1)
        self.fig.add_trace(self.create_fig_deces(), row=1, col=2)

        self.fig.update_mapboxes(
            style='carto-positron',
            center={"lat": 47.0353, "lon": 2.2928},
            zoom=4.42,
        )

        # main layout
        self.main_layout = html.Div(children=[
            html.H3(children='Naissance et décès en France en 2019-2020'),
            html.Div([
                dcc.Markdown("""
                    Select here the year to preview :
                    """),
                dcc.RadioItems(
                            id='year',
                            options=[{'label': i, 'value': i} for i in
                                    ['2019', '2020']],
                            value='2019',
                            inline=True,
                            labelStyle={'display': 'block','font-size': 15},
                        )
        ]),
            
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
                dcc.Graph(id='size_france',
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
                    dcc.RadioItems(
                        id='wps-uni-mg-1',
                        options=[{'label': i, 'value': i} for i in
                                 ['Unitaire', 'Moyenne', ]],
                        value='Moyenne',
                        labelStyle={'display': 'block', 'font-size': 12},
                    ),
                ], style={'width': '10%', 'display': 'inline-block'}),
                # TODO size_tudom
                dcc.Graph(id='size_tudom',
                          style={'width': '95%', 'display': 'inline-block'}),
                html.Div([
                    html.Br(),
                    html.Br(),
                    html.Br(),
                    html.Br(),
                    dcc.RadioItems(
                        id='wps-uni-mg-11',
                        options=[{'label': i, 'value': i} for i in
                                 ['Unitaire', 'Moyenne', ]],
                        value='Moyenne',
                        labelStyle={'display': 'block', 'font-size': 12},
                    ),
                ], style={'width': '10%', 'display': 'inline-block'}),
            ], style={'display': 'flex',
                      'borderTop': 'thin lightgrey solid',
                      'justifyContent': 'center', }),
            html.Br(),

            html.Div([
                dcc.Graph(id='size_naissance',
                          style={'width': '90%', 'display':
                              'inline-block', }),
                html.Div([
                    html.Br(),
                    html.Br(),
                    html.Br(),
                    dcc.Checklist(
                        id='wps-hf-2',
                        options=[{'label': i, 'value': i} for i in
                                 ['Femme', 'Homme', 'Somme', 'Moyenne']],
                        value=['Femme', 'Homme'],
                        labelStyle={'display': 'block', 'font-size': 12},
                    ),
                    html.Br(),
                    dcc.RadioItems(
                        id='wps-uni-mg-2',
                        options=[{'label': i, 'value': i} for i in
                                 ['Unitaire', 'Moyenne', ]],
                        value='Moyenne',
                        labelStyle={'display': 'block', 'font-size': 12},
                    ),
                ], style={'width': '10%', 'display': 'inline-block', }),

                dcc.Graph(id='size_deces',
                          style={'width': '90%',
                                 'display': 'inline-block', }),

                html.Div([
                    html.Br(),
                    html.Br(),
                    html.Br(),
                    dcc.Checklist(
                        id='wps-hf-3',
                        options=[{'label': i, 'value': i} for i in
                                 ['Femme', 'Homme', 'Somme', 'Moyenne']],
                        value=['Femme', 'Homme'],
                        labelStyle={'display': 'block', 'font-size': 12},
                    ),
                    html.Br(),
                    dcc.RadioItems(
                        id='wps-uni-mg-3',
                        options=[{'label': i, 'value': i} for i in
                                 ['Unitaire', 'Moyenne', ]],
                        value='Moyenne',
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

            #### Informations intéressantes :
               * On remarque que les grosses villes ont un important nombre de naissances et un plus faible nombre de décès.
                Avec l'âge les gens finissent leur vie en régions plutôt que dans les grandes villes.
               * Cela se confirme en étudiant les départements unitairement, les zones à forte population ont plus de naissances que de décès.
                On observe le phénomène inverse dans les départements moins peuplés.
               * On observe une croissance démographique en France, il y a plus de naissances que de décès.
               * On repère les hivers avec un nombre plus important de mort durant ces périodes.
               * On observe moins de naissances de février à avril, pour un pic de naissances en juillet.
               * Les hommes ont en moyenne des enfants plus tard que les femmes.
               * Les femmes vivent plus longtemps que les hommes.

            #### À propos

            * Sources : https://www.data.gouv.fr/fr/datasets/population/
            * (c) 2022 William Grolleau, Jeremy Croiset.
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
            dash.dependencies.Output('size_france', 'figure'),
            dash.dependencies.Input('map', 'selectedData'),
            dash.dependencies.Input('wps-naissance-deces-1', 'value'),
            dash.dependencies.Input('wps-uni-mg-1', 'value'),
            dash.dependencies.Input('year', 'value'),
        )(self.size_france)
        self.app.callback(
            dash.dependencies.Output('size_tudom', 'figure'),
            dash.dependencies.Input('map', 'selectedData'),
            dash.dependencies.Input('wps-uni-mg-11', 'value'),
            dash.dependencies.Input('year', 'value'),
        )(self.size_tudom)
        self.app.callback(
            dash.dependencies.Output('size_naissance', 'figure'),
            dash.dependencies.Input('map', 'selectedData'),
            dash.dependencies.Input('wps-uni-mg-2', 'value'),
            dash.dependencies.Input('wps-hf-2', 'value'),
            dash.dependencies.Input('year', 'value'),
        )(self.size_naissance)
        self.app.callback(
            dash.dependencies.Output('size_deces', 'figure'),
            dash.dependencies.Input('map', 'selectedData'),
            dash.dependencies.Input('wps-uni-mg-3', 'value'),
            dash.dependencies.Input('wps-hf-3', 'value'),
            dash.dependencies.Input('year', 'value'),
        )(self.size_deces)

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
        )(self.map_sync)

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

    def map_sync(self, relayout_data, selected_data):
        """Update the layout and selection of other maps.

        :param relayout_data: layout of the updated map.
        :param selected_data: select data of the updated map.
        :return: New figure with all maps synced.
        """
        deps = self.get_department(selected_data)


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
        deps = self.get_department(selected_data)

        if len(deps) == 96:
            return 'Toute la France'
        else:
            return ', '.join([self.dep_map[d] for d in deps])

    def create_fig_naissances(self):
        """Setup `Naissances` figure.

        :return: new figure
        """
        return go.Choroplethmapbox(
            geojson=self.dep,
            name='',
            colorscale='Inferno',
            colorbar=dict(
                tickvals=[np.log10(i) for i in self.tickval],
                ticktext=self.tickval,
                thickness=20,
                x=0.46,
            ),
            locations=self.depn.index,
            customdata=np.stack((self.depn['NAME'], self.depn.index,
                                 self.depn['SIZE']),
                                axis=1),
            hovertemplate=
            "<b>Departement : %{customdata[1]}</b><br><br>" +
            "Nom : %{customdata[0]}<br>" +
            "Naissance : %{customdata[2]}<br>",
            z=np.log10(self.depn['SIZE']),
            zmin=np.log10(self.zmin),
            zmax=np.log10(self.zmax),
        )

    def create_fig_deces(self):
        """Setup `Décès` figure.

        :return: new figure
        """
        return go.Choroplethmapbox(
            geojson=self.dep,
            name='',
            colorscale='Inferno',
            colorbar=dict(
                tickvals=[np.log10(i) for i in self.tickval],
                ticktext=self.tickval,
                thickness=20,
                x=0.46,
            ),
            locations=self.depd.index,
            customdata=np.stack((self.depd['NAME'], self.depd.index,
                                 self.depd['SIZE']),
                                axis=1),
            hovertemplate=
            "<b>Departement : %{customdata[1]}</b><br><br>" +
            "Nom : %{customdata[0]}<br>" +
            "Décès : %{customdata[2]}<br>",
            z=np.log10(self.depd['SIZE']),
            zmin=np.log10(self.zmin),
            zmax=np.log10(self.zmax),
        )

    def get_department(self, selected_data):
        """Get department id of all selected departments. By default, return
        every department in France.

        :param selected_data: selected department data.
        :return: List of department id.
        """
        if selected_data is None or selected_data['points'] == []:
            return list(self.dep_map.keys())
        return [p['location'] for p in selected_data['points']]

    def size_france(self, selected_data, unit_mean, type, year):
        """Graph about size of Naissance and Deces of every department.

        :param selected_data: selected department.
        :param unit_mean: 'Naissance' or 'Deces'.
        :param type: 'Unitaire' or 'Moyenne'.
        :return: figure of the graph.
        """
        deps = self.get_department(selected_data)
        if year == '2020':
            dfn = self.daten_20
            dfd = self.dated_20
            date_axis = self.date_axis_20
        else:
            dfn = self.daten
            dfd = self.dated
            date_axis = self.date_axis

        what = []
        if type == 'Unitaire':
            if 'Naissance' in unit_mean:
                what += [(d, dfn, 'SIZE', 'Naissance ' +
                          self.dep_map[d])
                         for d in deps]

            if 'Décès' in unit_mean:
                what += [(d, self.dated, 'SIZE',
                          'Décès ' + self.dep_map[d])
                         for d in deps]
        else:
            if 'Naissance' in unit_mean:
                data = dfn.loc[deps].reset_index().groupby(
                    ['date']).sum()
                what += [(None, data, 'SIZE', 'Naissance cumulée')]
            if 'Décès' in unit_mean:
                data = dfd.loc[deps].reset_index().groupby(
                    ['date']).sum()
                what += [(None, data, 'SIZE', 'Décès cumulé')]

        return self.cts(date_axis, what,
                        "Nombre de naissance et décès par mois")
    
    def size_tudom(self, selected_data, type, year):
        """Graph about size of Naissance and Deces of every department.

        :param selected_data: selected department.
        :param type: 'Unitaire' or 'Moyenne'.
        :return: figure of the graph.
        """
        deps = self.get_department(selected_data)
        
        if year == '2020':
            tudom = self.tudom_20
        else:
            tudom = self.tudom
        what = []
        if type == 'Unitaire':
            what += [(d, tudom, 'SIZE', 'Naissance ' +
                        self.dep_map[d])
                        for d in deps]
        else:
            data = tudom.loc[deps].reset_index().groupby(
                ['TUDOM']).sum()
            what += [(None, data, 'SIZE', 'Naissance cumulée')]
        return self.cts(self.tudom_axis, what,
                        "Nombre de naissance en fonction de la taille de la ville")

    def size_naissance(self, selected_data, unit_mean, type, year):
        """Graph about parents age when they have a child of every department.

        :param selected_data: selected department.
        :param unit_mean: 'Naissance' or 'Deces'.
        :param type: 'Homme, 'Femme, 'Unitaire' or 'Moyenne'.
        :return: figure of the graph.
        """
        dep = self.get_department(selected_data)
        if year == '2020':
            agen = self.agen_20
        else:
            agen = self.agen
        what = []

        if unit_mean == 'Unitaire':
            if 'Femme' in type:
                what += [(d, agen, 'SIZEMEREN', 'Femme ' +
                          self.dep_map[d]) for d in dep]
            if 'Homme' in type:
                what += [(d, agen, 'SIZEPEREN', 'Homme ' +
                          self.dep_map[d]) for d in dep]
            if 'Somme' in type:
                what += [(d, agen, 'SIZEMEREPEREN', 'Somme H/F ' +
                          self.dep_map[d]) for d in dep]
            if 'Moyenne' in type:
                what += [(d, agen, 'MGMEREPEREN', 'Moyenne H/F ' +
                          self.dep_map[d]) for d in dep]

        else:
            data = agen.loc[dep].reset_index().groupby(['level_1']).sum()
            if 'Femme' in type:
                what += [(None, data, 'SIZEMEREN', 'Total femmes')]
            if 'Homme' in type:
                what += [(None, data, 'SIZEPEREN', 'Total hommes')]
            if 'Somme' in type:
                what += [(None, data, 'SIZEMEREPEREN', 'Total H/F')]
            if 'Moyenne' in type:
                what += [(None, data, 'MGMEREPEREN', 'Moyenne H/F')]

        return self.cts(self.age_naissances_axis, what,
                        "Nombre de naissance en fonction de l'age")

    def size_deces(self, selected_data, unit_mean, type, year):
        """Graph about age of death of male and female of every department.

        :param selected_data: selected department.
        :param unit_mean: 'Naissance' or 'Deces'.
        :param type: 'Homme, 'Femme, 'Unitaire' or 'Moyenne'.
        :return: figure of the graph.
        """
        dep = self.get_department(selected_data)
        what = []
        if year == '2020':
            aged = self.aged_20
        else:
            aged = self.aged

        if unit_mean == 'Unitaire':
            if 'Femme' in type:
                what += [(d, aged, 'SIZEMERED', 'Femme ' +
                          self.dep_map[d]) for d in dep]
            if 'Homme' in type:
                what += [(d, aged, 'SIZEPERED', 'Homme ' +
                          self.dep_map[d]) for d in dep]
            if 'Somme' in type:
                what += [(d, aged, 'SIZEMEREPERED', 'Somme H/F ' +
                          self.dep_map[d]) for d in dep]
            if 'Moyenne' in type:
                what += [(d, aged, 'MGMEREPERED', 'Moyenne H/F ' +
                          self.dep_map[d]) for d in dep]
        else:
            data = aged.loc[dep].reset_index().groupby(['AGE']).sum()
            if 'Femme' in type:
                what += [(None, data, 'SIZEMERED', 'Total femmes')]
            if 'Homme' in type:
                what += [(None, data, 'SIZEPERED', 'Total hommes')]
            if 'Somme' in type:
                what += [(None, data, 'SIZEMEREPERED', 'Total H/F')]
            if 'Moyenne' in type:
                what += [(None, data, 'MGMEREPERED', 'Moyenne H/F')]

        return self.cts(self.age_deces_axis, what,
                        "Nombre de décès en fonction de l'age")

    def cts(self, x_axis, what, title):
        scatters = []
        for dep, dataframe, w, name in what:
            scatters.append(go.Scatter(
                x=x_axis,
                y=dataframe[w] if dep is None else dataframe.loc[dep][w],
                name=name,
                mode='lines+markers',
            ))

        return {
            'data': scatters,
            'layout': {
                'height': 300,
                'margin': {'l': 50, 'b': 30, 'r': 10, 't': 70},
                'yaxis': {'type': 'linear',
                          'font': {'size': 15}},
                'title': {'text': title,
                          'font': {'size': 15}},
                'legend': {
                    'title': {'font': {'size': 5}},
                    'font': {'size': 11}},
                'xaxis': {'showgrid': False},
                'font': {'size': 10},
            }
        }


if __name__ == '__main__':
    mpj = Naissance()
    mpj.app.run_server(debug=True, port=8051)
