import streamlit as st
import pandas as pd
import folium
from folium.plugins import HeatMap
from streamlit_folium import folium_static
import joblib
from datetime import datetime

# Set Streamlit page config
st.set_page_config(layout="wide", page_title="PM2.5 Prediction Dashboard", page_icon="🌍")

# Logo and title section
with st.container():
    cols = st.columns([1, 8])
    with cols[0]:
        st.image("D:\ISRO Hackthon 2025\Team Logo.png", width=100)
    with cols[1]:
        st.title("🌍 AirCast:AI-Driven PM2.5 Forecasting")
        st.markdown("""
        This dashboard allows users to upload satellite + weather grid data and view predicted PM2.5 air pollution values on an interactive map.
        """)

# Load pre-trained model
@st.cache_resource
def load_model():
    return joblib.load("rf_model.pkl")

model = load_model()

# Sidebar: Upload
st.sidebar.header("📤 Upload Section")
uploaded_file = st.sidebar.file_uploader("Upload Grid CSV", type=["csv"])

# Main content
if uploaded_file:
    df = pd.read_csv(uploaded_file)

    # Convert date column
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'])

    # Rename columns if needed
    if 'temp' in df.columns:
        df.rename(columns={"temp": "Temp", "u": "U wind", "v": "V wind"}, inplace=True)

    # Check required columns
    required_cols = ['AOD', 'Temp', 'RH', 'U wind', 'V wind', 'PBL']
    if all(col in df.columns for col in required_cols):

        # Date Filter
        if 'date' in df.columns:
            with st.expander("📅 Filter by Date", expanded=True):
                unique_dates = sorted(df['date'].dt.date.unique())
                selected_date = st.slider("Select Date", min_value=min(unique_dates), max_value=max(unique_dates), value=min(unique_dates))
                df = df[df['date'].dt.date == selected_date]

        # Predict
        X = df[required_cols]
        df['PM2.5'] = model.predict(X)
        df['weight'] = (df['PM2.5'] - df['PM2.5'].min()) / (df['PM2.5'].max() - df['PM2.5'].min())

        st.success("✅ PM2.5 Predictions Completed")

        # Section 1: Table
        with st.expander("📋 Data Table", expanded=False):
            st.dataframe(df[['lat', 'lon', 'PM2.5']])

        # Section 2: Download Button
        with st.expander("💾 Download Predicted Data", expanded=False):
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Download CSV", csv, "pm25_predictions.csv", "text/csv")

        # Section 3: Map
        st.subheader("🗺️ PM2.5 Prediction Heatmap")
        m = folium.Map(location=[df['lat'].mean(), df['lon'].mean()], zoom_start=7)
        heat_data = [[row['lat'], row['lon'], row['weight']] for _, row in df.iterrows()]
        HeatMap(heat_data, radius=12, blur=18, max_zoom=10).add_to(m)

        # Threshold circles
        for _, row in df.iterrows():
            color = 'green' if row['PM2.5'] <= 60 else 'orange' if row['PM2.5'] <= 90 else 'red'
            folium.CircleMarker(
                location=[row['lat'], row['lon']],
                radius=5,
                color=color,
                fill=True,
                fill_opacity=0.6,
                tooltip=f"PM2.5: {row['PM2.5']:.1f}"
            ).add_to(m)

        folium_static(m)

    else:
        st.error(f"❌ Missing required columns: {', '.join(set(required_cols) - set(df.columns))}")

else:
    st.info("Upload a grid CSV with columns: lat, lon, AOD, Temp, RH, U wind, V wind, PBL")

# About Section
with st.expander("ℹ️ About this Project"):
    st.markdown("""
    **Project Title**: Monitoring Air Pollution from Space using Satellite Observations and AI/ML

    **Goal**: Predict surface-level PM2.5 concentrations using satellite-based AOD, weather reanalysis data, and ground truth models.

    **Technologies Used**: Python, Random Forest, Streamlit, Folium, Pandas, INSAT-3D, ERA5/MERRA2

    **Team**: [TechnoBits]
    """)
