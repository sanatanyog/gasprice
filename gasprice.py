import streamlit as st
import requests
from bs4 import BeautifulSoup
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px
import datetime
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

def get_quarter_label(date_str, fmt="%d-%b-%Y"):
    """Convert a date string to a 'Qx YYYY update' label."""
    dt = datetime.datetime.strptime(date_str, fmt)
    quarter = (dt.month - 1) // 3 + 1
    return f"Q{quarter} {dt.year} update"

def get_gas_data():
    url = "https://www.globalpetrolprices.com/gasoline_prices/"
    html = requests.get(url).text
    soup = BeautifulSoup(html, 'lxml')
    h1 = soup.select_one('h1').text
    date_str = h1.split(',')[-1].strip()
    quarter_label = get_quarter_label(date_str)
    names = soup.find('div', id='outsideLinks').div.text.split('\n\n')[1:-1]
    countries = [n.strip().replace("*", "") for n in names]
    prices = [float(p) for p in soup.find('div', id='graphic').div.text.split()[:-1]]
    df = pd.DataFrame({"Country": countries, "Price": prices})
    return df, quarter_label

def get_diesel_data():
    url = "https://www.globalpetrolprices.com/diesel_prices/"
    html = requests.get(url).text
    soup = BeautifulSoup(html, 'lxml')
    h1 = soup.select_one('h1').text
    date_str = h1.split(',')[-1].strip()
    quarter_label = get_quarter_label(date_str)
    names = soup.find('div', id='outsideLinks').div.text.split('\n\n')[1:-1]
    countries = [n.strip().replace("*", "") for n in names]
    prices = [float(p) for p in soup.find('div', id='graphic').div.text.split()[:-1]]
    df = pd.DataFrame({"Country": countries, "Price": prices})
    return df, quarter_label

def get_lpg_data():
    url = "https://www.globalpetrolprices.com/lpg_prices/"
    html = requests.get(url).text
    soup = BeautifulSoup(html, 'lxml')
    h1 = soup.select_one('h1').text
    date_str = h1.split(',')[-1].strip()
    quarter_label = get_quarter_label(date_str)
    names = soup.find('div', id='outsideLinks').div.text.split('\n\n')[1:-1]
    countries = [n.strip().replace("*", "") for n in names]
    prices = [float(p) for p in soup.find('div', id='graphic').div.text.split()[:-1]]
    df = pd.DataFrame({"Country": countries, "Price": prices})
    return df, quarter_label

def get_electricity_data():
    url = "https://www.globalpetrolprices.com/electricity_prices/"
    html = requests.get(url).text
    soup = BeautifulSoup(html, 'lxml')
    # Extract "Qx YYYY update" from <b> or <strong>
    quarter_label = ""
    for tag in soup.find_all(['b', 'strong']):
        text = tag.get_text(strip=True)
        if "update" in text.lower():
            quarter_label = text
            break
    if not quarter_label:
        match = re.search(r"(Q[1-4]\s*\d{4}\s*update)", html, re.IGNORECASE)
        if match:
            quarter_label = match.group(1)
    tables = pd.read_html(html)
    df_raw = tables[1]
    df_raw.columns = ["Country", "Residential", "Business"]
    df = df_raw[["Country", "Residential"]].rename(columns={"Residential": "Price"})
    return df, quarter_label

def get_natural_gas_data():
    """
    Scrape household natural gas prices and the "Month YYYY update" label.
    """
    url = "https://www.globalpetrolprices.com/natural_gas_prices/"
    html = requests.get(url).text
    soup = BeautifulSoup(html, "lxml")

    # Extract "Month YYYY update" via regex
    match = re.search(r"(\w+\s+\d{4})\s+price update", html, re.IGNORECASE)
    update_label = f"{match.group(1).title()} update" if match else ""

    # Scrape countries
    country_links = soup.select("#outsideLinks .graph_outside_link")
    if not country_links:
        country_links = soup.find('div', id='outsideLinks').find_all('a')
    countries = [a.get_text(strip=True) for a in country_links]

    # Scrape and align prices
    raw_tokens = soup.find("div", id="graphic").get_text(" ", strip=True).split()
    numeric_tokens = [tok for tok in raw_tokens if tok.replace(".", "", 1).isdigit()]
    prices = [float(tok) for tok in numeric_tokens[: len(countries)]]

    df = pd.DataFrame({"Country": countries, "Price": prices})
    return df, update_label

def main():
    st.set_page_config(page_title="⛽ Energy Price Analysis", layout="centered", page_icon=":fuelpump:")
    st.markdown(
        f"<h1 style='color:{CXO_COLORS['primary']}; font-size: 2em;'>🌍 World Energy Price Analysis</h1>",
        unsafe_allow_html=True
    )

    data_funcs = {
        "Gasoline": get_gas_data,
        "Diesel": get_diesel_data,
        "LPG": get_lpg_data,
        "Electricity": get_electricity_data,
        "Natural Gas": get_natural_gas_data
    }
    energy = st.sidebar.selectbox("Select energy type:", list(data_funcs.keys()))

    df, q_label = data_funcs[energy]()
    prices = df["Price"].values
    mu = round(float(np.mean(prices)), 3)
    sigma = round(float(np.std(prices)), 3)
    count = df.shape[0]

    col1, col2, col3 = st.columns(3)
    unit = "USD/kWh" if energy in ["Electricity", "Natural Gas"] else "USD/L"
    col1.metric("🌐 Global Average", f"{mu}{unit}")
    col2.metric("σ (Std. Dev.)", f"{sigma}")
    col3.metric("Countries", f"{count}")
    st.caption(f"Data update: {q_label} | Source: GlobalPetrolPrices.com")

    st.header(f"🔎 Compare {energy} Prices")
    selected = st.multiselect("Select countries (max 5):", sorted(df["Country"]), max_selections=5)
    plot_type = st.selectbox("Select analysis type:", ["Distribution Plot", "Boxplot Analysis"])

    if selected:
        sub_df = df[df["Country"].isin(selected)].set_index("Country")
        styled = (
            sub_df.style
            .format({"Price": f"{mu:.2f}{unit}"})
            .set_properties(**{"background-color": CXO_COLORS["secondary"],
                               "color": CXO_COLORS["primary"],
                               "font-weight": "bold"}, subset=["Price"])
            .set_caption(" ")
        )
        st.subheader("Price Comparison")
        st.dataframe(styled, use_container_width=True)

        if plot_type == "Distribution Plot":
            data_sim = np.random.normal(mu, sigma, len(prices))
            fig, ax = plt.subplots(figsize=(6,4))
            ax.hist(data_sim, bins=30, density=True, alpha=0.7, color=CXO_COLORS["primary"])
            xs = np.linspace(min(data_sim), max(data_sim), 200)
            ax.plot(xs, 1/(sigma*np.sqrt(2*np.pi))*np.exp(-(xs-mu)**2/(2*sigma**2)),
                    color=CXO_COLORS["accent"], linewidth=2)
            for i, c in enumerate(selected):
                v = float(df[df["Country"] == c]["Price"])
                ax.axvline(v, color=plt.cm.tab10(i), linestyle='--', label=f"{c} ({v}{unit})")
            ax.set_title(f"{energy} Price Distribution & Selected Countries", color=CXO_COLORS["primary"])
            ax.set_xlabel(f"Price ({unit})")
            ax.set_ylabel("Density")
            ax.legend(fontsize=8)
            st.pyplot(fig)
        else:
            fig = px.box(df, y="Price", points="all",
                         title=f"{energy} Price Distribution",
                         labels={"Price": f"Price ({unit})"},
                         color_discrete_sequence=[CXO_COLORS["primary"]])
            for i, c in enumerate(selected):
                v = float(df[df["Country"] == c]["Price"])
                fig.add_hline(y=v, line_dash="dot", line_color=px.colors.qualitative.Plotly[i],
                              annotation_text=f"{c} ({v}{unit})",
                              annotation_font_color=px.colors.qualitative.Plotly[i])
            fig.update_layout(showlegend=False, plot_bgcolor="white", paper_bgcolor="white",
                              font=dict(color=CXO_COLORS["text"]))
            st.plotly_chart(fig, use_container_width=True)

if __name__ == "__main__":
    main()
