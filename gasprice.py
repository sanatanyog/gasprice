#!/usr/bin/env python
# coding: utf-8

# In[2]:


import streamlit as st
import requests
from bs4 import BeautifulSoup
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px

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
    return pd.DataFrame({'Country': cname, 'Price': petrol_head}), date

def main():
    st.set_page_config(page_title="⛽ World Gas Price Analysis", layout="wide", page_icon=":fuelpump:")
    st.markdown(
        "<h1 style='color:#0072B5; font-size: 2em;'>🌍 World Gas Price Analysis</h1>",
        unsafe_allow_html=True
    )

    df, date = get_gas_data()
    petrol_head = df['Price'].values
    mu = round(float(np.mean(petrol_head)), 3)
    sigma = round(float(np.std(petrol_head)), 3)
    o_std = sigma + mu
    nv_mu_80 = mu - sigma
    nv_mu_95 = mu - 2 * sigma
    countries_count = len(df)

    st.markdown("### Key Metrics")
    st.write(
        f"🌐 **Global Average:** ${mu}/L &nbsp;&nbsp; | &nbsp;&nbsp; "
        f"σ (Std. Dev.): {sigma} &nbsp;&nbsp; | &nbsp;&nbsp; "
        f"Countries: {countries_count}"
    )
    st.caption(f"Data last updated: {date} | Source: GlobalPetrolPrices.com")

    st.header("🔎 Compare Your Country")
    country_input = st.selectbox(
        "Select your country:",
        options=[""] + sorted(df['Country'].tolist()),
        index=0,
        format_func=lambda x: "Type or select..." if x == "" else x,
        help="Start typing to search and select your country"
    )

    plot_type = None
    if country_input and country_input != "":
        plot_type = st.selectbox(
            "Select analysis type:",
            options=["", "Distribution Plot", "Boxplot Analysis"],
            index=0,
            format_func=lambda x: "Select..." if x == "" else x
        )

    if country_input and country_input != "" and plot_type and plot_type != "":
        q = country_input
        try:
            value = float(df[df['Country'] == q]['Price'].values[0])
            st.success(f'Current price in **{q}**: **${value}**')
            st.caption(f"Data refreshed: {date}")

            if value > mu:
                diff = round(((value-mu)/value)*100)
                st.markdown(f"<span style='color:crimson;'>{q}'s price is {diff}% higher than global average</span>", unsafe_allow_html=True)
            else:
                diff = round(((mu-value)/mu)*100)
                st.markdown(f"<span style='color:green;'>{q}'s price is {diff}% lower than global average</span>", unsafe_allow_html=True)

            st.subheader("Position Analysis")
            if value < o_std and value > mu:
                st.info(f'{q} pays what 68% of countries pay.')
            elif value < mu and value > nv_mu_80:
                st.info(f'{q} pays what 68% of countries pay.')
            elif value < nv_mu_80 and value > nv_mu_95:
                st.warning(f'{q} pays less than 80% of countries.')
            elif value < nv_mu_95:
                st.warning(f'{q} pays less than 95% of countries.')
            elif value > o_std:
                st.error(f'{q} is an OUTLIER - pays more than 80% of countries.')
            else:
                st.info("Position analysis not available")

            if plot_type == "Distribution Plot":
                data = np.random.normal(mu, sigma, 170)
                fig, ax = plt.subplots(figsize=(4, 3))
                ax.hist(data, 30, density=True, alpha=0.5, color="#0072B5")
                ax.plot(
                    np.linspace(min(data), max(data), 100),
                    1/(sigma * np.sqrt(2 * np.pi)) * np.exp(-(np.linspace(min(data), max(data), 100) - mu)**2 / (2 * sigma**2)),
                    linewidth=2, color='#FF800E'
                )
                ax.axvline(value, color='red', linestyle='dashed', linewidth=2, label=f"{q}'s Price")
                ax.set_title(f"Global Price Distribution ({date})")
                ax.set_xlabel("Price ($/liter)")
                ax.set_ylabel("Density")
                ax.legend()
                st.pyplot(fig, use_container_width=True)

            elif plot_type == "Boxplot Analysis":
                fig = px.box(df, y="Price", points="all",
                             title=f"Global Gas Price Distribution",
                             labels={"Price": "Price per liter (USD)"})
                fig.add_hline(y=value, line_dash="dot", line_color="red",
                              annotation_text=f"{q}'s Price (${value})")
                fig.update_layout(showlegend=False)
                st.plotly_chart(fig, use_container_width=True)

                q1 = df['Price'].quantile(0.25)
                median = df['Price'].median()
                q3 = df['Price'].quantile(0.75)
                iqr = q3 - q1
                lower_bound = q1 - 1.5 * iqr
                upper_bound = q3 + 1.5 * iqr

                st.subheader("Quartile Analysis")
                if value < q1:
                    st.info(f"**Lowest quartile (Q1):** {q} pays less than 75% of countries")
                    st.markdown("- Typically indicates strong local production or government subsidies")
                elif value < median:
                    st.info(f"**Second quartile (Q2):** {q} pays less than half of countries")
                    st.markdown("- Suggests moderate taxation and stable supply chains")
                elif value < q3:
                    st.info(f"**Third quartile (Q3):** {q} pays more than half of countries")
                    st.markdown("- Often reflects higher transportation costs or import dependencies")
                else:
                    st.warning(f"**Highest quartile (Q4):** {q} pays more than 75% of countries")
                    st.markdown("- Typically indicates high fuel taxes or complex supply logistics")

                st.subheader("Outlier Analysis")
                if value < lower_bound or value > upper_bound:
                    st.error(f"**{q} is a statistical OUTLIER** in global gas prices:")
                    if value > upper_bound:
                        st.markdown(f"- Prices **${round(value - upper_bound,2)}/L above** normal range")
                        st.markdown("- Potential factors: High taxes, import dependency, or supply constraints")
                    else:
                        st.markdown(f"- Prices **${round(lower_bound - value,2)}/L below** normal range")
                        st.markdown("- Potential factors: Subsidies, local production, or price controls")
                else:
                    st.info(f"{q} is within the normal price range for global gas prices")

        except Exception as e:
            st.error(f'Error processing data: {str(e)}')

if __name__ == "__main__":
    main()


# In[ ]:




