## SEPARATE DASHBOARD REPO VERSION ##
# DASHBOARD CODE #

#load libraries
import streamlit as st
import geopandas as gpd
import pandas as pd
import numpy as np
import altair as alt
#import pydeck as pdk
import json

# load data
#cha = pd.read_csv('/Users/ariannawooten/Downloads/final_project_AWJP_w26/data/raw-data/Chicago Health Atlas Data Download - Census Tracts.csv')#chicago health atlas data (2020)
@st.cache_data

def load_data():
    # load health (cha) data
    df_cha = pd.read_csv('Chicago_Health_Atlas_Data.csv')
    # remove first 3 rows, which have data definitions, citations, etc.
    df_cha = df_cha.iloc[4:809]
    # convert to gdf
    df_cha = gpd.GeoDataFrame(
    df_cha, geometry=gpd.points_from_xy(
        df_cha.Longitude, df_cha.Latitude), 
        crs="EPSG:4326")

    # load census tract geodata
    df_census = gpd.read_file('CensusTractsTIGER2010_20260303.geojson')
    
    # load pharmacy data and convert to gdf
    df_pharm = pd.read_csv('Pharmacy_Status_-_Historical_20260302.csv').dropna(subset=['New Georeferenced Column'])
    # drop nas
    df_pharm = df_pharm.dropna(subset=['New Georeferenced Column'])

    # drop na strings
    df_pharm = df_pharm[
        df_pharm['New Georeferenced Column']
        .str.lower()
        .ne('nan')
    ]

    # convert wkt to a geometry
    df_pharm['geometry'] = gpd.GeoSeries.from_wkt(
        df_pharm['New Georeferenced Column'],
        on_invalid='ignore'
    )
    # drop failed parses
    df_pharm = df_pharm.dropna(subset=['geometry'])
    # create geodataframe
    pharm_gdf = gpd.GeoDataFrame(
        df_pharm,
        geometry='geometry',
        crs='EPSG:4326'
        )
    
    # merge census tract and pharmacy location data
    combined2_gdf = gpd.sjoin(df_census, pharm_gdf, 
                how='left',
                predicate='intersects')
    # rename geo id column for merging 
    combined2_gdf = combined2_gdf.rename(columns={'geoid10':'GEOID'})

    return df_cha, df_census, pharm_gdf

df_cha, df_census, pharm_gdf = load_data()


# make the tract names numeric (https://www.statology.org/pandas-remove-characters-from-string/)
df_cha['Name'] = df_cha['Name'].str.replace('Tract ', '')

# create data subsets with different categories of census tracts
# first convert income column to numeric data type
df_cha['INC_2020-2024'] = pd.to_numeric(df_cha['INC_2020-2024'], downcast=None)

# create df for below median income tracts
low_inc = df_cha[df_cha['INC_2020-2024']< df_cha['INC_2020-2024'].median()]

# create df for above median hardship index
df_cha['HDX_2020-2024'] = pd.to_numeric(df_cha['HDX_2020-2024'], downcast=None)
hdx = df_cha[df_cha['HDX_2020-2024'] > df_cha['HDX_2020-2024'].median()]

# create df for above median percentage of seniors living alone
df_cha['SLA-S_2020-2024'] = pd.to_numeric(df_cha['SLA-S_2020-2024'], downcast=None)
senior = df_cha[df_cha['SLA-S_2020-2024'] > df_cha['SLA-S_2020-2024'].median()]


# create histogram: proximity to roads, railways, and airports by census
#hist = alt.Chart(cha).mark_bar().encode(
#    alt.X('Name:N', title='Census Tract', 
#    sort = alt.EncodingSortField(field='EKR_2024', order = 'descending')),
#    alt.Y('average(EKR_2024):Q', title = 'Proximity to Roads, Railways, and Airports')
#    )

#hist

#scatter = alt.Chart(cha).mark_point().encode(
#    alt.X('Name:O'),
#    alt.Y('EKR_2024')
#)

#scatter

# bar plot 2: median household income by census tract
#hist2 = alt.Chart(cha).mark_bar().encode(
#    alt.X('Name:O', title='Census Tract', sort = alt.EncodingSortField(field='INC_2020-2024', order = 'descending')),
#    alt.Y('INC_2020-2024:Q', title='Median Household Income')
#)

#hist2

# transportation burden plot
#transpo = alt.Chart(cha).mark_bar().encode(
#    alt.X('Name:O', title='Census Tract', sort = alt.EncodingSortField(field='RITB_2022', order = 'descending')),
#    alt.Y('RITB_2022:Q', title='Transportation Burden (Percentile)')
#    )

#transpo

#demo_options = ['All', 'Low Median Household Income','Hardship Index', 'Percentage of Seniors Living Alone']
sample_options = {'cha': 'All', 'low_inc': 'Low Median Household Income', 'hdx': 'High Hardship Index', 'senior': 'High Percentage of Seniors Living Alone'}


# ── Page config ────────────────────────────────────────────────
st.set_page_config(page_title="Chicago Health and Pharmacy Access Dashboard", layout="wide")
st.title("Chicago Health and Pharmacy Access Dashboard")

# ── Sidebar controls ──────────────────────────────────────────
demographics = st.sidebar.selectbox("Sample Options", sample_options.values())

#show_unchanged = st.sidebar.checkbox("Show routes with no cuts", value=True)
#mode_filter = st.sidebar.multiselect("Mode", ["Bus", "L"], default=["Bus", "L"])

st.subheader(f"Chicago Transportation Burden by Census Tract ({demographics})")

def create_plot(df=df_cha):
    # determine which data subset to use
    if demographics == 'All':
        df = df_cha
    if demographics == 'Low Median Household Income':
        df = low_inc
    if demographics == 'High Hardship Index':
        df = hdx
    if demographics == 'High Percentage of Seniors Living Alone':
        df = senior
    
    transpo = alt.Chart(df).mark_bar(color='navy').encode(
        alt.X('Name:O', title='Census Tract', sort = alt.EncodingSortField(field='average(RITB_2022):Q', order = 'descending')).bin(),
        alt.Y('average(RITB_2022):Q', title='Transportation Burden (Percentile)')
    )

    # add a line showing the 50th percentile
    # source: https://stackoverflow.com/questions/77802979/how-to-draw-a-horizontal-line-at-y-0-in-an-altair-line-chart
    median = alt.Chart(pd.DataFrame({'y': [50]})).mark_rule(
        color='red',
        size=2
        ).encode(
        y='y:Q'
        )

    transpo = transpo + median
    return(transpo)

st.altair_chart(create_plot(), use_container_width=True)


#### test

