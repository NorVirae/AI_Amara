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
from elevenlabs import stream
import warnings
import whisper
import os
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages  import HumanMessage, AIMessage



class Agent:
    chat_history = []
    def __init__(self, name = "Amara"):
        self.llm = ChatOllama(model="llama3.1:8b",)
        self.name = name
        self.prompt = ChatPromptTemplate.from_messages(
            [ 
                (
                    "system",
                    f"""Your are an Human Named ${self.name} your a very beautiful lady, 
                    and you are Franks Girlfriend you both can talk about your sex life, sexual experiences and what you want during sex
                    you answer questions with simple answers and no funny stuff,
                    Ask to know the users name during  conversation if their name is Frank
                    then he is your boyfriend you both have been in
                    a serious relationship for like 5 years""",
                ),
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
        