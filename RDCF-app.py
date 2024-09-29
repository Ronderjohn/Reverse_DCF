import streamlit as st
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd

# Function to scrape stock data from Screener.in
def scrape_screener(stock_symbol):
    # Initialize Selenium WebDriver
    service = Service('/path/to/chromedriver')  # Update path to your chromedriver
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')  # Run in headless mode
    driver = webdriver.Chrome(service=service, options=options)

    try:
        # Load the stock page
        url = f"https://www.screener.in/company/{stock_symbol}/"
        driver.get(url)

        # Wait until the page loads and the "5Yr" button is clickable
        wait = WebDriverWait(driver, 10)
        five_year_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@value='1825']")))
        five_year_button.click()  # Click the "5Yr" button

        # Wait for the chart to load
        wait.until(EC.presence_of_element_located((By.ID, 'chart')))

        # Extracting the tooltip values
        chart_section = driver.find_element(By.ID, 'chart')
        
        # Find the tooltip for the date 1 year prior
        # Adjusting to the correct date might require some manipulation based on the current date
        tooltip = driver.find_element(By.XPATH, "//div[@id='chart-tooltip-title']")

        # Extract values from the tooltip
        tooltip_text = tooltip.text
        values = {}
        if "PE:" in tooltip_text:
            # Parse PE and EPS from the tooltip text
            parts = tooltip_text.split(' ')
            for part in parts:
                if 'PE:' in part:
                    values['FY23 PE'] = part.split(':')[1].strip()
                elif 'EPS:' in part:
                    values['EPS TTM'] = part.split(':')[1].strip()

        # Extract other metrics from the page
        metrics_container = driver.find_elements(By.CLASS_NAME, 'flex.flex-space-between')
        for metric in metrics_container:
            label = metric.find_element(By.CLASS_NAME, 'name').text
            value = metric.find_element(By.CLASS_NAME, 'number').text.replace(',', '')

            # Store relevant data only
            if label in ['Stock P/E', 'Market Cap', 'Net Profit (FY23)']:
                values[label] = value

        # Extract 5-Year Median RoCE from the chart legend or tooltip (if present)
        legend_items = chart_section.find_elements(By.TAG_NAME, 'label')
        for item in legend_items:
            if "Median RoCE" in item.text:
                values['5 Yr Median RoCE'] = item.text.split('=')[-1].strip()

    except Exception as e:
        st.error(f"Error occurred: {e}")
        return None
    finally:
        driver.quit()  # Ensure the browser is closed after execution

    return values

# Streamlit app to use the scrape_screener function
def main():
    st.title("Screener.in Stock Data Scraper")
    stock_symbol = st.text_input("Enter Stock Symbol (e.g., AAPL):")
    
    if st.button("Scrape Data"):
        if stock_symbol:
            data = scrape_screener(stock_symbol)
            if data:
                st.write(data)
        else:
            st.error("Please enter a valid stock symbol.")

if __name__ == "__main__":
    main()
