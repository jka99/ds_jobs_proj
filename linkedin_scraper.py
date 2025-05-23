# -*- coding: utf-8 -*-
"""
Created on Tue May 20 21:00:08 2025

@author: jeffe
"""

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import pandas as pd
from urllib.parse import quote_plus


def get_jobs_linkedin(keyword: str,
                      num_jobs: int,
                      verbose: bool,
                      driver_path: str,
                      sleep_time: float) -> pd.DataFrame:
    """
    Scrapes LinkedIn Jobs for the given keyword, collecting up to num_jobs listings.
    Returns a DataFrame with summary fields and detail fields for each job.
    """
    # 1) Initialize WebDriver with a smaller window size for consistent rendering
    options = webdriver.ChromeOptions()
    # options.add_argument('headless')  # uncomment to run headless
    service = Service(driver_path)
    driver = webdriver.Chrome(service=service, options=options)
    driver.set_window_size(1200, 800)  # smaller window to reduce rendering delays

    # 2) Navigate to LinkedIn job search
    encoded_keyword = quote_plus(keyword)
    url = f"https://www.linkedin.com/jobs/search/?keywords={encoded_keyword}"
    if verbose:
        print(f"Navigating to LinkedIn jobs URL: {url}")
    driver.get(url)

    # 2b) Close potential sign-in/login modal by clicking its 'X'
    time.sleep(5)  # allow modal to appear
    for sel in [
        'button.artdeco-modal__dismiss',
        'button.modal__dismiss',
        'button.contextual-sign-in-modal__modal-dismiss',
        'button[aria-label="Dismiss"]'
    ]:
        try:
            close_btn = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, sel))
            )
            close_btn.click()
            if verbose:
                print(f"Closed popup using selector: {sel}")
            break
        except (TimeoutException, NoSuchElementException):
            continue

    # 3) Wait for at least one job card to appear
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'li[data-occludable-job-id]'))
        )
    except TimeoutException:
        print("Job cards did not load in time.")
        driver.quit()
        return pd.DataFrame()
    pane = driver.find_element(By.CSS_SELECTOR, 'div.scaffold-layout__list')

    # 4) Scroll pane to load enough cards
    cards = pane.find_elements(By.CSS_SELECTOR, 'li[data-occludable-job-id]')
    prev_count = 0
    while len(cards) < num_jobs and len(cards) != prev_count:
        prev_count = len(cards)
        driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight;", pane)
        time.sleep(sleep_time)
        cards = pane.find_elements(By.CSS_SELECTOR, 'li[data-occludable-job-id]')
        if verbose:
            print(f"Loaded {len(cards)} job cards so far...")

    # 5) Iterate through each card up to num_jobs
    jobs = []
    for card in cards[:num_jobs]:
        # Summary details from card
        try:
            title_elem = card.find_element(By.CSS_SELECTOR, 'a.job-card-list__title--link')
            title = title_elem.text
            job_url = title_elem.get_attribute('href')
        except NoSuchElementException:
            title = ''
            job_url = ''
        try:
            company = card.find_element(By.CSS_SELECTOR, '.artdeco-entity-lockup__subtitle').text
        except NoSuchElementException:
            company = ''
        try:
            location = card.find_element(By.CSS_SELECTOR, 'ul.job-card-container__metadata-wrapper li').text
        except NoSuchElementException:
            location = ''

        # 6) Open detail page in new tab to get more info
        description = ''
        benefits = ''
        company_about = ''
        if job_url:
            driver.execute_script("window.open(arguments[0]);", job_url)
            driver.switch_to.window(driver.window_handles[-1])

            # Wait for description to load
            try:
                desc_el = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'div.jobs-description__content'))
                )
                description = desc_el.text
            except TimeoutException:
                description = ''

            # Try benefits section
            try:
                ben_el = driver.find_element(By.CSS_SELECTOR, 'div.job-details-module')
                benefits = ben_el.text
            except NoSuchElementException:
                benefits = ''

            # Try company about section
            try:
                about_el = driver.find_element(By.CSS_SELECTOR, 'section.jobs-company')
                company_about = about_el.text
            except NoSuchElementException:
                company_about = ''

            # Close detail tab and switch back
            driver.close()
            driver.switch_to.window(driver.window_handles[0])

        # Append job data
        jobs.append({
            'Job Title': title,
            'Company Name': company,
            'Location': location,
            'Job URL': job_url,
            'Description': description,
            'Benefits': benefits,
            'Company About': company_about
        })

        if verbose:
            print(jobs[-1])

    # 7) Clean up
    driver.quit()
    return pd.DataFrame(jobs)
