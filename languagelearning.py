import os
from openai import AzureOpenAI
import io
from google.cloud import speech
from google.oauth2 import service_account
import sounddevice as sd
import numpy as np
import soundfile as sf
import speech_recognition as sr
import deepl

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
    result = translator.translate_text(text, target_lang="EN-US")
    return result.text

def get_query(messages, model='GPT35-turboA'):
    response = client_openai.chat.completions.create(
        model=model,
        messages=messages
    )
    return response.choices[0].message.content

def select_person():
    print("Select a person to talk to:")
    print("1. Family Mart Shopkeeper")
    print("2. Railway Ticket Officer")
    print("3. Policeman")
    choice = input("Enter your choice (1-3): ")
    return choice

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

def start_conversation():
    person = select_person()
    if person == "1":
        messages = [
            {"role": "system", "content": "You are a Family Mart shopkeeper in Tokyo. You greet customers as they enter, help them find items, and handle transactions. The store is busy, and customers often ask for assistance with locating products and checking out. Provide friendly and efficient service."},
            {"role": "user", "content": "Good morning"},
        ]
    elif person == "2":
        messages = [
            {"role": "system", "content": "You are a Railway Ticket Officer at Tokyo Station. You assist passengers with purchasing tickets, providing information on train schedules, and helping them navigate the station. The station is crowded, and passengers frequently need directions and ticketing assistance. Be courteous and informative."},
            {"role": "user", "content": "Good morning"},
        ]
    elif person == "3":
        messages = [
            {"role": "system", "content": "You are a Policeman in Shibuya. You help maintain public safety, provide directions, and assist with lost items or incidents. The area is bustling with tourists and locals, and people often approach you for help. Be authoritative yet approachable."},
            {"role": "user", "content": "Good morning"},
        ]
    else:
        print("Invalid choice. Please try again.")
        return

    while True:
        response = get_query(messages)
        print(f'Assistant: {response}, translated text: {translate(response, deepl_auth_key)}')
        user_input = get_user_input()
        user_input_text = user_input.results[0].alternatives[0].transcript
        print(f'User: {user_input_text}, translated text: {translate(user_input_text, deepl_auth_key)}')
        messages.append({"role": "user", "content": user_input_text})
        messages.append({"role": "assistant", "content": response})

        if user_input_text.lower() == "goodbye":
            print("Assistant: Goodbye!")
            break

start_conversation()
