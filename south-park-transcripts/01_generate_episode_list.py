"""Generate episode list for South Park from IMSDb.

This script only fetches and parses the episode list from IMSDb,
saving it to episode_list.json. Run this first to get/update the episode list.
"""

import json
import re
from pathlib import Path
import requests
from bs4 import BeautifulSoup

# Configuration
SOUTH_PARK_URL = "https://imsdb.com/TV/South%20Park.html"
BASE_URL = "https://imsdb.com"
OUTPUT_FILE = Path(__file__).parent / "transcripts" / "episode_list.json"


def get_episode_list() -> list:
    """Get list of all South Park episodes with correct season numbers."""
    print(f"Fetching episode list from {SOUTH_PARK_URL}...")
    
    response = requests.get(SOUTH_PARK_URL, timeout=30)
    response.raise_for_status()
    
    soup = BeautifulSoup(response.text, 'html.parser')
    
    episodes = []
    current_season = 1
    episode_counter = 0
    
    # Get all text content and find season headers
    # The page has h2 or h3 tags like "Series 1", "Series 2", etc.
    
    # Method: Walk through all elements and track when we hit a Series header
    body = soup.find('body')
    if body:
        for element in body.find_all(['h2', 'h3', 'h4', 'p', 'div']):
            text = element.get_text()
            
            # Check for season/series header
            series_match = re.search(r'Series\s*(\d+)', text, re.IGNORECASE)
            if series_match:
                current_season = int(series_match.group(1))
                episode_counter = 0
                print(f"  Found Series {current_season}")
                continue
            
            # Check for episode links within this element
            links = element.find_all('a', href=True)
            for link in links:
                href = link.get('href', '')
                text = link.get_text(strip=True)
                
                # Look for episode links: /TV Transcripts/South Park - ...
                if '/TV Transcripts/South Park' in href and href.endswith('.html'):
                    episode_counter += 1
                    
                    # Clean title
                    title = text.replace(' Script', '').strip()
                    
                    episode = {
                        "title": title,
                        "season": current_season,
                        "episode_num": episode_counter,
                        "imsdb_url": BASE_URL + href,
                        "transcript_url": ""
                    }
                    episodes.append(episode)
    
    # Alternative method if the above didn't work well:
    # Parse based on position in document
    if len(episodes) < 100:
        print("Trying alternative parsing method...")
        
        # Reset
        episodes = []
        current_season = 1
        episode_counter = 0
        
        # Find all headers and their positions
        headers = []
        for tag in soup.find_all(['h2', 'h3', 'h4']):
            text = tag.get_text()
            match = re.search(r'Series\s*(\d+)', text, re.IGNORECASE)
            if match:
                headers.append({
                    'tag': tag,
                    'season': int(match.group(1)),
                    'position': tag.sourceline if hasattr(tag, 'sourceline') else 0
                })
        
        # Sort by position
        headers.sort(key=lambda x: x['position'])
        
        # Find all episode links
        all_links = []
        for link in soup.find_all('a', href=True):
            href = link.get('href', '')
            text = link.get_text(strip=True)
            if '/TV Transcripts/South Park' in href and href.endswith('.html'):
                position = link.sourceline if hasattr(link, 'sourceline') else 0
                all_links.append({
                    'href': href,
                    'text': text,
                    'position': position
                })
        
        # Assign seasons based on position between headers
        for i, link_data in enumerate(all_links):
            # Find which season this belongs to
            season = 1
            for header in headers:
                if link_data['position'] > header['position']:
                    season = header['season']
            
            current_season = season
            episode_counter = i + 1  # Simple counter
            
            title = link_data['text'].replace(' Script', '').strip()
            
            episodes.append({
                "title": title,
                "season": current_season,
                "episode_num": episode_counter,
                "imsdb_url": BASE_URL + link_data['href'],
                "transcript_url": ""
            })
        
        # Now fix episode_num to be per-season, not global
        # Group by season and renumber
        season_eps = {}
        for ep in episodes:
            s = ep['season']
            if s not in season_eps:
                season_eps[s] = []
            season_eps[s].append(ep)
        
        # Renumber
        episodes = []
        for s in sorted(season_eps.keys()):
            for idx, ep in enumerate(season_eps[s], 1):
                ep['episode_num'] = idx
                episodes.append(ep)
    
    print(f"Found {len(episodes)} episodes")
    return episodes


def main():
    """Main entry point."""
    print("=" * 60)
    print("South Park Episode List Generator")
    print("=" * 60)
    
    # Ensure output directory exists
    OUTPUT_FILE.parent.mkdir(exist_ok=True)
    
    # Get episode list
    episodes = get_episode_list()
    
    # Save to JSON
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(episodes, f, indent=2)
    
    print(f"\nSaved episode list to {OUTPUT_FILE}")
    
    # Show summary
    seasons = {}
    for ep in episodes:
        s = ep['season']
        seasons[s] = seasons.get(s, 0) + 1
    
    print("\nSeason summary:")
    for s in sorted(seasons.keys()):
        print(f"  Season {s}: {seasons[s]} episodes")
    
    print("=" * 60)


if __name__ == "__main__":
    main()
