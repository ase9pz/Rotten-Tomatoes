from kalshi_client.client import KalshiClient
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
import pandas as pd
import time
import re
import logging

# Configure logging
logging.basicConfig(level=logging.WARNING, format='%(asctime)s - %(levelname)s - %(message)s')

# Load private key
def load_private_key_from_file(private_key_path: str):
    with open(private_key_path, "rb") as key_file:
        private_key = serialization.load_pem_private_key(
            key_file.read(),
            password=None,
            backend=default_backend()
        )
    return private_key

# Kalshi Client Setup
private_key_path = "/Users/nemmociccone/Documents/Nemmo4k.txt"
key_id = "682d265a-6f68-460e-9668-5a3721eef16d"
kalshi_client = KalshiClient(key_id=key_id, private_key=load_private_key_from_file(private_key_path))

# Define manual start and end times for filtering Rotten Tomatoes data
start_timestamp = "2025-02-16 22:37:21.361890"
end_timestamp = "2025-02-20 09:57:11.439278"

# Convert timestamps to datetime
start_time = pd.to_datetime(start_timestamp)
end_time = pd.to_datetime(end_timestamp)

# Event ticker
event_ticker = "KXRTTHEMONKEY"

# Get all markets for the event
markets_data = kalshi_client.get_event(event_ticker=event_ticker)
markets_df = pd.DataFrame()

for market in markets_data.get("markets", []):
    if "ticker" in market and market["ticker"].startswith(f"{event_ticker}-"):
        match = re.search(fr'{event_ticker}-(\d+)', market["ticker"])
        if match:
            threshold_value = int(match.group(1)) + 0.5
            new_row = {
                "market_ticker": market["ticker"],
                "threshold": threshold_value
            }
            markets_df = pd.concat([markets_df, pd.DataFrame([new_row])], ignore_index=True)

# Initialize an empty DataFrame to store all merged data
all_merged_data = pd.DataFrame()

# Load Rotten Tomatoes data from the CSV file
rt_df = pd.read_csv('/Users/nemmociccone/Downloads/the_monkey_rotten_tomatoes_reviews.csv', skiprows=[0], header=None)
rt_df.columns = ['timestamp', 'Score', 'Review_Count']  

# Ensure 'timestamp' is in datetime format
rt_df['timestamp'] = pd.to_datetime(rt_df['timestamp'])

# Filter Rotten Tomatoes data between the manual start and end timestamps
rt_df_filtered = rt_df[(rt_df['timestamp'] >= start_time) & (rt_df['timestamp'] <= end_time)]


# Iterate through all market tickers and fetch candlestick data
for _, market_row in markets_df.iterrows():
    market_ticker = market_row['market_ticker']
    
    try:
        # Fetch candlestick data for the market
        candlestick_data = kalshi_client.get_market_candlesticks(
            ticker=market_ticker,
            series_ticker=event_ticker,
            start_ts=int(start_time.timestamp()),
            end_ts=int(end_time.timestamp()),
            period_interval=1  # Minute interval
        )["candlesticks"]
    except Exception as e:
        if "400" in str(e):
            logging.warning(f"Skipping market {market_ticker} due to API error: {e}")
            continue  # Skip this market and move to the next
        else:
            raise  # Raise the error for anything other than a 400 error

    # Convert candlestick data to DataFrame
    candlestick_df = pd.DataFrame(candlestick_data)
    if "end_period_ts" not in candlestick_df.columns:
        logging.warning(f"Missing 'end_period_ts' in candlestick data for {market_ticker}. Skipping.")
        continue  # Skip this market
    candlestick_df["timestamp"] = pd.to_datetime(candlestick_df["end_period_ts"], unit="s")

    # Drop unnecessary columns
    candlestick_df = candlestick_df.drop(columns=["volume", "open_interest"], errors="ignore")

    # Add market ticker column
    candlestick_df["market"] = market_ticker

    # Merge Rotten Tomatoes data with candlestick data
    merged_df = pd.merge_asof(
        rt_df_filtered.sort_values(by='timestamp'),
        candlestick_df.sort_values(by='timestamp'),
        on="timestamp",
        direction="nearest"
    )

    # Append to the main DataFrame
    all_merged_data = pd.concat([all_merged_data, merged_df], ignore_index=True)

# Save the final merged data to a CSV
all_merged_data.to_csv("the_monkey_market_data.csv", index=False)
print(f'merged dataframe yielded!')
