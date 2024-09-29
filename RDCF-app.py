import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import datetime
import plotly.graph_objects as go
import plotly.express as px

# Function to scrape stock data from Screener.in
def scrape_screener(stock_symbol):
    # Screener URL for the stock
    url = f"https://www.screener.in/company/{stock_symbol}/"

    # Send a GET request to the website with headers
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
    }
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        st.error(f"Failed to retrieve data for {stock_symbol}. Status code: {response.status_code}")
        return None

    # Parse the webpage content using BeautifulSoup
    soup = BeautifulSoup(response.content, 'html.parser')

    # Dictionary to store the scraped data
    data = {}

    # Targeting the relevant section of the page for financial metrics
    try:
        # Find the container that holds the financial metrics
        metrics_container = soup.find_all('li', class_='flex flex-space-between')

        # Dictionary to hold the desired metrics
        metric_map = {
            'Stock P/E': 'Stock P/E',
            'EPS (TTM)': 'EPS TTM',
            'Market Cap': 'Market Cap',
            'Net Profit (FY23)': 'Net Profit FY23',
        }

        for metric in metrics_container:
            label = metric.find('span', class_='name')
            value = metric.find('span', class_='number')
            if label and value:
                label_text = label.get_text(strip=True)
                value_text = value.get_text(strip=True).replace(',', '')  # Remove commas for conversion

                # Store relevant data only
                if label_text in metric_map:
                    data[metric_map[label_text]] = value_text

        # Selecting the "5Yr" metrics by simulating the button click
        five_year_url = f"{url}?days=1825"  # Assuming 1825 days corresponds to 5 years
        response = requests.get(five_year_url, headers=headers)
        soup = BeautifulSoup(response.content, 'html.parser')

        # Extracting the values from the chart section for FY23 PE and 5-Year Median RoCE
        chart_section = soup.find(id='chart')
        if chart_section:
            # Extracting 5-Year Median RoCE
            median_roce_label = chart_section.find('label', string="5-Year Median RoCE")
            if median_roce_label:
                median_roce_value = median_roce_label.find_next('span').get_text(strip=True).replace(',', '')
                data['5 Yr Median RoCE'] = median_roce_value

            # Adjusting tooltip position for 1 year prior
            one_year_ago = datetime.now() - timedelta(days=365)
            tooltip_date = one_year_ago.strftime("%Y-%m-%d")

            # Here we would find the tooltip data by locating elements specific to that date
            # Example: Find the tooltip that corresponds to one_year_ago
            tooltip = chart_section.find('div', {'data-date': tooltip_date})
            if tooltip:
                tooltip_text = tooltip.get_text(strip=True)
                if 'PE:' in tooltip_text:
                    fy23_pe = tooltip_text.split('PE:')[1].split('EPS:')[0].strip()
                    data['FY23 PE'] = fy23_pe

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
            current_pe = float(financials.get('Stock P/E', '0'))  # Default to 0 if not available
            fy23_pe = float(financials.get('FY23 PE', '0'))  # Fetching FY23 PE directly from scraped data
            roce = float(financials.get('5 Yr Median RoCE', '0'))

            st.write(f"Current PE: {current_pe}")
            st.write(f"FY23 PE: {fy23_pe}")
            st.write(f"5-Year Median RoCE (Pre-tax): {roce}")

            # Sample growth data (this needs to be scraped separately if available)
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

            # Sales and Profit Growth Table
            growth_df = pd.DataFrame({
                "Period": ["10Y", "5Y", "3Y", "TTM"],
                "Sales Growth": [growth_data["10Y Sales Growth"], growth_data["5Y Sales Growth"], growth_data["3Y Sales Growth"], growth_data["TTM Sales Growth"]],
                "Profit Growth": [growth_data["10Y Profit Growth"], growth_data["5Y Profit Growth"], growth_data["3Y Profit Growth"], growth_data["TTM Profit Growth"]],
            })

            st.table(growth_df)

            # Plot sales growth (currently static data, replace with actual scraped data)
            fig_sales = px.bar(growth_df, x='Period', y='Sales Growth', title="Sales Growth over Different Periods")
            st.plotly_chart(fig_sales)

            # Plot profit growth (currently static data, replace with actual scraped data)
            fig_profit = px.bar(growth_df, x='Period', y='Profit Growth', title="Profit Growth over Different Periods")
            st.plotly_chart(fig_profit)

            # Perform Intrinsic PE calculation
            intrinsic_pe = calculate_intrinsic_pe(cost_of_capital, roce, growth_high, growth_period, fade_period, terminal_growth)
            st.write(f"Calculated Intrinsic PE: {intrinsic_pe}")

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

        except Exception as e:
            st.error(f"An error occurred while processing the data: {e}")

if __name__ == "__main__":
    main()
