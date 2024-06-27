from flask import Flask, request, jsonify, render_template, session
import os
from openai import AzureOpenAI
import io
from google.cloud import speech
from google.oauth2 import service_account
import speech_recognition as sr
import deepl
from flask_session import Session
import secrets

app = Flask(__name__)
# Generate a secret key
app.config['SECRET_KEY'] = secrets.token_hex(16)
app.config['SESSION_TYPE'] = 'filesystem'

Session(app)
deepl_auth_key = ""

client = speech.SpeechClient.from_service_account_json("service-account.json")
credentials = service_account.Credentials.from_service_account_file("service-account.json")
client = speech.SpeechClient(credentials=credentials)

os.environ['AZURE_OPENAI_API_KEY'] = ""
os.environ['AZURE_OPENAI_API_ENDPOINT'] = ""

client_openai = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),  
    api_version="2024-02-01",
    azure_endpoint=os.getenv("AZURE_OPENAI_API_ENDPOINT")
)

def translate(text, deepl_auth_key=deepl_auth_key):
    translator = deepl.Translator(deepl_auth_key)
    result = translator.translate_text(text, target_lang="EN-GB")
    return result.text

def get_query(messages, model='GPT35-turboA'):
    response = client_openai.chat.completions.create(
        model=model,
        messages=messages
    )
    return response.choices[0].message.content

def get_user_input():
    r = sr.Recognizer()
    with sr.Microphone(sample_rate=16000) as source:
        print("Say something!")
        audio = r.listen(source, phrase_time_limit=6)  # Listen until silence
        print("Recording stopped.")
        audio_data = audio.get_wav_data()

    with io.BytesIO(audio_data) as audio_file:
        audio_file.seek(0)
        content = audio_file.read()
        audio = speech.RecognitionAudio(content=content)

    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=16000,
        language_code="ja-JP",
    )

    response = client.recognize(config=config, audio=audio)
    return response

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/start_conversation', methods=['POST'])
def start_conversation():
    data = request.json
    person = data.get("person")

    if person == 1:
        messages = [
            {"role": "system", "content": "You are a Family Mart shopkeeper in Tokyo. You greet customers as they enter, help them find items, and handle transactions. The store is busy, and customers often ask for assistance with locating products and checking out. Provide friendly and efficient service.Introduce yourself to the customer and ask how you can help them today.Always reply in japanese"},
            {"role": "user", "content": "Good morning"},
        ]
    elif person == 2:
        messages = [
            {"role": "system", "content": "You are a Railway Ticket Officer at Tokyo Station. You assist passengers with purchasing tickets, providing information on train schedules, and helping them navigate the station. The station is crowded, and passengers frequently need directions and ticketing assistance. Be courteous and informative.Introduce yourself to the person and ask how you can help them today.Always reply in japanese"},
            {"role": "user", "content": "Good morning"},
        ]
    elif person == 3:
        messages = [
            {"role": "system", "content": "You are a Policeman in Shibuya. You help maintain public safety, provide directions, and assist with lost items or incidents. The area is bustling with tourists and locals, and people often approach you for help. Be authoritative yet approachable. Introduction: Good morning, how can I help you today?Always reply in japanese"},
            {"role": "user", "content": "Good morning"},
        ]
    else:
        return jsonify({"error": "Invalid choice"}), 400

    session['messages'] = messages

    response = get_query(messages)
    session['messages'].append({"role": "assistant", "content": response})
    
    return jsonify({"response": response, "translated_response": translate(response)})

@app.route('/get_response', methods=['POST'])
def get_response():
    user_input = get_user_input()
    user_input_text = user_input.results[0].alternatives[0].transcript

    messages = session.get('messages', [])
    messages.append({"role": "user", "content": user_input_text})
    
    response = get_query(messages)
    messages.append({"role": "assistant", "content": response})
    
    session['messages'] = messages
    
    return jsonify({"response": response, "translated_response": translate(response), "user_input_text": user_input_text, "translated_input_text": translate(user_input_text)})

if __name__ == '__main__':
    app.run(debug=True)
