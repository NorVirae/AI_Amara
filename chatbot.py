from langchain_ollama import ChatOllama
import sys
import time
import threading
from elevenlabs.client import ElevenLabs
from elevenlabs import stream
from dotenv import load_dotenv
import os

load_dotenv()

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

def generateVoice(text):

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
        
        stop_event = threading.Event()  # Event to stop the loading animation


        user_input = input("> ")  # Wait for user input

             
             
        loader_thread = threading.Thread(target=loading_animation, args=(stop_event,))
        loader_thread.start()
        response = llm.invoke(user_input)
        
        stop_event.set()  # Stop the animation
        loader_thread.join()  # Wait for the loader thread to finish
             
        print(response.content)
        generateVoice(response.content)
            
        if user_input.lower() == 'q':  # Check if the input is 'q' (case insensitive)
            print("Exiting the program. Goodbye!")
            break
        

if __name__ == "__main__":
    main()


