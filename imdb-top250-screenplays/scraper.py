"""Scraping logic for IMDb and IMSDb."""

import re
import json
import time
import requests
from typing import Optional, List
from bs4 import BeautifulSoup

from config import (
    IMDB_TOP250_URL,
    IMSDB_BASE_URL,
    IMSDB_SEARCH_URL,
    PROXIES,
    REQUEST_TIMEOUT,
    DELAY_BETWEEN_REQUESTS,
)
from models import Movie


class IMSDbScraper:
    """Scraper for IMSDb (Internet Movie Script Database)."""
    
    # Cache the all-scripts page for searching
    _all_scripts_cache = None
    
    def __init__(self):
        self.session = requests.Session()
        self.session.proxies = PROXIES
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })
    
    def _get_all_scripts(self) -> BeautifulSoup:
        """Get and cache the all-scripts page."""
        if IMSDbScraper._all_scripts_cache is None:
            url = f"{IMSDB_BASE_URL}/all-scripts.html"
            response = self.session.get(url, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            IMSDbScraper._all_scripts_cache = BeautifulSoup(response.text, "html.parser")
        return IMSDbScraper._all_scripts_cache
    
    def search_movie(self, movie_title: str) -> Optional[str]:
        """Search for a movie on IMSDb using search.php and verify the result."""
        # Clean the movie title for search
        search_query = movie_title.strip()
        
        try:
            # Search using the search.php endpoint
            response = self.session.post(
                f"{IMSDB_BASE_URL}/search.php",
                data={"search_query": search_query, "submit": "Go!"},
                timeout=REQUEST_TIMEOUT
            )
            
            if response.status_code != 200:
                return None
            
            # Parse the search result page
            soup = BeautifulSoup(response.text, "html.parser")
            
            # Use the same DOM expression: table td[valign="top"][2]
            tables = soup.find_all('table')
            main_block = None
            
            for table in tables:
                tds = table.find_all('td', attrs={'valign': 'top'})
                if len(tds) >= 2:
                    main_block = tds[1]
                    break
            
            if not main_block:
                return None
            
            # Find all links in the main block
            links = main_block.find_all('a', href=True)
            
            # Filter for movie intro pages (not transcript pages)
            movie_links = []
            for link in links:
                href = link.get('href', '')
                text = link.get_text(strip=True)
                # Look for /Movie Scripts/ links (intro pages)
                if '/movie/' in href.lower() or '/Movie Scripts/' in href:
                    movie_links.append({'href': href, 'text': text})
            
            if not movie_links:
                return None

            print(movie_links)
            # Score the links to find best match
            title_lower = movie_title.lower().strip()
            title_clean = title_lower.replace('the ', '').strip()
            
            best_match = None
            best_score = 0
            
            for link_data in movie_links:
                href = link_data['href']
                text = link_data['text'].lower().replace(' script', '').strip()
                
                # Calculate match score
                if title_clean == text:
                    score = 100
                elif title_clean in text or text in title_clean:
                    score = 80
                elif all(word in text for word in title_clean.split() if len(word) > 2):
                    score = 60
                else:
                    score = 0
                
                if score > best_score:
                    best_score = score
                    best_match = href

            if best_match and best_score >= 60:
                # Visit the intro page to get transcript URL
                intro_url = IMSDB_BASE_URL + best_match if best_match.startswith('/') else best_match
                transcript_url = self._get_transcript_from_intro_page(intro_url, movie_title)

                if transcript_url:
                    return transcript_url
            
            return None
            
        except Exception as e:
            print(f"Search error: {e}")
            return None
    
    def _get_transcript_from_intro_page(self, intro_url: str, movie_title: str) -> Optional[str]:
        """Visit the movie intro page and get transcript URL using .script-details a[href^='/transcripts']"""
        try:
            response = self.session.get(intro_url, timeout=REQUEST_TIMEOUT)
            if response.status_code != 200:
                return None
            
            soup = BeautifulSoup(response.text, "html.parser")
            
            # Use .script-details a[href^="/scripts"] to find transcript link
            script_details = soup.select('.script-details')
            
            if script_details:
                links = script_details[0].select('a[href^="/scripts"]')
                if links:
                    href = links[0].get('href', '')
                    if href:
                        return IMSDB_BASE_URL + href
            
            return None
            
        except Exception as e:
            return None
    
    def _verify_script_url(self, url: str, movie_title: str = "") -> bool:
        """Check if the URL has actual screenplay content in a <pre> tag."""
        try:
            response = self.session.get(url, timeout=REQUEST_TIMEOUT)
            if response.status_code != 200:
                return False
            
            # Check for <pre> tag with substantial content
            pres = re.findall(r'<pre[^>]*>(.*?)</pre>', response.text, re.DOTALL)
            if not pres or len(pres[0].strip()) < 100:
                return False
            
            # If movie_title provided, check if it's in the top area of <pre>
            if movie_title:
                pre_content = pres[0][:1000]  # Check first 1000 chars
                # Check if title appears (case insensitive)
                title_words = movie_title.lower().split()
                # Check if most title words are in the first part
                matches = sum(1 for word in title_words if word in pre_content.lower())
                if matches < len(title_words) * 0.5:
                    return False
            
            return True
            
        except:
            pass
        return False
    
    def get_script_url_by_title(self, movie_title: str) -> Optional[str]:
        """Try to construct the direct URL for the movie script (fallback)."""
        # Simply format the title with dashes
        formatted_title = movie_title.replace("'", "'").replace(" ", "-").strip()
        
        direct_url = f"{IMSDB_BASE_URL}/scripts/{formatted_title}.html"
        
        # Verify the URL has actual screenplay content
        if self._verify_script_url(direct_url, movie_title):
            return direct_url
        
        return None
    
    def download_script(self, url: str) -> Optional[str]:
        """Download the screenplay HTML from the given URL."""
        try:
            response = self.session.get(url, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            print(f"Error downloading script from '{url}': {e}")
            return None


class IMDbScraper:
    """Scraper for IMDb Top 250."""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.proxies = PROXIES
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept-Language": "en-US,en;q=0.9"
        })

    def get_top250(self) -> List[Movie]:
        """Scrape the IMDb Top 250 list."""
        print("Fetching IMDb Top 250 page...")
        
        # First get the JSON-LD data which has all 250 movies
        movies_data = self._get_json_ld_movies()
        
        if not movies_data:
            print("JSON-LD failed, trying HTML parsing...")
            movies_data = self._get_movies_from_html()

        print(f"Found {len(movies_data)} movies, fetching details...")

        # Now fetch details (year, english title) for each movie
        movies = []
        for i, data in enumerate(movies_data):
            imdb_id = data['imdb_id']
            imdb_url = f"https://www.imdb.com/title/{imdb_id}/"
            print(f"  [{i+1}/{len(movies_data)}] Fetching {imdb_id}...", end=" ", flush=True)
            details = None # self._get_movie_details(imdb_id)
            title = data.get('title')
            if details:
                movies.append(Movie(
                    title=title,
                    year=details['year'],
                    imdb_id=imdb_id,
                    imdb_url=imdb_url
                ))
                print(f"{title} ({details['year']})")
            else:
                # Use fallback
                movies.append(Movie(
                    title=title,
                    year=data.get('year', 0),
                    imdb_id=imdb_id,
                    imdb_url=imdb_url
                ))
                print("failed, using fallback")

            # time.sleep(0.5)  # Small delay between requests
        
        return movies
    
    def _get_json_ld_movies(self) -> List[dict]:
        """Get movie list from JSON-LD data."""
        try:
            response = self.session.get(IMDB_TOP250_URL, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, "html.parser")
            script_tags = soup.find_all("script", type="application/ld+json")
            
            for script in script_tags:
                try:
                    data = json.loads(script.string)
                    if isinstance(data, dict) and data.get("@type") == "ItemList":
                        items = data.get("itemListElement", [])
                        movies = []
                        for item in items:
                            movie_data = item.get("item", {})
                            url = movie_data.get("url", "")
                            imdb_match = re.search(r'/title/(tt\d+)/', url)
                            if imdb_match:
                                movies.append({
                                    'imdb_id': imdb_match.group(1),
                                    'title': movie_data.get("name", "").replace('&apos;', '\''),
                                })
                        return movies
                except (json.JSONDecodeError, AttributeError):
                    continue
        except requests.RequestException as e:
            print(f"Error fetching IMDb: {e}")
        return []
    
    def _get_movies_from_html(self) -> List[dict]:
        """Fallback: parse movies from HTML."""
        try:
            response = self.session.get(IMDB_TOP250_URL, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
            
            items = soup.select('li.ipc-metadata-list-summary-item')
            movies = []
            
            for index, item in items:
                link = item.find('a', href=re.compile(r'/title/tt\d+'))
                if link:
                    href = link.get('href', '')
                    imdb_match = re.search(r'/title/(tt\d+)', href)
                    if imdb_match:
                        movies.append({
                            'imdb_id': imdb_match.group(1),
                            'title': '',
                            'year': 0
                        })
            return movies
        except:
            return []
    
    def _get_movie_details(self, imdb_id: str) -> Optional[dict]:
        """Get movie details (title, year) from individual movie page."""
        try:
            url = f"https://www.imdb.com/title/{imdb_id}/"
            response = self.session.get(url, timeout=REQUEST_TIMEOUT)
            if response.status_code != 200:
                return None
            
            soup = BeautifulSoup(response.text, "html.parser")
            
            # Get title - prefer English/original title from JSON-LD
            title = None
            year = 0
            
            # Try JSON-LD first for original title
            scripts = soup.find_all('script', type='application/ld+json')
            for script in scripts:
                try:
                    data = json.loads(script.string)
                    if isinstance(data, dict) and data.get('@type') == 'Movie':
                        # Get original title (not alternateName which is translated)
                        title = data.get("name")
                        # Try to get from datePublished
                        date = data.get('datePublished', '')
                        if date:
                            year = int(date[:4])
                        break
                except:
                    continue
            
            # Fallback to title tag if no JSON-LD title
            if not title:
                title_tag = soup.find('title')
                if title_tag:
                    title_text = title_tag.get_text()
                    title_match = re.match(r'^(.+?)\s*\(', title_text)
                    if title_match:
                        title = title_match.group(1).strip()
                    else:
                        title = title_text.split(' - ')[0].strip()
            
            # Get year if not found from JSON-LD
            if not year:
                title_tag = soup.find('title')
                if title_tag:
                    title_tag_text = title_tag.get_text()
                    year_match = re.search(r'\((\d{4})\)', title_tag_text)
                    if year_match:
                        year = int(year_match.group(1))
            
            if not year:
                meta = soup.find('meta', attrs={'name': 'keywords'})
                if meta:
                    content = meta.get('content', '')
                    year_match = re.search(r'(\d{4})', content)
                    if year_match:
                        year = int(year_match.group(1))
            
            if title and year:
                return {'title': title, 'year': year}
            
            return None
            
        except requests.RequestException:
            return None


def scrape_all_screenplays():
    """Main function to scrape IMDb Top 250 and find screenplays."""
    print("=" * 60)
    print("Starting IMDb Top 250 Screenplay Scraper")
    print("=" * 60)
    
    imdb_scraper = IMDbScraper()
    movies = imdb_scraper.get_top250()
    
    print(f"\nTotal movies: {len(movies)}")
    
    imsdb_scraper = IMSDbScraper()
    results = []
    
    print("\nSearching for screenplays on IMSDb...")
    for i, movie in enumerate(movies):
        print(f"[{i+1}/{len(movies)}] {movie.title} ({movie.year})...", end=" ", flush=True)
        
        # First try direct URL construction
        script_url = imsdb_scraper.get_script_url_by_title(movie.title)
        
        # If not found, use search
        if not script_url:
            script_url = imsdb_scraper.search_movie(movie.title)
        
        if script_url:
            print(f"✓ Found")
            movie.imsdb_url = script_url
            results.append(movie)
        else:
            print(f"✗ Not found")

        print(f"  Actual URL: {script_url}")
        
        time.sleep(DELAY_BETWEEN_REQUESTS)
    
    return results


if __name__ == "__main__":
    movies = scrape_all_screenplays()
    print(f"\nFound {len(movies)} screenplays on IMSDb")
    for m in movies:
        print(f"  - {m.title} ({m.year}): {m.imsdb_url}")
