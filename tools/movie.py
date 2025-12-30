import os
import requests
from typing import List, Optional, Dict, Any
from langchain_core.tools import tool
from pydantic import BaseModel, Field

GENRE_MAP = {
    "action": 28,
    "adventure": 12,
    "animation": 16,
    "comedy": 35,
    "crime": 80,
    "documentary": 99,
    "drama": 18,
    "family": 10751,
    "fantasy": 14,
    "history": 36,
    "horror": 27,
    "music": 10402,
    "mystery": 9648,
    "romance": 10749,
    "science fiction": 878,
    "scifi": 878,
    "tv movie": 10770,
    "thriller": 53,
    "war": 10752,
    "western": 37
}

class DiscoverMovieInput(BaseModel):
    primary_release_date_gte: Optional[str] = Field(
        None, 
        description="Filter and only include movies that have a primary release date that is greater or equal to the specified value, format YYYY-MM-DD"
    )
    primary_release_date_lte: Optional[str] = Field(
        None, 
        description="Filter and only include movies that have a primary release date that is less or equal to the specified value, format YYYY-MM-DD"
    )
    with_genres: Optional[str] = Field(
        None,
        description="Comma-separated list of genre names. Supported values: action, adventure, animation, comedy, crime, documentary, drama, family, fantasy, history, horror, music, mystery, romance, science fiction, tv movie, thriller, war, western."
    )
    vote_average_gte: Optional[float] = Field(
        None,
        description="Filter and only include movies that have a vote average that is greater or equal to the specified value."
    )
    sort_by: Optional[str] = Field(
        "popularity.desc",
        description="Choose a sort option, e.g. popularity.desc, popularity.asc, release_date.desc, release_date.asc, revenue.desc, revenue.asc, primary_release_date.desc, primary_release_date.asc, original_title.desc, original_title.asc, vote_average.desc, vote_average.asc, vote_count.desc, vote_count.asc"
    )
    page: int = Field(
        1,
        description="Specify the page of results to query."
    )

@tool(
    "discover_movies",
    description="Discover movies based on different criteria like release date, genres, vote average, and popularity.",
    args_schema=DiscoverMovieInput
)
def discover_movies(
    primary_release_date_gte: Optional[str] = None,
    primary_release_date_lte: Optional[str] = None,
    with_genres: Optional[str] = None,
    vote_average_gte: Optional[float] = None,
    sort_by: str = "popularity.desc",
    page: int = 1
) -> List[Dict[str, Any]] | Dict[str, str]:
    """
    Discover movies using the TMDB API.
    """
    access_token = os.getenv("TMDB_ACCESS_KEY")
    if not access_token:
        return {"error": "TMDB_ACCESS_KEY not configured"}

    url = "https://api.themoviedb.org/3/discover/movie"
    
    params = {
        "page": page,
        "sort_by": sort_by,
    }
    
    if primary_release_date_gte:
        params["primary_release_date.gte"] = primary_release_date_gte
    if primary_release_date_lte:
        params["primary_release_date.lte"] = primary_release_date_lte

    if with_genres:
        genre_ids = []
        for g in with_genres.split(","):
            g_clean = g.strip().lower()
            if g_clean in GENRE_MAP:
                genre_ids.append(str(GENRE_MAP[g_clean]))
        if genre_ids:
            params["with_genres"] = "|".join(genre_ids)

    if vote_average_gte is not None:
        params["vote_average.gte"] = str(vote_average_gte)

    headers = {
        "Authorization": f"Bearer {access_token}",
        "accept": "application/json"
    }

    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()

        results = []
        for movie in data.get("results", []):
            results.append({
                "id": movie.get("id"),
                "title": movie.get("title"),
                "overview": movie.get("overview"),
                "release_date": movie.get("release_date"),
                "vote_average": movie.get("vote_average"),
                "popularity": movie.get("popularity"),
                "genre_ids": movie.get("genre_ids")
            })

        return results
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}
