"""Data models for South Park transcripts."""

from dataclasses import dataclass
from typing import Optional
import re


@dataclass
class Episode:
    """Represents a South Park episode."""
    title: str
    season: int
    episode_num: int  # Episode number within season (e.g., 1 for S01E01)
    imsdb_url: Optional[str] = None
    transcript_url: Optional[str] = None
    
    @property
    def safe_filename(self) -> str:
        """Generate safe filename for the episode."""
        # Clean title for filename
        clean_title = re.sub(r'[^\w\s-]', '', self.title)
        clean_title = re.sub(r'\s+', '_', clean_title.strip())
        return f"S{self.season:02d}E{self.episode_num:02d}_{clean_title}"
    
    @property
    def display_name(self) -> str:
        """Display name with season/episode."""
        return f"S{self.season:02d}E{self.episode_num:02d} - {self.title}"


@dataclass
class Season:
    """Represents a season of South Park."""
    season_num: int
    episodes: list
    
    @property
    def episode_count(self) -> int:
        return len(self.episodes)
