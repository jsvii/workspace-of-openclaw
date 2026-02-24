# IMDb Top 250 Screenplays Project

Python project to scrape IMDb Top 250 movies and convert screenplays from IMSDb to Fountain format.

## Setup

```bash
pip install -r requirements.txt
```

## Usage

```bash
python main.py
```

Screenplays will be saved to the `screenplays/` folder.

## Project Structure

- `main.py` - Entry point
- `scraper.py` - IMDb and IMSDb scraping
- `converter.py` - HTML to Fountain conversion
- `models.py` - Data models
- `config.py` - Configuration
