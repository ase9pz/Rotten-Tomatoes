# Rotten Tomatoes Prediction Market Simulator

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Active-brightgreen.svg)](https://github.com/yourusername/Rotten-Tomatoes)

## Overview

This project is a probabilistic framework for analyzing and trading on Rotten Tomatoes (RT) scores in Kalshi prediction markets. On Kalshi, you can bet on a film's RT score at a set expiration date. The goal of this project is to model the evolution of a film's RT score and provide tools to inform trading decisions.

RT scores are based on binomial outcomes: each review is classified as "good" or "bad" by RT's NLP, and the displayed RT score is simply the proportion of total positive reviews. We model the underlying "true" distribution of a movie's quality as a Beta distribution, with parameters α and β determined by current positive reviews and total reviews.

Critic reviews are recorded from RT's author pages ([Critics' Blogs](https://www.rottentomatoes.com/critics/authors)) and typically appear on the RT site within 1–2 days of publication. Reviews are used from a movie's embargo date until the Kalshi contract expiration, allowing us to trade on predicted movement in RT scores over time.

`Example_Workflow.ipynb` goes in-depth on how to use these models to drive your trading decisions based on various assumptions. A more detailed discussion of the statistics is there as well.

## Table of Contents

- [Overview](#overview)  
- [Features](#features)  
- [Installation](#installation)  
- [Usage](#usage)  
- [Heuristics & Trading Notes](#heuristics--trading-notes)  
- [License](#license)  

## Installation

Clone the repository and install dependencies:

```bash
git clone <https://github.com/ase9pz/Rotten-Tomatoes>
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

## Usage
All key functions are defined in `functions.py`. Example usages include:

* Forecasting the probability that a movie exceeds a given RT score at contract expiry.
* Simulating review arrival using Monte Carlo methods (with or without Bayesian updating).
* Calculating exact Beta-Binomial mixture PDFs and CDFs.
* Visualizing final score distributions and cumulative probabilities.

Check `Example_Workflow.ipynb` for a detailed demonstration of how the models can inform trading decisions.


## Heuristics & Trading Notes

* Embargo dates are informative: movies expected to be well-received often have earlier embargo dates to allow more positive reviews for marketing. Poor movies may delay embargo.
* Reviews often arrive in chunks, and weekend arrivals are slower.
* Individual reviews have diminishing marginal impact on score as the number of reviews grows.
* RT may temporarily omit or add reviews, causing minor inconsistencies in score and review count.

* You can combine bets to bet on a range, not just over/under a single threshold


## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contact

Nemmo Ciccone - ase9pz@virginia.edu

Project Link: 
https://github.com/ase9pz/Rotten-Tomatoes