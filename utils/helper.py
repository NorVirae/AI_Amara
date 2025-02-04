
import os
import base64
import json
import subprocess
from pydub import AudioSegment
from app.defiOperations import DeFiOperations
import math

class Helper:
    tokens = {
        "USDC":"0x5A887dfC5fC4eAd13E6c9691b71cffA41552B51D",
        "USDT":"0x10BdEaBc356120FaD66d000C777e1877DBA807A2",
        "WBTC":"0xc0e983e374AAF8068A14eD3B5D3f46128c9B7410"
    }

    listOfFriendsWallets = {
        "Dave":"0x7D5F3FC77ffB4d33551343b7C0BDC0A41AAdB2A8",
        "Ugo":"0x623787c0582026d6b13236268630Dd2c7a961BD4",
        "Ada":"0xd24977e5CC8BbDE8F408dF1Ee05DDc2E9A893EE7",
        "me": "0xB4D0402E12AA8CF44Fea9E46d82e979b36a84427"
    }

    def __init__(self):
        """_summary_
        """
    
    def loadCharacter(name):
        """
        Load A Json file containin character Info
        """
        
        character_file = f"app/characters/{name}.json"
        try:
            with open(character_file, "r") as json_file:
                # Load the JSON data into a variable
                data = json.load(json_file)
                return data
        except FileNotFoundError:
            print(f"Error: The file at {character_file} was not found.")
            return None
        except json.JSONDecodeError as e:
            print(f"Error: Failed to decode JSON. {e}")
            return None
        
    def convert_mp3_to_wav(self, input_file, output_file):
        try:
            # Load the MP3 file
            audio = AudioSegment.from_mp3(input_file)
            
            # Export as WAV file
            audio.export(output_file, format="wav")
            print(f"Conversion successful: {output_file}")
        except Exception as e:
            print(f"Error during conversion: {e}")


    def generate_lip_sync(self, audio_path, output_path, output_format="json"):
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

    def load_json_file(self, file_path):
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


    def handleCryptoInteraction(self, action):
        print(action, "Action hasbeen Carried Out")
        USDC = "0x5A887dfC5fC4eAd13E6c9691b71cffA41552B51D"
        USDT= "0x10BdEaBc356120FaD66d000C777e1877DBA807A2"
        WBTC = "0xc0e983e374AAF8068A14eD3B5D3f46128c9B7410"
        walletOwner = "0xB4D0402E12AA8CF44Fea9E46d82e979b36a84427"
        crypto_operations = DeFiOperations(os.environ["ASSETCHAIN_RPC"], walletOwner, os.environ["PRIVATE_KEY"])
        
        match action["type"]:
            case "send":
                result = crypto_operations.transfer_tokens(self.tokens[action["token"]], self.listOfFriendsWallets[action['recipient']], action['amount'])
                return {"transactionHash":result.transactionHash.hex()}
            case "swap":
                result = crypto_operations.swap_tokens_uniswap_v3(self.tokens[action["tokenIn"]], self.tokens[action["tokenOut"]], action['amount'], 0, self.listOfFriendsWallets[action['recipient']])
                print(result.transactionHash.hex(), "HULA")
                return {"transactionHash":result.transactionHash.hex()}
            case "fetch_balance":
                newBalance = crypto_operations.fetch_balance(self.tokens[action["token"]], self.listOfFriendsWallets[action['balancee']])
                flooredBalance = math.floor(int(newBalance))
                correctedBalance = f"${flooredBalance:,.0f}"
                return {"balance": correctedBalance, "token": action["token"]}
            case _:
                return
    

    def audio_to_base64(self, file_path):
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
    
   
    
    def prepResponseForClient(self, parsed_data, agent, save_out_path, save_out_path_wav, lip_sync_path, data_list):
        try:
            agent.generateVoice(parsed_data["response"], save_out_path)
            self.convert_mp3_to_wav(save_out_path, save_out_path_wav)
            self.generate_lip_sync(os.path.join(os.getcwd(), save_out_path_wav), os.path.join(os.getcwd(),lip_sync_path), "json")
            lip_sync_json_data = self.load_json_file(lip_sync_path)
            base64_audio = self.audio_to_base64(save_out_path_wav)
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
            lip_sync_json_data = self.load_json_file(error_json_lipSync_path)
            base64_audio = self.audio_to_base64(error_audio_response_path)
            data_list.append({
                    "message": "Sapa don knack my side",
                    "animation": "Idle",
                    "facialExpression": "default",
                    "audio": base64_audio,
                    "lipsync": lip_sync_json_data
                })
            return data_list
    
    def getJsonData(self, response_message):
        parsed_data = json.loads(response_message)
        if not isinstance(parsed_data, object):
            raise ValueError("Expected a dictionary.")
        print(parsed_data, "ITem")
        return parsed_data