"""Data models for movies and screenplays."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class Movie:
    """Represents a movie from IMDb Top 250."""
    title: str
    year: int
    imdb_id: str
    imdb_url: str
    imsdb_url: Optional[str] = None
    
    @property
    def safe_filename(self) -> str:
        """Create a safe filename from the movie title."""
        return f"{self.title} ({self.year})".replace("/", "-").replace(":", "-")


@dataclass
class Screenplay:
    """Represents a screenplay."""
    movie: Movie
    html_content: str
    fountain_content: str = ""
    
    @property
    def filename(self) -> str:
        """Output filename for the Fountain screenplay."""
        return f"{self.movie.safe_filename}.fountain"
