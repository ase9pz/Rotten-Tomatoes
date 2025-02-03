import datetime
import requests
import pandas as pd
import math
import time
import re
from bs4 import BeautifulSoup
from kalshi_client.client import KalshiClient
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
from typing import List, Tuple, Optional
import uuid
import numpy as np

def load_private_key_from_file(private_key_path: str):
    with open(private_key_path, "rb") as key_file:
        private_key = serialization.load_pem_private_key(
            key_file.read(),
            password=None,
            backend=default_backend()
        )
    return private_key

def get_rotten_tomatoes_data(url: str, headers: dict) -> Tuple[Optional[int], Optional[int]]:
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.content, "html.parser")

    tomatometer_element = soup.find("rt-text", {"slot": "criticsScore"})
    tomatometer_score_grab = int(tomatometer_element.text.strip("%")) if tomatometer_element else None
    
    review_element = soup.find("rt-link", {"slot": "criticsReviews"})
    review_count = int(review_element.text.strip().replace(" Reviews", "")) if review_element else None
    tomatometer_score =  round(100 * round((tomatometer_score_grab/100 * review_count), 0) / review_count, 3) #calculate precise tomatometer score

    return tomatometer_score, review_count


# Updated function to calculate bucket chances
def binomial_probability(n, k, p):
    """Compute the binomial probability."""
    try:
        return math.comb(n, k) * (p ** k) * ((1 - p) ** (n - k))
    except ValueError:
        return 0  


FINAL_REVIEW_ESTIMATE = 60   # Estimate the final review count
FINAL_REVIEW_STDDEV = 5

def calculate_future_bucket_chances(initial_reviews, initial_rating, bucket_threshold):
  
    if pd.isna(initial_rating) or pd.isna(initial_reviews):
        return None  

    num_pos_reviews = round(initial_rating * initial_reviews)
    
    
    min_final = initial_reviews
    max_final = int(FINAL_REVIEW_ESTIMATE + 3 * FINAL_REVIEW_STDDEV)
    possible_final_reviews = np.arange(min_final, max_final + 1)
    
    
    weights = np.exp(-0.5 * ((possible_final_reviews - FINAL_REVIEW_ESTIMATE) / FINAL_REVIEW_STDDEV) ** 2)

    weights /= np.sum(weights)
    
    total_probability = 0
    
    for final_reviews, weight in zip(possible_final_reviews, weights):
        additional_reviews = final_reviews - initial_reviews
        if additional_reviews < 0:
            continue  
        
        probability_for_this_final = 0
        
        for future_pos_reviews in range(0, additional_reviews + 1):
            final_score = (num_pos_reviews + future_pos_reviews) / final_reviews
            if final_score >= bucket_threshold:
                probability_for_this_final += binomial_probability(additional_reviews, future_pos_reviews, initial_rating)
                
        total_probability += weight * probability_for_this_final
        
    return total_probability

while True:
    try:
        current_time = datetime.datetime.now()
        print(current_time)

        url = f"https://www.rottentomatoes.com/m/heart_eyes?nocache={int(time.time())}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
        }
        tomatometer_score, review_count = get_rotten_tomatoes_data(url, headers)
        print(f"Tomatometer Score: {tomatometer_score}, Review Count: {review_count}")

        key_id = "682d265a-6f68-460e-9668-5a3721eef16d"
        private_key_path = "/Users/nemmociccone/Documents/Nemmo4k.txt"
        #private_key_path = "/home/ec2-user/Trading/Nemmo4k.txt"
        kalshi_client = KalshiClient(key_id=key_id, private_key=load_private_key_from_file(private_key_path))

        balance = kalshi_client.get_balance()["balance"]
        print(f"Cash: ${balance/100}")

        eventTicker ='KXRTHEARTEYES'
        data = kalshi_client.get_event(event_ticker=eventTicker)

        df = pd.DataFrame(columns=["ticker", "threshold"])
        for market in data.get("markets", []):
            if "ticker" in market and market["ticker"].startswith(f"{eventTicker}-"):
                match = re.search(fr'{eventTicker}-(\d+)', market["ticker"])
                if match:
                    threshold_value = int(match.group(1)) + 0.5
                    if not df.empty:
                        df = pd.concat([df, pd.DataFrame([{ "ticker": market["ticker"], "threshold": threshold_value }])], ignore_index=True)
                    else:
                        df = pd.DataFrame([{ "ticker": market["ticker"], "threshold": threshold_value }])


        markets_df = df
        # Get book odds (asks) from Kalshi
        book_yes_odds_list = []
        for index, market in markets_df.iterrows():
            marketTicker = markets_df['ticker'][index]
            marketResponse = kalshi_client.get_market(marketTicker)
            if marketResponse and 'market' in marketResponse:
                book_yes_odds_list.append(marketResponse['market'].get('yes_ask'))
        book_no_odds_list = []
        for index, market in markets_df.iterrows():
            marketTicker = markets_df['ticker'][index]
            marketResponse = kalshi_client.get_market(marketTicker)
            if marketResponse and 'market' in marketResponse:
                book_no_odds_list.append(marketResponse['market'].get('no_ask'))

        # Get book bids from Kalshi
        book_yes_bids_list = []
        for index, market in markets_df.iterrows():
            marketTicker = markets_df['ticker'][index]
            marketResponse = kalshi_client.get_market(marketTicker)
            if marketResponse and 'market' in marketResponse:
                book_yes_bids_list.append(marketResponse['market'].get('yes_bid'))
        book_no_bids_list = []
        for index, market in markets_df.iterrows():
            marketTicker = markets_df['ticker'][index]
            marketResponse = kalshi_client.get_market(marketTicker)
            if marketResponse and 'market' in marketResponse:
                book_no_bids_list.append(marketResponse['market'].get('no_bid'))
                
        complete_odds_df = markets_df.copy()
        complete_odds_df['yes book odds'] = book_yes_odds_list
        complete_odds_df['no book odds'] = book_no_odds_list
        complete_odds_df['yes bid'] = book_yes_bids_list
        complete_odds_df['no bid'] = book_no_bids_list
        # Calculate custom odds and edges
        my_odds_df = complete_odds_df.copy()
        my_yes_odds_list = []
        yes_edges = []
        no_edges = []
        probability_curves = []

        for _, market in markets_df.iterrows():
            bucket_threshold = market['threshold'] / 100
            prob = calculate_future_bucket_chances(review_count, tomatometer_score/100, bucket_threshold)
            

            my_yes_odds = round(prob * 100, 2)
            my_yes_odds_list.append(my_yes_odds)

            yes_market_price = complete_odds_df.loc[market.name, 'yes book odds']
            no_market_price = complete_odds_df.loc[market.name, 'no book odds']

            yes_edge = round(my_yes_odds - yes_market_price, 2)
            no_edge = round((100 - my_yes_odds) - no_market_price, 2)
            yes_edges.append(yes_edge)
            no_edges.append(no_edge)

        my_odds_df['my yes odds'] = my_yes_odds_list
        my_odds_df['my no odds'] = [100 - x for x in my_yes_odds_list]
        my_odds_df['yes edge'] = yes_edges
        my_odds_df['no edge'] = no_edges

        # Add current open positions
        my_positions = kalshi_client.get_positions()
        filtered_positions = [
            {'ticker': position['ticker'], 'position': position['position']}
            for position in my_positions['market_positions']
            if position['position'] != 0
        ]

        if not filtered_positions:
            my_positions_df = pd.DataFrame(columns=["ticker", "position"])
        else:
            my_positions_df = pd.DataFrame(filtered_positions)

        final_df = my_odds_df.merge(my_positions_df, on="ticker", how="left")

        print(final_df[['ticker', 'my yes odds', 'yes book odds', 'yes edge', 'my no odds', 'no book odds', 'no edge', 'yes bid', 'no bid', 'position']])

        
        close_threshold = -2
        unit_size = 1

        #Place "yes" contracts
        for _, row in final_df.iterrows():
            traded_yes = 0  # Flag for tracking "yes" trade
            traded_no = 0   # Flag for tracking "no" trade
            
            # Place "yes" contracts if not already traded
            if row['yes edge'] >= 10 and row['position'] < 70:
                orderUuid = str(uuid.uuid4())
                orderResponse = kalshi_client.create_order(
                    client_order_id=orderUuid,
                    side="yes",
                    action="buy",
                    count=1 * unit_size,
                    type="market",
                    ticker=row['ticker'],
                )
                traded_yes = 1  # Mark as traded
                print(f"Market buy (yes): {orderResponse}")

            # Place "no" contracts if not already traded and no "yes" was traded
            if row['no edge'] >= 10  and row['position'] < 70:
                orderUuid = str(uuid.uuid4())
                orderResponse = kalshi_client.create_order(
                    client_order_id=orderUuid,
                    side="no",
                    action="buy",
                    count=1 * unit_size,
                    type="market",
                    ticker=row['ticker'],
                )
                traded_no = 1  # Mark as traded
                print(f"Market buy (no): {orderResponse}")

            # Close positions when the edge turns slightly negative
            if abs(row['position']) > 0:
                position = row['position']
                
                # Closing "yes" contracts if edge is below the threshold and "yes" was traded
                if row['my yes odds'] < row['yes bid'] -2:
                    orderUuid = str(uuid.uuid4())
                    orderResponse = kalshi_client.create_order(
                        client_order_id=orderUuid,
                        side="yes",
                        action="sell",
                        count=int(position),
                        type="market",
                        ticker=row['ticker'],
                    )
                    traded_yes = 0  # Reset after the sale
                    print(f"Market sell (yes): {orderResponse}")
                
                # Closing "no" contracts if edge is below the threshold and "no" was traded
                if row['my no odds'] < row['no bid'] - 2 and row['position'] < 0:
                    orderUuid = str(uuid.uuid4())
                    orderResponse = kalshi_client.create_order(
                        client_order_id=orderUuid,
                        side="no",
                        action="sell",
                        count=int(position*-1),
                        type="market",
                        ticker=row['ticker'],
                    )
                    traded_no = 0  # Reset after the sale
                    print(f"Market sell (no): {orderResponse}")


        time.sleep(60)

    except Exception as e:
        print(f"Error occurred: {e}")
        time.sleep(60)  
