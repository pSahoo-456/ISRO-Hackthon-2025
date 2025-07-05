import streamlit as st
import pandas as pd
import folium
from folium.plugins import HeatMap
from streamlit_folium import st_folium
import joblib
from PIL import Image

# Load logo
logo_path = "D:\ISRO Hackthon 2025\Team Logo.png"
logo = Image.open(logo_path)

# Load the trained model
model = joblib.load("rf_model.pkl")

# Set page config
st.set_page_config(page_title="PM2.5 Predictor - TechnoBits", layout="wide", page_icon="🛰️")

# Simple professional style
st.markdown("""
    <style>
    .main {
        background-color: #f8f9fa;
        color: #333333;
    }
    .title-style {
        font-size: 40px;
        color: #0056b3;
        font-weight: 600;
    }
    .subtitle-style {
        font-size: 18px;
        color: #343a40;
    }
    .footer-style {
        text-align: center;
        font-size: 14px;
        color: #6c757d;
        margin-top: 50px;
    }
    </style>
""", unsafe_allow_html=True)

# Display logo and title
col1, col2 = st.columns([1, 8])
with col1:
    st.image(logo, width=100)
with col2:
    st.markdown("<div class='title-style'>TechnoBits PM2.5 Predictor</div>", unsafe_allow_html=True)
    st.markdown("<div class='subtitle-style'>Upload satellite and weather data to predict and visualize surface PM2.5 levels.</div>", unsafe_allow_html=True)

# File uploader
uploaded_file = st.file_uploader("📤 Upload CSV File (lat, lon, AOD, Temp, RH, U wind, V wind, PBL)", type=["csv"])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    st.success("File Uploaded Successfully!")

    # Rename columns if needed
    rename_map = {'temp': 'Temp', 'u': 'U wind', 'v': 'V wind'}
    df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns}, inplace=True)

    required_cols = ['AOD', 'Temp', 'RH', 'U wind', 'V wind', 'PBL']

    if all(col in df.columns for col in required_cols):
        X = df[required_cols]
        df['PM2.5'] = model.predict(X)

        st.subheader("Sample of Predictions")
        st.dataframe(df.head(), use_container_width=True)

        # Interactive Heatmap
        st.subheader("🗺️ PM2.5 Heatmap")
        map_center = [df['lat'].mean(), df['lon'].mean()]
        m = folium.Map(location=map_center, zoom_start=7)

        heat_data = [[row['lat'], row['lon'], row['PM2.5']] for index, row in df.iterrows()]
        HeatMap(heat_data, radius=10, blur=15).add_to(m)

        st_data = st_folium(m, width=1000, height=600)

        # Downloadable prediction CSV
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download Prediction CSV", csv, "predicted_pm25.csv", "text/csv")

    else:
        st.error("Uploaded file must contain: AOD, Temp, RH, U wind, V wind, PBL, lat, lon")
else:
    st.info("Upload a CSV file to get started.")

# Footer
st.markdown("<div class='footer-style'>Made with ❤️ by Team <b>TechnoBits</b></div>", unsafe_allow_html=True)