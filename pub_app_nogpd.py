## SEPARATE DASHBOARD REPO VERSION ##
# DASHBOARD CODE #

#load libraries
import streamlit as st
#import geopandas as gpd
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
    df_cha = pd.read_csv('all_merged.csv')
    
    # load census tract geodata
    #df_census = gpd.read_file('CensusTractsTIGER2010_20260303.geojson')
    #df_census = df_census.rename(columns={'geoid10':'GEOID'})

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
    #df_pharm['geometry'] = gpd.GeoSeries.from_wkt(
    #    df_pharm['New Georeferenced Column'],
    #    on_invalid='ignore'
   # )
    # drop failed parses
    #df_pharm = df_pharm.dropna(subset=['geometry'])
    # create geodataframe
    #pharm_gdf = gpd.GeoDataFrame(
    #    df_pharm,
    #    geometry='geometry',
    #    crs='EPSG:4326'
    #    )
    
    # merge census tract and pharmacy location data
   # combined2_gdf = gpd.sjoin(df_census, pharm_gdf, 
   #             how='left',
    #            predicate='intersects')
    # rename geo id column for merging 
   # combined2_gdf = combined2_gdf.rename(columns={'geoid10':'GEOID'})

    # merge all data together: pharmacy location, census tract, and health data by census tract
  #  cha_pharm = combined2_gdf.merge(df_cha, on='GEOID')

    return df_cha

df_cha = load_data()


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
sample_options = {'cha': 'All Census Tracts', 'low_inc': 'Low (Below City Median) Median Household Income', 'hdx': 'High Hardship Index', 'senior': 'High Percentage of Seniors Living Alone'}


# ── Page config ────────────────────────────────────────────────
st.set_page_config(page_title="Chicago Health and Pharmacy Access Dashboard", layout="wide")
st.title("Chicago Health and Pharmacy Access Dashboard")
st.subheader("Data Definitions:")
st.text("Transporation Burden: a percentile value based on average cost and time spent on transportation (a higher value indicates a higher transportation burden)")
st.text('Hardship Index: a numerical score that tries to quantify community hardship based on unemployment, age dependency, education, per capita income, crowded housing, and poverty')

# ── Sidebar controls ──────────────────────────────────────────
# show barplots?
show_barplot = st.sidebar.checkbox("Show density plot", value=False)
# bar plot options
if show_barplot:
    demographics = st.sidebar.selectbox("Density Plot Sample Options", sample_options.values())

# show scatter plots?
show_scatter = st.sidebar.checkbox("Show scatterplot", value=True)

scatter_x_options = {'INC_2020-2024':'Median Household Income', 'RITB_2022':'Transportation Burden Percentile', 'EKW_2024':'Walkability Score', 'POV_2020-2024':'Poverty Rate'}
scatter_y_options = {'pharm_density': 'Pharmacy Density', 'pharm_per_1000': 'Pharmacies per 1000 Residents', 'RITB_2022':'Transportation Burden Percentile'}

# source: https://discuss.streamlit.io/t/format-func-function-examples-please/11295
if show_scatter:
    scatter_x_select = st.sidebar.selectbox("Scatterplot x-axis:", list(scatter_x_options.keys()),
                                      format_func=lambda x: scatter_x_options[x])
    scatter_y_select = st.sidebar.selectbox("Scatterplot y-axis:", list(scatter_y_options.keys()),
                                      format_func=lambda y: scatter_y_options[y])


# scatter plot options
#show_unchanged = st.sidebar.checkbox("Show routes with no cuts", value=True)
#mode_filter = st.sidebar.multiselect("Mode", ["Bus", "L"], default=["Bus", "L"])


# CREATE BAR PLOT
def create_plot(df=df_cha):
    # determine which data subset to use
    if demographics == 'All Census Tracts':
        df = df_cha
    if demographics == 'Low (Below City Median) Median Household Income':
        df = low_inc
    if demographics == 'High Hardship Index':
        df = hdx
    if demographics == 'High Percentage of Seniors Living Alone':
        df = senior
    
    transpo = alt.Chart(df, title=f"Chicago Transportation Burden by Census Tract ({demographics})").mark_bar(color='navy').encode(
        alt.X('Name:N', title='Census Tract Number', sort = alt.EncodingSortField(field='RITB_2022', order = 'descending')),
        alt.Y('RITB_2022:Q', title='Transportation Burden (Percentile)')
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

if show_barplot:
    st.altair_chart(create_plot(), use_container_width=True)

# CREATE SCATTER PLOT
def make_scatterplot(x_col, y_col):
    scatter = alt.Chart(df_cha).mark_point().encode(
        alt.X(x_col, title=scatter_x_options[x_col]),
        alt.Y(y_col, title=scatter_y_options[y_col])
    ).properties(title=f"{scatter_x_options[x_col]} and {scatter_y_options[y_col]}", height=600)

    return scatter

if show_scatter:
    st.altair_chart(make_scatterplot(scatter_x_select, scatter_y_select), use_container_width=True)

