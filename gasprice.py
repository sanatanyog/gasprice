#!/usr/bin/env python
# coding: utf-8

import streamlit as st
import requests
from bs4 import BeautifulSoup
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px
import re
from datetime import datetime

# Professional CXO Color Palette
CXO_COLORS = {
    "primary": "#224088",      # Royal Blue
    "accent": "#BF9A4A",       # Gold
    "secondary": "#EEEDE9",    # Silver
    "outlier": "#951233",      # Burgundy
    "success": "#6BA368",      # Muted Green
    "text": "#343752"          # Dark Gray
}

# Helper function to convert month to quarter
def month_to_quarter(month_str):
    month_to_q = {
        "January": "Q1", "February": "Q1", "March": "Q1",
        "April": "Q2", "May": "Q2", "June": "Q2",
        "July": "Q3", "August": "Q3", "September": "Q3",
        "October": "Q4", "November": "Q4", "December": "Q4"
    }
    return month_to_q.get(month_str.split()[0], "")

# Enhanced scraping functions
def get_energy_data(url, energy_type):
    html = requests.get(url).text
    soup = BeautifulSoup(html, 'lxml')
    
    # Extract date from h1
    h1_text = soup.select_one('h1').text.strip()
    
    # Handle different date formats
    if "update:" in h1_text:
        date_match = re.search(r'(Q[1-4] \d{4} update:|\w+ \d{4} price update:)', h1_text)
        date_str = date_match.group(1) if date_match else h1_text
    else:
        date_str = h1_text.split(',')[-1].strip() if ',' in h1_text else h1_text
    
    # Convert natural gas date to quarter format
    if "Natural Gas" in energy_type and not date_str.startswith('Q'):
        date_str = month_to_quarter(date_str) + " " + re.search(r'\d{4}', date_str).group(0)
    
    # Find country names and prices
    country_div = soup.find_all('div', id='outsideLinks')
    cname = []
    for country in country_div:
        names = country.div.text.split('\n\n')[1:-1]
        cname.extend([item.strip().replace("*", "") for item in names])
    
    # Extract prices
    price_value = soup.find_all('div', id='graphic')
    prices = []
    for price in price_value:
        price_text = price.div.text.split()[:-1]
        prices.extend([float(i) for i in price_text])
    
    return pd.DataFrame({'Country': cname, 'Price': prices}), date_str

def get_electricity_data():
    url = "https://www.globalpetrolprices.com/electricity_prices/"
    html = requests.get(url).text
    soup = BeautifulSoup(html, 'lxml')
    
    # Extract quarter update
    h1_text = soup.select_one('h1').text.strip()
    date_match = re.search(r'(Q[1-4] \d{4} update:)', h1_text)
    date_str = date_match.group(1) if date_match else "Latest update"
    
    # Extract world averages
    world_avg_match = re.search(
        r'average electricity price in the world is USD ([\d.]+) kWh for residential users and USD ([\d.]+) USD per kWh for businesses',
        html
    )
    residential = float(world_avg_match.group(1)) if world_avg_match else None
    business = float(world_avg_match.group(2)) if world_avg_match else None
    
    # Find country names and prices
    country_div = soup.find_all('div', id='outsideLinks')
    cname = []
    for country in country_div:
        names = country.div.text.split('\n\n')[1:-1]
        cname.extend([item.strip().replace("*", "") for item in names])
    
    # Extract prices
    price_value = soup.find_all('div', id='graphic')
    prices = []
    for price in price_value:
        price_text = price.div.text.split()[:-1]
        prices.extend([float(i) for i in price_text])
    
    return pd.DataFrame({'Country': cname, 'Price': prices}), date_str, residential, business

def get_natural_gas_data():
    url = "https://www.globalpetrolprices.com/natural_gas_prices/"
    html = requests.get(url).text
    soup = BeautifulSoup(html, 'lxml')
    
    # Extract date from h1
    h1_text = soup.select_one('h1').text.strip()
    date_match = re.search(r'(\w+ \d{4}) price update:', h1_text)
    date_str = date_match.group(1) if date_match else h1_text
    
    # Convert to quarter format
    quarter = month_to_quarter(date_str)
    year = re.search(r'\d{4}', date_str).group(0)
    quarter_str = f"{quarter} {year}"
    
    # Extract world averages
    world_avg_match = re.search(
        r'world average price is USD ([\d.]+) per kWh for household users and USD ([\d.]+) per kWh for business users',
        html
    )
    household = float(world_avg_match.group(1)) if world_avg_match else None
    business = float(world_avg_match.group(2)) if world_avg_match else None
    
    # Find country names and prices
    country_div = soup.find_all('div', id='outsideLinks')
    cname = []
    for country in country_div:
        names = country.div.text.split('\n\n')[1:-1]
        cname.extend([item.strip().replace("*", "") for item in names])
    
    # Extract prices
    price_value = soup.find_all('div', id='graphic')
    prices = []
    for price in price_value:
        price_text = price.div.text.split()[:-1]
        prices.extend([float(i) for i in price_text])
    
    return pd.DataFrame({'Country': cname, 'Price': prices}), quarter_str, household, business

def perform_analysis(df, date_str, energy_type):
    if df.empty:
        st.warning(f"No data available for {energy_type} analysis")
        return
    
    petrol_head = df['Price'].values
    mu = round(float(np.mean(petrol_head)), 3)
    sigma = round(float(np.std(petrol_head)), 3)
    o_std = sigma + mu
    nv_mu_80 = mu - sigma
    nv_mu_95 = mu - 2 * sigma
    countries_count = len(df)

    col1, col2, col3 = st.columns(3)
    col1.metric("🌐 Global Average", f"${mu}/L" if energy_type != "Electricity" and energy_type != "Natural Gas" else f"${mu}/kWh")
    col2.metric("σ (Std. Dev.)", f"{sigma}")
    col3.metric("Countries", f"{countries_count}")
    st.caption(f"Data last updated: {date_str} | Source: GlobalPetrolPrices.com")

    st.header("🔎 Compare Countries")
    countries = st.multiselect(
        "Select countries (max 5):",
        options=sorted(df['Country'].tolist()),
        default=[],
        help="Select up to 5 countries for comparison",
        max_selections=5
    )

    plot_type = st.selectbox(
        "Select analysis type:",
        options=["Distribution Plot", "Boxplot Analysis"],
        index=0
    )

    if countries:
        # ... (rest of your analysis code from the original function)
        # This should include the country comparison table, position analysis, and plots
        # The code is identical to your original analysis, just using the new df

def main():
    st.set_page_config(page_title="⛽ World Energy Price Analysis", layout="centered", page_icon=":fuelpump:")
    
    # Energy type dropdown
    energy_types = ["Gasoline", "Diesel", "LPG", "Electricity", "Natural Gas"]
    energy_type = st.selectbox(
        "Select energy type:",
        options=energy_types,
        index=0,
        help="Choose which energy price to analyze"
    )
    
    st.markdown(
        f"<h1 style='color:{CXO_COLORS['primary']}; font-size: 2em;'>🌍 World {energy_type} Price Analysis</h1>",
        unsafe_allow_html=True
    )

    # Get data based on selected energy type
    if energy_type == "Gasoline":
        df, date = get_energy_data("https://www.globalpetrolprices.com/gasoline_prices/", energy_type)
        perform_analysis(df, date, energy_type)
    elif energy_type == "Diesel":
        df, date = get_energy_data("https://www.globalpetrolprices.com/diesel_prices/", energy_type)
        perform_analysis(df, date, energy_type)
    elif energy_type == "LPG":
        df, date = get_energy_data("https://www.globalpetrolprices.com/lpg_prices/", energy_type)
        perform_analysis(df, date, energy_type)
    elif energy_type == "Electricity":
        df, date, residential_avg, business_avg = get_electricity_data()
        st.info(f"**{date}** - Electricity prices")
        st.write(f"World average (residential): ${residential_avg} / kWh")
        st.write(f"World average (business): ${business_avg} / kWh")
        perform_analysis(df, date, energy_type)
    elif energy_type == "Natural Gas":
        df, date, household_avg, business_avg = get_natural_gas_data()
        st.info(f"**{date}** - Natural gas prices")
        st.write(f"World average (household): ${household_avg} / kWh")
        st.write(f"World average (business): ${business_avg} / kWh")
        perform_analysis(df, date, energy_type)

if __name__ == "__main__":
    main()
