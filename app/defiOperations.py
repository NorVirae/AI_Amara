from web3 import Web3
from eth_account.messages import encode_defunct
from datetime import datetime, timedelta


class DeFiOperations:
    def __init__(self, web3_provider, wallet_address, private_key):
        """
        Initialize DeFi operations with Web3 provider and wallet credentials
        
        Args:
            web3_provider (str): URL of the Web3 provider (e.g. Infura endpoint)
            wallet_address (str): Your wallet address
            private_key (str): Your wallet's private key
        """
        self.w3 = Web3(Web3.HTTPProvider(web3_provider))
        self.wallet_address = wallet_address
        self.private_key = private_key
        print(web3_provider, "WEB3")
        # Uniswap V3 Router contract address (AssetChain Testnet)
        self.uniswap_router = "0x6f9232316901DA45a7087b876118fa6ecb9B841E"
        
    def transfer_tokens(self, token_address, recipient_address, amount):
        """
        Transfer ERC20 tokens to another wallet
        
        Args:
            token_address (str): Address of token to transfer
            recipient_address (str): Recipient's wallet address
            amount (int): Amount of tokens to transfer (in smallest unit)
            
        Returns:
            dict: Transaction receipt
        """
        print( "WEB3", self.private_key)
        
        try:
            # Standard ERC20 ABI for transfer function
            token_abi = [
                {
                    "constant": False,
                    "inputs": [
                        {"name": "_to", "type": "address"},
                        {"name": "_value", "type": "uint256"}
                    ],
                    "name": "transfer",
                    "outputs": [{"name": "", "type": "bool"}],
                    "type": "function"
                }
            ]
            
            # Create contract instance
            token_contract = self.w3.eth.contract(
                address=token_address,
                abi=token_abi
            )
            
            # Build transaction
            transaction = token_contract.functions.transfer(
                recipient_address,
                self.w3.to_wei(amount, "ether")
            ).build_transaction({
                'from': self.wallet_address,
                'gas': 100000,
                'gasPrice': self.w3.eth.gas_price,
                'nonce': self.w3.eth.get_transaction_count(self.wallet_address)
            })
            
            # Sign and send transaction
            signed_txn = self.w3.eth.account.sign_transaction(transaction, self.private_key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.raw_transaction)
            
            # Wait for transaction receipt
            return self.w3.eth.wait_for_transaction_receipt(tx_hash)
            
        except Exception as e:
            raise Exception(f"Transfer failed: {str(e)}")
        
    def swap_tokens_uniswap_v3(self, token_in_address, token_out_address, amount_in, min_amount_out, deadline=None):
        """
        Perform a swap on Uniswap V3 with enhanced error checking
        """
        try:
            
            # Validate addresses
            if not self.w3.is_address(token_in_address):
                raise ValueError(f"Invalid input token address: {token_in_address}")
            if not self.w3.is_address(token_out_address):
                raise ValueError(f"Invalid output token address: {token_out_address}")
                
            # Check if we have enough balance
            erc20_abi = [
                {
                    "constant": True,
                    "inputs": [{"name": "_owner", "type": "address"}],
                    "name": "balanceOf",
                    "outputs": [{"name": "balance", "type": "uint256"}],
                    "type": "function"
                },
                {
                    "constant": False,
                    "inputs": [
                        {"name": "_spender", "type": "address"},
                        {"name": "_value", "type": "uint256"}
                    ],
                    "name": "approve",
                    "outputs": [{"name": "", "type": "bool"}],
                    "type": "function"
                }
            ]
            
            # Create contract instance for input token
            token_contract = self.w3.eth.contract(
                address=token_in_address,
                abi=erc20_abi
            )
            
            # Check balance
            amount_in_wei = self.w3.to_wei(amount_in, "ether")
            balance = token_contract.functions.balanceOf(self.wallet_address).call()
            
            if balance < amount_in_wei:
                raise ValueError(f"Insufficient balance. Have {balance}, need {amount_in_wei}")
            
            # Approve tokens for Uniswap Router
            approve_txn = token_contract.functions.approve(
                self.uniswap_router,
                amount_in_wei
            ).build_transaction({
                'from': self.wallet_address,
                'gas': 150000,
                'gasPrice': self.w3.eth.gas_price,
                'nonce': self.w3.eth.get_transaction_count(self.wallet_address)
            })
            
            # Sign and send approval transaction
            signed_approve = self.w3.eth.account.sign_transaction(approve_txn, self.private_key)
            approve_tx_hash = self.w3.eth.send_raw_transaction(signed_approve.raw_transaction)
            
            # Wait for approval to be mined
            self.w3.eth.wait_for_transaction_receipt(approve_tx_hash)
            
            # Set deadline if not provided
            if deadline is None:
                deadline = int((datetime.now() + timedelta(minutes=20)).timestamp())
            
            # Prepare swap parameters
            swap_params = {
                'tokenIn': token_in_address,
                'tokenOut': token_out_address,
                'fee': 3000,  # 0.3% fee tier
                'recipient': self.wallet_address,
                'deadline': deadline,
                'amountIn': amount_in_wei,
                'amountOutMinimum': self.w3.to_wei(min_amount_out, "ether"),
                'sqrtPriceLimitX96': 0
            }
            
            
            # Create Uniswap Router contract instance
            router_abi = [
                {
                    "inputs": [
                        {
                            "components": [
                                {"internalType": "address", "name": "tokenIn", "type": "address"},
                                {"internalType": "address", "name": "tokenOut", "type": "address"},
                                {"internalType": "uint24", "name": "fee", "type": "uint24"},
                                {"internalType": "address", "name": "recipient", "type": "address"},
                                {"internalType": "uint256", "name": "deadline", "type": "uint256"},
                                {"internalType": "uint256", "name": "amountIn", "type": "uint256"},
                                {"internalType": "uint256", "name": "amountOutMinimum", "type": "uint256"},
                                {"internalType": "uint160", "name": "sqrtPriceLimitX96", "type": "uint160"}
                            ],
                            "internalType": "struct ISwapRouter.ExactInputSingleParams",
                            "name": "params",
                            "type": "tuple"
                        }
                    ],
                    "name": "exactInputSingle",
                    "outputs": [{"internalType": "uint256", "name": "amountOut", "type": "uint256"}],
                    "stateMutability": "payable",
                    "type": "function"
                }
            ]
            
            router_contract = self.w3.eth.contract(
                address=self.uniswap_router,
                abi=router_abi
            )
            
            # Build swap transaction
            swap_txn = router_contract.functions.exactInputSingle(swap_params).build_transaction({
                'from': self.wallet_address,
                'gas': 350000,  # Increased gas limit for swap
                'gasPrice': self.w3.eth.gas_price,
                'nonce': self.w3.eth.get_transaction_count(self.wallet_address)
            })
            
            # Sign and send swap transaction
            signed_swap = self.w3.eth.account.sign_transaction(swap_txn, self.private_key)
            swap_tx_hash = self.w3.eth.send_raw_transaction(signed_swap.raw_transaction)
            
            # Wait for and return swap receipt
            receipt = self.w3.eth.wait_for_transaction_receipt(swap_tx_hash)
            return receipt
            
        except Exception as e:
            raise Exception(f"Swap failed: {str(e)}")