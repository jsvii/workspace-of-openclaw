"""Generate episode list for South Park from IMSDb.

This script fetches and parses the episode list from IMSDb,
including transcript URLs, and saves it to episode_list.json.
Run this first to get/update the episode list.

Usage:
    python 01_generate_episode_list.py
    python 01_generate_episode_list.py --url "https://imsdb.com/TV/South%20Park.html"
"""

import json
import re
import argparse
from pathlib import Path
import requests
from bs4 import BeautifulSoup

# Default Configuration
DEFAULT_SOUTH_PARK_URL = "https://imsdb.com/TV/South%20Park.html"
BASE_URL = "https://imsdb.com"
OUTPUT_FILE = Path(__file__).parent / "transcripts" / "episode_list.json"
DELAY_BETWEEN_REQUESTS = 1.0


def get_episode_list(south_park_url: str) -> list:
    """Get list of all South Park episodes with correct season numbers."""
    print(f"Fetching episode list from {south_park_url}...")
    
    response = requests.get(south_park_url, timeout=30)
    response.raise_for_status()
    
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Find all h2 tags that contain "Series X"
    h2_tags = soup.find_all('h2')
    season_positions = {}  # {season_num: index in h2_tags}
    
    for idx, h2 in enumerate(h2_tags):
        text = h2.get_text(strip=True)
        match = re.search(r'Series\s*(\d+)', text, re.IGNORECASE)
        if match:
            season_positions[int(match.group(1))] = idx
    
    print(f"Found seasons: {list(season_positions.keys())}")
    
    # Get all episode links in order
    all_links = []
    for link in soup.find_all('a', href=True):
        href = link.get('href', '')
        text = link.get_text(strip=True)
        if '/TV Transcripts/South Park' in href and href.endswith('.html'):
            all_links.append({
                'href': href,
                'text': text,
            })
    
    print(f"Found {len(all_links)} episode links")
    
    # Assign seasons to episodes based on which h2 they come after
    episodes = []
    for i, link_data in enumerate(all_links):
        # Find which season this episode belongs to
        # It should be after the h2 for that season but before the next h2
        
        # Simple approach: count which season bucket based on position
        # Since we know total episodes per season from the page structure
        
        title = link_data['text'].replace(' Script', '').strip()
        
        # Find the episode's position relative to season headers
        # by checking if it's in the same parent element
        
        # Get the parent of this link
        parent = link_data.get('parent')
        
        episodes.append({
            "title": title,
            "season": 1,  # Will be fixed
            "episode_num": i + 1,  # Temporary
            "imsdb_url": BASE_URL + link_data['href'],
            "transcript_url": ""
        })
    
    # Better approach: iterate through h2 tags and find episodes under each
    episodes = []
    season_num = 1
    episode_in_season = 0
    
    # Get body content
    body = soup.find('body')
    if body:
        for child in body.children:
            if hasattr(child, 'get_text'):
                text = child.get_text(strip=True)
                
                # Check if this is a season header
                match = re.search(r'Series\s*(\d+)', text, re.IGNORECASE)
                if match:
                    season_num = int(match.group(1))
                    episode_in_season = 0
                    continue
                
                # Check for episode links in this element
                if child.name in ['h2', 'h3', 'h4', 'p', 'div', 'td']:
                    links = child.find_all('a', href=True) if hasattr(child, 'find_all') else []
                    for link in links:
                        href = link.get('href', '')
                        link_text = link.get_text(strip=True)
                        
                        if '/TV Transcripts/South Park' in href and href.endswith('.html'):
                            episode_in_season += 1
                            title = link_text.replace(' Script', '').strip()
                            
                            episodes.append({
                                "title": title,
                                "season": season_num,
                                "episode_num": episode_in_season,
                                "imsdb_url": BASE_URL + href,
                                "transcript_url": ""
                            })
    
    # If that didn't work well, try yet another approach
    if len(episodes) < 100:
        print("Trying alternative parsing...")
        episodes = []
        
        # Use the position of links relative to h2 headers
        h2_list = soup.find_all('h2')
        
        for idx, h2 in enumerate(h2_list):
            text = h2.get_text(strip=True)
            match = re.search(r'Series\s*(\d+)', text, re.IGNORECASE)
            if not match:
                continue
            
            current_season = int(match.group(1))
            
            # Find all links after this h2 until next h2
            next_h2 = h2_list[idx + 1] if idx + 1 < len(h2_list) else None
            
            # Get all elements between this h2 and next h2
            for sibling in h2.find_next_siblings():
                if sibling == next_h2:
                    break
                if hasattr(sibling, 'find_all'):
                    links = sibling.find_all('a', href=True)
                    for link in links:
                        href = link.get('href', '')
                        link_text = link.get_text(strip=True)
                        
                        if '/TV Transcripts/South Park' in href and href.endswith('.html'):
                            # Get current episode number for this season
                            existing_count = sum(1 for ep in episodes if ep['season'] == current_season)
                            
                            title = link_text.replace(' Script', '').strip()
                            episodes.append({
                                "title": title,
                                "season": current_season,
                                "episode_num": existing_count + 1,
                                "imsdb_url": BASE_URL + href,
                                "transcript_url": ""
                            })
    
    print(f"Parsed {len(episodes)} episodes")
    return episodes


def get_transcript_url(imsdb_url: str) -> str:
    """Get transcript URL from episode page using .script-details a[href^="/transcripts"]."""
    try:
        response = requests.get(imsdb_url, timeout=30)
        if response.status_code != 200:
            return ""
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find .script-details container
        script_details = soup.select('.script-details')
        
        if script_details:
            links = script_details[0].select('a[href^="/transcripts"]')
            if links:
                href = links[0].get('href', '')
                return BASE_URL + href
        
    except Exception as e:
        print(f"    Warning: {e}")
    
    return ""


def main():
    """Main entry point."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Generate episode list for South Park from IMSDb.")
    parser.add_argument(
        "--url", 
        type=str, 
        default=DEFAULT_SOUTH_PARK_URL,
        help="URL of the TV transcript page"
    )
    args = parser.parse_args()
    
    south_park_url = args.url
    
    print("=" * 60)
    print("South Park Episode List Generator")
    print("=" * 60)
    print(f"Using URL: {south_park_url}")
    
    # Ensure output directory exists
    OUTPUT_FILE.parent.mkdir(exist_ok=True)
    
    # Get episode list
    episodes = get_episode_list(south_park_url)
    
    # Fetch transcript URLs for each episode
    print("\nFetching transcript URLs...")
    for i, ep in enumerate(episodes):
        season = ep['season']
        episode_num = ep['episode_num']
        title = ep['title']
        
        print(f"  [{i+1}/{len(episodes)}] S{season:02d}E{episode_num:02d} - {title}...", end=" ", flush=True)
        
        transcript_url = get_transcript_url(ep['imsdb_url'])
        
        if transcript_url:
            ep['transcript_url'] = transcript_url
            print(f"✓ Found")
        else:
            print(f"✗ Not found")
    
    # Save to JSON
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(episodes, f, indent=2)
    
    print(f"\nSaved episode list to {OUTPUT_FILE}")
    
    # Show summary
    seasons = {}
    for ep in episodes:
        s = ep['season']
        seasons[s] = seasons.get(s, 0) + 1
    
    have_urls = sum(1 for ep in episodes if ep.get('transcript_url'))
    
    print("\nSeason summary:")
    for s in sorted(seasons.keys()):
        print(f"  Season {s}: {seasons[s]} episodes")
    
    print(f"\nTranscript URLs found: {have_urls}/{len(episodes)}")
    print("=" * 60)


if __name__ == "__main__":
    main()
