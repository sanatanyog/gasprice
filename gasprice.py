import streamlit as st
import requests
from bs4 import BeautifulSoup
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# (Include your CXO_COLORS and helper functions get_fuel_data, get_gas_data, 
# get_diesel_data, get_lpg_data, get_electricity_data,
# display_price_analysis, display_electricity_analysis here)

def main():
    st.set_page_config(page_title="Energy Price Dashboard", layout="centered", page_icon="⚡")
    st.markdown(f"<h1 style='color:{CXO_COLORS['primary']};'>Global Energy Price Analysis</h1>", unsafe_allow_html=True)

    # --- Dropdown to select energy type ---
    energy_type = st.selectbox(
        "Select Energy Type",
        ["Gasoline", "Diesel", "LPG", "Electricity"]
    )

    # --- Load and display based on selection ---
    if energy_type == "Gasoline":
        df, label = get_gas_data()
        display_price_analysis(df, label, unit_label="$")
    elif energy_type == "Diesel":
        df, label = get_diesel_data()
        display_price_analysis(df, label, unit_label="$")
    elif energy_type == "LPG":
        df, label = get_lpg_data()
        display_price_analysis(df, label, unit_label="$")
    else:  # Electricity
        df, q_label = get_electricity_data()
        display_electricity_analysis(df, q_label)

if __name__ == "__main__":
    main()
