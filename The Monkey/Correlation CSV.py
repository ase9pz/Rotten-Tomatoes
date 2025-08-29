import pandas as pd
from datetime import datetime

# Load the data
df = pd.read_csv("/Users/nemmociccone/Downloads/the_monkey_rotten_tomatoes_reviews.csv", skiprows=[0], header=None)
df.columns = ['Timestamp', 'Score', 'Review_Count']  # Adjust column names as needed

# Ensure Score is a string before stripping percentage sign
df['Score'] = round(df['Score'].astype(str).str.rstrip('%').astype(float) / 100, 4)

# Handle missing values
df['Score'].fillna(0, inplace=True)
df['Review_Count'].fillna(0, inplace=True)

# Track the highest review count seen so far
highest_review_count = 0
filtered_rows = []

# Iterate through the DataFrame to detect new highest review counts
for _, row in df.iterrows():
    review_count = row['Review_Count']
    score = row['Score']
    
    if review_count > highest_review_count:
        highest_review_count = review_count
        positive_reviews = round(score * highest_review_count)
        row['Positive_Reviews'] = positive_reviews
        filtered_rows.append(row)

# Create a new DataFrame with only the rows where the review count increased
filtered_df = pd.DataFrame(filtered_rows)

# Compute days until release (02/20/25)
release_date = datetime(2025, 2, 20)
filtered_df['Timestamp'] = pd.to_datetime(filtered_df['Timestamp'], errors='coerce')  # Ensure timestamp is a datetime object
filtered_df['Days_Until_Release'] = (release_date - filtered_df['Timestamp']).dt.days

filtered_df = filtered_df.drop(columns=['Timestamp'])

# Save the updated DataFrame
filtered_df.to_csv("updated_reviews.csv", index=False)

print("Processing complete. Updated data saved to 'updated_reviews.csv'.")
