import pandas as pd
import numpy as np
import math
import logging

logging.basicConfig(filename='flight_risk_trade_log.txt', level=logging.INFO, 
                    format='%(asctime)s - %(message)s')

FINAL_REVIEW_ESTIMATE = 77  # estimate final review count
FINAL_REVIEW_STDDEV = 5     
TRADE_SIZE = 1              

def binomial_probability(n, k, p):
    """Compute the binomial probability."""
    try:
        return math.comb(n, k) * (p ** k) * ((1 - p) ** (n - k))
    except ValueError:
        return 0  # Handle extreme cases

def calculate_future_bucket_chances(initial_reviews, initial_rating, bucket_threshold):
    """
    Calculate the weighted probability of exceeding the bucket threshold by considering a range
    of possible final review counts weighted by a discrete normal distribution.
    """
    if pd.isna(initial_rating) or pd.isna(initial_reviews):
        logging.warning(f"NaN values found: reviews: {initial_reviews}, Rating: {initial_rating}")
        return None  

    num_pos_reviews = round(initial_rating * initial_reviews)
    
    min_final = initial_reviews
    max_final = int(FINAL_REVIEW_ESTIMATE + 3 * FINAL_REVIEW_STDDEV)
    possible_final_reviews = np.arange(min_final, max_final + 1)
    
   
    weights = np.exp(-0.5 * ((possible_final_reviews - FINAL_REVIEW_ESTIMATE) / FINAL_REVIEW_STDDEV) ** 2)
    weights /= np.sum(weights)
    
    total_probability = 0
    
    # Loop over each possible final review count and calculate the weighted probability
    for final_reviews, weight in zip(possible_final_reviews, weights):
        additional_reviews = final_reviews - initial_reviews
        if additional_reviews < 0:
            continue  

        probability_for_this_final = 0
        # Sum the binomial probabilities for future positive reviews that result in a final score
        # above the bucket threshold.
        for future_pos_reviews in range(0, additional_reviews + 1):
            final_score = (num_pos_reviews + future_pos_reviews) / final_reviews
            if final_score >= bucket_threshold:
                probability_for_this_final += binomial_probability(additional_reviews, future_pos_reviews, initial_rating)
                
        # Weight the probability for this possible final review count.
        total_probability += weight * probability_for_this_final
        
    return total_probability

def process_trades(csv_file, output_file):
    df = pd.read_csv(csv_file)
    
    positions = {}  # e.g., positions[market] = {'yes': current_yes_count, 'no': current_no_count}
    
    with open(output_file, 'w') as f:
        for _, row in df.iterrows():
            market = row['market']
            bucket_threshold = (int(market.split('-')[-1]) + 0.5) / 100
            timestamp = row['timestamp']
            
            if market not in positions:
                positions[market] = {'yes': 0, 'no': 0}
            
            try:
                initial_rating = float(row['Score']) / 100
                review_count = int(row['Review_Count'])
                
                if np.isnan(initial_rating) or np.isnan(review_count):
                    logging.warning(f"Skipping trade for {market}: Invalid data -> Score: {row['Score']}, Reviews: {row['Review_Count']}")
                    continue  

                prob = calculate_future_bucket_chances(review_count, initial_rating, bucket_threshold)
                if prob is None:
                    logging.warning(f"Skipping trade for {market}: Probability calculation failed.")
                    continue

                my_yes_odds = round(prob * 100, 2)
                yes_ask = eval(row['yes_ask'])['close']  # Extract lowest ask price
                yes_bid = eval(row['yes_bid'])['close']
                no_ask = 100 - yes_bid
                no_bid = 100 - yes_ask
                my_no_odds = 100 - my_yes_odds

                # Check to open a Yes position
                if my_yes_odds >= yes_ask + 10:
                    positions[market]['yes'] += TRADE_SIZE
                    logging.info(f"Opening 1 Yes: Market {market}, My Odds {my_yes_odds}, Market Ask {yes_ask}, Time {timestamp}")
                
                # Check to close Yes positions only if we hold any
                if positions[market]['yes'] > 0 and my_yes_odds <= yes_bid -2:
                    logging.info(f"Closing all Yes: Market {market}, My Odds {my_yes_odds}, Market Bid {yes_bid}, Time {timestamp}")
                    positions[market]['yes'] = 0

                # Check to open a No position
                if my_no_odds >= no_ask + 10:
                    positions[market]['no'] += TRADE_SIZE
                    logging.info(f"Opening 1 No: Market {market}, My Odds {my_no_odds}, Market Ask {no_ask}, Time {timestamp}")

                # Check to close No positions only if we hold any
                if positions[market]['no'] > 0 and my_no_odds <= no_bid - 2:
                    logging.info(f"Closing all No: Market {market}, My Odds {my_no_odds}, Market Bid {no_bid}, Time {timestamp}")
                    positions[market]['no'] = 0

                if not ((my_yes_odds >= yes_ask + 10) or 
                        (positions[market]['yes'] > 0 and my_yes_odds <= yes_bid - 2) or
                        (my_no_odds >= no_ask + 10) or 
                        (positions[market]['no'] > 0 and my_no_odds <= no_bid - 2)):
                    logging.info(f"No Trade: Market {market}, My Odds {my_yes_odds}, Yes Ask {yes_ask}, No Ask {no_ask}, Time {timestamp}")

            except Exception as e:
                logging.error(f"Error processing market {market}: {e}")

process_trades('flight_risk_market_data.csv', 'output.txt')
