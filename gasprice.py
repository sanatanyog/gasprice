#!/usr/bin/env python
# coding: utf-8
"""
World Energy Price Analysis – Streamlit app
Scrapes GlobalPetrolPrices tables for:
• Gasoline • Diesel • LPG • Electricity • Natural Gas
Provides dropdown, country comparison, distribution & box-plot analytics.
"""

import re
from datetime import datetime

import numpy as np
import pandas as pd
import requests
from bs4 import BeautifulSoup
import matplotlib.pyplot as plt
import plotly.express as px
import streamlit as st

# ───────────────────────────── Styling ──────────────────────────────────────────
CXO_COLORS = {
    "primary":   "#224088",   # Royal Blue
    "accent":    "#BF9A4A",   # Gold
    "secondary": "#EEEDE9",   # Silver
    "outlier":   "#951233",   # Burgundy
    "success":   "#6BA368",   # Muted Green
    "text":      "#343752"    # Dark Gray
}

# ───────────────────────────── Utilities ────────────────────────────────────────
def month_to_quarter(month_year: str) -> str:
    """Convert 'December 2024' ➜ 'Q4 2024'."""
    m = month_year.split()[0]
    q = {"January":1,"February":1,"March":1,
         "April":2,"May":2,"June":2,
         "July":3,"August":3,"September":3,
         "October":4,"November":4,"December":4}.get(m, None)
    return f"Q{q} {month_year[-4:]}" if q else month_year

def scrape_common(url: str) -> tuple[pd.DataFrame, str]:
    """
    Generic scraper for Gasoline / Diesel / LPG tables.
    Returns (DataFrame<Country,Price>, date_string)
    """
    html = requests.get(url, timeout=15).text
    soup = BeautifulSoup(html, "lxml")

    # date string in H1
    h1 = soup.select_one("h1").text.strip()
    date = h1.split(",")[-1].strip() if "," in h1 else h1        # e.g. "24 June 2025"

    # table is rendered in two <div id="outsideLinks"> + <div id="graphic">
    countries = [c.strip().replace("*","")
                 for div in soup.find_all("div", id="outsideLinks")
                 for c in div.div.text.split("\n\n")[1:-1]]

    prices = [float(p) for div in soup.find_all("div", id="graphic")
                        for p in div.div.text.split()[:-1]]

    return pd.DataFrame({"Country": countries, "Price": prices}), date

def scrape_electricity() -> tuple[pd.DataFrame, str, float, float]:
    url = "https://www.globalpetrolprices.com/electricity_prices/"
    html = requests.get(url, timeout=15).text
    soup = BeautifulSoup(html, "lxml")
    h1 = soup.select_one("h1").text.strip()
    date = re.search(r"Q[1-4] \d{4} update:", h1).group(0)

    # world averages
    m = re.search(r"average electricity price .*? USD ([\d.]+) .*? residential .*? USD ([\d.]+) .*? businesses",
                  html, re.I | re.S)
    res_avg = float(m.group(1)) if m else None
    bus_avg = float(m.group(2)) if m else None

    # country table
    df, _ = scrape_common(url)          # uses same div structure
    return df, date, res_avg, bus_avg

def scrape_natural_gas() -> tuple[pd.DataFrame, str, float, float]:
    url = "https://www.globalpetrolprices.com/natural_gas_prices/"
    html = requests.get(url, timeout=15).text
    soup = BeautifulSoup(html, "lxml")

    # date in “December 2024 price update:” → Q4 2024
    m = re.search(r"(\w+ \d{4}) price update:", html)
    date_raw = m.group(1) if m else "Latest"
    date = f"{month_to_quarter(date_raw)} update:"

    # world averages
    w = re.search(r"world average price is USD ([\d.]+) .*? households .*? USD ([\d.]+) .*? business",
                  html, re.I | re.S)
    house_avg = float(w.group(1)) if w else None
    bus_avg   = float(w.group(2)) if w else None

    df, _ = scrape_common(url)
    return df, date, house_avg, bus_avg

# ───────────────────────────── Analysis ─────────────────────────────────────────
def statistics_section(df: pd.DataFrame, units: str) -> dict:
    vals = df["Price"].values.astype(float)
    mu, sigma = vals.mean(), vals.std(ddof=0)
    return {
        "mu": round(mu, 3),
        "sigma": round(sigma, 3),
        "upper_1sd": mu + sigma,
        "lower_1sd": mu - sigma,
        "lower_2sd": mu - 2 * sigma,
        "units": units
    }

def render_metrics(stats: dict, n_countries: int):
    col1, col2, col3 = st.columns(3)
    col1.metric("🌐 Global Average", f"${stats['mu']} / {stats['units']}")
    col2.metric("σ (Std Dev)",       f"{stats['sigma']}")
    col3.metric("Countries",         f"{n_countries}")

def comparison_table(df: pd.DataFrame, sel: list[str]):
    st.subheader("Price Comparison")
    styled = (df[df.Country.isin(sel)]
              .set_index("Country")
              .style.format({"Price": "${:.2f}"})
              .set_properties(**{"background-color":"#F6F7FB",
                                 "color":"#224088",
                                 "font-size":"1.1em",
                                 "font-weight":"bold"}))
    st.dataframe(styled, use_container_width=True)

def position_commentary(sel_data: dict, stats: dict):
    pos = {"within":[], "above":[], "below":[]}
    for c, v in sel_data.items():
        if v > stats["upper_1sd"]:
            pos["above"].append(c)
        elif v < stats["lower_1sd"]:
            pos["below"].append(c)
        else:
            pos["within"].append(c)
    if pos["above"]:
        st.warning(f"**{', '.join(pos['above'])}** have prices > 1 σ above mean (expensive).")
    if pos["below"]:
        st.warning(f"**{', '.join(pos['below'])}** have prices > 1 σ below mean (cheap).")
    if pos["within"]:
        st.info(f"**{', '.join(pos['within'])}** sit within ±1 σ of the global average.")

def distribution_plot(df: pd.DataFrame, sel_data: dict, stats: dict, date: str):
    x = np.random.normal(stats["mu"], stats["sigma"], 200)
    fig, ax = plt.subplots(figsize=(5,3))
    ax.hist(x, 30, density=True, alpha=0.7, color=CXO_COLORS["primary"])
    curve_x = np.linspace(min(x), max(x), 120)
    ax.plot(curve_x,
            1/(stats["sigma"]*np.sqrt(2*np.pi)) *
            np.exp(-(curve_x-stats["mu"])**2/(2*stats["sigma"]**2)),
            lw=2, color=CXO_COLORS["accent"])
    for i,(c,v) in enumerate(sel_data.items()):
        ax.axvline(v, color=plt.cm.tab10(i), lw=2, ls="--", label=f"{c} ${v}")
    ax.set_title(f"Distribution & Selected Countries ({date})",
                 color=CXO_COLORS['primary'])
    ax.set_xlabel(f"Price (${stats['units']})"); ax.set_ylabel("Density")
    ax.legend(fontsize=8)
    st.pyplot(fig)

def box_plot(df: pd.DataFrame, sel_data: dict):
    fig = px.box(df, y="Price", points="all",
                 labels={"Price":"Price"},
                 color_discrete_sequence=[CXO_COLORS["primary"]])
    for i,(c,v) in enumerate(sel_data.items()):
        fig.add_hline(y=v, line_dash="dot",
                      line_color=px.colors.qualitative.Plotly[i],
                      annotation_text=f"{c} ${v}",
                      annotation_font_color=px.colors.qualitative.Plotly[i])
    st.plotly_chart(fig, use_container_width=True)

# ───────────────────────────── Streamlit UI ────────────────────────────────────
def main() -> None:
    st.set_page_config("⛽ World Energy Price Analysis", page_icon=":fuelpump:")
    st.markdown(
        "<style>div.block-container{padding-top:1rem;}</style>",
        unsafe_allow_html=True,
    )

    # ── Energy selector
    energy = st.selectbox("Select energy type:",
                          ["Gasoline","Diesel","LPG","Electricity","Natural Gas"],
                          key="energy_type_selector")
    st.markdown(f"<h1 style='color:{CXO_COLORS['primary']};'>🌍 World {energy} Price Analysis</h1>",
                unsafe_allow_html=True)

    # ── Scrape
    if energy == "Gasoline":
        df, date = scrape_common("https://www.globalpetrolprices.com/gasoline_prices/")
        units = "L"
    elif energy == "Diesel":
        df, date = scrape_common("https://www.globalpetrolprices.com/diesel_prices/")
        units = "L"
    elif energy == "LPG":
        df, date = scrape_common("https://www.globalpetrolprices.com/lpg_prices/")
        units = "L"
    elif energy == "Electricity":
        df, date, res_avg, bus_avg = scrape_electricity()
        st.info(f"**{date}** World avg: Residential ${res_avg}/kWh • Business ${bus_avg}/kWh")
        units = "kWh"
    else:  # Natural Gas
        df, date, house_avg, bus_avg = scrape_natural_gas()
        st.info(f"**{date}** World avg: Household ${house_avg}/kWh • Business ${bus_avg}/kWh")
        units = "kWh"

    # ── Stats & caption
    stats = statistics_section(df, units)
    render_metrics(stats, len(df))
    st.caption(f"Source – GlobalPetrolPrices.com | Data updated: {date}")

    # ── Country selector & plots
    sel = st.multiselect("Compare up to 5 countries:",
                         sorted(df.Country.tolist()), max_selections=5,
                         key="country_selector")
    plot_choice = st.selectbox("Choose analysis plot:",
                               ["Distribution","Box-plot"], key="plot_select")

    if sel:
        sel_data = {c: float(df.loc[df.Country==c,"Price"].iat[0]) for c in sel}
        comparison_table(df, sel)
        position_commentary(sel_data, stats)

        if plot_choice == "Distribution":
            distribution_plot(df, sel_data, stats, date)
        else:
            box_plot(df, sel_data)

# ────────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    main()
