#!/usr/bin/env python
# coding: utf-8

# In[2]:


# Core dependencies for data processing and visualization
import streamlit as st  # Web app framework
import requests  # HTTP requests for web scraping
from bs4 import BeautifulSoup  # HTML parsing
import numpy as np  # Statistical calculations
import pandas as pd  # Data manipulation
import matplotlib.pyplot as plt  # Basic visualization
import difflib  # Fuzzy string matching for country input

def get_gas_data():
    """
    Scrapes gasoline price data from GlobalPetrolPrices.com
    Returns:
        DataFrame: Country-price pairs
        str: Data timestamp
    """
    url = "https://www.globalpetrolprices.com/gasoline_prices/"
    html = requests.get(url).text  # Fetch webpage content
    soup = BeautifulSoup(html, 'lxml')  # Parse HTML structure
    
    # Extract and clean date from page header
    h1_text = soup.select('h1')[0].text.strip()
    date = h1_text.split(',')[-1].strip() if ',' in h1_text else h1_text
    
    # Country list extraction
    country_div = soup.find_all('div', id='outsideLinks')
    for country in country_div:
        cname = country.div.text.split('\n\n')[1:-1]  # Remove empty elements
        cname = [item.strip().replace("*", "") for item in cname]  # Clean formatting
    
    # Price data extraction
    petrol_value = soup.find_all('div', id='graphic')
    for price in petrol_value:
        petrol_price = price.div.text.split()[:-1]  # Exclude last empty element
        petrol_head = [float(i) for i in petrol_price]  # Convert to numerical values
    
    return pd.DataFrame({'Country': cname, 'Price': petrol_head}), date

def main():
    # Configure app layout with wide screen and a custom icon
    st.set_page_config(page_title="⛽ World Gas Price Analysis", layout="wide", page_icon=":fuelpump:")
    
    # Use a colored header for better visual appeal
    st.markdown(
        "<h1 style='color:#0072B5; font-size: 2.5em;'>🌍 World Gas Price Analysis</h1>",
        unsafe_allow_html=True
    )
    
    # Data loading and processing
    df, date = get_gas_data()
    petrol_head = df['Price'].values
    
    # Statistical calculations
    mu = round(float(np.mean(petrol_head)), 3)  # Global average
    sigma = round(float(np.std(petrol_head)), 3)  # Standard deviation
    o_std = sigma + mu  # Upper bound for 68% distribution
    nv_mu_80 = mu - sigma  # Lower bound for 68% distribution
    nv_mu_95 = mu - 2 * sigma  # 95% distribution threshold

    # Display key metrics in columns for emphasis
    col1, col2, col3 = st.columns(3)
    col1.metric("🌐 Global Average", f"${mu} / liter")
    col2.metric("σ (Std. Dev.)", f"{sigma}")
    col3.metric("Countries", f"{len(df)}")
    
    st.caption(f"Data last updated: {date} | Source: GlobalPetrolPrices.com")
    
    # Country input with searchable dropdown, placed in a sidebar for clarity
    with st.sidebar:
        st.header("🔎 Compare Your Country")
        country_input = st.selectbox(
            "Select your country:",
            options=[""] + sorted(df['Country'].tolist()),
            index=0,
            format_func=lambda x: "Type or select..." if x == "" else x,
            help="Start typing to search and select your country. Use Tab or arrow keys to choose."
        )
        show_plot = st.checkbox("Show distribution plot", True)
        st.markdown(
            "<small style='color:gray;'>Tip: Start typing and we'll help find the closest match!</small>",
            unsafe_allow_html=True
        )

    # Main analysis section
    if country_input and country_input != "":
        q = country_input  # Directly use the selected value from dropdown

        try:
            value = float(df[df['Country'] == q]['Price'].values[0])
            # Display price and refresh date
            st.success(f'Current price in **{q}**: **${value}**')
            st.write(f"Data refreshed on: **{date}** (source: GlobalPetrolPrices.com)")
            
            # Use color-coded markdown for price comparison
            if value > mu:
                st.markdown(f"<span style='color:crimson;'>{q}'s price is {round(((value-mu)/value)*100)}% higher than world average (${mu}/liter).</span>", unsafe_allow_html=True)
            else:
                st.markdown(f"<span style='color:green;'>{q}'s price is {round(((value-mu)/value)*100)}% lower than world average (${mu}/liter).</span>", unsafe_allow_html=True)
            
            # Position in global distribution
            st.write(f"**{q}'s Position in global distribution:**")
            if value < o_std and value > mu:
                st.info(f'{q} pays what 68% of countries pay.')
            elif value < mu and value > nv_mu_80:
                st.info(f'{q} pays what 68% of countries pay.')
            elif value < nv_mu_80 and value > nv_mu_95:
                st.warning(f'{q} pays less than 80% of countries.')
            elif value < nv_mu_95:
                st.warning(f'{q} pays less than 95% of countries.')
            elif value > o_std:
                st.error(f'{q} pays more than 80% of countries.')

            # Normal distribution visualization
            if show_plot:
                data = np.random.normal(mu, sigma, 170)
                fig, ax = plt.subplots(figsize=(10, 6))
                ax.hist(data, 30, density=True, stacked=True, alpha=0.5, color="#0072B5")
                ax.plot(
                    np.linspace(min(data), max(data), 100),
                    1/(sigma * np.sqrt(2 * np.pi)) * np.exp(-(np.linspace(min(data), max(data), 100) - mu)**2 / (2 * sigma**2)),
                    linewidth=2, color='#FF800E'
                )
                ax.axvline(value, color='#3CB371', linestyle='dashed', linewidth=2, label=f"{q}'s Price")
                ax.set_title(f"Global Price Distribution ({date})", fontsize=16, color='#0072B5')
                ax.set_xlabel("Price ($/liter)", fontsize=12)
                ax.set_ylabel("Density", fontsize=12)
                ax.legend()
                st.pyplot(fig)
                
        except Exception as e:
            st.error('Name not found')

if __name__ == "__main__":
    main()


# In[ ]:




