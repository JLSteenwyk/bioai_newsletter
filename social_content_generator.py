"""Unified content orchestrator for social platform content generation."""
from __future__ import annotations

import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Sequence

from content_types import SocialPost, WeeklySocialContent
from summarizer import AISummarizer


class SocialContentGenerator:
    """Coordinates content generation across Bluesky, LinkedIn, and Blog platforms."""

    def __init__(self, summarizer: AISummarizer):
        self.summarizer = summarizer

    def generate_weekly_content(
        self,
        articles: Sequence[Dict],
        community_posts: Sequence[Dict],
        trends: Sequence[Dict],
        max_posts: int = 3
    ) -> WeeklySocialContent:
        """Generate social content for all platforms based on weekly data.

        Args:
            articles: Curated articles from respected sources
            community_posts: Community discussion posts
            trends: Trending topics with metadata
            max_posts: Maximum number of social posts to generate

        Returns:
            WeeklySocialContent containing all generated posts
        """
        print("\n📱 Generating social media content...")

        weekly_content = WeeklySocialContent(
            generated_at=datetime.now(),
            week_start=(datetime.now() - timedelta(days=7)).strftime("%B %d"),
            week_end=datetime.now().strftime("%B %d, %Y"),
            total_articles_analyzed=len(articles),
            total_community_posts=len(community_posts)
        )

        # Extract primary topics from trends
        primary_topics = self._extract_primary_topics(trends, max_topics=max_posts)

        if not primary_topics:
            print("  ⚠️  No trending topics found, using top article topics")
            primary_topics = self._extract_topics_from_articles(articles, max_topics=max_posts)

        for topic_data in primary_topics:
            topic = topic_data["keyword"]
            print(f"  📝 Generating content for: {topic}")

            # Get relevant articles for this topic
            topic_articles = self._filter_articles_for_topic(
                topic, articles, community_posts, topic_data
            )

            # Generate social post
            post = self._generate_social_post(
                topic=topic,
                topic_data=topic_data,
                articles=topic_articles["articles"],
                community_posts=topic_articles["community"],
                trends=list(trends)
            )

            weekly_content.add_post(post)

        print(f"  ✅ Generated {len(weekly_content.posts)} social posts")
        return weekly_content

    def _extract_primary_topics(
        self, trends: Sequence[Dict], max_topics: int = 3
    ) -> List[Dict]:
        """Extract the most significant topics from trending data."""
        if not trends:
            return []

        # Sort by mentions and take top N
        sorted_trends = sorted(
            trends,
            key=lambda t: t.get("mentions", 0),
            reverse=True
        )

        return list(sorted_trends[:max_topics])

    def _extract_topics_from_articles(
        self, articles: Sequence[Dict], max_topics: int = 3
    ) -> List[Dict]:
        """Extract topics from articles when no trends are available."""
        if not articles:
            return []

        # Count keyword occurrences across articles
        keyword_counts: Dict[str, int] = {}
        for article in articles:
            keywords = article.get("keywords", [])
            for kw in keywords:
                if kw and len(kw) > 2:
                    keyword_counts[kw] = keyword_counts.get(kw, 0) + 1

        # Sort by count and create topic dicts
        sorted_keywords = sorted(
            keyword_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )

        topics = []
        for keyword, count in sorted_keywords[:max_topics]:
            topics.append({
                "keyword": keyword,
                "mentions": count,
                "respected_sources": [],
                "community_posts": []
            })

        return topics

    def _filter_articles_for_topic(
        self,
        topic: str,
        articles: Sequence[Dict],
        community_posts: Sequence[Dict],
        topic_data: Dict
    ) -> Dict[str, List[Dict]]:
        """Filter articles and posts relevant to a specific topic."""
        topic_lower = topic.lower()

        # Use pre-filtered sources from topic_data if available
        filtered_articles = list(topic_data.get("respected_sources", []))
        filtered_community = list(topic_data.get("community_posts", []))

        # If no pre-filtered data, search manually
        if not filtered_articles:
            for article in articles:
                title = (article.get("title") or "").lower()
                summary = (article.get("summary") or "").lower()
                keywords = [k.lower() for k in article.get("keywords", [])]

                if (topic_lower in title or
                    topic_lower in summary or
                    topic_lower in keywords):
                    filtered_articles.append(article)

        if not filtered_community:
            for post in community_posts:
                title = (post.get("title") or "").lower()
                selftext = (post.get("selftext") or "").lower()

                if topic_lower in title or topic_lower in selftext:
                    filtered_community.append(post)

        # Fallback: use top articles if no matches
        if not filtered_articles and articles:
            filtered_articles = list(articles[:3])

        return {
            "articles": filtered_articles[:5],
            "community": filtered_community[:3]
        }

    def _generate_social_post(
        self,
        topic: str,
        topic_data: Dict,
        articles: List[Dict],
        community_posts: List[Dict],
        trends: List[Dict]
    ) -> SocialPost:
        """Generate a complete SocialPost with content for all platforms."""
        # Generate unique ID
        post_id = self._generate_post_id(topic)

        # Build Bluesky thread
        bluesky_posts = self._build_bluesky_thread(
            topic, topic_data, articles, community_posts
        )

        # Generate LinkedIn post
        linkedin_post = self.summarizer.generate_linkedin_post(
            topic, articles, trends
        )

        # Generate blog post
        blog_title, blog_content, blog_meta = self.summarizer.generate_blog_post(
            topic, articles, community_posts, trends
        )

        # Build citations list
        citations = []
        for i, article in enumerate(articles, 1):
            source = article.get('source', '') or article.get('subreddit', '')
            title = article.get('title', '')
            link = article.get('link', '') or article.get('url', '')
            citations.append(f"[{i}] {source}: {title} - {link}")

        return SocialPost(
            id=post_id,
            title=articles[0].get("title", topic) if articles else topic,
            topic_keyword=topic,
            source_articles=articles,
            bluesky_posts=bluesky_posts,
            linkedin_post=linkedin_post,
            blog_title=blog_title,
            blog_content=blog_content,
            blog_meta_description=blog_meta,
            generated_at=datetime.now(),
            model_used="claude-3-7-sonnet-20250219",
            citations=citations
        )

    def _generate_post_id(self, topic: str) -> str:
        """Generate a unique ID for a social post."""
        timestamp = datetime.now().isoformat()
        hash_input = f"{topic}_{timestamp}"
        return f"post_{hashlib.md5(hash_input.encode()).hexdigest()[:12]}"

    def _build_bluesky_thread(
        self,
        topic: str,
        topic_data: Dict,
        articles: List[Dict],
        community_posts: List[Dict]
    ) -> List[str]:
        """Build a Bluesky thread (3-5 posts) for a topic.

        Each post should be under 300 characters with hashtags.
        """
        posts: List[str] = []
        mentions = topic_data.get("mentions", 0)
        sentiment = topic_data.get("community_sentiment", "neutral")

        # Post 1: Hook/intro
        hashtag = f"#{topic.replace(' ', '')[:20]}"
        if articles:
            title = articles[0].get("title", "")[:100]
            intro = f"{hashtag} 🧬 {title}"
            if len(intro) > 280:
                intro = intro[:277] + "..."
        else:
            intro = f"{hashtag} 🧬 This week's spotlight in BioAI - here's what you need to know:"
        posts.append(intro)

        # Post 2: Key finding/development
        if articles and len(articles) > 0:
            summary = articles[0].get("summary", "")
            if summary:
                # Extract first sentence or truncate
                first_sentence = summary.split(".")[0] + "."
                if len(first_sentence) > 280:
                    first_sentence = first_sentence[:277] + "..."
                posts.append(first_sentence)

        # Post 3: Stats/engagement
        sentiment_map = {
            "very_positive": "strong enthusiasm",
            "positive": "positive reception",
            "neutral": "measured discussion",
            "negative": "skeptical debate"
        }
        sentiment_phrase = sentiment_map.get(sentiment, "active discussion")

        if mentions > 0:
            stats_post = f"📊 {mentions} mentions this week with {sentiment_phrase} across research and community channels."
            if len(stats_post) <= 300:
                posts.append(stats_post)

        # Post 4: Sources (if available)
        sources = []
        for article in articles[:2]:
            source = article.get("source", "")
            if source and source not in sources:
                sources.append(source)

        if sources:
            source_text = f"📚 Coverage from: {', '.join(sources)}"
            if len(source_text) <= 300:
                posts.append(source_text)

        # Post 5: CTA
        today = datetime.now().strftime("%b %d")
        cta = f"Full analysis in BioAI Weekly ({today}). Subscribe for weekly research + community insights. {hashtag}"
        if len(cta) > 300:
            cta = f"Full analysis in BioAI Weekly ({today}). {hashtag}"
        posts.append(cta)

        return posts
