import dash
from dash import dcc
from dash import html

# import projects as <trigramme>_lib
from nrj_energies import energies as nrj_lib
from wfr_fertilite_revenus import main as wfr_lib
from fdc_deces import deces as fdc_lib
from cd_naissance_deces import naissance_deces as nd_lib

# external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__,  title="Delta", suppress_callback_exceptions=True) # , external_stylesheets=external_stylesheets)
server = app.server
wfr = wfr_lib.WorldPopulationStats(app)
nrj = nrj_lib.Energies(app)
fdc = fdc_lib.Deces(app)
nd = nd_lib.Naissance(app)

main_layout = html.Div([
    html.Div(className = "row",
             children=[ 
                 dcc.Location(id='url', refresh=False),
                 html.Div(className="two columns",
                          children = [
                              html.Center(html.H2("Δelta δata")),
                              dcc.Link(html.Button("Prix d'énergies", style={'width':"100%"}), href='/nrj'),
                              html.Br(),
                              dcc.Link(html.Button('Fertilité vs revenus', style={'width':"100%"}), href='/wfr'),
                              html.Br(),
                              dcc.Link(html.Button('Décès journaliers', style={'width':"100%"}), href='/fdc'),
                              html.Br(),
                              dcc.Link(html.Button('Naissance et Décès 2019-2020', style={'width':"100%"}), href='/nd'),
                              html.Br(),
                              html.Br(),
                              html.Br(),
                              html.Center(html.A('Code source', href='https://github.com/oricou/delta2')),
                          ]),
                 html.Div(id='page_content', className="ten columns"),
            ]),
])


home_page = html.Div([
    html.Br(),
    html.Br(),
    html.Br(),
    html.Br(),
    dcc.Markdown("Choisissez le jeu de données dans l'index à gauche."),
])

to_be_done_page = html.Div([
    dcc.Markdown("404 -- Désolé cette page n'est pas disponible."),
])

app.layout = main_layout

# Update the index
@app.callback(dash.dependencies.Output('page_content', 'children'),
              [dash.dependencies.Input('url', 'pathname')])
def display_page(pathname):
    if pathname == '/nrj':
        return nrj.main_layout
    elif pathname == '/wfr':
        return wfr.main_layout
    elif pathname == '/fdc':
        return fdc.main_layout
    elif pathname == '/nd':
        return nd.main_layout
    else:
        return home_page


if __name__ == '__main__':
    app.run_server(debug=True)
