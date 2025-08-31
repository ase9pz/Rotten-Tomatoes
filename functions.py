import datetime
import requests
import pandas as pd
import math
import time
import re
import csv
from bs4 import BeautifulSoup
from kalshi_client.client import KalshiClient
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
from typing import List, Tuple, Optional
import uuid
import numpy as np
from scipy.stats import beta, betabinom
from scipy.special import comb, betaln  


#For Kalshi API
def load_private_key_from_file(private_key_path: str):
    with open(private_key_path, "rb") as key_file:
        private_key = serialization.load_pem_private_key(
            key_file.read(),
            password=None,
            backend=default_backend()
        )
    return private_key

#For Rotten Tomatoes Scraping
def get_rotten_tomatoes_data(url: str, headers: dict) -> Tuple[Optional[int], Optional[int]]:
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.content, "html.parser")

    tomatometer_element = soup.find("rt-text", {"slot": "criticsScore"})
    tomatometer_score_grab = int(tomatometer_element.text.strip("%")) if tomatometer_element else None
    
    review_element = soup.find("rt-link", {"slot": "criticsReviews"})
    review_count = int(review_element.text.strip().replace(" Reviews", "")) if review_element else None
    tomatometer_score =  round(100 * round((tomatometer_score_grab/100 * review_count), 0) / review_count, 3) #calculate precise tomatometer score

    return tomatometer_score, review_count

#For logging review data, particularly useful for backtesting
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

#For Beta Distribution
def estimate_variance_from_reviews(mu, review_count):
    if review_count <= 0:
        raise ValueError("Review count must be positive.")
    return mu * (1 - mu) / review_count / 100

def beta_parameters_from_mean_and_variance(mu, sigma_squared):
    if mu <= 0 or mu >= 1:
        raise ValueError("Mean (mu) must be between 0 and 1 (exclusive).")
    if sigma_squared <= 0:
        raise ValueError("Variance must be positive.")
    
    v = mu * (1 - mu) / sigma_squared - 1
    alpha = mu * v
    beta = (1 - mu) * v
    return alpha, beta



#Run MC Sim for Bayesian Updating of Beta Distribution
def bayesian_monte_carlo(pos_reviews, total_reviews, steps=5, num_simulations=10000):
    """
    Simulates review evolution using Beta distribution posterior.
    Starts from (pos_reviews / total_reviews) and runs MC for `steps` steps.

    Returns:
        final_scores: Array of size num_simulations containing simulated final scores
    """
    alpha_0 = pos_reviews + 1  # +1 for Laplace smoothing (optional)
    beta_0 = (total_reviews - pos_reviews) + 1

    # Final state after n new reviews simulated
    final_scores = []

    for _ in range(num_simulations):
        alpha = alpha_0
        beta_param = beta_0

        for _ in range(steps):
            # Simulate a new review from the true underlying Beta distribution
            sampled_mu = np.random.beta(alpha, beta_param)
            new_review = np.random.binomial(1, sampled_mu)

            # Update posterior
            if new_review == 1:
                alpha += 1
            else:
                beta_param += 1

        final_score = alpha / (alpha + beta_param)
        final_scores.append(final_score)

    return np.array(final_scores)

#Similar to above, but without Bayesian Updating
def constant_monte_carlo(alpha, beta_param, n_new_reviews=10, num_samples=100000):
    # Sample true mu from current Beta posterior
    sampled_mus = np.random.beta(alpha, beta_param, size=num_samples)
    
    # For each mu, simulate new review outcomes
    new_pos = np.random.binomial(n_new_reviews, sampled_mus)
    
    # Update alpha and beta
    new_alpha = alpha + new_pos
    new_beta = beta_param + n_new_reviews - new_pos
    
    # Posterior means after new reviews
    final_scores = new_alpha / (new_alpha + new_beta)
    return final_scores

#Creates beta binomial distribution to calculate weights for mixture distribution
#choosing k positive reviews out of n new reviews
def beta_binomial_pmf(k, n, alpha, beta_param):
    # Using betaln for numerical stability
    log_p = np.log(comb(n, k)) + betaln(alpha + k, beta_param + n - k) - betaln(alpha, beta_param)
    return np.exp(log_p)

def final_score_pdf(x, alpha, beta_param, n_new):
    # x can be array of points to evaluate the PDF at
    pdf_vals = np.zeros_like(x, dtype=float)
    for k in range(n_new + 1):
        weight = beta_binomial_pmf(k, n_new, alpha, beta_param)
        pdf_component = beta.pdf(x, alpha + k, beta_param + n_new - k)
        pdf_vals += weight * pdf_component
    return pdf_vals

#Uses weights from beta_binomial_pmf to calculate mean of mixture distribution
def mixture_mean(alpha, beta_param, n_new):
    mean = 0.0
    denom = alpha + beta_param + n_new
    for k in range(n_new + 1):
        weight = beta_binomial_pmf(k, n_new, alpha, beta_param)
        mean += weight * (alpha + k) / denom
    return mean

#Uses weights from beta_binomial_pmf to calculate cdf of mixture distribution
def mixture_cdf(x, alpha, beta_param, n_new):
    cdf_val = 0.0
    for k in range(n_new + 1):
        weight = beta_binomial_pmf(k, n_new, alpha, beta_param)
        cdf_val += weight * beta.cdf(x, alpha + k, beta_param + n_new - k)
    return cdf_val

#Takes lower and upper bounds (a, b) and calculates probability of 
#score being in that range
def mixture_prob_range(a, b, alpha, beta_param, n_new):
    return mixture_cdf(b, alpha, beta_param, n_new) - mixture_cdf(a, alpha, beta_param, n_new)

#Simulates future trend of score based on recent biased data
def biased_trend_monte_carlo(
    historical_pos, historical_total,
    recent_pos, recent_total,
    future_reviews=50,
    num_simulations=10000
):
    # Use recent data to model future trend
    alpha = recent_pos + 1
    beta_param = recent_total - recent_pos + 1
    
    # Sample future mean positive rates
    sampled_mus = np.random.beta(alpha, beta_param, size=num_simulations)
    
    # Simulate new positive review counts
    new_pos = np.random.binomial(n=future_reviews, p=sampled_mus)
    
    # Combine with historical fixed data
    final_scores = (historical_pos + new_pos) / (historical_total + future_reviews)
    
    return final_scores

#More technical version of biased_trend_monte_carlo with weight parameter
def trend_weighted_monte_carlo(
    historical_pos, historical_total,
    recent_pos, recent_total,
    future_reviews=50,
    num_simulations=10000,
    recent_weight=2.0
):
    """
    recent_weight > 1 emphasizes recent reviews more than historical data
    recent_weight < 1 de-emphasizes recent reviews
    
    When setting params, historical_pos+recent_pos should = current positives
    if you want to use actually occured data. In theory, you could forecast
    and adjust the params to test different scenarios.
    """

    # Weighted posterior parameters
    alpha = historical_pos + recent_weight * recent_pos + 1
    beta_param = (historical_total - historical_pos) + recent_weight * (recent_total - recent_pos) + 1

    # Sample future underlying probabilities
    sampled_mus = np.random.beta(alpha, beta_param, size=num_simulations)

    # Simulate new positives for future_reviews
    new_pos = np.random.binomial(n=future_reviews, p=sampled_mus)

    # Compute final scores including all historical + future reviews
    final_scores = (historical_pos + recent_pos + new_pos) / (historical_total + recent_total + future_reviews)

    return final_scores

#Numerical equivalent of trend_weighted_monte_carlo
def trend_weighted_mixture(historical_pos, historical_total, recent_pos, recent_total, future_reviews=50, recent_weight=2.0):
    # Effective prior
    alpha_eff = historical_pos + recent_weight * recent_pos + 1
    beta_eff = (historical_total - historical_pos) + recent_weight * (recent_total - recent_pos) + 1
    
    # Beta-Binomial PMF over future reviews
    k_values = np.arange(future_reviews + 1)
    pmf = betabinom.pmf(k_values, future_reviews, alpha_eff, beta_eff)
    
    # Final scores for each possible k
    final_scores_discrete = (historical_pos + recent_pos + k_values) / (historical_total + recent_total + future_reviews)
    
    # Smoothed grid for visualization
    final_score_grid = np.linspace(final_scores_discrete.min(), final_scores_discrete.max(), 1000)
    
    # Compute smoothed PDF using Beta PDFs centered at each discrete point
    pdf_vals = np.zeros_like(final_score_grid)
    for k, weight in zip(k_values, pmf):
        # Beta component: small "variance" smoothing
        a = alpha_eff + k
        b = beta_eff + future_reviews - k
        pdf_vals += weight * beta.pdf(final_score_grid, a, b)
    
    # Normalize PDF
    pdf_vals /= np.trapz(pdf_vals, final_score_grid)
    
    # Approximate CDF
    cdf_vals = np.cumsum(pdf_vals)
    cdf_vals /= cdf_vals[-1]
    
    # Mean final score
    mean_score = np.sum(final_scores_discrete * pmf)
    
    return final_score_grid, pdf_vals, cdf_vals, mean_score
