import time
from datetime import datetime, timedelta
from typing import List, Tuple

import dotenv
import pandas as pd
from bs4 import BeautifulSoup
from fire import Fire
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


def take_screenshot(url: str, path: str = "screenshot.png"):
    options = Options()
    options.add_argument("--headless")  # Run in headless mode (optional)
    driver = webdriver.Chrome(options=options)

    driver.get(url)
    driver.save_screenshot(path)
    driver.quit()

    print(f"Screenshot saved as {path}")


def check_sutd(url: str = "https://usermgmtsys.sutd.edu.sg/login"):
    driver = webdriver.Chrome()
    driver.get(url)
    username = dotenv.get_key(".env", "IBMS_USERNAME")
    password = dotenv.get_key(".env", "IBMS_PASSWORD")

    # Wait for the username field to be visible and enter the username
    wait = WebDriverWait(driver, 10)
    username_field = wait.until(EC.presence_of_element_located((By.ID, "username")))
    username_field.send_keys(username)

    password_field = driver.find_element(By.ID, "password")
    password_field.send_keys(password)
    login_button = driver.find_element(By.ID, "btn_submit")
    login_button.click()

    court_url = "https://facilitybookingsys.sutd.edu.sg/bookings/booking-scheduler-search?building_id=19"
    driver.get(court_url)
    print("Logged in successfully!")
    time.sleep(1)
    driver.save_screenshot("demo.png")
    driver.quit()


def get_week_dates(day: int, month: int, year: int) -> List[Tuple[int, int, int]]:
    # Get current date and 6 more days
    dates = []
    for i in range(7):
        date = datetime(year, month, day) + timedelta(days=i)
        dates.append((date.day, date.month, date.year))
    return dates


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


def check_expo(
    url: str = "https://singaporebadmintonhall.getomnify.com/widgets/O3MRKGBH359GA55KHMG1RD",
):
    # Iframe from https://singaporebadmintonhall.com/expo/
    driver = webdriver.Chrome()
    driver.get(url)

    click_item(driver, "css", "div.dateTextWrapper")
    element = wait_item(driver, "css", "td.xdsoft_date.xdsoft_current")
    day = int(element.get_attribute("data-date"))
    month = int(element.get_attribute("data-month"))
    year = int(element.get_attribute("data-year"))
    print(dict(day=day, month=month, year=year))

    all_slots = []
    for day, month, year in get_week_dates(day, month, year):
        click_item(driver, "css", "div.dateTextWrapper")
        click_item(driver, "css", "div.dateTextWrapper")
        click_item(
            driver,
            "css",
            f"td[data-date='{day}'][data-month='{month}'][data-year='{year}']",
        )

        wait_item(driver, "cls", "week-column.facility-row")
        html = driver.page_source
        soup = BeautifulSoup(html, "html.parser")

        for s in soup.find_all("div", class_="time-slot facility-slot"):
            raw = s.attrs
            print(raw)
            if "arina" in raw.get("data-facility_name", "").lower():
                continue
            all_slots.append(dict(day=day, month=month + 1, year=year, **raw))

        df = pd.DataFrame(all_slots)
        print(df)


"""
p analysis.py take_screenshot --url "https://www.carc.org.sg/FacilityBooking.aspx"
p analysis.py take_screenshot --url "http://ibms.sutd.edu.sg"
p analysis.py take_screenshot --url "https://usermgmtsys.sutd.edu.sg/login"
p analysis.py take_screenshot --url "https://usermgmtsys.sutd.edu.sg/login"
python analysis.py check_sutd
python analysis.py check_expo
"""

if __name__ == "__main__":
    Fire()
