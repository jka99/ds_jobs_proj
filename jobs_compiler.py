# -*- coding: utf-8 -*-
"""
Created on Tue May 20 12:43:38 2025

@author: jeffe
"""

from glassdoor_scraper import get_jobs_glassdoor
from linkedin_scraper import get_jobs_linkedin
import pandas as pd

keyword = 'data scientist'

path = "C:/Users/jeffe/Documents/ds_jobs_proj/chromedriver.exe"

df = get_jobs_glassdoor(keyword, 1000, False, path, 1)
#df = get_jobs_linkedin(keyword, 10, False, path, 1)

# clean up pay
df.to_csv('jobs.csv')
#   remove est
#   col for min and max

# get link to job posting
# get date posted
