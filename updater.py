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


def get_webdriver(
    agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
):
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument(f"user-agent={agent}")  # To avoid cloudflare captcha
    return webdriver.Chrome(options=options)


def get_changi_data(url: str = "https://www.carc.org.sg/FacilityBooking.aspx"):
    driver = get_webdriver()
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


def click_item(driver, by: str, value: str, break_on_error: bool = True):
    print(dict(click=by, value=value))
    wait = WebDriverWait(driver, 3)
    mapping = dict(css=By.CSS_SELECTOR, cls=By.CLASS_NAME, id=By.ID, xpath=By.XPATH)

    try:
        wait.until(EC.element_to_be_clickable((mapping[by], value))).click()
    except Exception as e:
        print(f"Could not click {value}", e)
        if break_on_error:
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
):
    # Iframe from https://singaporebadmintonhall.com/expo/
    driver = get_webdriver()
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
    data = [dict(Time=t, **{format_date(*d): [] for d in dates}) for t in timings]
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


def get_origin_data(
    url: str = "https://originbadmintontennis.setmore.com/book?step=time-slot&products=sgrolacnx0m9p2mqoycdgk0n9upmhxc1&type=service&staff=cg98cjfg44hsmkg1roi2w3m3unolyliw&staffSelected=true",
):
    today = datetime.now()
    data = []

    for day, month, year in get_week_dates(today.day, today.month, today.year):
        text = datetime(year, month, day).strftime("%-d %B %Y")
        print(text)
        driver = get_webdriver()
        driver.get(url)

        click_item(driver, "css", f"button[aria-label*='{text}']", break_on_error=False)
        soup = BeautifulSoup(driver.page_source, "html.parser")

        # Find all time spans
        time_slots = []
        for time_element in soup.find_all(
            "span", {"class": "where:block inline text-body-14 font-strong"}
        ):
            time = time_element.text
            # Find the adjacent PM/AM span
            period = time_element.find_next_sibling(
                "span",
                {"class": "where:block inline text-primary text-body-12 font-strong"},
            ).text.strip()
            time_slots.append(f"{time}{period}")

        # Print all time slots
        for slot in time_slots:
            print(slot)

        data.append(dict(Date=text, Slots=",".join(time_slots).strip()))

    df = pd.DataFrame(data)
    markdown = df.to_markdown(index=False)
    time_now = pd.Timestamp.now("Asia/Singapore").strftime("%Y-%m-%d %H:%M:%S %Z")
    header = f"[Origin Badminton Stringing ({time_now})]({url})\n\n"
    return header + markdown


def update_readme(path_out: str = "README.md"):
    data = get_changi_data() + "\n\n" + get_expo_data() + "\n\n" + get_origin_data()
    with open(path_out, "w") as f:
        print(data, file=f)


if __name__ == "__main__":
    update_readme()
