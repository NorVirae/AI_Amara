import whisper
import sounddevice as sd
import numpy as np
import wave

# Parameters
SAMPLE_RATE = 16000  # Whisper works best with 16kHz
DURATION = 2  # Record duration in seconds
FILENAME = "recorded_audio.wav"

# Function to record audio
def record_audio(filename, duration, sample_rate):
    print("Recording...")
    audio_data = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=1, dtype=np.int16)
    sd.wait()
    print("Recording complete.")
    
    # Save to WAV file
    with wave.open(filename, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)  # 16-bit PCM
        wf.setframerate(sample_rate)
        wf.writeframes(audio_data.tobytes())

# Function to transcribe audio
def transcribe_audio(filename):
    model = whisper.load_model("tiny")  # Load Whisper tiny model
    result = model.transcribe(filename)
    return result["text"]

if __name__ == "__main__":
    record_audio(FILENAME, DURATION, SAMPLE_RATE)
    transcription = transcribe_audio(FILENAME)
    print("Transcription:", transcription)
