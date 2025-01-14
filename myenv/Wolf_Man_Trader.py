import datetime
import requests
import pandas as pd
import math
import time
import re
import matplotlib.pyplot as plt
from bs4 import BeautifulSoup
from kalshi_client.client import KalshiClient
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
from typing import List, Tuple, Optional
from scipy.stats import norm
import uuid
# Helper function to load private key
def load_private_key_from_file(private_key_path: str):
    with open(private_key_path, "rb") as key_file:
        private_key = serialization.load_pem_private_key(
            key_file.read(),
            password=None,
            backend=default_backend()
        )
    return private_key

# Helper function to fetch Rotten Tomatoes data
def get_rotten_tomatoes_data(url: str, headers: dict) -> Tuple[Optional[int], Optional[int]]:
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.content, "html.parser")

    # Extract tomatometer score
    tomatometer_element = soup.find("rt-text", {"slot": "criticsScore"})
    tomatometer_score_grab = int(tomatometer_element.text.strip("%")) if tomatometer_element else None
    
    # Extract review count
    review_element = soup.find("rt-link", {"slot": "criticsReviews"})
    review_count = int(review_element.text.strip().replace(" Reviews", "")) if review_element else None
    tomatometer_score =  round(100 * round((tomatometer_score_grab/100 * review_count), 0) / review_count, 3) #calculate precise tomatometer score

    return tomatometer_score, review_count

# Updated function to calculate bucket chances
def calculate_future_bucket_chances(
    min_reviews: int, max_reviews: int, initial_reviews: int,
    initial_rating: float, bucket_threshold: float, true_tomatometer_score: float
) -> List[Tuple[int, float]]:
    """
    Calculate the probability of exceeding a bucket threshold based on future reviews only.
    
    Parameters:
        min_reviews: Minimum total review count to simulate.
        max_reviews: Maximum total review count to simulate.
        initial_reviews: Current number of reviews (given).
        initial_rating: Current tomatometer score (given, 0-1).
        bucket_threshold: Threshold to calculate probability for (0-1).
        true_tomatometer_score: Assumed probability of a positive review for future reviews (0-1).

    Returns:
        A list of tuples with total review count and probability of exceeding the threshold.
    """
    results = []

    # Fixed historical positive reviews
    num_pos_reviews = round(initial_rating * initial_reviews)

    for exact_final_reviews in range(min_reviews, max_reviews + 1):
        additional_reviews = exact_final_reviews - initial_reviews

        def binomial_probability(n, k, p):
            return math.comb(n, k) * (p ** k) * ((1 - p) ** (n - k))

        # Simulate outcomes for additional reviews only
        total_probability = 0.0
        for future_pos_reviews in range(0, additional_reviews + 1):
            final_pos_reviews = num_pos_reviews + future_pos_reviews
            final_rating = final_pos_reviews / exact_final_reviews

            # Add probability if final_rating meets or exceeds the threshold
            if final_rating >= bucket_threshold:
                probability = binomial_probability(additional_reviews, future_pos_reviews, true_tomatometer_score)
                total_probability += probability

        results.append((exact_final_reviews, total_probability))

    return results

# Main loop
while True:
    try:
        current_time = datetime.datetime.now()
        print(current_time)

        # Rotten Tomatoes data
        url = f"https://www.rottentomatoes.com/m/wolf_man_2025?nocache={int(time.time())}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
        }
        tomatometer_score, review_count = get_rotten_tomatoes_data(url, headers)
        print(f"Tomatometer Score: {tomatometer_score}, Review Count: {review_count}")

        # Kalshi client setup
        key_id = "682d265a-6f68-460e-9668-5a3721eef16d"
        private_key_path = "/Users/nemmociccone/Documents/Nemmo4k.txt"
        kalshi_client = KalshiClient(key_id=key_id, private_key=load_private_key_from_file(private_key_path))

        # Kalshi balance check
        balance = kalshi_client.get_balance()["balance"]
        print(f"Cash: ${balance/100}")

        # Market data setup
        eventTicker = 'KXRTWOLFMAN'
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

        true_tomatometer_score = None
        effective_tomatometer_score = true_tomatometer_score if true_tomatometer_score is not None else tomatometer_score
        for _, market in markets_df.iterrows():
            bucket_threshold = market['threshold'] / 100
            prob = calculate_future_bucket_chances(review_count, 70, int(review_count)+1,
                                                   tomatometer_score / 100,
                                                   bucket_threshold,
                                                   effective_tomatometer_score / 100)
            # Extract probabilities and review counts
            review_counts, probabilities = zip(*prob)
            probability_curves.append((review_counts, probabilities))

            # Calculate "my yes odds" using weighted probability
            weights = norm.pdf(review_counts, loc=55, scale=5)  # Example mean and std dev
            weighted_yes_odds = sum(probabilities[i] * weights[i] for i in range(len(review_counts))) / sum(weights)
            my_yes_odds_list.append(round(weighted_yes_odds * 100, 2))  # Convert to percentage

            # Calculate edge as difference between my yes odds and market price
            yes_market_price = complete_odds_df.loc[market.name, 'yes book odds']  # Access by index
            yes_edge = round(weighted_yes_odds * 100 - yes_market_price, 2)
            yes_edges.append(yes_edge)

            no_market_price = complete_odds_df.loc[market.name, 'no book odds']
            no_edge = round((1 - weighted_yes_odds)*100 - no_market_price, 2)
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

        print(final_df[['ticker', 'my yes odds','yes edge', 'my no odds', 'no edge', 'position', 'yes bid', 'no bid']])

        #Plot results
        # plt.figure(figsize=(14, 8))
        # for i, (review_counts, probabilities) in enumerate(probability_curves):
        #     color = f'C{i}'  # Cycle through default matplotlib colors
        #     yes_market_price = float(complete_odds_df['yes book odds'].iloc[i])
        #     if 5 < yes_market_price < 95:
        #         plt.plot(review_counts, probabilities, label=f'Market {markets_df.ticker.iloc[i]}', color=color)
        #         plt.axhline(y=yes_market_price / 100, color=color, linestyle='--', label=f'Market Price {markets_df.ticker.iloc[i]}')

        # plt.xlabel('Final Review Count')
        # plt.ylabel('Probability')
        # plt.title('Probability vs. Final Review Count')
        # plt.grid(True)
        # plt.legend(loc='lower right')
        # plt.show()
        

        #Threshold for closing positions
        close_threshold = -2  # Edge below this value triggers closing a position
        unit_size = 1
        # Place "yes" contracts
        for _, row in final_df.iterrows():
            count = 0
            if row['yes edge'] >= 5 and row['position'] <= 157:
                orderUuid = str(uuid.uuid4())
                orderResponse = kalshi_client.create_order(
                    client_order_id=orderUuid,
                    side="yes",
                    action="buy",
                    count=1 * unit_size,
                    type="market",
                    ticker=row['ticker'],
                )
                count+1
                print(f"Market buy (yes): {orderResponse}")

        # Place "no" contracts
        for _, row in final_df.iterrows():
            if row['no edge'] >= 5 and (abs(row['position']) <= 20 or pd.isna(row['position'])):
                orderUuid = str(uuid.uuid4())
                orderResponse = kalshi_client.create_order(
                    client_order_id=orderUuid,
                    side="no",
                    action="buy",
                    count=1 * unit_size,
                    type="market",
                    ticker=row['ticker'],
                )
                print(f"Market buy (no): {orderResponse}")

        # Close positions when the edge turns slightly negative
        # for _, row in final_df.iterrows():
        #     if abs(row['position'] > 0):
        #         position = row['position']
        #         # Closing "yes" contracts if edge is below the threshold
        #         if row['yes edge'] < close_threshold and ((row['my yes odds'] == 0.00 and row['yes edge == -1.00']) is False):
        #             orderUuid = str(uuid.uuid4())
        #             orderResponse = kalshi_client.create_order(
        #                 client_order_id=orderUuid,
        #                 side="yes",
        #                 action="sell",
        #                 count=int(position),
        #                 type="market",
        #                 ticker=row['ticker'],
        #             )
        #             print(f"Market sell (yes): {orderResponse}")
        #         # Closing "no" contracts if edge is below the threshold
        #         #Fix code to close positions, need to make sure selling no's doesn't open yes's, and account for highest bid when selling

        #         if row['no edge'] < close_threshold and (row['no bid'] - row['no book odds'] <=3) and count  == 0:  
        #             orderUuid = str(uuid.uuid4())
        #             orderResponse = kalshi_client.create_order(
        #                 client_order_id=orderUuid,
        #                 side="no",
        #                 action="sell",
        #                 count=int(position),
        #                 type="market",
        #                 ticker=row['ticker'],
        #             )
        #             print(f"Market sell (no): {orderResponse}")

        time.sleep(60)

    except Exception as e:
        print(f"Error occurred: {e}")
        time.sleep(60)  # Retry after 1 minute
