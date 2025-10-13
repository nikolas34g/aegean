import pandas as pd
from transformers import pipeline
import glob
import os

# Initialize sentiment analysis pipeline
sentiment_pipeline = pipeline(
    "sentiment-analysis",
    model="cardiffnlp/twitter-roberta-base-sentiment"
)


# csv_file = os.path.join("datasets", "google_maps_reviews_2025-09-01_15-34-22.csv")  
csv_file = os.path.join("..", "datasets", "google_maps_reviews_2025-09-01_15-34-22.csv")

# Check if the file exists
if not os.path.exists(csv_file):
    print(f"File not found: {csv_file}")
    exit()

print(f"Processing file: {csv_file}")
df = pd.read_csv(csv_file)
df = df.drop_duplicates(subset=['review', 'rating'])  # remove duplicates

results = []

for idx, row in df.iterrows():
    review_text = row['review']
    rating = row['rating']
    result = sentiment_pipeline(review_text)[0]
    
    results.append({
        "review": review_text,
        "rating": rating,
        "sentiment": result['label'],
        "score": result['score']
    })
    
    # Optional: print to console
    # print(f"Review {idx+1}: {review_text}")
    # print(f"Rating: {rating}")
    # print(f"Sentiment: {result['label']}, Score: {result['score']:.4f}")
    # print("-" * 50)

# Convert results to a DataFrame
results_df = pd.DataFrame(results)

# Ensure the reviews folder exists
output_folder = os.path.join("..", "reviews")
os.makedirs(output_folder, exist_ok=True)

# Save results to a CSV file
output_file = os.path.join(output_folder, f"sentiment_Cardiff_NLP{os.path.basename(csv_file)}")
results_df.to_csv(output_file, index=False)

print(f"Sentiment analysis results saved to: {output_file}")

