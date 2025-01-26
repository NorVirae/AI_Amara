
from app.defiOperations import DeFiOperations
from dotenv import load_dotenv
from  web3 import Web3, utils
import os

load_dotenv()

def main(type = "send"):
    try:
        defiOps = DeFiOperations(os.environ["ASSETCHAIN_RPC"], os.environ["ACCOUNT_WALLET_ADDRESS"], os.environ["PRIVATE_KEY"])
        if type == "send":  
            result = defiOps.transfer_tokens("0x5A887dfC5fC4eAd13E6c9691b71cffA41552B51D", "0x7D5F3FC77ffB4d33551343b7C0BDC0A41AAdB2A8", 50)
            print(result.transactionHash.hex())
        elif type == "swap":
            result = defiOps.swap_tokens_uniswap_v3("0x5A887dfC5fC4eAd13E6c9691b71cffA41552B51D", "0x10BdEaBc356120FaD66d000C777e1877DBA807A2", 50,  1)
            print(result.transactionHash.hex())
            
    except Exception as err:
        print(err)
        

if __name__ == "__main__":
    main("swap")