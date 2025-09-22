import os
import pandas as pd
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch

# Specify the CSV file to process
csv_file = os.path.join("datasets", "google_maps_reviews_2025-09-01_15-34-22.csv")

if not os.path.exists(csv_file):
    print(f"File not found: {csv_file}")
    exit()

# Read CSV and remove duplicates
df = pd.read_csv(csv_file)
df = df.drop_duplicates(subset=['review', 'rating'])

# Load the multilingual sentiment model
model_name = "nlptown/bert-base-multilingual-uncased-sentiment"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSequenceClassification.from_pretrained(model_name)

results = []

for idx, row in df.iterrows():
    review_text = str(row['review'])
    rating = row['rating']
    
    # Tokenize input
    inputs = tokenizer(review_text, return_tensors="pt", truncation=True)
    
    # Get model predictions
    with torch.no_grad():
        outputs = model(**inputs)
        probs = torch.nn.functional.softmax(outputs.logits, dim=-1)
        star_rating = torch.argmax(probs, dim=-1).item() + 1  # 1-5 stars
    
    # Map star rating to sentiment
    if star_rating >= 4:
        sentiment = "Positive"
    elif star_rating == 3:
        sentiment = "Neutral"
    else:
        sentiment = "Negative"
    
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
output_folder = "reviews"
os.makedirs(output_folder, exist_ok=True)
output_file = os.path.join(output_folder, f"sentiment_hf_multilingual{os.path.basename(csv_file)}")
results_df.to_csv(output_file, index=False)
print(f"Sentiment analysis results saved to: {output_file}")
