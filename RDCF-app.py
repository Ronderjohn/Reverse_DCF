import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

# Function to scrape Screener.in data
def fetch_company_data(symbol):
    # Try fetching consolidated data
    url = f"https://www.screener.in/company/{symbol}/"
    response = requests.get(url)
    if response.status_code != 200:  # If not available, fallback to standalone data
        url = f"https://www.screener.in/company/{symbol}/"
        response = requests.get(url)

    soup = BeautifulSoup(response.text, 'html.parser')
    return soup

# Function to extract financial metrics from the scraped page
def extract_financials(soup):
    # Find Stock PE
    try:
        pe_value = soup.find(text="Stock P/E").find_next("span").text.strip()
    except:
        pe_value = "N/A"

    # Find Market Cap
    try:
        market_cap = soup.find(text="Market Cap").find_next("span").text.strip()
    except:
        market_cap = "N/A"

    # Find Net Profit for FY23 (Assuming this is found in the 'Profit & Loss' section)
    try:
        net_profit_fy23 = soup.find("td", string="Net Profit").find_next("td").text.strip()
    except:
        net_profit_fy23 = "N/A"

    # Find 5-Year RoCE Median
    try:
        roce_values = soup.find(text="RoCE %").find_all_next("td", limit=5)
        roce_median = pd.Series([float(value.text.strip('%')) for value in roce_values]).median()
    except:
        roce_median = "N/A"
    
    # Placeholder for sales and profit growth, scraped from HTML structure
    growth_data = {
        "10Y Sales Growth": "N/A",
        "5Y Sales Growth": "N/A",
        "3Y Sales Growth": "N/A",
        "TTM Sales Growth": "N/A",
        "10Y Profit Growth": "N/A",
        "5Y Profit Growth": "N/A",
        "3Y Profit Growth": "N/A",
        "TTM Profit Growth": "N/A",
    }

    return {
        "pe_value": pe_value,
        "market_cap": market_cap,
        "net_profit_fy23": net_profit_fy23,
        "roce_median": roce_median,
        "growth_data": growth_data,
    }

# DCF model for intrinsic PE calculation
def calculate_intrinsic_pe(cost_of_capital, roce, growth_high, growth_period, fade_period, terminal_growth):
    tax_rate = 0.25
    intrinsic_pe = (roce - tax_rate) / cost_of_capital * growth_high * (growth_period + fade_period)
    return round(intrinsic_pe, 2)

# Degree of overvaluation calculation
def calculate_overvaluation(current_pe, fy23_pe, intrinsic_pe):
    if current_pe < fy23_pe:
        degree_of_ov = (current_pe / intrinsic_pe) - 1
    else:
        degree_of_ov = (fy23_pe / intrinsic_pe) - 1
    return round(degree_of_ov * 100, 2)  # Expressed as a percentage

# Main Streamlit app structure
def main():
    st.title("Financial Data Analysis and Intrinsic PE Calculation")
    st.sidebar.header("User Input")

    # User Inputs for NSE/BSE Symbol and Financial Parameters
    symbol = st.sidebar.text_input("Enter NSE/BSE Symbol", "NESTLEIND")
    cost_of_capital = st.sidebar.slider("Cost of Capital (%)", 5, 15, 10)
    roce = st.sidebar.slider("RoCE (%)", 5, 50, 20)
    growth_high = st.sidebar.slider("High Growth Rate (%)", 5, 30, 15)
    growth_period = st.sidebar.slider("High Growth Period (Years)", 5, 20, 15)
    fade_period = st.sidebar.slider("Fade Period (Years)", 5, 20, 15)
    terminal_growth = st.sidebar.slider("Terminal Growth Rate (%)", 1, 5, 2)

    # Scrape and display company data
    st.subheader(f"Financial Data for {symbol}")
    company_data = fetch_company_data(symbol)
    financials = extract_financials(company_data)

    # Display scraped data
    st.write(f"Stock PE: {financials['pe_value']}")
    st.write(f"Market Cap: {financials['market_cap']}")
    st.write(f"FY23 Net Profit: {financials['net_profit_fy23']}")
    st.write(f"5-Year Median RoCE (Pre-tax): {financials['roce_median']}")

    # Sales and Profit Growth Table
    growth_df = pd.DataFrame({
        "Period": ["10Y", "5Y", "3Y", "TTM"],
        "Sales Growth": [financials['growth_data']["10Y Sales Growth"], financials['growth_data']["5Y Sales Growth"], financials['growth_data']["3Y Sales Growth"], financials['growth_data']["TTM Sales Growth"]],
        "Profit Growth": [financials['growth_data']["10Y Profit Growth"], financials['growth_data']["5Y Profit Growth"], financials['growth_data']["3Y Profit Growth"], financials['growth_data']["TTM Profit Growth"]],
    })

    st.table(growth_df)

    # Plot sales growth
    fig_sales = px.bar(growth_df, x='Period', y='Sales Growth', title="Sales Growth over Different Periods")
    st.plotly_chart(fig_sales)

    # Plot profit growth
    fig_profit = px.bar(growth_df, x='Period', y='Profit Growth', title="Profit Growth over Different Periods")
    st.plotly_chart(fig_profit)

    # Perform Intrinsic PE calculation
    intrinsic_pe = calculate_intrinsic_pe(cost_of_capital, roce, growth_high, growth_period, fade_period, terminal_growth)
    st.write(f"Calculated Intrinsic PE: {intrinsic_pe}")

    # Example: using random values for Current PE and FY23 PE
    current_pe = 45.0  # This would be scraped from the webpage
    fy23_pe = 50.0     # FY23 PE from the webpage, scraped

    # Calculate degree of overvaluation
    degree_of_ov = calculate_overvaluation(current_pe, fy23_pe, intrinsic_pe)
    st.write(f"Degree of Overvaluation: {degree_of_ov}%")

    # Visualization using Plotly for Degree of Overvaluation
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=degree_of_ov,
        title={'text': "Overvaluation Degree"},
        gauge={'axis': {'range': [-100, 100], 'tickwidth': 1, 'tickcolor': "darkblue"},
                'bar': {'color': "red"},
                'bgcolor': "white",
                'borderwidth': 2,
                'bordercolor': "gray",
                'steps': [
                    {'range': [-100, 0], 'color': 'lightgreen'},
                    {'range': [0, 100], 'color': 'lightcoral'}],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': degree_of_ov}}))

    st.plotly_chart(fig)

if __name__ == "__main__":
    main()
