import dash
import json
import numpy as np
import plotly.graph_objs as go
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

pts = np.loadtxt(np.DataSource().open('https://raw.githubusercontent.com/plotly/datasets/master/mesh_dataset.txt'))
x, y, z = pts.T

app.layout = html.Div([
   dcc.Graph(
        id='hover-test',
        figure = {
            'data':[
                go.Mesh3d(
                        x = x,
                        y = y,
                        z = z,
                        # text = ['a', 'b', 'c', 'd'],
                        customdata = ['aa'],
                        name = 'Trace 1',
                        # mode = 'markers',
                        # marker = {'size': 12}
                    ),
                go.Mesh3d(
                    x=x,
                    y=y,
                    z=z+10,
                    # text = ['a', 'b', 'c', 'd'],
                    customdata=['cc'] * len(z),
                    name='Trace 2',
                    # mode = 'markers',
                    # marker = {'size': 12}
                )
                ]
            }
        ),
    html.Div([
        html.Pre(
            id = 'hover-data',
        )
    ])
])

@app.callback(Output('hover-data', 'children'),
              [Input('hover-test', 'hoverData')])

def dis_play_hover_data(hover_data):
    return json.dumps(hover_data, indent=2)

if __name__ == '__main__':
    app.run_server(debug=True)
