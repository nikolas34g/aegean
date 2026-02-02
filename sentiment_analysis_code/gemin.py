import os
import sys
import pandas as pd
from google import genai
from google.genai import types
from dotenv import load_dotenv
import time
BASE_DIR = os.path.dirname(os.path.abspath(__file__))   # sentiment_analysis_code
ROOT_DIR = os.path.dirname(BASE_DIR)                    # backend
ENV_PATH = os.path.join(ROOT_DIR, "environments", ".env")

load_dotenv(ENV_PATH)
gemini_key = os.getenv("GEMINI_API_KEY")

if len(sys.argv) < 2:
    print("Usage: python gemini.py <csv_file_path>")
    sys.exit(1)

csv_file = sys.argv[1]

if not os.path.exists(csv_file):
    print(f"❌ File not found: {csv_file}")
    sys.exit(1)

# ✅ Initialize Gemini client


# client = genai.Client(api_key="AIzaSyCWSvfk15LGLedXRpOV6UIg3OsmojIX_Ro")
client = genai.Client(
    api_key=gemini_key,
    http_options=types.HttpOptions(
        retry_options=types.HttpRetryOptions(
            attempts=5,          # Try 5 times before giving up
            initial_delay=2,     # Start with 2 seconds
            max_delay=30,        # Maximum wait of 30 seconds
            http_status_codes=[429] # Specifically retry on Rate Limits
        )
    )
)
# ✅ Read the CSV
df = pd.read_csv(csv_file)
df = df.drop_duplicates(subset=['review', 'rating'])

results = []

for idx, row in df.iterrows():
    review_text = row['review']
    rating = row['rating']

    prompt = f"Classify this review as Positive, Neutral, or Negative. ONLY return one word: '{review_text}'"

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                thinking_config=types.ThinkingConfig(thinking_budget=0)
            )
        )
        sentiment = response.text.strip()
    except Exception as e:
        sentiment = f"Error: {e}"

    results.append({
        "review": review_text,
        "rating": rating,
        "sentiment": sentiment
    })
time.sleep(5)
    # print(f"✅ Review {idx+1}: {sentiment}")

# ✅ Save results in the 'reviews' folder
output_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "reviews")
os.makedirs(output_folder, exist_ok=True)

output_name = f"sentiment_gemini_{os.path.basename(csv_file)}"
output_file = os.path.join(output_folder, output_name)

results_df = pd.DataFrame(results)
results_df.to_csv(output_file, index=False, encoding='utf-8-sig')

print(f"💾 Sentiment analysis results saved to: {output_file}")

