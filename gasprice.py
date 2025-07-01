import streamlit as st
import requests
from bs4 import BeautifulSoup
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px

# Professional CXO Color Palette
CXO_COLORS = {
    "primary": "#224088",      # Royal Blue
    "accent": "#BF9A4A",       # Gold
    "secondary": "#EEEDE9",    # Silver
    "outlier": "#951233",      # Burgundy
    "success": "#6BA368",      # Muted Green
    "text": "#343752"          # Dark Gray
}

def get_fuel_data(url, header_selector='h1', country_div_id='outsideLinks', graphic_div_id='graphic'):
    """
    Generic scraper for fuel prices (gasoline, diesel, LPG).
    Returns a DataFrame with Country and Price, and a string for the update label.
    """
    html = requests.get(url).text
    soup = BeautifulSoup(html, 'lxml')
    # Extract update label (the date)
    raw_header = soup.select(header_selector)[0].text.strip()
    update_label = raw_header.split(',')[-1].strip() if ',' in raw_header else raw_header

    # Extract country names
    cname = []
    country_divs = soup.find_all('div', id=country_div_id)
    for div in country_divs:
        lines = div.div.text.split('\n\n')[1:-1]
        for item in lines:
            clean = item.strip().replace('*','')
            cname.append(clean)
    # Extract prices
    prices = []
    graphic_divs = soup.find_all('div', id=graphic_div_id)
    for div in graphic_divs:
        vals = div.div.text.split()[:-1]  # drop unit label
        prices = [float(v) for v in vals]
    df = pd.DataFrame({'Country': cname, 'Price': prices})
    return df, update_label

def get_gas_data():
    return get_fuel_data("https://www.globalpetrolprices.com/gasoline_prices/")

def get_diesel_data():
    return get_fuel_data("https://www.globalpetrolprices.com/diesel_prices/")

def get_lpg_data():
    return get_fuel_data("https://www.globalpetrolprices.com/lpg_prices/")

def get_electricity_data():
    """
    Scrape electricity prices table for residential and business rates,
    and extract the Q update label.
    """
    url = "https://www.globalpetrolprices.com/electricity_prices/"
    html = requests.get(url).text
    soup = BeautifulSoup(html, 'lxml')
    # Extract Q update label
    # Assumes first <strong> contains text like "Q2 2025 update"
    q_label = soup.find('strong').text.strip()

    # Read tables with pandas
    tables = pd.read_html(url)
    # The 2nd table is the country compare table
    df = tables[1]
    df.columns = [
        "Country",
        "Residential_USD_per_kWh_2023_2025_avg",
        "Business_USD_per_kWh_2023_2025_avg"
    ]
    return df, q_label

def display_price_analysis(df, update_label, unit_label):
    """
    Display key metrics and allow country comparison for a given fuel DataFrame.
    """
    prices = df['Price'].values
    mu = round(prices.mean(), 3)
    sigma = round(prices.std(), 3)
    total_countries = len(df)

    c1, c2, c3 = st.columns(3)
    c1.metric("🌐 Global Average", f"{unit_label}{mu}")
    c2.metric("σ (Std. Dev.)", f"{sigma}")
    c3.metric("Countries", f"{total_countries}")
    st.caption(f"{unit_label.strip()} prices {update_label} | Source: GlobalPetrolPrices.com")

    st.header("🔎 Compare Countries")
    countries = st.multiselect(
        "Select countries (max 5):",
        options=sorted(df['Country']),
        max_selections=5
    )
    if not countries:
        return

    selected = df[df['Country'].isin(countries)].set_index('Country')
    st.subheader("Price Comparison")
    styled = (
        selected.style
        .format({"Price": f"{unit_label}{{:.2f}}"})
        .set_properties(**{"background-color": CXO_COLORS["secondary"], "color": CXO_COLORS["primary"]})
        .set_table_styles([{"selector":"th","props":[("background-color",CXO_COLORS["secondary"])]}])
    )
    st.dataframe(styled, use_container_width=True)

    # Distribution plot
    st.subheader("Distribution Plot")
    data = np.random.normal(mu, sigma, total_countries)
    fig, ax = plt.subplots(figsize=(6, 3))
    ax.hist(data, bins=30, density=True, alpha=0.6, color=CXO_COLORS["primary"])
    x = np.linspace(data.min(), data.max(), 100)
    ax.plot(x, 1/(sigma*np.sqrt(2*np.pi))*np.exp(-(x-mu)**2/(2*sigma**2)),
            color=CXO_COLORS["accent"], linewidth=2)
    for i, country in enumerate(countries):
        val = float(selected.loc[country, 'Price'])
        ax.axvline(val, linestyle='--', linewidth=2, label=f"{country} ({unit_label}{val})")
    ax.legend(fontsize=8)
    ax.set_title(f"Global {unit_label.strip()} Distribution & Selected Countries", color=CXO_COLORS["primary"])
    ax.set_xlabel(f"{unit_label} per unit")
    ax.set_ylabel("Density")
    st.pyplot(fig)

def display_electricity_analysis(df, q_label):
    """
    Display electricity price metrics and comparison table.
    """
    # Metrics
    res_avg = round(df['Residential_USD_per_kWh_2023_2025_avg'].mean(), 3)
    bus_avg = round(df['Business_USD_per_kWh_2023_2025_avg'].mean(), 3)
    st.header("⚡ Electricity Price Analysis")
    st.subheader(f"{q_label}")
    c1, c2 = st.columns(2)
    c1.metric("🌐 Residential Avg", f"USD {res_avg}/kWh")
    c2.metric("🌐 Business Avg", f"USD {bus_avg}/kWh")
    st.caption(f"2023–2025 averages | Source: GlobalPetrolPrices.com")

    st.header("🔎 Compare Countries")
    countries = st.multiselect(
        "Select countries (max 5):",
        options=sorted(df['Country']),
        max_selections=5,
        key="elec_countries"
    )
    if countries:
        sel = df[df['Country'].isin(countries)].set_index('Country')
        styled = (
            sel.style
            .format({
                "Residential_USD_per_kWh_2023_2025_avg": "USD {:.3f}",
                "Business_USD_per_kWh_2023_2025_avg": "USD {:.3f}"
            })
            .set_properties(**{"background-color": CXO_COLORS["secondary"], "color": CXO_COLORS["primary"]})
            .set_table_styles([{"selector":"th","props":[("background-color",CXO_COLORS["secondary"])]}])
        )
        st.dataframe(styled, use_container_width=True)

def main():
    st.set_page_config(page_title="⛽ Fuel & ⚡ Electricity Price Analysis", layout="centered", page_icon=":fuelpump:")
    st.markdown(f"<h1 style='color:{CXO_COLORS['primary']};'>Global Fuel & Electricity Price Dashboard</h1>", unsafe_allow_html=True)

    tab1, tab2, tab3, tab4 = st.tabs(["Gasoline", "Diesel", "LPG", "Electricity"])

    with tab1:
        df_gas, label_gas = get_gas_data()
        display_price_analysis(df_gas, label_gas, unit_label="$")

    with tab2:
        df_diesel, label_diesel = get_diesel_data()
        display_price_analysis(df_diesel, label_diesel, unit_label="$")

    with tab3:
        df_lpg, label_lpg = get_lpg_data()
        display_price_analysis(df_lpg, label_lpg, unit_label="$")

    with tab4:
        df_elec, label_elec = get_electricity_data()
        display_electricity_analysis(df_elec, label_elec)

if __name__ == "__main__":
    main()
