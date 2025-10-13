import os
import pandas as pd
from google import genai
from google.genai import types

# Initialize the Gemini client with API key
client = genai.Client(api_key="AIzaSyCWSvfk15LGLedXRpOV6UIg3OsmojIX_Ro")

# Specify the CSV file to process
csv_file = os.path.join("..", "datasets", "google_maps_reviews_2025-09-01_15-24-04.csv")

if not os.path.exists(csv_file):
    print(f"File not found: {csv_file}")
    exit()

# Read CSV and remove duplicate reviews with same rating
df = pd.read_csv(csv_file)
df = df.drop_duplicates(subset=['review', 'rating'])

results = []

for idx, row in df.iterrows():
    review_text = row['review']
    rating = row['rating']
    
    # Create the prompt for sentiment classification
    prompt = f"Classify this review as Positive, Neutral, or Negative. ONLY return one word: '{review_text}'"
    
    try:
        # Use the client to generate content
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                thinking_config=types.ThinkingConfig(thinking_budget=0)  # Disable thinking
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
    
    print(f"Review {idx+1}: {review_text}")
    print(f"Rating: {rating}")
    print(f"Sentiment: {sentiment}")
    print("-" * 50)

# Save results to CSV
results_df = pd.DataFrame(results)
output_folder = os.path.join("..", "reviews")
os.makedirs(output_folder, exist_ok=True)
output_file = os.path.join(output_folder, f"sentiment_gemini_{os.path.basename(csv_file)}")
results_df.to_csv(output_file, index=False)
print(f"Sentiment analysis results saved to: {output_file}")
