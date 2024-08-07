#!/usr/bin/env python
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from requests import get
from argparse import ArgumentParser
from selenium.webdriver.support.select import Select
from selenium.common.exceptions import NoSuchElementException

parser = ArgumentParser(description="Syncs the value in a helper entity in home assistant to a fronius inverter's soft limit field.")

parser.add_argument('-t', '--home_assistant_token', type=str, required=True, help='Home Assistant Token')
parser.add_argument('-u', '--home_assistant_url', type=str, required=True, help='Home Assistant URL. Eg: http://192.168.2.100:8123')
parser.add_argument('-f', '--fronius_url', type=str, required=True, help='Fronius URL. Eg: http://192.168.2.100')
parser.add_argument('-p', '--fronius_password', type=str, required=True, help='Fronius service account password')
parser.add_argument('-e', '--home_assistant_export_limit_entity', type=str, default='input_number.export_limit', help='Home Assistant Export Limit Entity (default: input_number.export_limit)')
parser.add_argument('-n', '--not_headless', action="store_true", help="Do not run firefox in headless mode. Might be useful if running the script locally to test it or something...")

args = parser.parse_args()

options = webdriver.FirefoxOptions()
if not args.not_headless:
    options.add_argument("-headless")
driver = webdriver.Firefox(options)

try:
    driver.implicitly_wait(10)
    driver.get(f"{args.fronius_url}/#/settings/evu")

    # While we're waiting for firefox to load, lets get the expected limit
    response = get(
        f"{args.home_assistant_url}/api/states/{args.home_assistant_export_limit_entity}",
        headers={
            "Authorization": f"Bearer {args.home_assistant_token}"
        }
    ).json()
    desired_limit = int(float(response["state"]))
    if desired_limit < -1:
        print("Setting to 0, rather than", desired_limit)
        desired_limit = 0
    else:
        print("Setting to", desired_limit)
    # Ok, back to webdriver.

    username = Select(driver.find_element(By.TAG_NAME, "select"))
    username.select_by_visible_text("service")
    password = driver.find_element(By.CSS_SELECTOR, "[type=password]")
    password.send_keys(args.fronius_password)
    password.send_keys(Keys.RETURN)

    try:
        limit = driver.find_element(By.CSS_SELECTOR, '[input-validator="softLimitValidator"]')
    except NoSuchElementException:
        driver.get(f"{args.fronius_url}/#/settings/evu")
        limit = driver.find_element(By.CSS_SELECTOR, '[input-validator="softLimitValidator"]')

    current_limit = limit.get_property("value")
    print("Existing limit: ", current_limit)
    if current_limit == str(desired_limit):
        print("They match. Skip!")
        exit(0)
    limit.clear()
    limit.send_keys(str(desired_limit))

    ok_button = driver.find_elements(By.CSS_SELECTOR, "button.OK")
    ok_button[2].click()
    driver.find_elements(By.XPATH, '//button[normalize-space()="OK"]')
except Exception:
    print(driver.find_element(By.TAG_NAME, "body").screenshot_as_base64)
    raise
finally:
    driver.close()
