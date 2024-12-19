import kalshi_client
from KalshiClientsBaseV2ApiKey import ExchangeClient
import requests
import pandas as pd
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
import requests
from bs4 import BeautifulSoup
import math
import matplotlib.pyplot as plt
import pprintpp as pprint
from kalshi_client.client import KalshiClient
import re
import math
from CombinatoricsScript import bucket_chance

#==================================================================
# Get current Rotten Tomatoes score 
url = "https://www.rottentomatoes.com/m/mufasa"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
}
response = requests.get(url, headers=headers)
soup = BeautifulSoup(response.content, "html.parser")
tomatometer_element = soup.find("rt-text", {"slot": "criticsScore"})
tomatometer_score = int(tomatometer_element.text.strip("%")) if tomatometer_element else None
print(f"Tomatometer Score: {tomatometer_score}")

# Get Review Count
review_element = soup.find("rt-link", {"slot": "criticsReviews"})
review_count = int(review_element.text.strip().replace(" Reviews", "")) if review_element else None
print(f"Review Count: {review_count}")

# Access Kalshi client with API key
def load_private_key_from_file(private_key_path):
    with open(private_key_path, "rb") as key_file:
        private_key = serialization.load_pem_private_key(
            key_file.read(),
            password=None,  # or provide a password if your key is encrypted
            backend=default_backend()
        )
    return private_key

key_id = "039347d9-0f10-46a8-80ab-e353f31080a4"
private_key_path = "C:\\Users\\19413\\Downloads\\Nemmo2k.txt"
kalshi_client = KalshiClient(key_id=key_id, private_key=load_private_key_from_file(private_key_path))

# Check Exchange Status and balance
print(kalshi_client.get_balance())

# Identify our event
eventTicker = 'KXRTMUFASA'
eventResponse = kalshi_client.get_event(event_ticker=eventTicker)

data = kalshi_client.get_event(event_ticker='KXRTMUFASA')

#=================================================================
# Create a data frame with every market for our event

df = pd.DataFrame(columns=["ticker", "threshold"])

for market in data.get("markets", []):
    if "ticker" in market and market["ticker"].startswith("KXRTMUFASA-"):
        match = re.search(r'KXRTMUFASA-(\d+)', market["ticker"])
        if match:
            threshold_value = int(match.group(1)) + 1
            new_row = {
                "ticker": market["ticker"],
                "threshold": threshold_value
            }
            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)

markets_df = df  


initial_reviews = review_count
initial_rating = tomatometer_score / 100
for index, market in markets_df.iterrows():
    bucket_threshold = market['threshold'] / 100  
    initial_reviews = int(review_count)   
    initial_rating = int(tomatometer_score)/100

    def bucket_chance(final_reviews):
        additional_reviews = final_reviews - initial_reviews     
        num_pos_reviews = round(initial_rating * initial_reviews)  

        def binomial_probability(n, k, p):
            return math.comb(n, k) * (p ** k) * ((1 - p) ** (n - k))

        possible_outcomes = []

        for future_pos_reviews in range(0, additional_reviews + 1):
            final_pos_reviews = num_pos_reviews + future_pos_reviews
            final_rating = final_pos_reviews / final_reviews

            probability = binomial_probability(
                additional_reviews, future_pos_reviews, initial_rating
            )

            possible_outcomes.append((final_rating, probability))

        total_probability = sum(prob for rating, prob in possible_outcomes if rating >= bucket_threshold)

        return total_probability


    review_range = range(100, 175)  
    total_prob_sum = 0  
    count = 0  

    for final_reviews in review_range:
        prob = bucket_chance(final_reviews)
        total_prob_sum += prob  
        count += 1  

    average_probability = total_prob_sum / count
    print(f'avg prob above {round(bucket_threshold * 100, 2)} for final reviews {review_range.start}-{review_range.stop - 1}: {average_probability:.4f}')

        
