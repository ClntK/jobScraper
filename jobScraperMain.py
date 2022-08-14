# jobscraperReal.py

"""
Created on Tue Apr 28 11:35:04 2020
@author: chrislovejoy
"""

"""Modified on Fri Aug 12 13:40:00 2022
Modified By: Clint Kline

Modifications:
- updated to automatically detect chromedriver.exe, and install/update if earlier than v104.0.5112.79.
- made to work with .com rather than .co.uk
- update to indeed.com's most recent US web layout

"""


import urllib
import requests
from bs4 import BeautifulSoup
import selenium
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
import pandas as pd
import os
import xlwt
import wget
import zipfile
from chromedriver_py import binary_path # this will get you the path variable

def update_chromedriver():
    driver = webdriver.Chrome() 
    gdversion = driver.capabilities['chrome']['chromedriverVersion'].split(' ')[0]

    if gdversion != '104.0.5112.79': # update with newest chromedrivers version number        
        print('Obtaining latest google chrome driver...')
        url = 'https://chromedriver.storage.googleapis.com/LATEST_RELEASE'
        response = requests.get(url)
        version_number = response.text

        # build the download url
        download_url = "https://chromedriver.storage.googleapis.com/" + version_number +"/chromedriver_win32.zip"

        # download the zip file using the url built above
        latest_driver_zip = wget.download(download_url,'chromedriver.zip')

        # extract the zip file
        with zipfile.ZipFile(latest_driver_zip, 'r') as zip_ref:
            zip_ref.extractall() # you can specify the destination folder path here
        # delete the zip file once its contents are extracted
        os.remove(latest_driver_zip)
        
    else:
        print('chromedriver.exe is up to date.')

def find_jobs_from(website, job_title, location, desired_characs, filename="results.xls"):    
    """
    This function extracts all the desired characteristics of all new job postings
    of the title and location specified and returns them in single file.
    The arguments it takes are:
        - Website: to specify which website to search (options: 'Indeed' or 'CWjobs')
        - Job_title
        - Location
        - Desired_characs: this is a list of the job characteristics of interest,
            from titles, companies, links and date_listed.
        - Filename: to specify the filename and format of the output.
            Default is .xls file called 'results.xls'
    """
    
    if website == 'Indeed':
        location_of_driver = os.getcwd()
        driver = initiate_driver(location_of_driver, browser='chrome')
        job_soup = load_indeed_jobs_div(job_title, location)
        jobs_list, num_listings = extract_job_information_indeed(job_soup, desired_characs)
    
    # if website == 'CWjobs':
    #     location_of_driver = os.getcwd()
    #     driver = initiate_driver(location_of_driver, browser='chrome')
    #     job_soup = make_job_search(job_title, location, driver)
    #     jobs_list, num_listings = extract_job_information_cwjobs(job_soup, desired_characs)
    
    save_jobs_to_excel(jobs_list, filename)
 
    print('{} new job postings retrieved from {}. Stored in {}.'.format(num_listings, website, filename))
                                                                          
# ======================= 
#    GENERIC FUNCTIONS 
# =======================

def save_jobs_to_excel(jobs_list, filename):
    jobs = pd.DataFrame(jobs_list)
    jobs.to_excel(filename)

# ==================================== 
#   FUNCTIONS FOR INDEED.COM 
# ====================================

def load_indeed_jobs_div(job_title, location):
    getVars = {'q' : job_title, 'l' : location, 'fromage' : 'last', 'sort' : 'date'}
    url = ('http://www.indeed.com/jobs?' + urllib.parse.urlencode(getVars))
    # print(url) # for debugging
    # Add user-agent header to url
    page = requests.get(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.36'})
    soup = BeautifulSoup(page.content, "html.parser")
    job_soup = soup.find(class_="jobsearch-ResultsList") # updated element class 
    return job_soup

def extract_job_information_indeed(job_soup, desired_characs):
    job_elems = job_soup.find_all('div', class_='slider_container') # updated element class
     
    cols = []
    extracted_info = []
    
    # ensure that table columns are only sent to excel doc if they are not empty
    if 'titles' in desired_characs:
        titles = []
        cols.append('titles')
        for job_elem in job_elems:
            titles.append(extract_job_title_indeed(job_elem))
        extracted_info.append(titles)                    
    
    if 'companies' in desired_characs:
        companies = []
        cols.append('companies')
        for job_elem in job_elems:
            companies.append(extract_company_indeed(job_elem))
        extracted_info.append(companies)
    
    if 'links' in desired_characs:
        links = []
        cols.append('links')
        for job_elem in job_elems:
            links.append(extract_link_indeed(job_elem))
        extracted_info.append(links)
    
    if 'date_listed' in desired_characs:
        dates = []
        cols.append('date_listed')
        for job_elem in job_elems:
            dates.append(extract_date_indeed(job_elem))
        extracted_info.append(dates)
    
    jobs_list = {}
    
    for j in range(len(cols)):
        jobs_list[cols[j]] = extracted_info[j]
    
    num_listings = len(extracted_info[0])
    
    return jobs_list, num_listings

def extract_job_title_indeed(job_elem):
    title_elem = job_elem.find('h2', class_='jobTitle')
    title = title_elem.text.strip()
    return title

def extract_company_indeed(job_elem):
    company_elem = job_elem.find('span', class_='companyName')
    company = company_elem.text.strip()
    return company

def extract_link_indeed(job_elem):
    link = job_elem.find('a')['href']
    link = 'www.indeed.com/' + link
    return link

def extract_date_indeed(job_elem):
    date_elem = job_elem.find('span', class_='date')
    date = date_elem.text.strip()
    return date


def initiate_driver(location_of_driver, browser):
    if browser == 'chrome':
        driver = webdriver.Chrome(executable_path=(location_of_driver + "/chromedriver"))
    elif browser == 'firefox':
        driver = webdriver.Firefox(executable_path=(location_of_driver + "/firefoxdriver"))
    elif browser == 'safari':
        driver = webdriver.Safari(executable_path=(location_of_driver + "/safaridriver"))
    elif browser == 'edge':
        driver = webdriver.Edge(executable_path=(location_of_driver + "/edgedriver"))
    return driver

## ================== FUNCTIONS FOR CWJOBS.CO.UK =================== ##

# def make_job_search(job_title, location, driver):
#     driver.get('https://www.cwjobs.co.uk/')
    
#     # Select the job box
#     job_title_box = driver.find_element_by_name('Keywords')

#     # Send job information
#     job_title_box.send_keys(job_title)

#     # Selection location box
#     location_box = driver.find_element_by_id('location')
    
#     # Send location information
#     location_box.send_keys(location)
    
#     # Find Search button
#     search_button = driver.find_element_by_id('search-button')
#     search_button.click()

#     driver.implicitly_wait(5)

#     page_source = driver.page_source
    
#     job_soup = BeautifulSoup(page_source, "html.parser")
    
#     return job_soup


# def extract_job_information_cwjobs(job_soup, desired_characs):
    
#     job_elems = job_soup.find_all('div', class_="job")
     
#     cols = []
#     extracted_info = []
    
#     if 'titles' in desired_characs:
#         titles = []
#         cols.append('titles')
#         for job_elem in job_elems:
#             titles.append(extract_job_title_cwjobs(job_elem))
#         extracted_info.append(titles) 
                           
    
#     if 'companies' in desired_characs:
#         companies = []
#         cols.append('companies')
#         for job_elem in job_elems:
#             companies.append(extract_company_cwjobs(job_elem))
#         extracted_info.append(companies)
    
#     if 'links' in desired_characs:
#         links = []
#         cols.append('links')
#         for job_elem in job_elems:
#             links.append(extract_link_cwjobs(job_elem))
#         extracted_info.append(links)
                
#     if 'date_listed' in desired_characs:
#         dates = []
#         cols.append('date_listed')
#         for job_elem in job_elems:
#             dates.append(extract_date_cwjobs(job_elem))
#         extracted_info.append(dates)    
    
#     jobs_list = {}
    
#     for j in range(len(cols)):
#         jobs_list[cols[j]] = extracted_info[j]
    
#     num_listings = len(extracted_info[0])
    
#     return jobs_list, num_listings


# def extract_job_title_cwjobs(job_elem):
#     title_elem = job_elem.find('h2')
#     title = title_elem.text.strip()
#     return title
 
# def extract_company_cwjobs(job_elem):
#     company_elem = job_elem.find('h3')
#     company = company_elem.text.strip()
#     return company

# def extract_link_cwjobs(job_elem):
#     link = job_elem.find('a')['href']
#     return link

# def extract_date_cwjobs(job_elem):
#     link_elem = job_elem.find('li', class_='date-posted')
#     link = link_elem.text.strip()
#     return link

# search_term = "data"
# search_term = "driver"
# search_term = "computer"
# search_term = "website"
search_term = "IT"
# search_term = "python"
# search_term = "remote"
# search_term = ""

desired_characs = ['titles', 'companies', 'links', 'date_listed']
# Extracting jobs from Indeed.com
update_chromedriver()
find_jobs_from('Indeed', search_term, 'clarion', desired_characs)
# Extracting jobs from CWjobs.co.uk (using Selenium)
# find_jobs_from('CWjobs', 'data', 'clarion', desired_characs)
