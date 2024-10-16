import time
import streamlit as st

import numpy as np
import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait


def extract_table(driver: webdriver.Chrome, facility: str) -> pd.DataFrame:
    dropdown = Select(driver.find_element(By.ID, "ddlFacility"))
    dropdown.select_by_visible_text(facility)

    # Wait for the table to load (adjust the timeout as needed)
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "MyTable")))
    html = driver.page_source
    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table", {"id": "MyTable"})

    rows = []
    for tr in table.find_all("tr"):
        row = [td.text.strip() for td in tr.find_all("td")]
        rows.append(row)

    rows[0][0] = "Time"  # Rename the first column
    df = pd.DataFrame(rows[1:], columns=rows[0])
    df = df.set_index("Time")
    return df


def merge_cells(cell1, cell2):
    if cell1 == "Book Now" and cell2 == "Book Now":
        return "1,2"
    elif cell1 == "Book Now":
        return "1"
    elif cell2 == "Book Now":
        return "2"
    else:
        return ""


def merge_tables(df1: pd.DataFrame, df2: pd.DataFrame) -> pd.DataFrame:
    assert df1.shape == df2.shape, "Both DataFrames must have the same shape"
    vectorized_merge = np.vectorize(merge_cells)

    # Apply the vectorized function element-wise
    merged_values = vectorized_merge(df1.values, df2.values)
    merged_df = pd.DataFrame(merged_values, index=df1.index, columns=df1.columns)
    return merged_df


@st.cache_data(ttl=600)
def get_table(url: str) -> pd.DataFrame:
    start = time.time()

    # Set up the WebDriver with options to speed up loading
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    driver = webdriver.Chrome(options=options)  # or webdriver.Firefox(), etc.

    driver.get(url)
    table1 = extract_table(driver, facility="Badminton Court 1")
    table2 = extract_table(driver, facility="Badminton Court 2")
    driver.quit()
    st.write(f"Loading time: {time.time() - start:.2f} seconds")
    return merge_tables(table1, table2)


def main(url: str = "https://www.carc.org.sg/FacilityBooking.aspx"):
    st.header(f"[Changi Airport Badminton Courts]({url})")
    data = get_table(url)
    st.dataframe(data, height=600)


if __name__ == "__main__":
    main()
