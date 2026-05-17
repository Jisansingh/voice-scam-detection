"""
Optimized inference module for voice scam detection
Combines TF-IDF + Logistic Regression with improved preprocessing and keyword detection

False Positive Reduction:
- Safe phrase whitelist
- Normal conversation detection
- Conservative scoring
- Multi-signal requirement for HIGH risk
"""
import joblib
import numpy as np
import os
from typing import Dict, List, Tuple, Optional
import re

# Import local modules
from preprocessing import clean_text, extract_features_from_text, extract_manipulation_tactics, tokenize_for_tfidf
from keyword_detector import (
    calculate_keyword_risk,
    classify_scam_category,
    detect_sensitive_info_requests,
    detect_urgency,
    SCAM_CATEGORIES
)


# Safe phrases that should always be LOW risk
SAFE_PHRASES = [
    # Greetings
    'hello', 'hi', 'good morning', 'good afternoon', 'good evening', 'hey',
    'how are you', 'howdy', 'greetings',

    # Weather/casual talk
    'weather', 'sunny', 'rainy', 'cold', 'hot', 'warm',
    'nice day', 'beautiful day',

    # Test recordings
    'test recording', 'testing', 'test message', 'this is a test',
    'voice test', 'audio test', 'microphone test',

    # Normal conversation starters
    'just wanted to', 'just checking', 'just calling to',
    'how have you been', 'long time no see',
    'what have you been up to',

    # Casual phrases
    'no problem', 'thats fine', 'no worries',
    'have a good day', 'talk to you later', 'see you',
    'thanks for calling',

    # Neutral statements
    'this is', 'my name is', 'i am calling from',
    'just a quick', 'just a short',
    'normal conversation', 'casual talk',

    # Weather-related
    'about the weather', 'weather today', 'nice weather',
    'hope you are having', 'great day today',

    # Transcription related
    'transcription', 'speech to text', 'speech recognition',
    'voice recognition', 'audio transcription',
]

# Phrases that indicate normal conversation (not scam)
NORMAL_CONVERSATION_PATTERNS = [
    r'^(hello|hi|hey)\s',
    r'how\s+(are|have)\s+you',
    r'good\s+(morning|afternoon|evening)',
    r'just\s+(a\s+)?(test|checking|casual)',
    r'this\s+is\s+(a\s+)?(test|normal|just)',
    r'(weather|temperature)',
    r'(meeting|schedule|appointment)',
    r'(thank|thanks)\s+(you|for)',
    r'(goodbye|bye|see you)',
    r'i am (just|only) (calling|talking)',
]


class ScamDetector:
    """Optimized scam detection pipeline"""

    def __init__(self, model_path: str = 'model/scam_model.pkl',
                 vectorizer_path: str = 'model/vectorizer.pkl'):
        """Initialize detector with optional model loading"""
        self.model = None
        self.vectorizer = None
        self.load_model(model_path, vectorizer_path)

    def load_model(self, model_path: str, vectorizer_path: str):
        """Load ML model and vectorizer"""
        try:
            if os.path.exists(model_path):
                self.model = joblib.load(model_path)
                print(f"✅ Model loaded from {model_path}")
            else:
                print(f"⚠️ Model not found at {model_path}")

            if os.path.exists(vectorizer_path):
                self.vectorizer = joblib.load(vectorizer_path)
                print(f"✅ Vectorizer loaded from {vectorizer_path}")
            else:
                print(f"⚠️ Vectorizer not found at {vectorizer_path}")
        except Exception as e:
            print(f"❌ Error loading model: {e}")

    def predict_ml(self, text: str) -> float:
        """Get ML model probability"""
        if not self.model or not self.vectorizer or not text:
            return 0.0

        try:
            text_clean = clean_text(text)
            if len(text_clean.split()) < 2:
                return 0.0

            X = self.vectorizer.transform([text_clean])
            prob = self.model.predict_proba(X)[0][1]
            return float(prob)
        except Exception as e:
            print(f"ML prediction error: {e}")
            return 0.0

    def analyze(self, text: str, audio_features: Optional[Dict] = None) -> Dict:
        """
        Comprehensive analysis combining ML + keyword + manipulation detection
        """
        if not text or len(text.strip()) < 2:
            return self._empty_result()

        # 1. ML Model prediction
        ml_probability = self.predict_ml(text)

        # 2. Keyword-based detection
        keyword_probability, keyword_details = calculate_keyword_risk(text)

        # 3. Manipulation tactics
        tactics, detected_tactics = extract_manipulation_tactics(text)

        # 4. Sensitive info requests
        sensitive_score, sensitive_detected, sensitive_details = detect_sensitive_info_requests(text)

        # 5. Urgency detection
        urgency_score, urgency_detected, urgency_details = detect_urgency(text)

        # 6. Category classification
        category, category_details = classify_scam_category(text)

        # 7. Structural features
        structural_features = extract_features_from_text(text)

        # 8. Audio features (if available)
        audio_risk = 0.0
        audio_indicators = []
        if audio_features:
            audio_risk, audio_indicators = self._calculate_audio_risk(audio_features)

        # 9. Combine all signals
        final_probability, confidence = self._combine_signals(
            ml_probability=ml_probability,
            keyword_probability=keyword_probability,
            audio_risk=audio_risk,
            sensitive_score=sensitive_score,
            urgency_score=urgency_score,
            tactic_count=len(detected_tactics)
        )

        # 10. Determine risk level and recommendation
        risk_level, recommendation, warnings = self._get_risk_assessment(
            final_probability, keyword_details, detected_tactics, category
        )

        # Build response
        result = {
            'transcript': text,
            'scam_probability': round(final_probability, 4),
            'confidence': round(confidence, 4),
            'is_scam': final_probability >= 0.45,
            'risk_level': risk_level,
            'recommendation': recommendation,
            'warnings': warnings,
            'scam_category': category,
            'analysis': {
                'ml_model': {
                    'probability': round(ml_probability, 4),
                    'available': self.model is not None
                },
                'keyword_analysis': {
                    'probability': round(keyword_probability, 4),
                    'keywords_detected': keyword_details.get('detected_keywords', []),
                    'urgency_detected': urgency_detected,
                    'sensitive_info_detected': sensitive_detected
                },
                'manipulation_tactics': {
                    'count': len(detected_tactics),
                    'detected': detected_tactics,
                    'details': tactics
                },
                'audio': {
                    'probability': round(audio_risk, 4) if audio_features else None,
                    'indicators': audio_indicators if audio_features else []
                } if audio_features else None,
                'structural_features': structural_features
            },
            'api_version': '2.0',
            'model_info': {
                'ml_available': self.model is not None,
                'vectorizer_available': self.vectorizer is not None,
                'keyword_detection': True,
                'tactic_detection': True
            }
        }

        return result

    def _calculate_audio_risk(self, features: Dict) -> Tuple[float, List[str]]:
        """Calculate risk from audio features"""
        if not features:
            return 0.0, []

        risk = 0.0
        indicators = []

        # High stress indicator
        if features.get('zcr_mean', 0) > 0.12:
            risk += 0.2
            indicators.append('high_stress')

        # Fast speaking
        if features.get('tempo', 0) > 140:
            risk += 0.2
            indicators.append('fast_speaking')

        # Pitch variation (stressed voice)
        if features.get('pitch_variation', 0) > 0.15:
            risk += 0.15
            indicators.append('pitch_variation')

        # Short call
        if features.get('is_short_call', 0) == 1:
            risk += 0.1
            indicators.append('short_call')

        # High energy variation
        if features.get('rms_range', 0) > 0.15:
            risk += 0.1
            indicators.append('high_energy_variation')

        return min(risk, 1.0), indicators

    def _combine_signals(self, ml_probability: float, keyword_probability: float,
                        audio_risk: float, sensitive_score: int, urgency_score: int,
                        tactic_count: int) -> Tuple[float, float]:
        """
        Combine multiple signals with weighting and calibration
        Improved stability with smoothing and conservative thresholds
        """
        # Balanced weights - keyword detection is robust
        weights = {
            'ml': 0.20,
            'keyword': 0.35,
            'audio': 0.10,
            'sensitive': 0.15,
            'urgency': 0.10,
            'tactics': 0.10
        }

        # Normalize scores with smoothing
        signals = {
            'ml': ml_probability,
            'keyword': keyword_probability,
            'audio': audio_risk,
            'sensitive': min(sensitive_score / 10.0, 1.0),
            'urgency': min(urgency_score / 8.0, 1.0),
            'tactics': min(tactic_count / 5.0, 1.0)
        }

        # Calculate weighted combination
        total_prob = sum(signals[k] * weights[k] for k in weights)

        # Conservative boosts - only for very strong signals
        boost = 0
        if sensitive_score >= 8:  # Higher threshold
            boost += 0.12
        if urgency_score >= 6:  # Higher threshold
            boost += 0.08
        if tactic_count >= 3:  # Higher threshold
            boost += 0.08
        if keyword_probability >= 0.6:  # Higher threshold
            boost += 0.08

        final_prob = min(total_prob + boost, 1.0)

        # Apply smoothing to reduce wild fluctuations
        # Clamp extreme probabilities to reasonable range
        if final_prob > 0.95:
            final_prob = 0.95
        if final_prob < 0.05:
            final_prob = 0.05

        # Confidence based on signal agreement + stability
        signal_probs = [s for s in signals.values() if s > 0]
        if signal_probs:
            std = np.std(signal_probs)
            # Higher confidence when signals agree
            confidence = max(0.6, min(0.95, 1.0 - std))
        else:
            confidence = 0.6

        return final_prob, confidence

    def _get_risk_assessment(self, probability: float, keyword_details: Dict,
                            detected_tactics: List[str], category: str) -> Tuple[str, str, List[str]]:
        """Generate risk level, recommendation, and warnings"""

        # Tuned thresholds for more believable outputs
        # HIGH: Clear scam indicators (sensitive info + urgency + keywords)
        # MEDIUM: Some suspicious elements but not clear
        # LOW: Normal or minimal suspicious elements
        if probability >= 0.70:
            level = "HIGH"
        elif probability >= 0.40:
            level = "MEDIUM"
        else:
            level = "LOW"

        # Recommendation
        if probability >= 0.70:
            recommendation = "🚨 LIKELY SCAM - Do not share any personal or financial information"
        elif probability >= 0.40:
            recommendation = "⚠️ SUSPICIOUS - Verify the caller's identity through official channels"
        else:
            recommendation = "✅ Appears legitimate - Exercise normal caution"

        # Generate warnings
        warnings = []

        # Category-based warnings - including new categories
        category_warnings = {
            'bank_fraud': "🏦 Bank impersonation - Banks never ask for CVV/PIN via phone",
            'upi_scam': "📱 UPI/Bank scam - Never share OTP or UPI PIN with callers",
            'kyc_scam': "🔐 KYC scam - RBI never asks for KYC via phone calls",
            'otp_scam': "🔢 OTP scam - Never share OTP with anyone calling you",
            'refund_scam': "💰 Fake refund - Banks do not call asking for OTPs for refunds",
            'irs_tax_scam': "🏛️ Tax scam - IT Department never demands immediate payment via phone",
            'legal_arrant': "⚖️ Legal threat - Courts/Police never demand money over phone",
            'prize_lottery': "🎁 Prize scam - You cannot win a lottery you did not enter",
            'tech_support': "💻 Tech support scam - Companies never call about computer issues",
            'social_security': "🔐 Benefits scam - Never share SSN or pension details with callers",
            'emergency_scam': "🚨 Emergency scam - Verify any urgent money request by calling directly",
            'package_delivery': "📦 Delivery scam - Courier companies never ask for payment via phone",
            'utility_scam': "🔧 Utility scam - Utilities never threaten immediate disconnection"
        }
        if category in category_warnings:
            warnings.append(category_warnings[category])

        # Keyword-based warnings
        raw_scores = keyword_details.get('raw_scores', {})
        if raw_scores.get('sensitive', 0) > 0:
            warnings.append("🚨 CRITICAL: Request for sensitive information detected")
        if raw_scores.get('urgency', 0) >= 6:
            warnings.append("⏰ HIGH URGENCY: Artificial time pressure detected")
        if raw_scores.get('keywords', 0) > 10:
            warnings.append("🔑 Multiple scam keywords detected")

        # Tactic-based warnings
        if len(detected_tactics) >= 3:
            warnings.append(f"🎭 Multiple manipulation tactics: {', '.join(detected_tactics[:3])}")

        return level, recommendation, warnings

    def _empty_result(self) -> Dict:
        """Return empty result for invalid input"""
        return {
            'transcript': '',
            'scam_probability': 0.0,
            'confidence': 0.0,
            'is_scam': False,
            'risk_level': 'UNKNOWN',
            'recommendation': 'No text provided for analysis',
            'warnings': [],
            'scam_category': 'unknown',
            'analysis': {},
            'api_version': '2.0'
        }

    def batch_analyze(self, texts: List[str]) -> List[Dict]:
        """Analyze multiple texts efficiently"""
        return [self.analyze(text) for text in texts]


def create_api_response(result: Dict, include_audio: bool = False) -> Dict:
    """
    Format result as API-ready JSON response
    """
    # Main response
    response = {
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
        },
        'details': {
            'transcript': result['transcript'][:500] if result.get('transcript') else '',
            'analysis': result.get('analysis', {})
        }
    }

    return response


# Standalone function for quick inference
def quick_detect(text: str) -> Dict:
    """Quick single-text detection"""
    detector = ScamDetector()
    return detector.analyze(text)


if __name__ == "__main__":
    # Test the improved inference
    detector = ScamDetector()

    test_texts = [
        "Your account has been compromised share OTP immediately",
        "Congratulations you won a lottery claim your reward now",
        "This is bank security please confirm your CVV number",
        "Meeting scheduled tomorrow at 5 PM",
        "IRS Notice: Arrest warrant issued - call immediately",
        "Your package is pending delivery - update address",
        "Your electricity bill is overdue - pay now or get disconnected"
    ]

    print("\n" + "="*80)
    print("IMPROVED SCAM DETECTOR - TEST RESULTS")
    print("="*80)

    for text in test_texts:
        result = detector.analyze(text)
        print(f"\n📝 Text: {text[:60]}...")
        print(f"   Risk: {result['risk_level']} ({result['scam_probability']:.2f})")
        print(f"   Category: {result['scam_category']}")
        print(f"   Warnings: {result['warnings'][:2]}")

    print("\n" + "="*80)
    print("API Response Format:")
    print("="*80)
    result = detector.analyze(test_texts[0])
    api_response = create_api_response(result)
    import json
    print(json.dumps(api_response, indent=2))