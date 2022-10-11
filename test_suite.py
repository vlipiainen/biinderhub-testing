#! /bin/python

from selenium import webdriver
from datetime import datetime
import sys
import time
import logging
import argparse
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities


#driver.quit()

#driver.get("https://binder4.org.aalto.fi/v2/gh/binder-examples/jupyter-stacks-datascience/HEAD")
#driver.find_element_by_xpath('//button[normalize-space()="show"]').click()
#time.sleep(15)
#driver.save_screenshot(f'screenshot-{sys.argv[1]}.png')
#driver.close()

# https://stackoverflow.com/questions/49906237/how-to-find-button-with-selenium-by-its-text-inside-python
# https://stackoverflow.com/questions/28431765/open-web-in-new-tab-selenium-python

def take_screenshots(tabs, driver, t):
    i = 0
    for tab in tabs:
        driver.switch_to.window(tab)
        i = i + 1
        driver.save_screenshot(f'screenshots/screenshot-{i}-{time}.png')

def check_success(tabs, driver):
    succeeded = 0
    failed = 0
    pending = 0
    error_tabs = []
    success_tabs = []

    for tab in tabs:
        driver.switch_to.window(tab)
        if "JupyterLab" in driver.title:
            succeeded = succeeded + 1
            success_tabs.append(tab)
        if "Binder" in driver.title:
            pending = pending + 1
        if (len(driver.find_elements_by_class_name('error')) != 0):
            error_tabs.append(tab)
            pending = pending - 1
            failed = failed + 1
    
    return(succeeded, pending, failed, error_tabs, success_tabs)

def parse_input():
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="https://binder4.org.aalto.fi/v2/gh/binder-examples/jupyter-stacks-datascience/HEAD", type=str, help="the full url for launching a binder")
    parser.add_argument("--trials", default=2, type=int, help="number of trials")
    parser.add_argument("--delta", default=0.5, type=float, help="time between trials in seconds")
    parser.add_argument("--shortcycl", default=5, type=int, help="number of short cycles")
    parser.add_argument("--longcycl", default=10, type=int, help="number of long cycles")
    return parser.parse_args()
    

def main():
    global args
    args = parse_input()

    logging.basicConfig(filename=f'logs/tests-{datetime.now()}.log', encoding='utf-8', level=logging.INFO)
    global trial_num
    trial_num = args.trials
    url = args.url

    logging.info(f'Doing {args.trials} tests on {url} at {datetime.now()}')
    logging.info(f'Command line arguments: {args}')

    opts = webdriver.FirefoxOptions()
    opts.set_preference("dom.popup_maximum", 100)
    caps = DesiredCapabilities().FIREFOX
#    caps["pageLoadStrategy"] = "normal"  #  complete
    caps["pageLoadStrategy"] = "none"

    driver = webdriver.Firefox(options=opts, desired_capabilities=caps)

    driver.set_page_load_timeout(10)

    logging.info(f'Opening tabs')
    for n in range(trial_num - 1):
        logging.debug(f'Opening tab {n+2}')
        driver.execute_script("window.open('');")

    tabs = driver.window_handles

    logging.info(f'Fetching URLs')
    for tab in tabs:
        time.sleep(args.delta)
        try:
            logging.debug(f'Fetching url for tab {tab}')
            driver.switch_to.window(tab)
            driver.get(url)
            try: 
                driver.find_element_by_xpath('//button[normalize-space()="show"]').click()
            except:
                logging.debug("No show-button found")
        except:
            logging.warning(f'Error fetching url for tab {tab}, skipping.')


    short_cycles = args.shortcycl

    total_success = 0
    total_failed = 0
    total_pending = 0

    for n in range(short_cycles):
        logging.info(f'At {n*5} seconds, {datetime.now()}')
        succeeded, pending, failed, error_tabs, success_tabs = check_success(tabs, driver)
        total_success += succeeded
        total_failed += failed
        logging.info(f'{total_success}/{trial_num} succeeded')
        logging.info(f'{total_failed}/{trial_num} failed')
        logging.info(f'{pending} pending')
        take_screenshots(error_tabs, driver, n*60 + short_cycles*5)
        tabs = [item for item in tabs if item not in error_tabs and item not in success_tabs]
        if (len(tabs)==0):
            logging.info(f'Reached end of tests at {datetime.now()}')
            return
        logging.info("Sleeping 5 sec")
        time.sleep(5)

    long_cycles = args.longcycl
    for n in range(long_cycles):
        logging.info(f'At {n*60 + short_cycles*5} seconds, {datetime.now()}')
        succeeded, pending, failed, error_tabs, success_tabs = check_success(tabs, driver)
        logging.info(success_tabs)
        total_success += succeeded
        total_failed += failed
        logging.info(f'{total_success}/{trial_num} succeeded')
        logging.info(f'{total_failed}/{trial_num} failed')
        logging.info(f'{pending} pending')
        take_screenshots(error_tabs, driver, n*60 + short_cycles*5)
        tabs = [item for item in tabs if item not in error_tabs and item not in success_tabs]
        if (len(tabs)==0): 
            logging.info(f'Reached end of tests at {datetime.now()}')
            return
        logging.info("Sleeping 60 sec")
        time.sleep(60)

    logging.info("Reached end of tests")

if __name__ == "__main__":

    main()

# https://stackoverflow.com/questions/44770796/how-to-make-selenium-not-wait-till-full-page-load-which-has-a-slow-script/44771628#44771628
