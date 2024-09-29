import streamlit as st
import requests
from bs4 import BeautifulSoup
import plotly.graph_objects as go

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
        pe_value = soup.find(text="Stock PE").find_next("span").text.strip()
    except:
        pe_value = "N/A"
    
    # Placeholder for other metrics, to be scraped similarly
    # Here we are extracting values using beautifulsoup. Adapt the scraping logic for specific HTML tags in the Screener.in website.
    try:
        market_cap = soup.find(text="Market Cap").find_next("span").text.strip()
    except:
        market_cap = "N/A"
    
    return {
        "pe_value": pe_value,
        "market_cap": market_cap,
        # Add other metrics like RoCE, sales growth, etc.
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
    cost_of_capital = st.sidebar.slider("Cost of Capital (%)", 5.0, 15.0, 10.0)
    roce = st.sidebar.slider("RoCE (%)", 5.0, 50.0, 20.0)
    growth_high = st.sidebar.slider("High Growth Rate (%)", 5.0, 30.0, 15.0)
    growth_period = st.sidebar.slider("High Growth Period (Years)", 5, 20, 15)
    fade_period = st.sidebar.slider("Fade Period (Years)", 5, 20, 15)
    terminal_growth = st.sidebar.slider("Terminal Growth Rate (%)", 1.0, 5.0, 2.0)

    # Scrape and display company data
    st.subheader(f"Financial Data for {symbol}")
    company_data = fetch_company_data(symbol)
    financials = extract_financials(company_data)

    # Display scraped data
    st.write(f"Stock PE: {financials['pe_value']}")
    st.write(f"Market Cap: {financials['market_cap']}")
    # Display other financial metrics...

    # Perform Intrinsic PE calculation
    intrinsic_pe = calculate_intrinsic_pe(cost_of_capital, roce, growth_high, growth_period, fade_period, terminal_growth)
    st.write(f"Calculated Intrinsic PE: {intrinsic_pe}")

    # Example: using random values for Current PE and FY23 PE
    current_pe = 45.0  # This would be scraped from the webpage
    fy23_pe = 50.0     # FY23 PE from the webpage, scraped

    # Calculate degree of overvaluation
    degree_of_ov = calculate_overvaluation(current_pe, fy23_pe, intrinsic_pe)
    st.write(f"Degree of Overvaluation: {degree_of_ov}%")

    # Visualization using Plotly (if needed)
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
