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
import kalshi_python
import uuid
import _uuid
import time

import os
os.system('cls' if os.name == 'nt' else 'clear')

#==================================================================
# Get current Rotten Tomatoes score 


import requests
from bs4 import BeautifulSoup
import time

url = f"https://www.rottentomatoes.com/m/sonic_the_hedgehog_3?nocache={int(time.time())}"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
}

response = requests.get(url, headers=headers)

soup = BeautifulSoup(response.content, "html.parser")

# Get the Tomatometer score
tomatometer_element = soup.find("rt-text", {"slot": "criticsScore"})
tomatometer_score = int(tomatometer_element.text.strip("%")) if tomatometer_element else None
print(f'Tomatometer Score: {tomatometer_score}')

# Get the review count
review_element = soup.find("rt-link", {"slot": "criticsReviews"})
review_count = int(review_element.text.strip().replace(" Reviews", "")) if review_element else None
print(f'Review Count: {review_count}')

#===================================================================
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

#==================================================================
# Check Exchange Status and balance
balance = kalshi_client.get_balance()


#=================================================================
# Create a data frame with every market for our event
eventTicker = 'KXRTSONIC3'
eventResponse = kalshi_client.get_event(event_ticker=eventTicker)

data = kalshi_client.get_event(event_ticker= eventTicker)

df = pd.DataFrame(columns=["ticker", "threshold"])

for market in data.get("markets", []):
    if "ticker" in market and market["ticker"].startswith(f"{eventTicker}-"):
        match = re.search(fr'{eventTicker}-(\d+)', market["ticker"])
        if match:
            threshold_value = int(match.group(1)) + 1
            new_row = {
                "ticker": market["ticker"],
                "threshold": threshold_value
            }
            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)

markets_df = df  

#===================================================================================
# Calculate my odds by running combinatorics script

initial_reviews = review_count
initial_rating = tomatometer_score / 100
my_odds_df = markets_df.copy()
my_yes_odds_list = []

for index, market in markets_df.iterrows():
    bucket_threshold = market['threshold'] / 100
    initial_reviews = int(review_count)
    initial_rating = int(tomatometer_score) / 100

    def bucket_chance(final_reviews):
        additional_reviews = final_reviews - initial_reviews     
        num_pos_reviews = round(initial_rating * initial_reviews)  #

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

    range_min = initial_reviews
    review_range = range(initial_reviews, 200)  
    total_prob_sum = 0  
    count = 0  

    for final_reviews in review_range:
        prob = bucket_chance(final_reviews)
        total_prob_sum += prob  
        count += 1  

    average_probability = total_prob_sum / count
    my_yes_odds_list.append(round(average_probability*100, 3))

my_no_odds_list = []                #Take complement of each "yes" chance to get theoretical "no" chance
for i in my_yes_odds_list:
    my_no_odds_list.append(100 - i)



my_odds_df['my yes odds'] = my_yes_odds_list
my_odds_df['my no odds'] = my_no_odds_list

#===============================================================
# Get book odds (asks) from Kalshi

book_yes_odds_list = []  
for index, market in markets_df.iterrows():
    marketTicker = markets_df['ticker'][index]
    marketResponse = kalshi_client.get_market(marketTicker)
    if marketResponse and 'market' in marketResponse:  
        fields_to_extract = ['yes_ask']
        for field in fields_to_extract:
            value = marketResponse['market'].get(field)
            book_yes_odds_list.append(value)
book_no_odds_list = []
for index, market in markets_df.iterrows():
    marketTicker = markets_df['ticker'][index]
    marketResponse = kalshi_client.get_market(marketTicker)
    if marketResponse and 'market' in marketResponse:  
        fields_to_extract = ['no_ask']
        for field in fields_to_extract:
            value = marketResponse['market'].get(field)
            book_no_odds_list.append(value)

complete_odds_df = my_odds_df.copy()
complete_odds_df['yes book odds'] = book_yes_odds_list
complete_odds_df['no book odds'] = book_no_odds_list
#=================================================================
# Get bids prices for each market
yes_bids_list = []
for index, market in complete_odds_df.iterrows():
    marketTicker = markets_df['ticker'][index]
    marketResponse = kalshi_client.get_market(marketTicker)
    if marketResponse and 'market' in marketResponse:  
        fields_to_extract = ['yes_bid']
        for field in fields_to_extract:
            value = marketResponse['market'].get(field)
            yes_bids_list.append(value)

no_bids_list = []
for index, market in markets_df.iterrows():
    marketTicker = markets_df['ticker'][index]
    marketResponse = kalshi_client.get_market(marketTicker)
    if marketResponse and 'market' in marketResponse:  
        fields_to_extract = ['no_bid']
        for field in fields_to_extract:
            value = marketResponse['market'].get(field)
            no_bids_list.append(value)
bids_asks_df = complete_odds_df.copy()
bids_asks_df['yes bid'] = yes_bids_list
bids_asks_df['no bid'] = no_bids_list

#================================================================
# Iterate through complete odds df and identify trades with edge 

yes_edge = complete_odds_df['my yes odds'] - complete_odds_df['yes book odds']
no_edge = complete_odds_df['my no odds'] - complete_odds_df['no book odds']

edge_df = bids_asks_df.copy()
edge_df['yes edge'] = yes_edge
edge_df['no edge'] = no_edge 

trade_yes_list = []
trade_no_list = []
for index, market in edge_df.iterrows():
    if market['yes edge'] > 8:
        trade_yes_list.append(f'buy')
    else:
        trade_yes_list.append(f'none')

    if market['no edge'] > 8:
        trade_no_list.append(f'buy')
    else:
        trade_no_list.append(f'none')

trade_df = edge_df.copy()
trade_df['trade yes'] = trade_yes_list
trade_df['trade no'] = trade_no_list
print(trade_df)
#===============================================================
# Go through trade_list and place limit orders to open positions
"""
for _, row in trade_df.iterrows():
    if row['trade yes'] == 'buy':
        orderUuid = str(uuid.uuid4())
        orderResponse = kalshi_client.create_order(
            client_order_id=orderUuid,
            side="yes",
            action='buy',
            count=1,
            type='limit',
            yes_price = row['yes book odds']-1,
            ticker=row['ticker'],
        )
        print(orderResponse)
"""
"""
for _, row in trade_df.iterrows():
    if row['trade no'] == 'buy':
        orderUuid = str(uuid.uuid4())
        orderResponse = kalshi_client.create_order(
            client_order_id=orderUuid,
            side="no",
            action='buy',
            count=1,
            type='limit',
            no_price=row['no book odds']-1,
            ticker=row['ticker'],
        )
        print(orderResponse)
"""
#============================================================
# Go through current positions and sell if needed
my_positions = kalshi_client.get_portfolio_settlements()
print(my_positions)

# Extract the 'settlements' list
settlements = my_positions.get('settlements', [])

# Define the columns you want in the DataFrame
columns = ["ticker", "market_result", "yes_count", "yes_total_cost", 
           "no_count", "no_total_cost", "revenue", "settled_time"]

# Initialize an empty list to hold processed rows
processed_data = []

# Loop through settlements and extract the required fields
for settlement in settlements:
    row = {col: settlement.get(col, None) for col in columns}
    processed_data.append(row)

# Create the DataFrame
df = pd.DataFrame(processed_data)

# Display the DataFrame
print(df)
