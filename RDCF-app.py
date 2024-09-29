import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import numpy as np
from datetime import datetime

# Initialize page configuration
st.set_page_config(layout="wide", page_title="Company Dashboard")

# Function to scrape data from screener.in
def scrape_screener(symbol, consolidated=True):
    url = f"https://www.screener.in/company/{symbol}"
    if consolidated:
        url += "/consolidated"
    
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Extract relevant information
    pe_current = float(soup.find('span', class_='value').text.strip())
    fy23_pe = None
    
    # Calculate FY23 PE
    market_cap = float(soup.find('div', class_='market-cap').text.replace(',', '').strip().split()[0]) * 100000000
    net_profit_fy23 = float(soup.find('td', text=lambda t: t and 'Net Profit' in t).find_next_sibling('td').text.replace(',', '').strip()) * 100000000
    fy23_pe = market_cap / net_profit_fy23 if net_profit_fy23 != 0 else None
    
    roce_5_year_median = float(soup.find('td', text=lambda t: t and 'ROCE' in t).find_next_sibling('td').text.strip())
    
    # Extract growth rates
    growth_rates = {}
    for year in ['TTM', '3Y', '5Y', '10Y']:
        growth_rate = float(soup.find('td', text=lambda t: t and f'{year} Growth Rate' in t).find_next_sibling('td').text.strip())
        growth_rates[year] = growth_rate
    
    return {
        'pe_current': pe_current,
        'fy23_pe': fy23_pe,
        'roce_5_year_median': roce_5_year_median,
        'growth_rates': growth_rates
    }

# Function to calculate intrinsic PE and degree of overvaluation
def calculate_dcf_model(cost_of_capital, roce, high_growth_period, fade_period, terminal_growth_rate):
    intrinsic_pe = (
        (roce * (1 + terminal_growth_rate)) /
        ((cost_of_capital - terminal_growth_rate) * (1 + cost_of_capital)**fade_period)
    ) * (
        (1 + cost_of_capital)**high_growth_period -
        (1 + terminal_growth_rate)**high_growth_period
    ) / (
        (1 + cost_of_capital)**fade_period -
        (1 + terminal_growth_rate)**fade_period
    )
    return intrinsic_pe

def calculate_degree_of_overvaluation(current_pe, fy23_pe, intrinsic_pe):
    if current_pe < fy23_pe:
        return (current_pe / intrinsic_pe) - 1
    else:
        return (fy23_pe / intrinsic_pe) - 1

# Main function to run the app
def main():
    st.title("Company Dashboard")
    
    # Sidebar for user input
    st.sidebar.header("User Input")
    symbol_input = st.sidebar.text_input("Enter NSE/BSE Symbol", "NESTLEIND")
    
    # Call the data loading function
    company_data = scrape_screener(symbol_input)
    
    # Display the dashboard
    display_dashboard(company_data)
    
    # DCF model inputs
    cost_of_capital = st.number_input("Cost of Capital (%)", min_value=0.01, max_value=0.20, value=0.08, step=0.01)
    roce = st.number_input("ROCE (%)", min_value=0.05, max_value=0.50, value=0.20, step=0.01)
    high_growth_period = st.number_input("High Growth Period (Years)", min_value=1, max_value=30, value=15, step=1)
    fade_period = st.number_input("Fade Period (Years)", min_value=1, max_value=30, value=15, step=1)
    terminal_growth_rate = st.number_input("Terminal Growth Rate (%)", min_value=-0.01, max_value=0.20, value=0.03, step=0.001)
    
    # Calculate intrinsic PE and degree of overvaluation
    intrinsic_pe = calculate_dcf_model(cost_of_capital/100, roce/100, high_growth_period, fade_period, terminal_growth_rate)
    degree_of_overvaluation = calculate_degree_of_overvaluation(company_data['pe_current'], company_data['fy23_pe'], intrinsic_pe)
    
    # Display results
    st.subheader("DCF Model Results")
    st.write(f"Intrinsic PE: {intrinsic_pe:.2f}")
    st.write(f"Degree of Overvaluation: {degree_of_overvaluation:.2f}")

def display_dashboard(company_data):
    st.subheader(f"Company Overview: {company_data['symbol']}")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Current PE", f"{company_data['pe_current']:.2f}")
        st.metric("FY23 PE", f"{company_data['fy23_pe']:.2f}" if company_data['fy23_pe'] else "-")
        st.metric("5-Year Median ROCE", f"{company_data['roce_5_year_median']:.2f}%")
    
    with col2:
        st.metric("TTM Growth", f"{company_data['growth_rates']['TTM']:.2f}%")
        st.metric("3Y Growth", f"{company_data['growth_rates']['3Y']:.2f}%")
        st.metric("5Y Growth", f"{company_data['growth_rates']['5Y']:.2f}%")
        st.metric("10Y Growth", f"{company_data['growth_rates']['10Y']:.2f}%")

if __name__ == "__main__":
    main()
