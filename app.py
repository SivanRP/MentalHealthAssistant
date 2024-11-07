from flask import Flask, request, jsonify, render_template, Response
import sounddevice as sd
import numpy as np
import speech_recognition as sr
import requests
import json
from scipy.io import wavfile
import tempfile
import os
import pyttsx3
import threading
import cv2
from deepface import DeepFace

app = Flask(__name__)

# Initialize the TTS engine
engine = pyttsx3.init()

# Cerebras API details
api_key = 'csk-69599dcnpnw3k63k9w6de4yve4p3t8yh5kpwx2pk36dt63p2'
cerebras_url = 'https://api.cerebras.ai/v1/chat/completions'

# Global variable to store the last detected emotion
last_detected_emotion = None

def process_voice_input(recording_duration=5):
    fs = 44100  # Sample rate
    recording = sd.rec(int(recording_duration * fs), samplerate=fs, channels=1)
    sd.wait()

    # Normalize and save recording
    recording = np.int16(recording / np.max(np.abs(recording)) * 32767)
    with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_wav:
        wavfile.write(temp_wav.name, fs, recording)

    recognizer = sr.Recognizer()
    with sr.AudioFile(temp_wav.name) as source:
        audio = recognizer.record(source)

    os.unlink(temp_wav.name)  # Clean up the temporary file

    try:
        return recognizer.recognize_google(audio)
    except sr.UnknownValueError:
        return "Could not understand audio"
    except sr.RequestError as e:
        return f"Could not request results; {e}"

def generate_response(prompt, emotion=None):
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    emotion_context = f"The user's facial expression indicates they are feeling {emotion}. " if emotion else ""
    
    data = {
        'model': 'llama3.1-70b',
        'messages': [
            {'role': 'system', 'content': f'You are a mental health assistant. {emotion_context}Provide supportive and general advice, but always encourage seeking professional help for serious concerns.'},
            {'role': 'user', 'content': prompt}
        ]
    }
    
    response = requests.post(cerebras_url, json=data, headers=headers)
    
    if response.status_code == 200:
        result = response.json()
        if 'choices' in result and result['choices']:
            return result['choices'][0]['message']['content']
    
    return "I'm having trouble connecting to my brain right now."

def speak_text(text):
    """Convert text to speech in a separate thread."""
    def speak():
        engine.say(text)
        engine.runAndWait()
    
    # Create and start a new thread for TTS
    t = threading.Thread(target=speak)
    t.start()

def detect_emotion(frame):
    try:
        result = DeepFace.analyze(frame, actions=['emotion'], enforce_detection=False)
        return result[0]['dominant_emotion']
    except:
        return None

def gen_frames():
    global last_detected_emotion
    camera = cv2.VideoCapture(0)
    if not camera.isOpened():
        print("Error: Could not open camera.")
        return

    while True:
        success, frame = camera.read()
        if not success:
            print("Error: Could not read frame.")
            break
        else:
            try:
                emotion = detect_emotion(frame)
                if emotion:
                    last_detected_emotion = emotion
                ret, buffer = cv2.imencode('.jpg', frame)
                frame = buffer.tobytes()
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
            except Exception as e:
                print(f"Error processing frame: {str(e)}")
                break

    camera.release()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/resources')
def resources():
    return render_template('resources.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/get_current_emotion')
def get_current_emotion():
    global last_detected_emotion
    return jsonify({'emotion': last_detected_emotion or 'None'})

def add_disclaimer(response):
    disclaimer = "\n\nDisclaimer: This AI assistant provides general information and support. It is not a substitute for professional medical advice, diagnosis, or treatment. Always seek the advice of your physician or other qualified health provider with any questions you may have regarding a medical condition."
    return response + disclaimer

@app.route('/process_voice', methods=['POST'])
def handle_voice():
    text = process_voice_input()
    response = generate_response(text, last_detected_emotion)
    response_with_disclaimer = add_disclaimer(response)
    speak_text(response)
    return jsonify({'response': response_with_disclaimer})

@app.route('/process_text', methods=['POST'])
def handle_text():
    user_input = request.json.get('text')
    response = generate_response(user_input, last_detected_emotion)
    response_with_disclaimer = add_disclaimer(response)
    speak_text(response)
    return jsonify({'response': response_with_disclaimer})

@app.route('/process_emotion', methods=['POST'])
def process_emotion():
    emotion = request.json.get('emotion')
    prompt = f"The user appears to be feeling {emotion}. Provide a supportive response."
    response = generate_response(prompt, emotion)
    response_with_disclaimer = add_disclaimer(response)
    return jsonify({'response': response_with_disclaimer})

if __name__ == "__main__":
    app.run(debug=True)