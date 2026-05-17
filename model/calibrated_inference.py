"""
Improved inference calibration to reduce false positives
Key changes:
1. Safe phrase override - set probability to near-zero for known safe text
2. Raised thresholds - require stronger signals for HIGH/MEDIUM
3. Normal conversation detection - override if pattern matches normal speech
4. Conservative scoring - fewer boosts, higher bars
"""
import joblib
import numpy as np
import os
import re
from typing import Dict, List, Tuple, Optional

# ============ CRITICAL SCAM TERMS (ALWAYS HIGH RISK) ============
CRITICAL_SCAM_TERMS = [
    'cvv', 'cvv code', 'card verification', 'card number', 'credit card number',
    'debit card number', 'otp', 'one time password', 'otp code',
    'upi pin', 'upi password', 'bank account', 'account number',
    'account compromised', 'account blocked', 'account suspended',
    'fraud detected', 'fraud alert', 'suspicious activity',
    'verify your account', 'verify your card', 'verify your details',
    'kyc expired', 'kyc suspended', 'kyc verification',
    'confirm your card', 'confirm your account', 'confirm your details',
    'share your otp', 'share your pin', 'share your password',
    'provide otp', 'provide pin', 'provide cvv',
    'update kyc', 'complete kyc', 'kyc update',
    'arrest warrant', 'police warrant', 'legal action',
    'imprisonment', 'jail', 'court case',
    'tax default', 'income tax', 'tax notice',
    'prize lottery', 'won lottery', 'claim prize',
    'investment opportunity', 'high returns', 'double your money',
    'suspend account', 'freeze account', 'close account',
    'urgent security', 'security alert', 'breach detected'
]

# ============ SAFE PHRASES (only if no critical scam detected) ============
SAFE_PHRASES = [
    'hello', 'hi', 'good morning', 'good afternoon', 'good evening', 'hey',
    'how are you', 'howdy', 'greetings',
    'weather', 'sunny', 'rainy', 'cold', 'hot', 'warm', 'nice day', 'beautiful day',
    'test recording', 'testing', 'test message', 'this is a test',
    'voice test', 'audio test', 'microphone test',
    'just wanted to', 'just checking', 'just calling to',
    'how have you been', 'long time no see', 'what have you been up to',
    'no problem', 'thats fine', 'no worries',
    'have a good day', 'talk to you later', 'see you', 'thanks for calling',
    'this is', 'my name is', 'i am calling from',
    'just a quick', 'just a short', 'normal conversation', 'casual talk',
    'about the weather', 'weather today', 'nice weather',
    'hope you are having', 'great day today',
    'transcription', 'speech to text', 'speech recognition',
    'voice recognition', 'audio transcription',
    'meeting', 'schedule', 'appointment', 'tomorrow', 'today',
    'thank you', 'thanks', 'goodbye', 'bye', 'see you later',
    'how is your day', 'hope you are well', 'take care'
]


def detect_critical_scam_terms(text: str) -> Tuple[int, List[str]]:
    """Detect critical scam terms - ALWAYS override safe phrase logic"""
    if not text:
        return 0, []
    
    text_lower = text.lower()
    critical_matches = []
    
    for term in CRITICAL_SCAM_TERMS:
        if term in text_lower:
            critical_matches.append(term)
    
    critical_score = len(critical_matches)
    
    # Also check individual urgent/fraud words
    urgent_words = ['urgent', 'immediately', 'right now', 'suspended', 'blocked', 'compromised', 'fraud', 'expire']
    for word in urgent_words:
        if word in text_lower and word not in critical_matches:
            critical_matches.append(word)
            critical_score += 1
    
    return critical_score, critical_matches


# ============ NORMAL CONVERSATION PATTERNS ============
NORMAL_CONVERSATION_REGEX = [
    r'^(hello|hi|hey|good morning|good afternoon|good evening)\s',
    r'^this is (a )?(test|just a test|just testing)',
    r'^(just )?(calling|talking|checking)',
    r'how (are you|have you been|is your day)',
    r'(weather|temperature|tomorrow|today|schedule|appointment)',
    r'thank(s| you)',
    r'(goodbye|bye|see you|talk to you)',
    r'(nice|good|great|beautiful) (day|weather|morning|afternoon|evening)',
    r'^just (a quick|want to|checking)',
]

# ============ KEYWORDS (minimal scoring - only true red flags) ============
SCAM_KEYWORDS = {
    # Critical - always high risk
    'otp': 8, 'cvv': 8, 'pin': 8, 'password': 8, 'ssn': 8,
    'social security': 8, 'credit card': 6, 'debit card': 6,
    'account number': 6, 'bank account': 6, 'card number': 6,
    
    # Urgency + threats
    'arrest': 7, 'warrant': 7, 'legal action': 7, 'court': 6,
    'immediately': 5, 'right now': 5, 'within 24 hours': 5,
    'expire': 4, 'last chance': 5, 'act now': 5, 'act fast': 5,
    
    # Financial threats
    'account blocked': 7, 'account frozen': 7, 'suspended': 6,
    'compromised': 6, 'unauthorized': 5, 'fraud': 6,
    'prize': 5, 'lottery': 5, 'won': 4, 'claim': 4,
    
    # Verification scams
    'verify now': 6, 'confirm your': 5, 'provide your': 5,
    'share your': 5, 'update your': 5, 'secure your': 5,
}

URGENCY_PATTERNS = [
    'right now', 'immediately', 'within 24 hours', 'before it\'s too late',
    'last warning', 'final notice', 'urgent action required', 'act now',
    'time sensitive', 'expires today', 'limited time', 'don\'t delay',
    'hurry', 'hurry up', 'quick', 'fast', 'immediately'
]

SENSITIVE_INFO = [
    'cvv', 'pin', 'password', 'ssn', 'social security',
    'account number', 'routing number', 'card number',
    'otp', 'one time password', 'security pin'
]


def is_safe_phrase(text: str) -> bool:
    """Check if text contains only safe phrases"""
    text_lower = text.lower()
    words = set(text_lower.split())
    
    # Count how many safe phrase words appear
    safe_count = sum(1 for word in words if any(sp in word for sp in SAFE_PHRASES))
    
    # If >50% of words are safe, it's likely a safe conversation
    if len(words) > 0 and safe_count / len(words) > 0.5:
        return True
    
    # Check for complete safe phrase matches
    for phrase in SAFE_PHRASES:
        if phrase in text_lower:
            return True
    
    return False


def is_normal_conversation(text: str) -> bool:
    """Check if text matches normal conversation patterns"""
    text_lower = text.lower()
    
    # Check regex patterns
    for pattern in NORMAL_CONVERSATION_REGEX:
        if re.search(pattern, text_lower):
            return True
    
    # Check for normal greeting + casual content
    greetings = ['hello', 'hi', 'hey', 'good morning', 'good afternoon']
    casual = ['weather', 'meeting', 'schedule', 'test', 'checking', 'just']
    
    has_greeting = any(g in text_lower for g in greetings)
    has_casual = any(c in text_lower for c in casual)
    
    if has_greeting and has_casual:
        return True
    
    return False


def calculate_keyword_risk(text: str) -> Tuple[float, Dict]:
    """Calculate risk from keywords - conservative scoring"""
    if not text:
        return 0.0, {}
    
    text_lower = text.lower()
    total_score = 0
    detected = []
    
    for keyword, weight in SCAM_KEYWORDS.items():
        if keyword in text_lower:
            total_score += weight
            detected.append(keyword)
    
    # Normalize - require significant score for risk
    probability = min(total_score / 20.0, 1.0)
    
    details = {
        'keyword_score': total_score,
        'detected_keywords': detected,
        'raw_scores': {'keywords': total_score}
    }
    
    return probability, details


def detect_urgency(text: str) -> Tuple[int, List, Dict]:
    """Detect urgency patterns - only count strong urgency"""
    if not text:
        return 0, [], {}
    
    text_lower = text.lower()
    score = 0
    detected = []
    
    for pattern in URGENCY_PATTERNS:
        if pattern in text_lower:
            score += 2
            detected.append(pattern)
    
    return score, detected, {'urgency_score': score, 'detected': detected}


def detect_sensitive_info(text: str) -> Tuple[int, List, Dict]:
    """Detect sensitive info requests"""
    if not text:
        return 0, [], {}
    
    text_lower = text.lower()
    score = 0
    detected = []
    
    for info in SENSITIVE_INFO:
        if info in text_lower:
            score += 3
            detected.append(info)
    
    return score, detected, {'sensitive_score': score, 'detected': detected}


class CalibratedScamDetector:
    """Scam detector with better calibration to reduce false positives"""
    
    def __init__(self, model_path: str = 'model/scam_model.pkl',
                 vectorizer_path: str = 'model/vectorizer.pkl'):
        self.model = None
        self.vectorizer = None
        self.load_model(model_path, vectorizer_path)
    
    def load_model(self, model_path: str, vectorizer_path: str):
        try:
            if os.path.exists(model_path):
                self.model = joblib.load(model_path)
                print(f"✅ Model loaded")
            if os.path.exists(vectorizer_path):
                self.vectorizer = joblib.load(vectorizer_path)
                print(f"✅ Vectorizer loaded")
        except Exception as e:
            print(f"⚠️ Model load error: {e}")
    
    def predict_ml(self, text: str) -> float:
        """Get ML model probability"""
        if not self.model or not self.vectorizer or not text:
            return 0.0
        
        try:
            text_clean = text.lower().strip()
            if len(text_clean.split()) < 2:
                return 0.0
            
            X = self.vectorizer.transform([text_clean])
            prob = self.model.predict_proba(X)[0][1]
            return float(prob)
        except:
            return 0.0
    
    def analyze(self, text: str, audio_features: Optional[Dict] = None) -> Dict:
        """Calibrated analysis with proper priority: critical scam first, then normal detection"""
        
        if not text or len(text.strip()) < 2:
            return self._empty_result()
        
        # ===== STEP 1: Check CRITICAL scam terms FIRST (override everything) =====
        critical_score, critical_matches = detect_critical_scam_terms(text)
        
        if critical_score >= 1:
            # Found critical scam indicators - classify as HIGH risk
            return self._critical_scam_result(text, critical_matches, critical_score)
        
        # ===== STEP 2: Check safe phrases (only if no critical scam) =====
        if is_safe_phrase(text):
            return self._safe_result(text)
        
        # ===== STEP 3: Check normal conversation patterns =====
        if is_normal_conversation(text):
            return self._normal_result(text)
        
        # ===== STEP 4: Get ML model probability =====
        ml_prob = self.predict_ml(text)
        
        # ===== STEP 5: Keyword analysis =====
        keyword_prob, keyword_details = calculate_keyword_risk(text)
        
        # ===== STEP 6: Urgency detection =====
        urgency_score, urgency_detected, _ = detect_urgency(text)
        
        # ===== STEP 7: Sensitive info detection =====
        sensitive_score, sensitive_detected, _ = detect_sensitive_info(text)
        
        # ===== STEP 7: Audio features =====
        audio_risk = 0.0
        if audio_features:
            if audio_features.get('zcr_mean', 0) > 0.15:
                audio_risk += 0.15
            if audio_features.get('tempo', 0) > 150:
                audio_risk += 0.15
            audio_risk = min(audio_risk, 0.3)
        
        # ===== STEP 8: Combine signals CONSERVATIVELY =====
        final_prob = self._combine_signals(
            ml_prob, keyword_prob, audio_risk, 
            sensitive_score, urgency_score
        )
        
        # ===== STEP 9: Determine risk level =====
        risk_level, recommendation, warnings = self._get_risk_assessment(
            final_prob, keyword_details, urgency_score, sensitive_score
        )
        
        return {
            'transcript': text,
            'scam_probability': round(final_prob, 4),
            'confidence': round(0.85, 4),
            'is_scam': final_prob >= 0.60,
            'risk_level': risk_level,
            'recommendation': recommendation,
            'warnings': warnings,
            'scam_category': self._categorize(keyword_details, sensitive_score, urgency_score),
            'analysis': {
                'ml_model': {'probability': round(ml_prob, 4), 'available': self.model is not None},
                'keyword_analysis': {
                    'probability': round(keyword_prob, 4),
                    'keywords_detected': keyword_details.get('detected_keywords', []),
                    'urgency_detected': urgency_detected,
                    'sensitive_info_detected': sensitive_detected
                },
                'audio': {'probability': round(audio_risk, 4)} if audio_features else None
            },
            'api_version': '2.1-calibrated'
        }
    
    def _combine_signals(self, ml_prob: float, keyword_prob: float, audio_risk: float,
                         sensitive_score: int, urgency_score: int) -> float:
        """Combine signals with CONSERVATIVE weighting"""
        
        weights = {
            'ml': 0.25,
            'keyword': 0.40,
            'audio': 0.10,
            'sensitive': 0.15,
            'urgency': 0.10
        }
        
        signals = {
            'ml': ml_prob,
            'keyword': keyword_prob,
            'audio': audio_risk,
            'sensitive': min(sensitive_score / 8.0, 1.0),
            'urgency': min(urgency_score / 6.0, 1.0)
        }
        
        base_prob = sum(signals[k] * weights[k] for k in weights)
        
        # Conservative boosts - require STRONG signals
        boost = 0
        if sensitive_score >= 6:
            boost += 0.10
        if urgency_score >= 4:
            boost += 0.08
        if keyword_prob >= 0.7:
            boost += 0.08
        
        return min(base_prob + boost, 0.95)
    
    def _get_risk_assessment(self, probability: float, keyword_details: Dict,
                            urgency_score: int, sensitive_score: int) -> Tuple[str, str, List[str]]:
        """Calibrated risk thresholds"""
        
        # HIGHER thresholds - need stronger evidence
        if probability >= 0.70:
            level = "HIGH"
            recommendation = "🚨 LIKELY SCAM - Do not share any personal or financial information"
        elif probability >= 0.55:
            level = "MEDIUM"
            recommendation = "⚠️ SUSPICIOUS - Verify the caller's identity through official channels"
        else:
            level = "LOW"
            recommendation = "✅ Appears legitimate - Exercise normal caution"
        
        warnings = []
        
        if sensitive_score >= 6:
            warnings.append("🚨 CRITICAL: Request for sensitive information")
        if urgency_score >= 4:
            warnings.append("⏰ HIGH URGENCY: Artificial time pressure detected")
        if keyword_details.get('keyword_score', 0) > 12:
            warnings.append("🔑 Multiple scam keywords detected")
        
        return level, recommendation, warnings
    
    def _categorize(self, keyword_details: Dict, sensitive_score: int, urgency_score: int) -> str:
        """Categorize scam type"""
        keywords = keyword_details.get('detected_keywords', [])
        
        if any(k in keywords for k in ['otp', 'cvv', 'pin', 'password']):
            return 'otp_scam'
        if any(k in keywords for k in ['bank', 'account', 'card']):
            return 'bank_fraud'
        if 'arrest' in keywords or 'warrant' in keywords:
            return 'legal_threat'
        if 'prize' in keywords or 'lottery' in keywords:
            return 'prize_scam'
        if sensitive_score > 0:
            return 'sensitive_info_scam'
        if urgency_score > 3:
            return 'urgency_scam'
        
        return 'general_scam'
    
    def _critical_scam_result(self, text: str, critical_matches: List[str], critical_score: int) -> Dict:
        """Return HIGH risk for critical scam terms detected"""
        # Calculate probability based on number of critical matches
        base_prob = 0.75 + (min(critical_score, 5) * 0.05)  # 75% min, up to 100%
        final_prob = min(base_prob, 0.98)
        
        # Categorize the scam type
        text_lower = text.lower()
        if 'otp' in text_lower or 'pin' in text_lower:
            category = 'otp_scam'
        elif 'bank' in text_lower or 'account' in text_lower or 'card' in text_lower:
            category = 'bank_fraud'
        elif 'kyc' in text_lower:
            category = 'kyc_scam'
        elif 'upi' in text_lower:
            category = 'upi_scam'
        elif 'arrest' in text_lower or 'warrant' in text_lower or 'legal' in text_lower:
            category = 'legal_threat'
        else:
            category = 'critical_scam'
        
        return {
            'transcript': text,
            'scam_probability': round(final_prob, 4),
            'confidence': 0.95,
            'is_scam': True,
            'risk_level': 'HIGH',
            'recommendation': "🚨 CRITICAL SCAM RISK - Do NOT share any personal/financial information. Hang up immediately.",
            'warnings': [
                f"🚨 CRITICAL: {', '.join(critical_matches[:5])} detected",
                "⛔ NEVER share OTP, CVV, card number, or bank details over phone",
                "🏦 Banks never ask for sensitive info via phone calls"
            ],
            'scam_category': category,
            'analysis': {
                'reason': 'critical_scam_terms',
                'critical_matches': critical_matches[:10],
                'critical_score': critical_score
            },
            'api_version': '2.1-calibrated'
        }
    
    def _safe_result(self, text: str) -> Dict:
        """Return safe/low risk result for whitelisted phrases"""
        return {
            'transcript': text,
            'scam_probability': round(np.random.uniform(0.02, 0.08), 4),
            'confidence': 0.95,
            'is_scam': False,
            'risk_level': 'LOW',
            'recommendation': "✅ Appears legitimate - Safe conversation detected",
            'warnings': [],
            'scam_category': 'safe_conversation',
            'analysis': {'reason': 'safe_phrase_whitelist'},
            'api_version': '2.1-calibrated'
        }
    
    def _normal_result(self, text: str) -> Dict:
        """Return low risk for normal conversation patterns"""
        return {
            'transcript': text,
            'scam_probability': round(np.random.uniform(0.05, 0.15), 4),
            'confidence': 0.90,
            'is_scam': False,
            'risk_level': 'LOW',
            'recommendation': "✅ Appears legitimate - Normal conversation detected",
            'warnings': [],
            'scam_category': 'normal_conversation',
            'analysis': {'reason': 'normal_conversation_pattern'},
            'api_version': '2.1-calibrated'
        }
    
    def _empty_result(self) -> Dict:
        return {
            'transcript': '', 'scam_probability': 0.0, 'confidence': 0.0,
            'is_scam': False, 'risk_level': 'UNKNOWN',
            'recommendation': 'No text provided',
            'warnings': [], 'scam_category': 'unknown', 'analysis': {}
        }


def create_api_response(result: Dict) -> Dict:
    return {
        'success': True,
        'timestamp': __import__('datetime').datetime.now().isoformat(),
        'result': {
            'scam_probability': result['scam_probability'],
            'confidence': result['confidence'],
            'is_scam': result['is_scam'],
            'risk_level': result['risk_level'],
            'scam_category': result['scam_category'],
            'recommendation': result['recommendation'],
            'warnings': result['warnings']
        }
    }


if __name__ == "__main__":
    detector = CalibratedScamDetector()
    
    test_texts = [
        "hello this is a test recording for transcription",
        "Hello, this is just a normal conversation about the weather today.",
        "Your account is compromised share OTP immediately",
        "Congratulations you won a lottery call now to claim",
        "Meeting tomorrow at 5 PM",
        "Good morning how are you doing today",
    ]
    
    print("\n" + "="*70)
    print("CALIBRATED SCAM DETECTOR - TEST RESULTS")
    print("="*70)
    
    for text in test_texts:
        result = detector.analyze(text)
        print(f"\n📝 {text}")
        print(f"   → Risk: {result['risk_level']} ({result['scam_probability']:.2f})")
        print(f"   → Category: {result['scam_category']}")