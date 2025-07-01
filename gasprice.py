import streamlit as st
import requests
from bs4 import BeautifulSoup
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px
import re

# Professional CXO Color Palette
CXO_COLORS = {
    "primary": "#224088",      # Royal Blue
    "accent": "#BF9A4A",       # Gold
    "secondary": "#EEEDE9",    # Silver
    "outlier": "#951233",      # Burgundy
    "success": "#6BA368",      # Muted Green
    "text": "#343752"          # Dark Gray
}

def get_energy_data(energy_type):
    url_map = {
        "Gasoline prices": "https://www.globalpetrolprices.com/gasoline_prices/",
        "Diesel": "https://www.globalpetrolprices.com/diesel_prices/",
        "Electricity": "https://www.globalpetrolprices.com/electricity_prices/",
        "LPG": "https://www.globalpetrolprices.com/lpg_prices/"
    }
    unit_map = {
        "Gasoline prices": "USD/Liter",
        "Diesel": "USD/Liter",
        "Electricity": "USD/kWh",
        "LPG": "USD/Liter"
    }
    url = url_map[energy_type]
    html = requests.get(url).text
    soup = BeautifulSoup(html, 'lxml')
    
    # Date extraction
    if energy_type == "Electricity":
        content = soup.get_text()
        quarter_match = re.search(r'Q[1-4] \d{4} update', content)
        date = quarter_match.group(0) if quarter_match else "Latest Update"
    else:
        h1_text = soup.select('h1')[0].text.strip()
        date = h1_text.split(',')[-1].strip() if ',' in h1_text else h1_text

    # Country names - robust extraction
    country_div = soup.find('div', id='outsideLinks')
    cname = []
    if country_div:
        country_text = country_div.get_text().strip()
        cname = [line.strip().replace("*", "") 
                for line in country_text.split('\n') 
                if line.strip() and not line.strip().isdigit()]
    
    # Prices - robust extraction
    price_div = soup.find('div', id='graphic')
    price_head = []
    if price_div:
        price_text = price_div.get_text().strip()
        price_head = [float(num) for num in price_text.split() if num.replace('.', '', 1).isdigit()]
    
    # Ensure equal length of data
    n = min(len(cname), len(price_head))
    return pd.DataFrame({'Country': cname[:n], 'Price': price_head[:n]}), date, unit_map[energy_type]

def main():
    st.set_page_config(page_title="⛽ World Energy Price Analysis", layout="centered", page_icon=":fuelpump:")
    st.markdown(
        f"<h1 style='color:{CXO_COLORS['primary']}; font-size: 2em;'>🌍 World Energy Price Analysis</h1>",
        unsafe_allow_html=True
    )

    energy_options = ["Gasoline prices", "Diesel", "Electricity", "LPG"]
    selected_energy = st.selectbox("Select energy type:", options=energy_options)

    try:
        df, date, unit = get_energy_data(selected_energy)
        if df.empty:
            st.warning(f"No data available for {selected_energy}")
            return
            
        # ... [REST OF YOUR CODE FROM THE ORIGINAL FILE] ...
        # Include all your existing analysis and visualization code here
        # Make sure to replace all hardcoded units with the `unit` variable
        
    except Exception as e:
        st.error(f"Error processing {selected_energy} data: {str(e)}")

if __name__ == "__main__":
    main()
