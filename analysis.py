import time

import dotenv
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


"""
p analysis.py take_screenshot --url "https://www.carc.org.sg/FacilityBooking.aspx"
p analysis.py take_screenshot --url "http://ibms.sutd.edu.sg"
p analysis.py take_screenshot --url "https://usermgmtsys.sutd.edu.sg/login"
p analysis.py take_screenshot --url "https://usermgmtsys.sutd.edu.sg/login"
python analysis.py check_sutd
"""

if __name__ == "__main__":
    Fire()
