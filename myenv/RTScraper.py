import time
import datetime
import requests
import csv
from bs4 import BeautifulSoup
from typing import List, Tuple, Optional

from typing import Tuple, Optional
import requests
from bs4 import BeautifulSoup

def get_rotten_tomatoes_data(url: str, headers: dict) -> Tuple[Optional[str], Optional[int]]:
    try:
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.content, "html.parser")

        # Extract tomatometer score
        tomatometer_element = soup.find("rt-text", {"slot": "criticsScore"})
        tomatometer_score_grab = int(tomatometer_element.text.strip("%")) if tomatometer_element else None
    except ValueError:
        tomatometer_score_grab = None
    # Extract review count
    review_element = soup.find("rt-link", {"slot": "criticsReviews"})
    review_count = int(review_element.text.strip().replace(" Reviews", "")) if review_element else None
    if tomatometer_score_grab is None:
        tomatometer_score = "N/A"
    else:
        tomatometer_score =  round(100 * round((tomatometer_score_grab/100 * review_count), 0) / review_count, 3) #calculate precise tomatometer score

    if review_count is None:
            review_count = 0

    return tomatometer_score, review_count


def log_review_data(timestamp, tomatometer_score, review_count, output_file):
    """Log the review data with timestamp to a CSV file."""
    file_exists = False
    try:
        file_exists = open(output_file, 'r')
    except FileNotFoundError:
        pass
    finally:
        if file_exists:
            file_exists.close()

    # Write data to CSV file
    with open(output_file, mode='a', newline='') as file:
        writer = csv.writer(file)
        if not file_exists:
            writer.writerow(["Timestamp", "Tomatometer Score", "Review Count"])
        writer.writerow([timestamp, tomatometer_score, review_count])

if __name__ == "__main__":
    url = f"https://www.rottentomatoes.com/m/flight_risk_2024?nocache={int(time.time())}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
    }

    output_file = "rotten_tomatoes_reviews.csv"

    while True:
        current_time = datetime.datetime.now()
        tomatometer_score, review_count = get_rotten_tomatoes_data(url, headers)

        print(f"[{current_time}] Tomatometer Score: {tomatometer_score}, Review Count: {review_count}")

        log_review_data(current_time, tomatometer_score, review_count, output_file)

        # Sleep for 60 seconds before checking again
        time.sleep(60)
