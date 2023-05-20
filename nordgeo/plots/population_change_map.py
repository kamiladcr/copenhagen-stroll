import os
os.environ['USE_PYGEOS'] = '0'
import geopandas as gpd
from nordgeo import data
import plotly.express as px

# Municipal level population trend

def show():
    df = data.load()

    df.sort_values(['municipality', 'year'], inplace=True)

    df['population dynamics'] = (df["value_total"] - df["value_total_prev"]) / df["value_total_prev"] * 100

    # previous_total_value = {}
    # for index, row in df.iterrows():
    #     current_year = int(row['year'])
    #     current_total_value = row['value_total']
    #     if current_year > 2018:
    #         if current_total_value is not None and current_total_value != 0:
    #             population_dynamics = (current_total_value - previous_total_value) / previous_total_value * 100
    #             df.at[index, 'population dynamics'] = population_dynamics
    #     previous_total_value = current_total_value
    # df.loc[df['year'] == '2018', 'population dynamics'] = None

    # add age group dynamics trend
    # df['population trend'] = None
    # df.loc[df['population dynamics'] >= 0, 'population trend'] = 'population increase'
    # df.loc[df['population dynamics'] < 0, 'population trend'] = 'population decrease'

    # Working age group trend
    gdf = gpd.GeoDataFrame(df)
    gdf = gdf.drop(['centroid'], axis=1)
    gdf = gdf[gdf['year'] != "2018"]

    # color_map = {
    #     'population increase': 'green',
    #     'population decrease': 'red'
    # }

    fig = px.choropleth_mapbox(
        title='Population change by municipality',
        data_frame=gdf,
        geojson=gdf._to_geo(),
        featureidkey="properties.municipality",
        locations='municipality',
        #color='population trend',
        color='population dynamics',
        range_color=(-5, +5),
        color_continuous_scale="RdBu",
        # color_discrrete_map=color_map,
        mapbox_style='carto-positron',
        zoom=7,
        center={'lat': 56.05, 'lon': 12.70},
        opacity=0.7,
        labels={'value': 'Value'},
        animation_frame='year',
        height=1000,
    )

    fig.update_layout(margin={'r': 0, 't': 0, 'l': 0, 'b': 0})

    fig.show()
