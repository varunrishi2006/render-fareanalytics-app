import dash
import json
from dash import dcc, html, Input, Output, State, dash_table
import pandas as pd
from pandas.api.types import CategoricalDtype
import dash_bootstrap_components as dbc
import datetime
from datetime import datetime as dt
import plotly.graph_objects as go
import plotly.express as px

app = dash.Dash(
    __name__,
    meta_tags=[{"name": "viewport",
                "content": "width=device-width, initial-scale=1"}],
)
server = app.server

app.title = "Fare Insights Dashboard"

app.config['suppress_callback_exceptions'] = True

df_fare_comp = pd.read_csv(
    "https://raw.githubusercontent.com/varunrishi2006/render-fareanalytics-app/main/fare_comp.csv")
# df_fare_freq = pd.read_excel('C:/Users/varun/Desktop/Personal/SimplyOR/Sample_Data.xlsx', sheet_name='View5')

category_order = CategoricalDtype([
    '0-7',
    '8-15',
    '16-30',
    '31-60',
    '61-90',
    '91-120',
    '>120'
], ordered=True)

forecast_order = CategoricalDtype([
    '0-70',
    '71-80',
    '81-90',
    '91-100',
    '101-110',
    '>110'
], ordered=True)

fare_delta_order = CategoricalDtype([
    '(>10)',
    '(6-10)',
    '(3-5)',
    '(0-2)',
    '0-2',
    '3-5',
    '6-10',
    '>10'
], ordered=True)

departure_order = CategoricalDtype([
    'Load Critical Departures',
    'Competitive Departures',
    'Yield Critical Departures',
], ordered=True)

fare_category_order = CategoricalDtype([
    'Down-selling',
    'Competitively Priced',
    'Up-selling',
], ordered=True)

df_fare_comp['Departure Time'] = pd.to_datetime(df_fare_comp['Departure Time'], format='%d-%m-%Y')
df_fare_comp['Forecast'] = round(df_fare_comp['Forecast'] * 100)
init_date = min(df_fare_comp['Departure Time']).date()
last_date = dt(2023, 9, 10),

df_fare_comp.loc[df_fare_comp['Forecast'].between(0, 70, 'both'), 'Forecast Range'] = '0-70'
df_fare_comp.loc[df_fare_comp['Forecast'].between(71, 80, 'both'), 'Forecast Range'] = '71-80'
df_fare_comp.loc[df_fare_comp['Forecast'].between(81, 90, 'both'), 'Forecast Range'] = '81-90'
df_fare_comp.loc[df_fare_comp['Forecast'].between(91, 100, 'both'), 'Forecast Range'] = '91-100'
df_fare_comp.loc[df_fare_comp['Forecast'].between(101, 110, 'both'), 'Forecast Range'] = '101-110'
df_fare_comp.loc[df_fare_comp['Forecast'].between(111, 10000, 'both'), 'Forecast Range'] = '>110'
df_fare_comp['Forecast Range'] = df_fare_comp['Forecast Range'].astype(forecast_order)

df_fare_comp.loc[df_fare_comp['NDO'].between(0, 7, 'both'), 'NDO Range'] = '0-7'
df_fare_comp.loc[df_fare_comp['NDO'].between(8, 15, 'both'), 'NDO Range'] = '8-15'
df_fare_comp.loc[df_fare_comp['NDO'].between(16, 30, 'both'), 'NDO Range'] = '16-30'
df_fare_comp.loc[df_fare_comp['NDO'].between(31, 60, 'both'), 'NDO Range'] = '31-60'
df_fare_comp.loc[df_fare_comp['NDO'].between(61, 90, 'both'), 'NDO Range'] = '61-90'
df_fare_comp.loc[df_fare_comp['NDO'].between(91, 120, 'both'), 'NDO Range'] = '91-120'
df_fare_comp.loc[df_fare_comp['NDO'].between(121, 10000, 'both'), 'NDO Range'] = '>120'
df_fare_comp['NDO Range'] = df_fare_comp['NDO Range'].astype(category_order)

df_client = df_fare_comp[df_fare_comp['Carrier'].isin(['AA'])]
df_industry = df_fare_comp[~df_fare_comp['Carrier'].isin(['AA'])]
df_ind = df_industry.groupby(['Departure Time'])['Fare'].min()
df_final = pd.merge(df_client, df_ind, left_on='Departure Time', right_on='Departure Time', suffixes=['', '_Ind'])
df_final['Fare_diff'] = df_final['Fare'] - df_final['Fare_Ind']

df_final.loc[df_final['Fare_diff'].between(0, 2, 'both'), 'Fare Delta'] = '0-2'
df_final.loc[df_final['Fare_diff'].between(3, 5, 'both'), 'Fare Delta'] = '3-5'
df_final.loc[df_final['Fare_diff'].between(6, 10, 'both'), 'Fare Delta'] = '6-10'
df_final.loc[df_final['Fare_diff'].between(11, 100000, 'both'), 'Fare Delta'] = '>10'
df_final.loc[df_final['Fare_diff'].between(-2, -1, 'both'), 'Fare Delta'] = '(0-2)'
df_final.loc[df_final['Fare_diff'].between(-5, -3, 'both'), 'Fare Delta'] = '(3-5)'
df_final.loc[df_final['Fare_diff'].between(-10, -6, 'both'), 'Fare Delta'] = '(6-10)'
df_final.loc[df_final['Fare_diff'].between(-100000, -11, 'both'), 'Fare Delta'] = '(>10)'

df_final['Fare Delta'] = df_final['Fare Delta'].astype(fare_delta_order)

day_list = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
]
initial_active_cell = {"row": 4, "column": 4, "column_id": "All", "row_id": "All"}
test_cols = ['Departure Status', 'Down-selling', 'Competitively Priced',
             'Up-selling', 'All']


def calc_flight_status(forecast, forecast_lower_limit, forecast_upper_limit):
    if forecast < forecast_lower_limit:
        status = 'Load Critical Departures'
    elif forecast > forecast_upper_limit:
        status = 'Yield Critical Departures'
    else:
        status = 'Competitive Departures'
    return status


def create_fare_delta(fare_diff, lower_limit, upper_limit):
    if fare_diff < lower_limit:
        category = "Down-selling"
    elif fare_diff > upper_limit:
        category = "Up-selling"
    else:
        category = "Competitively Priced"

    return category


def calc_filtered_data(start_ndo, end_ndo, market, sector):
    df_fare_copy = df_fare_comp.copy(deep=True)
    df_init = df_fare_copy[(df_fare_copy['NDO'] >= start_ndo) &
                           (df_fare_copy['NDO'] <= end_ndo) &
                           (df_fare_copy['Route'] == market) &
                           (df_fare_copy['Sector'] == sector)]
    return df_init


def description_card():
    """
    :return: A Div containing dashboard title & descriptions.
    """
    return html.Div(
        id="description-card",
        children=[
            html.H5("Fare Analytics",
                    style={"font-weight": "bold"}),
            html.H3("Welcome to the Fare Insights Analytics Dashboard"),
            html.P(
                "Explore insights related to fares across varied routes, flights, products etc. and analyse fare trend for upcoming departures.\n"
                "This dashboard is at sector level which could be further drilled down till respective flight numbers by Departure date range or Days-to-departure range",
                style={'fontSize': 14}),
            html.P(),
            html.Span(children=[
                html.I("Note: The dashboard has been created considering"),
                html.B(" AA "),
                html.I("as the operating Carrier and other carriers as potential competitors in the route."),
                html.I("Filters in this section will work on all the views of the dashboard.")],
                style={'color': 'brown', 'fontSize': 14})
        ],
    )


def create_fare_range(df, forecast_lower_limit, forecast_upper_limit, fare_lower_limit, fare_upper_limit):
    df.loc[df['Fare_diff'].between(0, 2, 'both'), 'Fare Delta'] = '0-2'
    df.loc[df['Fare_diff'].between(3, 5, 'both'), 'Fare Delta'] = '3-5'
    df.loc[df['Fare_diff'].between(6, 10, 'both'), 'Fare Delta'] = '6-10'
    df.loc[df['Fare_diff'].between(11, 100000, 'both'), 'Fare Delta'] = '>10'
    df.loc[df['Fare_diff'].between(-2, -1, 'both'), 'Fare Delta'] = '(0-2)'
    df.loc[df['Fare_diff'].between(-5, -3, 'both'), 'Fare Delta'] = '(3-5)'
    df.loc[df['Fare_diff'].between(-10, -6, 'both'), 'Fare Delta'] = '(6-10)'
    df.loc[df['Fare_diff'].between(-100000, -11, 'both'), 'Fare Delta'] = '(>10)'

    df['Departure Status'] = df.apply(
        lambda x: calc_flight_status(x.Forecast, forecast_lower_limit, forecast_upper_limit), axis=1)
    df['Fare_Category'] = df.apply(lambda x: create_fare_delta(x.Fare_diff, fare_lower_limit, fare_upper_limit), axis=1)
    df['Departure Status'] = df['Departure Status'].astype(departure_order)
    df['Fare_Category'] = df['Fare_Category'].astype(fare_category_order)
    return df


def create_res_df(df, flight_no, comp, comp_flight):
    df_client_details = df[(df['Carrier'] == "AA") & (df['Flight No'].isin(flight_no))]
    df_industry_details = df[(df['Carrier'].isin(comp)) & (df['Flight No'].isin(comp_flight))]
    df_ind_gp = df_industry_details.groupby(['Departure Time'])['Fare'].min()
    df_res_details = pd.merge(df_client_details, df_ind_gp, left_on='Departure Time', right_on='Departure Time',
                              suffixes=['', '_Ind'])
    df_res_details['Fare_diff'] = df_res_details['Fare'] - df_res_details['Fare_Ind']
    return df_res_details


def generate_control_card():
    """
    :return: A Div containing controls for graphs.
    """
    return html.Div(
        id="control-card",
        children=[
            html.P(),
            html.P("Select Departure Date Range", id="test-tooltip"),
            dbc.Tooltip(
                "Assumed departures starting from 01st Apr'23",
                target="test-tooltip",
                placement="bottom",
                style={'fontSize': 12, 'color': 'brown'}
            ),
            dcc.DatePickerRange(
                id="dtd-date-range",
                start_date=min(df_fare_comp['Departure Time']).date(),
                end_date=max(df_fare_comp['Departure Time']).date(),
                min_date_allowed=min(df_fare_comp['Departure Time']).date(),
                max_date_allowed=max(df_fare_comp['Departure Time']).date(),
                initial_visible_month=dt(2023, 7, 1),
                className="dcc_control",
            ),
            html.Br(),
            html.P("Select Days-to-Departure Range"),
            dcc.RangeSlider(
                id="dtd-range-slider",
                min=0,
                max=180,
                step=None,
                marks={0: '0', 7: '7', 15: '15', 30: '30', 45: '45', 60: '60', 90: '90', 120: '120', 180: '180'},
                value=[0, 180],
                tooltip={"placement": "bottom", "always_visible": True},
                allowCross=False,
                className="dcc_control",
            ),
            html.P(),
            html.P("Select Acceptable Load Forecast Range (%)"),
            dcc.RangeSlider(
                id="forecast-range-slider",
                min=0,
                max=120,
                step=10,
                value=[90, 100],
                allowCross=False,
                className="dcc_control",
            ),
            html.P(),
            html.P("Select Acceptable Price Variation Range ($)"),
            dcc.RangeSlider(
                id="price-delta-slider",
                min=-10,
                max=10,
                step=2,
                value=[-2, 2],
                allowCross=False,
                className="dcc_control",
            ),
            html.P(),
            html.Div(
                [
                    html.Div(
                        [
                            html.P("Select Route"),
                            dcc.Dropdown(
                                id="market-select",
                                options=df_fare_comp['Route'].unique(),
                                value="BOMDEL",
                                className="dcc_control",
                                searchable=True,
                                search_value="Search for Market"
                            )
                        ], style={'width': '40%', 'display': 'inline-block', 'margin': '0px 80px 0px 0px'}
                    ),
                    html.Div(
                        [
                            html.P("Select Sector"),
                            dcc.Dropdown(
                                id="sector-select",
                                options=df_fare_comp['Sector'].unique(),
                                value="BOMDEL",
                                multi=False,
                                className="dcc_control",
                            )
                        ], style={'width': '40%', 'display': 'inline-block', 'margin': '0px 0px 0px 10px'}
                    )
                ]
            ),
            html.P(),
            html.P("Select Competition"),
            dcc.Dropdown(
                id="comp-select",
                options=["BB", "CC", "DD"],
                # value=all_sectors[:],
                value=["BB", "CC", "DD"],
                multi=True,
                className="dcc_control",
            ),
            html.P(),
            html.Div(
                [
                    html.Div(
                        [
                            html.P("Select Flight"),
                            dcc.Dropdown(
                                id="flight-select",
                                options=df_client['Flight No'].unique(),
                                # value=all_flights[:],
                                # value=[2393, 4589, 9876],
                                multi=True,
                                className="dcc_control",
                            )
                        ], style={'width': '100%'}
                    ),
                    html.Div(
                        [
                            html.P("Select Competition Flight"),
                            dcc.Dropdown(
                                id="comp-flight-select",
                                options=df_industry['Flight No'].unique(),
                                value=df_industry['Flight No'].unique(),
                                multi=True,
                                className="dcc_control",
                                # # maxHeight=5,
                                # optionHeight=5,
                            )
                        ], style={'width': '100%'}
                    )
                ]
            ),
        ],
    )


app.layout = html.Div(
    id="app-container",
    children=[
        # Banner
        # html.Div(
        #     id="banner",
        #     className="banner",
        #     # children=[html.Img(src=app.get_asset_url("plotly_logo.png"))],
        # ),
        html.Div(
            [
                html.Div(
                    id="left-column",
                    className="pretty_container four columns",
                    children=[description_card(), generate_control_card()],
                    style={'border': '1px solid black'},
                ),
                # Right column
                html.Div(
                    [
                        html.Div(
                            [
                                html.Div(
                                    [html.H5(id="tot-departureText"), html.P("Total Departures (Sector)")],
                                    # id="departures",
                                    className="mini_container",
                                    style={'padding': '0px 10px', 'textAlign': 'center', 'fontWeight': 'bold',
                                           'backgroundColor': 'lightgrey'}
                                ),
                                html.Div(
                                    [html.H5(id="departureText"), html.P("AA Departures (Sector)")],
                                    # id="departures",
                                    className="mini_container",
                                    style={'padding': '0px 10px', 'textAlign': 'center', 'fontWeight': 'bold',
                                           'backgroundColor': 'lightgrey'}
                                ),
                                html.Div(
                                    [html.H5(id="competitionText"), html.P("Major Competition (Departures)")],
                                    # id="overbooked_departures",
                                    className="mini_container",
                                    style={'padding': '0px 5px', 'textAlign': 'center', 'fontWeight': 'bold',
                                           'backgroundColor': 'lightgrey'}
                                ),
                                html.Div(
                                    [html.H5(id="yield-criticalText"), html.P("Yield Critical Departures")],
                                    # id="yield-criticalText",
                                    className="mini_container",
                                    style={'padding': '0px 10px', 'textAlign': 'center', 'fontWeight': 'bold',
                                           'backgroundColor': 'lightgrey'}
                                ),
                                html.Div(
                                    [html.H5(id="load-criticalText"), html.P("Load Critical Departures")],
                                    # id="load-criticalText",
                                    className="mini_container",
                                    style={'padding': '0px 15px', 'textAlign': 'center', 'fontWeight': 'bold',
                                           'backgroundColor': 'lightgrey'}
                                )
                            ],
                            id="info-container",
                            className="row container-display",
                        ),
                        html.Div(
                            [
                                html.Div(html.B("1. Pricing Performance", style={'fontSize': 18})),
                                html.Span(children=[
                                    html.I(
                                        "* Objective is to provide a summary of departures where we are competitive basis overall load forecast and highlight uncompetitive departures requiring "
                                        "immediate attention in terms of pricing or inventory correction by sector, flight number and days-to-departure.")
                                ]),
                                html.Div(
                                    [html.Br(),
                                     html.B("1.1 Departure Distribution by Price Variation and Departure Status",
                                            style={'textAlign': 'center', 'font': 'Arial', 'fontSize': 15}),
                                     html.P()]
                                ),
                                html.Div(
                                    [
                                        dcc.RadioItems(
                                            id='price-radio',
                                            options=
                                            [
                                                {'value': 'dep_count', 'label': 'By Departure Count'},
                                                {'value': 'perc_count', 'label': 'As a Percentage of Total Departures'}
                                            ],
                                            value='dep_count',
                                            inline=True,
                                            inputStyle={'margin-right': '10px'},
                                            labelStyle={'display': 'inline-block', 'padding': '0.5rem 0.5rem'}
                                        )
                                    ],
                                ),
                                html.Br(),
                                html.Div(
                                    [
                                        dash_table.DataTable(
                                            id="fare_comp",
                                            columns=[{"name": i, "id": i} for i in test_cols],
                                            active_cell=initial_active_cell,
                                            tooltip_header={
                                                'Down-selling': 'Selling below Acceptable Price Variation',
                                                'Competitively Priced': 'Selling within Acceptable Price Variation',
                                                'Up-selling': 'Selling above Acceptable Price Variation  ',
                                            },
                                            tooltip_data=[
                                                {
                                                    'Departure Status': 'Departures below desired forecast',
                                                    'Down-selling': 'Load critical departures selling below market price',
                                                    'Competitively Priced': 'Load critical departures selling at market price',
                                                    'Up-selling': 'Load critical departures selling above market price',
                                                },
                                                {
                                                    'Departure Status': 'Departures within desired forecast',
                                                    'Down-selling': 'Competitive departures selling below market price',
                                                    'Competitively Priced': 'Competitive departures selling at market price',
                                                    'Up-selling': 'Competitive departures selling above market price',
                                                },
                                                {
                                                    'Departure Status': 'Departures above desired forecast',
                                                    'Down-selling': 'Yield critical departures selling below market price ',
                                                    'Competitively Priced': 'Yield critical departures selling at market price',
                                                    'Up-selling': 'Yield critical departures selling above market price',
                                                }
                                            ],
                                            css=[{
                                                'selector': '.dash-table-tooltip',
                                                'rule': 'background-color: lightgrey; font-family: monospace; color: brown'
                                            }],
                                            style_data_conditional=(
                                                [
                                                    # 'filter_query', 'column_id', 'column_type', 'row_index', 'state', 'column_editable'.
                                                    # filter_query ****************************************
                                                    {
                                                        'if': {
                                                            'row_index': 0,
                                                            'column_id': 'Down-selling'
                                                        },
                                                        'backgroundColor': '#d3d3d3',
                                                    },
                                                    {
                                                        'if': {
                                                            'row_index': 1,
                                                            'column_id': 'Down-selling'
                                                        },
                                                        'backgroundColor': '#dc143c',
                                                        # 'backgroundColor': '#dc143c',
                                                        'color': 'white'
                                                    },
                                                    {
                                                        'if': {
                                                            'row_index': 2,
                                                            'column_id': 'Down-selling'
                                                        },
                                                        # 'backgroundColor': '#2c82ff',
                                                        'backgroundColor': '#dc143c',
                                                        'color': 'white'
                                                    },
                                                    {
                                                        'if': {
                                                            'row_index': 0,
                                                            'column_id': 'Competitively Priced'
                                                        },
                                                        'backgroundColor': '#f4a460',
                                                    },
                                                    {
                                                        'if': {
                                                            'row_index': 1,
                                                            'column_id': 'Competitively Priced'
                                                        },
                                                        'backgroundColor': '#d3d3d3',
                                                    },
                                                    {
                                                        'if': {
                                                            'row_index': 2,
                                                            'column_id': 'Competitively Priced'
                                                        },
                                                        'backgroundColor': '#f4a460',
                                                        'color': 'black'
                                                    },
                                                    {
                                                        'if': {
                                                            'row_index': 0,
                                                            'column_id': 'Up-selling'
                                                        },
                                                        'backgroundColor': '#dc143c',
                                                        'color': 'white'
                                                    },
                                                    {
                                                        'if': {
                                                            'row_index': 1,
                                                            'column_id': 'Up-selling'
                                                        },
                                                        'backgroundColor': '#dc143c',
                                                        'color': 'white'
                                                    },
                                                    {
                                                        'if': {
                                                            'row_index': 2,
                                                            'column_id': 'Up-selling'
                                                        },
                                                        'backgroundColor': '#d3d3d3',
                                                    },
                                                    {
                                                        'if': {
                                                            'state': 'active'  # 'active' | 'selected'
                                                        },
                                                        'border': '3px solid rgb(0, 116, 217)'
                                                    },
                                                ]
                                            ),
                                            style_cell={
                                                # ensure adequate header width when text is shorter than cell's text
                                                'minWidth': 95, 'maxWidth': 95, 'width': 95, 'textAlign': 'center',
                                                'padding': '5px',
                                                'font_family': 'sans-serif', 'backgroundColor': 'rgba(0,0,0,0)'
                                            },
                                            style_table={'height': '175px', 'overflowY': 'auto'},
                                            style_data={  # overflow cells' content into multiple lines
                                                'whiteSpace': 'normal',
                                                'height': 'auto',
                                                'template': 'ggplot2',
                                                'font_family': 'sans-serif'
                                            },
                                            style_header={
                                                'template': 'ggplot2',
                                                'fontWeight': 'bold',
                                                'font_family': 'sans-serif'
                                            },
                                            style_as_list_view=True,
                                        )
                                    ]
                                    # id='fare_comp',

                                ),
                                html.Br(),
                                html.P(),

                                html.Div(
                                    [

                                        html.B("1.2 Departure Distribution by Days-to-Departure and Departure Status",
                                               style={'textAlign': 'center', 'font': 'Arial', 'fontSize': 15}),
                                        html.P()
                                    ]
                                ),
                                html.Div(
                                    [
                                        dcc.RadioItems(
                                            id='price-radio-1',
                                            options=
                                            [
                                                {'value': 'dep_count', 'label': 'By Departure Count'},
                                                {'value': 'perc_count', 'label': 'As a Percentage of Total Departures'}
                                            ],
                                            value='dep_count',
                                            inline=True,
                                            inputStyle={'margin-right': '10px'},
                                            labelStyle={'display': 'inline-block', 'padding': '0.5rem 0.5rem'}
                                        )
                                    ],
                                ),
                                html.P(),
                                html.Div(
                                    # id='bar-container',
                                    dcc.Graph(id="bar-container")
                                    # className="pretty_container twelve columns"
                                ),
                            ],
                            className="pretty_container"
                        ),
                    ],
                    id="right-column",
                    className="eight columns",
                ),
            ],
            className="row flex-display",
        ),
        html.Div(
            [
                html.Div(
                    [
                        html.Div(html.B("2. Fare Competitiveness Analysis", style={'fontSize': 18})),
                        html.P(),
                        html.B("2.1 Load Factor Forecast Trend",
                               style={'textAlign': 'center', 'font': 'Arial', 'fontSize': 15}),
                        html.P(),
                        html.Span(children=[
                            html.I(
                                "* This view displays the forecast for the selected sector and flight by departure date.",
                                style={'fontSize': 14}),
                            html.P(),
                            html.I(
                                "* Apart from the forecast user can also identify the pricing status (Up-selling, Down-selling or Competitively-priced), colors highlighted at the peak of a bar",
                                style={'fontSize': 14}),
                            html.P(),
                            html.I(
                                "* The view will be automatically updated basis the selection of global filters or data selected in",
                                style={'fontSize': 14}),
                            html.B(" Pricing Performance",
                                   style={'fontSize': 14}),
                            html.I(
                                "  view displayed above.",
                                style={'fontSize': 14}),
                        ]),
                        dcc.Graph(id="forecast_trend")
                    ],
                    className="pretty_container twelve columns"
                ),
            ],
            className="row flex-display",
        ),
        html.Div(
            [
                html.Div(
                    [
                        html.B("2.2 Industry Minimum Fare Comparison",
                               style={'textAlign': 'center', 'font': 'Arial', 'fontSize': 15}),
                        html.P(),
                        html.Span(children=[
                            html.I(
                                "* This view gives user a comparative analysis of min fare offered by client AA by departure dates vs min fare offered by any carrier in the selected route and flight (Industry Minimum).",
                                style={'fontSize': 14}),
                            html.P(),
                            html.I(
                                "* The view will be automatically updated basis the selection of global filters or data selected in",
                                style={'fontSize': 14}),
                            html.B(" Pricing Performance",
                                   style={'fontSize': 14}),
                            html.I(
                                "  view displayed above.",
                                style={'fontSize': 14}),
                            # html.P(),
                            # html.I(
                            #     "* Apart from the forecast user can also identify the pricing status (Up-selling, Down-selling or Competitively-priced), colors highlighted at the peak of a bar",
                            #     style={'fontSize': 14}),
                        ]),
                        dcc.Graph(id="ind_min")
                    ],
                    className="pretty_container twelve columns"
                ),
            ],
            className="row flex-display",
        ),
        html.Div(
            [
                html.Div(
                    [
                        html.B("2.3 Industry Fare Comparison",
                               style={'textAlign': 'center', 'font': 'Arial', 'fontSize': 15}),
                        html.P(),
                        html.Span(children=[
                            html.I(
                                "* This view allows user to compare the fare offered by them vs fares offered by other carriers in the selected route and flight",
                                style={'fontSize': 14}),
                            html.P(),
                            html.I(
                                "* User can also choose the competition with whom they want to compare their fares by doing a single-click on 'Published Fare by Carrier' shown in the legends just above the view.",
                                style={'fontSize': 14}),
                            html.P(),
                            html.I(
                                "* The view will be automatically updated basis the selection of global filters or data selected in",
                                style={'fontSize': 14}),
                            html.B(" Pricing Performance",
                                   style={'fontSize': 14}),
                            html.I(
                                "  view displayed above.",
                                style={'fontSize': 14}),

                        ]),
                        dcc.Graph(id="fare_comparison")
                    ],
                    className="pretty_container twelve columns"
                ),
            ],
            className="row flex-display",
        ),
        html.Div(
            [
                html.Div(
                    [
                        html.B("3. Available Fares and Frequency by Carrier and Route",
                               style={'textAlign': 'center', 'font': 'Arial', 'fontSize': 18}),
                        html.P(),
                        html.Span(children=[
                            html.I(
                                "* Main objective of this view is to provide users a consolidated view of fares offered by them vs competition by doing a single-click on 'Carrier' shown in the legends just above the view and optimize their fare structure accordingly.",
                                style={'fontSize': 14}),
                            html.P(),
                            html.I(
                                "* User can also choose the competition with whom they want to compare their fares by doing a single-click on 'Carrier' shown in the legends just above the view.",
                                style={'fontSize': 14}),
                            html.P(),
                            html.I(
                                "* The view will be automatically updated basis the selection of global filters ",
                                style={'fontSize': 14}),
                            html.B(" ONLY",
                                   style={'fontSize': 14}),
                            html.I(
                                " unlike the views displayed above.",
                                style={'fontSize': 14}),

                        ]),
                        dcc.Graph(id="fare_freq_comparison")
                    ],
                    className="pretty_container twelve columns"
                ),
            ],
            className="row flex-display",
        ),
        # dcc.Store stores the intermediate value
        dcc.Store(id='intermediate-value'),
        # dcc.Store(id='price-matrix')

    ]
)


# @app.callback(
#     [Output("dtd-date-range", "start_date"),
#      Output("dtd-date-range", "end_date")],
#     Input("dtd-range-slider", "value")
# )
# def update_departure_dates(dtd_range_slider):
#     init_date_1 = init_date + datetime.timedelta(days=dtd_range_slider[0])
#     last_date_1 = init_date + datetime.timedelta(days=dtd_range_slider[1])
#     return init_date_1, last_date_1


@app.callback(
    Output('dtd-range-slider', 'value'),
    Input('dtd-date-range', 'start_date'),
    Input('dtd-date-range', 'end_date')
)
def update_departure_dtd(start_date, end_date):
    value_list = list()
    # print(f'Check the value of start_date during start {start_date}')
    # print(f'Check the value of end_date during start {end_date}')
    start_date = dt.strptime(start_date, '%Y-%m-%d').date()
    # print(f'Check the value of start_date {start_date}')
    end_date = dt.strptime(end_date, '%Y-%m-%d').date()
    # print(f'Check the value of end_date {end_date}')
    ndo_range_min = (start_date - init_date).days
    # print(f'Check the value of ndo_range_min {ndo_range_min}')
    value_list.append(ndo_range_min)
    ndo_range_max = (end_date - init_date).days
    # print(f'Check the value of ndo_range_max {ndo_range_max}')
    value_list.append(ndo_range_max)
    return value_list


@app.callback(
    Output("comp-flight-select", "value"),
    Input("comp-select", "value"),
    Input("sector-select", "value")
)
def update_comp_flights(comp, sector):
    return df_industry[(df_industry['Carrier'].isin(comp)) &
                       (df_industry['Sector'] == sector)]['Flight No'].unique()


@app.callback(
    Output("flight-select", "value"),
    Input("sector-select", "value")
)
def update_client_flights(sector):
    return df_client[df_client['Sector'] == sector]['Flight No'].unique()


@app.callback(
    Output("intermediate-value", "data"),
    [
        Input("dtd-range-slider", "value"),
        Input("market-select", "value"),
        Input("sector-select", "value"),
        Input("comp-select", "value"),
        Input("flight-select", "value"),
        Input("comp-flight-select", "value"),
        Input("forecast-range-slider", "value"),
        Input("price-delta-slider", "value"),
    ]
)
def calc_inter_data(dtd_range, market, sector, comp, flight_no, comp_flight, forecast_range, price_delta):
    forecast_lower_limit = forecast_range[0]
    forecast_upper_limit = forecast_range[1]
    lower_limit = price_delta[0]
    upper_limit = price_delta[1]
    df_filt_init = calc_filtered_data(dtd_range[0], dtd_range[1], market, sector)
    df_res_total = create_res_df(df_filt_init, flight_no, comp, comp_flight)
    df_final_updated = create_fare_range(df_res_total, forecast_lower_limit, forecast_upper_limit, lower_limit,
                                         upper_limit)

    datasets = {
        'df_1': df_filt_init.to_json(orient='split', date_format='iso'),
        'df_2': df_res_total.to_json(orient='split', date_format='iso'),
        'df_3': df_final_updated.to_json(orient='split', date_format='iso'),
    }
    return json.dumps(datasets)


@app.callback(
    [
        Output("tot-departureText", "children"),
        Output("departureText", "children"),
        Output("competitionText", "children"),
        Output("yield-criticalText", "children"),
        Output("load-criticalText", "children")
    ],
    [
        Input("dtd-range-slider", "value"),
        Input("market-select", "value"),
        Input("sector-select", "value"),
        Input("comp-select", "value"),
        Input("flight-select", "value"),
        Input("comp-flight-select", "value"),
        Input("forecast-range-slider", "value"),
    ]
)
def update_header_details(dtd_range, market, sector, comp, flight_no, comp_flight, forecast_range):
    forecast_lower_limit = forecast_range[0]
    forecast_upper_limit = forecast_range[1]

    df_fare_comp_1 = calc_filtered_data(dtd_range[0], dtd_range[1], market, sector)
    total_departures = df_fare_comp_1['Flight No'].count()

    df_client_1 = df_fare_comp_1[(df_fare_comp_1['Carrier'] == "AA") & (df_fare_comp_1['Flight No'].isin(flight_no))]
    df_industry_1 = df_fare_comp_1[
        (df_fare_comp_1['Carrier'].isin(comp)) & (df_fare_comp_1['Flight No'].isin(comp_flight))]

    # Capturing the client departure details with respect to the competition and flight numbers selected
    client_departures = df_client_1['Flight No'].count()
    client_departures_perc = round(client_departures / total_departures * 100)
    departure_details = str(client_departures) + " (" + str(client_departures_perc) + "%)"

    # Capturing the number of departures of the biggest competition available
    comp_departures = df_industry_1.groupby('Carrier')['Flight No'].count().sort_values(ascending=False).reset_index()
    comp_carrier = comp_departures['Carrier'][0]
    comp_carrier_freq = comp_departures['Flight No'][0]
    comp_departures_perc = round(comp_carrier_freq / total_departures * 100)
    comp_departure_details = str(comp_carrier) + " (" + str(comp_departures_perc) + "%)"

    # Capturing the total departures which are over-forecasted but underpriced and under-forecasted but overpriced
    df_client_1['Departure Status'] = df_client_1.apply(lambda x: calc_flight_status(x.Forecast,
                                                                                     forecast_lower_limit,
                                                                                     forecast_upper_limit),
                                                        axis=1)

    df_client_1['Departure Status'] = df_client_1['Departure Status'].astype(departure_order)
    yield_crit_dep = df_client_1[df_client_1['Departure Status'] == 'Yield Critical Departures']['Flight No'].count()
    load_crit_dep = df_client_1[df_client_1['Departure Status'] == 'Load Critical Departures']['Flight No'].count()
    yield_crit_dep_perc = round(yield_crit_dep / client_departures * 100)
    yield_crit_departure_details = str(yield_crit_dep) + " (" + str(yield_crit_dep_perc) + "%)"

    load_crit_dep_perc = round(load_crit_dep / client_departures * 100)
    load_crit_departure_details = str(load_crit_dep) + " (" + str(load_crit_dep_perc) + "%)"

    return total_departures, departure_details, comp_departure_details, yield_crit_departure_details, load_crit_departure_details


# @app.callback(
#     Output('price-matrix', 'data'),
#     Input('fare_comp', 'derived_virtual_selected_rows')
# )
# def update_price_matrix(price_matrix_input):
#     print(f'lets check the value of price_matrix_input {price_matrix_input}')
#     return price_matrix_input


@app.callback(
    [
        Output('fare_comp', 'data'),
    ],
    [
        Input("intermediate-value", "data"),
        Input("price-radio", "value")
    ]
)
def update_price_delta_matrix(cleaned_data, agg_method):
    datasets = json.loads(cleaned_data)
    dff = pd.read_json(datasets['df_3'], orient='split')
    df_final_updated = dff.copy(deep=True)
    df_final_updated['Departure Status'] = df_final_updated['Departure Status'].astype(departure_order)
    df_final_updated['Fare_Category'] = df_final_updated['Fare_Category'].astype(fare_category_order)
    df_final_updated['DTD Range'] = df_final_updated['NDO Range'].astype(category_order)

    df_pivot = pd.pivot_table(df_final_updated, values='Fare', index='Departure Status', columns='Fare_Category',
                              aggfunc='count', fill_value=0, margins=True)
    if agg_method == 'perc_count':
        fare_count = df_final_updated['Fare'].count()
        df_pivot = round((df_pivot / fare_count) * 100)

    df_res_1 = df_pivot.reset_index()
    df_res_1.columns.name = None
    # print(f'Checking the column names of df_res_1 {df_res_1.columns}')
    df_res_1['id'] = df_res_1['Departure Status']
    df_res_1.set_index('id', inplace=True, drop=False)
    data = df_res_1.to_dict("records"),

    return data


#
# @app.callback(
#     Output("fare_comp", "children"),
#     [Input("intermediate-value", "data"),
#      Input("price-radio", "value")]
# )
# def update_price_delta_matrix(cleaned_data, agg_method):
#     datasets = json.loads(cleaned_data)
#     dff = pd.read_json(datasets['df_3'], orient='split')
#     df_final_updated = dff.copy(deep=True)
#     df_final_updated['Departure Status'] = df_final_updated['Departure Status'].astype(departure_order)
#     df_final_updated['Fare_Category'] = df_final_updated['Fare_Category'].astype(fare_category_order)
#     df_final_updated['DTD Range'] = df_final_updated['NDO Range'].astype(category_order)
#
#     df_pivot = pd.pivot_table(df_final_updated, values='Fare', index='Departure Status', columns='Fare_Category',
#                               aggfunc='count', fill_value=0, margins=True)
#     if agg_method == 'perc_count':
#         fare_count = df_final_updated['Fare'].count()
#         df_pivot = round((df_pivot / fare_count) * 100)
#
#     df_res_1 = df_pivot.reset_index()
#     df_res_1.columns.name = None
#     columns = list(df_res_1.columns)
#     df_res_1['id'] = df_res_1['Departure Status']
#     df_res_1.set_index('id', inplace=True, drop=False)
#
#     children = dash_table.DataTable(
#         id='datatable-interactivity',
#         columns=[{'name': i,
#                   'id': i
#                   } for i in columns],
#         data=df_res_1.to_dict("records"),
#         tooltip_delay=0,
#         tooltip_duration=None,
#         tooltip_header={
#             'Down-selling': 'Selling below Acceptable Price Variation',
#             'Competitively Priced': 'Selling within Acceptable Price Variation',
#             'Up-selling': 'Selling above Acceptable Price Variation  ',
#         },
#         tooltip_data=[
#             {
#                 'Departure Status': 'Departures below desired forecast',
#                 'Down-selling': 'Load critical departures selling below market price',
#                 'Competitively Priced': 'Load critical departures selling at market price',
#                 'Up-selling': 'Load critical departures selling above market price',
#             },
#             {
#                 'Departure Status': 'Departures within desired forecast',
#                 'Down-selling': 'Competitive departures selling below market price',
#                 'Competitively Priced': 'Competitive departures selling at market price',
#                 'Up-selling': 'Competitive departures selling above market price',
#             },
#             {
#                 'Departure Status': 'Departures above desired forecast',
#                 'Down-selling': 'Yield critical departures selling below market price ',
#                 'Competitively Priced': 'Yield critical departures selling at market price',
#                 'Up-selling': 'Yield critical departures selling above market price',
#             }
#         ],
#         css=[{
#             'selector': '.dash-table-tooltip',
#             'rule': 'background-color: lightgrey; font-family: monospace; color: brown'
#         }],
#         active_cell=initial_active_cell,
#         style_data_conditional=(
#             [
#                 # 'filter_query', 'column_id', 'column_type', 'row_index', 'state', 'column_editable'.
#                 # filter_query ****************************************
#                 {
#                     'if': {
#                         'row_index': 0,
#                         'column_id': 'Down-selling'
#                     },
#                     'backgroundColor': '#d3d3d3',
#                 },
#                 {
#                     'if': {
#                         'row_index': 1,
#                         'column_id': 'Down-selling'
#                     },
#                     'backgroundColor': '#dc143c',
#                     # 'backgroundColor': '#dc143c',
#                     'color': 'white'
#                 },
#                 {
#                     'if': {
#                         'row_index': 2,
#                         'column_id': 'Down-selling'
#                     },
#                     # 'backgroundColor': '#2c82ff',
#                     'backgroundColor': '#dc143c',
#                     'color': 'white'
#                 },
#                 {
#                     'if': {
#                         'row_index': 0,
#                         'column_id': 'Competitively Priced'
#                     },
#                     'backgroundColor': '#f4a460',
#                 },
#                 {
#                     'if': {
#                         'row_index': 1,
#                         'column_id': 'Competitively Priced'
#                     },
#                     'backgroundColor': '#d3d3d3',
#                 },
#                 {
#                     'if': {
#                         'row_index': 2,
#                         'column_id': 'Competitively Priced'
#                     },
#                     'backgroundColor': '#f4a460',
#                     'color': 'black'
#                 },
#                 {
#                     'if': {
#                         'row_index': 0,
#                         'column_id': 'Up-selling'
#                     },
#                     'backgroundColor': '#dc143c',
#                     'color': 'white'
#                 },
#                 {
#                     'if': {
#                         'row_index': 1,
#                         'column_id': 'Up-selling'
#                     },
#                     'backgroundColor': '#dc143c',
#                     'color': 'white'
#                 },
#                 {
#                     'if': {
#                         'row_index': 2,
#                         'column_id': 'Up-selling'
#                     },
#                     'backgroundColor': '#d3d3d3',
#                 },
#                 {
#                     'if': {
#                         'state': 'active'  # 'active' | 'selected'
#                     },
#                     'border': '3px solid rgb(0, 116, 217)'
#                 },
#             ]
#         ),
#         style_cell={  # ensure adequate header width when text is shorter than cell's text
#             'minWidth': 95, 'maxWidth': 95, 'width': 95, 'textAlign': 'center', 'padding': '5px',
#             'font_family': 'sans-serif', 'backgroundColor': 'rgba(0,0,0,0)'
#         },
#         style_table={'height': '175px', 'overflowY': 'auto'},
#         style_data={  # overflow cells' content into multiple lines
#             'whiteSpace': 'normal',
#             'height': 'auto',
#             'template': 'ggplot2',
#             'font_family': 'sans-serif'
#         },
#         style_header={
#             'template': 'ggplot2',
#             'fontWeight': 'bold',
#             'font_family': 'sans-serif'
#         },
#
#         style_as_list_view=True,
#     )
#
#     return children


@app.callback(
    Output("bar-container", "figure"),
    [
        Input("intermediate-value", "data"),
        Input("price-radio-1", "value"),
        Input('fare_comp', 'active_cell'),
    ])
def update_price_dist_ndo(cleaned_data, agg_method, selected_data):
    datasets = json.loads(cleaned_data)
    dff = pd.read_json(datasets['df_3'], orient='split')
    df_final_updated = dff.copy(deep=True)
    df_final_updated['Departure Status'] = df_final_updated['Departure Status'].astype(departure_order)
    df_final_updated['Fare_Category'] = df_final_updated['Fare_Category'].astype(fare_category_order)
    df_final_updated['NDO Range'] = df_final_updated['NDO Range'].astype(category_order)
    df_final1 = pd.DataFrame()

    if selected_data is not None and selected_data['column_id'] != 'Departure Status':
        print(f' Check the value of elected_data["column_id"] {selected_data["column_id"]} ')
        print(f' Check the value of elected_data["row_id"] {selected_data["row_id"]} ')
        if selected_data['column_id'] == 'All' and selected_data['row_id'] in (
                ['Load Critical Departures', 'Competitive Departures', 'Yield Critical Departures']):
            df_final1 = df_final_updated[df_final_updated['Departure Status'] == selected_data['row_id']]
            df_bar = df_final1.groupby(['NDO Range', 'Departure Status'])['Fare'].count()
        elif selected_data['row_id'] == 'All' and selected_data['column_id'] in (
                ['Down-selling', 'Competitively Priced', 'Up-selling']):
            df_final1 = df_final_updated[df_final_updated['Fare_Category'] == selected_data['column_id']]
            df_bar = df_final1.groupby(['NDO Range', 'Departure Status'])['Fare'].count()
        elif selected_data['row_id'] == 'All' and selected_data['column_id'] == 'All':
            df_final1 = df_final_updated.copy(deep=True)
            df_bar = df_final_updated.groupby(['NDO Range', 'Departure Status'])['Fare'].count()
        else:
            # print(f'Checking the value of selected data {selected_data}')
            departure_status = selected_data['row_id']
            fare_category = selected_data['column_id']
            df_final1 = df_final_updated[(df_final_updated['Departure Status'] == departure_status) &
                                         (df_final_updated['Fare_Category'] == fare_category)]
            df_bar = df_final1.groupby(['NDO Range', 'Departure Status'])['Fare'].count()
    else:
        df_bar = df_final_updated.groupby(['NDO Range', 'Departure Status'])['Fare'].count()

    if agg_method == 'perc_count':
        if selected_data is not None:
            # print("Are we entering when selected_Data is not none ?")
            fare_count = df_final1['Fare'].count()
        else:
            # print("Are we entering here ?")
            fare_count = df_final_updated['Fare'].count()
        df_bar_final = df_bar.reset_index(name="Departure Count")
        df_bar_final.loc[:, "Departure Distribution (in %)"] = round(df_bar_final['Departure Count'] / fare_count * 100)
        # print(f'Checking the value of df_bar_final {df_bar_final}')
        fig = px.bar(df_bar_final, y='NDO Range', x='Departure Distribution (in %)', color='Departure Status',
                     barmode='stack', orientation='h', template='ggplot2', custom_data=['Departure Count'],
                     # labels={'Fare': 'Departure Distribution (in %)',
                     #         'NDO Range': 'Days-to-Departure Range'},
                     text_auto=True)
    else:
        fig = px.bar(df_bar.reset_index(), y='NDO Range', x='Fare', color='Departure Status',
                     barmode='stack', orientation='h', template='ggplot2',
                     labels={'Fare': 'Departure Count',
                             'NDO Range': 'Days-to-Departure Range'},
                     text_auto=True)

    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        legend=dict(
            orientation="h",
            font=dict(size=12),
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=0.8))

    return fig


@app.callback(
    Output("forecast_trend", "figure"),
    [Input("fare_comp", "active_cell"),
     Input("intermediate-value", "data")]
)
def update_forecast(selected_data, cleaned_data):
    datasets = json.loads(cleaned_data)
    dff = pd.read_json(datasets['df_3'], orient='split')
    df_final_updated = dff.copy(deep=True)

    fig = go.Figure()
    if selected_data is not None and selected_data['row_id'] != 'All' and selected_data['column_id'] != 'All':
        departure_status = selected_data['row_id']
        fare_category = selected_data['column_id']
        df_final1 = df_final_updated[(df_final_updated['Departure Status'] == departure_status) &
                                     (df_final_updated['Fare_Category'] == fare_category)]
    else:
        df_final1 = df_final_updated.copy()

    df_final_result = df_final1.groupby(['Departure Time', 'Departure Status', 'Fare_Category'])[
        'Forecast'].mean().dropna().reset_index()
    # print(f'Check the value of df_final_result for colors {df_final_result["Fare_Category"].unique()} ')
    df_final_result['colors'] = df_final_result['Fare_Category'].apply(
        lambda x: 1 if x == 'Competitively Priced' else (2 if x == 'Down-selling' else 3))
    # print(f'Check the value of colors {df_final_result.colors.unique()}')

    fig.add_trace(
        go.Scatter(
            x=df_final_result['Departure Time'],
            y=df_final_result['Forecast'],
            marker=dict(color=df_final_result.colors),
            mode='markers',
            # stackgroup='one',
            line=dict(width=0.5, color='rgb(111, 231, 219)'),
            customdata=df_final_result['Fare_Category'],
            hovertemplate='Forecast: %{y} <br>Departure Date: %{x} <br>Fare Category: %{customdata}',
        ))
    fig.add_trace(
        go.Bar(
            x=df_final_result['Departure Time'],
            y=df_final_result['Forecast'],
            marker=dict(color='#1f77b4'),
            hovertemplate='Forecast: %{y} <br>Departure Date: %{x}',
            opacity=0.7
        ))

    fig.update_layout(
        # title="Load Factor Forecast Trend",
        xaxis_title="Departure Date",
        yaxis_title="Load Factor Forecast",
        bargap=0,
        title_x=0.5,
        showlegend=False,
        font=dict(family="Arial", size=15, color="black"),
        plot_bgcolor='rgba(0,0,0,0)',
        #     template='ggplot2',
        yaxis=dict(
            type='linear',
            range=[1, 125],
            ticksuffix='%'))

    return fig


@app.callback(
    Output("ind_min", "figure"),
    [Input("fare_comp", "active_cell"),
     Input("intermediate-value", "data")
     ]
)
def update_industry_min(selected_data, cleaned_data):
    datasets = json.loads(cleaned_data)
    dff = pd.read_json(datasets['df_3'], orient='split')
    df_final_updated = dff.copy(deep=True)

    fig = go.Figure()
    if selected_data is not None and selected_data['row_id'] != 'All' and selected_data['column_id'] != 'All':
        departure_status = selected_data['row_id']
        fare_category = selected_data['column_id']
        df_final1 = df_final_updated[(df_final_updated['Departure Status'] == departure_status) &
                                     (df_final_updated['Fare_Category'] == fare_category)]
    else:
        df_final1 = df_final_updated.copy(deep=True)

    # df_final1.rename(columns={'Fare': 'Selling Fare', 'Fare_Ind': 'Industry Minimum'}, inplace=True)
    df_fare_comp_res = df_final1.groupby(['Departure Time', 'Departure Status', 'Fare_Category']).agg(
        {'Fare': 'min', 'Fare_Ind': 'min', 'Forecast': 'mean'}).dropna().reset_index()
    df_fare_comp_res.rename(columns={'Fare': 'Selling Fare', 'Fare_Ind': 'Industry Minimum'}, inplace=True)

    fig.add_trace(
        go.Scatter(
            x=df_fare_comp_res['Departure Time'],
            y=df_fare_comp_res['Industry Minimum'],
            #         marker=dict(color=df_final_result.colors),
            name='Industry Min',
            mode='markers',
            marker_symbol='diamond',
            marker=dict(size=7, color='brown'),
            hovertemplate='Industry Minimum: %{y} <br>Departure Date: %{x}',
        ))
    fig.add_trace(
        go.Bar(
            x=df_fare_comp_res['Departure Time'],
            y=df_fare_comp_res['Selling Fare'],
            name='Selling Fare',
            marker=dict(color='#1f77b4'),
            hovertemplate='Selling Fare: %{y} <br>Departure Date: %{x}',
            #         marker_color='rgb(158,202,225)',
            #         marker_line_color='rgb(17, 69, 126)',
            opacity=0.7
        ))

    fig.update_layout(
        # title="Industry Minimum Fare Comparison",
        xaxis_title="Departure Date",
        yaxis_title="Fares (in $)",
        title_x=0.5,
        legend_title="Fare Type",
        font=dict(family="Arial", size=15, color="black"),
        plot_bgcolor='rgba(0,0,0,0)',
        legend=dict(
            orientation="h",
            # entrywidth=90,
            font=dict(size=12),
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=0.6))
    #     template='ggplot2')

    return fig


@app.callback(
    Output("fare_comparison", "figure"),
    [Input("fare_comp", "active_cell"),
     Input("forecast-range-slider", "value"),
     Input("price-delta-slider", "value"),
     Input("dtd-range-slider", "value"),
     Input("market-select", "value"),
     Input("sector-select", "value"),
     Input("comp-select", "value"),
     Input("flight-select", "value"),
     Input("comp-flight-select", "value")]
)
def update_fare_comp(selected_data, forecast_range, price_delta, dtd_range, market, sector, comp, flight_no,
                     comp_flight):
    forecast_lower_limit = forecast_range[0]
    forecast_upper_limit = forecast_range[1]
    lower_limit = price_delta[0]
    upper_limit = price_delta[1]
    df_filt_init = calc_filtered_data(dtd_range[0], dtd_range[1], market, sector)
    df_client_details = df_filt_init[(df_filt_init['Carrier'] == "AA") & (df_filt_init['Flight No'].isin(flight_no))]
    df_industry_details = df_filt_init[
        (df_filt_init['Carrier'].isin(comp)) & (df_filt_init['Flight No'].isin(comp_flight))]

    df_ind_gp = df_industry_details.groupby(['Departure Time'])['Fare'].min()
    df_res_details = pd.merge(df_client_details, df_ind_gp, left_on='Departure Time', right_on='Departure Time',
                              suffixes=['', '_Ind'])
    df_res_details['Fare_diff'] = df_res_details['Fare'] - df_res_details['Fare_Ind']
    df_res_details = create_fare_range(df_res_details, forecast_lower_limit, forecast_upper_limit, lower_limit,
                                       upper_limit)

    df_cal_status = df_res_details[['Departure Time', 'Departure Status', 'Fare_Category']].drop_duplicates()

    df_final_updated = pd.concat([df_client_details, df_industry_details])
    df_final_updated = df_final_updated.merge(df_cal_status, left_on='Departure Time', right_on='Departure Time')
    # print(f'Lets check the shape of df_final_updated {df_final_updated.shape}')
    # print(f'Lets check the columns of df_final_updated {df_final_updated.columns}')
    # print(f'Lets check the data of df_final_updated {df_final_updated.head()}')

    if selected_data is not None and selected_data['row_id'] != 'All' and selected_data['column_id'] != 'All':
        departure_status = selected_data['row_id']
        fare_category = selected_data['column_id']
        df_final1 = df_final_updated[(df_final_updated['Departure Status'] == departure_status) &
                                     (df_final_updated['Fare_Category'] == fare_category)]
    else:
        df_final1 = df_final_updated.copy(deep=True)

    df_client_aa = df_final1[df_final1['Carrier'] == "AA"].groupby('Departure Time').agg(
        {'Fare': 'min'}).dropna().reset_index()
    df_client_bb = df_final1[df_final1['Carrier'] == "BB"].groupby('Departure Time').agg(
        {'Fare': 'min'}).dropna().reset_index()
    df_client_cc = df_final1[df_final1['Carrier'] == "CC"].groupby('Departure Time').agg(
        {'Fare': 'min'}).dropna().reset_index()
    df_client_dd = df_final1[df_final1['Carrier'] == "DD"].groupby('Departure Time').agg(
        {'Fare': 'min'}).dropna().reset_index()

    fig = go.Figure()

    fig.add_trace(
        go.Bar(
            x=df_client_aa['Departure Time'],
            y=df_client_aa['Fare'],
            name="Published Fare - AA",
            # marker=dict(color='#1f77b4'),
            marker_color='rgb(158,202,225)',
            marker_line_color='rgb(17, 69, 126)',
            marker_line_width=0.75,
            opacity=0.7
        ))

    fig.add_trace(
        go.Scatter(
            x=df_client_bb['Departure Time'],
            y=df_client_bb['Fare'],
            name="Published Fare - BB",
            marker=dict(color='red'),
            marker_symbol='circle',
            # mode='lines+markers',
            mode='markers',
            # marker={'size':1},
            # line = dict(color='firebrick', width=3)
        ))

    fig.add_trace(
        go.Scatter(
            x=df_client_cc['Departure Time'],
            y=df_client_cc['Fare'],
            name="Published Fare - CC",
            marker=dict(color='blue'),
            marker_symbol='triangle-up',
            # mode='lines+markers',
            mode='markers',
            # marker={'size':1},
            # line = dict(color='firebrick', width=3)
        ))

    fig.add_trace(
        go.Scatter(
            x=df_client_dd['Departure Time'],
            y=df_client_dd['Fare'],
            name="Published Fare - DD",
            marker=dict(color='purple'),
            marker_symbol='star',
            # mode='lines+markers',
            mode='markers',
            # marker={'size':1},
            # line = dict(color='firebrick', width=3)
        ))

    fig.update_layout(
        # title="Industry Fare Comparison",
        title_x=0.5,
        xaxis_title="Departure Date",
        yaxis_title="Fares (in $)",
        legend_title="Published Fare by Carrier",
        font=dict(family="Arial", size=15, color="black"),
        plot_bgcolor='rgba(0,0,0,0)',
        #     template='ggplot2',
        legend=dict(
            orientation="h",
            # entrywidth=90,
            font=dict(size=12),
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=0.75))

    return fig


@app.callback(
    Output("fare_freq_comparison", "figure"),
    [
        Input("dtd-range-slider", "value"),
        Input("market-select", "value"),
        Input("sector-select", "value"),
        Input("comp-select", "value"),
        Input("flight-select", "value"),
        Input("comp-flight-select", "value")
    ]
)
def comp_fare_frequency(dtd_range, market, sector, comp, flight_no, comp_flight):
    flight_list = flight_no + comp_flight
    comp.append("AA")
    df_filt_init = calc_filtered_data(dtd_range[0], dtd_range[1], market, sector)
    df_filt_init_final = df_filt_init[
        (df_filt_init['Carrier'].isin(comp)) & (df_filt_init['Flight No'].isin(flight_list))]

    df_fare_comp_copy = df_filt_init_final.copy(deep=True)
    df_fare_comp_copy.rename(columns={'Fare': 'Selling Fare'}, inplace=True)
    fare_levels = df_fare_comp_copy['Selling Fare'].unique()
    fare_levels.sort()
    fare_levels_1 = fare_levels.astype('str')

    fare_categories = CategoricalDtype(fare_levels_1, ordered=True)
    df_fare_comp_copy['Selling Fare'] = df_fare_comp_copy['Selling Fare'].astype(str)
    df_fare_comp_copy['Selling Fare'] = df_fare_comp_copy['Selling Fare'].astype(fare_categories)

    df_grouped_fares = df_fare_comp_copy.groupby(['Selling Fare', 'Carrier']).agg(
        Departure_Count=('Selling Fare', 'count')).reset_index().sort_values(by='Selling Fare')
    fig = px.bar(df_grouped_fares, x='Selling Fare', y='Departure_Count', color='Carrier', barmode='group',
                 template='ggplot2',
                 # title="Fare Frequency Comparison"
                 )
    fig.update_layout(title_font_family="Arial", font_color="black", font=dict(size=15),
                      legend=dict(
                          orientation="h",
                          # entrywidth=90,
                          font=dict(size=12),
                          yanchor="bottom",
                          y=1.02,
                          xanchor="right",
                          x=0.60)
                      )
    fig.update_traces(width=0.7)
    return fig


# Run the server
if __name__ == "__main__":
    app.run_server(debug=True)
