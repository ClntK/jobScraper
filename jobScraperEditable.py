# jobScraper.py

"""
Created on Tue Apr 28 11:35:04 2020
Original Author: chrislovejoy

Modified on Fri Aug 12 13:40:00 2022
Modified By: Clint Kline

Modifications:
    - updated to automatically detect chromedriver.exe, and install/update if earlier than v104.0.5112.79.
    - made to work with .com rather than .co.uk
    - update to parse indeed.com's most recent US web layout
    - made list vars global to enable multi-page searches
    - additional comments
    - this is ongoing, plans exist for additional functionality and cleaning.

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

titles = []
companies = []
links = []
dates = []

def update_chromedriver():
    driver = webdriver.Chrome() 
    gdversion = driver.capabilities['chrome']['chromedriverVersion'].split(' ')[0]

    if gdversion != '104.0.5112.79':
        
        # get the latest chrome driver version number   
        print('Obtaining latest google chrome driver...')
        url = 'https://chromedriver.storage.googleapis.com/LATEST_RELEASE'
        response = requests.get(url)
        version_number = response.text

        # build the donwload url
        download_url = "https://chromedriver.storage.googleapis.com/" + version_number +"/chromedriver_win32.zip"

        # download the zip file using the url built above
        latest_driver_zip = wget.download(download_url,'chromedriver.zip')

        # extract the zip file
        with zipfile.ZipFile(latest_driver_zip, 'r') as zip_ref:
            zip_ref.extractall() # you can specify the destination folder path here
        # delete the zip file downloaded above
        os.remove(latest_driver_zip)
        
    else:
        print('chromedriver.exe is up to date.')
        
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

def find_jobs_from(website, job_title, location, desired_characs, filename="results.xls"):    
    
    if website == 'Indeed':
        location_of_driver = os.getcwd() # pull chromedriver.exe from cwd
        driver = initiate_driver(location_of_driver, browser='chrome')
        startVal = 00 # create a variable to represent the url page property
        jobs_list = [] # creat list to contain job details
        while startVal <= 20:  # set page number, 10 = page 2, 20 = page 3
            job_soup = load_indeed_jobs_div(job_title, location, startVal) # create var to hold the contents of each job card
            jobs_list, num_listings = extract_job_information_indeed(job_soup, desired_characs) # create job info and track the number of jobs retrieved
            startVal += 10 # increment the page by 1
            
    save_jobs_to_excel(jobs_list, filename)
 
    print('{} new job postings retrieved from {}. Stored in {}.'.format(num_listings, website, filename))
                                                                          
## ======================= GENERIC FUNCTIONS ======================= ##

def save_jobs_to_excel(jobs_list, filename):
    jobs = pd.DataFrame(jobs_list)
    jobs.to_excel(filename)

## ================== FUNCTIONS FOR INDEED.COM =================== ##

def load_indeed_jobs_div(job_title, location, startVal):
    # create a dictionary of properties to attach to the end of the base url
    getVars = {'q' : job_title, 'l' : location, 'fromage' : 'last', 'sort' : 'date', 'start' : startVal}
    # designate the base url
    url = ('http://www.indeed.com/jobs?' + urllib.parse.urlencode(getVars))
    # pull the desired page from the web to be scraped
    page = requests.get(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.36'})
    # use bs4 to parse page content
    soup = BeautifulSoup(page.content, "html.parser")
    # isolate the portion of the page inside of the 'jobsearch-ResultsList' class
    job_soup = soup.find(class_="jobsearch-ResultsList")
    return job_soup

def extract_job_information_indeed(job_soup, desired_characs):
    # find all instances of 'slider_container classes inside the job_soup variable contents
    job_elems = job_soup.find_all('div', class_='slider_container')
    # create a var to keep track of each seperate list
    cols = []
    # create var to contain the contents of each of those lists
    extracted_info = []
    
    
    if 'titles' in desired_characs:
        cols.append('titles')
        for job_elem in job_elems:
            titles.append(extract_job_title_indeed(job_elem))
        extracted_info.append(titles)                    
    
    if 'companies' in desired_characs:
        cols.append('companies')
        for job_elem in job_elems:
            companies.append(extract_company_indeed(job_elem))
        extracted_info.append(companies)
    
    if 'links' in desired_characs:
        cols.append('links')
        for job_elem in job_elems:
            links.append(extract_link_indeed(job_elem))
        extracted_info.append(links)
    
    if 'date_listed' in desired_characs:
        cols.append('date_listed')
        for job_elem in job_elems:
            dates.append(extract_date_indeed(job_elem))
        extracted_info.append(dates)
    
    jobs_list_add = {}
    
    for j in range(len(cols)):
        jobs_list_add[cols[j]] = extracted_info[j]
    
    num_listings = len(extracted_info[0])
    
    return jobs_list_add, num_listings

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


# search_term = "data"
search_term = "driver"
# search_term = "computer"
# search_term = "website"
# search_term = "IT"
# search_term = ""

desired_characs = ['titles', 'companies', 'links', 'date_listed']
# Extracting jobs from Indeed.com
update_chromedriver()
find_jobs_from('Indeed', search_term, 'clarion', desired_characs)
