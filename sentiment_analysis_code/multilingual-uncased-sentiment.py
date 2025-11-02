import os
import pandas as pd
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
import sys

if len(sys.argv) < 2:
    print("Usage: python sentiment_hf.py <csv_file_path>")
    sys.exit(1)

csv_file = sys.argv[1]

if not os.path.exists(csv_file):
    print(f"❌ File not found: {csv_file}")
    sys.exit(1)

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
    
    # print(f"✅ Review {idx+1}: {sentiment}")

# ✅ Save results in the 'reviews' folder (same as Gemini style)
output_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "reviews")
os.makedirs(output_folder, exist_ok=True)

output_name = f"sentiment_hf_multilingual_{os.path.basename(csv_file)}"
output_file = os.path.join(output_folder, output_name)

results_df = pd.DataFrame(results)
results_df.to_csv(output_file, index=False, encoding='utf-8-sig')

print(f"💾 Sentiment analysis results saved to: {output_file}")