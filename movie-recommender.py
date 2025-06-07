import streamlit as st
import requests
import boto3
import json
import os
from dotenv import load_dotenv

# Load .env secrets
load_dotenv()
API_KEY = os.getenv("TMDB_API_KEY")

bedrock = boto3.client(
    "bedrock-runtime",
    region_name=os.getenv("AWS_REGION"),
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY")
)

# Inject CSS for background gradient
st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(135deg, #cceeff, #3399ff);
        color: #000;
        padding: 2rem;
    }
    </style>
""", unsafe_allow_html=True)

BASE_URL = "https://api.themoviedb.org/3"

def gpt_parse_prompt(prompt):
    body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 300,
        "messages": [{
            "role": "user",
            "content": f"""
You are a helpful movie assistant. A user typed this prompt:

\"{prompt}\"

Extract the following structured JSON:
- genres: list of strings
- year_start: int or null
- year_end: int or null
- min_score: float or null
- min_runtime: int or null
- max_runtime: int or null
- certification: string or null

Return ONLY valid JSON:
"""
        }]
    }

    response = bedrock.invoke_model(
        modelId="anthropic.claude-3-5-sonnet-20240620-v1:0",
        contentType="application/json",
        accept="application/json",
        body=json.dumps(body)
    )
    result = json.loads(response["body"].read())
    try:
        text = result["content"][0]["text"]
        json_text = text.strip().split("```json")[-1].split("```")[0] if "```json" in text else text
        return json.loads(json_text)
    except:
        st.error("❌ Claude response couldn't be parsed. Try rewording your query.")
        return {}

@st.cache_data
def get_genre_ids():
    url = f"{BASE_URL}/genre/movie/list"
    response = requests.get(url, params={"api_key": API_KEY, "language": "en-US"})
    return {g["name"]: g["id"] for g in response.json().get("genres", [])}

def discover_movies(genres=[], year_start=None, year_end=None, min_score=None,
                    certification=None, min_runtime=None, max_runtime=None, include_adult=False):
    genre_id_map = get_genre_ids()
    genre_ids = [str(genre_id_map[g]) for g in genres if g in genre_id_map]

    base_params = {
        "api_key": API_KEY,
        "language": "en-US",
        "sort_by": "popularity.desc",
        "include_adult": include_adult,
        "with_genres": ",".join(genre_ids) if genre_ids else None,
        "vote_average.gte": min_score,
        "certification_country": "US",
        "certification.lte": certification,
        "with_runtime.gte": min_runtime,
        "with_runtime.lte": max_runtime,
    }

    results = []
    for page in range(1, 6):
        base_params["page"] = page
        response = requests.get(f"{BASE_URL}/discover/movie", params={k: v for k, v in base_params.items() if v is not None})
        results += response.json().get("results", [])

    if year_start and year_end:
        results = [m for m in results if m.get("release_date", "") and year_start <= int(m["release_date"][:4]) <= year_end]

    if genres:
        reverse_genre_map = {v: k for k, v in get_genre_ids().items()}
        results = [
            m for m in results
            if any(g in [reverse_genre_map.get(id) for id in m.get("genre_ids", [])] for g in genres)
        ]

    results.sort(key=lambda m: m.get("popularity", 0), reverse=True)
    return results

def display_movies(movies, genres=[]):
    cols = st.columns(3)
    for i, m in enumerate(movies):
        with cols[i % 3]:
            st.image(f"https://image.tmdb.org/t/p/w500{m['poster_path']}", width=200)
            runtime = f"{m.get('runtime', '??')} min" if m.get("runtime") else ""
            title = f"{m['title']} ({m.get('release_date', 'N/A')[:4]})"
            st.markdown(f"**{title}**  \n⏱️ {runtime}")
            st.caption(f"⭐ {m.get('vote_average', 'N/A')}")
            with st.expander("Overview"):
                st.write(m.get("overview", "No overview available."))

# === UI ===
st.title("Blake’s Movie Recommender")

query = st.text_input("What movie are you looking for? (e.g., 'action movie for kids')")
st.markdown("Or fine-tune your search manually:")

genre_list = list(get_genre_ids().keys())
genres = st.multiselect("🎭 Genre", genre_list)

decade = st.selectbox("🕰️ Decade", ["Any", "1970s", "1980s", "1990s", "2000s", "2010s", "2020s"])
decade_range = {
    "1970s": (1970, 1979),
    "1980s": (1980, 1989),
    "1990s": (1990, 1999),
    "2000s": (2000, 2009),
    "2010s": (2010, 2019),
    "2020s": (2020, 2025),
    "Any": (None, None)
}
y_start, y_end = decade_range.get(decade, (None, None))

critics_only = st.checkbox("🌟 Critically Acclaimed Only (Score ≥ 7.0)", value=False)
min_score = 7.0 if critics_only else None

include_adult = st.checkbox("🔞 Include adult content", value=False)

min_runtime = None
max_runtime = None

if query:
    with st.spinner("🧠 Claude is analyzing your prompt..."):
        parsed = gpt_parse_prompt(query)

    if not genres and parsed.get("genres"):
        genres = parsed["genres"]
    if decade == "Any" and parsed.get("year_start") and parsed.get("year_end"):
        y_start = parsed["year_start"]
        y_end = parsed["year_end"]
    if not min_score and parsed.get("min_score"):
        min_score = parsed["min_score"]
    min_runtime = parsed.get("min_runtime")
    max_runtime = parsed.get("max_runtime")

if st.button("🎥 Recommend Movies"):
    with st.spinner("🔍 Searching TMDb..."):
        movies = discover_movies(
            genres, y_start, y_end, min_score,
            parsed.get("certification"),
            min_runtime, max_runtime,
            include_adult
        )

        # Fallback 1 — no critic score
        if not movies:
            st.info("No results with all filters. Trying without critic score...")
            movies = discover_movies(
                genres, y_start, y_end, None,
                parsed.get("certification"),
                min_runtime, max_runtime,
                include_adult
            )

        # Fallback 2 — no runtime
        if not movies:
            st.info("Still nothing. Trying without runtime filter...")
            movies = discover_movies(
                genres, y_start, y_end, None,
                parsed.get("certification"),
                None, None,
                include_adult
            )

        # Fallback 3 — no certification
        if not movies and parsed.get("certification"):
            st.info("Still no results. Trying without certification filter...")
            movies = discover_movies(
                genres, y_start, y_end, None,
                None, None, None,
                include_adult
            )

        # Fallback 4 — only first genre
        if not movies and genres:
            st.info("Trying again with only one genre...")
            movies = discover_movies(
                [genres[0]], y_start, y_end, None,
                None, None, None,
                include_adult
            )

    if movies:
        display_movies(movies, genres)
    else:
        st.warning("No results found at all. Try a more general query.")
