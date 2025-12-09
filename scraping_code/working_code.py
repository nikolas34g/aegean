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
import random
import traceback

# =================== CONFIG ===================
mode = "random10"  # "all" or "random10"
max_reviews_to_scrape = 15  # Only used if mode="random10"
# ============================================

# Get URL and output path from command line
if len(sys.argv) < 3:
    print("Usage: python google_maps_scraping.py <URL> <OUTPUT_CSV_PATH>")
    sys.exit(1)

url = sys.argv[1]
output_path = sys.argv[2]

stop_words = set(stopwords.words('english'))

def clean_text(text):
    text = text.replace("(Translated by Google)", "").replace("(Original)", "")
    text = re.sub(r'\s+', ' ', text).strip().lower()
    text = re.sub(r'[^\w\s]', '', text)
    words = word_tokenize(text)
    # words = [w for w in words if w not in stop_words]
    return ' '.join(words)

# Chrome options
options = uc.ChromeOptions()
options.add_argument('--disable-blink-features=AutomationControlled')
options.add_argument('--start-maximized')
# Comment out headless to see browser during debugging
# options.add_argument('--headless')
options.add_argument('--disable-gpu')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--log-level=3')

driver = uc.Chrome(options=options)

try:
    print("[DEBUG] Opening URL...")
    driver.get(url)
    time.sleep(3)
    driver.save_screenshot("debug_initial_page.png")

    # Accept cookies
    try:
        cookie_btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(.,'Accept all') or contains(.,'Αποδοχή όλων')]"))
        )
        cookie_btn.click()
        print("[DEBUG] Clicked cookie popup")
        time.sleep(2)
    except Exception as e:
        print("[DEBUG] No cookie popup found:", e)

    # DEBUG: Print all button aria-labels
    print("[DEBUG] Listing all buttons:")
    buttons = driver.find_elements(By.TAG_NAME, "button")
    for idx, b in enumerate(buttons):
        label = b.get_attribute("aria-label")
        text = b.text
        print(f"[{idx}] aria-label: {label} | text: {text}")

    # Click Reviews tab
    try:
        # Try dynamic approach
        reviews_tab = None
        possible_xpaths = [
            "//button[contains(@aria-label, 'Reviews') or contains(@aria-label, 'Κριτικές')]",
            "//*[contains(text(), 'Reviews') or contains(text(), 'Κριτικές')]"
        ]
        for xpath in possible_xpaths:
            try:
                reviews_tab = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, xpath))
                )
                if reviews_tab:
                    reviews_tab.click()
                    print(f"[DEBUG] Clicked Reviews tab using XPath: {xpath}")
                    break
            except:
                continue

        if not reviews_tab:
            print("[ERROR] Could not find Reviews tab using any XPath")
            driver.save_screenshot("debug_no_reviews_tab.png")
            print(driver.page_source[:1000])  # First 1000 chars of page HTML
            driver.quit()
            sys.exit(1)

        time.sleep(3)
    except Exception as e:
        print("[ERROR] Could not find Reviews tab:", e)
        traceback.print_exc()
        driver.save_screenshot("debug_reviews_tab_fail.png")
        driver.quit()
        sys.exit(1)

    # Wait for reviews to load
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'jftiEf')]"))
        )
        print("[DEBUG] Reviews loaded")
        driver.save_screenshot("debug_reviews_loaded.png")
    except Exception as e:
        print("[ERROR] No reviews found:", e)
        traceback.print_exc()
        driver.save_screenshot("debug_no_reviews.png")
        driver.quit()
        sys.exit(1)

    # Scroll for more reviews
    prev_count = 0
    max_scrolls = 20
    scroll_attempts = 0
    while scroll_attempts < max_scrolls:
        current_reviews = driver.find_elements(By.XPATH, "//div[contains(@class, 'jftiEf')]")
        print(f"[DEBUG] Current reviews count: {len(current_reviews)}")
        if len(current_reviews) == prev_count:
            scroll_attempts += 1
        else:
            scroll_attempts = 0
            prev_count = len(current_reviews)

        if mode == "random10" and len(current_reviews) >= max_reviews_to_scrape:
            break

        driver.execute_script("""
            var scrollContainer = document.querySelector('.m6QErb.DxyBCb.kA9KIf.dS8AEf');
            if (scrollContainer) { scrollContainer.scrollTop = scrollContainer.scrollHeight; }
        """)
        time.sleep(2)

    # Collect data
    df = pd.DataFrame(columns=['review', 'rating'])
    df_raw = pd.DataFrame(columns=['review', 'rating'])

    reviews_elements = driver.find_elements(By.XPATH, "//div[contains(@class, 'jftiEf')]")
    print(f"[DEBUG] Total reviews to process: {len(reviews_elements)}")

    for i, review_element in enumerate(reviews_elements):
        if mode == "random10" and i >= max_reviews_to_scrape:
            break
        try:
            # Expand review if "More" button exists
            try:
                more_button = review_element.find_element(By.XPATH, ".//button[contains(., 'More') or contains(., 'Περισσότερα')]")
                more_button.click()
                print(f"[DEBUG] Clicked 'More' for review #{i}")
                time.sleep(0.5)
            except:
                pass

            review_text_raw = ""
            review_text = ""
            rating = ""

            try:
                review_text_raw = review_element.find_element(By.XPATH, ".//span[@class='wiI7pd']").text
                review_text = clean_text(review_text_raw)
            except:
                print(f"[DEBUG] Could not find review text for review #{i}")

            try:
                rating_element = review_element.find_element(By.XPATH, ".//span[contains(@class, 'kvMYJc')]")
                rating_val = rating_element.get_attribute("aria-label")
                rating_match = re.search(r'(\d+)', rating_val)
                rating = rating_match.group(1) if rating_match else ""
            except:
                print(f"[DEBUG] Could not find rating for review #{i}")

            if review_text and rating:
                df.loc[len(df)] = [review_text, rating]
            if review_text_raw and rating:
                review_text_raw_single_line = review_text_raw.replace('\n', ' ').replace('\r', ' ').strip()
                df_raw.loc[len(df_raw)] = [review_text_raw_single_line, rating]

        except Exception as e:
            print(f"[ERROR] Processing review #{i} failed:", e)
            traceback.print_exc()
            continue

    # Random sampling if needed
    if mode == "random10" and len(df) > 10:
        df = df.sample(n=10, random_state=42).reset_index(drop=True)
    if mode == "random10" and len(df_raw) > 10:
        df_raw = df_raw.sample(n=10, random_state=42).reset_index(drop=True)

    # Save CSVs
    df.to_csv(output_path, index=False, encoding='utf-8-sig')
    raw_output_path = output_path.replace('.csv', '_raw.csv')
    df_raw.to_csv(raw_output_path, index=False, encoding='utf-8-sig')

    print(f"Total reviews collected: {len(df)}")
    print(f"✅ Cleaned reviews saved to: {output_path}")
    print(f"✅ Raw reviews saved to: {raw_output_path}")

except Exception as e:
    print("[ERROR] Unexpected error:", e)
    traceback.print_exc()

finally:
    try:
        driver.quit()
    except Exception as e:
        print("[DEBUG] Driver quit failed:", e)
