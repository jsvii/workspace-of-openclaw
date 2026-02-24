"""Main entry point for IMDb Top 250 Screenplays project."""

import os
import json
import time
from typing import List
from pathlib import Path

from config import SCREENPLAYS_DIR, DELAY_BETWEEN_REQUESTS
from scraper import IMDbScraper, IMSDbScraper, scrape_all_screenplays
from converter import convert_html_to_fountain
from models import Movie


def ensure_screenplays_dir():
    """Create the screenplays directory if it doesn't exist."""
    Path(SCREENPLAYS_DIR).mkdir(exist_ok=True)


def save_screenplay(movie: Movie, fountain_content: str) -> str:
    """Save the Fountain screenplay to a file."""
    filepath = os.path.join(SCREENPLAYS_DIR, f"{movie.safe_filename}.fountain")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(fountain_content)
    return filepath


def load_movie_list() -> List[Movie]:
    """Load movie list from existing movie_list.json if available."""
    movie_list_file = os.path.join(SCREENPLAYS_DIR, "movie_list.json")
    
    if os.path.exists(movie_list_file):
        print(f"Loading from existing movie_list.json...")
        with open(movie_list_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        movies = []
        for item in data:
            movie = Movie(
                title=item.get("title", ""),
                year=item.get("year", 0),
                imdb_id=item.get("imdb_id", ""),
                imdb_url=item.get("imdb_url", ""),
                imsdb_url=item.get("imsdb_url", "")
            )
            movies.append(movie)
        
        print(f"Loaded {len(movies)} movies from local file")
        return movies
    
    return None


def main():
    """Main workflow: scrape movies, find screenplays, convert to Fountain."""
    print("=" * 60)
    print("IMDb Top 250 Screenplays Scraper")
    print("=" * 60)
    
    ensure_screenplays_dir()
    
    # Try to load from existing movie_list.json first
    movies = load_movie_list()
    
    if movies is None:
        # Step 1: Scrape IMDb Top 250
        print("\n[1/4] Scraping IMDb Top 250 movies...")
        imdb_scraper = IMDbScraper()
        movies = imdb_scraper.get_top250()
        print(f"Found {len(movies)} movies")

        if not movies:
            print("No movies found. Check network/proxy configuration.")
            return
        
        # Step 2: Find screenplays on IMSDb
        print("\n[2/4] Searching for screenplays on IMSDb...")
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
        
        # Save the movie list for reference
        movie_list_file = os.path.join(SCREENPLAYS_DIR, "movie_list.json")
        with open(movie_list_file, "w", encoding="utf-8") as f:
            json.dump([
                {
                    "title": m.title,
                    "year": m.year,
                    "imdb_id": m.imdb_id,
                    "imdb_url": m.imdb_url,
                    "imsdb_url": m.imsdb_url
                }
                for m in movies
            ], f, indent=2)
        print(f"Saved movie list to {movie_list_file}")
    else:
        # Filter to only movies with imsdb_url
        movies = [m for m in movies if m.imsdb_url]
        print(f"Using {len(movies)} movies with screenplays from local data")
    
    # Step 3: Download and convert screenplays
    print("\n[3/4] Downloading and converting screenplays...")
    imsdb_scraper = IMSDbScraper()
    successful = 0
    failed = 0
    skipped = 0
    
    for i, movie in enumerate(movies):
        print(f"  [{i+1}/{len(movies)}] {movie.title}...", end=" ")
        
        html_content = imsdb_scraper.download_script(movie.imsdb_url)
        
        if html_content:
            try:
                fountain_content = convert_html_to_fountain(html_content)
                if not fountain_content or len(fountain_content.strip()) < 50:
                    print("✗ No screenplay content found on page")
                    failed += 1
                else:
                    filepath = save_screenplay(movie, fountain_content)
                    print(f"✓ Saved to {filepath}")
                    successful += 1
            except Exception as e:
                print(f"✗ Conversion error: {e}")
                failed += 1
        else:
            print("✗ Download failed")
            failed += 1
        
        time.sleep(DELAY_BETWEEN_REQUESTS)
    
    # Step 4: Summary
    print("\n[4/4] Summary")
    print(f"  Total movies with screenplays: {len(movies)}")
    print(f"  Successfully converted: {successful}")
    print(f"  Failed: {failed}")
    print(f"\nScreenplays saved to: {SCREENPLAYS_DIR}/")
    print("=" * 60)


if __name__ == "__main__":
    main()
