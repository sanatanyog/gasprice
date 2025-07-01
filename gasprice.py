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
    return pd.DataFrame({"Country": countries, "Price": prices}), quarter_label

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
    return pd.DataFrame({"Country": countries, "Price": prices}), quarter_label

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
    return pd.DataFrame({"Country": countries, "Price": prices}), quarter_label

def get_electricity_data():
    url = "https://www.globalpetrolprices.com/electricity_prices/"
    html = requests.get(url).text
    soup = BeautifulSoup(html, 'lxml')
    quarter_label = ""
    for tag in soup.find_all(['b', 'strong']):
        text = tag.get_text(strip=True)
        if "update" in text.lower():
            quarter_label = text
            break
    if not quarter_label:
        match = re.search(r"(Q[1-4]\s*\d{4}\s*update)", html, re.IGNORECASE)
        quarter_label = match.group(1) if match else ""
    tables = pd.read_html(html)
    df_raw = tables[1]
    df_raw.columns = ["Country", "Residential", "Business"]
    df = df_raw[["Country", "Residential"]].rename(columns={"Residential": "Price"})
    return df, quarter_label

def get_natural_gas_data():
    url = "https://www.globalpetrolprices.com/natural_gas_prices/"
    html = requests.get(url).text
    soup = BeautifulSoup(html, "lxml")
    match = re.search(r"(\w+\s+\d{4})\s+price update", html, re.IGNORECASE)
    update_label = f"{match.group(1).title()} update" if match else ""
    country_links = soup.select("#outsideLinks .graph_outside_link") or soup.find('div', id='outsideLinks').find_all('a')
    countries = [a.get_text(strip=True) for a in country_links]
    raw_tokens = soup.find("div", id="graphic").get_text(" ", strip=True).split()
    numeric_tokens = [tok for tok in raw_tokens if tok.replace(".", "", 1).isdigit()]
    prices = [float(tok) for tok in numeric_tokens[: len(countries)]]
    return pd.DataFrame({"Country": countries, "Price": prices}), update_label

def main():
    st.set_page_config(page_title="⛽ Energy Price Analysis", layout="centered", page_icon=":fuelpump:")
    st.markdown(f"<h1 style='color:{CXO_COLORS['primary']}; font-size: 2em;'>🌍 World Energy Price Analysis</h1>", unsafe_allow_html=True)

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
    mu = round(np.mean(prices), 3)
    sigma = round(np.std(prices), 3)
    count = len(df)
    unit = "USD/kWh" if energy in ["Electricity", "Natural Gas"] else "USD/L"

    col1, col2, col3 = st.columns(3)
    col1.metric("🌐 Global Average", f"{mu}{unit}")
    col2.metric("σ (Std. Dev.)", f"{sigma}")
    col3.metric("Countries", f"{count}")
    st.caption(f"Data update: {q_label} | Source: GlobalPetrolPrices.com")

    st.header(f"🔎 Compare {energy} Prices")
    country_input = st.selectbox("Select your country:", [""] + sorted(df["Country"].tolist()), index=0)
    show_dist = st.checkbox("Show distribution commentary & plot", True)
    show_box = st.checkbox("Show boxplot commentary & plot", True)

    if country_input:
        value = float(df.loc[df["Country"] == country_input, "Price"])
        # Compute distribution stats
        q1 = df["Price"].quantile(0.25)
        median = df["Price"].quantile(0.50)
        q3 = df["Price"].quantile(0.75)
        iqr = q3 - q1
        lower_whisker = q1 - 1.5 * iqr
        upper_whisker = q3 + 1.5 * iqr
        percentile = round(df["Price"].rank(pct=True)[df["Country"] == country_input].iloc[0] * 100, 1)

        # Distribution Commentary
        if show_dist:
            if value < lower_whisker or value > upper_whisker:
                outlier_comment = f"🔴 {country_input} is an outlier (outside 1.5×IQR)."
            else:
                outlier_comment = f"🟢 {country_input} is within the expected range (whiskers)."
            if value <= q1:
                quartile_comment = "in the lowest 25% of countries."
            elif value <= median:
                quartile_comment = "between the 25th and 50th percentile."
            elif value <= q3:
                quartile_comment = "between the 50th and 75th percentile."
            else:
                quartile_comment = "in the highest 25% of countries."
            st.markdown(f"**📊 Distribution Commentary for {country_input}:**")
            st.write(f"- **Value:** {value}{unit}")
            st.write(f"- **Mean (μ):** {mu}{unit}  •  **σ:** {sigma}{unit}")
            st.write(f"- **Percentile rank:** {percentile}th percentile")
            st.write(f"- **Quartile placement:** {country_input} is {quartile_comment}")
            st.write(f"- **Outlier status:** {outlier_comment}")

            data_sim = np.random.normal(mu, sigma, len(prices))
            fig, ax = plt.subplots()
            ax.hist(data_sim, bins=30, density=True, alpha=0.6, color=CXO_COLORS["primary"])
            xs = np.linspace(min(data_sim), max(data_sim), 200)
            ax.plot(xs, 1/(sigma*np.sqrt(2*np.pi))*np.exp(-(xs-mu)**2/(2*sigma**2)), color=CXO_COLORS["accent"], linewidth=2)
            ax.axvline(value, color=CXO_COLORS["success"], linestyle="--", linewidth=2, label=f"{country_input}: {value}{unit}")
            ax.set_title(f"{energy} Distribution ({q_label})", color=CXO_COLORS["primary"])
            ax.set_xlabel(f"Price ({unit})")
            ax.set_ylabel("Density")
            ax.legend(fontsize=8)
            st.pyplot(fig)

        # Boxplot Commentary
        if show_box:
            st.markdown("**📦 Boxplot Commentary:**")
            st.write(f"- **Q1 (25th):** {q1}{unit}  •  **Median:** {median}{unit}  •  **Q3 (75th):** {q3}{unit}")
            st.write(f"- **IQR (Q3–Q1):** {round(iqr,3)}{unit}")
            st.write(f"- **Whiskers:** [{round(lower_whisker,3)}, {round(upper_whisker,3)}]{unit}")
            st.write(f"- {country_input} at the {percentile}th percentile (green dot).")

            fig2, ax2 = plt.subplots()
            ax2.boxplot(df["Price"], vert=False, flierprops={'markerfacecolor':CXO_COLORS["outlier"]})
            ax2.scatter(value, 1, color=CXO_COLORS["success"], zorder=3)
            ax2.set_title(f"{energy} Boxplot ({q_label})", color=CXO_COLORS["primary"])
            ax2.set_xlabel(f"Price ({unit})")
            ax2.get_yaxis().set_visible(False)
            st.pyplot(fig2)

if __name__ == "__main__":
    main()
