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

def get_gas_data():
    url = "https://www.globalpetrolprices.com/gasoline_prices/"
    html = requests.get(url).text
    soup = BeautifulSoup(html, 'lxml')
    h1_text = soup.select('h1')[0].text.strip()
    date = h1_text.split(',')[-1].strip() if ',' in h1_text else h1_text
    country_div = soup.find_all('div', id='outsideLinks')
    for country in country_div:
        cname = country.div.text.split('\n\n')[1:-1]
        cname = [item.strip().replace("*", "") for item in cname]
    petrol_value = soup.find_all('div', id='graphic')
    for price in petrol_value:
        petrol_price = price.div.text.split()[:-1]
        petrol_head = [float(i) for i in petrol_price]
    return pd.DataFrame({'Country': cname, 'Price': petrol_head}), date, "USD/Liter"

# Placeholder: Replace with actual scraping or API for diesel prices
def get_diesel_data():
    # Example: Simulate data
    countries = ["USA", "Germany", "India", "China", "Brazil", "UK", "France", "Japan", "Australia", "Canada"]
    prices = [1.20, 1.80, 1.10, 1.00, 1.30, 1.90, 1.85, 1.75, 1.70, 1.60]
    date = "June 2025"
    return pd.DataFrame({'Country': countries, 'Price': prices}), date, "USD/Liter"

# Placeholder: Replace with actual scraping or API for electricity prices
def get_electricity_data():
    countries = ["USA", "Germany", "India", "China", "Brazil", "UK", "France", "Japan", "Australia", "Canada"]
    prices = [0.15, 0.32, 0.09, 0.08, 0.18, 0.28, 0.27, 0.25, 0.22, 0.20]
    date = "Q2 2025"
    return pd.DataFrame({'Country': countries, 'Price': prices}), date, "USD/kWh"

# Placeholder: Replace with actual scraping or API for LPG prices
def get_lpg_data():
    countries = ["USA", "Germany", "India", "China", "Brazil", "UK", "France", "Japan", "Australia", "Canada"]
    prices = [0.70, 1.10, 0.60, 0.65, 0.75, 1.15, 1.12, 1.05, 1.00, 0.95]
    date = "June 2025"
    return pd.DataFrame({'Country': countries, 'Price': prices}), date, "USD/Liter"

def main():
    st.set_page_config(page_title="🌍 World Energy Price Analysis", layout="centered", page_icon=":fuelpump:")
    st.markdown(
        f"<h1 style='color:{CXO_COLORS['primary']}; font-size: 2em;'>🌍 World Energy Price Analysis</h1>",
        unsafe_allow_html=True
    )

    energy_options = ["Gasoline prices", "Diesel", "Electricity", "LPG"]
    selected_energy = st.selectbox("Select energy type:", options=energy_options)

    # Data selection logic
    if selected_energy == "Gasoline prices":
        df, date, unit = get_gas_data()
    elif selected_energy == "Diesel":
        df, date, unit = get_diesel_data()
    elif selected_energy == "Electricity":
        df, date, unit = get_electricity_data()
    elif selected_energy == "LPG":
        df, date, unit = get_lpg_data()
    else:
        st.error("Unknown energy type selected.")
        return

    # Analysis
    price_col = "Price"
    values = df[price_col].values
    mu = round(float(np.mean(values)), 3)
    sigma = round(float(np.std(values)), 3)
    o_std = sigma + mu
    nv_mu_80 = mu - sigma
    nv_mu_95 = mu - 2 * sigma
    countries_count = len(df)

    col1, col2, col3 = st.columns(3)
    col1.metric("🌐 Global Average", f"${mu} {unit}")
    col2.metric("σ (Std. Dev.)", f"{sigma}")
    col3.metric("Countries", f"{countries_count}")
    st.caption(f"Data last updated: {date}")

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
        country_data = {}
        position_groups = {
            "close_to_68_1": [],
            "close_to_68_2": [],
            "less_than_80": [],
            "less_than_95": [],
            "more_than_80": []
        }
        for country in countries:
            try:
                value = float(df[df['Country'] == country][price_col].values[0])
                country_data[country] = value
                if value < o_std and value > mu:
                    position_groups["close_to_68_1"].append(country)
                elif value < mu and value > nv_mu_80:
                    position_groups["close_to_68_2"].append(country)
                elif value < nv_mu_80 and value > nv_mu_95:
                    position_groups["less_than_80"].append(country)
                elif value < nv_mu_95:
                    position_groups["less_than_95"].append(country)
                elif value > o_std:
                    position_groups["more_than_80"].append(country)
            except Exception as e:
                st.error(f'Error processing data for {country}: {str(e)}')

        # Price comparison table
        st.subheader("Price Comparison")
        compare_df = df[df['Country'].isin(countries)].set_index("Country")
        styled = (
            compare_df.style
            .format({price_col: "${:.2f}"})
            .set_properties(**{
                "background-color": "#F6F7FB",
                "color": "#224088",
                "font-size": "1.1em",
                "font-weight": "bold"
            }, subset=pd.IndexSlice[:, [price_col]])
            .set_table_styles([
                {"selector": "th", "props": [("font-size", "1.1em"), ("font-weight", "bold"), ("color", "#343752"), ("background", "#EEEDE9")]},
                {"selector": "td", "props": [("border", "1px solid #EEEDE9")]},
                {"selector": "tr:hover", "props": [("background-color", "#FFF9E5")]}
            ])
            .set_caption(" ")
        )
        st.dataframe(styled, use_container_width=True)

        st.subheader("Position Analysis")
        commentary = []
        if position_groups["close_to_68_1"] or position_groups["close_to_68_2"]:
            close_countries = position_groups["close_to_68_1"] + position_groups["close_to_68_2"]
            commentary.append(f"**{', '.join(close_countries)}** pay close to what 68% of countries pay.")
        if position_groups["less_than_80"]:
            commentary.append(f"**{', '.join(position_groups['less_than_80'])}** pay less than 80% of countries.")
        if position_groups["less_than_95"]:
            commentary.append(f"**{', '.join(position_groups['less_than_95'])}** pay less than 95% of countries.")
        if position_groups["more_than_80"]:
            commentary.append(f"**{', '.join(position_groups['more_than_80'])}** pay more than 80% of countries.")
        for comment in commentary:
            st.info(comment)

        if plot_type == "Distribution Plot":
            data = np.random.normal(mu, sigma, 170)
            fig, ax = plt.subplots(figsize=(5, 3))
            ax.hist(data, 30, density=True, alpha=0.7, color=CXO_COLORS["primary"])
            ax.plot(
                np.linspace(min(data), max(data), 100),
                1/(sigma * np.sqrt(2 * np.pi)) * np.exp(-(np.linspace(min(data), max(data), 100) - mu)**2 / (2 * sigma**2)),
                linewidth=2, color=CXO_COLORS["accent"]
            )
            color_cycle = plt.cm.tab10.colors
            for i, (country, value) in enumerate(country_data.items()):
                ax.axvline(value, color=color_cycle[i % 10], linestyle='dashed', linewidth=2, label=f"{country} (${value})")
            handles, labels = ax.get_legend_handles_labels()
            filtered = [(h, l) for h, l in zip(handles, labels) if any(c in l for c in countries)]
            if filtered:
                handles, labels = zip(*filtered)
                ax.legend(handles, labels, fontsize=8)
            else:
                ax.legend().remove()
            ax.set_title(f"Global {selected_energy} Distribution, Normal Curve & Selected Countries ({date})", fontsize=13, color=CXO_COLORS["primary"])
            ax.set_xlabel(f"Price ({unit})", fontsize=10)
            ax.set_ylabel("Density", fontsize=10)
            st.pyplot(fig)

            st.subheader("Distribution Analysis")
            dist_groups = {"Above 1 Std Dev": [], "Below 1 Std Dev": [], "Within 1 Std Dev": []}
            for country, value in country_data.items():
                if value > mu + sigma:
                    dist_groups["Above 1 Std Dev"].append(country)
                elif value < mu - sigma:
                    dist_groups["Below 1 Std Dev"].append(country)
                else:
                    dist_groups["Within 1 Std Dev"].append(country)
            if dist_groups["Above 1 Std Dev"]:
                st.warning(f"**{', '.join(dist_groups['Above 1 Std Dev'])}** have prices more than 1 standard deviation above the global mean.")
            if dist_groups["Below 1 Std Dev"]:
                st.warning(f"**{', '.join(dist_groups['Below 1 Std Dev'])}** have prices more than 1 standard deviation below the global mean.")
            if dist_groups["Within 1 Std Dev"]:
                st.info(f"**{', '.join(dist_groups['Within 1 Std Dev'])}** have prices within 1 standard deviation of the global mean.")

        elif plot_type == "Boxplot Analysis":
            fig = px.box(df, y=price_col, points="all",
                         title=f"Global {selected_energy} Price Distribution",
                         labels={price_col: f"Price ({unit})"},
                         color_discrete_sequence=[CXO_COLORS["primary"]])
            color_cycle = px.colors.qualitative.Plotly
            for i, (country, value) in enumerate(country_data.items()):
                fig.add_hline(
                    y=value, line_dash="dot", 
                    line_color=color_cycle[i % len(color_cycle)],
                    annotation_text=f"{country} (${value})", 
                    annotation_font_color=color_cycle[i % len(color_cycle)]
                )
            fig.update_layout(
                showlegend=False,
                plot_bgcolor="white",
                paper_bgcolor="white",
                font=dict(color=CXO_COLORS["text"])
            )
            st.plotly_chart(fig, use_container_width=True)
            
            st.subheader("Detailed Analysis")
            q1 = df[price_col].quantile(0.25)
            median = df[price_col].median()
            q3 = df[price_col].quantile(0.75)
            iqr = q3 - q1
            lower_bound = q1 - 1.5 * iqr
            upper_bound = q3 + 1.5 * iqr

            analysis_groups = {}
            for country, value in country_data.items():
                if value < q1:
                    quartile = "Lowest Quartile (Q1)"
                    quartile_desc = "- Below 25% of countries"
                    quartile_color = "info"
                elif value < median:
                    quartile = "Second Quartile (Q2)"
                    quartile_desc = "- Below 50% of countries"
                    quartile_color = "info"
                elif value < q3:
                    quartile = "Third Quartile (Q3)"
                    quartile_desc = "- Above 50% of countries"
                    quartile_color = "info"
                else:
                    quartile = "Highest Quartile (Q4)"
                    quartile_desc = "- Top 25% of countries"
                    quartile_color = "warning"
                if value < lower_bound or value > upper_bound:
                    outlier = "Statistical Outlier"
                    outlier_color = "error"
                    if value > upper_bound:
                        outlier_desc = f"- **Deviation:** {value - upper_bound:.2f} {unit} above normal"
                    else:
                        outlier_desc = f"- **Deviation:** {lower_bound - value:.2f} {unit} below normal"
                else:
                    outlier = "Within Normal Range"
                    outlier_color = "success"
                    outlier_desc = "- Follows global distribution"
                key = (quartile, outlier, quartile_desc, outlier_desc, quartile_color, outlier_color)
                analysis_groups.setdefault(key, []).append(country)

            for (quartile, outlier, quartile_desc, outlier_desc, quartile_color, outlier_color), countries_list in analysis_groups.items():
                st.markdown(f"### {', '.join(countries_list)}")
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("**Quartile Position**")
                    if quartile_color == "warning":
                        st.warning(f"**{quartile}**")
                    else:
                        st.info(f"**{quartile}**")
                    for line in quartile_desc.split('\n'):
                        if line.strip():
                            st.markdown(line)
                with col2:
                    st.markdown("**Outlier Status**")
                    if outlier_color == "error":
                        st.error(f"**{outlier}**")
                    else:
                        st.success(f"{outlier}")
                    for line in outlier_desc.split('\n'):
                        if line.strip():
                            st.markdown(line)

if __name__ == "__main__":
    main()
