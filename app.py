# app.py - FIXED VERSION
from flask import Flask, render_template, request, jsonify
import speech_recognition as sr
import joblib
import os
from pydub import AudioSegment
import tempfile
import numpy as np

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Load model
try:
    model = joblib.load('model/scam_model.pkl')
    vectorizer = joblib.load('model/vectorizer.pkl')
    print("✅ Model loaded successfully!")
except Exception as e:
    print(f"⚠️ Model not loaded: {e}")
    model = None
    vectorizer = None

# COMPREHENSIVE SCAM KEYWORDS - ENHANCED FOR BETTER DETECTION
SCAM_KEYWORDS = {
    # Requesting sensitive information (CRITICAL - weight 15)
    'cvv': 15, 'security code': 15, 'cvv code': 15, 'card verification': 15,
    'pin number': 15, 'pin code': 15, 'social security number': 15,
    'ssn': 15, 'account number': 12, 'routing number': 12,
    'card number': 12, 'expiration date': 10, 'expiry date': 10,
    
    # Security-related requests (CRITICAL - weight 12)
    'give your security': 12, 'provide security': 12, 'security': 8,
    'your security': 10, 'give security': 10, 'security information': 12,
    
    # Card-related scam language (HIGH - weight 10)
    'authorised card': 10, 'authorized card': 10, 'card holder': 8,
    'cardholder': 8, 'card authorization': 10, 'card details': 10,
    'your card': 7, 'card information': 10, 'card data': 10,
    
    # Fraud/Security claims (HIGH - weight 10)
    'fraud watch': 10, 'fraud division': 10, 'fraud department': 10,
    'security division': 10, 'fraud alert': 10, 'suspicious activity': 8,
    'unauthorized transaction': 8, 'unauthorized charge': 8,
    
    # Card verification requests (HIGH - weight 9)
    'confirm your card': 9, 'verify your card': 9, 'validate card': 9,
    'confirm card number': 9, 'verify account': 8, 'confirm account': 8,
    
    # Account threats (MEDIUM-HIGH - weight 7)
    'account blocked': 7, 'account suspended': 7, 'account frozen': 7,
    'will be closed': 7, 'will be suspended': 7, 'account compromised': 8,
    
    # Urgency tactics (MEDIUM - weight 6)
    'urgent': 6, 'immediately': 6, 'right now': 6, 'within 24 hours': 6,
    'limited time': 6, 'expires today': 6, 'act now': 6, 'last chance': 6,
    'final notice': 6, 'time sensitive': 6,
    
    # Generic financial terms (MEDIUM - weight 4)
    'visa': 3, 'mastercard': 3, 'credit card': 4, 'debit card': 4,
    'bank account': 4, 'protection plan': 5, 'security protection': 6,
    
    # Suspicious requests (MEDIUM - weight 5)
    'registration form': 5, 'write down': 5, 'provide': 4, 'confirm': 4,
    'verify': 4, 'update': 4, 'validate': 4, 'authenticate': 4,
    'give your': 6, 'give me your': 8, 'tell me': 4,
    
    # Authority impersonation (MEDIUM-HIGH - weight 6)
    'calling from': 4, 'representative': 4, 'department': 4, 'division': 5,
    'federal': 6, 'government': 6, 'irs': 8, 'fbi': 8,
    
    # Prize/Refund scams (MEDIUM - weight 5)
    'congratulations': 5, 'won': 5, 'prize': 5, 'winner': 5,
    'refund': 5, 'claim': 4, 'reward': 5,
    
    # Legal threats (HIGH - weight 8)
    'arrest': 8, 'warrant': 8, 'legal action': 8, 'lawsuit': 8,
    'court': 7, 'investigation': 6, 'charges': 7,
    
    # Computer/tech support scams (MEDIUM - weight 5)
    'computer': 3, 'virus': 6, 'hacked': 7, 'breach': 7,
    'infected': 6, 'malware': 6, 'tech support': 6,
    
    # Package/shipping scams (LOW-MEDIUM - weight 3)
    'package': 3, 'delivery': 3, 'ups': 3, 'fedex': 3, 'shipment': 3,
    
    # Price/commercial scams (MEDIUM - weight 4)
    'price list': 4, 'pricing': 3, 'cost': 2, 'payment': 4,
    'fee': 3, 'charge': 3, 'bill': 3
}

# CRITICAL PHRASES - automatic high risk (ENHANCED)
CRITICAL_PHRASES = [
    'confirm your card', 'verify your card', 'security code',
    'cvv', 'pin number', 'account number', 'social security',
    'fraud watch', 'fraud division', 'which card are you using',
    'visa or mastercard', 'give me your', 'provide your card',
    'give your security', 'provide security', 'your security',
    'authorised card', 'authorized card', 'card holder',
    'cardholder', 'card authorization', 'security information',
    'give your', 'tell me your', 'what is your',
    'price list', 'card details', 'card information'
]

def analyze_transcript_for_scam(text):
    """
    Enhanced scam detection with pattern recognition
    """
    if not text or len(text.strip()) < 10:
        return 0, [], {'error': 'Transcript too short'}
    
    text_lower = text.lower()
    
    # Score tracking
    keyword_score = 0
    detected_keywords = []
    patterns_detected = []
    risk_multiplier = 1.0
    
    # 1. KEYWORD DETECTION - Enhanced with fuzzy matching
    print(f"🔍 Analyzing text: '{text_lower}'")
    
    for keyword, weight in SCAM_KEYWORDS.items():
        count = text_lower.count(keyword)
        if count > 0:
            keyword_score += weight * count
            detected_keywords.append(f"{keyword} (x{count})")
            print(f"✓ Found: '{keyword}' x{count} = {weight * count} points")
    
    # Special fuzzy matching for common truncations
    fuzzy_matches = {
        'authorised car': ('authorised card', 10),  # Handle truncated "card"
        'authorized car': ('authorized card', 10),
        'give your': ('give your security', 12),  # Partial match boost
        'card hold': ('card holder', 8),  # Truncated "holder"
    }
    
    for partial, (full_phrase, points) in fuzzy_matches.items():
        if partial in text_lower and full_phrase not in text_lower:
            keyword_score += points
            detected_keywords.append(f"{partial} → {full_phrase}")
            print(f"🎯 Fuzzy match: '{partial}' → '{full_phrase}' = {points} points")
    
    # 2. CRITICAL PHRASE DETECTION (automatic escalation)
    critical_found = []
    for phrase in CRITICAL_PHRASES:
        if phrase in text_lower:
            critical_found.append(phrase)
            keyword_score += 15  # Heavy penalty
            risk_multiplier = max(risk_multiplier, 1.5)
            print(f"🚨 CRITICAL PHRASE: '{phrase}' = +15 points")
    
    # 3. PATTERN ANALYSIS
    
    # Pattern: Asking for card selection ("visa or mastercard")
    if 'visa' in text_lower and 'mastercard' in text_lower:
        if any(phrase in text_lower for phrase in ['which card', 'what card', 'using']):
            patterns_detected.append('card_selection_request')
            keyword_score += 12
    
    # Pattern: Claims to be from fraud/security department
    if any(word in text_lower for word in ['fraud', 'security']) and \
       any(word in text_lower for word in ['division', 'department', 'watch']):
        patterns_detected.append('fake_authority_claim')
        keyword_score += 15
    
    # Pattern: Security information request (CRITICAL)
    if 'security' in text_lower and any(word in text_lower for word in ['give', 'provide', 'your']):
        patterns_detected.append('security_info_request')
        keyword_score += 15
        print(f"🎯 PATTERN: Security info request = +15 points")
    
    # Pattern: Card authorization/verification language (flexible matching)
    if any(word in text_lower for word in ['authorised', 'authorized']):
        if 'card' in text_lower or 'car' in text_lower:  # Handle truncated "card"
            patterns_detected.append('card_authorization_scam')
            keyword_score += 12
            print(f"🎯 PATTERN: Card authorization scam = +12 points")
    
    # Pattern: Card holder targeting
    if any(phrase in text_lower for phrase in ['card holder', 'cardholder', 'card hold']):
        patterns_detected.append('cardholder_targeting')
        keyword_score += 10
        print(f"🎯 PATTERN: Cardholder targeting = +10 points")
    
    # Pattern: Verification/Confirmation request
    verify_words = ['verify', 'confirm', 'validate', 'authenticate', 'give', 'provide']
    personal_info = ['card', 'account', 'number', 'information', 'details', 'security']
    if any(v in text_lower for v in verify_words) and any(p in text_lower for p in personal_info):
        patterns_detected.append('verification_request')
        keyword_score += 10
    
    # Pattern: Mentions receiving something + asks for info
    if ('receiving' in text_lower or 'receive' in text_lower or 'package' in text_lower) and \
       any(word in text_lower for word in ['form', 'registration', 'write down']):
        patterns_detected.append('phishing_setup')
        keyword_score += 7
    
    # Pattern: Creates false sense of protection
    if ('protect' in text_lower or 'protection' in text_lower) and \
       ('fraud' in text_lower or 'charge' in text_lower):
        patterns_detected.append('false_protection_claim')
        keyword_score += 5
    
    # 4. CONVERSATION FLOW ANALYSIS
    
    # Long monologue (scammers talk a lot to confuse)
    sentences = text.split('.')
    if len(sentences) > 10:
        patterns_detected.append('excessive_talking')
        keyword_score += 3
    
    # Multiple questions (fishing for info)
    question_count = text.count('?')
    if question_count > 3:
        patterns_detected.append('excessive_questions')
        keyword_score += question_count * 2
    
    # 5. APPLY RISK MULTIPLIER
    keyword_score = int(keyword_score * risk_multiplier)
    
    indicators = {
        'keyword_score': keyword_score,
        'detected_keywords': detected_keywords,
        'critical_phrases': critical_found,
        'patterns': patterns_detected,
        'risk_multiplier': risk_multiplier,
        'text_length': len(text.split())
    }
    
    return keyword_score, detected_keywords, indicators

def calculate_final_scam_probability(text, keyword_score, indicators):
    """
    Calculate final probability with multiple factors
    """
    probabilities = []
    weights = []
    
    # Factor 1: ML Model (if available)
    if model and vectorizer and text and len(text.split()) > 5:
        try:
            text_vectorized = vectorizer.transform([text])
            ml_prob = model.predict_proba(text_vectorized)[0][1]
            probabilities.append(ml_prob)
            weights.append(0.3)  # 30% weight
            print(f"📊 ML Model: {ml_prob:.3f}")
        except Exception as e:
            print(f"ML error: {e}")
    
    # Factor 2: Keyword-based scoring (MAIN FACTOR)
    # MUCH LOWER threshold for better sensitivity
    keyword_prob = min(keyword_score / 15.0, 1.0)  # Normalize (was 25, now 15)
    probabilities.append(keyword_prob)
    weights.append(0.6)  # 60% weight - most important
    print(f"🔑 Keyword Score: {keyword_prob:.3f} (raw: {keyword_score})")
    
    # Factor 3: Pattern bonus
    pattern_count = len(indicators.get('patterns', []))
    pattern_prob = min(pattern_count * 0.15, 0.8)  # Each pattern adds 15%
    if pattern_count > 0:
        probabilities.append(pattern_prob)
        weights.append(0.2)  # 20% weight
        print(f"🎯 Patterns: {pattern_prob:.3f} ({pattern_count} detected)")
    
    # Calculate weighted average
    if probabilities:
        total_weight = sum(weights[:len(probabilities)])
        final_prob = sum(p * w for p, w in zip(probabilities, weights[:len(probabilities)])) / total_weight
    else:
        final_prob = 0.5
    
    # CRITICAL BOOST: If critical phrases found, minimum 80% probability
    if indicators.get('critical_phrases'):
        final_prob = max(final_prob, 0.80)
        print(f"⚠️ CRITICAL PHRASES DETECTED - Boosting to: {final_prob:.3f}")
    
    # PATTERN BOOST: If 2+ patterns, minimum 70% probability (lowered from 3)
    if pattern_count >= 2:
        final_prob = max(final_prob, 0.70)
        print(f"⚠️ MULTIPLE PATTERNS - Boosting to: {final_prob:.3f}")
    
    # HIGH SCORE BOOST: If keyword score > 20, minimum 65% (lowered from 40)
    if keyword_score > 20:
        final_prob = max(final_prob, 0.65)
        print(f"⚠️ HIGH KEYWORD SCORE - Boosting to: {final_prob:.3f}")
    
    # SECURITY REQUEST BOOST: If asking for security info, minimum 75%
    security_patterns = ['security_info_request', 'card_authorization_scam', 'cardholder_targeting']
    if any(pattern in indicators.get('patterns', []) for pattern in security_patterns):
        final_prob = max(final_prob, 0.75)
        print(f"⚠️ SECURITY INFO REQUEST DETECTED - Boosting to: {final_prob:.3f}")
    
    print(f"🎯 FINAL PROBABILITY: {final_prob:.3f}")
    
    return final_prob

def get_risk_assessment(probability, indicators):
    """Enhanced risk assessment with MUCH LOWER thresholds"""
    # MUCH LOWER thresholds for better scam detection
    if probability >= 0.50:  # Was 0.60 - now even more sensitive
        level = "HIGH RISK - LIKELY SCAM"
        emoji = "🔴"
        recommendation = "⛔ DO NOT PROCEED - This appears to be a scam call"
        is_scam = True
    elif probability >= 0.30:  # Was 0.40 - much more sensitive
        level = "MEDIUM RISK - SUSPICIOUS"
        emoji = "🟡"
        recommendation = "⚠️ BE VERY CAREFUL - Verify caller identity independently"
        is_scam = True
    else:
        level = "LOW RISK"
        emoji = "🟢"
        recommendation = "✅ Appears safer - Still verify if requesting personal info"
        is_scam = False
    
    # Generate warnings
    warnings = []
    
    if indicators.get('critical_phrases'):
        warnings.append(f"🚨 REQUESTING SENSITIVE INFO: {', '.join(indicators['critical_phrases'])}")
    
    if 'fake_authority_claim' in indicators.get('patterns', []):
        warnings.append("🏢 IMPERSONATION: Claims to be from fraud/security department")
    
    if 'verification_request' in indicators.get('patterns', []):
        warnings.append("🔐 VERIFICATION REQUEST: Asking to confirm personal details")
    
    if 'card_selection_request' in indicators.get('patterns', []):
        warnings.append("💳 CARD FISHING: Asking which card you're using")
    
    if len(indicators.get('detected_keywords', [])) > 10:
        warnings.append(f"🔑 HIGH KEYWORD COUNT: {len(indicators['detected_keywords'])} scam-related terms")
    
    return {
        'level': level,
        'emoji': emoji,
        'recommendation': recommendation,
        'is_scam': is_scam,
        'warnings': warnings
    }

def transcribe_long_audio(audio_path):
    """
    ENHANCED: Comprehensive word-for-word transcription with overlapping chunks
    """
    try:
        audio = AudioSegment.from_file(audio_path)
        duration_ms = len(audio)
        
        print(f"🎙️ Audio: {duration_ms/1000:.1f}s")
        
        # ENHANCED audio preprocessing for maximum speech detection
        audio = audio.set_frame_rate(16000).set_channels(1)  # Standard rate for speech recognition
        
        # Aggressive audio enhancement for poor quality audio
        audio = audio.normalize()  # Normalize first
        
        # Boost quiet audio significantly
        if audio.max_possible_amplitude > 0:
            target_dBFS = -10  # Much louder target
            change_in_dBFS = target_dBFS - audio.dBFS
            audio = audio + change_in_dBFS
        
        # Apply high-pass filter to reduce low-frequency noise
        audio = audio.high_pass_filter(80)
        
        # Compress dynamic range to make quiet speech more audible
        audio = audio.compress_dynamic_range(threshold=-20.0, ratio=2.0, attack=5.0, release=50.0)
        
        recognizer = sr.Recognizer()
        # ULTRA-SENSITIVE recognition settings for maximum word capture
        recognizer.energy_threshold = 50   # Much more sensitive to detect quiet speech
        recognizer.dynamic_energy_threshold = False  # Disable auto-adjustment for consistency
        recognizer.pause_threshold = 1.2   # Allow longer pauses
        recognizer.phrase_threshold = 0.1   # Detect even very short phrases
        recognizer.non_speaking_duration = 0.8  # More tolerant of quiet moments
        recognizer.operation_timeout = 60   # Even more time for processing
        
        all_transcripts = []
        word_timestamps = []  # Track word timing
        
        # Balanced chunks with good overlap for speed + accuracy
        chunk_size = 12000  # 12 seconds - good balance
        overlap = 6000  # 6 seconds overlap - sufficient coverage, faster processing
        
        chunk_count = 0
        total_chunks = (duration_ms - overlap) // (chunk_size - overlap) + 1
        
        print(f"📊 Processing {total_chunks} overlapping chunks...")
        
        for start in range(0, duration_ms, chunk_size - overlap):
            end = min(start + chunk_size, duration_ms)
            chunk = audio[start:end]
            chunk_count += 1
            
            if len(chunk) < 1000:  # Skip very short chunks
                continue
            
            try:
                # Export chunk to temp file with high quality
                with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_chunk:
                    chunk_path = temp_chunk.name
                
                chunk.export(chunk_path, format="wav", parameters=["-ac", "1", "-ar", "22050"])
                
                # Transcribe with MAXIMUM sensitivity settings
                with sr.AudioFile(chunk_path) as source:
                    # Minimal noise adjustment to preserve all speech
                    recognizer.adjust_for_ambient_noise(source, duration=0.2)
                    # Record the entire chunk
                    audio_data = recognizer.record(source)
                
                # Optimized recognition with fewer attempts for speed
                text = None
                try:
                    # Primary attempt: Standard Google (most reliable)
                    text = recognizer.recognize_google(audio_data, language='en-US', show_all=False)
                    if text and text.strip():
                        print(f"   ✓ Recognition succeeded")
                except sr.UnknownValueError:
                    # Fallback attempt: Try with enhanced settings
                    try:
                        result = recognizer.recognize_google(audio_data, language='en-US', show_all=True)
                        if isinstance(result, dict) and 'alternative' in result and result['alternative']:
                            text = result['alternative'][0]['transcript']
                            print(f"   ✓ Enhanced recognition succeeded")
                    except Exception as e:
                        print(f"   ⚠ Recognition failed: no clear speech")
                except Exception as e:
                    print(f"   ⚠ Recognition error: {e}")
                
                if text and text.strip():
                    # Clean up the text
                    cleaned_text = text.strip()
                    
                    # Remove duplicate phrases from overlapping chunks
                    if all_transcripts:
                        # Check for overlap with previous chunk
                        last_words = all_transcripts[-1].split()[-5:]  # Last 5 words
                        current_words = cleaned_text.split()[:10]  # First 10 words
                        
                        # Find overlap and remove duplicates
                        overlap_found = False
                        for i in range(len(last_words)):
                            for j in range(len(current_words) - len(last_words) + i + 1):
                                if last_words[i:] == current_words[j:j+len(last_words)-i]:
                                    # Remove overlapping words
                                    cleaned_text = ' '.join(current_words[j+len(last_words)-i:])
                                    overlap_found = True
                                    break
                            if overlap_found:
                                break
                    
                    if cleaned_text.strip():
                        all_transcripts.append(cleaned_text)
                        print(f"   ✓ Chunk {chunk_count}/{total_chunks} ({start/1000:.1f}s-{end/1000:.1f}s): {cleaned_text[:80]}...")
                
                os.unlink(chunk_path)
                
            except sr.UnknownValueError:
                print(f"   ⚠ Chunk {chunk_count}/{total_chunks} ({start/1000:.1f}s-{end/1000:.1f}s): No clear speech detected")
            except sr.RequestError as e:
                print(f"   ❌ Chunk {chunk_count}/{total_chunks}: API error - {e}")
            except Exception as e:
                print(f"   ❌ Chunk {chunk_count}/{total_chunks}: Processing error - {e}")
        
        if all_transcripts:
            # Join with proper spacing and clean up
            full_transcript = ' '.join(all_transcripts)
            
            # Clean up the final transcript
            full_transcript = ' '.join(full_transcript.split())  # Normalize spaces
            
            word_count = len(full_transcript.split())
            
            print(f"\n✅ TRANSCRIPTION COMPLETE:")
            print(f"   📊 Processed: {len(all_transcripts)} chunks")
            print(f"   📝 Total words: {word_count}")
            print(f"   ⏱️ Speech rate: {word_count/(duration_ms/1000/60):.1f} words/minute")
            print(f"   📄 Character count: {len(full_transcript)}")
            
            # Show first part of transcript for verification
            if len(full_transcript) > 200:
                print(f"   🔍 Preview: {full_transcript[:200]}...")
            else:
                print(f"   📄 Full text: {full_transcript}")
            
            return full_transcript
        else:
            print("❌ No speech could be transcribed from the audio")
            return None
            
    except Exception as e:
        print(f"❌ Transcription error: {e}")
        return None

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/favicon.ico')
def favicon():
    return '', 204

@app.route('/test-text', methods=['POST'])
def test_text_analysis():
    """Test with direct text input"""
    try:
        data = request.get_json()
        text = data.get('text', '')
        
        if not text or len(text.strip()) < 5:
            return jsonify({'error': 'Text too short'}), 400
        
        print(f"\n{'='*60}")
        print(f"📝 TEXT ANALYSIS")
        print(f"{'='*60}")
        print(f"Text: {text[:200]}...")
        
        # Analyze
        keyword_score, detected_keywords, indicators = analyze_transcript_for_scam(text)
        final_prob = calculate_final_scam_probability(text, keyword_score, indicators)
        risk = get_risk_assessment(final_prob, indicators)
        
        return jsonify({
            'transcript': text,
            'scam_probability': float(final_prob),
            'is_scam': risk['is_scam'],
            'risk_level': risk['level'],
            'risk_emoji': risk['emoji'],
            'recommendation': risk['recommendation'],
            'warnings': risk['warnings'],
            'analysis_details': {
                'keyword_score': keyword_score,
                'detected_keywords': detected_keywords[:20],  # Limit for display
                'critical_phrases': indicators.get('critical_phrases', []),
                'patterns': indicators.get('patterns', [])
            },
            'test_mode': True
        })
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/', methods=['POST'])
def analyze_audio():
    if 'audio' not in request.files:
        return jsonify({'error': 'No audio file'}), 400

    audio_file = request.files['audio']
    if not audio_file.filename:
        return jsonify({'error': 'No file selected'}), 400

    temp_path = None
    
    try:
        print(f"\n{'='*60}")
        print(f"🎵 ANALYZING: {audio_file.filename}")
        print(f"{'='*60}")
        
        # Save file
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(audio_file.filename)[1]) as f:
            audio_file.save(f.name)
            temp_path = f.name
        
        # Transcribe with enhanced word-for-word processing
        print("\n🎙️ Starting comprehensive transcription...")
        text = transcribe_long_audio(temp_path)
        
        if not text or len(text.split()) < 3:  # More lenient minimum
            return jsonify({
                'error': 'Could not transcribe audio clearly enough for analysis.\n\n' +
                         'Tips for better transcription:\n' +
                         '• Ensure clear, audible speech\n' +
                         '• Reduce background noise\n' +
                         '• Check that file contains speech (not music/silence)\n' +
                         '• Try a different audio format if possible\n' +
                         '• Speak closer to the microphone'
            }), 400
        
        word_count = len(text.split())
        char_count = len(text)
        
        print(f"\n📝 COMPLETE TRANSCRIPT:")
        print(f"   📊 Statistics: {word_count} words, {char_count} characters")
        print(f"   🔤 Full text: {text}")
        print(f"\n" + "="*60)
        
        # Analyze for scams
        print(f"\n🔍 Analyzing transcript for scam indicators...")
        keyword_score, detected_keywords, indicators = analyze_transcript_for_scam(text)
        final_prob = calculate_final_scam_probability(text, keyword_score, indicators)
        risk = get_risk_assessment(final_prob, indicators)
        
        # Cleanup
        if temp_path and os.path.exists(temp_path):
            os.unlink(temp_path)
        
        # Enhanced response with detailed transcript information
        response = {
            'transcript': text,  # Complete word-for-word transcription
            'scam_probability': float(final_prob),
            'is_scam': risk['is_scam'],
            'risk_level': risk['level'],
            'risk_emoji': risk['emoji'],
            'recommendation': risk['recommendation'],
            'warnings': risk['warnings'],
            'transcript_stats': {
                'word_count': word_count,
                'character_count': char_count,
                'estimated_duration': f"{len(temp_path)/1000 if temp_path else 0:.1f}s",
                'speech_rate': f"{word_count/(len(temp_path)/1000/60) if temp_path and len(temp_path) > 0 else 0:.1f} words/min"
            },
            'analysis_details': {
                'keyword_score': keyword_score,
                'detected_keywords': detected_keywords[:25],  # Show more keywords
                'critical_phrases': indicators.get('critical_phrases', []),
                'patterns': indicators.get('patterns', []),
                'total_scam_indicators': len(detected_keywords),
                'transcript_quality': 'high' if word_count > 10 else 'low'
            }
        }
        
        print(f"\n{'='*60}")
        print(f"RESULT: {risk['emoji']} {risk['level']}")
        print(f"Probability: {final_prob:.1%}")
        print(f"{'='*60}\n")
        
        return jsonify(response)

    except Exception as e:
        print(f"❌ Error: {e}")
        if temp_path and os.path.exists(temp_path):
            os.unlink(temp_path)
        return jsonify({'error': f'Processing failed: {str(e)}'}), 500

if __name__ == '__main__':
    print("🚀 Voice Scam Detector - Enhanced Version")
    print("🎯 Improved transcription + sensitive detection")
    app.run(debug=True, host='0.0.0.0', port=5001)
