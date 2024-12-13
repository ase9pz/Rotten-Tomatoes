import numpy as np
import matplotlib.pyplot as plt

# Step 1: Generate synthetic data for illustration
#Movie review scores
np.random.seed(42)
n_movies = 5
n_reviews_per_movie = 20

# True population parameters (you would estimate these in practice)
mu_population_true = 75
sigma_population_true = 10
tau_true = 15

# Generate movie-specific data (in reality, you'd use actual data)
theta_true = np.random.normal(mu_population_true, sigma_population_true, size=n_movies)
sigma_true = np.random.exponential(1/tau_true, size=n_movies)
scores = [np.random.normal(theta_true[i], sigma_true[i], size=n_reviews_per_movie) for i in range(n_movies)]

# Step 2: Define the Metropolis-Hastings sampler
def metropolis_hastings(n_iter, initial_values, target_log_pdf, proposal_std):
    # Initialize variables
    samples = np.zeros((n_iter, len(initial_values)))
    samples[0] = initial_values
    
    for t in range(1, n_iter):
        # Propose new values based on previous
        proposal = samples[t-1] + np.random.normal(0, proposal_std, len(initial_values))
        
        # Calculate acceptance ratio (Metropolis-Hastings)
        acceptance_ratio = np.exp(target_log_pdf(proposal) - target_log_pdf(samples[t-1]))
        
        # Accept the proposal with the calculated probability
        if np.random.rand() < acceptance_ratio:
            samples[t] = proposal
        else:
            samples[t] = samples[t-1]
    
    return samples

# Step 3: Define the target log-posterior distribution
def log_posterior(params, data, n_movies, n_reviews_per_movie):
    mu_population, sigma_population, tau = params
    
    # Prior for mu_population and sigma_population (normal priors)
    log_prior_mu = -0.5 * (mu_population**2 / sigma_population**2)
    log_prior_sigma = -0.5 * (sigma_population**2 / 10**2)  # Assuming a prior variance of 100
    
    # Prior for tau (exponential prior)
    log_prior_tau = -tau / 15.0  # Assuming a prior rate of 15
    
    # Likelihood (movie scores likelihood)
    log_likelihood = 0
    for i in range(n_movies):
        for j in range(n_reviews_per_movie):
            score = data[i][j]
            log_likelihood += -0.5 * np.log(2 * np.pi * sigma_population) - 0.5 * ((score - mu_population)**2 / sigma_population)
    
    # Combine log-priors and log-likelihood
    log_posterior_value = log_prior_mu + log_prior_sigma + log_prior_tau + log_likelihood
    return log_posterior_value

# Step 4: Initialize parameters and run Metropolis-Hastings sampling
initial_values = [75, 10, 15]  # Initial guesses for mu_population, sigma_population, tau
n_iter = 5000  # Number of Metropolis iterations
proposal_std = 0.5  # Standard deviation of proposal distribution

# Run Metropolis-Hastings sampling
samples = metropolis_hastings(n_iter, initial_values, lambda params: log_posterior(params, scores, n_movies, n_reviews_per_movie), proposal_std)

# Step 5: Plot the results
plt.figure(figsize=(10, 6))

# Plot histograms of the sampled values for each parameter
plt.subplot(1, 3, 1)
plt.hist(samples[:, 0], bins=50, alpha=0.75, label="mu_population")
plt.title("Posterior of mu_population")
plt.legend()

plt.subplot(1, 3, 2)
plt.hist(samples[:, 1], bins=50, alpha=0.75, label="sigma_population")
plt.title("Posterior of sigma_population")
plt.legend()

plt.subplot(1, 3, 3)
plt.hist(samples[:, 2], bins=50, alpha=0.75, label="tau")
plt.title("Posterior of tau")
plt.legend()

plt.tight_layout()
plt.show()
