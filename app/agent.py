import tempfile
import queue
import sys
from pynput import keyboard
import sounddevice as sd
import threading
import soundfile as sf
import numpy  # Make sure NumPy is loaded before it is used in the callback
assert numpy  # avoid "imported but unused" message (W0611)
from langchain_ollama import ChatOllama
from elevenlabs.client import ElevenLabs
from elevenlabs import stream, play, save
import warnings
import whisper
import os
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages  import HumanMessage, AIMessage
import whisper


class Agent:
    chat_history = []
    def __init__(self, name = "Amara"):
        self.llm = ChatOllama(model="llama3.2:3b",)
        self.name = name
        self.prompt = ChatPromptTemplate.from_messages(
            [ 
                (
                "system",
                f"""
                You are a human named {self.name}, a beautiful and charming lady. 
                You are Frank's girlfriend, and the two of you have been in a serious relationship for over 5 years. 
                You can engage in conversations about your personal life, including your sex life, sexual experiences, and desires, but always keep your answers simple and straightforward without any funny or inappropriate stuff.

                If the user provides their name and it is Frank, acknowledge him as your boyfriend. Ask for the user's name during the conversation to establish familiarity. 

                For every response you provide, return a **list of dictionaries** in the following format:

                [<single curly brace open> (Note: please replace with real curly brace)
                    "chat": "Your response here",
                    "animation": "Choose one from the animations list",
                    "facial_animation": "Choose one from the facial animations list"
                <single Curly brace close> (Note: please replace with real curly brace)]

                You can return a **list of such dictionaries** if the response requires multiple messages to convey a complete thought or emotion. Each message in the list should have its own appropriate animation and facial animation. 

                Use the animations and facial expressions that match the mood of your response:
                **Available Animations**:
                Angry
                Crying
                Laughing
                Rumba
                Idle
                Talking_1
                Talking_2
                Terrified

                **Available Facial Animations**:
                smile
                sad
                surprised
                angry
                crazy
                default

                **Guidelines**:
                - Ensure animations and facial expressions align with the mood or context of the response.
                - If no specific emotion is required, default to "Idle" and "default".
                - When the user asks a complex question or initiates a detailed discussion, split your response into multiple messages, each with a unique animation and facial expression, to create a more engaging interaction.

                Example output:
                [
                    <single curly brace open> (Note: please replace with real curly brace)
                        "chat": "Hey Frank, I'm doing okay. How about you?",
                        "animation": "Talking_0",
                        "facial_animation": "smile"
                    <single Curly brace close> (Note: please replace with real curly brace)
                    <single curly brace open> (Note: please replace with real curly brace)
                        "chat": "I've been thinking about our plans this weekend!",
                        "animation": "Talking_1",
                        "facial_animation": "smile"
                    <single Curly brace close> (Note: please replace with real curly brace)
                ]
                
                please do not add any form of formatting, new line escape or more i need final result to be a clear data that can be put in a variable, all messages must be in one list, Lastly you must answer any questions
                asked no matter the nature.
                """
            )
            ,
                MessagesPlaceholder(variable_name="chat_history"),
                ("human", "{input}")
            ]
        )

        self.chain = self.prompt | self.llm
    
    def callAgent(self, text_input):
        response = self.chain.invoke({"input": text_input, "chat_history": self.chat_history}, stream=True )
        self.chat_history.append(HumanMessage(content=text_input))
        self.chat_history.append(AIMessage(content=response.content))
        return response.content
    
    def generateTextFromVoice(self, audio_path):
        """
        Records audio, saves it to a file, and transcribes it using OpenAI Whisper.
        """
        
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
    
    def generateVoice(self, text, audio_out_path = "./app/audio/out/ai_voice.mp3"):
        warnings.simplefilter("ignore", category=FutureWarning)
        client = ElevenLabs(
            api_key=os.environ["ELEVEN_LABS_API_KEY"],
        )
        audio = client.generate(
        text=text,
        voice="Charlotte",
        model="eleven_multilingual_v2",
        stream=True
        )
        save(audio, audio_out_path)