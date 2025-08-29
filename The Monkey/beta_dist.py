import numpy as np
import matplotlib.pyplot as plt
import scipy.stats as stats
from datetime import datetime
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

# -------------------------------------------
        # Functions
# -------------------------------------------

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

def plot_tomatometer_distributions(tomatometer_score: float, review_count: int, final_review_count: int, check_ranges=None):
    """
    Vectorized version using Beta-Binomial distribution for efficient simulation.
    """
    # Convert score to fraction and calculate initial Beta parameters
    tomatometer_fraction = tomatometer_score / 100.0
    alpha0 = (tomatometer_fraction * review_count) + 1
    beta0 = ((1 - tomatometer_fraction) * review_count) + 1

    # Plot current Beta distribution (same as before)
    x = np.linspace(0, 1, 1000)
    current_pdf = stats.beta.pdf(x, alpha0, beta0)
    plt.figure(figsize=(8, 5))
    plt.plot(x * 100, current_pdf, label=f"Current Beta({alpha0:.1f}, {beta0:.1f})", color='b')
    plt.axvline(tomatometer_score, color='r', linestyle="--", label=f"Observed {tomatometer_score}%")
    plt.xlabel("Tomatometer Score (%)")
    plt.ylabel("Probability Density")
    plt.title("Current True Tomatometer Probability Distribution")
    plt.legend()
    plt.grid(True)
    plt.show()

    # Vectorized simulation using Beta-Binomial distribution
    num_simulations = 50000
    additional_reviews = final_review_count - review_count
    
    if additional_reviews <= 0:
        final_scores = np.full(num_simulations, tomatometer_score)
    else:
        # Generate simulated positive reviews in one vectorized operation
        simulated_positives = stats.betabinom.rvs(
            n=additional_reviews,
            a=alpha0,
            b=beta0,
            size=num_simulations
        )
        
        # Calculate final scores using vectorized operations
        total_positives = (alpha0 - 1) + simulated_positives  # alpha0-1 = current positive reviews
        final_scores = (total_positives / final_review_count) * 100


    # -------------------------------------------
    # 2. Stepwise simulation of additional reviews.
    # -------------------------------------------
    num_simulations = 50000
    final_scores = np.zeros(num_simulations)
    
    # Number of additional reviews to simulate
    additional_reviews = final_review_count - review_count

    # If no additional reviews are coming in, then the final score is exactly the observed score.
    if additional_reviews <= 0:
        final_scores.fill(tomatometer_score)
    else:
        # For each simulation, update the Beta parameters review by review.
        for i in range(num_simulations):
            # Start with the current parameters
            alpha_sim = alpha0
            beta_sim = beta0
            # Stepwise update: simulate one review at a time.
            for _ in range(additional_reviews):
                # The predictive probability of a positive review is the mean of the current Beta.
                p_positive = alpha_sim / (alpha_sim + beta_sim)
                # Sample one new review outcome from a Bernoulli trial.
                if np.random.rand() < p_positive:
                    alpha_sim += 1  # positive review observed
                else:
                    beta_sim += 1   # negative review observed
            # The final number of positive reviews (excluding the prior) is (alpha_sim - 1),
            # and total reviews is final_review_count.
            final_score_fraction = (alpha_sim - 1) / (final_review_count)
            final_scores[i] = final_score_fraction * 100  # convert to percentage

    # -------------------------------------------
    # 3. Plot the predicted final distribution.
    # -------------------------------------------
    plt.figure(figsize=(8, 5))
    plt.hist(final_scores, bins=50, density=True, alpha=0.7, color='g', 
             label=f"Predicted at {final_review_count} Reviews")
    plt.axvline(tomatometer_score, color='r', linestyle="--", label=f"Current {tomatometer_score}%")
    plt.xlabel("Tomatometer Score (%)")
    plt.ylabel("Probability Density")
    plt.title(f"Predicted Tomatometer Distribution at {final_review_count} Reviews")
    plt.legend()
    plt.grid(True)
    plt.show()

    # -------------------------------------------
    # 4. Compute probability mass within user-defined ranges.
    # -------------------------------------------
    if check_ranges:
        print("Probability mass within defined tomatometer score ranges (final distribution):")
        zero_ranges = []
        for (lower, upper) in check_ranges:
            # Calculate fraction of simulations with final score in the range [lower, upper)
            prob_mass = float(np.mean((final_scores >= lower) & (final_scores < upper)))
            zero_ranges.append(prob_mass)
            print(f"Between {lower}-{upper}%: {prob_mass * 100:.2f}%")
        return zero_ranges
    
zero_ranges = plot_tomatometer_distributions(tomatometer_score = 85, 
                                            review_count = 93, 
                                            final_review_count= 150, 
                                            check_ranges=[(0,80.5), (80.5, 100)])

print(zero_ranges)