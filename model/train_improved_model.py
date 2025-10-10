import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, accuracy_score, confusion_matrix
import joblib
import re
from collections import Counter

def create_improved_training_data():
    """Create improved training dataset with balanced scam and legitimate messages"""
    
    # Enhanced dataset with both English and Hindi/Hinglish examples
    training_data = [
        # Scam messages (Label: 1) - 40 examples
        ("Congratulations! You've won a prize of Rs.10,000. Share your card details to claim.", 1),
        ("Your account has been blocked. Share OTP to reactivate immediately.", 1),
        ("URGENT: Your card will be blocked. Call now and share CVV.", 1),
        ("Aapka account block hone wala hai, jaldi OTP share karo.", 1),
        ("Bank se call hai, security ke liye aapka card number aur CVV batayein.", 1),
        ("KYC expire ho raha hai, turant OTP share karein.", 1),
        ("Lottery jeete hain aap, card details share karein prize ke liye.", 1),
        ("Account hack ho gaya hai, PIN number confirm karein.", 1),
        ("Your computer has virus, share screen and bank details for fix.", 1),
        ("IRS is filing lawsuit, pay immediately through gift cards.", 1),
        ("Sir, your card blocked ho jayega, please share OTP.", 1),
        ("Cyber crime department se call hai, aapka account hack hua hai.", 1),
        ("Account me suspicious activity hai, card details confirm karein.", 1),
        ("Government tax department se call hai, urgent payment karein.", 1),
        ("Congratulations! Aap lottery ke winner hai, OTP share karein.", 1),
        ("Your card showing illegal transaction, share CVV to block.", 1),
        ("Bank security team calling, need your PIN for verification.", 1),
        ("Police case filed against your card, share details to resolve.", 1),
        ("Aapki KYC expire ho rahi hai, abhi update karein.", 1),
        ("Account suspicious activity detected, share OTP fast.", 1),
        ("URGENT! Click this link to verify your bank account now.", 1),
        ("You have won 50 lakh rupees lottery, send bank details.", 1),
        ("Your ATM card will expire today, share CVV to renew.", 1),
        ("Income tax refund pending, provide your account number.", 1),
        ("Call back urgently regarding fraudulent transaction on your card.", 1),
        ("Microsoft tech support calling, your computer has malware.", 1),
        ("Amazon customer service, need your password to fix account.", 1),
        ("WhatsApp verification failed, send OTP to reactivate.", 1),
        ("Social security office calling, your number will be suspended.", 1),
        ("PayPal security alert, confirm your credit card immediately.", 1),
        ("Facebook account hacked, provide password to secure.", 1),
        ("Netflix payment failed, update card details now.", 1),
        ("Google account suspended, verify with phone number.", 1),
        ("Covid vaccine certificate ready, pay Rs.500 fee.", 1),
        ("Aadhaar card blocked, update details immediately.", 1),
        ("Electricity bill overdue, pay now or connection cut.", 1),
        ("LPG subsidy pending, share bank account for transfer.", 1),
        ("Insurance claim approved, share account for payment.", 1),
        ("Credit score check free, provide PAN and Aadhaar number.", 1),
        ("Job offer confirmed, pay Rs.5000 registration fee.", 1),
        
        # Legitimate messages (Label: 0) - 40 examples
        ("Welcome to our bank. Download our app for easy banking.", 0),
        ("Your account statement for July is ready to view.", 0),
        ("Thank you for your recent transaction at our store.", 0),
        ("Your mobile recharge of Rs.499 was successful.", 0),
        ("Aapka bill payment safaltapurvak ho gaya hai.", 0),
        ("Bank ki nayi branch khul gayi hai aapke area mein.", 0),
        ("Your OTP is 123456. Never share OTP with anyone.", 0),
        ("Please complete your pending KYC at nearest branch.", 0),
        ("Download our secure banking app from official store.", 0),
        ("Meeting scheduled for tomorrow at 10 AM.", 0),
        ("Your account balance is Rs.5000. Download statement.", 0),
        ("New credit card features available. Visit branch.", 0),
        ("Thank you for using our ATM services.", 0),
        ("Your salary has been credited to your account.", 0),
        ("Bank holiday notification: Closed on Sunday.", 0),
        ("EMI payment successful for your loan account.", 0),
        ("Important: Keep your PIN private and secure.", 0),
        ("Visit our branch for account related queries.", 0),
        ("Your cheque book request is processed.", 0),
        ("Bank app maintenance scheduled for tonight.", 0),
        ("Transaction alert: Withdrawal of Rs.2000 from ATM.", 0),
        ("Your fixed deposit has matured. Visit branch.", 0),
        ("Monthly account statement sent to your email.", 0),
        ("New offers available on our credit cards.", 0),
        ("Thank you for choosing our banking services.", 0),
        ("Your insurance premium is due next week.", 0),
        ("Reminder: Doctor appointment scheduled for Friday.", 0),
        ("Your food order has been delivered successfully.", 0),
        ("Library book return reminder: Due in 3 days.", 0),
        ("Weather alert: Heavy rain expected tomorrow.", 0),
        ("Your gym membership expires next month.", 0),
        ("Flight booking confirmation for Delhi-Mumbai.", 0),
        ("Hotel reservation confirmed for your stay.", 0),
        ("Your movie tickets are ready for download.", 0),
        ("Electricity bill generated, due date 15th.", 0),
        ("Your internet plan will renew automatically.", 0),
        ("Train ticket booking successful, journey tomorrow.", 0),
        ("Your subscription to magazine renewed.", 0),
        ("School fee payment received, thank you.", 0),
        ("Your package has been shipped and tracking info sent.", 0)
    ]
    
    return training_data

def preprocess_text(text):
    """Enhanced text preprocessing"""
    # Convert to lowercase
    text = text.lower()
    
    # Remove special characters but keep essential punctuation
    text = re.sub(r'[^\w\s.,!?]', '', text)
    
    # Normalize common scam-related terms
    text = text.replace('kyc', 'know_your_customer')
    text = text.replace('cvv', 'card_verification_value')
    text = text.replace('otp', 'one_time_password')
    text = text.replace('pin', 'personal_identification_number')
    
    # Add space around numbers for better tokenization
    text = re.sub(r'(\d+)', r' \1 ', text)
    
    return text

def extract_custom_features(texts):
    """Extract domain-specific features"""
    features = []
    
    for text in texts:
        feature_vector = []
        text_lower = text.lower()
        
        # Urgency indicators (stronger weight)
        urgency_words = ['urgent', 'immediately', 'jaldi', 'turant', 'quick', 'fast', 'abhi', 'now', 'asap']
        urgency_count = sum(2 if word in text_lower else 0 for word in urgency_words)
        feature_vector.append(urgency_count)
        
        # Sensitive information requests (high importance)
        sensitive_info = ['card', 'cvv', 'pin', 'otp', 'password', 'security', 'account', 'number', 
                         'details', 'verify', 'confirm', 'share', 'provide', 'send']
        sensitive_count = sum(2 if word in text_lower else 0 for word in sensitive_info)
        feature_vector.append(sensitive_count)
        
        # Threat language (high importance)
        threat_words = ['block', 'hack', 'suspend', 'banned', 'legal', 'police', 'expire', 'illegal',
                       'suspended', 'terminated', 'frozen', 'locked', 'cut', 'disconnected']
        threat_count = sum(2 if word in text_lower else 0 for word in threat_words)
        feature_vector.append(threat_count)
        
        # Prize/lottery scam indicators
        prize_words = ['congratulations', 'winner', 'prize', 'lottery', 'win', 'jeet', 'won', 'lakh',
                      'crore', 'reward', 'gift', 'free', 'bonus']
        prize_count = sum(2 if word in text_lower else 0 for word in prize_words)
        feature_vector.append(prize_count)
        
        # Official authority claims
        authority_words = ['bank', 'government', 'official', 'department', 'cyber', 'tax', 'irs',
                          'microsoft', 'amazon', 'google', 'facebook', 'paypal', 'whatsapp']
        authority_count = sum(1 if word in text_lower else 0 for word in authority_words)
        feature_vector.append(authority_count)
        
        # Money/payment indicators
        money_words = ['rs', 'rupees', 'pay', 'payment', 'fee', 'money', 'cash', 'amount', 'refund']
        money_count = sum(1 if word in text_lower else 0 for word in money_words)
        feature_vector.append(money_count)
        
        # Contact/action requests
        contact_words = ['call', 'click', 'visit', 'download', 'install', 'register', 'login']
        contact_count = sum(1 if word in text_lower else 0 for word in contact_words)
        feature_vector.append(contact_count)
        
        features.append(feature_vector)
    
    return np.array(features)

def train_improved_model():
    print("🚀 Training Improved Scam Detection Model...")
    print("=" * 60)
    
    # Get training data
    training_data = create_improved_training_data()
    texts, labels = zip(*training_data)
    
    print(f"Dataset Info:")
    print(f"Total samples: {len(training_data)}")
    print(f"Scam samples: {sum(labels)}")
    print(f"Legitimate samples: {len(labels) - sum(labels)}")
    
    # Preprocess texts
    processed_texts = [preprocess_text(text) for text in texts]
    
    # Create TF-IDF features with enhanced parameters
    print("\n📊 Creating TF-IDF features...")
    tfidf = TfidfVectorizer(
        ngram_range=(1, 3),  # Include up to trigrams
        max_features=1000,
        min_df=1,  # Include words that appear at least once
        stop_words='english',
        lowercase=True
    )
    
    # Transform texts to TF-IDF features
    X_tfidf = tfidf.fit_transform(processed_texts)
    
    # Extract custom features
    print("🔧 Extracting custom features...")
    custom_features = extract_custom_features(texts)
    
    # Combine TF-IDF and custom features
    X = np.hstack((X_tfidf.toarray(), custom_features))
    y = np.array(labels)
    
    # Split data with stratification to maintain class balance
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.3, random_state=42, stratify=y
    )
    
    print(f"\nTraining set: {len(X_train)} samples")
    print(f"Test set: {len(X_test)} samples")
    
    # Create and train model with optimized parameters
    print("\n🤖 Training RandomForest model...")
    model = RandomForestClassifier(
        n_estimators=100,
        max_depth=15,
        min_samples_split=2,
        min_samples_leaf=1,
        class_weight='balanced',  # Handle class imbalance
        random_state=42,
        n_jobs=-1
    )
    
    # Train model
    model.fit(X_train, y_train)
    
    # Evaluate model
    train_predictions = model.predict(X_train)
    test_predictions = model.predict(X_test)
    
    train_accuracy = accuracy_score(y_train, train_predictions)
    test_accuracy = accuracy_score(y_test, test_predictions)
    
    print("\n" + "="*60)
    print("📈 MODEL EVALUATION RESULTS")
    print("="*60)
    print(f"Training Accuracy: {train_accuracy:.2%}")
    print(f"Test Accuracy: {test_accuracy:.2%}")
    
    print(f"\n📋 Detailed Classification Report:")
    print(classification_report(y_test, test_predictions, 
                              target_names=['Legitimate', 'Scam']))
    
    print(f"\n🔢 Confusion Matrix:")
    cm = confusion_matrix(y_test, test_predictions)
    print(f"True Negative: {cm[0,0]}, False Positive: {cm[0,1]}")
    print(f"False Negative: {cm[1,0]}, True Positive: {cm[1,1]}")
    
    # Feature importance
    print(f"\n🔍 Top 10 Most Important Features:")
    feature_names = list(tfidf.get_feature_names_out()) + [
        'urgency_count', 'sensitive_info_count', 'threat_count', 
        'prize_count', 'authority_count', 'money_count', 'contact_count'
    ]
    feature_importance = list(zip(feature_names, model.feature_importances_))
    feature_importance.sort(key=lambda x: x[1], reverse=True)
    
    for i, (feature, importance) in enumerate(feature_importance[:10]):
        print(f"{i+1}. {feature}: {importance:.4f}")
    
    # Save model and vectorizer
    print(f"\n💾 Saving model files...")
    joblib.dump(model, 'model/scam_model.pkl')
    joblib.dump(tfidf, 'model/vectorizer.pkl')
    
    print("✅ Model and vectorizer saved successfully!")
    print("📂 Files saved:")
    print("   - model/scam_model.pkl")
    print("   - model/vectorizer.pkl")
    print("="*60)
    
    return model, tfidf, test_accuracy

if __name__ == "__main__":
    model, vectorizer, accuracy = train_improved_model()
    
    if accuracy >= 0.85:
        print(f"🎉 SUCCESS! Model achieved {accuracy:.1%} accuracy - Ready for deployment!")
    else:
        print(f"⚠️ Model accuracy {accuracy:.1%} - Consider adding more training data.")