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


class LLMAgent:
    name = "Amara"
    chat_history = []
    def __init__(self, name, args,  parser):
        # innitialise llm
        self.q = queue.Queue()

        self.llm = ChatOllama(model="llama3.1:8b", )
        self.name = name
        self.prompt = ChatPromptTemplate.from_messages(
            [ 
                {
                    "system",
                    f"Your are an AI Named ${self.name} you answer questions with simple answers and no funny stuff.",
                },
                MessagesPlaceholder(variable_name="chat_history"),
                {"human", "{input}"}
            ]
        )
        self.chain = self.prompt | self.llm
        self.args = args
        self.parser = parser
        self.recordThread = threading.Thread(target=self.recordAudio)
        self.runLLMThread = threading.Thread(target=self.runLLM)
        self.key_pressed = False
    
    def getChain(self):
        return self.chain
    
    def runLLM(self):
        # global pool
        if not self.args.filename:
            print("no audio file found")
            return
        text_input = self.generateTextFromVoice()
        response = self.chain.invoke({"input": text_input, "chat_history": self.chat_history}, stream=True )
        self.chat_history.append(HumanMessage(content=text_input))
        self.chat_history.append(AIMessage(content=response.content))
        
        self.generateVoice(response.content)
        print("")
        print(response.content)
        os.unlink(self.args.filename)
        self.args.filename = None
        
        
    def callback(self,indata, frames, time, status):
        """This is called (from a separate thread) for each audio block."""
        if status:
            print(status, file=sys.stderr)
        self.q.put(indata.copy())
        
    def recordAudio(self):
        print("Got in Before try")
        try:
            print("Got in after try")
            
            if self.args.samplerate is None:
                device_info = sd.query_devices(self.args.device, 'input')
                # soundfile expects an int, sounddevice provides a float:
                self.args.samplerate = int(device_info['default_samplerate'])
            if self.args.filename is None:
                self.args.filename = tempfile.mktemp(prefix='delme_rec_unlimited_',
                                                suffix='.wav', dir='')

            # Open the file and input stream for recording
            with sf.SoundFile(self.args.filename, mode='x', samplerate=self.args.samplerate,
                            channels=self.args.channels, subtype=self.args.subtype) as file:
                with sd.InputStream(samplerate=self.args.samplerate, device=self.args.device,
                                    channels=self.args.channels, callback=self.callback):
                    print('#' * 80)
                    print('Currently recording. Release key to stop.')
                    print('#' * 80)
                    while self.key_pressed:  # Loop while the key is pressed
                        # print("is key pressed: ", key_pressed)
                        file.write(self.q.get())  # Write audio data to the file
        except KeyboardInterrupt:
            print('\nRecording finished: ' + repr(self.args.filename))
            self.parser.exit(0)
        except Exception as e:
            self.parser.exit(type(e).__name__ + ': ' + str(e))
            
    def generateTextFromVoice(self):
        """
        Records audio, saves it to a file, and transcribes it using OpenAI Whisper.
        """
        
        # Load Whisper model
        print("Loading Whisper model...")
        model = whisper.load_model("turbo")
        
        # Transcribe the audio
        print("Transcribing audio...", self.args.filename)
        result = model.transcribe(self.args.filename, fp16=False)
        
        # Print the transcription
        print("Transcription:")
        print(result["text"])
        return result["text"]
    
    def generateVoice(self, text):
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
        
    def run(self):
        with keyboard.Listener(on_press=self.on_press, on_release=self.on_release) as listener:
            print("Press R(r) key to speak to AI..")
            listener.join()
            
    def on_press(self,key):
        try:
            # Check if the spacebar is pressed and the flag is False
            if key.char == 'r' and not self.key_pressed:
                self.key_pressed = True  # Set the flag to True
                self.on_r_pressed()
        except AttributeError:
            pass
        if key == keyboard.Key.esc:
            return False  # Stop the listener

    def on_release(self,key):
        try:
            # Check if the spacebar is released
            if key.char == 'r' and self.key_pressed:
                self.key_pressed = False
                self.on_r_released()
                # Reset the flag
        except AttributeError:
            pass
        
    # Define the functions to be called
    def on_r_pressed(self,):
        # global recordThread
        # global runLLMThread

        # if(runLLMThread != 0):
        #     runLLMThread.join()
        print("Currently Recording...")
        # pool.submit(recordAudio)
        if not self.recordThread.is_alive():            
            try:
                self.recordThread.start()
            except RuntimeError:
                recordThread = threading.Thread(target=self.recordAudio)
                recordThread.start()
        # recordAudio()

    def on_r_released(self,):
        # global pool
        # global recordThread
        
        print('\nRecording finished: ' + repr(self.args.filename))
        # recordThread.join()
        # pool.submit(runLLM)
        if not self.runLLMThread.is_alive():
            print(self.runLLMThread, "thread is not alive")
            
            try:
                self.runLLMThread.start()
            except RuntimeError:
                self.runLLMThread = threading.Thread(target=self.runLLM)
                self.runLLMThread.start()
        # runLLMThread = threading.Thread(target=runLLM)
        # runLLMThread.start()
        # parser.exit(0)
        print("stopped Recording..")