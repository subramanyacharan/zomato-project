# Problem Statement: AI-Powered Restaurant Recommendation System (Zomato Use Case)

Build an AI-powered restaurant recommendation application inspired by Zomato. The system should combine structured restaurant data with a Large Language Model (LLM) to generate personalized, relevant, and easy-to-understand recommendations based on user preferences.

## Objective

Design and implement an application that:

- Accepts user preferences such as location, budget, cuisine, and minimum rating.
- Uses a real-world restaurant dataset.
- Leverages an LLM to produce personalized, human-like recommendations.
- Presents clear and useful results in a user-friendly format.

## System Workflow

### 1) Data Ingestion

- Load and preprocess the Zomato dataset from Hugging Face: [Zomato Restaurant Recommendation Dataset](https://huggingface.co/datasets/ManikaSaini/zomato-restaurant-recommendation).
- Extract relevant fields such as restaurant name, location, cuisine, average cost, and rating.

### 2) User Input Collection

Collect user preferences, including:

- Location (for example: Delhi, Bangalore)
- Budget (low, medium, high)
- Preferred cuisine (for example: Italian, Chinese)
- Minimum rating threshold
- Optional preferences (for example: family-friendly, quick service)

### 3) Integration Layer

- Filter and prepare candidate restaurant records based on user input.
- Pass the filtered structured data into an LLM prompt.
- Design the prompt to help the LLM reason over options and rank them effectively.

### 4) Recommendation Engine

Use the LLM to:

- Rank the most suitable restaurants.
- Explain why each recommendation matches the user's preferences.
- Optionally provide a short summary of the top choices.

### 5) Output Presentation

Display top recommendations in a clear, user-friendly format with:

- Restaurant name
- Cuisine
- Rating
- Estimated cost
- AI-generated explanation
