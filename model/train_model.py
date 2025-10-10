import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
import joblib

print("Loading dataset...")
df = pd.read_csv('model/training_data.csv')
print(f"Dataset loaded with {len(df)} rows")

vectorizer = TfidfVectorizer(stop_words='english')
X = vectorizer.fit_transform(df['text'])
y = df['label']

model = LogisticRegression()
model.fit(X, y)

print("✅ Model trained successfully!")
joblib.dump(model, 'model/scam_model.pkl')
joblib.dump(vectorizer, 'model/vectorizer.pkl')
print("✅ Model saved to model/scam_model.pkl")
