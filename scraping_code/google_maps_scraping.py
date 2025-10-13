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

# Download NLTK resources
nltk.download('punkt')
nltk.download('stopwords')

stop_words = set(stopwords.words('english'))  # Change to Greek stopwords if needed

# Function to clean and preprocess review text
def clean_text(text):
    text = text.replace("(Translated by Google)", "").replace("(Original)", "")
    text = re.sub(r'\s+', ' ', text).strip().lower()
    text = re.sub(r'[^\w\s]', '', text)
    # Tokenization
    words = word_tokenize(text)
    # Remove stopwords
    words = [w for w in words if w not in stop_words]
    return ' '.join(words)

# Generate a unique filename with timestamp
timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
filename = f'../datasets/google_maps_reviews_{timestamp}.csv'
url = 'https://www.google.com/maps/place/%CE%91%CE%BB%CE%B9%CE%B5%CF%85%CF%84%CE%B9%CE%BA%CE%AE+%CE%A0%CF%81%CE%BF%CE%B2%CE%BB%CE%AE%CF%84%CE%B1+%CE%91%CF%81%CE%B5%CF%84%CF%83%CE%BF%CF%8D/@40.5732093,22.9518629,16.25z/data=!4m6!3m5!1s0x14a83f649254da0f:0xb8b5825505714fc8!8m2!3d40.572209!4d22.9482184!16s%2Fg%2F11h1kx_z33?authuser=0&hl=en&entry=ttu&g_ep=EgoyMDI1MDkxNy4wIKXMDSoASAFQAw%3D%3D'

# Chrome options
options = uc.ChromeOptions()
options.add_argument('--disable-blink-features=AutomationControlled')
options.add_argument('--start-maximized')

driver = uc.Chrome(options=options)
driver.get(url)

# Accept cookies
try:
    WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, "//button[contains(.,'Accept all') or contains(.,'Αποδοχή όλων')]"))
    ).click()
    time.sleep(2)
except:
    print("Δεν βρέθηκε cookie popup")
    pass

# Click Reviews tab
try:
    reviews_tab = WebDriverWait(driver, 15).until(
        EC.element_to_be_clickable((By.XPATH, "//button[contains(@aria-label, 'Reviews') or contains(@aria-label, 'Κριτικές')]"))
    )
    reviews_tab.click()
    time.sleep(3)
except Exception as e:
    print(f"Δεν μπορέσαμε να βρούμε το Reviews tab: {e}")
    driver.quit()
    exit()

# Wait for reviews to load
try:
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'jftiEf')]"))
    )
except:
    print("Δεν βρέθηκαν reviews")
    driver.quit()
    exit()

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
        print(f"Σφάλμα κατά την επεξεργασία review: {e}")
        continue

# Save CSV
df.to_csv(filename, index=False, encoding='utf-8-sig')
driver.quit()

print(f"Συνολικά reviews: {len(df)}")
print(f"Τα reviews αποθηκεύτηκαν στο {filename}")
