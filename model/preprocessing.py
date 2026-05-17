"""
Improved preprocessing for voice scam detection
"""
import re
import string
from typing import List, Tuple
from model.preprocessing import *
# Common contractions expansion
CONTRACTIONS = {
    "ain't": "is not", "aren't": "are not", "can't": "cannot",
    "couldn't": "could not", "didn't": "did not", "doesn't": "does not",
    "don't": "do not", "hadn't": "had not", "hasn't": "has not",
    "haven't": "have not", "he'd": "he would", "he'll": "he will",
    "he's": "he is", "i'd": "i would", "i'll": "i will",
    "i'm": "i am", "i've": "i have", "isn't": "is not",
    "it's": "it is", "let's": "let us", "might've": "might have",
    "must've": "must have", "needn't": "need not", "shan't": "shall not",
    "she'd": "she would", "she'll": "she will", "she's": "she is",
    "should've": "should have", "that's": "that is", "there's": "there is",
    "they'd": "they would", "they'll": "they will", "they're": "they are",
    "they've": "they have", "wasn't": "was not", "we'd": "we would",
    "we'll": "we will", "we're": "we are", "we've": "we have",
    "weren't": "were not", "what's": "what is", "where's": "where is",
    "who'd": "who would", "who'll": "who will", "who's": "who is",
    "won't": "will not", "wouldn't": "would not", "you'd": "you would",
    "you'll": "you will", "you're": "you are", "you've": "you have"
}

# Normalize numbers in text (preserve for pattern detection but normalize format)
def normalize_numbers(text: str) -> str:
    text = re.sub(r'\d{10,}', 'LONG_NUMBER', text)
    text = re.sub(r'\d{4,}', 'NUMBER', text)
    return text

def expand_contractions(text: str) -> str:
    """Expand contractions for better keyword matching"""
    for contraction, expansion in CONTRACTIONS.items():
        text = re.sub(r'\b' + contraction + r'\b', expansion, text, flags=re.IGNORECASE)
    return text

def clean_text(text: str) -> str:
    """Comprehensive text cleaning"""
    if not text:
        return ""

    text = text.lower()

    # Expand contractions
    text = expand_contractions(text)

    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text)

    # Remove special characters but keep important punctuation
    text = re.sub(r'[^\w\s\'\-]', ' ', text)

    # Normalize numbers
    text = normalize_numbers(text)

    # Remove extra whitespace
    text = text.strip()

    return text

def extract_features_from_text(text: str) -> dict:
    """Extract structural features that help identify scams"""
    if not text:
        return {}

    text_lower = text.lower()

    features = {}

    # Sentence structure
    sentences = text.split('.')
    features['sentence_count'] = len([s for s in sentences if s.strip()])
    features['avg_sentence_length'] = len(text.split()) / max(features['sentence_count'], 1)

    # Question patterns (common in social engineering)
    features['question_count'] = text.count('?')
    features['exclamation_count'] = text.count('!')

    # Capitalization (shouting detection)
    words = text.split()
    if words:
        caps_words = [w for w in words if w.isupper() and len(w) > 1]
        features['caps_ratio'] = len(caps_words) / len(words)
        features['caps_count'] = len(caps_words)
    else:
        features['caps_ratio'] = 0
        features['caps_count'] = 0

    # Number patterns
    features['has_phone_pattern'] = 1 if re.search(r'(\d{3}[-.]?\d{3}[-.]?\d{4}|\d{10,})', text) else 0
    features['has_money_pattern'] = 1 if re.search(r'(\$|dollar|rupee|lakh|crore|thousand)', text_lower) else 0

    # Action words (urgency indicators)
    action_words = ['immediately', 'urgent', 'now', 'today', 'fast', 'hurry', 'act', 'quick']
    features['action_word_count'] = sum(1 for w in action_words if w in text_lower)

    # Authority impersonation patterns
    authority_terms = ['bank', 'police', 'irs', 'tax', 'government', 'official', 'authority', 'department']
    features['authority_mentions'] = sum(1 for t in authority_terms if t in text_lower)

    return features

def tokenize_for_tfidf(text: str) -> List[str]:
    """Custom tokenizer for TF-IDF"""
    # Clean
    text = clean_text(text)

    # Split into tokens
    tokens = text.split()

    # Remove very short tokens
    tokens = [t for t in tokens if len(t) > 1]

    return tokens

def extract_manipulation_tactics(text: str) -> Tuple[dict, List[str]]:
    """Detect specific manipulation tactics used in scams"""
    if not text:
        return {}, []

    text_lower = text.lower()

    tactics = {}
    detected_tactics = []

    # 1. Authority Impersonation
    authority_patterns = [
        (r'\b(federal|irs|tax|revenue)\b.*\b(agent|officer|department)\b', 'authority_irs'),
        (r'\b(bank|security|account)\s*department\b', 'authority_bank'),
        (r'\b(police|court|legal|warrant|arrest)\b.*\b(issue|action|notice)\b', 'authority_legal'),
        (r'\b(government|official|agency)\b.*\b(official|agent)\b', 'authority_govt'),
    ]
    for pattern, name in authority_patterns:
        if re.search(pattern, text_lower):
            tactics[name] = True
            detected_tactics.append(name)

    # 2. Fear Induction
    fear_patterns = [
        (r'\b(arrest|warrant|jail|police)\b', 'fear_arrest'),
        (r'\b(block|suspended|closed|terminated)\b.*\b(account|license|service)\b', 'fear_account'),
        (r'\b(legal|action|sue|prosecute)\b', 'fear_legal'),
        (r'\b(compromised|hacked|stolen|fraud)\b', 'fear_fraud'),
    ]
    for pattern, name in fear_patterns:
        if re.search(pattern, text_lower):
            tactics[name] = True
            detected_tactics.append(name)

    # 3. Urgency Creation
    urgency_patterns = [
        (r'\b(immediately|right now|within\s+\d+\s*(hour|day))\b', 'urgency_now'),
        (r'\b(limited\s+time|expires?|deadline|final\s+notice)\b', 'urgency_deadline'),
        (r'\b(last\s+chance|act\s+fast|don\'t\s+delay)\b', 'urgency_pressure'),
    ]
    for pattern, name in urgency_patterns:
        if re.search(pattern, text_lower):
            tactics[name] = True
            detected_tactics.append(name)

    # 4. Prize/Lure Scams
    lure_patterns = [
        (r'\b(won|winner|lottery|prize|reward|claim)\b', 'lure_prize'),
        (r'\b(free|gift|bonus|cash)\b.*\b(claim|get|receive)\b', 'lure_free'),
        (r'\b(Congratulations|congrats|selected)\b', 'lure_congrats'),
    ]
    for pattern, name in lure_patterns:
        if re.search(pattern, text_lower):
            tactics[name] = True
            detected_tactics.append(name)

    # 5. Information Extraction
    info_patterns = [
        (r'\b(confirm|verify|validate)\b.*\b(card|cvv|pin|password)\b', 'info_sensitive'),
        (r'\b(share|provide|give)\b.*\b(detail|information|number)\b', 'info_request'),
        (r'\b(otp|one.?time|verification\s*code)\b', 'info_otp'),
    ]
    for pattern, name in info_patterns:
        if re.search(pattern, text_lower):
            tactics[name] = True
            detected_tactics.append(name)

    # 6. Authority Claim Without Verification
    verification_patterns = [
        (r'\b(this\s+is|代表|from)\b.*\b(bank|irs|police|government)\b', 'claim_authority'),
        (r'\b(caller\s+id|phone\s+number)\b.*\b(official|verified)\b', 'claim_verified'),
    ]
    for pattern, name in verification_patterns:
        if re.search(pattern, text_lower):
            tactics[name] = True
            detected_tactics.append(name)

    return tactics, detected_tactics

if __name__ == "__main__":
    # Test preprocessing
    test_texts = [
        "Your account has been compromised share OTP immediately",
        "Congratulations you won a lottery claim your reward now",
        "This is bank security please confirm your CVV number",
        "Meeting scheduled tomorrow at 5 PM",
        "Your PAN card will be blocked unless verified today",
        "IRS Notice: Arrest warrant issued - call immediately"
    ]

    for text in test_texts:
        print(f"\nOriginal: {text}")
        print(f"Cleaned: {clean_text(text)}")
        tactics, detected = extract_manipulation_tactics(text)
        print(f"Tactics: {detected}")
        features = extract_features_from_text(text)
        print(f"Features: {features}")