from flask import Flask, request, jsonify
from app.agent import Agent
import os
import base64
import json
import subprocess
from flask_cors import CORS
from pydub import AudioSegment


app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "http://localhost:5173"}})

def convert_mp3_to_wav(input_file, output_file):
    try:
        # Load the MP3 file
        audio = AudioSegment.from_mp3(input_file)
        
        # Export as WAV file
        audio.export(output_file, format="wav")
        print(f"Conversion successful: {output_file}")
    except Exception as e:
        print(f"Error during conversion: {e}")


def generate_lip_sync(audio_path, output_path, output_format="json"):
    """
    Generate lip sync data from an audio file using Rhubarb.

    :param audio_path: Path to the input audio file.
    :param output_path: Path to save the generated lip sync data.
    :param output_format: Format of the output file (default: "json").
    :return: True if successful, False otherwise.
    """
    try:
        # Construct the Rhubarb command
        command = [
            "rhubarb",
            audio_path,
            "-f", output_format,
            "-o", output_path
        ]

        # Run the command
        result = subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        # Output Rhubarb's response for debugging purposes (optional)
        print("Rhubarb output:", result.stdout.decode())
        return True

    except subprocess.CalledProcessError as e:
        # Print error output if the command fails
        print("Error during Rhubarb execution:", e.stderr.decode())
        return False
    except FileNotFoundError:
        print("Error: Rhubarb executable not found. Make sure it is installed and added to PATH.")
        return False

def load_json_file(file_path):
    """
    Open a JSON file and save its contents as a variable.

    :param file_path: Path to the JSON file.
    :return: The contents of the JSON file as a Python variable (dictionary or list).
    """
    try:
        with open(file_path, "r") as json_file:
            # Load the JSON data into a variable
            data = json.load(json_file)
            return data
    except FileNotFoundError:
        print(f"Error: The file at {file_path} was not found.")
        return None
    except json.JSONDecodeError as e:
        print(f"Error: Failed to decode JSON. {e}")
        return None


def audio_to_base64(file_path):
    """
    Converts an audio file to a Base64 string.
    :param file_path: Path to the audio file.
    :return: Base64 encoded string of the audio file.
    """
    try:
        with open(file_path, "rb") as audio_file:
            base64_audio = base64.b64encode(audio_file.read()).decode('utf-8')
        return base64_audio
    except FileNotFoundError:
        return None

@app.route("/chat", methods=['POST'])
def sendChat():
    try:
        # Ensure request method is POST
        if request.method != 'POST':
            return jsonify({"error": "Method not allowed"}), 405

        # Parse the incoming JSON data
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400

        # Ensure audio field exists in the request
        if "audio" not in data:
            return jsonify({"error": "Missing 'audio' field in request"}), 400

        # Extract the base64 audio data
        audio_base64 = data["audio"]
        if not audio_base64:
            return jsonify({"error": "Empty 'audio' field"}), 400

        # Decode and save the audio file
        save_path = "app/audio/input_audio.webm"
        with open(save_path, "wb") as f:
            f.write(base64.b64decode(audio_base64))

        # Define output paths
        save_out_path = "app/audio/out/ai_voice.mp3"
        save_out_path_wav = "app/audio/out/ai_voice.wav"
        
        lip_sync_path = "app/audio/out/ai_lipsync.json"

        # Process the audio and generate text
        agent = Agent("Amara")
        message = agent.generateTextFromVoice(save_path)

        # Generate agent's response and voice output
        response_message = agent.callAgent(message)
        
        data_list = []
        print(response_message,"ChEKC")
        
        try:
            parsed_data = json.loads(response_message)
            if not isinstance(parsed_data, list):
                raise ValueError("Expected a list of dictionaries.")
            for item in json.loads(response_message):
                print(item, "ITem")
                if not item["chat"]:
                    item["chat"]= item
                    item["animation"]= "Idle"
                    item["facial_animation"]= "default"
                    
                agent.generateVoice(item['chat'], save_out_path)
                convert_mp3_to_wav(save_out_path, save_out_path_wav)
                generate_lip_sync(os.path.join(os.getcwd(), save_out_path_wav), os.path.join(os.getcwd(),lip_sync_path), "json")
                lip_sync_json_data = load_json_file(lip_sync_path)
                base64_audio = audio_to_base64(save_out_path_wav)
                data_list.append({
                    "message": item['chat'],
                    "animation": item['animation'],
                    "facialExpression": item['facial_animation'],
                    "audio": base64_audio,
                    "lipsync": lip_sync_json_data
                })
        except (json.JSONDecodeError, ValueError) as e:
            print(f"Invalid input: {e}")
            agent.generateVoice("Sorry I didn't get you please come again", save_out_path)
            convert_mp3_to_wav(save_out_path, save_out_path_wav)
            generate_lip_sync(os.path.join(os.getcwd(), save_out_path_wav), os.path.join(os.getcwd(),lip_sync_path), "json")
            lip_sync_json_data = load_json_file(lip_sync_path)
            base64_audio = audio_to_base64(save_out_path_wav)
            data_list.append({
                    "message": "Sorry I didn't get you please come again",
                    "animation": "Idle",
                    "facialExpression": "default",
                    "audio": base64_audio,
                    "lipsync": lip_sync_json_data
                })
            

        
        
            
        
        # agent.generateVoice(response_message, save_out_path)

        # convert_mp3_to_wav(save_out_path, save_out_path_wav)

        # Generate lip sync data
        # generate_lip_sync(os.path.join(os.getcwd(), save_out_path_wav), os.path.join(os.getcwd(),lip_sync_path), "json")
        # lip_sync_json_data = load_json_file(lip_sync_path)

        # Convert generated audio to base64
        # base64_audio = audio_to_base64(save_out_path_wav)

        # Clean up input file
        os.unlink(save_path)

        # Return the response
        return jsonify({
            "messages": data_list
        })

    except Exception as e:
        data_list = []
        print(e)
        agent.generateVoice("Sorry Something Is Wrong on my end chill a bit, and send again", save_out_path)
        convert_mp3_to_wav(save_out_path, save_out_path_wav)
        generate_lip_sync(os.path.join(os.getcwd(), save_out_path_wav), os.path.join(os.getcwd(),lip_sync_path), "json")
        lip_sync_json_data = load_json_file(lip_sync_path)
        base64_audio = audio_to_base64(save_out_path_wav)
        data_list.append({
                "message": "Sorry Something Is Wrong on my end chill a bit, and send again",
                "animation": "Idle",
                "facialExpression": "default",
                "audio": base64_audio,
                "lipsync": lip_sync_json_data
            })
        return jsonify({"messages": data_list}), 500
