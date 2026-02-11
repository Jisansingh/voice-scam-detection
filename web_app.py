#!/usr/bin/env python3
"""
Complete Scam Detection Web Application
Serves HTML templates and provides API endpoints
"""

import sys
import os
# sys.path.append('/Users/jssingh/cybcup')  # Removed absolute path dependency

from flask import Flask, request, jsonify, render_template, redirect, url_for, session
import joblib
import numpy as np
import re
from sklearn.feature_extraction.text import TfidfVectorizer
import io
import tempfile

# Audio processing imports
try:
    from google.cloud import speech
    GOOGLE_SPEECH_AVAILABLE = True
    print("✅ Google Cloud Speech-to-Text available")
except ImportError:
    GOOGLE_SPEECH_AVAILABLE = False
    print("⚠️ Google Cloud Speech-to-Text not available, will use fallback")

try:
    from pydub import AudioSegment
    PYDUB_AVAILABLE = True
except ImportError:
    PYDUB_AVAILABLE = False
    print("⚠️ PyDub not available for audio conversion")

try:
    import speech_recognition as sr
    SPEECH_RECOGNITION_AVAILABLE = True
except ImportError:
    SPEECH_RECOGNITION_AVAILABLE = False
    print("⚠️ SpeechRecognition library not available for fallback")

print("🚀 Starting Complete Scam Detection Web Application...")

# Initialize Flask app
app = Flask(__name__)
app.secret_key = 'cybcup_scam_detection_2024'  # Change this in production

# Global variables for model and vectorizer
model = None
vectorizer = None

def load_model():
    """Load the trained model and vectorizer"""
    global model, vectorizer
    
    try:
        # Use relative paths for portability
        base_dir = os.path.dirname(os.path.abspath(__file__))
        model_path = os.path.join(base_dir, 'model', 'scam_model.pkl')
        vectorizer_path = os.path.join(base_dir, 'model', 'vectorizer.pkl')
        
        if os.path.exists(model_path) and os.path.exists(vectorizer_path):
            model = joblib.load(model_path)
            vectorizer = joblib.load(vectorizer_path)
            print("✅ Model loaded successfully!")
            return True
        else:
            print("❌ Model files not found!")
            return False
    except Exception as e:
        print(f"❌ Error loading model: {e}")
        return False

def preprocess_text(text):
    """Basic text preprocessing"""
    if not text:
        return ""
    
    # Convert to lowercase
    text = str(text).lower()
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

def extract_custom_features(texts):
    """Extract custom features for scam detection"""
    features = []
    
    for text in texts:
        text_lower = text.lower()
        feature_vector = []
        
        # Urgency indicators
        urgency_words = ['urgent', 'immediately', 'now', 'asap', 'quick', 'hurry', 'expire', 'limited time']
        urgency_count = sum(1 if word in text_lower else 0 for word in urgency_words)
        feature_vector.append(urgency_count)
        
        # Sensitive info requests
        sensitive_words = ['password', 'pin', 'otp', 'account', 'card', 'cvv', 'ssn', 'aadhar']
        sensitive_count = sum(1 if word in text_lower else 0 for word in sensitive_words)
        feature_vector.append(sensitive_count)
        
        # Threat indicators
        threat_words = ['suspend', 'block', 'close', 'terminate', 'freeze', 'cancel', 'legal action']
        threat_count = sum(1 if word in text_lower else 0 for word in threat_words)
        feature_vector.append(threat_count)
        
        # Prize/reward indicators
        prize_words = ['won', 'winner', 'prize', 'reward', 'lottery', 'congratulations', 'selected']
        prize_count = sum(1 if word in text_lower else 0 for word in prize_words)
        feature_vector.append(prize_count)
        
        # Authority claims
        authority_words = ['bank', 'government', 'official', 'department', 'cyber', 'tax', 'irs',
                          'microsoft', 'amazon', 'google', 'facebook', 'paypal', 'whatsapp']
        authority_count = sum(1 if word in text_lower else 0 for word in authority_words)
        feature_vector.append(authority_count)
        
        # Money indicators
        money_words = ['rs', 'rupees', 'pay', 'payment', 'fee', 'money', 'cash', 'amount', 'refund']
        money_count = sum(1 if word in text_lower else 0 for word in money_words)
        feature_vector.append(money_count)
        
        # Contact requests
        contact_words = ['call', 'click', 'visit', 'download', 'install', 'register', 'login']
        contact_count = sum(1 if word in text_lower else 0 for word in contact_words)
        feature_vector.append(contact_count)
        
        features.append(feature_vector)
    
    return np.array(features)

def transcribe_audio(audio_file):
    """Transcribe audio using Google Cloud Speech-to-Text (if credentials available)"""
    if not GOOGLE_SPEECH_AVAILABLE:
        return "Error: Google Cloud Speech-to-Text not available"
    
    try:
        # Read audio file content
        audio_content = audio_file.read()
        audio_file.seek(0)  # Reset file pointer for potential reuse
        
        # Initialize the client (this will fail if no credentials)
        try:
            client = speech.SpeechClient()
        except Exception as cred_error:
            print(f"Google Speech credentials not found: {cred_error}")
            return "Error: Google Cloud credentials not configured"
        
        # Convert audio to the right format if needed
        if PYDUB_AVAILABLE:
            try:
                # Try to convert audio to WAV format for better compatibility
                with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_wav:
                    # Load audio using pydub
                    audio = AudioSegment.from_file(io.BytesIO(audio_content))
                    
                    # Convert to mono, 16kHz (optimal for speech recognition)
                    audio = audio.set_channels(1).set_frame_rate(16000)
                    
                    # Export as WAV
                    audio.export(temp_wav.name, format="wav")
                    
                    # Read the converted audio
                    with open(temp_wav.name, 'rb') as f:
                        audio_content = f.read()
                    
                    # Clean up temp file
                    os.unlink(temp_wav.name)
                    
            except Exception as e:
                print(f"Audio conversion failed, using original: {e}")
        
        # Configure recognition
        audio = speech.RecognitionAudio(content=audio_content)
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=16000,
            language_code="en-US",
            # Enable automatic punctuation
            enable_automatic_punctuation=True,
        )
        
        # Perform the transcription
        response = client.recognize(config=config, audio=audio)
        
        # Extract transcript
        if response.results:
            transcript = ""
            for result in response.results:
                transcript += result.alternatives[0].transcript + " "
            return transcript.strip()
        else:
            return "Error: No speech detected in audio"
        
    except Exception as e:
        print(f"Google Speech API error: {e}")
        return f"Error: Google Speech API failed - {str(e)}"

def transcribe_audio_fallback(audio_file):
    """Fallback transcription using SpeechRecognition library with Google Web Speech API"""
    if not SPEECH_RECOGNITION_AVAILABLE:
        return "Error: No transcription libraries available"
    
    try:
        print("🔄 Using fallback transcription method...")
        
        # Initialize recognizer
        r = sr.Recognizer()
        
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_file:
            audio_file.seek(0)
            temp_file.write(audio_file.read())
            temp_file_path = temp_file.name
        
        try:
            # Convert to WAV if needed using pydub
            if PYDUB_AVAILABLE:
                try:
                    print("🔧 Converting audio format...")
                    audio = AudioSegment.from_file(temp_file_path)
                    # Convert to mono, 16kHz for better recognition
                    audio = audio.set_channels(1).set_frame_rate(16000)
                    # Ensure reasonable volume
                    audio = audio.normalize()
                    audio.export(temp_file_path, format="wav")
                    print("✅ Audio conversion successful")
                except Exception as conv_error:
                    print(f"⚠️ Audio conversion failed: {conv_error}")
            
            # Transcribe using speech_recognition
            with sr.AudioFile(temp_file_path) as source:
                # Adjust for ambient noise
                r.adjust_for_ambient_noise(source, duration=0.5)
                audio_data = r.record(source)
                
            print("🎯 Attempting transcription...")
            
            # Try Google Web Speech API (free, works without credentials)
            try:
                transcript = r.recognize_google(audio_data, language='en-US')
                print(f"✅ Google Web Speech successful: {transcript[:50]}...")
                return transcript
            except sr.UnknownValueError:
                print("⚠️ Google Web Speech could not understand audio")
                return "Error: Could not understand speech in audio file"
            except sr.RequestError as e:
                print(f"⚠️ Google Web Speech service error: {e}")
                
                # Try offline recognition as last resort
                try:
                    print("🔄 Trying offline recognition...")
                    transcript = r.recognize_sphinx(audio_data)
                    print(f"✅ Offline recognition successful: {transcript[:50]}...")
                    return transcript
                except:
                    return "Error: Could not transcribe audio - please try uploading a clearer audio file"
                    
        finally:
            # Clean up temp file
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
            
    except Exception as e:
        print(f"❌ Fallback transcription error: {e}")
        return f"Error: Transcription failed - {str(e)}"

def predict_scam(text):
    """Make prediction using the trained model"""
    if not model or not vectorizer:
        return {'error': 'Model not loaded'}
    
    try:
        # Preprocess text
        processed_text = preprocess_text(text)
        
        # Transform text using vectorizer
        X_tfidf = vectorizer.transform([processed_text])
        
        # Extract custom features
        custom_features = extract_custom_features([text])
        
        # Combine features
        X = np.hstack((X_tfidf.toarray(), custom_features))
        
        # Get prediction and probability
        prediction = model.predict(X)[0]
        probability = model.predict_proba(X)[0][1]  # Probability of being scam (0 to 1)
        
        # Convert to percentage (0 to 100)
        percentage = float(probability * 100)
        
        # Determine risk level
        if percentage >= 75:
            risk_level = "CRITICAL RISK"
        elif percentage >= 50:
            risk_level = "HIGH RISK"
        elif percentage >= 25:
            risk_level = "MEDIUM RISK"
        elif percentage >= 10:
            risk_level = "LOW RISK"
        else:
            risk_level = "MINIMAL RISK"
        
        return {
            'text': text,
            'scam_probability': round(percentage, 2),
            'raw_probability': round(probability, 4),
            'prediction': int(prediction),
            'risk_level': risk_level,
            'is_scam': bool(prediction == 1),
            'model_version': 'RandomForest_v1.0'
        }
        
    except Exception as e:
        return {'error': f'Prediction failed: {str(e)}'}

# =========================
# WEB ROUTES (HTML PAGES)
# =========================

@app.route('/')
def home():
    """Redirect to login page or dashboard if logged in"""
    if 'user_phone' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login')
def login():
    """Serve the login page"""
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    """Serve the main scam detection dashboard"""
    # Enforce authentication
    if 'user_phone' not in session:
        return redirect(url_for('login'))
    return render_template('index_enhanced.html')

# =========================
# API ROUTES (JSON)
# =========================

@app.route('/api/login', methods=['POST'])
def api_login():
    """Handle phone login and OTP"""
    try:
        data = request.get_json()
        phone = data.get('phone')
        otp = data.get('otp')
        
        if not phone:
            return jsonify({'error': 'Phone number required'}), 400
        
        if not otp:
            # Generate a random 6-digit OTP for demo
            import random
            generated_otp = str(random.randint(100000, 999999))
            
            # Store OTP in session for verification
            session[f'otp_{phone}'] = generated_otp
            
            # Print OTP to console for testing
            print(f"\n🔐 OTP GENERATED FOR TESTING:")
            print(f"📱 Phone: {phone}")
            print(f"🔑 OTP: {generated_otp}")
            print(f"⏰ Valid for this session\n")
            
            return jsonify({
                'success': True,
                'message': f'OTP sent to {phone}',
                'otp_sent': True
            })
        else:
            # Verify OTP against the generated one
            stored_otp = session.get(f'otp_{phone}')
            if stored_otp and otp == stored_otp:
                session['user_phone'] = phone
                # Clear the OTP after successful login
                session.pop(f'otp_{phone}', None)
                print(f"✅ Successful login for phone: {phone}")
                return jsonify({
                    'success': True,
                    'message': 'Login successful',
                    'redirect': '/dashboard'
                })
            else:
                print(f"❌ Invalid OTP attempt for phone: {phone}, provided: {otp}, expected: {stored_otp}")
                return jsonify({'error': 'Invalid or expired OTP'}), 400
                
    except Exception as e:
        return jsonify({'error': f'Login failed: {str(e)}'}), 500

@app.route('/api/logout', methods=['POST'])
def api_logout():
    """Handle user logout"""
    session.pop('user_phone', None)
    return jsonify({'success': True, 'redirect': '/login'})

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'model_loaded': model is not None and vectorizer is not None,
        'server': 'cybcup_web_app_v1.0'
    })

@app.route('/test-text', methods=['POST'])
def analyze_text_legacy():
    """Legacy endpoint for compatibility"""
    return analyze_text()

@app.route('/api/analyze-text', methods=['POST'])
def analyze_text():
    """Text analysis endpoint for the dashboard"""
    try:
        if not request.is_json:
            return jsonify({'error': 'Content-Type must be application/json'}), 400
        
        data = request.get_json()
        if not data or 'text' not in data:
            return jsonify({'error': 'Missing text field'}), 400
        
        text = str(data['text']).strip()
        if len(text) < 1:
            return jsonify({'error': 'Empty text'}), 400
        
        # Get prediction from model
        result = predict_scam(text)
        
        if 'error' in result:
            return jsonify(result), 500
        
        # Format for the enhanced UI
        formatted_result = {
            'transcript': text,
            'scam_probability': result['scam_probability'] / 100,  # Convert back to 0-1 for UI
            'risk_level': result['risk_level'],
            'recommendation': get_recommendation(result['scam_probability']),
            'warnings': get_warnings(text, result['scam_probability']),
            'analysis_details': get_analysis_details(text)
        }
        
        return jsonify(formatted_result)
        
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route('/api/analyze', methods=['POST'])
def analyze_audio():
    """Audio analysis endpoint with Google Cloud Speech-to-Text"""
    try:
        if 'audio' not in request.files:
            return jsonify({'error': 'No audio file provided'}), 400
        
        audio_file = request.files['audio']
        if audio_file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Transcribe audio using Google Cloud Speech
        transcript = transcribe_audio(audio_file)
        
        if not transcript or transcript.startswith('Error:'):
            # Fallback to SpeechRecognition if Google Cloud fails
            transcript = transcribe_audio_fallback(audio_file)
        
        if not transcript or transcript.startswith('Error:'):
            return jsonify({
                'error': transcript or 'Could not transcribe audio. Please try again or use text analysis.'
            }), 500
        
        # Now analyze the transcribed text using our scam detection model
        result = predict_scam(transcript)
        
        if 'error' in result:
            return jsonify({'error': f'Analysis failed: {result["error"]}'}), 500
        
        # Format for the enhanced UI
        formatted_result = {
            'transcript': transcript,
            'scam_probability': result['scam_probability'] / 100,  # Convert back to 0-1 for UI
            'risk_level': result['risk_level'],
            'recommendation': get_recommendation(result['scam_probability']),
            'warnings': get_warnings(transcript, result['scam_probability']),
            'analysis_details': get_analysis_details(transcript)
        }
        
        return jsonify(formatted_result)
        
    except Exception as e:
        return jsonify({'error': f'Audio analysis failed: {str(e)}'}), 500

def get_recommendation(probability):
    """Get recommendation based on scam probability"""
    if probability >= 75:
        return "🚨 HIGH ALERT: This appears to be a scam. Do not provide any personal information, money, or click any links. Block and report this communication immediately."
    elif probability >= 50:
        return "⚠️ WARNING: This message shows multiple scam indicators. Be very cautious. Verify through official channels before taking any action."
    elif probability >= 25:
        return "🟡 CAUTION: Some suspicious elements detected. Double-check the sender's identity through independent means before responding."
    else:
        return "✅ SAFE: This appears to be legitimate communication. However, always remain vigilant online."

def get_warnings(text, probability):
    """Get specific warnings based on text content"""
    warnings = []
    text_lower = text.lower()
    
    if probability >= 50:
        if any(word in text_lower for word in ['urgent', 'immediately', 'now']):
            warnings.append("⏰ Creates false urgency to pressure quick decisions")
        
        if any(word in text_lower for word in ['click', 'link', 'visit']):
            warnings.append("🔗 Contains suspicious links that may be malicious")
        
        if any(word in text_lower for word in ['password', 'pin', 'otp', 'cvv']):
            warnings.append("🔐 Requests sensitive personal or financial information")
        
        if any(word in text_lower for word in ['suspend', 'block', 'close']):
            warnings.append("😱 Uses fear tactics about account closure or suspension")
        
        if any(word in text_lower for word in ['prize', 'won', 'lottery']):
            warnings.append("🎁 Promises unrealistic rewards or prizes")
    
    return warnings

def get_analysis_details(text):
    """Get detailed analysis of the text"""
    text_lower = text.lower()
    
    scam_keywords = []
    critical_phrases = []
    patterns = []
    
    # Detect keywords
    keyword_categories = {
        'urgency': ['urgent', 'immediately', 'now', 'asap', 'quick'],
        'threats': ['suspend', 'block', 'close', 'terminate'],
        'rewards': ['won', 'prize', 'lottery', 'congratulations'],
        'financial': ['money', 'payment', 'fee', 'refund', 'bank'],
        'authority': ['government', 'official', 'department', 'tax']
    }
    
    for category, words in keyword_categories.items():
        found_words = [word for word in words if word in text_lower]
        if found_words:
            scam_keywords.extend(found_words)
    
    # Detect critical phrases
    critical_patterns = [
        'click here', 'verify account', 'confirm identity', 'update information',
        'account suspended', 'legal action', 'immediate payment'
    ]
    
    for pattern in critical_patterns:
        if pattern in text_lower:
            critical_phrases.append(pattern)
    
    # Detect patterns
    if re.search(r'\d{4}.*\d{4}.*\d{4}.*\d{4}', text):
        patterns.append('Credit card number pattern detected')
    
    if re.search(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', text):
        patterns.append('Contains external links')
    
    if len([word for word in text.split() if word.isupper()]) > 3:
        patterns.append('Excessive use of capital letters (urgency tactic)')
    
    return {
        'detected_keywords': scam_keywords[:10],  # Limit to top 10
        'critical_phrases': critical_phrases[:5],   # Limit to top 5
        'patterns': patterns[:5]                    # Limit to top 5
    }

if __name__ == '__main__':
    # Load model on startup
    if load_model():
        print("✅ Web application ready!")
        print("🔗 http://localhost:5002")
        print("📝 Login page: http://localhost:5002/login")
        print("📊 Dashboard: http://localhost:5002/dashboard")
        app.run(host='127.0.0.1', port=5002, debug=False)
    else:
        print("❌ Failed to load model. Server not started.")
        sys.exit(1)