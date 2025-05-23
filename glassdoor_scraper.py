# -*- coding: utf-8 -*-
"""
Created on Tue May 20 12:35:36 2025

@author: jeffe
"""
# https://github.com/arapfaik/scraping-glassdoor-selenium
# code derrived from above

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.common.exceptions import (
    NoSuchElementException,
    TimeoutException,
    ElementClickInterceptedException,
    StaleElementReferenceException,
)
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import pandas as pd
from urllib.parse import quote_plus


def get_jobs_glassdoor(keyword: str,
             num_jobs: int,
             verbose: bool,
             driver_path: str,
             sleep_time: float) -> pd.DataFrame:
    """
    Gathers summary info for up to `num_jobs` jobs from Glassdoor by
    clicking the "Show more jobs" button until enough cards load,
    and returns them as a pandas DataFrame.

    Only the keyword filter is applied; all other URL parameters (location,
    salary, rating, etc.) have been removed to broaden the search.
    """
    # Initialize Chrome driver
    options = webdriver.ChromeOptions()
    # options.add_argument("headless")  # uncomment to run without UI
    service = Service(driver_path)
    driver = webdriver.Chrome(service=service, options=options)
    driver.set_window_size(1120, 1000)

    # Build a clean URL using only the keyword
    encoded_keyword = quote_plus(keyword)
    url = f"https://www.glassdoor.com/Job/jobs.htm?sc.keyword={encoded_keyword}"
    if verbose:
        print("Navigating to:", url)
    driver.get(url)

    # Wait for initial job cards to load
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'li[data-test="jobListing"]'))
        )
    except TimeoutException:
        if verbose:
            print("Timed out waiting for job listings to load.")
        driver.quit()
        return pd.DataFrame()

    # Keep clicking "Show more jobs" until we have enough cards
    cards = driver.find_elements(By.CSS_SELECTOR, 'li[data-test="jobListing"]')
    while len(cards) < num_jobs:
        try:
            load_more_btn = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[data-test="load-more"]'))
            )
            driver.execute_script(
                "arguments[0].scrollIntoView({block:'center'});", load_more_btn
            )
            driver.execute_script("arguments[0].click();", load_more_btn)
            if verbose:
                print(f"Clicked 'Show more jobs'; currently {len(cards)} cards loaded.")
            time.sleep(sleep_time)
        except (TimeoutException, NoSuchElementException, ElementClickInterceptedException, StaleElementReferenceException):
            if verbose:
                print("No more 'Show more jobs' button or can't click; stopping load loop.")
            break
        cards = driver.find_elements(By.CSS_SELECTOR, 'li[data-test="jobListing"]')

    # Extract summary from each card up to num_jobs
    jobs = []
    cards = driver.find_elements(By.CSS_SELECTOR, 'li[data-test="jobListing"]')
    for card in cards[:num_jobs]:
        try:
            title = card.find_element(By.CSS_SELECTOR, 'a[data-test="job-title"]').text
        except NoSuchElementException:
            title = ""
        try:
            company = card.find_element(
                By.CSS_SELECTOR,
                'span[class*="EmployerProfile_compactEmployerName"]'
            ).text
        except NoSuchElementException:
            company = ""
        try:
            location = card.find_element(By.CSS_SELECTOR, 'div[data-test="emp-location"]').text
        except NoSuchElementException:
            location = ""
        try:
            salary = card.find_element(By.CSS_SELECTOR, 'div[data-test="detailSalary"]').text
        except NoSuchElementException:
            salary = -1
        try:
            description = card.find_element(By.CSS_SELECTOR, 'div[data-test="descSnippet"]').text
        except NoSuchElementException:
            description = ""
        try:
            rating = card.find_element(By.CSS_SELECTOR, 'span.rating-single-star_RatingText__XENmU').text
        except NoSuchElementException:
            rating = -1

        jobs.append({
            "Job Title":       title,
            "Company Name":    company,
            "Location":        location,
            "Salary Estimate": salary,
            "Rating":          rating,
            "Description":     description
        })
        if verbose:
            print(jobs[-1])

    driver.quit()
    return pd.DataFrame(jobs)
