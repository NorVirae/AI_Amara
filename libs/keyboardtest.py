import argparse
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
import time
from elevenlabs.client import ElevenLabs
from elevenlabs import stream
from dotenv import load_dotenv
import warnings
import whisper
import os
import wave
import concurrent.futures
from langchain_core.prompts import ChatPromptTemplate

load_dotenv()
# Flag to track key state
key_pressed = False

# innitialise llm
llm = ChatOllama(model="llama3.1:8b", )
prompt = ChatPromptTemplate.from_messages([ 
    ("system", "You are a world class technical documentation writer."),
    ("user", "{input}")
])
chain = prompt | llm

# pool = concurrent.futures.ThreadPoolExecutor(max_workers=2)

def int_or_str(text):
    """Helper function for argument parsing."""
    try:
        return int(text)
    except ValueError:
        return text


parser = argparse.ArgumentParser(add_help=False)
parser.add_argument(
    '-l', '--list-devices', action='store_true',
    help='show list of audio devices and exit')
args, remaining = parser.parse_known_args()
if args.list_devices:
    print(sd.query_devices())
    parser.exit(0)
parser = argparse.ArgumentParser(
    description=__doc__,
    formatter_class=argparse.RawDescriptionHelpFormatter,
    parents=[parser])
parser.add_argument(
    'filename', nargs='?', metavar='FILENAME',
    help='audio file to store recording to')
parser.add_argument(
    '-d', '--device', type=int_or_str,
    help='input device (numeric ID or substring)')
parser.add_argument(
    '-r', '--samplerate', type=int, help='sampling rate')
parser.add_argument(
    '-c', '--channels', type=int, default=1, help='number of input channels')
parser.add_argument(
    '-t', '--subtype', type=str, help='sound file subtype (e.g. "PCM_24")')
args = parser.parse_args(remaining)

q = queue.Queue()


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



def runLLM():
    # global pool
    if not args.filename:
        print("no audio file found")
        return
    text_input = generateTextFromVoice()
    response = llm.invoke(text_input, stream=True, )
    # loader_thread = threading.Thread(target=generateVoice, args=(response.content,))
    # loader_thread.start()
    
    generateVoice(response.content)
    
    # for chunk in llm.stream(response.content):
    #     print(chunk.content, end="", flush=True)
    
    print("")
    print(response.content)
    os.unlink(args.filename)
    args.filename = None
    # stop_event.set()  # Stop the animation
    # loader_thread.join()  # Wait for the loader thread to finish
    # print(response.content)
    # generateVoice(response.content)
           
# Define the functions to be called
def on_r_pressed():
    global recordThread
    # global recordThread
    # global runLLMThread

    # if(runLLMThread != 0):
    #     runLLMThread.join()
    print("Currently Recording...")
    # pool.submit(recordAudio)
    if not recordThread.is_alive():
        print(recordThread, "thread is not alive")
        
        try:
            recordThread.start()
        except RuntimeError:
            recordThread = threading.Thread(target=recordAudio)
            recordThread.start()
    # recordAudio()

def on_r_released():
    # global pool
    # global recordThread
    global runLLMThread
    
    print('\nRecording finished: ' + repr(args.filename))
    # recordThread.join()
    # pool.submit(runLLM)
    if not runLLMThread.is_alive():
        print(runLLMThread, "thread is not alive")
        
        try:
            runLLMThread.start()
        except RuntimeError:
            runLLMThread = threading.Thread(target=runLLM)
            runLLMThread.start()
    # runLLMThread = threading.Thread(target=runLLM)
    # runLLMThread.start()
    # parser.exit(0)
    print("stopped Recording..")

def callback(indata, frames, time, status):
    """This is called (from a separate thread) for each audio block."""
    
    if status:
        print(status, file=sys.stderr)
    q.put(indata.copy())
   
def recordAudio():
    global key_pressed  # Access the global flag
    print("Got in Before try")
    try:
        print("Got in after try")
        
        if args.samplerate is None:
            device_info = sd.query_devices(args.device, 'input')
            # soundfile expects an int, sounddevice provides a float:
            args.samplerate = int(device_info['default_samplerate'])
        if args.filename is None:
            args.filename = tempfile.mktemp(prefix='delme_rec_unlimited_',
                                            suffix='.wav', dir='')

        # Open the file and input stream for recording
        with sf.SoundFile(args.filename, mode='x', samplerate=args.samplerate,
                          channels=args.channels, subtype=args.subtype) as file:
            with sd.InputStream(samplerate=args.samplerate, device=args.device,
                                channels=args.channels, callback=callback):
                print('#' * 80)
                print('Currently recording. Release key to stop.')
                print('#' * 80)
                while key_pressed:  # Loop while the key is pressed
                    # print("is key pressed: ", key_pressed)
                    file.write(q.get())  # Write audio data to the file
    except KeyboardInterrupt:
        print('\nRecording finished: ' + repr(args.filename))
        parser.exit(0)
    except Exception as e:
        parser.exit(type(e).__name__ + ': ' + str(e))

recordThread = threading.Thread(target=recordAudio)
runLLMThread = threading.Thread(target=runLLM)
# Create a listener for keyboard events
def on_press(key):
    global key_pressed
    try:
        # Check if the spacebar is pressed and the flag is False
        if key.char == 'r' and not key_pressed:
            key_pressed = True  # Set the flag to True
            on_r_pressed()
    except AttributeError:
        pass
    if key == keyboard.Key.esc:
        return False  # Stop the listener

def on_release(key):
    global key_pressed
    try:
        # Check if the spacebar is released
        if key.char == 'r' and key_pressed:
            key_pressed = False
            on_r_released()
              # Reset the flag
    except AttributeError:
        pass

# Start listening for key events
with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
    print("Press R key to speak to AI..")
    listener.join()