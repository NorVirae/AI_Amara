from langchain_ollama import ChatOllama
import sys
import time
import threading
from elevenlabs.client import ElevenLabs
from elevenlabs import stream
from dotenv import load_dotenv
import warnings

import whisper
import sounddevice as sd
import numpy as np
import queue
import tempfile
import os
import wave

load_dotenv()

# Initialize a queue to hold audio data
audio_queue = queue.Queue()

# Parameters for audio recording
SAMPLE_RATE = 16000  # Whisper expects 16kHz
CHANNELS = 1  # Mono audio

llm = ChatOllama(model="llama3.1:8b",)

def loading_animation(stop_event):
    """Waiting for response"""
    animation = "|/-\\"
    idx = 0
    while not stop_event.is_set():
        sys.stdout.write("\rWaiting for Response " + animation[idx % len(animation)])
        sys.stdout.flush()
        idx += 1
        time.sleep(0.2)
    sys.stdout.write("\r" + " " * 30 + "\r")  # Clear the line


def record_audio(file_path, duration=10, sample_rate=48000):
    """
    Records audio from the microphone and saves it to a WAV file.
    """
    print(f"Recording for {duration} seconds...")
    
    # print(sd.query_devices())
    # Record audio
    audio_data = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=1, dtype="int16")
    sd.wait()  # Wait for the recording to complete
    
    # Save audio data to a WAV file
    with wave.open(file_path, "wb") as wf:
        wf.setnchannels(1)  # Mono audio
        wf.setsampwidth(2)  # 16-bit audio
        wf.setframerate(sample_rate)
        wf.writeframes(audio_data.tobytes())
    
    print(f"Audio saved to {file_path}")
    
def generateVoiceFromText():
    """
    Records audio, saves it to a file, and transcribes it using OpenAI Whisper.
    """
    # Temporary file to store the recorded audio
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_audio_file:
        audio_path = temp_audio_file.name

    # Record audio
    record_audio(audio_path, duration=10)  # Record 10 seconds of audio
    
    # Load Whisper model
    print("Loading Whisper model...")
    model = whisper.load_model("turbo")
    
    # Transcribe the audio
    print("Transcribing audio...", audio_path)
    result = model.transcribe(audio_path, fp16=False)
    
    # Print the transcription
    print("Transcription:")
    print(result["text"])
    return result["text"]


# def generateVoiceFromText():
    
#     model = whisper.load_model("tiny")
#     result = model.transcribe("audio.mp3", fp16=False)
#     print(result["text"])

def generateVoice(text):
    warnings.simplefilter("ignore", category=FutureWarning)
    client = ElevenLabs(
        api_key=os.environ["ELEVEN_LABS_API_KEY"],
    )
    audio = client.generate(
    text=text,
    voice="Brian",
    model="eleven_multilingual_v2",
    stream=True
    )
    
    stream(audio)

def main():
    print("Enter your prompts (type 'q' to quit):")
    while True:
        
        # stop_event = threading.Event()  # Event to stop the loading animation
        # generateVoiceFromText()
        text_input = generateVoiceFromText()
        print("")
        user_input = input("> ")  # Wait for user input
        if user_input.lower() == 'q':  # Check if the input is 'q' (case insensitive)
            print("Exiting the program. Goodbye!")
            break
             
             
        
        response = llm.invoke(text_input, stream=True, )
        # loader_thread = threading.Thread(target=generateVoice, args=(response.content,))
        # loader_thread.start()
        
        generateVoice(response.content)
       
        # for chunk in llm.stream(response.content):
        #     print(chunk.content, end="", flush=True)
        
        print("")
        print(response.content)
        # stop_event.set()  # Stop the animation
        # loader_thread.join()  # Wait for the loader thread to finish
        # print(response.content)
        # generateVoice(response.content)
            
        
        

if __name__ == "__main__":
    main()


