import requests
import feedparser
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import re

from bio_ai_topic_filter import TopicMatch, analyze_text_for_bio_ai

class CommunityAggregator:
    """Aggregate AI community chatter beyond Reddit."""

    def __init__(self):
        self.hacker_news_endpoint = "https://hn.algolia.com/api/v1/search_by_date"
        self.techmeme_feed = "https://www.techmeme.com/feed.xml"
        self.positive_words = ['amazing', 'incredible', 'breakthrough', 'exciting', 'love', 'awesome', 'great']
        self.negative_words = ['terrible', 'awful', 'concerning', 'worried', 'scary', 'dangerous', 'hate']

    def clean_text(self, text: Optional[str]) -> str:
        if not text:
            return ""
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    def extract_keywords(self, text: str) -> TopicMatch:
        return analyze_text_for_bio_ai(text)

    def get_sentiment_indicators(self, text: str, score: int) -> str:
        text_lower = text.lower()
        positive_count = sum(1 for word in self.positive_words if word in text_lower)
        negative_count = sum(1 for word in self.negative_words if word in text_lower)

        if score > 150 and positive_count >= negative_count:
            return 'very_positive'
        if score > 60 and positive_count >= negative_count:
            return 'positive'
        if score < 0 or negative_count > positive_count:
            return 'negative'
        return 'neutral'

    def fetch_hacker_news(self, days_back: int = 7, max_hits: int = 40) -> List[Dict]:
        """Fetch relevant Hacker News stories within the window."""
        cutoff = int((datetime.utcnow() - timedelta(days=days_back)).timestamp())
        params = {
            'tags': 'story',
            'numericFilters': f'created_at_i>{cutoff}',
            'query': 'AI OR "artificial intelligence" OR "machine learning"',
            'hitsPerPage': max_hits,
            'page': 0
        }

        try:
            response = requests.get(self.hacker_news_endpoint, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
        except Exception as exc:
            print(f"✗ Error fetching Hacker News: {exc}")
            return []

        stories = []
        for hit in data.get('hits', []):
            title = self.clean_text(hit.get('title'))
            url = hit.get('url') or f"https://news.ycombinator.com/item?id={hit.get('objectID')}"
            story_text = self.clean_text(hit.get('story_text'))
            combined_text = f"{title} {story_text}".strip()
            keyword_match = self.extract_keywords(combined_text)

            if not keyword_match.is_bio_ai:
                continue

            created_at = hit.get('created_at') or ''
            try:
                created_iso = datetime.fromisoformat(created_at.replace('Z', '+00:00')).isoformat()
            except Exception:
                created_iso = created_at

            score = hit.get('points', 0) or 0
            comments = hit.get('num_comments', 0) or 0

            sentiment = self.get_sentiment_indicators(combined_text, score)

            stories.append({
                'source': 'Hacker News',
                'subreddit': 'Hacker News',
                'title': title,
                'selftext': story_text[:300] + '...' if len(story_text) > 300 else story_text,
                'url': url,
                'score': score,
                'num_comments': comments,
                'created_utc': created_iso,
                'author': hit.get('author', 'unknown'),
                'keywords': keyword_match.keywords,
                'sentiment': sentiment,
                'type': 'community',
                'engagement_ratio': 1.0
            })

        print(f"✓ Hacker News: {len(stories)} relevant stories")
        return stories

    def fetch_techmeme(self, days_back: int = 7, limit: int = 30) -> List[Dict]:
        """Parse Techmeme feed and keep AI-focused items."""
        try:
            feed = feedparser.parse(self.techmeme_feed)
        except Exception as exc:
            print(f"✗ Error parsing Techmeme feed: {exc}")
            return []

        cutoff_date = datetime.utcnow() - timedelta(days=days_back)
        posts: List[Dict] = []

        for entry in feed.entries[:limit]:
            title = self.clean_text(entry.get('title', ''))
            summary = self.clean_text(entry.get('summary', ''))
            content = f"{title} {summary}"
            keyword_match = self.extract_keywords(content)

            if not keyword_match.is_bio_ai:
                continue

            published = None
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                published = datetime(*entry.published_parsed[:6])
            elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                published = datetime(*entry.updated_parsed[:6])

            if published and published < cutoff_date:
                continue

            published_iso = published.isoformat() if published else None
            score_proxy = 20  # Techmeme lacks votes; assign a modest weight for trend scoring.

            sentiment = self.get_sentiment_indicators(content, score_proxy)

            posts.append({
                'source': 'Techmeme',
                'subreddit': 'Techmeme',
                'title': title,
                'summary': summary[:300] + '...' if len(summary) > 300 else summary,
                'link': entry.get('link', ''),
                'score': score_proxy,
                'num_comments': 0,
                'created_utc': published_iso,
                'author': entry.get('author', 'Techmeme Editors'),
                'keywords': keyword_match.keywords,
                'sentiment': sentiment,
                'type': 'community',
                'engagement_ratio': 0.6
            })

        print(f"✓ Techmeme: {len(posts)} AI-focused posts")
        return posts

    def gather(self, days_back: int = 7) -> List[Dict]:
        """Collect all community stories beyond Reddit."""
        hacker_news = self.fetch_hacker_news(days_back=days_back)
        techmeme = self.fetch_techmeme(days_back=days_back)
        combined = hacker_news + techmeme
        combined.sort(key=lambda item: item.get('created_utc', ''), reverse=True)
        print(f"\n📰 Additional community signals collected: {len(combined)}")
        return combined


if __name__ == "__main__":
    aggregator = CommunityAggregator()
    stories = aggregator.gather(days_back=7)
    print(f"Fetched {len(stories)} community items")
