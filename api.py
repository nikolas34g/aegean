from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os, datetime, subprocess, pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import sys

python_executable = sys.executable 
app = FastAPI()

# Allow Angular frontend to access this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://160.40.51.142:47823"],  # Angular host
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class AnalysisRequest(BaseModel):
    url: str
    model: str  # "gemini" or "multilingual"

@app.post("/analyze")
def analyze_reviews(request: AnalysisRequest):
    url = request.url
    model = request.model.lower()

    # Create dataset filename with timestamp (not just date)
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    dataset_name = f"google_maps_reviews_{timestamp}.csv"
    dataset_path = os.path.join("datasets", dataset_name)

    base_dir = os.path.dirname(os.path.abspath(__file__))

    # ✅ Step 1: Run the scraping script — it will create the CSV file
    print("Scraping fresh reviews...")
    scraper_script = os.path.join(base_dir, "scraping_code", "google_maps_scraping.py")
    subprocess.run([python_executable, scraper_script, url, dataset_path])  # <-- pass dataset_path

    # ✅ Step 2: Run sentiment analysis on that same CSV
    print(f"Running {model} analysis...")
    if model == "gemini":
        script_path = os.path.join(base_dir, "sentiment_analysis_code", "gemin.py")
        subprocess.run([python_executable, script_path, dataset_path])  # <-- pass dataset_path
        reviews_path = os.path.join(base_dir, "reviews", f"sentiment_gemini_{dataset_name}")

    elif model == "multilingual":
        script_path = os.path.join(base_dir, "sentiment_analysis_code", "multilingual-uncased-sentiment.py")
        subprocess.run([python_executable, script_path, dataset_path])
        reviews_path = os.path.join("reviews", f"sentiment_multilingual_{dataset_name}")
    else:
        return {"error": "Invalid model name"}

    # ✅ Step 3: Return results
    if os.path.exists(reviews_path):
        df = pd.read_csv(reviews_path)
        return df.to_dict(orient="records")
    else:
        return {"error": f"Analysis file not found for model {model}"}







# from fastapi import FastAPI
# import pandas as pd
# from fastapi.middleware.cors import CORSMiddleware

# app = FastAPI()

# # Allow Angular frontend to access this API
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["http://160.40.51.142:47823"], 
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# # API endpoint to get hotel reviews
# @app.get("/reviews")
# def get_reviews():
#     df = pd.read_csv("reviews/sentiment_gemini_google_maps_reviews_2025-09-01_15-34-22.csv")
#     reviews = df.to_dict(orient="records")
#     return reviews
