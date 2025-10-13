from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
import re
import pandas as pd
import time
import undetected_chromedriver as uc
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
import datetime
# chrome_path = r"driver/chromedriver.exe"
# s = Service(chrome_path)
#Golden City Hotel

url = 'https://www.google.com/travel/search?qs=MihDaG9RbEtTRzhKbTRpX19KQVJvTkwyY3ZNVEYzWW1ONGJqbDVZeEFDOABIAA&ap=KigKEgmuuStSD0VEQBHa3zPuKgs3QBISCZ8IYd3TRkRAEdrfM5YVDzdAMAC6AQdyZXZpZXdz&ts=CAEaHgoAEhoSFAoHCOkPEAoYFBIHCOkPEAoYFRgBMgIIACoHCgU6A0VVUg'
driver = uc.Chrome()
driver.get(url)
action = ActionChains(driver)
#accept cookies popup
try:
    driver.find_element(By.XPATH, "//span[text() = 'Accept all']").click()
    time.sleep(2)
except:
    pass


#loading many reviews from the page by scrolling to the bottom until we cant scroll more

prev_height = -1
max_scrolls = 500
scroll_count = 0
body = driver.find_element(By.TAG_NAME, 'body')
while scroll_count < max_scrolls:
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    body.send_keys(Keys.PAGE_UP)
    time.sleep(2)  # give some time for new results to load
    new_height = driver.execute_script("return document.body.scrollHeight")
    if new_height == prev_height:
        break
    prev_height = new_height
    scroll_count += 1

driver.execute_script("window.scrollTo(0, 0)")


#gathering ratings and reviews
df = pd.DataFrame(columns=['review', 'rating'])
reviews = driver.find_elements(By.XPATH, "//div[@class = 'Svr5cf bKhjM']")
for review_wrapper in reviews:
    rating_element = review_wrapper.find_element(By.XPATH, ".//div[@class = 'GDWaad']")
    driver.execute_script("arguments[0].scrollIntoView({ block: 'center' });", rating_element)
    driver.execute_script("window.scrollBy(0, 150)")
    #time.sleep(0.5)
    try:
        review_wrapper.find_element(By.XPATH, ".//span[text() = 'Read more']").click()
        time.sleep(0.5)
        review = review_wrapper.find_elements(By.XPATH, ".//div[@class = 'K7oBsc']//span")[2]
    except:
        review = review_wrapper.find_element(By.XPATH, ".//div[@class = 'K7oBsc']")
    review_text = review.text.replace("(Translated by Google)", "").split("(Original)")[0]
    review_text = review_text.replace("\n", "").lower()
    review_text = re.sub(r'[^\w\s]', '', review_text)
    review_text = re.sub(r'\d+', '', review_text)
    rating = rating_element.text
    if len(review_text):
        df.loc[len(df)] = [review_text, rating]

#saving dataframe as csv

timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
filename = f'../datasets/hotel_Scrapping_reviews_{timestamp}.csv'

df.to_csv(filename, index=False, encoding='utf-8-sig')
driver.quit()