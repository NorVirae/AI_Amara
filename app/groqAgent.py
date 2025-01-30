import os

from langchain.chains import LLMChain
from langchain_core.prompts import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    MessagesPlaceholder,
)
from langchain_core.messages import SystemMessage
from langchain_groq import ChatGroq

from groq import Groq
import numpy  # Make sure NumPy is loaded before it is used in the callback
assert numpy  # avoid "imported but unused" message (W0611)
from elevenlabs.client import ElevenLabs
from elevenlabs import save
import warnings
import os
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.chains.llm import LLMChain
from utils.helper import Helper

system_info = f"{Helper.loadCharacter('Amara')}"



class GroqAgent:
    chat_history = []
    def __init__(self):
        """
        This function is the main entry point of the application. It sets up the Groq client, the Streamlit interface, and handles the chat interaction.
        """

        # Get Groq API key
        groq_api_key = os.environ['GROQ_API_KEY']
        model = 'llama-3.3-70b-versatile'
        # Initialize Groq Langchain chat object and conversation
        self.groq_chat = ChatGroq(
                groq_api_key=groq_api_key, 
                model_name=model
        )
        self.whisper= Groq(api_key=groq_api_key)
   
        print("Hello! I'm your friendly Groq chatbot. I can help answer your questions, provide information, or just chat. I'm also super fast! Let's start our conversation!")

        self.system_prompt = system_info
        

            
    def predict(self, text_input):
    # If the user has asked a question,
        if text_input:
            # Construct a chat prompt template using various components
            prompt = ChatPromptTemplate.from_messages(
                [
                    SystemMessage(
                        content=self.system_prompt
                    ),  # This is the persistent system prompt that is always included at the start of the chat.

                    MessagesPlaceholder(
                        variable_name="chat_history"
                    ),  # This placeholder will be replaced by the actual chat history during the conversation. It helps in maintaining context.

                    HumanMessagePromptTemplate.from_template(
                        "{human_input}"
                    ),  # This template is where the user's current input will be injected into the prompt.
                ]
            )

            # Create a conversation chain using the LangChain LLM (Language Learning Model)
            conversation = LLMChain(
                llm=self.groq_chat,  # The Groq LangChain chat object initialized earlier.
                prompt=prompt,  # The constructed prompt template.
                verbose=False,   # TRUE Enables verbose output, which can be useful for debugging.
            )
            
            self.chat_history.append({"role":"human", "content": text_input})
           
            # Invoke the conversation with properly formatted arguments
            response = conversation.predict(
              chat_history=self.chat_history,  human_input=text_input
            )
            
           
            print("RESPONSE", response)
            self.chat_history.append({"role":"ai", "content": response})
            
            return response

    def generateTextFromVoice(self, audio_path: str) -> str:
        """
        Records audio, saves it to a file, and transcribes it using OpenAI Whisper.
        """
        print("Loading Whisper model...")
        # model = whisper.load_model("turbo")
        
        print("Transcribing audio...", audio_path)
        # result = model.transcribe(audio_path, fp16=False)
        
        with open(audio_path, "rb") as file:
            transcription = self.whisper.audio.transcriptions.create(
            file=(audio_path, file.read()),
            model="whisper-large-v3-turbo",
            response_format="verbose_json",
            )
            
            print("Transcription:")
            print(transcription.text)
            return transcription.text
        return "thank you"
    
    def generateVoice(self, text: str, audio_out_path: str = "./app/audio/out/ai_voice.mp3") -> None:
        """
        Generates voice output using ElevenLabs API.
        """
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
# if __name__ == "__main__":
#     main()