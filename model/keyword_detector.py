"""
Enhanced keyword detection and scam category classification
"""
from typing import List, Dict, Tuple
import re

# Scam categories with associated keywords
SCAM_CATEGORIES = {
    'bank_fraud': {
        'keywords': ['bank', 'account', 'blocked', 'frozen', 'suspended', 'kyc', ' debit', 'credit card', 'atm', 'sbi', 'hdfc', 'icici', 'axis', 'yes bank', 'pnb'],
        'weight': 5,
        'patterns': [
            r'account\s+(blocked|frozen|suspended|compromised)',
            r'bank\s+(security|department)',
            r'verify\s+(account|card|details)',
            r'update\s+(kyc|account|details)',
            r'(sbi|hdfc|icici|axis)\s+(bank|calling)',
        ]
    },
    'upi_scam': {
        'keywords': ['upi', 'phonepe', 'paytm', 'google pay', 'amazon pay', 'phone pay', 'wallet', 'bank account', 'up i'],
        'weight': 6,
        'patterns': [
            r'upi\s+(account|verification)',
            r'(phonepe|paytm|google pay)\s+(account|kyc)',
            r'wallet\s+(blocked|suspended)',
            r'(upi|wallet)\s+payment\s+failed',
        ]
    },
    'kyc_scam': {
        'keywords': ['kyc', 'aadhaar', 'pan', 'kyc update', 'kyc expired', 'kyc pending', 'aadhar', 'pancard'],
        'weight': 6,
        'patterns': [
            r'kyc\s+(expired|pending|update)',
            r'aadhaar\s+(kyc|link)',
            r'pan\s+kyc',
            r'documents\s+expired',
        ]
    },
    'otp_scam': {
        'keywords': ['otp', 'one time password', 'verification code', '6 digit', 'otp sent', 'share otp', 'enter otp'],
        'weight': 7,
        'patterns': [
            r'share\s+otp',
            r'enter\s+otp',
            r'otp\s+(sent|expire)',
            r'verification\s+(code|number)',
        ]
    },
    'refund_scam': {
        'keywords': ['refund', 'money back', 'claim refund', 'pending refund', 'eligible refund', 'refund claim'],
        'weight': 5,
        'patterns': [
            r'pending\s+refund',
            r'claim\s+(your\s+)?refund',
            r'(money|refund)\s+credited',
            r'eligible\s+for\s+refund',
        ]
    },
    'irs_tax_scam': {
        'keywords': ['irs', 'tax', 'internal revenue', 'penalty', 'fine', 'refund', 'notice', 'income tax'],
        'weight': 5,
        'patterns': [
            r'irs\s+(agent|notice|department)',
            r'tax\s+(evasion|penalty|refund)',
            r'federal\s+tax',
            r'income\s+tax\s+(refund|notice)',
        ]
    },
    'legal_arrant': {
        'keywords': ['arrest', 'warrant', 'court', 'legal', 'summons', 'prosecute', 'jail', 'police', 'case filed'],
        'weight': 5,
        'patterns': [
            r'arrest\s+warrant',
            r'legal\s+(action|notice)',
            r'court\s+(order|summons)',
            r'police\s+(want|calling)',
            r'case\s+(filed|against)',
        ]
    },
    'prize_lottery': {
        'keywords': ['won', 'winner', 'lottery', 'prize', 'reward', 'claim', 'selected', 'gift', 'cashback'],
        'weight': 4,
        'patterns': [
            r'won\s+(the\s+)?(lottery|prize)',
            r'congratulations.*(winner|prize)',
            r'claim\s+(your\s+)?(prize|reward)',
            r'gift\s+(card| voucher)',
            r'cashback\s+(offer|eligible)',
        ]
    },
    'tech_support': {
        'keywords': ['microsoft', 'apple', 'google', 'windows', 'computer', 'laptop', 'screen', 'remote', 'infected'],
        'weight': 4,
        'patterns': [
            r'(microsoft|apple|google)\s+(support|security)',
            r'computer\s+(infected|problem)',
            r'remote\s+(access|support)',
            r'virus\s+(detected|infected)',
        ]
    },
    'social_security': {
        'keywords': ['social security', 'ssn', 'disability', 'benefits', 'medicare', 'pension'],
        'weight': 5,
        'patterns': [
            r'social\s+security\s+(number|account)',
            r'ssn\s+(suspended|compromised)',
            r'medicare\s+(benefits|coverage)',
            r'pension\s+(account|verification)',
        ]
    },
    'romance_scam': {
        'keywords': ['love', 'relationship', 'marriage', 'meet', 'profile', 'match', 'girlfriend', 'boyfriend'],
        'weight': 3,
        'patterns': [
            r'love\s+you',
            r'want\s+(to\s+)?marry',
            r'profile\s+(picture|photo)',
            r'(girlfriend|boyfriend)',
        ]
    },
    'emergency_scam': {
        'keywords': ['accident', 'hospital', 'emergency', 'bail', 'jail', 'help', 'trouble', 'son', 'daughter', 'grandson'],
        'weight': 5,
        'patterns': [
            r'met\s+with\s+accident',
            r'(son|daughter|grandson).*accident',
            r'emergency\s+(surgery|help)',
            r'(jail|bail)\s+needed',
            r'in\s+trouble\s+send\s+money',
        ]
    },
    'package_delivery': {
        'keywords': ['package', 'delivery', 'shipping', 'courier', 'track', 'address', 'customs', 'duty'],
        'weight': 3,
        'patterns': [
            r'package\s+(delivery|pending)',
            r'(fedex|dhl|ups|usps).*notice',
            r'update\s+(delivery|shipping)',
            r'customs\s+(duty|fee)',
        ]
    },
    'utility_scam': {
        'keywords': ['electricity', 'power', 'water', 'gas', 'disconnect', 'cut off', 'jio', 'airtel', 'bsnl'],
        'weight': 3,
        'patterns': [
            r'(electricity|power|water)\s+(disconnect|cut)',
            r'bill.*(due|overdue)',
            r'payment\s+(overdue|pending)',
            r'(jio|airtel|bsnl)\s+(bill|disconnect)',
        ]
    }
}

# Expanded keyword dictionary with weights - Indian scam focus
SCAM_KEYWORDS = {
    # Critical risk (weight 8) - Direct scam indicators
    'cvv': 8, 'cvv2': 8, 'c v v': 8,
    'pin number': 8, 'pin code': 8, 'atm pin': 8,
    'social security': 8, 'ssn': 8, 'ssni': 8,
    'arrest warrant': 8, 'arrest notice': 8,
    'warrant number': 8,

    # OTP/UPI specific (weight 7)
    'otp': 7, 'one time password': 7, 'verification code': 7,
    '6 digit': 7, 'six digit': 7, 'otp sent': 7,
    'share otp': 7, 'enter otp': 7, 'otp expires': 7,
    'upi': 6, 'phonepe': 6, 'paytm': 6, 'google pay': 6,
    'amazon pay': 6, 'wallet': 6,
    'upi kyc': 7, 'wallet kyc': 6,

    # Indian banking (weight 6)
    'sbi': 6, 'hdfc': 6, 'icici': 6, 'axis bank': 6,
    'yes bank': 6, 'pnb': 6, 'bank account': 6,
    'net banking': 6, 'mobile banking': 6, 'internet banking': 6,
    'credit card': 6, 'debit card': 6, 'card number': 6,
    'atm card': 6, 'account number': 6,
    'yono': 5, 'customer id': 5,

    # KYC/Aadhaar (weight 7)
    'kyc': 7, 'aadhaar': 7, 'adhar': 7, 'aadhar': 7,
    'pan card': 7, 'pancard': 7, 'kyc update': 7,
    'kyc expired': 7, 'kyc pending': 7, 'kyc documents': 7,
    'link aadhaar': 7, 'aadhaar linked': 7,

    # High risk (weight 6) - Strong indicators
    'password': 6, 'reset password': 6,
    'account blocked': 6, 'account frozen': 6, 'account suspended': 6,
    'unauthorized transaction': 6, 'suspicious activity': 6,
    'legal action': 6, 'court summons': 6, 'prosecute': 6,
    'compromised account': 6, 'hacked account': 6,
    'urgent action required': 6,
    'warrant': 6, 'arrested': 6, 'jail': 6,

    # Refund related (weight 5)
    'refund': 5, 'money back': 5, 'claim refund': 5,
    'pending refund': 5, 'eligible refund': 5,
    'tax refund': 5, 'income tax refund': 5,

    # Indian utility/telecom (weight 4)
    'jio': 4, 'airtel': 4, 'bsnl': 4, 'vodafone': 4,
    'electricity': 4, 'water bill': 4, 'gas connection': 4,
    'disconnection': 4, 'bill overdue': 4,

    # Hindi/Indian urgency phrases (weight 5)
    'abhi': 5, 'jaldi': 5, 'turant': 5, 'firse': 4,
    'last warning': 5, 'final notice': 5,
    'ab tak': 4, ' kabhi': 4,

    # Medium-high risk (weight 5)
    'verify now': 5, 'verify your': 5, 'confirm your': 5,
    'security alert': 5, 'security warning': 5, 'security notice': 5,
    'immediate payment': 5, 'pay now': 5, 'make payment': 5,
    'irs': 5, 'internal revenue': 5, 'tax penalty': 5,
    'federal tax': 5,
    'won lottery': 5, 'won prize': 5, 'winner selected': 5,
    'claim now': 5, 'claim prize': 5, 'claim reward': 5,
    'your account': 5, 'account details': 5,

    # Emergency/relative scam (weight 6)
    'accident': 6, 'hospital': 6, 'bail': 6,
    'son accident': 6, 'daughter accident': 6,
    'grandson accident': 6, 'nephew accident': 6,
    'jail hai': 6, 'police station': 6,
    'emergency money': 6, 'help me': 5,

    # Medium risk (weight 4)
    'urgent': 4, 'immediately': 4, 'right now': 4,
    'expire': 4, 'expires today': 4, 'expiring': 4,
    'confirm': 4, 'confirm now': 4,
    'update': 4, 'update now': 4,
    'prize': 4, 'lottery': 4, 'reward': 4,
    'federal': 4, 'investigation': 4,
    'limited time': 4, 'last chance': 4,
    'act now': 4, 'act fast': 4, 'don\'t delay': 4,
    'final warning': 4,
    'press 1': 4, 'press one': 4, 'call now': 4,

    # Hinglish call center phrases (weight 4)
    'this is calling from': 4, 'courtesy call': 4,
    'customer service': 4, 'toll free': 4,
    'stay on line': 4, 'do not disconnect': 4,
    'your call is important': 4, 'representative': 4,

    # Lower-medium risk (weight 3)
    'verify': 3, 'routing number': 3,
    'click link': 3, 'visit website': 3,
    'provide your': 3, 'share your': 3,
    'call back': 3, 'return call': 3,
    'government': 3, 'official': 3, 'authority': 3,
    'department': 3, 'agent': 3, 'officer': 3,

    # Suspicious phrases (weight 2)
    'won': 2, 'congratulations': 2, 'congrats': 2,
    'selected': 2, 'lucky': 2, 'eligible': 2,
    'tax': 2, 'bill': 2, 'payment': 2,
    'delivery': 2, 'package': 2, 'courier': 2,
    'suspended': 2, 'terminate': 2,
}

# Urgency indicators - including Hindi phrases
URGENCY_INDICATORS = {
    'extreme': ['right now', 'immediately', 'within 24 hours', 'before it\'s too late',
                'last warning', 'final notice', 'act now or lose', 'expire in minutes',
                'abhi jaldi', 'turant', 'firse abhi', 'last warning', 'final notice'],
    'high': ['urgent', 'time sensitive', 'expires today', 'limited time offer',
             'don\'t delay', 'hurry', 'fast', 'quick action needed', 'jaldi karein',
             'time limit', 'deadline today', '2 hours', '24 ghante'],
    'medium': ['act now', 'call back today', 'respond within', 'deadline approaching',
               'kal tak', 'aaj ke andar', 'avoid penalty']
}

# Sensitive information requests (red flags) - Indian focus
SENSITIVE_INFO_TYPES = {
    'financial': ['cvv', 'pin', 'card number', 'account number', 'routing number',
                  'bank details', 'credit card', 'debit card', 'atm card', 'upi',
                  'wallet', 'password', 'transaction password'],
    'identity': ['social security', 'ssn', 'date of birth', 'mother\'s maiden name',
                 'aadhaar', 'aadhar', 'pan card', 'pancard', 'passport', 'voter id',
                 'driving license', 'dob'],
    'security': ['password', 'otp', 'verification code', 'security question', 'pin number',
                 'login password', 'mpin', 'u pin'],
    'personal': ['address', 'phone number', 'email', 'full name', 'mobile number',
                 'alternative number', 'date of birth']
}


def detect_keywords(text: str) -> Tuple[int, List[str], Dict]:
    """Detect scam keywords and return score with details"""
    if not text:
        return 0, [], {}

    text_lower = text.lower()

    score = 0
    detected = []
    details = {}

    # Check each keyword
    for keyword, weight in SCAM_KEYWORDS.items():
        if keyword in text_lower:
            score += weight
            detected.append(keyword)

    # Group by category
    if detected:
        category_scores = {}
        for cat, cat_info in SCAM_CATEGORIES.items():
            cat_score = 0
            for kw in cat_info['keywords']:
                if kw in text_lower:
                    cat_score += cat_info['weight']
            if cat_score > 0:
                category_scores[cat] = cat_score
        details['category_scores'] = category_scores

    details['detected_keywords'] = detected
    details['keyword_count'] = len(detected)
    details['raw_score'] = score

    return score, detected, details


def detect_urgency(text: str) -> Tuple[int, List[str], Dict]:
    """Detect urgency indicators"""
    if not text:
        return 0, [], {}

    text_lower = text.lower()

    score = 0
    detected = []
    details = {}

    for level, phrases in URGENCY_INDICATORS.items():
        for phrase in phrases:
            if phrase in text_lower:
                if level == 'extreme':
                    score += 4
                elif level == 'high':
                    score += 3
                else:
                    score += 2
                detected.append(phrase)

    details['urgency_level'] = 'extreme' if score >= 6 else ('high' if score >= 3 else 'low')
    details['detected_phrases'] = detected

    return score, detected, details


def detect_sensitive_info_requests(text: str) -> Tuple[int, List[str], Dict]:
    """Detect requests for sensitive information"""
    if not text:
        return 0, [], {}

    text_lower = text.lower()

    score = 0
    detected = []
    details = {}

    category_detected = {}

    for category, info_types in SENSITIVE_INFO_TYPES.items():
        for info_type in info_types:
            if info_type in text_lower:
                score += 5
                detected.append(info_type)
                if category not in category_detected:
                    category_detected[category] = []
                category_detected[category].append(info_type)

    details['categories'] = category_detected
    details['critical'] = score >= 10

    return score, detected, details


def classify_scam_category(text: str) -> Tuple[str, Dict]:
    """Classify the type of scam based on text content"""
    if not text:
        return 'unknown', {}

    text_lower = text.lower()

    category_scores = {}

    for cat, cat_info in SCAM_CATEGORIES.items():
        score = 0

        # Check keywords
        for kw in cat_info['keywords']:
            if kw in text_lower:
                score += cat_info['weight']

        # Check patterns
        for pattern in cat_info['patterns']:
            if re.search(pattern, text_lower):
                score += cat_info['weight'] * 1.5

        if score > 0:
            category_scores[cat] = score

    if not category_scores:
        return 'general_scam', {'scores': {}}

    # Get top category
    top_category = max(category_scores, key=category_scores.get)
    confidence = min(category_scores[top_category] / 15.0, 1.0)

    return top_category, {
        'scores': category_scores,
        'top_category': top_category,
        'confidence': confidence,
        'all_categories': sorted(category_scores.items(), key=lambda x: x[1], reverse=True)
    }


def calculate_keyword_risk(text: str) -> Tuple[float, Dict]:
    """Calculate overall keyword-based risk score"""
    if not text or len(text.strip()) < 3:
        return 0.0, {}

    # Get individual scores
    kw_score, kw_detected, kw_details = detect_keywords(text)
    urgency_score, urgency_detected, urgency_details = detect_urgency(text)
    sensitive_score, sensitive_detected, sensitive_details = detect_sensitive_info_requests(text)

    # Category classification
    category, category_details = classify_scam_category(text)

    # Calculate probabilities
    # Keywords: normalize to 0-1 (cap at 20 points)
    kw_prob = min(kw_score / 20.0, 1.0)

    # Urgency: normalize to 0-1 (cap at 8 points)
    urgency_prob = min(urgency_score / 8.0, 1.0)

    # Sensitive: normalize to 0-1 (cap at 10 points)
    sensitive_prob = min(sensitive_score / 10.0, 1.0)

    # Weighted combination
    final_probability = (
        kw_prob * 0.5 +
        urgency_prob * 0.25 +
        sensitive_prob * 0.25
    )

    details = {
        'keyword_probability': kw_prob,
        'urgency_probability': urgency_prob,
        'sensitive_info_probability': sensitive_prob,
        'detected_keywords': kw_detected,
        'detected_urgency': urgency_detected,
        'detected_sensitive_info': sensitive_detected,
        'scam_category': category,
        'category_details': category_details,
        'raw_scores': {
            'keywords': kw_score,
            'urgency': urgency_score,
            'sensitive': sensitive_score
        }
    }

    return final_probability, details


if __name__ == "__main__":
    # Test
    test_texts = [
        "Your account has been compromised share OTP immediately",
        "Congratulations you won a lottery claim your reward now",
        "This is bank security please confirm your CVV number",
        "Meeting scheduled tomorrow at 5 PM",
        "IRS Notice: Arrest warrant issued - call immediately",
        "Your package is pending delivery - update address",
    ]

    for text in test_texts:
        prob, details = calculate_keyword_risk(text)
        cat, cat_details = classify_scam_category(text)
        print(f"\nText: {text}")
        print(f"Risk: {prob:.2f} | Category: {cat}")
        print(f"Keywords: {details['detected_keywords']}")
        print(f"Sensitive: {details['detected_sensitive_info']}")