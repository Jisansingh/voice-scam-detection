# train_model.py
from datasets import load_dataset, Audio
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix
import pickle
from scam_detector import ScamDetector
import pandas as pd

def prepare_training_data(num_samples=1000):
    """Prepare training data from Common Voice dataset"""
    print("Loading Common Voice dataset...")
    
    # Load dataset with streaming
    cv_dataset = load_dataset(
        "mozilla-foundation/common_voice_12_0", 
        "en", 
        split="train",
        streaming=True
    )
    
    # Set audio sampling rate to 16kHz
    cv_dataset = cv_dataset.cast_column("audio", Audio(sampling_rate=16000))
    
    # Initialize detector for feature extraction
    detector = ScamDetector()
    
    # Prepare features and labels
    X = []
    y = []
    
    print(f"Processing {num_samples} samples...")
    
    for i, sample in enumerate(cv_dataset):
        if i >= num_samples:
            break
        
        # Extract audio features
        audio_array = sample["audio"]["array"]
        sampling_rate = sample["audio"]["sampling_rate"]
        
        audio_features = detector.extract_audio_features(audio_array, sampling_rate)
        
        # Check for scam keywords in transcription
        text = sample["sentence"]
        keyword_score, _ = detector.detect_scam_keywords(text)
        
        # Combine features
        combined_features = np.append(audio_features, keyword_score)
        
        # Label as scam if keywords detected (simulated labeling)
        label = 1 if keyword_score > 5 else 0
        
        X.append(combined_features)
        y.append(label)
        
        if (i + 1) % 100 == 0:
            print(f"Processed {i + 1} samples...")
    
    return np.array(X), np.array(y)

def load_custom_training_data():
    """Load training data from training_data.csv if available"""
    try:
        df = pd.read_csv('training_data.csv')
        
        # Separate features and labels
        y = df['is_scam'].values
        X = df.drop(['is_scam'], axis=1).values
        
        return X, y
    except FileNotFoundError:
        print("No training_data.csv found. Using Common Voice dataset.")
        return None, None

def train_scam_model():
    """Train the scam detection model"""
    
    # Try to load custom data first
    X_custom, y_custom = load_custom_training_data()
    
    if X_custom is not None:
        print("Using custom training data from training_data.csv")
        X, y = X_custom, y_custom
    else:
        # Use Common Voice dataset
        X, y = prepare_training_data(num_samples=2000)
    
    print(f"\nDataset info:")
    print(f"Total samples: {len(X)}")
    print(f"Scam samples: {np.sum(y == 1)}")
    print(f"Legitimate samples: {np.sum(y == 0)}")
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    print("\nTraining Random Forest model...")
    
    # Train lightweight model for mobile deployment
    model = RandomForestClassifier(
        n_estimators=50,  # Keep small for mobile
        max_depth=10,
        min_samples_split=5,
        random_state=42,
        n_jobs=-1
    )
    
    model.fit(X_train, y_train)
    
    # Evaluate
    train_score = model.score(X_train, y_train)
    test_score = model.score(X_test, y_test)
    
    print(f"\nTraining accuracy: {train_score:.4f}")
    print(f"Testing accuracy: {test_score:.4f}")
    
    # Predictions
    y_pred = model.predict(X_test)
    
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred, 
                                target_names=['Legitimate', 'Scam']))
    
    print("\nConfusion Matrix:")
    print(confusion_matrix(y_test, y_pred))
    
    # Save model
    with open('scam_model.pkl', 'wb') as f:
        pickle.dump(model, f)
    
    print("\nModel saved to scam_model.pkl")
    
    return model

if __name__ == "__main__":
    model = train_scam_model()
    