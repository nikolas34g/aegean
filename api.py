from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os, datetime, subprocess, pandas as pd, sys
from google import genai
from google.genai import types
from dotenv import load_dotenv
import asyncio
python_executable = sys.executable
app = FastAPI()
load_dotenv()
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
async def analyze_reviews(request: AnalysisRequest):
    url = request.url
    model = request.model.lower()

    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    dataset_name = f"google_maps_reviews_{timestamp}.csv"
    dataset_path = os.path.join("datasets", dataset_name)
    base_dir = os.path.dirname(os.path.abspath(__file__))

    # Scrape reviews
    scraper_script = os.path.join(base_dir, "scraping_code", "google_maps_scraping.py")
    subprocess.run([python_executable, scraper_script, url, dataset_path], check=True)

    # Run sentiment model
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

    if not os.path.exists(reviews_path):
        return {"error": "Analysis file not found"}

    df = pd.read_csv(reviews_path)
    reviews = df.to_dict(orient="records")

    # Generate summary using Gemini API

    gemini_key = os.getenv("GEMINI_API_KEY")
    client = genai.Client(api_key=gemini_key)
    # client = genai.Client(api_key="AIzaSyCWSvfk15LGLedXRpOV6UIg3OsmojIX_Ro")
    summary_text = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=f"""Analyze these reviews ({model} results): {reviews}
        Provide:
        1. A very short recommendation (1-2 sentences)
        2. Positives in bullet points
        3. Negatives in bullet points"""
    ).text

    return {
        "reviews": reviews,
        "summary": summary_text
    }

# ------------------ COMPARISON ------------------ #
@app.post("/compare")
async def compare_models(request: ComparisonRequest):
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
    # Sentiment counts per model
    sentiment_counts = {
        "gemini": merged_df['sentiment_gemini'].value_counts().to_dict(),
        "huggingface": merged_df['sentiment_hf'].value_counts().to_dict(),
    }

    # Star ratings distribution
    ratings_counts = merged_df['rating'].value_counts().sort_index().to_dict()

    # Generate summaries with Gemini API
    client = genai.Client(api_key="AIzaSyCWSvfk15LGLedXRpOV6UIg3OsmojIX_Ro")

    # Gemini model summary
    gemini_summary = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=f"""Analyze these reviews (Gemini results): {merged_df[['review','sentiment_gemini']].to_dict(orient='records')}
        Provide:
        1. A very short recommendation for this place (1-2 sentences)
        2. Positives in bullet points or separate lines
        3. Negatives in bullet points or separate lines"""
    ).text
    await asyncio.sleep(60)

    # HuggingFace model summary
    hf_summary = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=f"""Analyze these reviews (HuggingFace results): {merged_df[['review','sentiment_hf']].to_dict(orient='records')}
        Provide:
        1. A very short recommendation for this place (1-2 sentences)
        2. Positives in bullet points or separate lines
        3. Negatives in bullet points or separate lines"""
    ).text
    await asyncio.sleep(60)

    # Combined models summary
    combined_summary = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=f"""Compare these reviews from both models: {merged_df.to_dict(orient='records')}
        Provide:
        1. A very short overall recommendation for this place (max 2 lines)
        2. Positives in separate lines
        3. Negatives in separate lines
        4. Most important keywords or highlights for this place"""
    ).text
    # await asyncio.sleep(10)
    return {
        "comparisons": merged_df.to_dict(orient="records"),
        "summary": {
            "gemini": gemini_summary,
            "huggingface": hf_summary,
            "combined": combined_summary
        },
        "plots": {
            "sentiment_counts": sentiment_counts,
            "ratings_counts": ratings_counts
        }
    }
