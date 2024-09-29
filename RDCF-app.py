import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import plotly.express as px

# Function to scrape stock data from Screener.in
def scrape_screener(stock_symbol):
    url = f"https://www.screener.in/company/{stock_symbol}/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
    }
    
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        st.error(f"Failed to retrieve data for {stock_symbol}. Status code: {response.status_code}")
        return None

    soup = BeautifulSoup(response.content, 'html.parser')
    data = {}

    try:
        # Find the container that holds the financial metrics
        metrics_container = soup.find_all('li', class_='flex flex-space-between')
        
        for metric in metrics_container:
            label = metric.find('span', class_='name')
            value = metric.find('span', class_='number')
            if label and value:
                data[label.get_text(strip=True)] = value.get_text(strip=True)

    except Exception as e:
        st.error(f"Error occurred: {e}")
        return None

    return data

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

    # Fetch company data
    st.subheader(f"Financial Data for {symbol}")
    financials = scrape_screener(symbol)

    if financials is not None:
        try:
            # Extracting relevant financial data
            current_pe = float(financials.get('PE', 0).replace(',', ''))  # Replace commas for conversion
            fy23_net_profit = float(financials.get('Net Profit', 0).replace(',', ''))  # Replace commas for conversion
            fy23_pe = current_pe  # Assuming FY23 PE is the same as the current PE
            roce_median = float(financials.get('RoCE', 0).replace('%', '').strip())  # Replace % for conversion

            st.write(f"Current PE: {current_pe}")
            st.write(f"FY23 Net Profit: {fy23_net_profit}")
            st.write(f"5-Year Median RoCE (Pre-tax): {roce_median}")

            # Sample growth data (you'll need to scrape this too or use placeholder data)
            growth_data = {
                "10Y Sales Growth": 12.0,  # Placeholder
                "5Y Sales Growth": 8.0,    # Placeholder
                "3Y Sales Growth": 5.0,    # Placeholder
                "TTM Sales Growth": 10.0,  # Placeholder
                "10Y Profit Growth": 11.0,  # Placeholder
                "5Y Profit Growth": 7.0,    # Placeholder
                "3Y Profit Growth": 4.0,    # Placeholder
                "TTM Profit Growth": 9.0,   # Placeholder
            }

            # Sales and Profit Growth Table
            growth_df = pd.DataFrame({
                "Period": ["10Y", "5Y", "3Y", "TTM"],
                "Sales Growth (%)": [growth_data["10Y Sales Growth"], growth_data["5Y Sales Growth"], growth_data["3Y Sales Growth"], growth_data["TTM Sales Growth"]],
                "Profit Growth (%)": [growth_data["10Y Profit Growth"], growth_data["5Y Profit Growth"], growth_data["3Y Profit Growth"], growth_data["TTM Profit Growth"]],
            })

            st.table(growth_df)

            # Plot sales growth
            fig_sales = px.bar(growth_df, x='Period', y='Sales Growth (%)', title="Sales Growth over Different Periods")
            st.plotly_chart(fig_sales)

            # Plot profit growth
            fig_profit = px.bar(growth_df, x='Period', y='Profit Growth (%)', title="Profit Growth over Different Periods")
            st.plotly_chart(fig_profit)

            # Perform Intrinsic PE calculation
            intrinsic_pe = calculate_intrinsic_pe(cost_of_capital, roce_median, growth_high, growth_period, fade_period, terminal_growth)
            st.write(f"Calculated Intrinsic PE: {intrinsic_pe}")

            # Calculate degree of overvaluation
            degree_of_ov = calculate_overvaluation(current_pe, fy23_pe, intrinsic_pe)
            st.write(f"Degree of Overvaluation: {degree_of_ov}%")

            # Visualization using Plotly for Degree of Overvaluation
            fig = px.gauge(
                value=degree_of_ov,
                title='Overvaluation Degree',
                range=[-100, 100],
                color=degree_of_ov,
                color_continuous_scale=px.colors.sequential.Plasma
            )
            st.plotly_chart(fig)

        except ValueError as e:
            st.error(f"Value conversion error: {e}")
        except KeyError as e:
            st.error(f"Missing key in the fetched data: {e}")

if __name__ == "__main__":
    main()
