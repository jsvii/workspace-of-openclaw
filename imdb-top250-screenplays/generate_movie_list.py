"""Generate movie list for IMDb Top 250 Screenplays.

This script scrapes IMDb Top 250 movies and searches for their
screenplays on IMSDb, saving the results to movie_list.json.
Run this first to generate/update the movie list.
"""

import json
import time
from pathlib import Path

from pathlib import Path

from config import SCREENPLAYS_DIR, DELAY_BETWEEN_REQUESTS
from scraper import IMDbScraper, IMSDbScraper
from models import Movie

# Output file
MOVIE_LIST_FILE = Path(SCREENPLAYS_DIR) / "movie_list.json"


def ensure_screenplays_dir():
    """Create the screenplays directory if it doesn't exist."""
    Path(SCREENPLAYS_DIR).mkdir(exist_ok=True)


def load_movie_list() -> list:
    """Load movie list from existing JSON file."""
    if MOVIE_LIST_FILE.exists():
        with open(MOVIE_LIST_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None


def save_movie_list(movies: list):
    """Save movie list to JSON file."""
    with open(MOVIE_LIST_FILE, 'w', encoding='utf-8') as f:
        json.dump(movies, f, indent=2)


def main():
    """Main workflow: scrape IMDb Top 250 + find IMSDb screenplays."""
    print("=" * 60)
    print("IMDb Top 250 - Movie List Generator")
    print("=" * 60)
    
    ensure_screenplays_dir()
    
    # Check for existing movie list
    existing = load_movie_list()
    if existing:
        # Check if we need to update (missing imsdb_url)
        needs_update = any(m.get('imsdb_url', '') == '' for m in existing)
        if not needs_update:
            print(f"\nMovie list already exists: {MOVIE_LIST_FILE}")
            print(f"Found {len(existing)} movies with screenplays")
            return
        else:
            print(f"\nFound existing movie list, but some entries missing IMSDb URLs")
            print("Will update missing URLs...")
    
    # Step 1: Scrape IMDb Top 250
    print("\n[1/2] Scraping IMDb Top 250 movies...")
    imdb_scraper = IMDbScraper()
    movies = imdb_scraper.get_top250()
    print(f"Found {len(movies)} movies")

    if not movies:
        print("No movies found. Check network/proxy configuration.")
        return

    # Step 2: Find screenplays on IMSDb
    print("\n[2/2] Searching for screenplays on IMSDb...")
    imsdb_scraper = IMSDbScraper()
    movies_with_scripts = []

    for i, movie in enumerate(movies):
        print(f"  [{i+1}/{len(movies)}] {movie.title} ({movie.year})...", end=" ")

        # Try direct URL first
        script_url = imsdb_scraper.get_script_url_by_title(movie.title)
        
        # If not found, try search
        if not script_url:
            script_url = imsdb_scraper.search_movie(movie.title)
        
        if script_url:
            movie.imsdb_url = script_url
            movies_with_scripts.append(movie)
            print(f"✓ Found")
        else:
            print("✗ Not found")
        
        time.sleep(DELAY_BETWEEN_REQUESTS)
    
    movies = movies_with_scripts
    print(f"\nFound {len(movies_with_scripts)} screenplays on IMSDb")
    
    # Save the movie list
    movie_list = [
        {
            "title": m.title,
            "year": m.year,
            "imdb_id": m.imdb_id,
            "imdb_url": m.imdb_url,
            "imsdb_url": m.imsdb_url
        }
        for m in movies
    ]
    save_movie_list(movie_list)
    
    print(f"Saved movie list to {MOVIE_LIST_FILE}")
    
    # Summary
    print("\n" + "=" * 60)
    print("Summary")
    print(f"  Total movies scraped: {len(movies)}")
    print(f"  Movies with screenplays: {len(movies_with_scripts)}")
    print(f"  Saved to: {MOVIE_LIST_FILE}")
    print("=" * 60)


if __name__ == "__main__":
    main()
