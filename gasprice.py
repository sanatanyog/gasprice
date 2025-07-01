import streamlit as st
import requests
from bs4 import BeautifulSoup
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px
import datetime

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
    # Extract and convert date to quarter label
    h1 = soup.select_one('h1').text
    date_str = h1.split(',')[-1].strip()
    quarter_label = get_quarter_label(date_str)
    # Parse countries and prices
    names = soup.find('div', id='outsideLinks').div.text.split('\n\n')[1:-1]
    countries = [n.strip().replace("*", "") for n in names]
    prices = soup.find('div', id='graphic').div.text.split()[:-1]
    prices = [float(p) for p in prices]
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
    prices = soup.find('div', id='graphic').div.text.split()[:-1]
    prices = [float(p) for p in prices]
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
    prices = soup.find('div', id='graphic').div.text.split()[:-1]
    prices = [float(p) for p in prices]
    df = pd.DataFrame({"Country": countries, "Price": prices})
    return df, quarter_label

def get_electricity_data():
    url = "https://www.globalpetrolprices.com/electricity_prices/"
    html = requests.get(url).text
    soup = BeautifulSoup(html, 'lxml')
    
    # Look for both <b> and <strong> tags containing "update"
    candidates = soup.find_all(['b', 'strong'])
    quarter_label = ""
    for tag in candidates:
        text = tag.get_text(strip=True)
        if "update" in text.lower():
            quarter_label = text
            break
    
    # Fallback: if still empty, try regex scan of the page
    if not quarter_label:
        import re
        match = re.search(r"(Q[1-4]\s*\d{4}\s*update)", html, re.IGNORECASE)
        if match:
            quarter_label = match.group(1)
    
    # Read the country-level table
    tables = pd.read_html(html)
    df_raw = tables[1]
    df_raw.columns = ["Country", "Residential", "Business"]
    df = df_raw[["Country", "Residential"]].rename(columns={"Residential": "Price"})
    
    return df, quarter_label


def main():
    st.set_page_config(page_title="⛽ Energy Price Analysis", layout="centered", page_icon=":fuelpump:")
    st.markdown(
        f"<h1 style='color:{CXO_COLORS['primary']}; font-size: 2em;'>🌍 World Energy Price Analysis</h1>",
        unsafe_allow_html=True
    )
    
    # Choose energy type
    data_funcs = {
        "Gasoline": get_gas_data,
        "Diesel": get_diesel_data,
        "LPG": get_lpg_data,
        "Electricity": get_electricity_data
    }
    energy = st.sidebar.selectbox("Select energy type:", list(data_funcs.keys()))
    
    # Load data
    df, q_label = data_funcs[energy]()
    prices = df["Price"].values
    mu = round(float(np.mean(prices)), 3)
    sigma = round(float(np.std(prices)), 3)
    countries_count = df.shape[0]
    
    # Display metrics
    col1, col2, col3 = st.columns(3)
    unit = "USD/kWh" if energy == "Electricity" else "USD/L"
    col1.metric("🌐 Global Average", f"{mu}{unit}")
    col2.metric("σ (Std. Dev.)", f"{sigma}")
    col3.metric("Countries", f"{countries_count}")
    st.caption(f"Data update: {q_label} | Source: GlobalPetrolPrices.com")
    
    # Country comparison
    st.header(f"🔎 Compare {energy} Prices")
    selected = st.multiselect(
        "Select countries (max 5):",
        options=sorted(df["Country"].tolist()),
        max_selections=5
    )
    plot_type = st.selectbox("Select analysis type:", ["Distribution Plot", "Boxplot Analysis"])
    
    if selected:
        country_data = {c: float(df[df["Country"]==c]["Price"]) for c in selected}
        
        # Price comparison table
        comp_df = df[df["Country"].isin(selected)].set_index("Country")
        styled = (
            comp_df.style
            .format({"Price": f"{mu:.2f}{unit}"})
            .set_properties(**{"background-color": CXO_COLORS["secondary"], "color": CXO_COLORS["primary"], "font-weight":"bold"}, subset=["Price"])
            .set_caption(" ")
        )
        st.subheader("Price Comparison")
        st.dataframe(styled, use_container_width=True)
        
        # Visualization
        if plot_type == "Distribution Plot":
            data_sim = np.random.normal(mu, sigma, len(prices))
            fig, ax = plt.subplots(figsize=(6,4))
            ax.hist(data_sim, bins=30, density=True, alpha=0.7, color=CXO_COLORS["primary"])
            xs = np.linspace(min(data_sim), max(data_sim), 200)
            ax.plot(xs, 1/(sigma*np.sqrt(2*np.pi))*np.exp(-(xs-mu)**2/(2*sigma**2)),
                    color=CXO_COLORS["accent"], linewidth=2)
            for i,(c,v) in enumerate(country_data.items()):
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
            for i,(c,v) in enumerate(country_data.items()):
                fig.add_hline(y=v, line_dash="dot", line_color=px.colors.qualitative.Plotly[i],
                              annotation_text=f"{c} ({v}{unit})",
                              annotation_font_color=px.colors.qualitative.Plotly[i])
            fig.update_layout(showlegend=False, plot_bgcolor="white", paper_bgcolor="white",
                              font=dict(color=CXO_COLORS["text"]))
            st.plotly_chart(fig, use_container_width=True)

if __name__ == "__main__":
    main()
