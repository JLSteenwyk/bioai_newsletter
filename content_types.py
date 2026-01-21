"""Data classes for social content generation."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional


@dataclass
class SocialPost:
    """Represents generated social content for all platforms."""

    id: str
    title: str
    topic_keyword: str
    source_articles: List[Dict] = field(default_factory=list)
    bluesky_posts: List[str] = field(default_factory=list)  # Thread posts
    linkedin_post: str = ""
    blog_title: str = ""
    blog_content: str = ""
    blog_meta_description: str = ""
    generated_at: datetime = field(default_factory=datetime.now)
    model_used: str = "claude-3-7-sonnet-20250219"
    citations: List[str] = field(default_factory=list)

    def word_count(self, platform: str) -> int:
        """Return word count for specified platform content."""
        if platform == "linkedin":
            return len(self.linkedin_post.split())
        elif platform == "blog":
            return len(self.blog_content.split())
        elif platform == "bluesky":
            return sum(len(post.split()) for post in self.bluesky_posts)
        return 0

    def char_count(self, platform: str) -> int:
        """Return character count for specified platform content."""
        if platform == "linkedin":
            return len(self.linkedin_post)
        elif platform == "blog":
            return len(self.blog_content)
        elif platform == "bluesky":
            return sum(len(post) for post in self.bluesky_posts)
        return 0


@dataclass
class WeeklySocialContent:
    """Container for all weekly social content."""

    posts: List[SocialPost] = field(default_factory=list)
    generated_at: datetime = field(default_factory=datetime.now)
    week_start: Optional[str] = None
    week_end: Optional[str] = None
    total_articles_analyzed: int = 0
    total_community_posts: int = 0

    def add_post(self, post: SocialPost) -> None:
        """Add a social post to the collection."""
        self.posts.append(post)

    def get_post_by_id(self, post_id: str) -> Optional[SocialPost]:
        """Find a post by its ID."""
        for post in self.posts:
            if post.id == post_id:
                return post
        return None
