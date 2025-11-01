import sys
from selenium import webdriver
from selenium.webdriver.common.by import By
import re
import pandas as pd
import time
import undetected_chromedriver as uc
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import datetime
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
import os

# Get URL from command line
# Get URL and output path from command line
if len(sys.argv) < 3:
    print("Usage: python google_maps_scraping.py <URL> <OUTPUT_CSV_PATH>")
    sys.exit(1)

url = sys.argv[1]
output_path = sys.argv[2]



stop_words = set(stopwords.words('english'))  # Change to Greek stopwords if needed

def clean_text(text):
    text = text.replace("(Translated by Google)", "").replace("(Original)", "")
    text = re.sub(r'\s+', ' ', text).strip().lower()
    text = re.sub(r'[^\w\s]', '', text)
    words = word_tokenize(text)
    words = [w for w in words if w not in stop_words]
    return ' '.join(words)

# Generate a unique filename with timestamp
timestamp = datetime.datetime.now().strftime("%Y-%m-%d")
dataset_folder = os.path.join(os.path.dirname(__file__), "..", "datasets")
os.makedirs(dataset_folder, exist_ok=True)
# filename = os.path.join(dataset_folder, f'google_maps_reviews_{timestamp}.csv')

# Chrome options
options = uc.ChromeOptions()
options.add_argument('--disable-blink-features=AutomationControlled')
options.add_argument('--start-maximized')
options.add_argument('--headless')
options.add_argument('--disable-gpu')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--log-level=3')

driver = uc.Chrome(options=options)
driver.get(url)

# Accept cookies
try:
    WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, "//button[contains(.,'Accept all') or contains(.,'Αποδοχή όλων')]"))
    ).click()
    time.sleep(2)
except:
    print("No cookie popup found")

# Click Reviews tab
try:
    reviews_tab = WebDriverWait(driver, 15).until(
        EC.element_to_be_clickable((By.XPATH, "//button[contains(@aria-label, 'Reviews') or contains(@aria-label, 'Κριτικές')]"))
    )
    reviews_tab.click()
    time.sleep(3)
except Exception as e:
    print(f"Could not find Reviews tab: {e}")
    driver.quit()
    sys.exit(1)

# Wait for reviews to load
try:
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'jftiEf')]"))
    )
except:
    print("No reviews found")
    driver.quit()
    sys.exit(1)

# Scroll for more reviews
prev_count = 0
max_scrolls = 20
scroll_attempts = 0

while scroll_attempts < max_scrolls:
    current_reviews = driver.find_elements(By.XPATH, "//div[contains(@class, 'jftiEf')]")
    if len(current_reviews) == prev_count:
        scroll_attempts += 1
    else:
        scroll_attempts = 0
        prev_count = len(current_reviews)
    
    driver.execute_script("""
        var scrollContainer = document.querySelector('.m6QErb.DxyBCb.kA9KIf.dS8AEf');
        if (scrollContainer) { scrollContainer.scrollTop = scrollContainer.scrollHeight; }
    """)
    time.sleep(2)

# Collect data
df = pd.DataFrame(columns=['review', 'rating'])
reviews_elements = driver.find_elements(By.XPATH, "//div[contains(@class, 'jftiEf')]")

for review_element in reviews_elements:
    try:
        try:
            more_button = review_element.find_element(By.XPATH, ".//button[contains(., 'More') or contains(., 'Περισσότερα')]")
            more_button.click()
            time.sleep(0.5)
        except:
            pass
        
        try:
            review_text = review_element.find_element(By.XPATH, ".//span[@class='wiI7pd']").text
            review_text = clean_text(review_text)
        except:
            review_text = ""
        
        try:
            rating_element = review_element.find_element(By.XPATH, ".//span[contains(@class, 'kvMYJc')]")
            rating = rating_element.get_attribute("aria-label")
            rating_match = re.search(r'(\d+)', rating)
            rating = rating_match.group(1) if rating_match else ""
        except:
            rating = ""
        
        if review_text and rating:
            df.loc[len(df)] = [review_text, rating]
            
    except Exception as e:
        print(f"Error processing review: {e}")
        continue

# Save CSV
df.to_csv(output_path, index=False, encoding='utf-8-sig')
# df.to_csv(filename, index=False, encoding='utf-8-sig')
driver.quit()

print(f"Total reviews: {len(df)}")
print(f"Reviews saved to: {output_path}")


