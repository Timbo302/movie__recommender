# 🎬 Blake’s Movie Recommender

An AI-powered movie recommendation web app that lets users type natural language prompts (like _"romantic movie under 90 minutes"_) and receive relevant film suggestions powered by Claude (via AWS Bedrock) and TMDb.

## 🧠 How It Works

1. Users enter a free-text movie description.
2. Claude parses the prompt into structured filters (genre, runtime, rating, etc.).
3. The app queries The Movie Database (TMDb) API using those filters.
4. It returns and displays matching movie titles, posters, ratings, and overviews.

## 🛠️ Features

- Natural language input via Claude (LLM)
- Genre/decade/critic/length filters (manual or automatic)
- Fallback logic for empty searches
- Blue gradient interface via Streamlit
- Results sorted by popularity
- Runtime and rating displayed
- .env file for API security

## 🚀 How to Run

1. Clone this repo:
   ```bash
   git clone https://github.com/your-username/movie-recommender.git
   cd movie-recommender

2. 
pip install -r requirements.txt    -   for installing packages necessary to run code

3.Create .env file for these
AWS_ACCESS_KEY_ID=your_key_here
AWS_SECRET_ACCESS_KEY=your_secret_here
AWS_REGION=us-west-2
TMDB_API_KEY=your_tmdb_api_key_here



4. Run app in terminal with this statement
streamlit run movie-recommender.py
