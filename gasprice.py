import streamlit as st
import requests
from bs4 import BeautifulSoup
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import datetime
import re

# Professional CXO Color Palette
CXO_COLORS = {
    "primary": "#224088",   # Royal Blue
    "accent": "#BF9A4A",    # Gold
    "secondary": "#EEEDE9", # Silver
    "outlier": "#951233",   # Burgundy
    "success": "#6BA368",   # Muted Green
    "text": "#343752"       # Dark Gray
}

def get_quarter_label(date_str, fmt="%d-%b-%Y"):
    dt = datetime.datetime.strptime(date_str, fmt)
    quarter = (dt.month - 1) // 3 + 1
    return f"Q{quarter} {dt.year} update"

def get_gas_data():
    url = "https://www.globalpetrolprices.com/gasoline_prices/"
    html = requests.get(url).text
    soup = BeautifulSoup(html, 'lxml')
    date_str = soup.select_one('h1').text.split(',')[-1].strip()
    q_label = get_quarter_label(date_str)
    names = soup.find('div', id='outsideLinks').div.text.split('\n\n')[1:-1]
    countries = [n.strip().replace("*","") for n in names]
    prices = [float(p) for p in soup.find('div', id='graphic').div.text.split()[:-1]]
    return pd.DataFrame({"Country": countries, "Price": prices}), q_label

def get_diesel_data():
    url = "https://www.globalpetrolprices.com/diesel_prices/"
    html = requests.get(url).text
    soup = BeautifulSoup(html, 'lxml')
    date_str = soup.select_one('h1').text.split(',')[-1].strip()
    q_label = get_quarter_label(date_str)
    names = soup.find('div', id='outsideLinks').div.text.split('\n\n')[1:-1]
    countries = [n.strip().replace("*","") for n in names]
    prices = [float(p) for p in soup.find('div', id='graphic').div.text.split()[:-1]]
    return pd.DataFrame({"Country": countries, "Price": prices}), q_label

def get_lpg_data():
    url = "https://www.globalpetrolprices.com/lpg_prices/"
    html = requests.get(url).text
    soup = BeautifulSoup(html, 'lxml')
    date_str = soup.select_one('h1').text.split(',')[-1].strip()
    q_label = get_quarter_label(date_str)
    names = soup.find('div', id='outsideLinks').div.text.split('\n\n')[1:-1]
    countries = [n.strip().replace("*","") for n in names]
    prices = [float(p) for p in soup.find('div', id='graphic').div.text.split()[:-1]]
    return pd.DataFrame({"Country": countries, "Price": prices}), q_label

def get_electricity_data():
    url = "https://www.globalpetrolprices.com/electricity_prices/"
    html = requests.get(url).text
    soup = BeautifulSoup(html, 'lxml')
    q_label = ""
    for tag in soup.find_all(['b','strong']):
        t = tag.text.strip()
        if "update" in t.lower():
            q_label = t
            break
    if not q_label:
        m = re.search(r"(Q[1-4]\s*\d{4}\s*update)", html)
        q_label = m.group(1) if m else ""
    df_raw = pd.read_html(html)[1]
    df_raw.columns = ["Country","Residential","Business"]
    df = df_raw[["Country","Residential"]].rename(columns={"Residential":"Price"})
    return df, q_label

def get_natural_gas_data():
    url = "https://www.globalpetrolprices.com/natural_gas_prices/"
    html = requests.get(url).text
    soup = BeautifulSoup(html, 'lxml')
    m = re.search(r"(\w+\s+\d{4})\s+price update", html, re.IGNORECASE)
    q_label = f"{m.group(1).title()} update" if m else ""
    links = soup.select("#outsideLinks .graph_outside_link") or soup.find('div',id='outsideLinks').find_all('a')
    countries = [a.text.strip() for a in links]
    tokens = soup.find("div",id="graphic").get_text(" ",strip=True).split()
    nums = [tok for tok in tokens if tok.replace(".","",1).isdigit()]
    prices = [float(tok) for tok in nums[:len(countries)]]
    return pd.DataFrame({"Country": countries, "Price": prices}), q_label

def main():
    st.set_page_config(page_title="⛽ Energy Price Analysis", layout="centered", page_icon=":fuelpump:")
    st.markdown(f"<h1 style='color:{CXO_COLORS['primary']}; font-size:2em;'>🌍 World Energy Price Analysis</h1>", unsafe_allow_html=True)

    data_funcs = {
        "Gasoline": get_gas_data,
        "Diesel": get_diesel_data,
        "LPG": get_lpg_data,
        "Electricity": get_electricity_data,
        "Natural Gas": get_natural_gas_data
    }
    energy = st.sidebar.selectbox("Select energy type:", list(data_funcs.keys()))
    df, q_label = data_funcs[energy]()
    
    prices = df["Price"].to_numpy()
    mu = round(prices.mean(), 3)
    sigma = round(prices.std(), 3)
    total_countries = len(df)
    unit = "USD/kWh" if energy in ["Electricity","Natural Gas"] else "USD/L"

    # Display key metrics
    c1, c2, c3 = st.columns(3)
    c1.metric("🌐 Global Average", f"{mu}{unit}")
    c2.metric("σ (Std. Dev.)", f"{sigma}")
    c3.metric("Countries", f"{total_countries}")
    st.caption(f"Data update: {q_label} | Source: GlobalPetrolPrices.com")

    st.header(f"🔎 Compare {energy} Prices")
    country = st.selectbox("Select your country:", [""] + sorted(df["Country"]))
    plot_choice = st.selectbox("What would you like to see?", ["—","Distribution Analysis","Boxplot Analysis"])

    if country and plot_choice != "—":
        value = float(df.loc[df["Country"]==country, "Price"])
        q1 = df["Price"].quantile(0.25)
        q3 = df["Price"].quantile(0.75)
        iqr = q3 - q1
        lower = q1 - 1.5*iqr
        upper = q3 + 1.5*iqr
        pct = df["Price"].rank(pct=True)[df["Country"]==country].iloc[0] * 100
        below_count = int(round((pct/100) * total_countries))

        # Human-friendly commentary
        st.markdown("### 🗒️ Quick Takeaways")
        st.markdown(
            f"- **Average vs Yours:** The world average is {mu}{unit}. "
            f"{country} pays **{value}{unit}**, which is "
            + ("higher" if value>mu else "lower")
            + " than the global average."
        )
        st.markdown(
            f"- **Countries Paying Less:** Only **{below_count}** out of "
            f"{total_countries} countries pay less than {country}."
        )
        if value < lower or value > upper:
            st.markdown(
                f"- **Outlier?** Yes. Most countries pay between "
                f"{lower:.3f}{unit} and {upper:.3f}{unit}; {country} is an outlier."
            )
        else:
            st.markdown(
                f"- **Outlier?** No. {country}’s price is within the normal range "
                f"({lower:.3f}–{upper:.3f}{unit})."
            )

        # Distribution plot
        if plot_choice == "Distribution Analysis":
            st.markdown("#### 📊 Price Distribution")
            data_sim = np.random.normal(mu, sigma, len(prices))
            fig, ax = plt.subplots()
            ax.hist(data_sim, bins=30, density=True, alpha=0.6, color=CXO_COLORS["primary"])
            xs = np.linspace(min(data_sim), max(data_sim), 200)
            ax.plot(xs,
                    1/(sigma*np.sqrt(2*np.pi)) * np.exp(-(xs-mu)**2/(2*sigma**2)),
                    color=CXO_COLORS["accent"], linewidth=2)
            ax.axvline(value, color=CXO_COLORS["success"], linestyle="--",
                       label=f"{country}: {value}{unit}")
            ax.set_title(f"{energy} Distribution ({q_label})", color=CXO_COLORS["primary"])
            ax.set_xlabel(f"Price ({unit})")
            ax.set_ylabel("Density")
            ax.legend(fontsize=8)
            st.pyplot(fig)

        # Boxplot analysis
        if plot_choice == "Boxplot Analysis":
            st.markdown("#### 📦 Price Boxplot")
            st.markdown(f"- The box covers the middle 50% (from {q1}{unit} to {q3}{unit}).")
            st.markdown(f"- Whiskers extend to [{lower:.3f},{upper:.3f}]{unit}; points beyond are outliers.")
            fig2, ax2 = plt.subplots()
            ax2.boxplot(prices, vert=False,
                        flierprops={'markerfacecolor':CXO_COLORS["outlier"], 'markeredgecolor':CXO_COLORS["outlier"]})
            ax2.scatter(value, 1, color=CXO_COLORS["success"], zorder=3, label=country)
            ax2.set_title(f"{energy} Boxplot ({q_label})", color=CXO_COLORS["primary"])
            ax2.set_xlabel(f"Price ({unit})")
            ax2.get_yaxis().set_visible(False)
            ax2.legend(fontsize=8)
            st.pyplot(fig2)

if __name__ == "__main__":
    main()
