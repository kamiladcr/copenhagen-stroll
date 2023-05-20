from nordgeo import data
import plotly.express as px

df = data.load()

def data():
    return (
        df
        .loc[df["year"]!="2018"]
        .groupby(["year", "municipality"])
        .agg({"value_grouped":"sum","value_grouped_prev":"sum"})
        .assign(population=lambda x: x.value_grouped)
        .assign(population_change=lambda x: x.value_grouped - x.value_grouped_prev)
        .assign(population_change_percent=lambda x: (x.value_grouped - x.value_grouped_prev) / x.value_grouped_prev * 100)
        .loc[:, ["population","population_change","population_change_percent"]]
        .reset_index()
    )

def bar():
    df = (
        data()
        .groupby(["year"])[["population_change"]]
        .sum()
        .reset_index()
    )

    px.bar(
        data_frame=df,
        y="population_change",
        x="year",
    ).show()

def violin():
    df = data()
    px.violin(
        df,
        y="population_change_percent",
        x="year",
        color="year",
        points="all",
        height=800,
        hover_name="municipality",
        hover_data=df.columns,
    ).show()

def lines():
    df = data()
    px.line(
        df,
        y="population_change_percent",
        x="year",
        color="municipality",
        height=800,
        hover_name="municipality",
        line_shape="spline",
        hover_data=df.columns,
    ).update_layout(legend=dict(itemclick="toggleothers")).show()

def scatter(year_from, year_to):
    df = (
        data()
        .loc[lambda x: x.year != "2022"]
        .pivot_table(values="population_change_percent", index="municipality", columns="year")
        .assign(median=lambda x: x.median(axis=1))
        .assign(change=lambda x: x[year_to] - x[year_from])
        .reset_index()
    )

    px.scatter(
        data_frame=df,
        y="median",
        x="change",
        color="municipality",
        range_x=(-3,3),
        range_y=(-1.5,3),
        hover_data=df.columns,
    ).show()

def classes():
    # 0 0 0 \\ Overall decline
    # 0 1 1 \/ Negative effect
    # 1 0 2 /\ Positive effect
    # 1 1 3 // Overall growth
    m_classes = {0: 'Overall decline', 1: 'Negative effect', 2: 'Positive effect', 3: 'Overall growth'}

    class_df = (
        data()
        .loc[lambda x: x.year != "2022"]
        .pivot_table(values="population_change_percent", index="municipality", columns="year")
        .assign(median=lambda x: x.median(axis=1))
        .assign(change_2020=lambda x: (x["2020"] - x["2019"] > 0).astype(int))
        .assign(change_2021=lambda x: (x["2021"] - x["2020"] > 0).astype(int))
        .assign(m_class=lambda x: ((x.change_2020 * 2) + x.change_2021).replace(m_classes))
        .assign(count=1)
        .reset_index()
    )

    display(class_df.groupby("m_class")["count"].sum().reset_index())

    gdf = (
        df
        .drop("centroid", axis=1)
        .merge(class_df, on="municipality", how="left")
        .loc[:, ["municipality", "geometry", "m_class"]]
    )

    px.choropleth_mapbox(
        data_frame=gdf,
        geojson=gdf._to_geo(),
        featureidkey="properties.municipality",
        locations='municipality',
        color='m_class',
        mapbox_style='carto-positron',
        zoom=7,
        center={'lat': 56.05, 'lon': 12.70},
        opacity=0.7,
        labels={'value': 'Value'},
        height=800,
    ).show()
