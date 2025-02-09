import requests

# Define the claim API URL
claim_url = "https://api-v1.zealy.io/communities/oceanprotocol/quests/v2/2b810fcd-cd63-43d1-80f0-85f8026def1d/claim"

# Headers (Ensure you include required headers)
headers = {
    "accept": "application/json",
    "origin": "https://zealy.io",
    "referer": "https://zealy.io/",
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-site",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
    "authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySWQiOiIyNzVkNTczOS03ZjRmLTQzODUtOGFkMi1hMTdkMjRmYjU4NDgiLCJhY2NvdW50VHlwZSI6ImVtYWlsIiwiaWF0IjoxNzM2NDk2ODQ0LCJleHAiOjE3MzkwODg4NDR9.C15yClkI1yAPCPp9uEhsnuwii4FIMnb2uQTyuMgUOF8",  # Set the access token dynamically
    "x-next-app-key": "",  # Add if needed
}

# Cookies (You can get them dynamically from browser storage)
cookies = {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySWQiOiIyNzVkNTczOS03ZjRmLTQzODUtOGFkMi1hMTdkMjRmYjU4NDgiLCJhY2NvdW50VHlwZSI6ImVtYWlsIiwiaWF0IjoxNzM2NDk2ODQ0LCJleHAiOjE3MzkwODg4NDR9.C15yClkI1yAPCPp9uEhsnuwii4FIMnb2uQTyuMgUOF8",
    "connect.sid": "s%3Ai-x0vi2iqL3RsdAOXmqWEtGd2EaF8stt.7bOrMpkmNdQGVLNFyU78II9FxDu6czPAddCO%2FrSuqIg",  # If needed
    # Add other cookies if necessary
}

# Make the claim request
response = requests.post(claim_url, headers=headers, cookies=cookies)

# Print response
print(response.status_code, response.text)
