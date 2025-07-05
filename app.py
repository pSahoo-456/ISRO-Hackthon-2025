import streamlit as st
import pandas as pd
import folium
from folium.plugins import HeatMap
from streamlit_folium import st_folium
import joblib

# Load the trained model
model = joblib.load("rf_model.pkl")

st.set_page_config(layout="wide")
st.title("🌍 PM2.5 Prediction & Visualization")
st.markdown("Upload a grid CSV file with AOD, weather features to predict and view PM2.5 spatially.")

# File uploader
uploaded_file = st.file_uploader("📤 Upload CSV File (lat, lon, AOD, Temp, RH, U wind, V wind, PBL)", type=["csv"])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    st.success("File Uploaded Successfully!")

 
    rename_map = {'temp': 'Temp', 'u': 'U wind', 'v': 'V wind'}
    df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns}, inplace=True)

    required_cols = ['AOD', 'Temp', 'RH', 'U wind', 'V wind', 'PBL']

    if all(col in df.columns for col in required_cols):
        X = df[required_cols]
        df['PM2.5'] = model.predict(X)

        st.subheader("Sample of Predictions")
        st.dataframe(df.head())

        # Interactive Heatmap
        st.subheader("🗺️ PM2.5 Heatmap")
        map_center = [df['lat'].mean(), df['lon'].mean()]
        m = folium.Map(location=map_center, zoom_start=7)

        heat_data = [[row['lat'], row['lon'], row['PM2.5']] for index, row in df.iterrows()]
        HeatMap(heat_data, radius=10, blur=15).add_to(m)

        st_folium(m, width=1000, height=600)

        # Downloadable prediction CSV
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download Prediction CSV", csv, "predicted_pm25.csv", "text/csv")

    else:
        st.error("Uploaded file must contain: AOD, Temp, RH, U wind, V wind, PBL, lat, lon")
else:
    st.info("⬆Upload a CSV file to get started.")

st.markdown("Developed by Team [TechnoBits] for ISRO Hackathon 🚀")
