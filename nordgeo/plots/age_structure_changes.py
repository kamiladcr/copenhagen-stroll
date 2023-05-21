from nordgeo import data
import plotly.graph_objects as go
import geopandas as gpd
import plotly.express as px

def show():
    df = data.load()

    df_grouped = df.groupby(["year", "age group"]).sum(numeric_only=True).reset_index()
    traces = []

    age_groups = df_grouped["age group"].unique()[::-1]

    for age_group in age_groups:
        df_age_group = df_grouped[df_grouped["age group"] == age_group]
        #    total_population = df_age_group['value_total'].sum(numeric_only=True)

        trace = go.Scatter(
            x=df_age_group["year"],
            y=df_age_group["value_grouped"],
            mode="lines",
            stackgroup="one",
            name=age_group,
        )

        traces.append(trace)

    layout = go.Layout(
        title="Age structure in 2018-2022",
        xaxis=dict(title="Year"),
        yaxis=dict(title="Population (total)"),
        showlegend=True,
        hovermode="x",
    )

    fig = go.Figure(data=traces, layout=layout)
    fig.show()


def working():
    df = data.load()
    df = df[df["age group"] == "working age"]
    df = df[df["year"] != "2018"]

    df["population dynamics"] = (
        (df["value_grouped"] - df["value_grouped_prev"])
        / df["value_grouped_prev"]
        * 100
    )

    gdf = gpd.GeoDataFrame(df)
    gdf = gdf.drop(["centroid"], axis=1)

    px.choropleth_mapbox(
        title="Population change in 2019-2022 for working age group",
        data_frame=gdf,
        geojson=gdf._to_geo(),
        featureidkey="properties.municipality",
        locations="municipality",
        color="population dynamics",
        range_color=(-5, +5),
        color_continuous_scale="RdBu",
        mapbox_style="carto-positron",
        zoom=6,
        center={"lat": 56.05, "lon": 12.70},
        opacity=0.7,
        labels={"value": "Value"},
        animation_frame="year",
        height=800,
    ).show()


def youth():
    df = data.load()
    df = df[df["age group"] == "youth"]
    df = df[df["year"] != "2018"]

    df["population dynamics"] = (
        (df["value_grouped"] - df["value_grouped_prev"])
        / df["value_grouped_prev"]
        * 100
    )

    gdf = gpd.GeoDataFrame(df)
    gdf = gdf.drop(["centroid"], axis=1)

    px.choropleth_mapbox(
        title="Population change in 2019-2022 for youth age group",
        data_frame=gdf,
        geojson=gdf._to_geo(),
        featureidkey="properties.municipality",
        locations="municipality",
        color="population dynamics",
        range_color=(-5, +5),
        color_continuous_scale="RdBu",
        mapbox_style="carto-positron",
        zoom=6,
        center={"lat": 56.05, "lon": 12.70},
        opacity=0.7,
        labels={"value": "Value"},
        animation_frame="year",
        height=800,
    ).show()


def elderly():
    df = data.load()
    df = df[df["age group"] == "elderly"]
    df = df[df["year"] != "2018"]

    df["population dynamics"] = (
        (df["value_grouped"] - df["value_grouped_prev"])
        / df["value_grouped_prev"]
        * 100
    )

    gdf = gpd.GeoDataFrame(df)
    gdf = gdf.drop(["centroid"], axis=1)

    px.choropleth_mapbox(
        title="Population change in 2019-2022 for elderly age group",
        data_frame=gdf,
        geojson=gdf._to_geo(),
        featureidkey="properties.municipality",
        locations="municipality",
        color="population dynamics",
        range_color=(-5, +5),
        color_continuous_scale="RdBu",
        mapbox_style="carto-positron",
        zoom=6,
        center={"lat": 56.05, "lon": 12.70},
        opacity=0.7,
        labels={"value": "Value"},
        animation_frame="year",
        height=800,
    ).show()
