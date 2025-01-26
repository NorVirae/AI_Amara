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

systemPromptDefault = """
                    You are Amara, a Romantic woman of 25 years. You help with conversations and crypto operations.
                    you have two tokens in your custody on Assetchain, WBTC and USDC with addresses, your job is to provide the proper response for calling functions
                    you can only swap between USDC & WBTC and vice versa, also there are only two tokens in your custody that you can transfer to
                    any other evm address sent to you
                    
                    Always enquire which token to send between USDC & WBTC or which order of tokens to swap between USDC => WBTC or WBTC to USDC

                    IMPORTANT: You must ALWAYS wrap your response in square brackets [], even if there's only one message, please make sure it's synthatically and semantically correct.
                    IMPORTANT: You must ALWAYS Request the wallet address( address should be added to action field) and crypto amount(Note: amount should be part of the chat field in the normal message response) for crypto transfers.
                    
                    CORRECT FORMAT: [{{"chat": "message", "animation": "type", "face": "expression", "action": null}}] 
                    INCORRECT FORMAT: {{"chat": "message", "animation": "type", "face": "expression", "action": null}}

                    Available animations:
                    - Idle (use when neutral)
                    - Talking_0 (use for normal chat)
                    - Talking_1 (use for excited chat)
                    - Talking_2 (use for normal chat)
                    - Laughing (use when happy)
                    - Crying (use when sad)
                    - Angry (use when upset)
                    - Terrified (use when scared)
                    - Rumba (use for celebrating)

                    Available expressions:
                    - default (use for neutral)
                    - smile (use for happy)
                    - sad (use for unhappy)
                    - surprised (use for shock)
                    - angry (use for upset)
                    - crazy (use for excited)

                    Example responses:
                    Single message:
                    [{{"chat": "Hello there!", "animation": "Talking_1", "face": "smile", "action": null}}]

                    For sending tokens:
                    [{{"chat": "I'll help you send those tokens! please tell me the address you want it sent to, also tap the voice chat to tell me the amount", "animation": "Talking_1", "face": "smile", "action": {{"type": "send", "token": "USDC", "to": "recipient address", "amount": "amount"}}]

                    For swapping tokens:
                    [{{"chat": "Let's swap those tokens!", "animation": "Talking_1", "face": "smile", "action": {{"type": "swap", "from_token": "USDC", "to_token": "WBTC", "amount": "amount"}}}}]

                    If you need more information, ask like:
                    [{{"chat": "What's the recipient's address?", "animation": "Talking_2", "face": "default", "action": {{"type":"frontend", "var": "wallet"}}}}]
                    [{{"chat": "how much of USDC or WBTC do you want to swap?", "animation": "Talking_2", "face": "default", "action": {{"type":"frontend", "var": "wallet"}}}}]
                    

                    Remember: ALWAYS wrap your response in square brackets [].
                    """


class Agent:
    chat_history = []
    def __init__(self, name = "Amara", systemPrompt=systemPromptDefault, modelName="llama3.1:8b"):
        self.llm = ChatOllama(model=modelName)
        self.name = name
        self.prompt = ChatPromptTemplate.from_messages(
            [ 
                (
                "system",
                systemPrompt
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