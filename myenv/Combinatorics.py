import matplotlib.pyplot as plt
import math
import kalshi_python

initial_rating = 0.94 # Initial Rotten Tomatoes score as a decimal
initial_reviews = 77         # Number of reviews at the start
bucket_threshold = 0.955  # Define the threshold (e.g., 50% positive reviews)

def bucket_chance(final_reviews):

    additional_reviews = final_reviews - initial_reviews       # Future reviews to be added
    num_pos_reviews = round(initial_rating * initial_reviews)  # Initial positive reviews

    def binomial_probability(n, k, p):
        return math.comb(n, k) * (p ** k) * ((1 - p) ** (n - k))

    possible_outcomes = []

    for future_pos_reviews in range(0, additional_reviews + 1):
        # Calculate the final number of positive reviews and final rating for this outcome
        final_pos_reviews = num_pos_reviews + future_pos_reviews
        final_rating = final_pos_reviews / final_reviews

        # Calculate the probability of this outcome
        probability = binomial_probability(
            additional_reviews, future_pos_reviews, initial_rating
        )

        possible_outcomes.append((final_rating, probability))

    total_probability = sum(prob for rating, prob in possible_outcomes if rating >= bucket_threshold)

    return total_probability


review_range = range(125, 200)  
total_prob_sum = 0  # Initialize sum of probabilities
count = 0  # Counter for number of final_reviews values tested

for final_reviews in review_range:
    prob = bucket_chance(final_reviews)
    total_prob_sum += prob  # Accumulate the total probability
    count += 1  # Increment count

average_probability = total_prob_sum / count
print(f'The average probability above {bucket_threshold * 100}% for final reviews {review_range.start}-{review_range.stop - 1}: {average_probability:.4f}')


x_values = [] 
y_values = []  

# Loop over the range and calculate probabilities
for final_reviews in review_range:
    prob = bucket_chance(final_reviews)  # Use the function defined earlier
    x_values.append(final_reviews)
    y_values.append(prob)



# Create the plot
plt.figure(figsize=(10, 6))
plt.plot(x_values, y_values, marker='o', linestyle='-', color='blue', label='Probability')

y_min = min(y_values)
y_max = max(y_values)
padding = 0.1 * (y_max - y_min)  # 10% of the range as padding

# Add labels, title, and legend
plt.title(f'Probability of Exceeding {bucket_threshold * 100}% Threshold'
          f' rating: {initial_rating}', fontsize=14
          )
plt.xlabel('Number of Reviews', fontsize=12)
plt.ylabel('Probability', fontsize=12)
plt.ylim(y_min-padding, y_max+padding)
#plt.axhline(y=0.91, color='red', linestyle='--', label='Market Line')  # Reference line
plt.grid(True)
plt.legend(fontsize=12)
plt.show()



