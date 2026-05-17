# enhanced_scam_detector.py - Improved with better preprocessing and inference
from flask import Flask, render_template, request, jsonify
import speech_recognition as sr
import joblib
import os
from pydub import AudioSegment
import tempfile
import librosa
import numpy as np
import warnings
import sys

warnings.filterwarnings('ignore')

# Add model directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import improved modules
try:
    from improved_inference import ScamDetector, create_api_response
    from preprocessing import clean_text, extract_features_from_text, extract_manipulation_tactics
    print("✅ Improved modules loaded")
    IMPROVED_MODE = True
except ImportError as e:
    print(f"⚠️ Could not load improved modules: {e}")
    IMPROVED_MODE = False

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Load ML model for legacy mode
try:
    model = joblib.load('model/scam_model.pkl')
    vectorizer = joblib.load('model/vectorizer.pkl')
    print("✅ Legacy model loaded!")
except Exception as e:
    print(f"⚠️ Legacy model not loaded: {e}")
    model = None
    vectorizer = None

# Initialize improved detector
detector = ScamDetector() if IMPROVED_MODE else None

# Legacy keyword lists (used if improved modules unavailable)
SCAM_KEYWORDS = {
    'cvv': 5, 'pin number': 5, 'social security': 5, 'arrest': 5,
    'warrant': 5, 'account blocked': 5, 'frozen account': 5,
    'otp': 4, 'password': 4, 'suspended': 4, 'unauthorized': 4,
    'legal action': 4, 'verify now': 4, 'compromised': 4,
    'urgent': 3, 'immediately': 3, 'expire': 3, 'confirm': 3,
    'update': 3, 'security alert': 3, 'tax': 3, 'prize': 3,
    'federal': 3, 'investigation': 3, 'limited time': 3,
    'verify': 2, 'bank account': 2, 'credit card': 2, 'refund': 2,
    'click link': 2, 'act now': 2, 'final notice': 2, 'won': 2,
    'last chance': 4, 'act fast': 4, 'call back': 3,
    'press 1': 3, 'press one': 3, 'your account': 2,
    'confirm your': 3, 'provide your': 3, 'share your': 3
}

URGENCY_PHRASES = [
    'right now', 'immediately', 'within 24 hours', 'before it\'s too late',
    'last warning', 'final notice', 'urgent action required', 'act now',
    'time sensitive', 'expires today', 'limited time', 'don\'t delay'
]

SENSITIVE_INFO_REQUESTS = [
    'cvv', 'pin', 'password', 'social security', 'ssn', 'account number',
    'routing number', 'mother\'s maiden name', 'date of birth', 'card number'
]

def extract_enhanced_audio_features(audio_path):
    """
    Enhanced audio feature extraction with more scam indicators
    """
    try:
        audio_array, sr = librosa.load(audio_path, sr=16000, duration=120)
        
        if len(audio_array) < sr:
            return None
        
        audio_array, _ = librosa.effects.trim(audio_array, top_db=20)
        
        features = {}
        
        # 1. MFCC - Voice characteristics
        mfccs = librosa.feature.mfcc(y=audio_array, sr=sr, n_mfcc=13)
        features['mfcc_mean'] = np.mean(mfccs)
        features['mfcc_std'] = np.std(mfccs)
        features['mfcc_var'] = np.var(mfccs)  # NEW: Variation detection
        
        # 2. Zero Crossing Rate - Stress/urgency
        zcr = librosa.feature.zero_crossing_rate(audio_array)
        features['zcr_mean'] = np.mean(zcr)
        features['zcr_std'] = np.std(zcr)
        features['zcr_max'] = np.max(zcr)  # NEW: Peak urgency
        
        # 3. Spectral features
        spectral_centroid = librosa.feature.spectral_centroid(y=audio_array, sr=sr)
        features['spectral_centroid_mean'] = np.mean(spectral_centroid)
        features['spectral_centroid_std'] = np.std(spectral_centroid)
        features['spectral_centroid_range'] = np.max(spectral_centroid) - np.min(spectral_centroid)
        
        # 4. Tempo - Speaking speed
        tempo, beats = librosa.beat.beat_track(y=audio_array, sr=sr)
        features['tempo'] = tempo
        features['is_fast_speaking'] = 1 if tempo > 140 else 0  # NEW: Binary flag
        
        # 5. Energy - Voice intensity
        rms = librosa.feature.rms(y=audio_array)
        features['rms_mean'] = np.mean(rms)
        features['rms_std'] = np.std(rms)
        features['rms_range'] = np.max(rms) - np.min(rms)  # NEW: Intensity variation
        
        # 6. Duration
        features['duration'] = len(audio_array) / sr
        features['is_short_call'] = 1 if features['duration'] < 30 else 0  # NEW
        
        # 7. NEW: Pitch analysis (scammers often have stressed voice)
        pitches, magnitudes = librosa.piptrack(y=audio_array, sr=sr)
        pitch_values = []
        for t in range(pitches.shape[1]):
            index = magnitudes[:, t].argmax()
            pitch = pitches[index, t]
            if pitch > 0:
                pitch_values.append(pitch)
        
        if pitch_values:
            features['pitch_mean'] = np.mean(pitch_values)
            features['pitch_std'] = np.std(pitch_values)
            features['pitch_variation'] = np.std(pitch_values) / (np.mean(pitch_values) + 1e-6)
        else:
            features['pitch_mean'] = 0
            features['pitch_std'] = 0
            features['pitch_variation'] = 0
        
        return features
        
    except Exception as e:
        print(f"❌ Audio feature extraction error: {e}")
        return None

def detect_scam_indicators(text):
    """
    ENHANCED: Multi-layer keyword and pattern detection
    """
    if not text:
        return 0, [], {}
    
    text_lower = text.lower()
    
    # Layer 1: Keyword scoring
    keyword_score = 0
    detected_keywords = []
    
    for keyword, weight in SCAM_KEYWORDS.items():
        if keyword in text_lower:
            keyword_score += weight
            detected_keywords.append(keyword)
    
    # Layer 2: Urgency detection (CRITICAL for scams)
    urgency_score = 0
    detected_urgency = []
    for phrase in URGENCY_PHRASES:
        if phrase in text_lower:
            urgency_score += 3
            detected_urgency.append(phrase)
    
    # Layer 3: Sensitive info requests (MAJOR RED FLAG)
    sensitive_score = 0
    detected_sensitive = []
    for info_type in SENSITIVE_INFO_REQUESTS:
        if info_type in text_lower:
            sensitive_score += 5
            detected_sensitive.append(info_type)
    
    # Layer 4: Pattern analysis
    pattern_score = 0
    patterns = []
    
    # Check for multiple question marks (urgency)
    if text.count('?') > 2:
        pattern_score += 2
        patterns.append('multiple_questions')
    
    # Check for ALL CAPS (shouting/urgency)
    words = text.split()
    caps_count = sum(1 for word in words if word.isupper() and len(word) > 2)
    if caps_count > 2:
        pattern_score += 2
        patterns.append('excessive_caps')
    
    # Check for numbers (account numbers, amounts, etc.)
    if any(char.isdigit() for char in text) and any(keyword in text_lower for keyword in ['account', 'card', 'number']):
        pattern_score += 1
        patterns.append('requests_numbers')
    
    # Total score
    total_score = keyword_score + urgency_score + sensitive_score + pattern_score
    
    indicators = {
        'keyword_score': keyword_score,
        'urgency_score': urgency_score,
        'sensitive_info_score': sensitive_score,
        'pattern_score': pattern_score,
        'detected_keywords': detected_keywords,
        'detected_urgency': detected_urgency,
        'detected_sensitive': detected_sensitive,
        'patterns': patterns
    }
    
    return total_score, detected_keywords, indicators

def calculate_scam_risk_enhanced(text, audio_features=None):
    """
    ENHANCED: Multi-factor risk calculation with lower threshold for false negatives
    """
    risk_scores = []
    weights = []
    details = {}
    
    # Factor 1: ML Model (if available) - 40% weight
    if model and vectorizer and text and len(text.split()) > 2:
        try:
            text_vectorized = vectorizer.transform([text])
            ml_probability = model.predict_proba(text_vectorized)[0][1]
            risk_scores.append(ml_probability)
            weights.append(0.4)
            details['ml_probability'] = ml_probability
            print(f"📊 ML Model: {ml_probability:.3f}")
        except Exception as e:
            print(f"ML error: {e}")
    
    # Factor 2: Text Analysis - 35% weight
    total_score, detected_keywords, indicators = detect_scam_indicators(text)
    
    # ENHANCED: More sensitive text scoring
    text_probability = min(total_score / 15.0, 1.0)  # LOWERED from 20 to 15 for sensitivity
    risk_scores.append(text_probability)
    weights.append(0.35)
    details['text_analysis'] = indicators
    details['text_probability'] = text_probability
    print(f"🔑 Text Analysis: {text_probability:.3f} (Score: {total_score})")
    
    # Factor 3: Audio Features - 25% weight
    if audio_features:
        audio_risk = 0
        audio_indicators = []
        
        # High stress/urgency indicators
        if audio_features.get('zcr_mean', 0) > 0.12:
            audio_risk += 0.25
            audio_indicators.append('high_stress')
        
        if audio_features.get('tempo', 0) > 140:
            audio_risk += 0.25
            audio_indicators.append('fast_speaking')
        
        # Pitch variation (stressed voice)
        if audio_features.get('pitch_variation', 0) > 0.15:
            audio_risk += 0.2
            audio_indicators.append('voice_stress')
        
        # High energy variation (aggressive speaking)
        if audio_features.get('rms_range', 0) > 0.15:
            audio_risk += 0.15
            audio_indicators.append('aggressive_tone')
        
        # Very short calls are suspicious
        if audio_features.get('is_short_call', 0) == 1:
            audio_risk += 0.15
            audio_indicators.append('short_duration')
        
        audio_probability = min(audio_risk, 1.0)
        risk_scores.append(audio_probability)
        weights.append(0.25)
        details['audio_probability'] = audio_probability
        details['audio_indicators'] = audio_indicators
        print(f"🎵 Audio Features: {audio_probability:.3f}")
    
    # Calculate weighted average
    if risk_scores:
        total_weight = sum(weights[:len(risk_scores)])
        combined_probability = sum(p * w for p, w in zip(risk_scores, weights[:len(risk_scores)])) / total_weight
    else:
        combined_probability = 0.5
    
    # CRITICAL: Boost probability if high-risk indicators present
    # This helps catch scams that slip through individual checks
    if indicators.get('sensitive_info_score', 0) > 0:
        combined_probability = min(combined_probability + 0.2, 1.0)  # Major boost
        details['boosted_for_sensitive_info'] = True
    
    if indicators.get('urgency_score', 0) >= 6:
        combined_probability = min(combined_probability + 0.15, 1.0)
        details['boosted_for_urgency'] = True
    
    # ENHANCED: Lower threshold - if ANY strong signal, increase risk
    if any([
        indicators.get('sensitive_info_score', 0) > 0,
        indicators.get('urgency_score', 0) > 5,
        indicators.get('keyword_score', 0) > 10,
        audio_features and audio_features.get('is_fast_speaking', 0) == 1
    ]):
        combined_probability = max(combined_probability, 0.55)  # Minimum 55% if red flags
        details['minimum_threshold_applied'] = True
    
    print(f"🎯 Final Risk: {combined_probability:.3f}")
    
    return combined_probability, details

def get_risk_assessment(probability, details):
    """
    ENHANCED: More nuanced risk assessment with explanations
    """
    # LOWERED thresholds for better sensitivity
    if probability >= 0.65:  # CHANGED from 0.7
        level = "HIGH RISK"
        emoji = "🔴"
        recommendation = "⛔ LIKELY SCAM - Do not share any information"
    elif probability >= 0.45:  # CHANGED from 0.5
        level = "MEDIUM RISK"
        emoji = "🟡"
        recommendation = "⚠️ SUSPICIOUS - Verify caller identity independently"
    else:
        level = "LOW RISK"
        emoji = "🟢"
        recommendation = "✅ Appears legitimate - Still verify if unsure"
    
    # Add specific warnings
    warnings = []
    indicators = details.get('text_analysis', {})
    
    if indicators.get('sensitive_info_score', 0) > 0:
        warnings.append("🚨 CRITICAL: Requesting sensitive information (CVV/PIN/SSN)")
    if indicators.get('urgency_score', 0) > 5:
        warnings.append("⏰ HIGH URGENCY: Creating artificial time pressure")
    if indicators.get('keyword_score', 0) > 8:
        warnings.append("🔑 MULTIPLE SCAM KEYWORDS: Contains typical scam language")
    if details.get('audio_probability', 0) > 0.6:
        warnings.append("🎵 AUDIO ANALYSIS: Voice patterns suggest deception")
    
    return {
        'level': level,
        'emoji': emoji,
        'recommendation': recommendation,
        'warnings': warnings
    }

def improve_transcription_quality(recognizer, audio_path):
    """
    ENHANCED: Better transcription with multiple strategies
    """
    # Load audio for analysis
    audio = AudioSegment.from_file(audio_path)
    duration_ms = len(audio)
    
    print(f"🎙️ Audio duration: {duration_ms/1000:.1f}s")
    
    # Strategy 1: Try full audio first (for short clips)
    if duration_ms < 30000:  # Less than 30 seconds
        try:
            print("Strategy 1: Full audio transcription...")
            with sr.AudioFile(audio_path) as source:
                recognizer.adjust_for_ambient_noise(source, duration=0.3)
                audio_data = recognizer.record(source)
            
            text = recognizer.recognize_google(audio_data, language='en-US', show_all=False)
            if text and len(text.split()) > 3:
                print(f"✅ Success: {text}")
                return text
        except Exception as e:
            print(f"Strategy 1 failed: {e}")
    
    # Strategy 2: Chunked approach with overlap
    print("Strategy 2: Chunked transcription with overlap...")
    transcripts = []
    chunk_size = 15000  # 15 seconds
    overlap = 2000  # 2 second overlap
    
    for start in range(0, min(duration_ms, 60000), chunk_size - overlap):  # Max 60 seconds
        end = min(start + chunk_size, duration_ms)
        chunk = audio[start:end]
        
        if len(chunk) < 2000:
            continue
        
        try:
            # Export chunk
            chunk_wav = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
            chunk_path = chunk_wav.name
            chunk = chunk.set_frame_rate(16000).set_channels(1)
            chunk.export(chunk_path, format="wav")
            
            with sr.AudioFile(chunk_path) as source:
                recognizer.adjust_for_ambient_noise(source, duration=0.2)
                audio_data = recognizer.record(source)
            
            text = recognizer.recognize_google(audio_data, language='en-US')
            
            if text and text.strip():
                transcripts.append(text.strip())
                print(f"   Chunk {len(transcripts)}: {text[:50]}...")
            
            os.unlink(chunk_path)
            
        except Exception as e:
            print(f"   Chunk at {start}ms failed: {e}")
            continue
    
    if transcripts:
        full_text = ' '.join(transcripts)
        return full_text
    
    return None

# Keep your existing routes and add enhanced analysis
@app.route('/', methods=['POST'])
def analyze_audio():
    """Analyze audio file for scam detection"""
    if 'audio' not in request.files:
        return jsonify({'error': 'No audio file provided'}), 400

    audio_file = request.files['audio']
    if audio_file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    temp_path = None
    converted_path = None

    try:
        print(f"\n{'='*60}")
        print(f"📁 ANALYZING: {audio_file.filename}")
        print(f"Mode: {'Improved' if IMPROVED_MODE and detector else 'Legacy'}")
        print(f"{'='*60}")

        # Save uploaded file
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(audio_file.filename)[1]) as temp_file:
            audio_file.save(temp_file.name)
            temp_path = temp_file.name

        # Convert to WAV
        audio = AudioSegment.from_file(temp_path)
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as converted_file:
            converted_path = converted_file.name

        audio = audio.set_frame_rate(16000).set_channels(1)
        audio.export(converted_path, format="wav")
        print(f"✅ Converted: {len(audio)}ms, {audio.frame_rate}Hz")

        # STEP 1: Extract audio features
        print("\n🎵 Extracting audio features...")
        audio_features = extract_enhanced_audio_features(converted_path)

        if audio_features:
            print(f"✅ Features extracted:")
            print(f"   Duration: {audio_features['duration']:.1f}s")
            print(f"   Tempo: {audio_features['tempo']:.0f} BPM")
            print(f"   Stress indicators: ZCR={audio_features['zcr_mean']:.3f}")

        # STEP 2: Transcription
        print("\n🎙️ Transcribing audio...")
        recognizer = sr.Recognizer()
        recognizer.energy_threshold = 250
        recognizer.dynamic_energy_threshold = True
        recognizer.pause_threshold = 0.8
        recognizer.operation_timeout = 30

        text = improve_transcription_quality(recognizer, converted_path)

        if not text or len(text.split()) < 3:
            if audio_features:
                print("⚠️ Transcription incomplete, relying on audio analysis")
                text = "[Audio analysis only - unclear speech]"
            else:
                return jsonify({
                    'error': 'Could not transcribe audio clearly. Please ensure:\n' +
                             '• Audio contains clear speech\n' +
                             '• Minimal background noise\n' +
                             '• Audio is not music or non-speech content'
                }), 400

        print(f"✅ Transcribed: {text[:100]}...")

        # STEP 3: Risk analysis - use improved detector if available
        print(f"\n🔍 Analyzing for scam indicators...")

        if IMPROVED_MODE and detector:
            # Use improved inference
            result = detector.analyze(text, audio_features)
            response = create_api_response(result, include_audio=bool(audio_features))

            # Add audio features to response
            if audio_features:
                response['result']['audio_features'] = {
                    'duration': round(audio_features.get('duration', 0), 1),
                    'tempo': round(audio_features.get('tempo', 0), 0),
                    'indicators': result.get('analysis', {}).get('audio', {}).get('indicators', [])
                }

            print(f"\n{'='*60}")
            print(f"RESULT: {result['risk_level']} RISK")
            print(f"Probability: {result['scam_probability']:.1%}")
            print(f"Category: {result['scam_category']}")
            print(f"{'='*60}\n")

            return jsonify(response)
        else:
            # Fall back to legacy analysis
            scam_probability, analysis_details = calculate_scam_risk_enhanced(text, audio_features)
            risk_assessment = get_risk_assessment(scam_probability, analysis_details)

            response = {
                'transcript': text,
                'scam_probability': float(scam_probability),
                'is_scam': scam_probability >= 0.45,
                'risk_level': risk_assessment['level'],
                'risk_emoji': risk_assessment['emoji'],
                'recommendation': risk_assessment['recommendation'],
                'warnings': risk_assessment['warnings'],
                'analysis_details': {
                    'text_indicators': analysis_details.get('text_analysis', {}),
                    'audio_features': {
                        'duration': audio_features.get('duration', 0) if audio_features else 0,
                        'tempo': audio_features.get('tempo', 0) if audio_features else 0,
                        'audio_risk_score': analysis_details.get('audio_probability', 0)
                    } if audio_features else None
                },
                'api_version': '1.5'
            }

            print(f"\n{'='*60}")
            print(f"RESULT: {risk_assessment['emoji']} {risk_assessment['level']}")
            print(f"Probability: {scam_probability:.1%}")
            print(f"{'='*60}\n")

            return jsonify(response)

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        try:
            if temp_path and os.path.exists(temp_path):
                os.unlink(temp_path)
            if converted_path and converted_path != temp_path and os.path.exists(converted_path):
                os.unlink(converted_path)
        except:
            pass
        return jsonify({'error': f'Processing failed: {str(e)}'}), 500

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/favicon.ico')
def favicon():
    return '', 204


@app.route('/api/analyze', methods=['POST'])
def analyze_text():
    """API endpoint for text-only scam analysis"""
    if not request.is_json:
        return jsonify({'error': 'Content-Type must be application/json'}), 400

    data = request.get_json()
    text = data.get('text', '')

    if not text or len(text.strip()) < 3:
        return jsonify({'error': 'Text is required (min 3 characters)'}), 400

    try:
        if IMPROVED_MODE and detector:
            result = detector.analyze(text)
            return jsonify(create_api_response(result))
        else:
            # Legacy mode
            score, keywords, indicators = detect_scam_indicators(text)
            probability = min(score / 15.0, 1.0)
            is_scam = probability >= 0.45

            return jsonify({
                'success': True,
                'result': {
                    'scam_probability': probability,
                    'is_scam': is_scam,
                    'risk_level': 'HIGH' if probability >= 0.65 else ('MEDIUM' if probability >= 0.45 else 'LOW'),
                    'detected_keywords': keywords,
                    'indicators': indicators
                }
            })
    except Exception as e:
        return jsonify({'error': f'Analysis failed: {str(e)}'}), 500


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'mode': 'improved' if IMPROVED_MODE else 'legacy',
        'ml_model_loaded': model is not None,
        'improved_modules': IMPROVED_MODE,
        'api_version': '2.0' if IMPROVED_MODE else '1.5'
    })


if __name__ == '__main__':
    print("\n" + "="*60)
    print("🚀 VOICE SCAM DETECTOR")
    print("="*60)
    print(f"Mode: {'Improved (v2.0)' if IMPROVED_MODE else 'Legacy (v1.5)'}")
    print(f"ML Model: {'Loaded' if model else 'Not available'}")
    print(f"Improved modules: {'Available' if IMPROVED_MODE else 'Not available'}")
    print("="*60 + "\n")
    app.run(debug=True, host='0.0.0.0', port=5001)

