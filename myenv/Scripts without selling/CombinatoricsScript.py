import requests
from bs4 import BeautifulSoup


#Get Rotten Tomatoes Score

url = "https://www.rottentomatoes.com/m/mufasa"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
}
response = requests.get(url, headers=headers)

soup = BeautifulSoup(response.content, "html.parser")

tomatometer_element = soup.find("rt-text", {"slot": "criticsScore"})

if tomatometer_element:
    tomatometer_score = tomatometer_element.text.strip()
    print(f"Tomatometer Score: {tomatometer_score}")
else:
    print("Tomatometer Score not found.")


#Get Review Count

url = "https://www.rottentomatoes.com/m/mufasa"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
}
response = requests.get(url, headers=headers)

soup = BeautifulSoup(response.content, "html.parser")

review_element = soup.find("rt-link", {"slot": "criticsReviews"})

if review_element:
    review_count = review_element.text.strip()
    print(review_count)
else:
    print("Review Count not found.")


import math

initial_reviews = int(review_count.strip("Reviews"))   
bucket_threshold = 0.56  
initial_rating = int(tomatometer_score.strip("%"))/100

def bucket_chance(final_reviews):
    additional_reviews = final_reviews - initial_reviews     
    num_pos_reviews = round(initial_rating * initial_reviews)  #

    def binomial_probability(n, k, p):
        return math.comb(n, k) * (p ** k) * ((1 - p) ** (n - k))

    possible_outcomes = []

    for future_pos_reviews in range(0, additional_reviews + 1):
        final_pos_reviews = num_pos_reviews + future_pos_reviews
        final_rating = final_pos_reviews / final_reviews

        probability = binomial_probability(
            additional_reviews, future_pos_reviews, initial_rating
        )

        possible_outcomes.append((final_rating, probability))

    total_probability = sum(prob for rating, prob in possible_outcomes if rating >= bucket_threshold)

    return total_probability


review_range = range(100, 200)  
total_prob_sum = 0  # Initialize sum of probabilities
count = 0  

for final_reviews in review_range:
    prob = bucket_chance(final_reviews)
    total_prob_sum += prob  
    count += 1  

#Calculate the average probability over the range
average_probability = total_prob_sum / count

