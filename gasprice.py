import streamlit as st
import requests
from bs4 import BeautifulSoup
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import datetime
import re
from io import StringIO

# Professional CXO Color Palette
CXO_COLORS = {
    "primary": "#224088",   # Royal Blue
    "accent": "#BF9A4A",    # Gold
    "secondary": "#EEEDE9", # Silver
    "outlier": "#951233",   # Burgundy
    "text": "#343752"       # Dark Gray
}

# Added caching so switching between Residential/Business is INSTANT
@st.cache_data(ttl=3600, show_spinner=False)
def get_data(url, is_electric=False, is_natural_gas=False, elec_type="Residential"):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        html = requests.get(url, headers=headers, timeout=10).text
        soup = BeautifulSoup(html, "lxml")

        if is_electric:
            # Look specifically for QX 20XX update format
            m = re.search(r"(Q[1-4]\s*\d{4}\s*update)", html, re.IGNORECASE)
            label = m.group(1).title() if m else "Update Unknown"
            
            tables = pd.read_html(StringIO(html))
            if len(tables) > 1:
                df_raw = tables[1]
                # Table has 3 columns: Country, Residential, Business
                df_raw.columns = ["Country", "Residential", "Business"]
                # Filter down to the specific type the user selected in the sidebar
                df = df_raw[["Country", elec_type]].rename(columns={elec_type: "Price"})
            else:
                return pd.DataFrame(), "Could not find electricity table on page."

        elif is_natural_gas:
            m = re.search(r"(\w+\s+\d{4})\s+price update", html, re.IGNORECASE)
            label = f"{m.group(1).title()} update" if m else "Update Unknown"
            links = soup.select("#outsideLinks .graph_outside_link") or soup.find(id="outsideLinks").find_all("a")
            countries = [a.get_text(strip=True) for a in links]
            tokens = soup.find(id="graphic").get_text(" ", strip=True).split()
            nums = [tok for tok in tokens if tok.replace(".","",1).isdigit()]
            prices = [float(tok) for tok in nums[:len(countries)]]
            df = pd.DataFrame({"Country": countries, "Price": prices})

        else:
            h1 = soup.select_one("h1").text
            date_str = h1.split(",")[-1].strip()
            try:
                dt = datetime.datetime.strptime(date_str, "%d-%b-%Y")
                quarter = (dt.month - 1) // 3 + 1
                label = f"Q{quarter} {dt.year} update"
            except:
                label = "Update Unknown"
                
            names = soup.find(id="outsideLinks").div.text.split("\n\n")[1:-1]
            countries = [n.strip().replace("*","") for n in names]
            prices = [float(p) for p in soup.find(id="graphic").div.text.split()[:-1]]
            df = pd.DataFrame({"Country": countries, "Price": prices})

        # Pre-emptive Clean
        df["Price"] = pd.to_numeric(df["Price"], errors="coerce")
        df = df.dropna(subset=["Price"]).drop_duplicates(subset=["Country"], keep="first")
        
        return df, label

    except Exception as e:
        return pd.DataFrame(), f"Error: {e}"

def main():
    st.set_page_config(page_title="⛽ Energy Price Analysis", layout="centered", page_icon=":fuelpump:")
    st.markdown(f"<h1 style='color:{CXO_COLORS['primary']}; font-size:2em;'>🌍 World Energy Price Analysis</h1>",
                unsafe_allow_html=True)

    sources = {
        "Gasoline":        ("https://www.globalpetrolprices.com/gasoline_prices/", False, False),
        "Diesel":          ("https://www.globalpetrolprices.com/diesel_prices/", False, False),
        "LPG":             ("https://www.globalpetrolprices.com/lpg_prices/", False, False),
        "Electricity":     ("https://www.globalpetrolprices.com/electricity_prices/", True, False),
        "Natural Gas":     ("https://www.globalpetrolprices.com/natural_gas_prices/", False, True)
    }

    # Sidebar inputs
    energy = st.sidebar.selectbox("Select energy type:", list(sources.keys()))
    
    # Show Residential/Business toggle ONLY if Electricity is selected
    elec_type = "Residential"
    if energy == "Electricity":
        elec_type = st.sidebar.radio("Select Rate Type:", ["Residential", "Business"])

    url, is_elec, is_ng = sources[energy]
    
    with st.spinner(f"Fetching latest {energy} data..."):
        df, q_label = get_data(url, is_electric=is_elec, is_natural_gas=is_ng, elec_type=elec_type)

    if df is None or df.empty:
        st.error(f"Something went wrong while scraping the data: {q_label}")
        st.stop()

    # Electricity-specific Information Banner
    if energy == "Electricity":
        st.info("💡 **Note:** These electricity rates are an average of prices between **2023 and 2026**. Such averages are better for comparing countries as they avoid quarter-to-quarter price volatility.")

    prices = df["Price"].to_numpy()
    mu, sigma = round(prices.mean(), 3), round(prices.std(), 3)
    N = len(df)
    unit = "USD/kWh" if energy in ["Electricity", "Natural Gas"] else "USD/L"

    # Global metrics
    c1, c2, c3 = st.columns(3)
    
    # Update metric label dynamically based on Electricity selection
    metric_label = f"🌐 Global Average ({elec_type})" if energy == "Electricity" else "🌐 Global Average"
    c1.metric(metric_label, f"{mu}{unit}")
    c2.metric("σ (Std. Dev.)", f"{sigma}")
    c3.metric("Countries", f"{N}")
    st.caption(f"Data update: {q_label} | Source: GlobalPetrolPrices.com")

    st.header(f"🔎 Compare {energy} Prices")
    countries = st.multiselect("Select up to 5 countries:", sorted(df["Country"]), max_selections=5)
    plot_choice = st.selectbox("Choose analysis:", ["—","Distribution","Boxplot"])

    if countries:
        q1, q3 = df["Price"].quantile([0.25, 0.75])
        iqr = q3 - q1
        lo, hi = q1 - 1.5*iqr, q3 + 1.5*iqr

        st.markdown("### 🗒️ Quick Takeaways")
        for ctr in countries:
            val = float(df.loc[df["Country"] == ctr, "Price"].iloc[0])
            pct = df["Price"].rank(pct=True)[df["Country"] == ctr].iloc[0] * 100
            below = int(round(pct/100 * N))
            comp = "more" if val > mu else "less"
            st.markdown(f"**{ctr}** pays **{val}{unit}**, which is **{comp}** than the world average of **{mu}{unit}**.")
            st.markdown(f"- **{below}/{N} countries pay less than {ctr} for {energy}**")
            if val < lo or val > hi:
                st.markdown(f"- **Is this unusual?** Yes — {ctr} is outside the normal range ({lo:.3f}–{hi:.3f}{unit}).")
            else:
                st.markdown(f"- **Is this unusual?** No — {ctr} is within the normal range ({lo:.3f}–{hi:.3f}{unit}).")
            st.markdown("---")

        if plot_choice == "Distribution":
            st.markdown("#### 📊 Price Distribution")
            sim = np.random.normal(mu, sigma, N)
            fig, ax = plt.subplots()
            ax.hist(sim, bins=30, density=True, alpha=0.6, color=CXO_COLORS["primary"])
            xs = np.linspace(sim.min(), sim.max(), 200)
            ax.plot(xs, 1/(sigma*np.sqrt(2*np.pi)) * np.exp(-(xs-mu)**2/(2*sigma**2)),
                    color=CXO_COLORS["accent"], linewidth=2)
            for i, ctr in enumerate(countries):
                v = float(df.loc[df["Country"] == ctr, "Price"].iloc[0])
                ax.axvline(v, linestyle="--", color=plt.cm.tab10(i),
                           label=f"{ctr} ({v}{unit})")
            ax.set_title(f"{energy} Distribution ({q_label})", color=CXO_COLORS["primary"])
            ax.set_xlabel(f"Price ({unit})"); ax.set_ylabel("Density")
            ax.legend(fontsize=8)
            st.pyplot(fig)

        if plot_choice == "Boxplot":
            st.markdown("#### 📦 Price Boxplot")
            st.markdown(
                "- The **box** shows where most prices sit (middle 50%).  \n"
                "- The **line** inside is the middle price.  \n"
                "- The **whiskers** show the normal range.  \n"
                "- **Dots** beyond whiskers are unusual prices."
            )
            fig2, ax2 = plt.subplots(figsize=(6,2))
            ax2.boxplot(prices, vert=False,
                        flierprops={'markerfacecolor': CXO_COLORS["outlier"],
                                    'markeredgecolor': CXO_COLORS["outlier"]})
            for i, ctr in enumerate(countries):
                v = float(df.loc[df["Country"] == ctr, "Price"].iloc[0])
                color = plt.cm.tab10(i)
                ax2.scatter(v, 1, color=color, s=100, label=f"{ctr}: {v}{unit}", zorder=3)
            ax2.set_title(f"{energy} Prices Boxplot ({q_label})", color=CXO_COLORS["primary"])
            ax2.set_xlabel(f"Price ({unit})")
            ax2.get_yaxis().set_visible(False)
            ax2.legend(loc="upper right", fontsize=8)
            st.pyplot(fig2)

if __name__ == "__main__":
    main()
