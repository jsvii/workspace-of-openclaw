"""Scrape and convert IMDb Top 250 screenplays to Fountain.

This script reads movie_list.json and downloads/converts screenplays.
Run 01_generate_movie_list.py first to generate the movie list.
"""

import os
import json
import time
from pathlib import Path

from pathlib import Path

from config import SCREENPLAYS_DIR, DELAY_BETWEEN_REQUESTS
from scraper import IMSDbScraper
from converter import convert_html_to_fountain
from models import Movie

# Output file
MOVIE_LIST_FILE = Path(SCREENPLAYS_DIR) / "movie_list.json"


def ensure_screenplays_dir():
    """Create the screenplays directory if it doesn't exist."""
    Path(SCREENPLAYS_DIR).mkdir(exist_ok=True)


def load_movie_list() -> list:
    """Load movie list from JSON file."""
    if not MOVIE_LIST_FILE.exists():
        raise FileNotFoundError(
            f"Movie list not found: {MOVIE_LIST_FILE}\n"
            "Run 01_generate_movie_list.py first to generate the movie list."
        )
    
    with open(MOVIE_LIST_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_movie_list(movies: list):
    """Save movie list to JSON file."""
    with open(MOVIE_LIST_FILE, 'w', encoding='utf-8') as f:
        json.dump(movies, f, indent=2)


def save_screenplay(movie: Movie, fountain_content: str) -> Path:
    """Save the Fountain screenplay to a file."""
    filepath = Path(SCREENPLAYS_DIR) / f"{movie.safe_filename}.fountain"
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(fountain_content)
    return filepath


def main():
    """Main workflow: download and convert screenplays."""
    print("=" * 60)
    print("IMDb Top 250 - Screenplay Scraper")
    print("=" * 60)
    
    ensure_screenplays_dir()
    
    # Load movie list
    print(f"\nLoading movie list from {MOVIE_LIST_FILE}...")
    movies_data = load_movie_list()
    print(f"Loaded {len(movies_data)} movies")
    
    # Convert to Movie objects
    movies = []
    for item in movies_data:
        movie = Movie(
            title=item.get("title", ""),
            year=item.get("year", 0),
            imdb_id=item.get("imdb_id", ""),
            imdb_url=item.get("imdb_url", ""),
            imsdb_url=item.get("imsdb_url", "")
        )
        movies.append(movie)
    
    # Filter to movies with IMSDb URL
    movies = [m for m in movies if m.imsdb_url]
    print(f"Movies with screenplay URLs: {len(movies)}")
    
    # Check which ones are already downloaded
    to_download = []
    already_done = 0
    
    for movie in movies:
        filepath = Path(SCREENPLAYS_DIR) / f"{movie.safe_filename}.fountain"
        if filepath.exists():
            already_done += 1
        else:
            to_download.append(movie)
    
    print(f"Already downloaded: {already_done}")
    print(f"Need to download: {len(to_download)}")
    
    if not to_download:
        print("\nAll screenplays already downloaded!")
        return
    
    # Download and convert
    print(f"\nDownloading {len(to_download)} screenplays...")
    imsdb_scraper = IMSDbScraper()
    successful = 0
    failed = 0
    
    for i, movie in enumerate(to_download):
        print(f"  [{i+1}/{len(to_download)}] {movie.title} ({movie.year})...", end=" ")
        
        try:
            html_content = imsdb_scraper.download_script(movie.imsdb_url)
            
            if html_content:
                fountain_content = convert_html_to_fountain(html_content)
                
                if fountain_content and len(fountain_content.strip()) > 50:
                    filepath = save_screenplay(movie, fountain_content)
                    print(f"✓ Saved to {filepath.name}")
                    successful += 1
                else:
                    print("✗ No screenplay content found on page")
                    failed += 1
            else:
                print("✗ Download failed")
                failed += 1
                
        except Exception as e:
            print(f"✗ Error: {e}")
            failed += 1
        
        time.sleep(DELAY_BETWEEN_REQUESTS)
    
    # Summary
    print("\n" + "=" * 60)
    print("Summary")
    print(f"  Total movies with screenplays: {len(movies)}")
    print(f"  Successfully converted: {successful}")
    print(f"  Failed: {failed}")
    print(f"\nScreenplays saved to: {SCREENPLAYS_DIR}/")
    print("=" * 60)


if __name__ == "__main__":
    main()
