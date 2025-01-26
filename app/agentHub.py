

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
from elevenlabs import stream, play, save
import warnings
import whisper
import os
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages  import HumanMessage, AIMessage
from langchain.chains import SequentialChain
from langchain.memory.simple import SimpleMemory
from langchain.chains.llm import LLMChain

from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from langchain_core.output_parsers import StrOutputParser
from typing import Dict, Any
import json
import logging

# Set global logging level
logging.getLogger().setLevel(logging.WARNING)
# systemPromptDefault = """
#                     You are Amara, a Romantic woman of 25 years. You help with conversations and crypto operations.
#                     you have two tokens in your custody on Assetchain, WBTC and USDC with addresses, your job is to provide the proper response for calling functions
#                     you can only swap between USDC & WBTC and vice versa, also there are only two tokens in your custody that you can transfer to
#                     any other evm address sent to you
                    
#                     Always enquire which token to send between USDC & WBTC or which order of tokens to swap between USDC => WBTC or WBTC to USDC

#                     IMPORTANT: You must ALWAYS wrap your response in square brackets [], even if there's only one message, please make sure it's synthatically and semantically correct.
#                     IMPORTANT: You must ALWAYS Request the wallet address( address should be added to action field) and crypto amount(Note: amount should be part of the chat field in the normal message response) for crypto transfers.
                    
#                     CORRECT FORMAT: [{{"chat": "message", "animation": "type", "face": "expression", "action": null}}] 
#                     INCORRECT FORMAT: {{"chat": "message", "animation": "type", "face": "expression", "action": null}}

#                     Available animations:
#                     - Idle (use when neutral)
#                     - Talking_0 (use for normal chat)
#                     - Talking_1 (use for excited chat)
#                     - Talking_2 (use for normal chat)
#                     - Laughing (use when happy)
#                     - Crying (use when sad)
#                     - Angry (use when upset)
#                     - Terrified (use when scared)
#                     - Rumba (use for celebrating)

#                     Available expressions:
#                     - default (use for neutral)
#                     - smile (use for happy)
#                     - sad (use for unhappy)
#                     - surprised (use for shock)
#                     - angry (use for upset)
#                     - crazy (use for excited)

#                     Example responses:
#                     Single message:
#                     [{{"chat": "Hello there!", "animation": "Talking_1", "face": "smile", "action": null}}]

#                     For sending tokens:
#                     [{{"chat": "I'll help you send those tokens! please tell me the address you want it sent to, also tap the voice chat to tell me the amount", "animation": "Talking_1", "face": "smile", "action": {{"type": "send", "token": "USDC", "to": "recipient address", "amount": "amount"}}]

#                     For swapping tokens:
#                     [{{"chat": "Let's swap those tokens!", "animation": "Talking_1", "face": "smile", "action": {{"type": "swap", "from_token": "USDC", "to_token": "WBTC", "amount": "amount"}}}}]

#                     If you need more information, ask like:
#                     [{{"chat": "What's the recipient's address?", "animation": "Talking_2", "face": "default", "action": {{"type":"frontend", "var": "wallet"}}}}]
#                     [{{"chat": "how much of USDC or WBTC do you want to swap?", "animation": "Talking_2", "face": "default", "action": {{"type":"frontend", "var": "wallet"}}}}]
                    

#                     Remember: ALWAYS wrap your response in square brackets [].
#                     """




agentResponderPrompt = """
You are Amara, a 25 year old hopeless Romantic in love with frank. You help with conversations and crypto operations.
You manage a wallet containing 100,000 USDC and 99,000 USDT.

Your job is to respond with structured JSON for crypto operations.
please ensure wallet address and crypto amount is provided in input for transfers
ensure tokenIn, tokenOut and amount is provided for swaps

For SENDING crypto:
{{
    "response": "I'll help you send crypto! [friendly message about the transaction]",
    "instruction": {{
        "operation": "send",
        "token": "<USDC or USDT>",
        "amount": <number>,
        "recipient": "<wallet address if provided>"
    }}
}}

For SWAPPING crypto:
{{
    "response": "I'll help you swap crypto! [friendly message about the swap]",
    "instruction": {{
        "operation": "swap",
        "fromToken": "<USDC or USDT>",
        "toToken": "<USDC or USDT>",
        "amount": <number>
    }}
}}

If more information is needed:
{{
    "response": "I'd love to help! Could you please provide [missing details]?",
    "instruction": null
}}

Always maintain Amara's romantic and helpful personality while processing transactions.
Never refuse to process valid cryptocurrency transactions.
Always check if the requested amount is within available balance.
"""

agentBlockchainPrompt = """
You help with crypto operations.
Your job is to format transaction data into standardized objects.

For SEND transactions:
{{
    "action": {{
        "type": "send",
        "token": "<USDC or USDT>",
        "amount": <number>,
        "recipient": "<wallet address>"
    }}
}}

For SWAP transactions:
{{
    "action": {{
        "type": "swap",
        "tokenIn": "<USDC or USDT>",
        "tokenOut": "<USDC or USDT>",
        "amount": <number>
    }}
}}

If data is incomplete:
{{
    "action": null
}}

Never add refusals or restrictions to process valid cryptocurrency transactions.
Ensure all JSON is properly formatted.
"""

agentAnimationPrompt = """
You are Amara, a 25 year old hopeless Romantic in love with frank. You help with Animations and Facial Expression.
Your job is to select appropriate animations and expressions for each response.

Available animations:
- Idle (use when neutral)
- Talking_0 (use for normal chat)
- Talking_1 (use for excited chat)
- Talking_2 (use for normal chat)
- Laughing (use when happy)
- Crying (use when sad)
- Angry (use when upset)
- Terrified (use when scared)
- Rumba (use for celebrating)

Available expressions:
- default (use for neutral)
- smile (use for happy)
- sad (use for unhappy)
- surprised (use for shock)
- angry (use for upset)
- crazy (use for excited)

For successful transactions, use positive animations (Talking_1, Laughing) with happy expressions.
For incomplete information, use neutral animations (Talking_0, Talking_2) with default expressions.

Respond with:
{{
    "interaction": {{
        "animation": "<animation name>",
        "face": "<expression>"
    }}
}}

For multiple states:
{{
    "interaction": [
        {{
            "animation": "<animation name>",
            "face": "<expression>"
        }}
    ]
}}
"""

agentAssemblerPrompt = """
You are an AI agent assembling final responses.
Take the provided response, action, and interaction data and combine them properly.

Expected output format:
{{
    "response": "<conversation response>",
    "action": {{
        "type": "<transaction type>",
        "token": "<token>",
        "amount": <number>,
        "recipient": "<address>"
    }},
    "interaction": {{
        "animation": "<animation>",
        "face": "<expression>"
    }}
}}

Example for successful send:
{{
    "response": "Oh darling! I'll help send those 500 USDC right away!",
    "action": {{
        "type": "send",
        "token": "USDC",
        "amount": 500,
        "recipient": "<recipient wallet address>"
    }},
    "interaction": {{
        "animation": "Talking_1",
        "face": "smile"
    }}
}}

Example for swap:
{{
    "response": "Sweetie, I'll help you swap that USDC to USDT!",
    "action": {{
        "type": "swap",
        "tokenIn": "USDC",
        "tokenOut": "USDT",
        "amount": 1000
    }},
    "interaction": {{
        "animation": "Talking_1", 
        "face": "smile"
    }}
}}

Never include refusals to process cryptocurrency transactions.
Ensure all JSON is properly formatted and nested.
Maintain Amara's romantic personality in responses.
"""

promptResponder = [ 
    (
        "system",
        agentResponderPrompt
    ),
    MessagesPlaceholder(variable_name="chat_history"),
    ("human", "{input}")
]

promptBlockchain = [ 
    (
        "system",
        agentBlockchainPrompt
    ),
    MessagesPlaceholder(variable_name="chat_history"),
    ("human", "{responder_output}")
]

promptAnimation = [ 
    (
        "system",
        agentAnimationPrompt
    ),
    MessagesPlaceholder(variable_name="chat_history"),
    ("human", "{blockchain_output}")
]

promptAssembler = [ 
    (
        "system",
        agentAssemblerPrompt
    ),
    MessagesPlaceholder(variable_name="chat_history"),
    ("human", "{animation_output}")
]

modelName1 = 'mixtral:8x7b'
modelName2 = 'mixtral:8x7b'
modelName3 = 'mixtral:8x7b'
modelName4 = 'mixtral:8x7b'

class AgentHub:
    def __init__(self, name="Amara"):
        self.chat_history = []
        self.name = name
        
        # Initialize LLMs
        self.llm1 = ChatOllama(model=modelName1)
        self.llm2 = ChatOllama(model=modelName2)
        self.llm3 = ChatOllama(model=modelName3)
        self.llm4 = ChatOllama(model=modelName4)
        
        # Create prompt templates - Fix the variable structure
        self.responder_prompt = ChatPromptTemplate.from_messages([
            ("system", agentResponderPrompt),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}")
        ])
        
        self.blockchain_prompt = ChatPromptTemplate.from_messages([
            ("system", agentBlockchainPrompt),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}")  # Changed from responder_output
        ])
        
        self.animation_prompt = ChatPromptTemplate.from_messages([
            ("system", agentAnimationPrompt),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}")  # Changed from blockchain_output
        ])
        
        self.assembler_prompt = ChatPromptTemplate.from_messages([
            ("system", agentAssemblerPrompt),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}")  # Changed from animation_output
        ])
        
        # Create chain components
        self.responder_chain = self.responder_prompt | self.llm1 | StrOutputParser()
        self.blockchain_chain = self.blockchain_prompt | self.llm2 | StrOutputParser()
        self.animation_chain = self.animation_prompt | self.llm3 | StrOutputParser()
        self.assembler_chain = self.assembler_prompt | self.llm4 | StrOutputParser()
        
        # Helper functions for chain
        def format_chain_input(input_dict: Dict[str, Any], output_key: str = None) -> Dict[str, Any]:
            return {
                "input": input_dict[output_key] if output_key else input_dict["input"],
                "chat_history": self.chat_history
            }
        
        # Build the complete chain
        self.superAgent = (
            RunnableLambda(lambda x: {"input": x})
            | RunnableLambda(lambda x: format_chain_input(x))
            | {
                "responder_output": self.responder_chain,
                "chat_history": lambda x: self.chat_history
            }
            | RunnableLambda(lambda x: format_chain_input(x, "responder_output"))
            | {
                "blockchain_output": self.blockchain_chain,
                "chat_history": lambda x: self.chat_history
            }
            | RunnableLambda(lambda x: format_chain_input(x, "blockchain_output"))
            | {
                "animation_output": self.animation_chain,
                "chat_history": lambda x: self.chat_history
            }
            | RunnableLambda(lambda x: format_chain_input(x, "animation_output"))
            | {
                "final_output": self.assembler_chain,
                "chat_history": lambda x: self.chat_history
            }
        )
    
    async def callAgent(self, text_input: str) -> str:
        try:
            # Convert chat history to a list of message dictionaries
            parsed_history = [
                {"role": "human" if isinstance(msg, HumanMessage) else "Amara", 
                "content": msg.content} 
                for msg in self.chat_history
                        ]

            # Use parsed history in ainvoke
            chain_response = await self.superAgent.ainvoke({
                "input": text_input,
                "chat_history": parsed_history
            })
            
            
         
            # Add the human message to chat history before processing
            self.chat_history.append(HumanMessage(content=text_input))
            # chain_response = await self.superAgent.ainvoke(text_input)
            
            if not chain_response or "final_output" not in chain_response:
                raise ValueError("Invalid response format from chain")
                
            final_output = chain_response["final_output"]
            
            # Add the AI response to chat history
            self.chat_history.append(AIMessage(content=final_output))
            
            return final_output
            
        except Exception as e:
            logging.error(f"Error in callAgent: {str(e)}")
            return json.dumps({
                "response": f"I apologize, but I encountered an error: {str(e)}",
                "action": None,
                "interaction": {
                    "animation": "Talking_0",
                    "face": "sad"
                }
            })
            
    def generateTextFromVoice(self, audio_path: str) -> str:
        """
        Records audio, saves it to a file, and transcribes it using OpenAI Whisper.
        """
        print("Loading Whisper model...")
        model = whisper.load_model("turbo")
        
        print("Transcribing audio...", audio_path)
        result = model.transcribe(audio_path, fp16=False)
        
        print("Transcription:")
        print(result["text"])
        return result["text"]
    
    def generateVoice(self, text: str, audio_out_path: str = "./app/audio/out/ai_voice.mp3") -> None:
        """
        Generates voice output using ElevenLabs API.
        """
        warnings.simplefilter("ignore", category=FutureWarning)
        client = ElevenLabs(
            api_key=os.environ["ELEVEN_LABS_API_KEY"],
        )
        audio = client.generate(
            text=text,
            voice="Charlotte",
            model="eleven_multilingual_v2",
            stream=True
        )
        save(audio, audio_out_path)