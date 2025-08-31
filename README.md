# Rotten Tomatoes Prediction Market Simulator

![Project Banner](banner.svg)

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Active-brightgreen.svg)](https://github.com/yourusername/Rotten-Tomatoes)

## Overview

This project is a probabilistic framework for analyzing and trading on Rotten Tomatoes (RT) scores in **Kalshi prediction markets**. On Kalshi, you can bet on a film's RT score at a set expiration date. The goal of this project is to model the evolution of a film's RT score and provide tools to inform trading decisions.

RT scores are based on **binomial outcomes**: each review is classified as "good" or "bad" by RT's NLP, and the displayed RT score is simply the proportion of total positive reviews. We model the underlying "true" distribution of a movie's quality as a **Beta distribution**, with parameters α and β determined by current positive reviews and total reviews.

Critic reviews are recorded from RT's author pages ([Critics' Blogs](https://www.rottentomatoes.com/critics/authors)) and typically appear on the RT site within 1–2 days of publication. Reviews are used from a movie's **embargo date** until the Kalshi contract expiration, allowing us to trade on predicted movement in RT scores over time.

---

## Table of Contents

- [Overview](#overview)  
- [Features](#features)  
- [Installation](#installation)  
- [Usage](#usage)  
- [Heuristics & Trading Notes](#heuristics--trading-notes)  
- [Technologies](#technologies)  
- [Example Workflow](#example-workflow)  
- [Diagram](#diagram)  
- [License](#license)  

---

## Features

- Monte Carlo simulations of future Rotten Tomatoes scores with and without Bayesian updating.  
- Exact **Beta-Binomial mixture distributions** for analytically calculating CDFs and expected scores.  
- Functions to compute **probabilities of thresholds, buckets, and ranges** for final scores.  
- Utilities for **scraping RT review data** from critics' personal pages.  
- Integration with **Kalshi API** for potential automated trading simulations.  
- Flexible framework for **hedging strategies** and "bucketed" probabilistic predictions.

---

## Installation

Clone the repository and install dependencies:

```bash
git clone <your-repo-url>
cd RottenTomatoesPredictionMarket
pip install -r requirements.txt
```

Required Python libraries:

```python
import functions
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.stats import beta, betabinom
from scipy.special import betaln, comb
```

Optional:

* `bs4` for scraping
* `kalshi_client` for automated trading

---

## Usage

All key functions are defined in `functions.py`. Example usages include:

* Forecasting the probability that a movie exceeds a given RT score at contract expiry.
* Simulating review arrival using Monte Carlo methods (with or without Bayesian updating).
* Calculating exact Beta-Binomial mixture PDFs and CDFs.
* Visualizing final score distributions and cumulative probabilities.

Check `Example_Workflow.ipynb` for a demonstration of how the models can inform trading decisions.

---

## Heuristics & Trading Notes

* Embargo dates are informative: movies expected to be well-received often have **earlier embargo dates** to allow more positive reviews for marketing. Poor movies may delay embargo.
* Reviews often arrive in **chunks**, and weekend arrivals are slower.
* Individual reviews have **diminishing marginal impact** on overall probability as the number of reviews grows.
* RT may temporarily omit or add reviews, causing minor inconsistencies in score and review count.

* Hedge predictions by **buckets** rather than simple over/under thresholds.

---

## Example Workflow

1. Import functions and historical RT review data.
2. Estimate α and β parameters based on observed positives and totals.
3. Choose a prediction method:

   * Constant Monte Carlo (`monte_carlo_final_score`)
   * Bayesian updating Monte Carlo (`run_beta_monte_carlo`)
   * Analytical Beta-Binomial mixture (`final_score_pdf`, `mixture_cdf`, `mixture_mean`)
4. Visualize probability distributions and CDFs.
5. Evaluate probabilities at thresholds to inform trading decisions.

---

## Diagram

Below is a conceptual illustration of the **Beta-Binomial mixture → continuous final score PDF → CDF**:

```
Discrete k values (number of positive reviews)
   │
   │  Each k has a Beta distribution representing posterior uncertainty
   ▼
Continuous mixture of Beta distributions
   │
   ▼
PDF of final scores
   │
   ▼
Integration → CDF
```

> You can replace this ASCII diagram with a proper figure if desired.

---

## Technologies

* Python 3.11+
* NumPy & SciPy for numerical calculations and probability distributions
* Pandas for data management
* Matplotlib for visualization
* BeautifulSoup (`bs4`) for scraping critic reviews
* Kalshi API (`kalshi_client`) for automated interactions

---

## License

MIT License 