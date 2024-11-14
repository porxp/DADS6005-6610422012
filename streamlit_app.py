import pandas as pd
import streamlit as st
import plotly.express as px
from pinotdb import connect
from datetime import datetime

# Set Streamlit to wide mode
st.set_page_config(layout="wide")

# Connect to Pinot
conn = connect(host='13.212.187.70', port=8099, path='/query/sql', scheme='http')
curs = conn.cursor()

# Streamlit App Layout
st.title("Pageview Activity Analytics")

# Show the last update time
now = datetime.now()
dt_string = now.strftime("%d %B %Y %H:%M:%S")
st.write(f"Last update: {dt_string}")

# Sidebar Filters
st.sidebar.markdown("### Filters")
# Gender Filter
query_gender = """
SELECT DISTINCT GENDER
FROM PageviewActivity_REALTIME
"""
curs.execute(query_gender)
gender_options = [row[0] for row in curs]
selected_genders = st.sidebar.multiselect(
    "Select Genders to Display",
    options=gender_options,
    default=gender_options
)

# Region Filter
query_region = """
SELECT DISTINCT REGIONID
FROM PageviewActivity_REALTIME
"""
curs.execute(query_region)
region_options = [row[0] for row in curs]
selected_regions = st.sidebar.multiselect(
    "Select Regions to Display",
    options=region_options,
    default=region_options
)

# Query 1: Distribution of Activities
query1 = """
SELECT ACTIVITY, COUNT(*) as Count
FROM PageviewActivity_REALTIME
GROUP BY ACTIVITY
ORDER BY Count DESC
"""
curs.execute(query1)
df_activities = pd.DataFrame(curs, columns=[item[0] for item in curs.description])

# Query 3: Total View Time by Gender
query3 = f"""
SELECT GENDER, SUM(CAST(VIEWTIME AS LONG)) as TotalViewTime
FROM PageviewActivity_REALTIME
WHERE GENDER IN ({', '.join("'" + g + "'" for g in selected_genders)})
GROUP BY GENDER
"""
curs.execute(query3)
df_viewtime_gender = pd.DataFrame(curs, columns=[item[0] for item in curs.description])

# Query 2: Activity Distribution by Gender
query2 = f"""
SELECT GENDER, ACTIVITY, COUNT(*) as Count
FROM PageviewActivity_REALTIME
WHERE GENDER IN ({', '.join("'" + g + "'" for g in selected_genders)})
GROUP BY GENDER, ACTIVITY
ORDER BY GENDER, Count DESC
"""
curs.execute(query2)
df_activity_gender = pd.DataFrame(curs, columns=[item[0] for item in curs.description])
df_activity_gender_pivot = df_activity_gender.pivot(index='GENDER', columns='ACTIVITY', values='Count').fillna(0)

# Query 4: Total Viewtime by Region
query4 = f"""
SELECT REGIONID, SUM(CAST(VIEWTIME AS LONG)) as TotalViewTime
FROM PageviewActivity_REALTIME
WHERE REGIONID IN ({', '.join("'" + str(r) + "'" for r in selected_regions)})
GROUP BY REGIONID
ORDER BY TotalViewTime DESC
"""
curs.execute(query4)
df_viewtime_region = pd.DataFrame(curs, columns=[item[0] for item in curs.description])
df_viewtime_region_filtered = df_viewtime_region[df_viewtime_region['REGIONID'].isin(selected_regions)]

# Adjusted row layout to reduce height
col1, col2 = st.columns([1, 1])  # Balanced columns for better fitting

with col1:
    st.markdown("<h3 style='font-size: 18px;'>1. Distribution of Activities</h3>", unsafe_allow_html=True)
    fig1 = px.bar(
        df_activities,
        y='ACTIVITY',
        x='Count',
        color='ACTIVITY',
        labels={'ACTIVITY': 'Activity Type', 'Count': 'Count'},
        title='',
        orientation='h',
        width=600,
        height=300  # Reduced height
    )
    fig1.update_layout(showlegend=False)
    st.plotly_chart(fig1, use_container_width=True)

with col2:
    st.markdown("<h3 style='font-size: 18px;'>2. Total View Time by Gender</h3>", unsafe_allow_html=True)
    fig2 = px.pie(
        df_viewtime_gender,
        names='GENDER',
        values='TotalViewTime',
        title='',
        hole=0.4,
        width=600,
        height=300  # Reduced height
    )
    fig2.update_traces(textinfo='percent+label')
    fig2.update_layout(showlegend=False)
    st.plotly_chart(fig2, use_container_width=True)

col3, col4 = st.columns([1, 1])

with col3:
    st.markdown("<h3 style='font-size: 18px;'>3. Activity Distribution by Gender</h3>", unsafe_allow_html=True)
    fig3 = px.bar(df_activity_gender_pivot, barmode='stack', labels={'value': 'Count'},
                  title='',
                  width=600,
                  height=300  # Reduced height
    )
    fig3.update_traces(texttemplate=None)
    st.plotly_chart(fig3, use_container_width=True)

with col4:
    st.markdown("<h3 style='font-size: 18px;'>4. Total Viewtime by Region</h3>", unsafe_allow_html=True)
    df_viewtime_region_sorted = df_viewtime_region_filtered.sort_values(by='TotalViewTime', ascending=True)

    def format_value(value):
        if value >= 1e9:
            return f"{value / 1e9:.2f}B"
        elif value >= 1e6:
            return f"{value / 1e6:.2f}M"
        elif value >= 1e4:
            return f"{value / 1e4:.2f}K"
        else:
            return f"{value:.2f}"

    df_viewtime_region_sorted['FormattedTotalViewTime'] = df_viewtime_region_sorted['TotalViewTime'].apply(format_value)

    fig4_treemap = px.treemap(
        df_viewtime_region_sorted,
        path=['REGIONID'],
        values='TotalViewTime',
        labels={'TotalViewTime': 'Total View Time', 'REGIONID': 'Region ID'},
        title='',
        width=600,
        height=300  # Reduced height
    )

    fig4_treemap.update_traces(
        texttemplate='%{label}<br>Total View Time: %{customdata}',
        hovertemplate='%{label}<br>Total View Time: %{customdata}',
        customdata=df_viewtime_region_sorted['FormattedTotalViewTime']
    )
    
    st.plotly_chart(fig4_treemap, use_container_width=True)
