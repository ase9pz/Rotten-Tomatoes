import kalshi_python
import kalshi_client
from KalshiClientsBaseV2ApiKey import ExchangeClient
import time
import uuid
import requests
import json
from datetime import datetime as dt
from urllib3.exceptions import HTTPError
from dateutil import parser
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime
from datetime import timedelta

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.exceptions import InvalidSignature
import time 
import base64
import requests
from bs4 import BeautifulSoup
import math
import matplotlib.pyplot as plt
import pprintpp as pprint
#First we need to start with the movie on the Rotten Tomatoes Page

#==========================================================
#Get Rotten Tomatoes Score

url = "https://www.rottentomatoes.com/m/mufasa"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114python T.0.0.0 Safari/537.36"
}
response = requests.get(url, headers=headers)

soup = BeautifulSoup(response.content, "html.parser")

tomatometer_element = soup.find("rt-text", {"slot": "criticsScore"})

if tomatometer_element:
    tomatometer_score = tomatometer_element.text.strip()
    print(f"Tomatometer Score: {tomatometer_score}")
else:
    print("Tomatometer Score not found.")

#===========================================================
#Get Review Count


url = "https://www.rottentomatoes.com/m/mufasa"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
}
response = requests.get(url, headers=headers)

soup = BeautifulSoup(response.content, "html.parser")

review_element = soup.find("rt-link", {"slot": "criticsReviews"})

if review_element:
    review_count = review_element.text.strip()
    print(f"Review Count: {review_count}")
else:
    print("Review Count not found.")

#===========================================================
#Access Kalshi client with API key

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend

def load_private_key_from_file(private_key_path):
    with open(private_key_path, "rb") as key_file:
        private_key = serialization.load_pem_private_key(
            key_file.read(),
            password=None,  # or provide a password if your key is encrypted
            backend=default_backend()
        )
    return private_key


key_id = "039347d9-0f10-46a8-80ab-e353f31080a4"

prod_api_base = "https://trading-api.kalshi.com/trade-api/v2"

private_key_path = "C:\\Users\\19413\\Downloads\\Nemmo2k.txt"
exchange_client = ExchangeClient(exchange_api_base=prod_api_base, key_id = key_id, private_key=load_private_key_from_file(private_key_path))

#===============================================================
#Check Exchance Status and balance

print(exchange_client.get_exchange_status())

from kalshi_client.client import KalshiClient
from kalshi_client.utils import load_private_key_from_file
import os

if __name__ == "__main__":
    key_id = "039347d9-0f10-46a8-80ab-e353f31080a4"
    
    private_key_path = "C:\\Users\\19413\\Downloads\\Nemmo2k.txt"
    
    kalshi_client = KalshiClient(key_id=key_id, private_key=load_private_key_from_file(private_key_path))
    
    print(kalshi_client.get_balance())

#==========================================================
#Identify our event
eventTicker = 'KXRTMUFASA'
eventResponse = kalshi_client.get_event(eventTicker)

import pandas as pd

# Assuming eventResponse is a dictionary containing the JSON data
data = eventResponse  # Assuming eventResponse is already a dictionary

# Initialize an empty DataFrame to store the markets
df = pd.DataFrame(columns=["ticker", "details"])

# Extract all 'ticker' entries that match the format 'KXRTMUFASA-<number>'
for market in data.get("markets", []):
    if "ticker" in market and market["ticker"].startswith("KXRTMUFASA-"):
        # Append the new row to the DataFrame
        new_row = {
            "ticker": market["ticker"],
            "details": market.get("details", "")
        }
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)

print(df)







