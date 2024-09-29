import requests
from bs4 import BeautifulSoup
import streamlit as st
import numpy as np

# Function to scrape company data from Screener.in
def fetch_company_data(symbol):
    url = f"https://www.screener.in/company/{symbol}/consolidated/"
    response = requests.get(url)
    if response.status_code != 200:
        url = f"https://www.screener.in/company/{symbol}/"
        response = requests.get(url)
    
    soup = BeautifulSoup(response.text, 'html.parser')
    return soup

# Function to extract financials like PE, RoCE, sales/profit growth, etc.
def extract_financials(soup):
    try:
        # Extract Stock PE
        pe_value = soup.find(text="Stock PE").find_next("span").text
        
        # Assuming further elements (5-year median RoCE, growth rates, etc.)
        # are available similarly as HTML elements. Extract as required.
        # Placeholder values:
        roce_5yr = 20.0  # Placeholder for 5-yr median RoCE
        growth_ttm = 12.0  # Placeholder for TTM growth
        growth_3yr = 10.0  # Placeholder for 3-year growth
        growth_5yr = 8.0  # Placeholder for 5-year growth
        growth_10yr = 6.0  # Placeholder for 10-year growth
        
        return {
            "pe_value": pe_value,
            "roce_5yr": roce_5yr,
            "growth_ttm": growth_ttm,
            "growth_3yr": growth_3yr,
            "growth_5yr": growth_5yr,
            "growth_10yr": growth_10yr
        }
    except Exception as e:
        st.error("Error fetching or parsing data")
        return None

# Function to calculate intrinsic PE using DCF model
def calculate_intrinsic_pe(cost_of_capital, roce, growth_high, growth_period, fade_period, terminal_growth):
    tax_rate = 0.25
    
    # High Growth Period Calculation (assuming earnings grow at growth_high)
    earnings_high_growth = []
    for i in range(growth_period):
        earnings_high_growth.append((1 + growth_high / 100) ** i)
    
    # Fade Period Calculation (earnings growth fades to terminal growth)
    fade_rate = (growth_high - terminal_growth) / fade_period
    earnings_fade = []
    for i in range(fade_period):
        growth_rate = growth_high - fade_rate * (i + 1)
        earnings_fade.append((1 + growth_rate / 100) ** (growth_period + i))
    
    # Terminal Value Calculation (using terminal growth rate)
    terminal_value = (1 + terminal_growth / 100) ** (growth_period + fade_period) / (cost_of_capital / 100)
    
    # Total intrinsic value = sum of discounted earnings + terminal value
    earnings_total = np.sum(earnings_high_growth) + np.sum(earnings_fade) + terminal_value
    intrinsic_pe = earnings_total * (1 - tax_rate)
    
    return intrinsic_pe

# Function to calculate degree of overvaluation
def calculate_overvaluation(current_pe, fy23_pe, intrinsic_pe):
    lower_pe = min(current_pe, fy23_pe)
    overvaluation = (lower_pe / intrinsic_pe) - 1
    return overvaluation

# Streamlit App Structure
st.title("Financial Dashboard")
st.sidebar.header("Company and Model Inputs")

# Input fields for company symbol and financial parameters
symbol = st.sidebar.text_input("Enter NSE/BSE Symbol", "NESTLEIND")
cost_of_capital = st.sidebar.slider("Cost of Capital (%)", 5.0, 15.0, 10.0)
roce = st.sidebar.slider("RoCE (%)", 5.0, 50.0, 20.0)
growth_high = st.sidebar.slider("High Growth Rate (%)", 5.0, 30.0, 15.0)
growth_period = st.sidebar.slider("High Growth Period (Years)", 5, 20, 15)
fade_period = st.sidebar.slider("Fade Period (Years)", 5, 20, 15)
terminal_growth = st.sidebar.slider("Terminal Growth Rate (%)", 1.0, 5.0, 2.0)

# Fetch and display company financial data
company_data = fetch_company_data(symbol)
if company_data:
    financials = extract_financials(company_data)
    
    if financials:
        # Display key metrics
        st.write(f"Stock PE: {financials['pe_value']}")
        st.write(f"5-Year Median RoCE: {financials['roce_5yr']}%")
        st.write(f"Sales Growth (TTM): {financials['growth_ttm']}%")
        st.write(f"Sales Growth (3-Year): {financials['growth_3yr']}%")
        st.write(f"Sales Growth (5-Year): {financials['growth_5yr']}%")
        st.write(f"Sales Growth (10-Year): {financials['growth_10yr']}%")
        
        # Placeholder for FY23 PE Calculation
        fy23_pe = 50  # Placeholder - calculate based on scraped data
        
        # Calculate intrinsic PE
        intrinsic_pe = calculate_intrinsic_pe(cost_of_capital, roce, growth_high, growth_period, fade_period, terminal_growth)
        st.write(f"Calculated Intrinsic PE: {intrinsic_pe:.2f}")
        
        # Calculate overvaluation
        current_pe = float(financials['pe_value'])
        overvaluation = calculate_overvaluation(current_pe, fy23_pe, intrinsic_pe)
        st.write(f"Degree of Overvaluation: {overvaluation:.2%}")
