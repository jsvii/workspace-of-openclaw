"""Configuration for IMDb Top 250 Screenplays project."""

# Proxy configuration
PROXIES = {
    "http": "http://127.0.0.1:20171",
    "https": "http://127.0.0.1:20171",
    "socks5": "socks5://127.0.0.1:20170",
}

# URLs
IMDB_TOP250_URL = "https://www.imdb.com/chart/top/"
IMSDB_BASE_URL = "https://imsdb.com"
IMSDB_SEARCH_URL = "https://imsdb.com/searches"

# Output
SCREENPLAYS_DIR = "screenplays"

# Request settings
REQUEST_TIMEOUT = 30
DELAY_BETWEEN_REQUESTS = 2  # seconds to avoid rate limiting
