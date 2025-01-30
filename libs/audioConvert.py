from pydub import AudioSegment

def convert_mp3_to_wav(mp3_file_path, wav_file_path):
    """
    Converts an MP3 file to WAV format.

    :param mp3_file_path: Path to the input MP3 file.
    :param wav_file_path: Path to save the output WAV file.
    """
    try:
        # Load the MP3 file
        audio = AudioSegment.from_mp3(mp3_file_path)
        
        # Export as WAV
        audio.export(wav_file_path, format="wav")
        
        print(f"Conversion successful! WAV file saved at: {wav_file_path}")
    except Exception as e:
        print(f"An error occurred: {e}")

# Example usage
mp3_file = "app\\audio\\audio.mp3"
wav_file = "app\\audio\\audio.wav"
convert_mp3_to_wav(mp3_file, wav_file)
