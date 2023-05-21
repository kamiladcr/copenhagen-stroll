from nordgeo import data
import plotly.graph_objects as go

# The distribution of age groups' populations over time
# Each area represents an age group, and the y-axis represents the population count.


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
