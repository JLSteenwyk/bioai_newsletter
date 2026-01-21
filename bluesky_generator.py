"""Generate Bluesky-ready social copy for BioAI Weekly."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Sequence
import html
import os

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")


@dataclass
class BlueskyPost:
    """Represents a single Bluesky post in the generated thread."""

    text: str

    def to_html(self, idx: int) -> str:
        escaped = html.escape(self.text)
        return (
            f"<div class='post'>"
            f"<div class='post-number'>Post {idx}</div>"
            f"<textarea readonly>{escaped}</textarea>"
            f"<button onclick=\"copyPost({idx})\">Copy</button>"
            f"</div>"
        )


class BlueskyPostGenerator:
    """Create short-form Bluesky threads that recap the weekly newsletter."""

    def __init__(self, summarizer):
        self.summarizer = summarizer

    def generate_bluesky_thread(
        self,
        articles: Sequence[Dict],
        community_posts: Sequence[Dict],
        trends: Sequence[Dict],
        filename: str | None = None
    ) -> str:
        posts = self._build_posts(articles, community_posts, trends)
        html_doc = self._render_html(posts)
        return self._save_html(html_doc, filename)

    # --- Post construction helpers -------------------------------------------------

    def _build_posts(
        self,
        articles: Sequence[Dict],
        community_posts: Sequence[Dict],
        trends: Sequence[Dict]
    ) -> List[BlueskyPost]:
        total_articles = len(articles)
        total_community = len(community_posts)
        top_trends = list(trends[:3])

        posts: List[BlueskyPost] = []

        intro = self._intro_post(total_articles, total_community, top_trends)
        posts.append(BlueskyPost(intro))

        if not top_trends:
            posts.append(
                BlueskyPost(
                    "No single theme dominated the BioAI feeds this week — the newsletter still has the best of the long tail!"
                )
            )
        else:
            for trend in top_trends:
                posts.append(BlueskyPost(self._trend_post(trend)))

        posts.append(BlueskyPost(self._cta_post()))
        return posts

    def _intro_post(
        self,
        total_articles: int,
        total_community: int,
        top_trends: Sequence[Dict]
    ) -> str:
        if total_articles == 0:
            return "Quiet week for BioAI — no qualifying stories met our filters, but we’ll be back with fresh signals soon."

        trend_tags = []
        for trend in top_trends:
            keyword = (trend.get('keyword') or '').strip()
            if not keyword:
                continue
            tag = f"#{keyword.replace(' ', '')[:20]}"
            trend_tags.append(tag)
        tags_text = " " + " ".join(trend_tags) if trend_tags else ""

        return (
            f"BioAI Weekly: sifted {total_articles} research drops + {total_community} community threads to map the frontier.{tags_text}"
        )

    def _trend_post(self, trend: Dict) -> str:
        keyword = trend.get('keyword', 'BioAI')
        mentions = trend.get('mentions', 0)
        community_sentiment = trend.get('community_sentiment', 'neutral')
        sentiment_map = {
            'very_positive': 'very positive energy',
            'positive': 'positive energy',
            'neutral': 'mixed chatter',
            'negative': 'cautious debate'
        }
        sentiment_phrase = sentiment_map.get(community_sentiment, 'mixed chatter')

        respected_sources = [item.get('source') for item in trend.get('respected_sources', []) if item.get('source')]
        community_sources = [item.get('source', item.get('subreddit')) for item in trend.get('community_posts', []) if item.get('source') or item.get('subreddit')]

        def shortlist(sources: List[str]) -> str:
            unique = []
            for src in sources:
                if src and src not in unique:
                    unique.append(src)
            return ", ".join(unique[:2])

        respected_text = shortlist(respected_sources)
        community_text = shortlist(community_sources)

        pieces = [f"{keyword}: {mentions} mentions"]
        if respected_text:
            pieces.append(f"labs: {respected_text}")
        if community_text:
            pieces.append(f"community: {community_text}")
        pieces.append(sentiment_phrase)

        summary = " • ".join(pieces)
        hashtag = f"#{keyword.replace(' ', '')[:20]}"
        return f"{hashtag} watch → {summary}"

    def _cta_post(self) -> str:
        today = datetime.now().strftime("%b %d")
        return (
            f"Full breakdown, citations, and longform takeaways in this week’s BioAI Weekly ({today}). Subscribe + share if it helps your lab."
        )

    # --- HTML rendering ------------------------------------------------------------

    def _render_html(self, posts: Sequence[BlueskyPost]) -> str:
        posts_html = "\n".join(post.to_html(idx + 1) for idx, post in enumerate(posts))
        generated = datetime.now().strftime("%B %d, %Y")

        return f"""<!DOCTYPE html>
<html lang=\"en\">
<head>
    <meta charset=\"UTF-8\" />
    <title>Bluesky Thread - BioAI Weekly</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f4f6f8;
            margin: 0;
            padding: 20px;
        }}
        .container {{
            max-width: 700px;
            margin: 0 auto;
            background: #ffffff;
            border-radius: 8px;
            box-shadow: 0 2px 12px rgba(0,0,0,0.08);
            padding: 30px;
        }}
        h1 {{
            margin-top: 0;
            font-size: 1.8em;
            color: #0077ff;
        }}
        .meta {{
            color: #666;
            margin-bottom: 25px;
        }}
        .post {{
            margin-bottom: 25px;
            position: relative;
        }}
        .post-number {{
            font-weight: 600;
            margin-bottom: 6px;
            color: #333;
        }}
        textarea {{
            width: 100%;
            min-height: 110px;
            resize: vertical;
            padding: 12px;
            border-radius: 6px;
            border: 1px solid #d0d7de;
            font-size: 0.95em;
            line-height: 1.5;
        }}
        button {{
            margin-top: 8px;
            padding: 8px 16px;
            background-color: #0077ff;
            color: #fff;
            border: none;
            border-radius: 4px;
            cursor: pointer;
        }}
        button:hover {{
            background-color: #005ec2;
        }}
    </style>
</head>
<body>
    <div class=\"container\">
        <h1>BioAI Weekly • Bluesky Thread</h1>
        <div class=\"meta\">Generated on {generated}</div>
        {posts_html}
    </div>
    <script>
        function copyPost(idx) {{
            const textarea = document.querySelectorAll('textarea')[idx - 1];
            textarea.select();
            textarea.setSelectionRange(0, 99999);
            document.execCommand('copy');
        }}
    </script>
</body>
</html>
"""

    def _save_html(self, html_doc: str, filename: str | None) -> str:
        if not filename:
            filename = f"bluesky_thread_{datetime.now().strftime('%Y%m%d')}.html"
        filepath = f"{OUTPUT_DIR}/{filename}"
        with open(filepath, 'w', encoding='utf-8') as handle:
            handle.write(html_doc)
        print(f"🐦 Bluesky thread saved to {filepath}")
        return filepath
