from dash import Dash, html, Input, Output, dcc, callback
import dash_ag_grid as dag
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import numpy as np
import pandas as pd
import ast
# from plotly.subplots import make_subplots

# get data
skill_trends = pd.read_csv('data/certprep-skill-trends.csv')
certprep_skills = pd.read_csv('data/certprep-skus-extracted-skills-and-demand.csv')
certprep_data = pd.read_csv('data/cert-prep-catalog-extracted-skills-agg-clean.csv')
certprep_skill_demand = pd.read_csv('data/certprep-skill-demand.csv')
skills = certprep_skills[['id', 'name', 'description']].drop_duplicates()

# https://dashaggrid.pythonanywhere.com/components/markdown
rain =  "![alt text: rain](https://www.ag-grid.com/example-assets/weather/rain.png)"
sun = "![alt text: sun](https://www.ag-grid.com/example-assets/weather/sun.png)"

# make a KPI card
def mk_card(header, id, value, height='100%'):
    return html.Div([
            dbc.Card(
                dbc.CardBody([
                    html.Div([
                        html.H2(header),
                        html.H3(str(value), id=id),
                    ], 
                        style={'textAlign': 'center', 'height': height},
                        className="div-card-body"
                    ) 
                ])
            ),
        ])


def skill_trend_plot(skill_ids):
    # get all skill trends associated with a course display name

     # Create figure
    fig = go.Figure()

    if skill_ids is not None:

        if not isinstance(skill_ids, list):
            skill_ids = [skill_ids]

        # skill_ids = certprep_skills.loc[certprep_skills.name.isin(skill_name), "id"].tolist()
        trends = skill_trends.loc[skill_trends.skill_id.isin(skill_ids), ["skill_id", "skill_trends"]]

        for skill_id, trend in trends.to_numpy():
            # format data
            data = pd.DataFrame(ast.literal_eval(trend))
            if len(data) != 0:
                data['date'] = pd.to_datetime(data['date'])

                fig.add_trace(
                    go.Scatter(
                        showlegend=True,
                        name=skills.loc[skills.id == skill_id, "name"].iloc[0][:12],
                        x=list(data.date), 
                        y=list(data.count_per_month)
                    )
                )

            fig.update_layout(
                # template="plotly_dark", 
                title="Skill Monthly Demand",
                xaxis_title="Date",
                yaxis_title="Jobs with Skill",
            )

    return fig

# Initialize the app
app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# rain = f"![image alt text]({app.get_asset_url('rain.png')})"

# application layout
app.layout = html.Div([
        html.Div(
        className="app-header",
        children=[
            html.Div('Achieve+ Local Trend Service', className="app-header--title")
        ]
    ),
    html.P("Powered by Faethm™", className="header-text"),
    html.I(
        "Select a CertPrep Course",
        style={
            "color": 'rgb(180, 180, 180)'
        }
    ),
    html.Br(),
    dcc.Dropdown(np.sort(certprep_data.display_name.unique()).tolist(), id='course-dropdown'),
    html.Br(),
    # dcc.Dropdown(np.sort(certprep_skills.name.unique()).tolist(), id='skill-dropdown'),
    # make cards
    # dbc.Container(
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    dbc.Row([
                        mk_card(
                            header="CertPrep Course", 
                            id="course-name", 
                            value="Hey"
                        )
                    ]),
                    dbc.Row([
                        mk_card(
                            header="Skills", 
                            id="no-skills", 
                            value="Meow"
                        )
                    ]),
                    dbc.Row([
                        mk_card(
                            header="In-Demand Skills", 
                            id="no-in-demend-skills", 
                            value="Meow"
                        )
                    ]),
                    dbc.Row([
                        mk_card(
                            header="Avg. YoY Skill Demand", 
                            id="avg-yoy-skill-demand", 
                            value="Meow"
                        )
                    ])
                ], id='col-left-panel', width=5),
                dbc.Col([
                    dbc.Row([
                       dcc.Graph(id='skill-trend-plot')
                    ]),
                     dbc.Row([
                        mk_card(
                            header="Skill Detail", 
                            id="skill-details", 
                            value=""
                        )
                    ]),
                ], id='col-skill-trend-plot', width=5),
                dbc.Col([
                    dbc.Row([
                        # multiple dropdown https://dash.plotly.com/dash-ag-grid/row-selection-multiple
                        dag.AgGrid(
                            id="selection-multiple-skills",
                            columnDefs=[
                                {"field": "name",}, 
                                {"field": "in_demand", "minWidth": 50,},
                                {"field": "YoY (%)", "minWidth": 50,},
                            ],
                            # rowData=certprep_skills.to_dict("records"),
                            columnSize="sizeToFit",
                            defaultColDef={"resizable": True, "sortable": True, "filter": True, "minWidth": 125,},
                            dashGridOptions={"rowSelection":"multiple"},
                            style={'height': 480}
                        )
                    ]),
                ], id='col-skill-selector', width=5)
            ])
        ], id='first-card-body'),
    # ),
    html.Div([
        html.P("Contact: GPDCPDA@grp.pearson.com", className="footer-paragraph"),
        html.P("Data Analyst: Maria Lentini", className="footer-paragraph")     
    ], id="footer")
])


@callback(
    Output(component_id='course-name', component_property='children'),
    Input(component_id='course-dropdown', component_property='value')
)
def update_dash(course_name):
    return course_name
        
@callback(
    [Output(component_id='selection-multiple-skills', component_property='rowData'),
    Output(component_id='no-skills', component_property='children'),
    Output(component_id='no-in-demend-skills', component_property='children'),
    Output(component_id='avg-yoy-skill-demand', component_property='children')],
    [Input(component_id='course-dropdown', component_property='value')]
)
def update_skills_multi_selector(course_name):
    if course_name:
        sku = certprep_data.loc[
            certprep_data.display_name ==  course_name,
            'sku'
        ].iloc[0]
        # filter data using sku associated wit course name
        data = certprep_skills.loc[certprep_skills.sku == sku, :]
        # get and formand avg yoy demand
        avg_yoy_demand = data.skill_changes_1y.mean()
        # format with '+' or '-' depending on sign
        if avg_yoy_demand >= 0:
            avg_yoy_demand = '+' + str(round(100 * avg_yoy_demand, 1)) + '%'
        else:
            avg_yoy_demand = str(round(100 * avg_yoy_demand, 1)) + '%'
        
        data['YoY (%)'] = (100 * data['skill_changes_1y']).round(1).astype(str)
        # # add images to in-demand column
        # xs = data.to_dict('records')
        # for x in xs:
        #     x["In-Demand"] = f"{rain}"
        # return skill sclector table and number of skills
        return data.to_dict("records"), data.id.nunique(), data.in_demand.sum(), avg_yoy_demand

@callback(
    [Output(component_id='skill-trend-plot', component_property='figure'),
    Output(component_id='skill-details', component_property='children')],
    Input("selection-multiple-skills", "selectedRows"),
)
def selected(selected):
    if selected:
        selected_skills = [s["name"] for s in selected]

        data = skills[skills.name.isin(selected_skills)]
        # data = certprep_skills.loc[certprep_skills.name.isin(selected_skills), :]

        return skill_trend_plot(data.id.tolist()), '. '.join(data.description.tolist())



# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)