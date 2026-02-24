"""Scrape and convert South Park transcripts to Fountain format.

This script reads episode_list.json and downloads/convert transcripts.
Run 01_generate_episode_list.py first to generate/update the episode list.
"""

import json
import time
from pathlib import Path
import requests
from bs4 import BeautifulSoup

from config import (
    TRANSCRIPTS_DIR,
    DELAY_BETWEEN_REQUESTS,
)
from models import Episode
from converter import convert_html_to_fountain


# Configuration
EPISODE_LIST_FILE = TRANSCRIPTS_DIR / "episode_list.json"
BASE_URL = "https://imsdb.com"


class TranscriptScraper:
    """Scraper for South Park transcripts."""
    
    def __init__(self):
        self.base_url = BASE_URL
    
    def load_episodes(self) -> list:
        """Load episode list from JSON file."""
        if not EPISODE_LIST_FILE.exists():
            raise FileNotFoundError(
                f"Episode list not found: {EPISODE_LIST_FILE}\n"
                "Run 01_generate_episode_list.py first to generate the episode list."
            )
        
        with open(EPISODE_LIST_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def save_episodes(self, episodes: list):
        """Save episode list to JSON file."""
        with open(EPISODE_LIST_FILE, 'w', encoding='utf-8') as f:
            json.dump(episodes, f, indent=2)
    
    def get_transcript_url(self, html_content: str) -> str:
        """Get the transcript URL from episode page HTML using .script-details a[href^="/transcripts"]."""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Find .script-details container
        script_details = soup.select('.script-details')
        
        if script_details:
            links = script_details[0].select('a[href^="/transcripts"]')
            if links:
                href = links[0].get('href', '')
                return self.base_url + href
        
        return None
    
    def get_transcript_from_page(self, url: str) -> str:
        """Directly fetch transcript from URL if it's a transcript page."""
        try:
            response = requests.get(url, timeout=30)
            if response.status_code == 200:
                if '<pre>' in response.text or '<pre ' in response.text:
                    return response.text
        except Exception:
            pass
        return None
    
    def download_and_convert(self, episodes: list) -> tuple:
        """Download all transcripts and convert to Fountain."""
        successful = 0
        failed = 0
        
        for i, ep in enumerate(episodes):
            season = ep['season']
            episode_num = ep['episode_num']
            title = ep['title']
            imsdb_url = ep.get('imsdb_url', '')
            transcript_url = ep.get('transcript_url', '')
            
            display_name = f"S{season:02d}E{episode_num:02d} - {title}"
            print(f"  [{i+1}/{len(episodes)}] {display_name}...", end=" ", flush=True)
            
            if not imsdb_url:
                print("✗ No URL")
                failed += 1
                continue
            
            # Check if already downloaded
            if transcript_url:
                safe_title = ep['title'].replace(' ', '_')
                safe_title = ''.join(c for c in safe_title if c.isalnum() or c in '_-')
                filepath = TRANSCRIPTS_DIR / f"S{season:02d}E{episode_num:02d}_{safe_title}.fountain"
                if filepath.exists():
                    print("✓ Already downloaded")
                    successful += 1
                    continue
            
            try:
                # If no transcript_url, fetch it
                if not transcript_url:
                    transcript_response = requests.get(imsdb_url, timeout=30)
                    if transcript_response.status_code != 200:
                        print(f"✗ Download failed ({transcript_response.status_code})")
                        failed += 1
                        continue
                    
                    new_transcript_url = self.get_transcript_url(transcript_response.text)
                    
                    if new_transcript_url:
                        transcript_url = new_transcript_url
                        ep['transcript_url'] = transcript_url
                    else:
                        # Try direct transcript URL
                        html_content = self.get_transcript_from_page(imsdb_url)
                        if html_content:
                            transcript_url = imsdb_url
                            ep['transcript_url'] = transcript_url
                        else:
                            print("✗ No transcript link found")
                            failed += 1
                            continue
                
                # Download transcript page
                transcript_response = requests.get(transcript_url, timeout=30)
                if transcript_response.status_code == 200:
                    html_content = transcript_response.text
                else:
                    print(f"✗ Transcript download failed ({transcript_response.status_code})")
                    failed += 1
                    continue
                
                # Convert to fountain
                fountain = convert_html_to_fountain(html_content, title)
                
                if fountain and len(fountain.strip()) > 50:
                    # Save to file
                    safe_title = title.replace(' ', '_')
                    safe_title = ''.join(c for c in safe_title if c.isalnum() or c in '_-')
                    filepath = TRANSCRIPTS_DIR / f"S{season:02d}E{episode_num:02d}_{safe_title}.fountain"
                    
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(fountain)
                    
                    print(f"✓ Saved to {filepath.name}")
                    successful += 1
                else:
                    print("✗ No transcript content")
                    failed += 1
                
            except Exception as e:
                print(f"✗ Error: {e}")
                failed += 1
            
            time.sleep(DELAY_BETWEEN_REQUESTS)
        
        return successful, failed


def main():
    """Main entry point."""
    print("=" * 60)
    print("South Park Transcript Scraper")
    print("=" * 60)
    
    scraper = TranscriptScraper()
    
    # Load episodes
    print(f"\nLoading episode list from {EPISODE_LIST_FILE}...")
    episodes = scraper.load_episodes()
    print(f"Loaded {len(episodes)} episodes")
    
    # Show current status
    done = sum(1 for ep in episodes if ep.get('transcript_url'))
    print(f"Episodes with transcript URLs: {done}/{len(episodes)}")
    
    have_files = 0
    for ep in episodes:
        season = ep['season']
        episode_num = ep['episode_num']
        title = ep['title']
        safe_title = title.replace(' ', '_')
        safe_title = ''.join(c for c in safe_title if c.isalnum() or c in '_-')
        filepath = TRANSCRIPTS_DIR / f"S{season:02d}E{episode_num:02d}_{safe_title}.fountain"
        if filepath.exists():
            have_files += 1
    
    print(f"Transcripts already downloaded: {have_files}")
    
    to_process = [ep for ep in episodes if not ep.get('transcript_url')]
    print(f"Need to process: {len(to_process)}")
    
    if not to_process and have_files == len(episodes):
        print("\nAll episodes already have transcripts!")
        return
    
    if to_process:
        print(f"\nFetching transcript URLs for {len(to_process)} episodes...")
        for i, ep in enumerate(to_process):
            season = ep['season']
            episode_num = ep['episode_num']
            title = ep['title']
            
            print(f"  [{i+1}/{len(to_process)}] S{season:02d}E{episode_num:02d} - {title}...", end=" ", flush=True)
            
            try:
                response = requests.get(ep['imsdb_url'], timeout=30)
                if response.status_code == 200:
                    new_url = scraper.get_transcript_url(response.text)
                    if new_url:
                        ep['transcript_url'] = new_url
                        print(f"✓ Found")
                    else:
                        print(f"✗ Not found")
                else:
                    print(f"✗ Failed")
            except Exception as e:
                print(f"✗ Error: {e}")
            
            time.sleep(DELAY_BETWEEN_REQUESTS)
        
        # Save updated URLs
        scraper.save_episodes(episodes)
    
    # Download transcripts
    print(f"\nDownloading transcripts...")
    successful, failed = scraper.download_and_convert(episodes)
    
    # Save updated episode list
    scraper.save_episodes(episodes)
    
    # Summary
    print("\n" + "=" * 60)
    print("Summary")
    print(f"  Total episodes: {len(episodes)}")
    print(f"  Successfully downloaded: {successful}")
    print(f"  Failed: {failed}")
    print(f"\nTranscripts saved to: {TRANSCRIPTS_DIR}/")
    print("=" * 60)


if __name__ == "__main__":
    main()
