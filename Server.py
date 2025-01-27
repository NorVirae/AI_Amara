from flask import Flask, request, jsonify
from app.agentHub import AgentHub
from app.groqAgent import GroqAgent

import os
import base64
import json
import subprocess
from flask_cors import CORS
from pydub import AudioSegment
from app.defiOperations import DeFiOperations
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "http://localhost:5173"}})

tokens = {
    "USDC":"0x5A887dfC5fC4eAd13E6c9691b71cffA41552B51D",
    "USDT":"0x10BdEaBc356120FaD66d000C777e1877DBA807A2",
    "WBTC":"0xc0e983e374AAF8068A14eD3B5D3f46128c9B7410"
}

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


def handleCryptoInteraction(action):
    print(action, "Action hasbeen Carried Out")
    USDC = "0x5A887dfC5fC4eAd13E6c9691b71cffA41552B51D"
    USDT= "0x10BdEaBc356120FaD66d000C777e1877DBA807A2"
    WBTC = "0xc0e983e374AAF8068A14eD3B5D3f46128c9B7410"
    walletOwner = "0xB4D0402E12AA8CF44Fea9E46d82e979b36a84427"
    crypto_operations = DeFiOperations(os.environ["ASSETCHAIN_RPC"], walletOwner, os.environ["PRIVATE_KEY"])
    
    match action["type"]:
        case "send":
            result = crypto_operations.transfer_tokens(tokens[action["token"]], action['recipientAddress'], action['amount'])
            return {"transactionHash":result.transactionHash.hex()}
        case "swap":
            result = crypto_operations.swap_tokens_uniswap_v3(tokens[action["tokenIn"]],tokens[action["tokenOut"]], action['amount'], 0, action['recipientAddress'])
            print(result.transactionHash.hex(), "HULA")
            return {"transactionHash":result.transactionHash.hex()}
        case "fetch_balance":
            newBalance = crypto_operations.fetch_balance(tokens[action["token"]], action["balanceAddress"])
            return {"balance": newBalance, "token": action["token"]}
        case _:
            return
    

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
    
   
    
def prepResponseForClient(parsed_data, agent, save_out_path, save_out_path_wav, lip_sync_path, data_list):
    try:
        agent.generateVoice(parsed_data["response"], save_out_path)
        convert_mp3_to_wav(save_out_path, save_out_path_wav)
        generate_lip_sync(os.path.join(os.getcwd(), save_out_path_wav), os.path.join(os.getcwd(),lip_sync_path), "json")
        lip_sync_json_data = load_json_file(lip_sync_path)
        base64_audio = audio_to_base64(save_out_path_wav)
        if "transactionHash" in parsed_data:
            data_list.append({
                "message": parsed_data['response'],
                "animation": parsed_data['interaction']["animation"],
                "facialExpression": parsed_data['interaction']["facial"],
                "audio": base64_audio,
                "lipsync": lip_sync_json_data,
                "action": parsed_data['action'],
                "transactionHash": parsed_data["transactionHash"]
            })
        else:
            data_list.append({
                "message": parsed_data['response'],
                "animation": parsed_data['interaction']["animation"],
                "facialExpression": parsed_data['interaction']["facial"],
                "audio": base64_audio,
                "lipsync": lip_sync_json_data,
                "action": parsed_data['action'],
                # "transactionHash": parsed_data["transactionHash"]
            })
        return data_list
    except (json.JSONDecodeError, ValueError) as e:
        # data_list = []
        print(e, "ERROR")
        error_audio_response_path = "app/audio/error_response/ai_voice.wav"
        error_json_lipSync_path = "app/audio/error_response/ai_lipsync.json"
        
        # agent.generateVoice("Sorry Something Is Wrong on my end chill a bit, we will chat in a jiffy", save_out_path)
        # convert_mp3_to_wav(save_out_path, save_out_path_wav)
        # generate_lip_sync(os.path.join(os.getcwd(), save_out_path_wav), os.path.join(os.getcwd(),lip_sync_path), "json")
        lip_sync_json_data = load_json_file(error_json_lipSync_path)
        base64_audio = audio_to_base64(error_audio_response_path)
        data_list.append({
                "message": "Sapa don knack my side",
                "animation": "Idle",
                "facialExpression": "default",
                "audio": base64_audio,
                "lipsync": lip_sync_json_data
            })
        return data_list
def getJsonData(response_message):
    parsed_data = json.loads(response_message)
    if not isinstance(parsed_data, object):
        raise ValueError("Expected a dictionary.")
    print(parsed_data, "ITem")
    return parsed_data

@app.route("/chat", methods=['POST'])
async def sendChat():
    # agent = AgentHub("Amara")
    agent = GroqAgent()
    try:
        # Ensure request method is POST
        if request.method != 'POST':
            return jsonify({"error": "Method not allowed"}), 405

        # Parse the incoming JSON data
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
        
        message = ""
        # Define output paths
        save_out_path = "app/audio/out/ai_voice.mp3"
        save_out_path_wav = "app/audio/out/ai_voice.wav"
        
        lip_sync_path = "app/audio/out/ai_lipsync.json"
        save_path = "app/audio/input_audio.webm"
        
        
        
        
        # Ensure audio field exists in the request
        if "audio" in data and data["audio"] is not None:
            print("Got in here!")
            # return jsonify({"error": "Missing 'audio' field in request"}), 400

            # Extract the base64 audio data
            audio_base64 = data["audio"]
            if not audio_base64:
                return jsonify({"error": "Empty 'audio' field"}), 400

            # Decode and save the audio file
            
            with open(save_path, "wb") as f:
                f.write(base64.b64decode(audio_base64))

                # Process the audio and generate text
            message = agent.generateTextFromVoice(save_path)
        
        
        elif "textInput" in data:
            print(data["textInput"], "MESSae")
            
            message = data["textInput"]
        
        print(message, "MESSae")
        # Generate agent's response and voice output
        response_message = agent.predict(message)
        
        data_list = []
        print("------ ------")
        print(response_message,"ChEKC")
        
        
        parsed_data = getJsonData(response_message)
        data_list = prepResponseForClient(parsed_data=parsed_data,agent=agent, save_out_path=save_out_path, save_out_path_wav=save_out_path_wav, lip_sync_path=lip_sync_path, data_list=data_list)
        if parsed_data["action"]:
            result  = handleCryptoInteraction(parsed_data["action"])
            blockchain_response = agent.predict(f"{result}")
            block_parsed_data = getJsonData(blockchain_response)
            data_list = prepResponseForClient(parsed_data=block_parsed_data,agent=agent, save_out_path=save_out_path, save_out_path_wav=save_out_path_wav, lip_sync_path=lip_sync_path, data_list=data_list)
            print(result)
        
       
        # Return the response
        return jsonify({
            "messages": data_list
        })

    except Exception as e:
        data_list = []
        print(e, "ERROR")
        error_audio_response_path = "app/audio/error_response/ai_voice.wav"
        error_json_lipSync_path = "app/audio/error_response/ai_lipsync.json"
        
        # agent.generateVoice("Sorry Something Is Wrong on my end chill a bit, we will chat in a jiffy", save_out_path)
        # convert_mp3_to_wav(save_out_path, save_out_path_wav)
        # generate_lip_sync(os.path.join(os.getcwd(), save_out_path_wav), os.path.join(os.getcwd(),lip_sync_path), "json")
        lip_sync_json_data = load_json_file(error_json_lipSync_path)
        base64_audio = audio_to_base64(error_audio_response_path)
        data_list.append({
                "message": "Sorry Something Is Wrong on my end chill a bit, and send again",
                "animation": "Idle",
                "facialExpression": "default",
                "audio": base64_audio,
                "lipsync": lip_sync_json_data
            })
        return jsonify({"messages": data_list}), 500
