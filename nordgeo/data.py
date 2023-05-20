import os

os.environ["USE_PYGEOS"] = "0"

import geopandas as gpd
import pandas as pd
import numpy as np
import pyarrow


def update():
    # load polygons for The Greater Copenhagen region
    mun = gpd.read_file("data/mun_2022/nord_mun22_lcc.shp")
    mun = mun[
        (mun["REG_NORDIC"] == "Skåne")
        | (mun["REG_NORDIC"] == "Halland")
        | (mun["REG_NORDIC"] == "Hovedstaden")
        | (mun["REG_NORDIC"] == "Sjælland")
    ]

    mun["centroid"] = mun["geometry"].centroid
    mun["lat"] = mun["centroid"].y
    mun["lon"] = mun["centroid"].x

    mun = mun.set_crs(3034, allow_override=True)
    mun = mun.to_crs(4326)
    mun = mun.reset_index(drop=True)

    # load SE age structure data by municipality
    # Source: Population by region, marital status, age and sex. Year 1968 - 2022

    SE_data_age = pd.read_csv("data/SE_data_age.csv", sep=";", encoding="ISO-8859-1")
    SE_data_age = SE_data_age.rename(columns={"region": "municipality"})
    SE_data_age["municipality"] = SE_data_age["municipality"].str[5:]

    # load DK age structure data by municipality
    # Source: BY2: Population 1. January by municipality, size of the city, age and sex

    DK_data_age = pd.read_csv(
        "data/DK_data_age.csv", sep=";", encoding="ISO-8859-1", header=1
    )
    DK_data_age[" "] = DK_data_age[" "].str.replace(" ", "")
    DK_data_age[" "] = DK_data_age[" "].replace("", np.nan)
    DK_data_age = DK_data_age.rename(columns={" ": "municipality", " .1": "age"})
    DK_data_age["municipality"] = DK_data_age["municipality"].fillna(method="ffill")
    DK_data_age = DK_data_age.dropna()
    DK_data_age.reset_index(inplace=True, drop=True)
    DK_data_age["municipality"] = DK_data_age["municipality"].replace(
        "Copenhagen", "København"
    )

    # merge SE age structure data with polygons

    gcr__SE_age = pd.merge(
        SE_data_age, mun, left_on="municipality", right_on="MUN_NORDIC"
    )

    def fill_region_se(row):
        if (
            row["municipality"]
            in mun[mun["REG_NORDIC"] == "Halland"]["MUN_NORDIC"].tolist()
        ):
            return "Halland"
        elif (
            row["municipality"]
            in mun[mun["REG_NORDIC"] == "Skåne"]["MUN_NORDIC"].tolist()
        ):
            return "Skåne"
        else:
            return None

    gcr__SE_age["region"] = gcr__SE_age.apply(fill_region_se, axis=1)
    gcr__SE_age = gcr__SE_age[
        (gcr__SE_age["REG_NORDIC"] == "Skåne")
        | (gcr__SE_age["REG_NORDIC"] == "Halland")
    ]

    # merge DK age structure data with polygons

    gcr__DK_age = pd.merge(
        DK_data_age, mun, left_on="municipality", right_on="MUN_NORDIC"
    )

    def fill_region_dk(row):
        if (
            row["municipality"]
            in mun[mun["REG_NORDIC"] == "Hovedstaden"]["MUN_NORDIC"].tolist()
        ):
            return "Hovedstaden"
        elif (
            row["municipality"]
            in mun[mun["REG_NORDIC"] == "Sjælland"]["MUN_NORDIC"].tolist()
        ):
            return "Sjælland"
        else:
            return None

    gcr__DK_age["region"] = gcr__DK_age.apply(fill_region_dk, axis=1)
    gcr__DK_age = gcr__DK_age[
        (gcr__DK_age["REG_NORDIC"] == "Hovedstaden")
        | (gcr__DK_age["REG_NORDIC"] == "Sjælland")
    ]

    # merge DK and SE age structure data

    gcr_age = pd.concat([gcr__SE_age, gcr__DK_age])
    gcr_age = gcr_age.drop(["COD_MUN", "COD_REG", "NUTS3_2016", "DGURBA"], axis=1)
    gcr_age.reset_index(inplace=True, drop=True)
    gcr_age = gcr_age.melt(
        id_vars=[
            "municipality",
            "age",
            "region",
            "geometry",
            "centroid",
            "lat",
            "lon",
            "MUN_NORDIC",
            "REG_NORDIC",
            "CNTR",
        ],
        var_name="year",
    )

    # add age groups to DK and SE age structure data

    age_groups = {"youth": (0, 19), "working age": (20, 64), "elderly": (65, 100)}

    def map_age_group(age):
        if pd.isnull(age):
            return None
        age = str(age).split()[0]
        try:
            age = int(age) if age != "126+" else 126
            for group, (lower, upper) in age_groups.items():
                if lower <= age <= upper:
                    return group
            return "elderly"
        except ValueError:
            return None

    gcr_age["age group"] = gcr_age["age"].apply(map_age_group)

    gcr_age = (
        gcr_age.groupby(["municipality", "year", "age group"])
        .agg(
            {
                "value": "sum",
                "region": "first",
                "geometry": "first",
                "centroid": "first",
                "lat": "first",
                "lon": "first",
                "MUN_NORDIC": "first",
                "REG_NORDIC": "first",
                "CNTR": "first",
            }
        )
        .reset_index()
    )

    # add the percentage of the total population for each age group

    df = gcr_age

    grouped = df.groupby(["municipality", "year", "age group"]).agg(
        {
            "value": "sum",
            "region": "first",
            "geometry": "first",
            "centroid": "first",
            "lat": "first",
            "lon": "first",
            "MUN_NORDIC": "first",
            "REG_NORDIC": "first",
            "CNTR": "first",
        }
    )

    total_population = gcr_age.groupby(["municipality", "year"]).agg({"value": "sum"})

    merged = grouped.merge(
        total_population,
        left_on=["municipality", "year"],
        right_index=True,
        suffixes=("_grouped", "_total"),
    )

    merged["percentage"] = (merged["value_grouped"] / merged["value_total"]) * 100

    gcr_age = merged.reset_index()

    gcr_age.sort_values(["municipality", "year", "age group"], inplace=True)

    # load DK internal migration data by municipality
    # Source: FLY66: Internal migration between municipalities by sex, age and municipality

    dk_raw = pd.read_csv("data/DK_data_migration.csv")

    def process_dk(df):
        df = df.rename(
            columns={
                "TILKOMMUNE": "to",
                "FRAKOMMUNE": "from",
                "ALDER": "age",
                "TID": "year",
                "INDHOLD": "value",
            }
        )
        df["to"] = df["to"].str[4:]
        df["from"] = df["from"].str[4:]

        migrated_to = (
            df.drop(["from"], axis=1)
            .groupby(by=["to", "year", "age"])
            .sum()
            .reset_index()
            .rename(columns={"to": "municipality", "value": "to"})
        )

        migrated_from = (
            df.drop(["to"], axis=1)
            .groupby(by=["from", "year", "age"])
            .sum()
            .reset_index()
            .rename(columns={"value": "from", "from": "municipality"})
        )

        return pd.merge(
            migrated_to,
            migrated_from,
            on=["municipality", "year", "age"],
            how="outer",
        )

    df_dk = process_dk(dk_raw)

    # add age groups

    df_dk["age group"] = df_dk["age"].apply(map_age_group)

    df_dk = (
        df_dk.groupby(["municipality", "year", "age group"])
        .agg(
            {
                "to": "sum",
                "from": "sum",
            }
        )
        .reset_index()
    )

    df_dk["net migration"] = df_dk["to"] - df_dk["from"]
    df_dk["year"] = df_dk["year"].astype(str)

    # load SE internal migration data by municipality
    # Source: Migration by region, age and sex. Year 1997 - 2022

    se_raw = pd.merge(
        left=(
            pd.read_csv("se_in.csv", sep=";", encoding="ISO-8859-1").melt(
                id_vars=["region", "age"], var_name="year", value_name="to"
            )
        ),
        right=(
            pd.read_csv("se_out.csv", sep=" ", encoding="ISO-8859-1").melt(
                id_vars=["region", "age"], var_name="year", value_name="from"
            )
        ),
    ).rename(columns={"region": "municipality"})

    def process_se(df):

        df["municipality"] = df["municipality"].str[5:]
        df["age group"] = df["age"].apply(map_age_group)

        df = (
            df.groupby(["municipality", "year", "age group"])
            .agg(
                {
                    "to": "sum",
                    "from": "sum",
                }
            )
            .reset_index()
        )

        df["net migration"] = df["to"] - df["from"]
        return df

    df_se = process_se(se_raw)

    # merge dk and se migration data

    migration = pd.merge(
        df_dk,
        df_se,
        on=["municipality", "year", "age group", "to", "from", "net migration"],
        how="outer",
    )
    migration["year"] = migration["year"].astype(str)

    # add data on internal migration
    gcr = pd.merge(
        gcr_age, migration, on=["municipality", "year", "age group"], how="outer"
    )

    gcr["region"] = gcr.apply(fill_region_dk, axis=1)
    gcr = gcr[
        (gcr["REG_NORDIC"] == "Hovedstaden")
        | (gcr["REG_NORDIC"] == "Sjælland")
        | (gcr["REG_NORDIC"] == "Skåne")
        | (gcr["REG_NORDIC"] == "Halland")
    ]

    column_order = [
        "municipality",
        "year",
        "age group",
        "REG_NORDIC",
        "CNTR",
        "geometry",
        "centroid",
        "lat",
        "lon",
        "value_grouped",
        "value_total",
        "net migration",
    ]
    gcr = gcr[column_order]
    gcr.rename(columns={"REG_NORDIC": "region", "CNTR": "country"}, inplace=True)

    return gpd.GeoDataFrame(gcr).to_parquet("data.parquet")


def load(target_file="data.parquet"):
    df = gpd.read_parquet(target_file)

    df_py = df.copy()
    df_py["year"] = (df_py["year"].astype(int) + 1).astype(str)

    merged = df.merge(
        df_py,
        how="left",
        on=["municipality", "year", "age group"],
        suffixes=["", "_prev"],
    )

    column_order = [
        "municipality",
        "year",
        "age group",
        "region",
        "country",
        "geometry",
        "centroid",
        "lat",
        "lon",
        "value_grouped",
        "value_total",
        "net migration",
        "value_grouped_prev",
        "value_total_prev",
        "net migration_prev",
    ]

    merged = merged[column_order]
    return merged
