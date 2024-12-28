import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from main import extract_table, merge_tables


def update_readme(
    url: str = "https://www.carc.org.sg/FacilityBooking.aspx",
    path_out: str = "README.md",
):
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
    data = merge_tables(table1, table2)
    markdown = data.to_markdown()

    time_now = pd.Timestamp.now("Asia/Singapore").strftime("%Y-%m-%d %H:%M:%S %Z")
    header = f"[Changi Airport Badminton Courts ({time_now})]({url})\n\n"
    with open(path_out, "w") as f:
        print(header + markdown, file=f)


if __name__ == "__main__":
    update_readme()
