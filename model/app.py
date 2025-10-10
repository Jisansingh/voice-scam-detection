from flask import Flask, render_template, request, jsonify
import speech_recognition as sr
from model.scam_detector import analyze_text
from pydub import AudioSegment
import os

app = Flask(__name__)

# Folder to temporarily store uploaded audio files
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/analyze_audio', methods=['POST'])
def analyze_audio():
    if 'audio' not in request.files:
        return jsonify({'error': 'No audio file provided'}), 400

    audio_file = request.files['audio']
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], audio_file.filename)
    audio_file.save(filepath)

    # Convert to WAV format if needed
    if not filepath.lower().endswith('.wav'):
        sound = AudioSegment.from_file(filepath)
        filepath = filepath.rsplit('.', 1)[0] + '.wav'
        sound.export(filepath, format='wav')

    recognizer = sr.Recognizer()
    with sr.AudioFile(filepath) as source:
        audio_data = recognizer.record(source)

    try:
        text = recognizer.recognize_google(audio_data)
    except Exception as e:
        return jsonify({'error': f'Speech recognition failed: {str(e)}'}), 500

    scam_score, reason = analyze_text(text)

    # Clean up uploaded file
    os.remove(filepath)

    return jsonify({
        'transcript': text,
        'score': scam_score,
        'reason': reason
    })

if __name__ == '__main__':
    app.run(debug=True)
