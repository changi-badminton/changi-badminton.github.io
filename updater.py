from datetime import datetime, timedelta
from typing import List
from typing import Tuple

import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from main import extract_table, merge_tables


def get_changi_data(
    url: str = "https://www.carc.org.sg/FacilityBooking.aspx",
    agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
):
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument(f"user-agent={agent}")  # To avoid cloudflare captcha
    driver = webdriver.Chrome(options=options)  # or webdriver.Firefox(), etc.

    driver.get(url)
    table1 = extract_table(driver, facility="Badminton Court 1")
    table2 = extract_table(driver, facility="Badminton Court 2")
    driver.quit()
    data = merge_tables(table1, table2)
    markdown = data.to_markdown()

    time_now = pd.Timestamp.now("Asia/Singapore").strftime("%Y-%m-%d %H:%M:%S %Z")
    header = f"[Changi Airport Badminton Courts ({time_now})]({url})\n\n"
    return header + markdown


def format_date(day: int, month: int, year: int):
    return f"{day}/{month}/{year}"


def format_court_names(names: List[str], limit: int = 3) -> str:
    suffix = ""
    if len(names) > limit:
        suffix = f",+{len(names) - limit}"
        names = names[:limit]

    return ",".join(sorted([x.split()[0] for x in names])) + suffix


def click_item(driver, by: str, value: str):
    print(dict(click=by, value=value))
    wait = WebDriverWait(driver, 10)
    mapping = dict(css=By.CSS_SELECTOR, cls=By.CLASS_NAME, id=By.ID, xpath=By.XPATH)

    try:
        wait.until(EC.element_to_be_clickable((mapping[by], value))).click()
    except Exception as e:
        print(f"Could not click {value}", e)
        breakpoint()


def wait_item(driver, by: str, value: str):
    print(dict(wait=by, value=value))
    wait = WebDriverWait(driver, 10)
    mapping = dict(css=By.CSS_SELECTOR, cls=By.CLASS_NAME, id=By.ID, xpath=By.XPATH)

    try:
        wait.until(EC.presence_of_element_located((mapping[by], value)))
    except Exception as e:
        print(f"Could not find {value}", e)
        with open("error.html", "w") as f:
            f.write(driver.page_source)

    return driver.find_element(mapping[by], value)


def get_week_dates(day: int, month: int, year: int) -> List[Tuple[int, int, int]]:
    # Get current date and 6 more days
    dates = []
    for i in range(7):
        date = datetime(year, month, day) + timedelta(days=i)
        dates.append((date.day, date.month, date.year))
    return dates


def get_expo_data(
    url: str = "https://singaporebadmintonhall.getomnify.com/widgets/O3MRKGBH359GA55KHMG1RD",
    agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
):
    # Iframe from https://singaporebadmintonhall.com/expo/
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument(f"user-agent={agent}")  # To avoid cloudflare captcha
    driver = webdriver.Chrome(options=options)  # or webdriver.Firefox(), etc.
    driver.get(url)

    click_item(driver, "css", "div.dateTextWrapper")
    element = wait_item(driver, "css", "td.xdsoft_date.xdsoft_current")

    dates = get_week_dates(
        int(element.get_attribute("data-date")),
        int(element.get_attribute("data-month")) + 1,  # 0-indexed
        int(element.get_attribute("data-year")),
    )

    timings = [
        "08:00 AM",
        "09:00 AM",
        "10:00 AM",
        "11:00 AM",
        "12:00 PM",
        "01:00 PM",
        "02:00 PM",
        "03:00 PM",
        "04:00 PM",
        "05:00 PM",
        "06:00 PM",
        "07:00 PM",
        "08:00 PM",
        "09:00 PM",
        "10:00 PM",
        "11:00 PM",
    ]
    data = [dict(time=t, **{format_date(*d): [] for d in dates}) for t in timings]
    print(dict(data=data))

    for day, month, year in dates:
        click_item(driver, "css", "div.dateTextWrapper")
        click_item(driver, "css", "div.dateTextWrapper")
        click_item(
            driver,
            "css",
            f"td[data-date='{day}'][data-month='{month - 1}'][data-year='{year}']",
        )

        wait_item(driver, "cls", "week-column.facility-row")
        html = driver.page_source
        soup = BeautifulSoup(html, "html.parser")

        for s in soup.find_all("div", class_="time-slot facility-slot"):
            raw = s.attrs
            i = timings.index(raw["data-starttime"])
            if "arina" in raw.get("data-facility_name", "").lower():
                continue

            data[i][format_date(day, month, year)].append(raw["data-facility_name"])

    # Convert list columns to comma-separated strings
    df = pd.DataFrame(data)
    for col in df.columns[1:]:
        df[col] = df[col].apply(format_court_names)
    print(df)

    markdown = df.to_markdown(index=False)
    time_now = pd.Timestamp.now("Asia/Singapore").strftime("%Y-%m-%d %H:%M:%S %Z")
    header = f"[SBH Expo Badminton Courts ({time_now})]({url})\n\n"
    return header + markdown


def update_readme(path_out: str = "README.md"):
    data = get_changi_data() + "\n\n" + get_expo_data()
    with open(path_out, "w") as f:
        print(data, file=f)


if __name__ == "__main__":
    update_readme()
