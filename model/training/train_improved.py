"""
Improved training pipeline for TF-IDF + Logistic Regression scam detector
"""
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
import joblib
import os
from collections import Counter
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import preprocessing
from preprocessing import clean_text, tokenize_for_tfidf


def load_training_data(data_path: str = 'datasets/scam_dataset.csv') -> pd.DataFrame:
    """Load or generate training data"""
    # Use absolute path from project root
    if not os.path.isabs(data_path):
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        data_path = os.path.join(project_root, data_path)

    if os.path.exists(data_path):
        df = pd.read_csv(data_path)
        print(f"✅ Loaded {len(df)} samples from {data_path}")
    else:
        # Generate sample training data
        print("⚠️ Training data not found, generating sample data...")

        scam_samples = [
            "Your account has been compromised share OTP immediately",
            "Congratulations you won a lottery claim your reward now",
            "Your PAN card will be blocked unless verified today",
            "This is bank security please confirm your CVV number",
            "IRS notice your account has been flagged for investigation",
            "Your social security number has been suspended call now",
            "Your bank account has been frozen due to suspicious activity",
            "Urgent your account will be blocked press 1 to verify",
            "You have a warrant for your arrest call immediately",
            "Tax refund pending verify your details to receive money",
            "Your computer has a virus call tech support now",
            "Package delivery failed pay customs fee now",
            "Your electricity will be disconnected pay bill now",
            "Congratulations you have been selected for prize money",
            "Your credit card has been used fraudulently verify now",
            "Legal action will be taken if you don't pay now",
            "Your account password has been compromised reset now",
            "Federal bank agent calling verify your account",
            "Win big money claim your lottery prize now",
            "Your mobile number wins lottery prize contact now",
            "URGENT your bank account blocked verify immediately",
            "Police department calling you have legal matter",
            "Income tax department refund due verify account",
            "Microsoft security alert your computer infected",
            "Amazon suspicious transaction in your account",
            "Flipkart KYC deadline update your documents now",
            "Aadhaar card blocked update verification now",
            "RBI notice your account will be suspended",
            "Pension account verification required immediately",
            "Government scheme selected you must verify now"
        ]

        legit_samples = [
            "Meeting scheduled tomorrow at 5 PM",
            "Your package has been delivered successfully",
            "Thank you for your payment",
            "Project review meeting is postponed",
            "Please find attached the requested document",
            "Your appointment is confirmed for next week",
            "Thank you for contacting customer support",
            "Your order has been shipped",
            "Please review the attached report",
            "The meeting has been rescheduled to Friday",
            "Your feedback has been recorded",
            "Your application is being processed",
            "Thank you for your patience",
            "The document is ready for your review",
            "Your request has been submitted",
            "Please call us during business hours",
            "Your account balance is available online",
            "Thank you for your recent purchase",
            "Your subscription has been renewed",
            "Your inquiry has been forwarded",
            "The team will get back to you soon",
            "Your order is being prepared",
            "Please verify your email address",
            "Your profile has been updated",
            "Your payment has been received",
            "The service is now available",
            "Your ticket has been created",
            "Please review and confirm",
            "Your request is important to us",
            "Thank you for choosing our service"
        ]

        # Create balanced dataset with more samples
        data = []
        for text in scam_samples:
            data.append({'text': text, 'label': 1})
        for text in legit_samples:
            data.append({'text': text, 'label': 0})

        df = pd.DataFrame(data)

        # Create directory if needed
        os.makedirs(os.path.dirname(data_path), exist_ok=True)
        df.to_csv(data_path, index=False)
        print(f"✅ Generated {len(df)} samples")

    return df


def preprocess_data(df: pd.DataFrame) -> pd.DataFrame:
    """Preprocess training data"""
    df = df.copy()

    # Clean text
    df['text_clean'] = df['text'].apply(clean_text)

    # Remove empty or very short texts
    df = df[df['text_clean'].str.len() > 3]

    # Show class distribution
    print(f"\n📊 Class distribution:")
    print(df['label'].value_counts().to_dict())

    return df


def create_vectorizer() -> TfidfVectorizer:
    """Create improved TF-IDF vectorizer"""
    vectorizer = TfidfVectorizer(
        # N-gram settings
        ngram_range=(1, 3),  # Include unigrams, bigrams, trigrams

        # Feature extraction
        max_features=5000,
        min_df=2,
        max_df=0.95,
        sublinear_tf=True,  # Apply sublinear tf scaling (log)

        # Token processing
        token_pattern=r'(?u)\b\w+\b',  # Include single char tokens
        strip_accents='unicode',

        # Normalization
        norm='l2',

        # Custom tokenizer
        tokenizer=tokenize_for_tfidf
    )
    return vectorizer


def train_model(df: pd.DataFrame, test_size: float = 0.2) -> tuple:
    """Train and evaluate the model"""

    X = df['text_clean'].values
    y = df['label'].values

    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=42, stratify=y
    )

    print(f"\n📦 Training set: {len(X_train)} samples")
    print(f"📦 Test set: {len(X_test)} samples")

    # Create and fit vectorizer
    vectorizer = create_vectorizer()
    X_train_tfidf = vectorizer.fit_transform(X_train)
    X_test_tfidf = vectorizer.transform(X_test)

    print(f"\n🔢 TF-IDF features: {X_train_tfidf.shape[1]}")

    # Train model with regularization
    model = LogisticRegression(
        C=1.0,  # Regularization strength
        class_weight='balanced',  # Handle class imbalance
        max_iter=1000,
        solver='lbfgs',
        random_state=42,
        n_jobs=-1
    )

    print("\n⚙️ Training Logistic Regression...")
    model.fit(X_train_tfidf, y_train)

    # Evaluate
    train_score = model.score(X_train_tfidf, y_train)
    test_score = model.score(X_test_tfidf, y_test)

    print(f"\n📈 Training accuracy: {train_score:.4f}")
    print(f"📈 Test accuracy: {test_score:.4f}")

    # Cross-validation (adjust folds for small datasets)
    n_splits = min(5, min(np.bincount(y_train)))
    if n_splits >= 2:
        cv_scores = cross_val_score(model, X_train_tfidf, y_train, cv=n_splits)
        print(f"📈 CV accuracy: {cv_scores.mean():.4f} (+/- {cv_scores.std()*2:.4f})")
    else:
        print("⚠️ Too few samples for cross-validation")

    # Detailed metrics
    y_pred = model.predict(X_test_tfidf)
    print("\n📊 Classification Report:")
    print(classification_report(y_test, y_pred, target_names=['Legitimate', 'Scam']))

    print("\n📊 Confusion Matrix:")
    cm = confusion_matrix(y_test, y_pred)
    print(f"  Legit  Scam")
    print(f"L {cm[0][0]:4d} {cm[0][1]:4d}")
    print(f"S {cm[1][0]:4d} {cm[1][1]:4d}")

    return model, vectorizer


def save_model(model, vectorizer, model_path: str = 'model/scam_model.pkl',
               vectorizer_path: str = 'model/vectorizer.pkl'):
    """Save model and vectorizer"""
    os.makedirs('model', exist_ok=True)

    joblib.dump(model, model_path)
    print(f"✅ Model saved to {model_path}")

    joblib.dump(vectorizer, vectorizer_path)
    print(f"✅ Vectorizer saved to {vectorizer_path}")


def print_top_features(model, vectorizer, n: int = 20):
    """Print top features for each class"""
    feature_names = vectorizer.get_feature_names_out()

    # Get coefficients
    coef = model.coef_[0]

    # Top scam indicators
    top_scam_idx = np.argsort(coef)[-n:][::-1]
    print("\n🚨 Top scam indicators:")
    for idx in top_scam_idx:
        print(f"  {feature_names[idx]}: {coef[idx]:.3f}")

    # Top legitimate indicators
    top_legit_idx = np.argsort(coef)[:n]
    print("\n✅ Top legitimate indicators:")
    for idx in top_legit_idx:
        print(f"  {feature_names[idx]}: {coef[idx]:.3f}")


def main():
    """Main training pipeline"""
    print("="*60)
    print("TRAINING IMPROVED SCAM DETECTION MODEL")
    print("="*60)

    # Load data
    df = load_training_data()

    # Preprocess
    df = preprocess_data(df)

    # Train
    model, vectorizer = train_model(df)

    # Save
    save_model(model, vectorizer)

    # Print top features
    print_top_features(model, vectorizer)

    print("\n" + "="*60)
    print("✅ TRAINING COMPLETE")
    print("="*60)


if __name__ == "__main__":
    main()