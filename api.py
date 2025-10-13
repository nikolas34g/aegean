from fastapi import FastAPI
import pandas as pd
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Allow Angular frontend to access this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # replace * with your Angular URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API endpoint to get hotel reviews
@app.get("/reviews")
def get_reviews():
    df = pd.read_csv("reviews/sentiment_gemini_google_maps_reviews_2025-09-01_15-34-22.csv")
    reviews = df.to_dict(orient="records")
    return reviews
