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
import json

class Mortality():


    def __init__(self, application = None):
        self.dir = 'mor_map/'
        self.geo = json.load(open(self.dir + 'data/countries.geojson'))
        self.df = pd.read_csv(self.dir + 'data/dataset.csv')
        self.second = pd.read_csv(self.dir + 'data/second.csv')

        self.main_layout = html.Div(children=[
            html.H3(children='The different causes of death in the world'),
            html.Div([dcc.Graph(figure=self.map(), id='map'), ], style={'width': '100%', }),

            html.Br(),
            html.Br(),

            dcc.Markdown("""Here is the graph that represents the 9 most important causes of death in France""", id='Title'),
            html.Div([dcc.Graph(figure=self.pie('France') , id='pie'), ], style={'width': '100%', }),
            
            html.Div([dcc.Graph(figure=self.line('France',0) , id='line1'), ], style={'width': '100%', }),
            html.Div([dcc.Graph(figure=self.line('France',1) , id='line2'), ], style={'width': '100%', }),
            html.Div([dcc.Graph(figure=self.line('France',2) , id='line3'), ], style={'width': '100%', }),
            html.Div([dcc.Graph(figure=self.line('France',3) , id='line4'), ], style={'width': '100%', }),
            html.Div([dcc.Graph(figure=self.line('France',4) , id='line5'), ], style={'width': '100%', }),
            html.Div([dcc.Graph(figure=self.line('France',5) , id='line6'), ], style={'width': '100%', }),
            html.Div([dcc.Graph(figure=self.line('France',6) , id='line7'), ], style={'width': '100%', }),
            html.Div([dcc.Graph(figure=self.line('France',7) , id='line8'), ], style={'width': '100%', }),
            html.Div([dcc.Graph(figure=self.line('France',8) , id='line9'), ], style={'width': '100%', }),

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
            [dash.dependencies.Output('Title', 'children'), dash.dependencies.Output('pie', 'figure'), dash.dependencies.Output('line1', 'figure'), dash.dependencies.Output('line2', 'figure'), dash.dependencies.Output('line3', 'figure'), dash.dependencies.Output('line4', 'figure'), dash.dependencies.Output('line5', 'figure'), dash.dependencies.Output('line6', 'figure'), dash.dependencies.Output('line7', 'figure'), dash.dependencies.Output('line8', 'figure'), dash.dependencies.Output('line9', 'figure')],
            dash.dependencies.Input('map', 'clickData')
        )(self.onClick)

    # Draw the map of the world
    def map(self):
        df = self.df
        geojson = self.geo

        fig = px.choropleth(df, locations="Code",
                    color="Total", # lifeExp is a column of gapminder
                    hover_name="Entity", # column to add to hover information
                    color_continuous_scale=px.colors.sequential.Plasma)

        fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})

        return fig


    def onClick(self, clickData):
        if clickData:
            return "Here is the graph that represents the 9 most important causes of death in " + clickData['points'][0]['hovertext'], self.pie(clickData['points'][0]['hovertext']),self.line(clickData['points'][0]['hovertext'],0),self.line(clickData['points'][0]['hovertext'],1),self.line(clickData['points'][0]['hovertext'],2),self.line(clickData['points'][0]['hovertext'],3),self.line(clickData['points'][0]['hovertext'],4),self.line(clickData['points'][0]['hovertext'],5),self.line(clickData['points'][0]['hovertext'],6),self.line(clickData['points'][0]['hovertext'],7),self.line(clickData['points'][0]['hovertext'],8)


        return 'Here is the graph that represents the 9 most important causes of death in France', self.pie('France'),self.line('France',0),self.line('France',1),self.line('France',2),self.line('France',3),self.line('France',4),self.line('France',5),self.line('France',6),self.line('France',7),self.line('France',8)

    # Draw the bar 9 upper charts without Entity, Code and Total of the selected country
    
    def pie(self, country):
        df = self.df
        df = df[df['Entity'] == country]
        df = df.drop(['Entity', 'Code', 'Total'], axis=1)
        df = df.transpose()
        df = df.reset_index()
        df.columns = ['Cause', 'Deaths']
        df = df.sort_values('Deaths', ascending=False)
        df = df.head(9)

        fig = px.bar(df, x='Cause', y='Deaths', color='Cause', color_discrete_sequence=px.colors.qualitative.Dark24)
        return fig

    # Draw the evolution in time of a cause of death in the selected country
    def line(self, country, n):
        df = self.df
        df = df[df['Entity'] == country]
        df = df.drop(['Entity', 'Code', 'Total'], axis=1)
        df = df.transpose()
        df = df.reset_index()
        df.columns = ['Cause', 'Deaths']
        df = df.sort_values('Deaths', ascending=False)
        df = df.head(9)

        # get the first cause of death
        cause = df['Cause'].iat[n]

        df = self.second
        df = df[df['Entity'] == country]
        df = df.drop(['Entity', 'Code'], axis=1)

        df.sort_values('Year', ascending=True, inplace=True)

        fig = px.line(df, x='Year', y=cause, title='Evolution of '+cause+'in '+country)
        

        return fig

if __name__ == '__main__':
    nrg = Mortality()
    nrg.app.run_server(debug=True, port=8062)
