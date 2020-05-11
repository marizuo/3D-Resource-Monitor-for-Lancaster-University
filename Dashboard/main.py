import dash
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
import dash_table
import datetime as dt
import copy
import dash_daq as daq
import time
import visdcc
import os
import plotly.express as px
from plotly.subplots import make_subplots
import shutil
from dash.dependencies import Input, Output, State
import plotly.graph_objects as go
import math
import dash_auth
import numpy as np
from flask_caching import Cache





buildings = pd.read_csv('buildings.csv')    # Loads all building metadata such as building code, building name, building type, internal area, year of build.
full_consumption_data = pd.read_csv('all_1hrly_combined_apr.csv')   # the processed consumption data
full_consumption_data['timestamp'] = pd.to_datetime(full_consumption_data['timestamp']) # to datetime format
full_wifi_data = pd.read_csv('wifi_data_fin2.csv')  #processed wifi data 
full_wifi_data['time'] = pd.to_datetime(full_wifi_data['time'])



app = dash.Dash(
    __name__,)
cache = Cache(app.server, config={  # Initialises the Cache! Used to memoize the compute-intensive functions so that they are not repeatedly ran.
    'CACHE_TYPE': 'simple',
})




modeColor2 = '#d8d8d8'  #set the background colour for graphs
modeColor = "#292b2c"   #set the text colour for graphs




def unixTimeMillis(dt2):  # https://stackoverflow.com/questions/51063191/date-slider-with-plotly-dash-does-not-work
    ''' Convert datetime to unix timestamp '''
    return int(time.mktime(dt2.timetuple()))


def unixToDatetime(unix): # https://stackoverflow.com/questions/51063191/date-slider-with-plotly-dash-does-not-work
    ''' Convert unix timestamp to datetime. '''
    return pd.to_datetime(unix, unit='s')



#The app layout describes the layout of the dashboard. The classnames are related to the stylesheet here: https://codepen.io/chriddyp/pen/bWLwgP in which certain classNames are styled. 
# EG a class name 'ten columns' indicates to the CSS that the element should span 10 columns. Row indicates inline-block instead of normal block
# Heavily influenced by the Dash Gallery's New York Oil&Gas dashboard  https://github.com/plotly/dash-oil-and-gas-demo
app.layout = html.Div(
    id="mainContainer",
    style={"display": "flex",
           "flex-direction": "column"},
    children=[
        dcc.Store(id='aggregate_data'), # Invisible data store that stores the aggregate consumption values for display in the infoboxes
        html.Div(
            className="row",
            style={"max-height": "200px"},
            children=[
                html.Div(
                    className="six columns row",
                    children=[
                        html.Div(
                            className='row',
                            children=[
                                html.H2(
                                    "Lancaster University Resource Monitor"),
                                html.
                                P("Campus Map with individual building resource usage data on-click, able to filter map by GIA, Year of Build. The main slider allows you to filter the data by the period which you'd like to see, eg specific term. Before colouring by resource, please click 'update batchtable' button in bottom left. Any suggestions would be greatly appreciated, please do feel free to email me at m.onuoha@lancaster.ac.uk"),
                            ]),
                    ],
                ),
                html.Div( 
                    className="row container-display",  
                    children=[
                        html.Div(
                            [
                                html.H6(
                                    id="building_num_text",
                                    className="info_text"),
                                html.H4("Buildings"),
                            ],
                            id="wells",
                            className="mini_container"),
                        html.Div(
                            [
                                html.H6(id="elecText", className="info_text"),
                                html.H4("Electricity used"),
                            ],
                            id="wells1",
                            className="mini_container"),
                        html.Div(
                            [
                                html.H6(id="heatText", className="info_text"),
                                html.H4("Heat energy used"),
                            ],
                            id="wells5",
                            className="mini_container"),
                        html.Div(
                            [
                                html.H6(id="waterText", className="info_text"),
                                html.H4("Water used"),
                            ],
                            id="wells2",
                            className="mini_container"),
                        html.Div(
                            [
                                html.H6(id="gasText", className="info_text"),
                                html.H4("Gas used"),
                            ],
                            id="wells3",
                            className="mini_container"),
                    ],
                ),
            ],
        ),
        html.Div(
            children=[
                html.Div(children=[
                    html.Div(
                        className="row",
                        children=[
                            html.Div(
                                id='mainSettings', # Main Settings encompasses the main two dropdowns (Cesium map options dropdown and the building specific dropdown)
                                className="three columns",
                                children=[
                                    html.P(
                                        'Select Cesium Map styling',
                                        className="control_label"),
                                    dcc.Dropdown(
                                        id='cesium_dropdown',
                                        options=[
                                            {
                                                'label': 'Filter Buildings',
                                                'value': 'filters'
                                            },
                                            {
                                                'label': 'Colour by Height',
                                                'value': 'height'
                                            },
                                            {
                                                'label': 'Colour by Usage',
                                                'value': 'energy'
                                            },
                                        ],
                                        value='filters'), #sets default value as filters
                                    html.Br(),
                                    dcc.Dropdown(
                                        id='building_specific_dropdown',
                                        options=[
                                            {
                                                'label':
                                                'Building-specific graphs',
                                                'value':
                                                'individualBuilding'
                                            },
                                            {
                                                'label':
                                                'Campus overview graphs',
                                                'value': 'campusOverview'
                                            },
                                        ],
                                        value='individualBuilding'),
                                ]),
                            html.Div(
                                id='usage_settings', # Usage_settings div is only visible when 'Colour by Usage' is selected in the main settings
                                className='three columns ',
                                children=[
                                    html.Div(
                                        className="",
                                        children=[
                                            html.P(
                                                'Select Consumption Type',
                                                className="control_label"),
                                            dcc.Dropdown(   # Dropdown where user selects which type of consumption (or occupancy) the map should be coloured by
                                                id='usage_type',
                                                options=[
                                                    {
                                                        'label': 'Electricity',
                                                        'value': 'electricity'
                                                    },
                                                    {
                                                        'label': 'Water',
                                                        'value': 'water'
                                                    },
                                                    {
                                                        'label': 'Gas',
                                                        'value': 'gas'
                                                    },
                                                    {
                                                        'label': 'Heat',
                                                        'value': 'heat'
                                                    },
                                                    {
                                                        'label': 'Occupancy',
                                                        'value': 'occupancy'
                                                    },
                                                ],
                                                value='electricity',
                                                style={"margin-bottom": "8px"},
                                            ),
                                        ]),
                                    dcc.Dropdown(
                                        id='usage_area', # Dropdown where user selects if building efficiency should be displayed by calculating consumption per building area
                                        options=[
                                            {
                                                'label': 'Absolute Usage',
                                                'value': 'absolute'
                                            },
                                            {
                                                'label':
                                                'Usage per m2 (Gross Internal Area)',
                                                'value':
                                                'pergia'
                                            },
                                        ],
                                        value='absolute',
                                    ),
                                ]),
                            html.Div(
                                id='filterSettings',
                                className='nine columns row',
                                children=[
                                    html.Div(
                                        className="three columns",
                                        children=[
                                            html.P(
                                                'Filter by Building Type',
                                                className="control_label"),
                                            dcc.Dropdown(
                                                id='building_type',
                                                options=[{
                                                    'label': 'All ',
                                                    'value': 'all'
                                                }, {
                                                    'label': 'Residential',
                                                    'value': 'residential'
                                                }, {
                                                    'label': 'Academic',
                                                    'value': 'university'
                                                }],
                                                value='all',
                                                className="dcc_control"),
                                        ]),
                                    html.Div(
                                        className="four columns",
                                        children=[
                                            html.P(
                                                'Year of Build',
                                                className="control_label"),
                                            dcc.RangeSlider(
                                                id='year_slider',   #Year of Build Slider to allow for filtering based on building year of build
                                                min=1950,
                                                max=2020,
                                                value=[1950, 2020],
                                                marks={
                                                    1950: {
                                                        'label': '1950'
                                                    },
                                                    1960: {
                                                        'label': '1960'
                                                    },
                                                    1970: {
                                                        'label': '1970'
                                                    },
                                                    1980: {
                                                        'label': '1980'
                                                    },
                                                    1990: {
                                                        'label': '1990'
                                                    },
                                                    2000: {
                                                        'label': '2000'
                                                    },
                                                    2010: {
                                                        'label': '2010'
                                                    },
                                                    2020: {
                                                        'label': '2020'
                                                    },
                                                },
                                                className="small_slider"),
                                        ],
                                        style={
                                            "flex": "1" # always grow flex 
                                        }),
                                    html.Div(
                                        className="four columns",
                                        children=[
                                            html.P(
                                                'Total Gross internal Area', # GIA slider to filter the buildings by
                                                className="control_label"),
                                            dcc.RangeSlider(
                                                id='GIA_slider',
                                                min=0,
                                                max=20000,
                                                marks={
                                                    0: {
                                                        'label': '0'
                                                    },
                                                    5000: {
                                                        'label': '5000'
                                                    },
                                                    10000: {
                                                        'label': '10000'
                                                    },
                                                    15000: {
                                                        'label': '15000'
                                                    },
                                                    20000: {
                                                        'label': '20000'
                                                    },
                                                },
                                                value=[0, 20000], # Initailly sets range to all values
                                                className="small_slider"),
                                        ],
                                        style={
                                            "flex": "1" # always grow flex
                                        }),
                                ]),
                        ]),
                ]),
            ],
        ),
        html.Div([
            html.Div(
                id='cesium_slider_text', # Empty div which will be updated by a callback to display the current dates that the user has selected on the time slider
                style={
                    "padding-top": "25px",
                    "text-align": "center"
                }),
            dcc.RangeSlider(  # DATETIME RANGE SLIDERS do not exist in Dash, so workaround used based on https://stackoverflow.com/questions/51063191/date-slider-with-plotly-dash-does-not-work
                id='cesium_slider',
                min=unixTimeMillis(full_consumption_data['timestamp'].unique().min()),
                max=unixTimeMillis(full_consumption_data['timestamp'].unique().max()),
                value=(unixTimeMillis(full_consumption_data['timestamp'].unique().min()),
                       unixTimeMillis(full_consumption_data['timestamp'].unique().max())),
                marks={
                    1543622400: { # Manual labels for each month in the dataset. Previously used stackoverflow method mentioned above but iterating through whole dataset for marks is too computationally heavy. Other options need exploring
                        'label': '12-2018'
                    },
                    1546300800: {
                        'label': '01-2019'
                    },
                    1548979200: {
                        'label': '02-2019'
                    },
                    1551398400: {
                        'label': '03-2019'
                    },
                    1554076800: {
                        'label': '04-2019'
                    },
                    1556668800: {
                        'label': '05-2019'
                    },
                    1559343600: {
                        'label': '06-2019'
                    },
                    1561939200: {
                        'label': '07-2019'
                    },
                    1564617600: {
                        'label': '08-2019'
                    },
                    1567296000: {
                        'label': '09-2019'
                    },
                    1569888000: {
                        'label': '10-2019'
                    },
                    1572566400: {
                        'label': '11-2019'
                    },
                    1575158400: {
                        'label': '12-2019'
                    },
                    1577836800: {
                        'label': '01-2020'
                    },
                    1580515200: {
                        'label': '02-2020'
                    },
                },
                step=3600, # Only allows user to select on the hour (since it is hourly data) 
                included=True)
        ], ),
        html.Br(),
        html.Div(
            id='mapandtrends', # Wrapper  for the cesium map and the trend graphs
            style={"height": "510px"},
            className='row',
            children=[
                html.Div(
                    style={"position": "relative"},
                    className="eight columns",
                    children=[
                        html.Div( # This is the Cesium map div - it is empty until the Javascript is run and the Cesium browser is appended to this div.
                            id='CesiumMap',
                            style={"height": "510px"},
                            className=""),
                        html.Div( # This is the Info Table for each building. Once again, the Javascript code appends the building metadata onto this Div when a user hovers over a building
                            'Building Name',
                            id='buildName',
                            className="map_container",
                            style={
                                "z-index": "1" # Make sure the building data is displayed OVER the map, not behind
                            }),
                        html.Div( 
                            id='Key', # This is a wrapper which contains the 5 keys (very low, low etc) and the colours of each. The consumption range for each key is appended on via a callback.
                            className="map_container",
                            style={
                                "z-index": "1", # Make sure the key is displayed OVER the map
                                "position": "absolute", # positioned at top right of cesium map
                                "top": "7px",
                                "right": "30px"
                            },
                            children=[
                                html.Div(
                                    className="row",
                                    children=[
                                        html.Div(
                                            id='veryhigh_key',
                                            style={
                                                "border-radius": "0",
                                                "display": "inline-block",
                                                "margin-right": "5px",
                                                "margin-top": "2px",
                                                "width": "15px",
                                                "height": "15px",
                                                "background-color": "red"
                                            }),
                                        html.Div(id='veryhigh_text'),
                                    ]),
                                html.Div(
                                    className="row",
                                    children=[
                                        html.Div(
                                            id='high_key',
                                            style={
                                                "border-radius": "0",
                                                "display": "inline-block",
                                                "margin-right": "5px",
                                                "margin-top": "2px",
                                                "width": "15px",
                                                "height": "15px",
                                                "background-color": "#f56d00"
                                            }),
                                        html.Div(id='high_text'),
                                    ]),
                                html.Div(
                                    className="row",
                                    children=[
                                        html.Div(
                                            id='medium_key',
                                            style={
                                                "border-radius": "0",
                                                "display": "inline-block",
                                                "margin-right": "5px",
                                                "margin-top": "2px",
                                                "width": "15px",
                                                "height": "15px",
                                                "background-color": "#d6a700"
                                            }),
                                        html.Div(id='medium_text'),
                                    ]),
                                html.Div(
                                    className="row",
                                    children=[
                                        html.Div(
                                            id='low_key',
                                            style={
                                                "border-radius": "0",
                                                "display": "inline-block",
                                                "margin-right": "5px",
                                                "margin-top": "2px",
                                                "width": "15px",
                                                "height": "15px",
                                                "background-color": "#a0d600"
                                            }),
                                        html.Div(id='low_text'),
                                    ]),
                                html.Div(
                                    className="row",
                                    children=[
                                        html.Div(
                                            id='verylow_key',
                                            style={
                                                "border-radius": "0",
                                                "display": "inline-block",
                                                "margin-right": "5px",
                                                "margin-top": "2px",
                                                "width": "15px",
                                                "height": "15px",
                                                "background-color": "#00ff05"
                                            }),
                                        html.Div(id='verylow_text'),
                                    ]),
                            ]),
                    ]),
                html.Div(
                    className='',
                    style={"flex": "1"},
                    children=[
                        dcc.Graph(id='trendgraphs',), # The subplots that display hourly, day of week, monthly trends for each building.
                    ]),
            ]),
        html.Div(
            style={"max-height": "1800px"},
            className="row",
            children=[
                html.Div(
                    [
                        html.Div(
                            className="",
                            children=[dcc.Graph(id='individual_graph')]), # The subplots that display historical consumption data for buildings selected in the map
                    ],
                    className="twelve columns pretty_container",
                    style={"max-height": "inherit"},
                ),
            ],
        ),
        html.Script(id='aa'),
        html.Script(id='ab'), # Empty elements that are used to empty callbacks into.
        
        #The following Run_JS elements are used by Callbacks to run javascript in the client browser. Callbacks can listen for events in each of these elements.
        visdcc.Run_js(id='getCesiumBuildingNum', event='MC078'),
        visdcc.Run_js(id='getBatchTableInfo'),
        visdcc.Run_js(id='changeColorJS'),
        visdcc.Run_js(id='loadBatchValuesToJS'),
        visdcc.Run_js(id='colorBy'),
        visdcc.Run_js(id='filtersJS'),

        visdcc.Run_js(
            id='intialiseCesium', # This initialises the Cesium client and appends it to the CesiumMap div created earlier called CesiumMap
                                  # Cesium programming tremendously helped by Sandbox examples such as Feature Picking found herehttps://sandcastle.cesium.com/index.html?src=3D%20Tiles%20Feature%20Picking.html
            run='''
    Cesium.Ion.defaultAccessToken = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJqdGkiOiI2Mzc2NGE2Yi02NTQxLTRmNDktYTA3Ni05YjcwZTJkMGI2ZjQiLCJpZCI6MTgzOTksInNjb3BlcyI6WyJhc3IiLCJnYyJdLCJpYXQiOjE1NzM3NDAwMzN9.dFNI-JvVuWkfR-8xDw41H3YxElw-777cApxdglW2_EU';
    viewer = new Cesium.Viewer('CesiumMap', {animation : false, selectionIndicator : false, baseLayerPicker : false,fullscreenButton : false,geocoder : false,homeButton : false,infoBox : false,sceneModePicker : false,timeline : false,navigationHelpButton : false}); // Disables most Cesium widgets as really only map is needed
    var imageryLayers = viewer.imageryLayers;
    imageryLayers.addImageryProvider(new Cesium.ArcGisMapServerImageryProvider({
    url : 'https://services.arcgisonline.com/arcgis/rest/services/Canvas/World_Dark_Gray_Base/MapServer/' // Imports the grey baselayer, ideal for colouring features as the colours pop out.
    }));
    tileset = viewer.scene.primitives.add(new Cesium.Cesium3DTileset({
    url : 'https://storage.googleapis.com/tilesetcesium/tileset.json',})); // Imports the tileset hosted on Google Storage
    viewer.zoomTo(tileset, new Cesium.HeadingPitchRange(1.5, -0.5, 1400)); // Zoom to the tileset (campus)
    viewer.scene.globe.enableLighting = true;
    viewer.clock.currentTime =  Cesium.JulianDate.fromIso8601("20190707T180000+0100"); 
    
    
    
    function getCodes(tile) {  // get the matching Batch ID for each Building Code and store it in the batches array (batches is declared in assets/alert.js as it must be global)
    content = tile.content;  // Get tile content
    var featuresLength = content.featuresLength; // Finds how many tiles in tileset
    for (let batchId = 0; batchId < featuresLength; batchId++) { // Iterate through all tiles  
    var code = content.getFeature(batchId).getProperty('Property code_y'); // Get Building Code 
    var combined_values = [batchId, code]; // Add BatchID and Building Code as an array. 
    batches.push(combined_values); // Add combined values to batches array
    }
    console.log(batches);
	tileset.tileVisible.removeEventListener(getCodes); // Once codes retrieved, no longer need to listen for tileVisible
}

tileset.tileVisible.addEventListener(getCodes); // Only get codes once tiles are loaded




colourByHeight = function() {

tileset.style = new Cesium.Cesium3DTileStyle({      // Initial style to clear all stylings
            color: {
            conditions: [
                ['${Height} >= 0', 'color("#F8F8F8")'],
                ['true', 'rgb(127, 59, 8)']
            ]
        }
});

tileset.style = new Cesium.Cesium3DTileStyle({
            color: {
            conditions: [       // Hard coded styling of buildings based on Height attribute
                ['${Height} >= 35', 'rgba(45, 0, 75, 0.5)'],
                ['${Height} >= 30', 'rgb(102, 71, 151)'],
                ['${Height} >= 25', 'rgb(170, 162, 204)'],
                ['${Height} >= 20', 'rgb(224, 226, 238)'],
                ['${Height} >= 15', 'rgb(252, 230, 200)'],
                ['${Height} >= 10', 'rgb(248, 176, 87)'],
                ['${Height} >= 5', 'rgb(198, 106, 11)'],
                ['true', 'rgb(127, 59, 8)']
            ]
        }
});

}

showFilters = function(low_g, up_g, low_y, up_y, typebuilding) { // Function to only show the filtered buildings on the Cesium map. Filter parameters are GIA (g), YOB (y) and typeBuilding which is residential, university or all
console.log(typebuilding);
if (typebuilding == 'residential') { // This had to be split up into residential, university and all because Cesium could not read typebuilding when it was set in the defines section.
tileset.style = new Cesium.Cesium3DTileStyle({
			  defines : { // define the variables that we will refer to in the show conditions section 
            GIA_low : low_g, 
			GIA_up : up_g,
			YOB_low : low_y,
			YOB_up : up_y,
        },
		show : '((${Total_GIA} >= ${GIA_low}) && (${Total_GIA} <= ${GIA_up})) && ((${year_of_build} >= ${YOB_low}) && (${year_of_build} <= ${YOB_up})) && (${building_type} === "residential")' // ONLY SHOW buildings where building's total_gia attribute is inbetween the upper and lower bands.. same with YOB. Only show buildings with building_type of residential
});
}
if (typebuilding == 'university') {
tileset.style = new Cesium.Cesium3DTileStyle({
			  defines : {
            GIA_low : low_g,
			GIA_up : up_g,
			YOB_low : low_y,
			YOB_up : up_y,
        },
		show : '((${Total_GIA} >= ${GIA_low}) && (${Total_GIA} <= ${GIA_up})) && ((${year_of_build} >= ${YOB_low}) && (${year_of_build} <= ${YOB_up})) && (${building_type} === "university")' // Same filters but only university buildings
});
}
if (typebuilding == 'all') {
tileset.style = new Cesium.Cesium3DTileStyle({
			  defines : {
            GIA_low : low_g,
			GIA_up : up_g,
			YOB_low : low_y,
			YOB_up : up_y,
        },
		show : '((${Total_GIA} >= ${GIA_low}) && (${Total_GIA} <= ${GIA_up})) && ((${year_of_build} >= ${YOB_low}) && (${year_of_build} <= ${YOB_up}))' // Same filters but without the building type filter
});
}


}


// FOLLOWING SECTION TAKEN FROM FEATURE PICKING EXAMPLE https://sandcastle.cesium.com/index.html?src=3D%20Tiles%20Feature%20Picking.html
    
var nameOverlay = document.getElementById('buildName'); // Div was declared in the app.layout, now the initial table with building data is being appended onto it so that it overlays the Cesium Map
nameOverlay.style.position = 'absolute';
nameOverlay.style.top = '7px';
nameOverlay.style.left = '10px';
nameOverlay.style['pointer-events'] = 'none';
nameOverlay.style.padding = '4px';


nameOverlay.innerHTML = '<table><tbody>' +  // Empty table at first
                                     '<tr><th>Building Name</th><td>' +
                                     '<tr><th>Building ID</th><td>' +
                                     '<tr><th>Floors</th><td>' +
                                     '<tr><th>Gross Internal Area</th><td>' + 
                                     '<tr><th>Year of Build</th><td>' + 
                                     '<tr><th>Usage</th><td>' +
                                     '</tbody></table>';

// Information about the currently selected feature
var selected = {
    feature: undefined,
    originalColor: new Cesium.Color()
};

// An entity object which will hold info about the currently selected feature for infobox display
var selectedEntity = new Cesium.Entity();

// Get default left click handler for when a feature is not picked on left click
var clickHandler = viewer.screenSpaceEventHandler.getInputAction(Cesium.ScreenSpaceEventType.LEFT_CLICK);

// If silhouettes are supported, silhouette features in blue on mouse over and silhouette green on mouse click.
// If silhouettes are not supported, change the feature color to yellow on mouse over and green on mouse click.
if (Cesium.PostProcessStageLibrary.isSilhouetteSupported(viewer.scene)) {
    // Silhouettes are supported
    var silhouetteBlue = Cesium.PostProcessStageLibrary.createEdgeDetectionStage();
    silhouetteBlue.uniforms.color = Cesium.Color.BLUE;
    silhouetteBlue.uniforms.length = 0.01;
    silhouetteBlue.selected = [];

    var silhouetteGreen = Cesium.PostProcessStageLibrary.createEdgeDetectionStage();
    silhouetteGreen.uniforms.color = Cesium.Color.LIME;
    silhouetteGreen.uniforms.length = 0.01;
    silhouetteGreen.selected = [];

    viewer.scene.postProcessStages.add(Cesium.PostProcessStageLibrary.createSilhouetteStage([silhouetteBlue, silhouetteGreen]));

    // Silhouette a feature blue on hover.
    viewer.screenSpaceEventHandler.setInputAction(function onMouseMove(movement) {
        // If a feature was previously highlighted, undo the highlight
        silhouetteBlue.selected = [];

        // Pick a new feature
        var pickedFeature = viewer.scene.pick(movement.endPosition);
        if (!Cesium.defined(pickedFeature)) {
           
            return;
        }

        // A feature was picked, so show it's overlay content
        nameOverlay.style.display = 'inline';
        var name = pickedFeature.getProperty('name');
        if (!Cesium.defined(name)) {
            name = pickedFeature.getProperty('id');
        }
        nameOverlay.innerHTML = '<table><tbody>' +  // ACTUAL Building data table - grabs attributes such as building ID, GIA, year of build and displays them in a table overlayed on the Cesium map when a mouse hovers on any building
                                     '<tr><th>Building Name</th><td>' + pickedFeature.getProperty('Property Name') +
                                     '<tr><th>Building ID</th><td>' + pickedFeature.getProperty('Property code_y') +
                                     '<tr><th>Floors</th><td>' + pickedFeature.getProperty('Floor') + '</td></tr>' +
                                     '<tr><th>Gross Internal Area</th><td>' + pickedFeature.getProperty('Total_GIA') + ' m2</td></tr>' +
                                     '<tr><th>Year of Build</th><td>' + pickedFeature.getProperty('year_of_build') + '</td></tr>' +
                                     '<tr><th>Usage</th><td>' + pickedFeature.getProperty('power') + '</td></tr>' +
                                     '</tbody></table>';

        // Highlight the feature if it's not already selected.
        if (pickedFeature !== selected.feature) {
            silhouetteBlue.selected = [pickedFeature];
        }
    }, Cesium.ScreenSpaceEventType.MOUSE_MOVE);

    // Silhouette a feature on selection and show metadata in the InfoBox.
    viewer.screenSpaceEventHandler.setInputAction(function onLeftClick(movement) {
        // If a feature was previously selected, undo the highlight
        silhouetteGreen.selected = [];

        // Pick a new feature
        var pickedFeature = viewer.scene.pick(movement.position);
        if (!Cesium.defined(pickedFeature)) {
            clickHandler(movement);
            return;
        }

        // Select the feature if it's not already selected
        if (silhouetteGreen.selected[0] === pickedFeature) {
            return;
        }

        // Save the selected feature's original color
        var highlightedFeature = silhouetteBlue.selected[0];
        if (pickedFeature === highlightedFeature) {
            silhouetteBlue.selected = [];
        }

        // Highlight newly selected feature
        silhouetteGreen.selected = [pickedFeature];

        // Set feature infobox description
        var featureName = pickedFeature.getProperty('name');
        selectedEntity.name = featureName;
        selectedEntity.description = 'Loading <div class="cesium-infoBox-loading"></div>';
        viewer.selectedEntity = selectedEntity;
        buildingCodeSelected = pickedFeature.getProperty('Property code_y'); // STORE THE BUILDING CODE SELECTED AS A VARIABLE


    }, Cesium.ScreenSpaceEventType.LEFT_CLICK);
} else {
    // Silhouettes are not supported. Instead, change the feature color.

    // Information about the currently highlighted feature
    var highlighted = {
        feature : undefined,
        originalColor : new Cesium.Color()
    };

    // Color a feature yellow on hover.
    viewer.screenSpaceEventHandler.setInputAction(function onMouseMove(movement) {
        // If a feature was previously highlighted, undo the highlight
        if (Cesium.defined(highlighted.feature)) {
            highlighted.feature.color = highlighted.originalColor;
            highlighted.feature = undefined;
        }
        // Pick a new feature
        var pickedFeature = viewer.scene.pick(movement.endPosition);
        if (!Cesium.defined(pickedFeature)) {
        
            return;
        }
        // A feature was picked, so show it's overlay content
        nameOverlay.style.display = 'block';
        //nameOverlay.style.bottom = viewer.canvas.clientHeight - movement.endPosition.y + 'px';
       // nameOverlay.style.left = movement.endPosition.x + 'px';
        var name = pickedFeature.getProperty('name');
        if (!Cesium.defined(name)) {
            name = pickedFeature.getProperty('id');
        }
        nameOverlay.textContent = name;
        // Highlight the feature if it's not already selected.
        if (pickedFeature !== selected.feature) {
            highlighted.feature = pickedFeature;
            Cesium.Color.clone(pickedFeature.color, highlighted.originalColor);
            pickedFeature.color = Cesium.Color.YELLOW;
        }
    }, Cesium.ScreenSpaceEventType.MOUSE_MOVE);

    // Color a feature on selection and show metadata in the InfoBox.
    viewer.screenSpaceEventHandler.setInputAction(function onLeftClick(movement) {
        // If a feature was previously selected, undo the highlight
        if (Cesium.defined(selected.feature)) {
            selected.feature.color = selected.originalColor;
            selected.feature = undefined;
        }
        // Pick a new feature
        var pickedFeature = viewer.scene.pick(movement.position);
        if (!Cesium.defined(pickedFeature)) {
            clickHandler(movement);
            return;
        }
        // Select the feature if it's not already selected
        if (selected.feature === pickedFeature) {
            return;
        }
        selected.feature = pickedFeature;
        // Save the selected feature's original color
        if (pickedFeature === highlighted.feature) {
            Cesium.Color.clone(highlighted.originalColor, selected.originalColor);
            highlighted.feature = undefined;
        } else {
            Cesium.Color.clone(pickedFeature.color, selected.originalColor);
        }

    }, Cesium.ScreenSpaceEventType.LEFT_CLICK);
}

    '''),
        html.Div(
            className='row',
            children=[
                html.Div(className="one column"),  # Column for spacing
                html.Div(
                    className='ten columns pretty_container',
                    children=[
                        dcc.Graph(id='tree'),  # Tree Graph in a 10-column wide div
                    ]),
                html.Div(className="one column"),  # Column for spacing
            ]),
            
        html.Button(
            'Update batchTable', # This button loads all of the client's buildings so that the Dash environment can then colour by individual buildings (check callback)
            id='batchButton',
            style={
                "width": "100px",
                "height": "100px"
            }
        ),  
    ])


def unixToDatetime(unix):  # This function converts unix timestamps into datetime timestamps
    return pd.to_datetime(unix, unit='s')


millnames = ['', ' Thsd.', ' Mln.', ' Bln.',
             ' Trln.']  # Abbreviations for thousand, million etcetera. Used by human_format function


def human_format(n):  # This function converts large numbers into human readable numbers. EG '1000000' into '1 Mln.' Taken from https://stackoverflow.com/questions/3154460/python-human-readable-large-numbers/7670181
    n = float(n)
    millidx = max(
        0,
        min(
            len(millnames) - 1,
            int(math.floor(0 if n == 0 else math.log10(abs(n)) / 3))))

    return '{:.0f}{}'.format(n / 10**(3 * millidx), millnames[millidx])


@app.callback(Output('getBatchTableInfo', 'run'), [Input('batchButton', 'n_clicks')])
def getBatchInfo(click):     # This function grabs the Batch/Building Code JS array called 'batches' that was created in the initial runJS CesiumJS module and raises it as an event. The callback below listens for it. 
    return '''
        setProps({ 
         'event': batches  
        })
    '''


batchTable = pd.DataFrame(columns=['batchid', 'buildingNum']) # initialises the batchtable dataframe for use below


@app.callback(Output('ab', 'title'), [Input('getBatchTableInfo', 'event')]) # This callback takes the batches array and turns it into a DataFrame. Now the BatchID is matched to Building Code and available in Python environment as batchTable. output is not important and is ignored
def setBatchTable(array):
    global batchTable
    batchTable = pd.DataFrame(columns=['batchid', 'buildingNum'])
    for i in range(len(array)): # for every item in array, appends the values into the DataFrame. (Batches is an array with arrays inside. Each array contains a batch id and building num) (Eg [[0, 'MC078'], [1, 'MC207']])
        batchTable = batchTable.append(pd.Series(array[i], index=batchTable.columns), ignore_index=True)    # we now have a dataframe in python with the batchid and building code of each building


@app.callback(Output('getCesiumBuildingNum', 'run'), [Input('CesiumMap', 'n_clicks')])
def getBuilding(click): # This callback triggers each time the Cesium Map is clicked - it gets the building selected (its stored as JS) and raises an event with the code as the content. Functions will lsiten to this event if they are building-specific functions such as the trendgraphs
    return '''
    console.log(a);
        setProps({ 
         'event': buildingCodeSelected
        })
    '''




filtered_buildings = pd.DataFrame()


@app.callback(
    Output('aggregate_data', 'data'), [
        Input('cesium_slider', 'value'),
        Input('building_type', 'value'),
        Input('GIA_slider', 'value'),
        Input('year_slider', 'value')
    ])
@cache.memoize()
def update_consumption_text(cesium_slider, building_type, GIA_slider, year_slider):
    global filtered_buildings
    periodSelected_lower = pd.to_datetime(cesium_slider[0], unit='s')   # Due to the workaround datetime rangeslider, the times selected are in unix and must first be converted to pandas datetime
    periodSelected_upper = pd.to_datetime(cesium_slider[1], unit='s')

    
    buildings2 = buildings[     # Creates a new DataFrame with only the buildings that match the filters. ie Year of Build must be bigger than lowest filter point, smaller than highest./
        (pd.to_datetime(buildings['Year of Build'], format='%Y') > dt.datetime(
            year_slider[0], 1, 1))
        & (pd.to_datetime(buildings['Year of Build'], format='%Y') <
           dt.datetime(year_slider[1], 1, 1)) &
        (buildings['Total GIA'] > GIA_slider[0]) &
        (buildings['Total GIA'] < GIA_slider[1])]
        
    if (building_type != 'all'):
        buildings2 = buildings[     # Creates same new DataFrame but also filters by building type (residential vs university)
            (buildings['building'] == building_type)
            & (pd.to_datetime(buildings['Year of Build'], format='%Y') >
               dt.datetime(year_slider[0], 1, 1)) &
            (pd.to_datetime(buildings['Year of Build'], format='%Y') <
             dt.datetime(year_slider[1], 1, 1)) &
            (buildings['Total GIA'] > GIA_slider[0]) &
            (buildings['Total GIA'] < GIA_slider[1])]
            
    num_buildings = buildings2.shape # Gets number of buildings currently meeting filters
    filtered_buildings = buildings2
    filtered_df = full_consumption_data[full_consumption_data['building'].isin(buildings2['Property code_y']) &   #Filtered DF is where the actual consumption data is extracted but only for the buildings which are within the filters.
                            ((full_consumption_data['timestamp'].dt.tz_localize(None)) <= periodSelected_upper)   # Consumption data is also filtered by time - must be within the range of the Cesium time slider
                            & ((full_consumption_data['timestamp'].dt.tz_localize(None)) >= periodSelected_lower)]
              
    # Creates separate dataframes for each consumption type          
    elec = filtered_df[filtered_df['type'] == 'electricity']
    gas = filtered_df[filtered_df['type'] == 'gas']
    water = filtered_df[filtered_df['type'] == 'water']
    heat = filtered_df[filtered_df['type'] == 'heat']
    
    return [ # Returns the sum of all consumptino types to the aggregate data store
        num_buildings,
        round(sum(elec['reading'])),  
        round(sum(gas['reading'])),
        round(sum(water['reading'])),
        round(sum(heat['reading']))
    ]


previousSliderValue = 'test'


@app.callback(
    dash.dependencies.Output('cesium_slider_text', 'children'), # text above cesium time slider that displays what period is selected
    [dash.dependencies.Input('cesium_slider', 'value')]) # listens to when cesium time slider changes 
def update_output(value):
    selectedDate1 = dt.datetime.utcfromtimestamp(value[0]) # Convert unix time back to normal 
    selectedDate2 = dt.datetime.utcfromtimestamp(value[1])
    return 'You have selected the period between ' + selectedDate1.strftime(   # Text that will be appended ot the cesium_Slider_text div, showing user what time period they have selected for visualisation
        '%Y-%m-%d %H:%M:%S') + ' and ' + selectedDate2.strftime(
            '%Y-%m-%d %H:%M:%S')


@app.callback(
    dash.dependencies.Output('colorBy', 'run'), 
    [dash.dependencies.Input('cesium_dropdown', 'value')]) 
def update_map(cesium_dropdown):
    global usage_type
    global usage_area
    global previousSliderValue
    if (cesium_dropdown == 'height'): 
        return 'colourByHeight()' ## Runs the Javascript colourByHeight which is a function created on Cesium initialisation. Cesium map is coloured by height.



@app.callback(
    Output('filtersJS', 'run'), [ # Runs JS which calls the showFilters function which filters the Cesium Map based on GIA, YOB, Building Type
        Input('building_type', 'value'),  # Residential, university or both building types shoudl be shown?  
        Input('GIA_slider', 'value'),   # listens for changes to GIA range
        Input('year_slider', 'value')   # listens for changes to year of build range
    ])
def update_filter(buildingtype, GIA_slider, year_slider):
    return '''
            showFilters({}, {}, {}, {}, '{}');'''.format(
        GIA_slider[0], GIA_slider[1], year_slider[0], year_slider[1], buildingtype)


@app.callback([
    dash.dependencies.Output('filterSettings', 'style'),# Div style. Either hidden or visible depending on user choice in the cesium dropdown
    dash.dependencies.Output('usage_settings', 'style') # Div style. Either hidden or visible depending on user choice in the cesium dropdown
], [dash.dependencies.Input('cesium_dropdown', 'value')])   # Cesium map dropdown - must listen to see what user is trying to do. If filter, then filter div must be displayed, etc
def update_output(cesium_dropdown):
    if (cesium_dropdown == 'filters'):  # If user selects filtering in the main settings, then show the filter div (which contains the filtering sliders) and hide the usage div (which contains the usage type dropdown)
        return ({"display": "inherit"}), ({"display": "none"}) #
    if (cesium_dropdown == 'height'): # If user colours by height, then neither usage nor filter divs are shown
        return ({"display": "none"}), ({"display": "none"})
    if (cesium_dropdown == 'energy'):   # Show usage div if usage is selected
        return ({"display": "none"}), ({"display": "block"})


usage_type = 'electricity' # Set initial values
usage_area = 'absolute'





@app.callback(
    dash.dependencies.Output('loadBatchValuesToJS', 'event'),
    [dash.dependencies.Input('usage_area', 'value')])
def update_type(value):
    global usage_area
    usage_area = value





@app.callback([
    Output('loadBatchValuesToJS', 'run'),   # Saves the building consumption values in a JS variable ready for changeColorJS to use to colour the cesium map
    Output('veryhigh_text', 'children'),    # key text.
    Output('high_text', 'children'),        # key text.
    Output('medium_text', 'children'),      # key text.
    Output('low_text', 'children'),         # key text.
    Output('verylow_text', 'children'),     # key text.
    Output('changeColorJS', 'run'),         # runJS module that changes the colour of cesium buildings based on consumption calculated in this funct.
    dash.dependencies.Output('tree', 'figure')
], [
    Input('cesium_slider', 'value'),        # Listeners: if cesium time slider changes, then time period changes so the consumption aggregate must be calculated again
    Input('cesium_dropdown', 'value'),                    # If the main dropdown changes to colorby consumption, then this function must be ready to calculate and display the colours.
    Input('usage_type', 'value'),                         # Which type of consumption does the function need to colour by? If changed, function must calculate and display the new consumption type on the map
    Input('usage_area', 'value')                           # Does user want to view absolute consumption values or consumption per gross internal area?. If changed, function must recalculate.
])
@cache.memoize()
def colorByUsage(slider_time, dropdown, usage_choice, area_choice): # FUNCTION COLOURS THE CESIUM MAP BY A RESOURCE TYPE ALSO CREATES TREEMAP
    global batchTable   # get the batchTable dataframe that contains the map's batchids and building codes

    
    buildingValues = [] # Empty array which will be populated with building ID, consumption and color and passed into a JS variable for the changeColorJS to use
    treemap_fig = px.treemap() # Empty treemap which will be populated based on usage_type
    run = ' ' 
    
    periodSelected_lower = pd.to_datetime(slider_time[0], unit='s')
    periodSelected_upper = pd.to_datetime(slider_time[1], unit='s')
    
    veryhigh_range, high_range, medium_range, low_range, verylow_range = '0', '0', '0', '0', '0', # Initially setting all key values to 0
    if (dropdown == 'energy'):  # If user actually wants to colour map by consumption: 
        records = full_consumption_data[(full_consumption_data['type'] == usage_choice) & ((full_consumption_data['timestamp'].dt.tz_localize(None)) <= periodSelected_upper) & ((full_consumption_data['timestamp'].dt.tz_localize(None)) >= periodSelected_lower)][['timestamp', 'building', 'reading']] # Filter consumption data by type, time
        
        if (filtered_buildings.empty != True): # If user has filtered buildings in the cesium map, then get the filtered buildings and only use consumption data from those.
            records = full_consumption_data[full_consumption_data['building'].isin(filtered_buildings['Property code_y']) & (full_consumption_data['type'] == usage_choice) & ((full_consumption_data['timestamp'].dt.tz_localize(None)) <= periodSelected_upper) & ((full_consumption_data['timestamp'].dt.tz_localize(None)) >= periodSelected_lower)][['timestamp', 'building', 'reading']]

        records2 = pd.merge(    # Merge the consumption data (records) with the building metadata in order to get the GIA
            records, buildings, left_on='building', right_on='Property code_y')
         
        
            
        agg_dict = {} # Dict that will be filled with each building's aggregated consumption and its GIA 

        for building in records2['building_x'].unique(): # For each building, calcuate sum of readings, get building GIA and building type
            agg_dict[building] = {
                'reading':
                records2[records2['building_x'] == building]['reading'].sum(),
                'type':
                records2[records2['building_x'] == building][
                    'building_y'].values[0],
                'GIA':
                records2[records2['building_x'] == building]['Total GIA']
                .values[0],
                'name':
                records2[records2['building_x'] == building]['name'].values[0] # building name
            }

        records3 = pd.DataFrame.from_dict(agg_dict, orient='index') # create a dataframe from this dict
        records3 = records3.reset_index()
        records3['building'] = records3['index']

        if (usage_choice == 'occupancy'):   
        # If users choose to colour by occupancy, the occupancy for each building is averaged as average device connections is much more intuitive than aggregated connections, most understand if '20' connections are in a building on avg compared to '175200' connections in a year (equivalent to 20/hr)

        
            records = full_wifi_data[((full_wifi_data['time'].dt.tz_localize(None)    # Grabs wifi data and filters by time period selected by the user
                                  ) <= periodSelected_upper) & (
                                      (full_wifi_data['time'].dt.tz_localize(None)
                                       ) >= periodSelected_lower)][[
                                           'time', 'buildingCode',
                                           'Authenticated Client Count'
                                       ]]
                                       
            if (filtered_buildings.empty != True):  # Once again, if user has filtered buildings, only the filtered buildings' data will be extracted
                records = full_wifi_data[(full_wifi_data['buildingCode'].isin(
                    filtered_buildings['Property code_y'])) & (
                        (full_wifi_data['time'].dt.tz_localize(None)
                         ) <= periodSelected_upper) &
                                    ((full_wifi_data['time'].dt.tz_localize(None))
                                     >= periodSelected_lower)][[
                                         'time', 'buildingCode',
                                         'Authenticated Client Count'
                                     ]]
                                     
                                     
            records2 = pd.merge(    # merge the consumption records with the buildings df to get building metadata such as name and GIA
                records,
                buildings,
                left_on='buildingCode',
                right_on='Property code_y')
                
                
            agg_dict = {}   # initialise the dict that will hold each building's consumption, name and GIA.
            
            
            for building in records2['buildingCode'].unique(): # for each building
                agg_dict[building] = { # add dict entry with building code
                    'reading':
                    records2[records2['buildingCode'] == building][
                        'Authenticated Client Count'].mean(), # MEAN of the device connections for each building
                    'type':
                    records2[records2['buildingCode'] == building][
                        'building'].values[0],
                    'GIA':
                    records2[records2['buildingCode'] == building][
                        'Total GIA'].values[0],
                    'name':
                    records2[records2['buildingCode'] == building]['name']
                    .values[0]
                }
                
            records3 = pd.DataFrame.from_dict(agg_dict, orient='index').reset_index() # Turn the dict into a dataframe
            
            records3['building'] = records3['index'] # get building codes from index

        if (usage_area == 'pergia'): # IF user has selected the 'consumption per m2' AKA building effiecency dropdown (usage_area), then reading values must be divided by the Gross internal Area of the building to get consumption/m2
            records3['reading'] = records3['reading'] / records3['GIA']

         ########CREATING TREEMAP#############
        tree_records = records3
        tree_records['all'] = 'all' # Created a common feature for all buildings in the treemap - all buildings will first be under 'all', then their building type etc. Read more https://plotly.com/python/treemaps/
        records3['name'].fillna(records3['building'], inplace=True) # If there is not a name available for the building, instead assign the building code as name
        treemap_fig = px.treemap(
            tree_records, path=['all', 'type', 'name'], values='reading')
        treemap_fig.data[0].textinfo = 'label+value+percent parent+percent entry' 
        treemap_fig.update_layout(
            autosize=True,
            margin=dict(l=30, r=30, b=5, t=60),
            font=dict(
                family="Courier New, monospace", size=16, color=modeColor2),
            hovermode="closest",
            plot_bgcolor=modeColor,
            paper_bgcolor=modeColor,
            uniformtext=dict(minsize=10, mode='show'))
        #######END OF TREEMAP CREATION#############
 
        records3_merged_batch = pd.merge(
            records3, batchTable, left_on='building',
            right_on='buildingNum').drop_duplicates('batchid') # Create dataFrame with only buildings that exist on the cesium map (inner join on the batchTable)
            
         # SEPARATING THE BUILDING CONSUMPTION AGGREGATE FIGURES BY THEIR VALUE IN COMPARISON TO THE AGGREGATE READINGS OVERALL. e.g. If building's reading is in between .80 and 1.0 quantile, it goes in records_vhigh DataFrame and is assigned the colour red.    
            
        records_vhigh = records3_merged_batch[records3_merged_batch['reading'].between(
            records3_merged_batch['reading'].quantile(.80),
            records3_merged_batch['reading'].quantile(1))]
        records_vhigh['color'] = '#FF0000'
        
        records_high = records3_merged_batch[records3_merged_batch['reading'].between(
            records3_merged_batch['reading'].quantile(.60),
            records3_merged_batch['reading'].quantile(.80))]
        records_high['color'] = '#f56d00'
        
        records_med = records3_merged_batch[records3_merged_batch['reading'].between(
            records3_merged_batch['reading'].quantile(.40),
            records3_merged_batch['reading'].quantile(.60))]
        records_med['color'] = '#d6a700'
        
        records_low = records3_merged_batch[records3_merged_batch['reading'].between(
            records3_merged_batch['reading'].quantile(.20),
            records3_merged_batch['reading'].quantile(.40))]
        records_low['color'] = '#a0d600'
        
        records_vlow = records3_merged_batch[records3_merged_batch['reading'].between(
            records3_merged_batch['reading'].quantile(0),
            records3_merged_batch['reading'].quantile(.20))]
        records_vlow['color'] = '#00ff05'
        
        # Consumption data is assembled back together again. but now each building has a color column which is decided by its consumption value
        
        records_all = records_vhigh
        records_all = records_all.append(records_high)
        records_all = records_all.append(records_med)
        records_all = records_all.append(records_low)
        records_all = records_all.append(records_vlow)

        
        
        reading_suffix = '' # Adding Unit Suffixes so they are visible in the Cesium Map 
        if ((usage_choice == 'electricity') or (usage_choice == 'heat')):
            reading_suffix = ' kWh' 
        elif ((usage_choice == 'water') or (usage_choice == 'gas')):
            reading_suffix = ' m3'
        elif (usage_choice == 'occupancy'):
            reading_suffix = ' devices'

        if (usage_area == 'pergia'):
            reading_suffix = reading_suffix + '/m2' # If building efficiency is shown, consumption is shown per /m2 and so suffix is added to show this

        records_all['reading'] = records_all['reading'].round().astype(
            str) + reading_suffix  # Round the readings, add the unit suffix to the readings



        buildingValues = records_all[['batchid', 'color', 'reading']].values.tolist()  # Turn the DataFrame into a list ready for sending to the JS function

        # The below variables are the vhigh, high.., reading ranges that will be displayed as the key.
        
        veryhigh_range = str(records3_merged_batch['reading'].quantile(
            .80).round()) + reading_suffix + ' - ' + str(
                records3_merged_batch['reading'].quantile(1).round()) + reading_suffix
                
        high_range = str(records3_merged_batch['reading'].quantile(
            .60).round()) + reading_suffix + ' - ' + str(
                records3_merged_batch['reading'].quantile(.80).round()) + reading_suffix
                
        medium_range = str(records3_merged_batch['reading'].quantile(
            .40).round()) + reading_suffix + ' - ' + str(
                records3_merged_batch['reading'].quantile(.60).round()) + reading_suffix
                
        low_range = str(records3_merged_batch['reading'].quantile(
            .20).round()) + reading_suffix + ' - ' + str(
                records3_merged_batch['reading'].quantile(.40).round()) + reading_suffix
                
        verylow_range = str(records3_merged_batch['reading'].quantile(
            0).round()) + reading_suffix + ' - ' + str(
                records3_merged_batch['reading'].quantile(.20).round()) + reading_suffix
 
        ##############VISUALISATION##########
        run = '''
        
        function changeColor(tile) {  
        content = tile.content;
        for (var i = 0; i < batchValues.length; i++) { // iterate through the list of batchValues
        content.getFeature(batchValues[i][0]).color = Cesium.Color.fromCssColorString(batchValues[i][1])  // Set the color of each building to its color column  
        }
        tileset.tileVisible.removeEventListener(changeColor); // remove event listener once done changing colors
        }
        
        tileset.tileVisible.addEventListener(changeColor);
        
        for (var i = 0; i < batchValues.length; i++) {
        content.getFeature(batchValues[i][0]).setProperty('power', batchValues[i][2]);      // set the consumption aggregate value as an attribute of each building, so it can be seen on mouse hover 
        }
        '''

    return (
        " batchValues = {}".format(buildingValues) # Sets the JS variable to the buildingValues that were calculated in this function. The run function then grabs this JS variable and changes the building colors
    ), veryhigh_range, high_range, medium_range, low_range, verylow_range, run, treemap_fig # Outputs the key ranges, the changeColor JS and the treemap treemap_figure


@app.callback(
    Output('trendgraphs', 'figure'), [  #Output the created subplot figure into the graph 'trendgraphs'
        Input('cesium_slider', 'value'),
        Input('usage_type', 'value'),
        Input('usage_area', 'value'),
        Input('getCesiumBuildingNum', 'event'), # As this is a building-specific graph, function must listen for when user selects a new building
        Input('building_specific_dropdown', 'value'),  # Listen for if user wants building-specific graphs or campus as a whole graph
    ])
@cache.memoize() # compute heavy function so results are memoized.
def update_subplots(slider_time, usage_choice, usagearea, buildingNum,
                    building_specific_dropdown):

    ######PROCESSING#####

    periodSelected_lower = pd.to_datetime(slider_time[0], unit='s')
    periodSelected_upper = pd.to_datetime(slider_time[1], unit='s')
    if (building_specific_dropdown == 'individualBuilding'):        # So if user has chosen building-specific graphs in the dropdown:
        building_selected = full_consumption_data[     # filter all consumption data by the building chosen, consumption type wanted and the time period selected and create a df with filtered results
            (full_consumption_data['building'] == buildingNum)
            & (full_consumption_data['type'] == usage_choice) &
            ((full_consumption_data['timestamp'].dt.tz_localize(None)) <=
             periodSelected_upper) &
            ((full_consumption_data['timestamp'].dt.tz_localize(None)) >=
             periodSelected_lower)][['timestamp', 'building', 'reading']]

    if ((usage_choice == 'occupancy') & (building_specific_dropdown == 'individualBuilding')):  #If user wants to see building-specific graphs for occupancy  
        building_selected = full_wifi_data[ # Filter all wifi data by building chosen and time period selected, create df with filtered result
            (full_wifi_data['buildingCode'] == buildingNum) &
            ((full_wifi_data['time'].dt.tz_localize(None)) <= periodSelected_upper)
            & ((full_wifi_data['time'].dt.tz_localize(None)) >=
               periodSelected_lower)][['time', 'buildingCode', 'Authenticated Client Count']]
               
        building_selected['timestamp'] = building_selected['time']  # change the wifi format into consumption format (just so that the processing below can use the same column names)
        building_selected['reading'] = building_selected[       # change the wifi format into consumption format (just so that the processing below can use the same column names)
            'Authenticated Client Count']

    if (building_specific_dropdown == 'campusOverview'):    # If user wants to see campus overall graphs
        buildingNum = 'Campus'  # not building specific, so buildingNum is now 'campus' (for the title of the figure)
        building_selected = full_consumption_data[(full_consumption_data['type'] == usage_choice) & (       #Filters all consumption data by consumption type and time period selected
            (full_consumption_data['timestamp'].dt.tz_localize(None)
             ) <= periodSelected_upper) & (
                 (full_consumption_data['timestamp'].dt.tz_localize(None)) >=
                 periodSelected_lower)][['timestamp', 'building', 'reading']]

        if (usage_choice == 'occupancy'):   # since occupancy uses a different dataset, must process slightly differently
            building_selected = full_wifi_data[((full_wifi_data['time'].dt.tz_localize( #Filters all wifi data by time period selected
                None)) <= periodSelected_upper) & (
                    (full_wifi_data['time'].dt.tz_localize(None)
                     ) >= periodSelected_lower)][[
                         'time', 'buildingCode', 'Authenticated Client Count'
                     ]]

            building_selected['timestamp'] = building_selected['time']  # once again standardizes the column names to consumption format
            building_selected['reading'] = building_selected[
                'Authenticated Client Count']

        building_selected = building_selected.groupby('timestamp').sum(min_count=1).reset_index()     # As user wants campus overview, groupby timestamp and sum all records. Now building_selected df contains a singular value for each timestamp representing campus consumption at that time. 


    if (usage_choice == 'occupancy'):           # If user selects occupancy, mean values are calculated for the 
        building_selected['daymonthyear'] = building_selected[
            'timestamp'].dt.strftime(
                '%d/%m/%Y'
            )  # Create a column with just the day/month/year instead of hourly timestamps.
        building_selected['monthyear'] = building_selected[ # Create a column with just the month/year instead of hourly timestamps.
            'timestamp'].dt.strftime('%m/%Y')
            
        building_selected_byday = building_selected[[
            'daymonthyear', 'reading'
        ]].groupby('daymonthyear').mean().reset_index()     # Using the daymonthyear column, calculate the average connections for each day and save as new df
        
        building_selected_byday['daynumber'] = pd.to_datetime(      # Create a new column called 'daynumber' which is assigned based on what day of the week it is. 0-6 going from Monday to Sunday.
            building_selected_byday['daymonthyear']).dt.dayofweek
            
        building_selected_bymonth = building_selected[[     # Using the monthyear column, calculate the average connections for each month and save as new df
            'monthyear', 'reading'
        ]].groupby('monthyear').mean().reset_index()
        
        building_selected_bymonth['monthnumber'] = pd.to_datetime( # Create a new column called 'monthnumber' which is assigned based on what month it is. 
            building_selected_bymonth['monthyear']).dt.month
    else:   # If user has not selected occupancy, then they have selected a type of consumption. Similar to occupancy but takes sum instead of mean of the readings.
        building_selected['daymonthyear'] = building_selected[
            'timestamp'].dt.strftime(
                '%d/%m/%Y')
                
        building_selected['monthyear'] = building_selected[
            'timestamp'].dt.strftime('%m/%Y')  
        building_selected_byday = building_selected[[
            'daymonthyear', 'reading'
        ]].groupby('daymonthyear').sum().reset_index()  # Takes SUM instead of mean as this is not an occupancy graph
        
        building_selected_byday['daynumber'] = pd.to_datetime(
            building_selected_byday['daymonthyear']).dt.dayofweek
        building_selected_bymonth = building_selected[[
            'monthyear', 'reading'
        ]].groupby('monthyear').sum().reset_index() # Takes SUM instead of mean as this is not an occupancy graph
        
        building_selected_bymonth['monthnumber'] = pd.to_datetime(
            building_selected_bymonth['monthyear']).dt.month


    building_selected['hourofday'] = building_selected['timestamp'].dt.hour # Assign a new column to building_selected with just the hour of the timestamp

    month_df = building_selected_bymonth.groupby(   
        'monthnumber').mean().reset_index() # using the bymonth df, groupby the month of the reading and take the mean. This returns the average reading for each month.
        
    dayofweek_df = building_selected_byday.groupby( # using the byday df, groupby the day of the week of the reading and take the mean. This returns the average reading for each day of the week.
        'daynumber').mean().reset_index()
        
    hourofday_df = building_selected.groupby('hourofday').mean().reset_index()  # using original df, groupby the hour column and take the mean. This returns the average reading for each hour of the day.



    hourofday_df['hourofday'] = pd.to_datetime(
        hourofday_df['hourofday'], format='%H').dt.strftime("%H:%M") # turned to datetime format with hour and minute (looks better on graph)

    daystext = pd.DataFrame(
        [['Monday', 0], ['Tuesday', 1], ['Wednesday', 2], ['Thursday', 3],
         ['Friday', 4], ['Saturday', 5], ['Sunday', 6]],
        columns=["day", "daynumber"])       # create datarame with the day name associated with each day of the week number. (Otherwise bar chart would show 0,1,2... instead of monday,tuesday,wednesday)
        
    monthstext = pd.DataFrame(
        [['January', 1], ['February', 2], ['March', 3], ['April', 4],
         ['May', 5], ['June', 6], ['July', 7], ['August', 8], ['September', 9],
         ['October', 10], ['November', 11], ['December', 12]],
        columns=["month", "monthnumber"])   # same as the daystext dataframe but for months of the year.
        
    dayofweek_df = dayofweek_df.merge(daystext, left_on='daynumber', right_on='daynumber')    # add the day name to the data 
    month_df = month_df.merge(monthstext, on='monthnumber') # add the month name to the data 

    ######VISUALISATION#####
    
    usageTypeColor = ['#fac1b7']        # The colour of the plots are decided by what type of consumption or occupancy is selected. The colours match the historical data graphs.
    if (usage_choice == 'electricity'):
        usageTypeColor = ['rgba(250, 193, 183, 0.76)']
    elif (usage_choice == 'gas'):
        usageTypeColor = ['#849E68']
    elif (usage_choice == 'heat'):
        usageTypeColor = ['#a3cce9']
    elif (usage_choice == 'water'):
        usageTypeColor = ['#59C3C3']
    elif (usage_choice == 'occupancy'):
        usageTypeColor = ['#58508d']
        
    subplot_fig = make_subplots(rows=3, cols=1, vertical_spacing=0.20)      # Create the subplot figure, 3 rows 1 column. 1 subplot on each row.

    subplot_fig.add_trace(      # Add line graph for hour of day trends
        px.line(
            hourofday_df,
            x='hourofday',
            y='reading',
            color_discrete_sequence=usageTypeColor)['data'][0],
        row=1,
        col=1)
    subplot_fig.update_xaxes(title_text="Hour of Day", row=1, col=1)    # update x axis title to hour of day

    subplot_fig.add_trace(  # Add bar chart for day of week trends
        px.bar(
            dayofweek_df,
            x='day',
            y='reading',
            color_discrete_sequence=usageTypeColor)['data'][0],
        row=2,
        col=1)
    subplot_fig.update_xaxes(title_text="Day of Week", row=2, col=1)

    subplot_fig.add_trace(  # Add bar chart for monthly trends
        px.bar(
            month_df,
            x='month',
            y='reading',
            color_discrete_sequence=usageTypeColor)['data'][0],
        row=3,
        col=1)
    subplot_fig.update_xaxes(title_text="Month", tickangle=-90, row=3, col=1)

    subplot_fig.update_layout(
        height=500,
        margin=dict(l=30, r=30, t=40, b=10),
        paper_bgcolor=modeColor,
        plot_bgcolor=modeColor,
        title_text=(buildingNum + ' ' + usage_type + " trends"),   # title of: building code + consumption(or occupancy) type + trends. Example title = 'MC078 water trends'. if campus overview dropdown selected then 'Campus water trends'
        title_x=0.5,
        showlegend=True,
        font=dict(color="#d8d8d8"),
    ),

    subplot_fig.update_traces(),

    return subplot_fig







#   The following 5 callbacks update the infoboxes such as 'Num. of Buildings', 'Electricity Used', 'Water used' etc by listening for when the aggregate data store is updated (ie user has changed a filter to change the aggregated values)

@app.callback(
    Output('building_num_text', 'children'), [Input('aggregate_data', 'data')])
def building_num_text(data):
    return str(data[0][0]) + " "


@app.callback(
    Output('elecText', 'children'), [Input('aggregate_data', 'data')])
def update_gas_text(data):
    return (human_format(data[1]) + " kWh")


@app.callback(Output('gasText', 'children'), [Input('aggregate_data', 'data')])
def update_gas_text(data):
    return (human_format(data[2]) + " m3")


@app.callback(
    Output('waterText', 'children'), [Input('aggregate_data', 'data')])
def update_water_text(data):
    return (human_format(data[3]) + " m3")


@app.callback(
    Output('heatText', 'children'), [Input('aggregate_data', 'data')])
def update_gas_text(data):
    return (human_format(data[4]) + " kWh")



@app.callback(
    Output('individual_graph', 'figure')    #output to the individual graph
, [
    Input('getCesiumBuildingNum', "event"), # Parameters are the building number selected and the building specific dropdown (ie if the user wants a campus overview or view graphs for the specific building)
    Input('building_specific_dropdown', 'value')
])
@cache.memoize()    # Compute intense so memoized 
    # Make the historical consumption graphs. Heavily adapted from the Dash Gallery's New York Gas dashboard example https://github.com/plotly/dash-oil-and-gas-demo. 
def make_individual_figure(buildingNum, building_specific_dropdown):     
    ##############PROCESSING##########
    if (building_specific_dropdown == 'campusOverview'):  # if campus overview is wanted, must combine building consumption values
        buildingNum = 'Campus' # no buildingNumber as the campus overview is being displayed
        selected_building = full_consumption_data.groupby(['timestamp', 'type']).sum().reset_index() # Get the sum of resource consumption for each timestamp for each individual resource in all buildings. Gives a dataframe of campus total usage at each timestamp for each resource type
        selectedBuilding_occu = full_wifi_data.groupby('time').sum(min_count=1).reset_index() # Get sum of devices at each timestamp in all buildings. Gives campus occupancy.
        
    if (building_specific_dropdown == 'individualBuilding'):    # if user wants building-specific graphs
        selected_building = full_consumption_data[(full_consumption_data['building'] == buildingNum)] # Get consumption data for just the building that the user selected using the parameter buildingNum
        selectedBuilding_occu = full_wifi_data[(full_wifi_data['buildingCode'] == buildingNum)] # Get device data for just the building that the user selected using the parameter buildingNum

    #Create dataFrames for each resource type
    selectedBuilding_elec = selected_building[(selected_building['type'] == 'electricity')]
    selectedBuilding_gas = selected_building[(selected_building['type'] == 'gas')]
    selectedBuilding_water = selected_building[(selected_building['type'] == 'water')]
    selectedBuilding_heat = selected_building[(selected_building['type'] == 'heat')]

    ##############VISUALISATION##########
    #Some styling
    layout_individual = dict(
        autosize=True,
        height=800,
        margin=dict(l=40, r=20, b=20, t=30),
        font=dict(family="Courier New, monospace", size=15, color=modeColor2),
        hovermode="closest",
        plot_bgcolor=modeColor,
        paper_bgcolor=modeColor,
        legend=dict(font=dict(size=14), orientation='h'),
    )

    data = [                # A scattergl graph created for each resource type (and occupancy) with a different colour for each. ScatterGL used instead of traditional scatter as it offers WebGL GPU-accelerated viewing.
        go.Scattergl(
            mode='lines',
            name='Electricity used (kWh)',
            x=selectedBuilding_elec['timestamp'],
            y=selectedBuilding_elec['reading'],
            line=dict(shape="linear", width=0.8, color='#fac1b7')),
        go.Scattergl(
            mode='lines',
            name='Gas used (m3)',
            x=selectedBuilding_gas['timestamp'],
            y=selectedBuilding_gas['reading'],
            line=dict(shape="linear", color='#849E68')),
        go.Scattergl(
            mode='lines',
            name='Heat (kWh)',
            x=selectedBuilding_heat['timestamp'],
            y=selectedBuilding_heat['reading'],
            line=dict(shape="linear", width=1, color='#a3cce9')),
        go.Scattergl(
            mode='lines',
            name='Water used (m3)',
            x=selectedBuilding_water['timestamp'],
            y=selectedBuilding_water['reading'],
            line=dict(shape="linear", color='#59C3C3')),
        go.Scattergl(
            mode='lines',
            name='Occupancy Count',
            x=selectedBuilding_occu['time'],
            y=selectedBuilding_occu['Authenticated Client Count'],
            line=dict(shape="linear", width=1, color='#58508d')),
    ]




    fig = make_subplots(rows=5, cols=1, shared_xaxes=True) # Makes the 5 subplots for all resource types (+ occupancy) all with a shared x axis

    # Adds all of the ScatterGL plots to the individual subplots to create the graph
    fig.add_trace(data[0], row=1, col=1)
    fig.add_trace(data[1], row=2, col=1)
    fig.add_trace(data[2], row=3, col=1)
    fig.add_trace(data[3], row=4, col=1)
    fig.add_trace(data[4], row=5, col=1)

    layout_individual['title'] = buildingNum + ' hourly consumption' # Add a title to the subplot visualisation
    fig.update_layout(layout_individual, legend=dict(x=0.2, y=1.1)) # Positioning title in top left

    #Styling the X and Y axis to look good on the dark grey background
    fig.update_yaxes(
        zeroline=True,
        showgrid=True,
        gridwidth=1,
        gridcolor='#454545',
        zerolinewidth=2,
        zerolinecolor='#454545')
    fig.update_xaxes(
        zeroline=True,
        showgrid=True,
        gridwidth=1,
        gridcolor='#454545',
        zerolinewidth=2,
        zerolinecolor='#454545')
    return fig



if __name__ == '__main__':
    app.run_server(debug=True, host='0.0.0.0', port=8052)
