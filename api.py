from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os, datetime, subprocess, pandas as pd, sys
from google import genai
from google.genai import types

python_executable = sys.executable
app = FastAPI()

# Allow Angular frontend to access this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://160.40.51.142:47823"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------ MODELS ------------------ #
class AnalysisRequest(BaseModel):
    url: str
    model: str  # "gemini" or "multilingual"

class ComparisonRequest(BaseModel):
    url: str

# ------------------ SINGLE MODEL ------------------ #
@app.post("/analyze")
def analyze_reviews(request: AnalysisRequest):
    url = request.url
    model = request.model.lower()

    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    dataset_name = f"google_maps_reviews_{timestamp}.csv"
    dataset_path = os.path.join("datasets", dataset_name)
    base_dir = os.path.dirname(os.path.abspath(__file__))

    # Scrape reviews
    scraper_script = os.path.join(base_dir, "scraping_code", "google_maps_scraping.py")
    subprocess.run([python_executable, scraper_script, url, dataset_path], check=True)

    # Run single sentiment model
    if model == "gemini":
        script_path = os.path.join(base_dir, "sentiment_analysis_code", "gemin.py")
        subprocess.run([python_executable, script_path, dataset_path], check=True)
        reviews_path = os.path.join(base_dir, "reviews", f"sentiment_gemini_{dataset_name}")

    elif model == "multilingual":
        script_path = os.path.join(base_dir, "sentiment_analysis_code", "multilingual-uncased-sentiment.py")
        subprocess.run([python_executable, script_path, dataset_path], check=True)
        reviews_path = os.path.join(base_dir, "reviews", f"sentiment_hf_multilingual_{dataset_name}")
    else:
        return {"error": "Invalid model name"}

    if os.path.exists(reviews_path):
        df = pd.read_csv(reviews_path)
        return df.to_dict(orient="records")
    else:
        return {"error": "Analysis file not found"}

# ------------------ COMPARISON ------------------ #
@app.post("/compare")
def compare_models(request: ComparisonRequest):
    url = request.url
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    dataset_name = f"google_maps_reviews_{timestamp}.csv"
    dataset_path = os.path.join("datasets", dataset_name)
    base_dir = os.path.dirname(os.path.abspath(__file__))

    # Scrape reviews
    scraper_script = os.path.join(base_dir, "scraping_code", "google_maps_scraping.py")
    subprocess.run([python_executable, scraper_script, url, dataset_path], check=True)

    # Run both sentiment models sequentially
    gemini_script = os.path.join(base_dir, "sentiment_analysis_code", "gemin.py")
    hf_script = os.path.join(base_dir, "sentiment_analysis_code", "multilingual-uncased-sentiment.py")
    subprocess.run([python_executable, gemini_script, dataset_path], check=True)
    subprocess.run([python_executable, hf_script, dataset_path], check=True)

    # Load results
    gemini_path = os.path.join(base_dir, "reviews", f"sentiment_gemini_{dataset_name}")
    hf_path = os.path.join(base_dir, "reviews", f"sentiment_hf_multilingual_{dataset_name}")
    df_gemini = pd.read_csv(gemini_path)
    df_hf = pd.read_csv(hf_path)

    # Merge
    merged_df = df_gemini.merge(df_hf, on=["review", "rating"], suffixes=("_gemini", "_hf"))

    # Generate summaries with Gemini API
    client = genai.Client(api_key="AIzaSyCWSvfk15LGLedXRpOV6UIg3OsmojIX_Ro")
    gemini_summary = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=f"Summarize general sentiment trends for these reviews (Gemini results): {merged_df[['review','sentiment_gemini']].to_dict(orient='records')}"
    ).text

    hf_summary = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=f"Summarize general sentiment trends for these reviews (HuggingFace results): {merged_df[['review','sentiment_hf']].to_dict(orient='records')}"
    ).text

    combined_summary = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=f"Compare both models' opinions and produce an overall recommendation for this place based on agreement and polarity: {merged_df.to_dict(orient='records')}"
    ).text

    return {
        "comparisons": merged_df.to_dict(orient="records"),
        "summary": {
            "gemini": gemini_summary,
            "huggingface": hf_summary,
            "combined": combined_summary
        }
    }
