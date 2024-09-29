import streamlit as st
import fdscraper as fds
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

# Function to fetch company data using fdscraper
def fetch_company_data(symbol):
    # Fetch financial data
    try:
        # Retrieve the financials for the given symbol
        data = fds.get_financials(symbol)
        return data
    except Exception as e:
        st.error(f"Error fetching data for {symbol}: {e}")
        return None

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
    financials = fetch_company_data(symbol)

    if financials is not None:
        # Display scraped data
        pe_value = financials['pe']
        market_cap = financials['market_cap']
        net_profit_fy23 = financials['net_profit']
        roce_median = financials['roce']

        st.write(f"Stock PE: {pe_value}")
        st.write(f"Market Cap: {market_cap}")
        st.write(f"FY23 Net Profit: {net_profit_fy23}")
        st.write(f"5-Year Median RoCE (Pre-tax): {roce_median}")

        # Sample growth data (this should be adjusted according to actual data from fdscraper)
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

        # Plot sales growth
        fig_sales = px.bar(growth_df, x='Period', y='Sales Growth', title="Sales Growth over Different Periods")
        st.plotly_chart(fig_sales)

        # Plot profit growth
        fig_profit = px.bar(growth_df, x='Period', y='Profit Growth', title="Profit Growth over Different Periods")
        st.plotly_chart(fig_profit)

        # Perform Intrinsic PE calculation
        intrinsic_pe = calculate_intrinsic_pe(cost_of_capital, roce, growth_high, growth_period, fade_period, terminal_growth)
        st.write(f"Calculated Intrinsic PE: {intrinsic_pe}")

        # Example values for Current PE and FY23 PE
        current_pe = float(pe_value)  # Ensure this is a float for calculations
        fy23_pe = float(pe_value)      # Assuming FY23 PE is the same as the current PE

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
