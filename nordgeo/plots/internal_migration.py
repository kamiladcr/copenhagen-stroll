import plotly.express as px
from nordgeo import data
import geopandas as gpd
import pandas as pd
import math


def bar():
    df = (
        data.load()
        .rename(columns={"net migration": "Internal net migration"})
        .loc[lambda x: x.year != "2018"]
        .groupby(["year"])[
            ["value_grouped", "value_grouped_prev", "Internal net migration"]
        ]
        .sum()
        .reset_index()
        .assign(population=lambda x: x.value_grouped)
        .assign(
            Other=lambda x: x.value_grouped
            - x.value_grouped_prev
            - x["Internal net migration"]
        )
        .loc[:, ["year", "Other", "Internal net migration"]]
    )

    px.bar(
        data_frame=df,
        y=["Other", "Internal net migration"],
        x="year",
    ).update_layout(
        legend=dict(title="Population change components"),
        title="Internal net migration in total population change",
        xaxis_title="Population change (absolute)",
        yaxis_title="Year",
    ).show()


def migration_trend_map():
    df = data.load()
    df = df[df["age group"] == "working age"]
    df = df[df["year"] == "2022"]
    df["net migration trend"] = df["net migration"].apply(
        lambda x: "positive" if x > 0 else "negative"
    )
    df["net migration"] = abs(df["net migration"])

    df["centroid"] = df["geometry"].centroid
    df["lat"] = df["centroid"].y
    df["lon"] = df["centroid"].x

    px.scatter_mapbox(
        df,
        lat="lat",
        lon="lon",
        hover_data=["municipality", "year", "age group", "net migration"],
        color="net migration trend",
        size="net migration",
        color_discrete_map={"positive": "green", "negative": "red"},
        size_max=30,
        zoom=5,
        height=800,
        # animation_frame="year",
    ).update_layout(
        title="Internal net migration in 2022",
        #    legend=dict("Net migration trend"),
        mapbox_style="carto-positron",
        mapbox_zoom=7,
        mapbox_center={"lat": 56.05, "lon": 12.70},
    ).show()


def migration_share_map():
    labels = [
        "<-0.5",
        "-0.5 - -0.1",
        "-0.1 - 0.1",
        "0.1 - 1",
        ">1",
    ]

    def categorize(x):
        return pd.cut(x, bins=[-math.inf, -0.5, -0.1, 0.1, 1, math.inf], labels=labels)

    df = data.load()
    df = gpd.GeoDataFrame(
        df.groupby(["municipality", "year", "geometry"], sort=False)
        .sum(numeric_only=True)[["value_grouped", "net migration"]]
        .reset_index()
        .assign(
            migration_percentage=lambda x: x["net migration"] / x["value_grouped"] * 100
        )
        .assign(category=lambda x: categorize(x["migration_percentage"]))
    )

    px.choropleth_mapbox(
        data_frame=df,
        geojson=df._to_geo(),
        locations="municipality",
        featureidkey="properties.municipality",
        color="category",
        mapbox_style="carto-positron",
        center={"lat": 56.05, "lon": 12.70},
        zoom=6,
        height=800,
        animation_frame="year",
        hover_name="municipality",
        hover_data=[
            "municipality",
            "value_grouped",
            "net migration",
            "migration_percentage",
        ],
        category_orders={"category": labels},
        color_discrete_sequence=px.colors.sequential.RdBu[3:],
        title="Internal net migration in total population",
    ).update_layout(
        legend=dict(title="Internal net migration in total population (%)")
    ).show()
