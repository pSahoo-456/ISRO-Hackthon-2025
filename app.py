import streamlit as st
import pandas as pd
import folium
from folium.plugins import HeatMap
from streamlit_folium import folium_static
import joblib
from datetime import datetime

# Set page config
st.set_page_config(layout="wide", page_title="PM2.5 Prediction Dashboard", page_icon="🌍")

# --- HEADER SECTION ---
with st.container():
    st.title("🌍 AirCast: AI-Driven PM2.5 Forecasting")
    st.markdown("Upload satellite + weather grid data and view predicted PM2.5 levels on an interactive map.")

# --- LOAD MODEL ---
@st.cache_resource
def load_model():
    return joblib.load("rf_model.pkl")

model = load_model()

# --- SIDEBAR UPLOAD ---
st.sidebar.header("📤 Upload Section")
uploaded_file = st.sidebar.file_uploader("Upload Grid CSV", type=["csv"])

# --- PM2.5 LEVEL CATEGORIZATION FUNCTION ---
def categorize_pm25(value):
    if value <= 30:
        return "Good"
    elif value <= 60:
        return "Satisfactory"
    elif value <= 90:
        return "Moderate"
    elif value <= 120:
        return "Poor"
    elif value <= 250:
        return "Very Poor"
    else:
        return "Severe"

# --- MAIN APP LOGIC ---
if uploaded_file:
    df = pd.read_csv(uploaded_file)

    # Convert date column
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'])

   
    if 'temp' in df.columns:
        df.rename(columns={"temp": "Temp", "u": "U wind", "v": "V wind"}, inplace=True)

    required_cols = ['AOD', 'Temp', 'RH', 'U wind', 'V wind', 'PBL']
    if all(col in df.columns for col in required_cols):

        # Date filter 
        if 'date' in df.columns:
            with st.expander("📅 Filter by Date", expanded=True):
                unique_dates = sorted(df['date'].dt.date.unique())
                selected_date = st.slider("Select Date", min_value=min(unique_dates), max_value=max(unique_dates), value=min(unique_dates))
                df = df[df['date'].dt.date == selected_date]

        # Predict
        X = df[required_cols]
        df['PM2.5'] = model.predict(X)
        df['PM2.5'] = df['PM2.5'].round(1)
        df['weight'] = (df['PM2.5'] - df['PM2.5'].min()) / (df['PM2.5'].max() - df['PM2.5'].min())
        df['AQI Level'] = df['PM2.5'].apply(categorize_pm25)

        st.success("✅ PM2.5 Predictions Completed")

        # --- SUMMARY STATS ---
        with st.container():
            st.subheader("📊 Summary Statistics")
            c1, c2, c3 = st.columns(3)
            c1.metric("Average PM2.5", f"{df['PM2.5'].mean():.1f} µg/m³")
            c2.metric("Max PM2.5", f"{df['PM2.5'].max():.1f} µg/m³")
            c3.metric("Most Common Level", df['AQI Level'].mode()[0])

        # --- TABLE ---
        with st.expander("📋 Data Table", expanded=False):
            st.dataframe(df[['lat', 'lon', 'PM2.5', 'AQI Level']])

        # --- DOWNLOAD BUTTON ---
        with st.expander("💾 Download Predicted Data", expanded=False):
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Download CSV", csv, "pm25_predictions.csv", "text/csv")

        # --- HEATMAP + MARKERS ---
        st.subheader("🗺️ PM2.5 Prediction Heatmap")
        m = folium.Map(location=[df['lat'].mean(), df['lon'].mean()], zoom_start=7)
        heat_data = df[['lat', 'lon', 'weight']].dropna().values.tolist()
        HeatMap(heat_data, radius=12, blur=18, max_zoom=10).add_to(m)

        # Circle markers with AQI tooltip
        for _, row in df.iterrows():
            color = 'green' if row['PM2.5'] <= 60 else 'orange' if row['PM2.5'] <= 90 else 'red'
            folium.CircleMarker(
                location=[row['lat'], row['lon']],
                radius=5,
                color=color,
                fill=True,
                fill_opacity=0.6,
                tooltip=f"PM2.5: {row['PM2.5']} µg/m³\nLevel: {row['AQI Level']}"
            ).add_to(m)

        folium_static(m)

    else:
        st.error(f"❌ Missing required columns: {', '.join(set(required_cols) - set(df.columns))}")
else:
    st.info("Upload a grid CSV with columns: lat, lon, AOD, Temp, RH, U wind, V wind, PBL")

# --- ABOUT SECTION ---
with st.expander("ℹ️ About this Project"):
    st.markdown("""
    **Project Title**: Monitoring Air Pollution from Space using Satellite Observations and AI/ML  
    **Goal**: Predict surface-level PM2.5 concentrations using satellite-based AOD, weather reanalysis data, and machine learning.  
    **Technologies Used**: Python, Random Forest, Streamlit, Folium, Pandas, INSAT-3D, ERA5/MERRA2  
    **Team**: TechnoBits  
    """)
