import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import os
from pathlib import Path
from rss_scraper import RSSNewsScraper
from reddit_scraper import RedditScraper
from community_scraper import CommunityAggregator
from trend_analyzer import TrendAnalyzer
from summarizer import AISummarizer
from bluesky_generator import BlueskyPostGenerator
from social_content_generator import SocialContentGenerator
from html_generator import HTMLGenerator

class NewsletterGenerator:
    def __init__(self, anthropic_api_key: str = None):
        self.rss_scraper = RSSNewsScraper()
        self.reddit_scraper = RedditScraper()
        self.community_aggregator = CommunityAggregator()
        self.trend_analyzer = TrendAnalyzer()
        self.summarizer = AISummarizer(anthropic_api_key)
        self.bluesky_generator = BlueskyPostGenerator(self.summarizer)
        self.social_content_generator = SocialContentGenerator(self.summarizer)
        self.html_generator = HTMLGenerator()
        
    def collect_all_data(self, days_back: int = 7) -> tuple:
        """Collect data from all sources"""
        print("🔄 Starting data collection for newsletter...\n")
        
        # Scrape RSS feeds
        rss_articles = self.rss_scraper.scrape_all_sources(days_back)
        
        # Scrape Reddit
        reddit_posts = self.reddit_scraper.scrape_all_subreddits('week')

        # Layer additional community signals (Hacker News, Techmeme, etc.)
        additional_posts = self.community_aggregator.gather(days_back)
        community_posts = reddit_posts + additional_posts
        
        # Combine and analyze trends
        all_content = rss_articles + community_posts
        trend_report = self.trend_analyzer.generate_trend_report(all_content)
        
        return rss_articles, community_posts, trend_report
    
    def select_top_stories(self, articles: List[Dict], max_stories: int = 5) -> List[Dict]:
        """Select the most important stories from respected sources"""
        # Score articles based on recency, source credibility, and keywords
        scored_articles = []
        
        for article in articles:
            score = 0
            
            # Recency bonus (newer = higher score)
            if article.get('published'):
                try:
                    pub_date = datetime.fromisoformat(article['published'].replace('Z', '+00:00'))
                    days_old = (datetime.now() - pub_date.replace(tzinfo=None)).days
                    score += max(7 - days_old, 0)  # Up to 7 points for recency
                except:
                    score += 1  # Minimal score if date parsing fails
            
            # Source credibility (some sources weighted higher)
            premium_sources = ['Nature Computational Biology', 'Science Magazine', 'Cell Press', 'MIT AI News', 'PLOS Computational Biology']
            if article.get('source') in premium_sources:
                score += 3
            
            # Keyword relevance
            keywords = article.get('keywords', [])
            high_value_keywords = ['protein folding', 'drug discovery', 'alphafold', 'crispr', 'genomics', 'breakthrough', 'research', 'clinical']
            score += len([k for k in keywords if k in high_value_keywords]) * 2
            
            scored_articles.append((score, article))
        
        # Sort by score and return top stories
        scored_articles.sort(key=lambda x: x[0], reverse=True)
        return [article for _, article in scored_articles[:max_stories]]
    
    def select_community_highlights(self, posts: List[Dict], max_posts: int = 5) -> List[Dict]:
        """Select the most engaging community posts"""
        # Filter and score posts
        scored_posts = []
        
        for post in posts:
            score = post.get('score', 0) + (post.get('num_comments', 0) * 2)
            
            # Bonus for positive sentiment
            if post.get('sentiment') == 'very_positive':
                score *= 1.5
            elif post.get('sentiment') == 'positive':
                score *= 1.2
            
            # Bonus for multiple keywords (broader relevance)
            keywords = post.get('keywords', [])
            if len(keywords) >= 3:
                score *= 1.3
            
            scored_posts.append((score, post))
        
        # Sort by score and return top posts
        scored_posts.sort(key=lambda x: x[0], reverse=True)
        return [post for _, post in scored_posts[:max_posts]]
    
    def generate_top_three_summary(self, top_stories: List[Dict], community_highlights: List[Dict], top_trends: List[Dict]) -> str:
        """Generate a brief bullet point summary of the top three overall stories"""
        # Take the first item from each category for the top 3
        top_three = []

        if top_stories:
            top_three.append({
                'title': top_stories[0].get('title', 'Untitled'),
                'type': 'Research',
                'link': top_stories[0].get('link', '#')
            })

        if community_highlights:
            top_three.append({
                'title': community_highlights[0].get('title', 'Untitled'),
                'type': 'Community',
                'link': community_highlights[0].get('url') or community_highlights[0].get('link', '#')
            })

        if top_trends:
            top_three.append({
                'title': top_trends[0].get('keyword', 'Trending Topic'),
                'type': 'Trending',
                'link': None
            })

        # Generate HTML for top three summary
        summary_html = ""
        for item in top_three[:3]:
            if item.get('link'):
                summary_html += f"• <strong>{item['type']}:</strong> <a href=\"{item['link']}\" target=\"_blank\">{item['title']}</a><br>\n"
            else:
                summary_html += f"• <strong>{item['type']}:</strong> {item['title']}<br>\n"

        return summary_html

    def generate_html_newsletter(self, articles: List[Dict], posts: List[Dict], trend_report: Dict) -> str:
        """Generate HTML newsletter"""
        
        # Get current date for header
        current_date = datetime.now().strftime("%B %d, %Y")
        week_start = (datetime.now() - timedelta(days=7)).strftime("%B %d")
        date_range = f"{week_start} - {datetime.now().strftime('%B %d, %Y')}"
        
        trends = (trend_report or {}).get('trending_topics', [])
        overview_summary = (trend_report or {}).get('overview_summary')
        # Select top content
        top_stories = self.select_top_stories(articles, 3)
        community_highlights = self.select_community_highlights(posts, 3)
        top_trends = trends[:3]
        
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>BioAI Weekly: Research & Community - {current_date}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 700px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f8f9fa;
        }}
        .newsletter-container {{
            background: white;
            padding: 40px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .header {{
            text-align: center;
            border-bottom: 3px solid #007acc;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }}
        .newsletter-title {{
            font-size: 2.5em;
            font-weight: bold;
            color: #007acc;
            margin: 0;
        }}
        .newsletter-subtitle {{
            font-size: 1.1em;
            color: #666;
            margin: 5px 0 0 0;
        }}
        .date {{
            color: #888;
            font-size: 0.9em;
            margin-top: 10px;
        }}
        .overview-intro {{
            margin: 25px 0;
            padding: 18px 20px;
            background: #eef6ff;
            border-left: 4px solid #007acc;
            border-radius: 6px;
            font-size: 1.05em;
        }}
        .section {{
            margin: 40px 0;
        }}
        .section-title {{
            font-size: 1.8em;
            font-weight: bold;
            margin-bottom: 15px;
            color: #2c3e50;
        }}
        .section-intro {{
            font-style: italic;
            color: #555;
            margin-bottom: 25px;
            font-size: 1.05em;
        }}
        .story {{
            margin-bottom: 30px;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 6px;
            border-left: 4px solid #007acc;
        }}
        .story-title {{
            font-size: 1.3em;
            font-weight: bold;
            margin-bottom: 8px;
            color: #2c3e50;
        }}
        .story-title a {{
            color: #2c3e50;
            text-decoration: none;
        }}
        .story-title a:hover {{
            color: #007acc;
        }}
        .story-source {{
            font-size: 0.85em;
            color: #007acc;
            font-weight: 500;
            margin-bottom: 10px;
        }}
        .story-content {{
            font-size: 1em;
            line-height: 1.7;
        }}
        .trend-item {{
            margin-bottom: 20px;
            padding: 15px;
            background: #fff3cd;
            border-radius: 6px;
            border-left: 4px solid #ffc107;
        }}
        .trend-keyword {{
            font-weight: bold;
            color: #856404;
            font-size: 1.1em;
        }}
        .trend-details {{
            font-size: 0.9em;
            color: #666;
            margin-top: 5px;
        }}
        .community-post {{
            margin-bottom: 25px;
            padding: 18px;
            background: #e8f5e8;
            border-radius: 6px;
            border-left: 4px solid #28a745;
        }}
        .post-title {{
            font-size: 1.2em;
            font-weight: bold;
            margin-bottom: 8px;
            color: #2c3e50;
        }}
        .post-title a {{
            color: #2c3e50;
            text-decoration: none;
        }}
        .post-title a:hover {{
            color: #28a745;
        }}
        .post-meta {{
            font-size: 0.85em;
            color: #28a745;
            margin-bottom: 10px;
        }}
        .footer {{
            margin-top: 50px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
            text-align: center;
            color: #888;
            font-size: 0.9em;
        }}
        .citations {{
            margin-top: 15px;
            font-size: 0.85em;
            color: #666;
            border-top: 1px solid #eee;
            padding-top: 10px;
            background: #f9f9f9;
            border-radius: 4px;
            padding: 10px;
        }}
        .citations strong {{
            color: #444;
            font-size: 0.9em;
        }}
        .citations a {{
            color: #007acc;
            text-decoration: none;
        }}
        .citations a:hover {{
            text-decoration: underline;
        }}
        .stats {{
            background: #e9ecef;
            padding: 15px;
            border-radius: 6px;
            margin: 20px 0;
            text-align: center;
        }}
        .top-three {{
            margin: 25px 0;
            padding: 20px;
            background: #fff8e1;
            border-left: 4px solid #ff9800;
            border-radius: 6px;
            font-size: 1.05em;
        }}
        .top-three h3 {{
            margin: 0 0 15px 0;
            color: #e65100;
            font-size: 1.3em;
        }}
        .top-three a {{
            color: #007acc;
            text-decoration: none;
        }}
        .top-three a:hover {{
            text-decoration: underline;
        }}
    </style>
</head>
<body>
    <div class="newsletter-container">
        <div class="header">
            <h1 class="newsletter-title">BioAI Weekly</h1>
            <p class="newsletter-subtitle">AI for Biology Research & Community</p>
            <p class="date">{date_range}</p>
        </div>

        <div class="stats">
            📊 This week: {len(articles)} articles analyzed • {len(posts)} community posts • {len(trends)} trending topics
        </div>
"""

        # Generate and add top three summary
        top_three_summary_html = self.generate_top_three_summary(top_stories, community_highlights, top_trends)
        if top_three_summary_html:
            html += f"""
        <div class="top-three">
            <h3>⭐ Top Three Stories This Week</h3>
            {top_three_summary_html}
        </div>
"""

        if overview_summary:
            html += f"""
        <div class="overview-intro">
            {overview_summary}
        </div>
"""

        # The Signal Section
        if top_stories:
            signal_intro = self.summarizer.generate_section_intro("The Signal", len(top_stories))
            html += f"""
        <div class="section">
            <h2 class="section-title">🔬 Research Frontiers</h2>
            <p class="section-intro">{signal_intro}</p>
"""
            
            for story in top_stories:
                title = story.get('title', 'Untitled')
                source = story.get('source', 'Unknown Source')
                link = story.get('link', '#')
                
                # Generate AI summary
                summary, _ = self.summarizer.summarize_individual_story(story, context="respected")
                
                html += f"""
            <div class="story">
                <div class="story-source">{source}</div>
                <h3 class="story-title"><a href="{link}" target="_blank">{title}</a></h3>
                <div class="story-content">{summary}</div>
            </div>
"""
            html += "        </div>"

        # The Noise Section
        if community_highlights:
            noise_intro = self.summarizer.generate_section_intro("The Noise", len(community_highlights))
            html += f"""
        <div class="section">
            <h2 class="section-title">🧬 Community Insights</h2>
            <p class="section-intro">{noise_intro}</p>
"""
            
            for post in community_highlights:
                title = post.get('title', 'Untitled')
                subreddit = post.get('subreddit') or post.get('source', 'Community')
                url = post.get('url') or post.get('link', '#')
                score = post.get('score', 0)
                comments = post.get('num_comments', 0)
                
                # Generate community-focused summary
                summary, _ = self.summarizer.summarize_individual_story(post, context="community")
                
                html += f"""
            <div class="community-post">
                <div class="post-meta">{subreddit} • {score} upvotes • {comments} comments</div>
                <h3 class="post-title"><a href="{url}" target="_blank">{title}</a></h3>
                <div class="story-content">{summary}</div>
            </div>
"""
            html += "        </div>"

        # Trending This Week Section
        if top_trends:
            trending_intro = self.summarizer.generate_section_intro("Trending This Week", len(top_trends))
            html += f"""
        <div class="section">
            <h2 class="section-title">📈 Trending This Week</h2>
            <p class="section-intro">{trending_intro}</p>
"""
            
            for trend in top_trends:
                keyword = trend.get('keyword', '')
                mentions = trend.get('mentions', 0)
                sentiment = trend.get('community_sentiment', 'neutral')
                respected_count = len(trend.get('respected_sources', []))
                community_count = len(trend.get('community_posts', []))
                
                # Create trend summary with citations
                trend_articles = trend.get('respected_sources', []) + trend.get('community_posts', [])
                trend_summary, citations, qa_flags = self.summarizer.summarize_topic_cluster(keyword, trend_articles, style='professional')
                if qa_flags:
                    print(f"⚠️  QA review suggested for trend '{keyword}': {', '.join(qa_flags)}")

                sentiment_emoji = {
                    'very_positive': '😍',
                    'positive': '😊',
                    'neutral': '😐',
                    'negative': '😕'
                }.get(sentiment, '😐')
                
                # Format citations for HTML
                citations_html = ""
                if citations:
                    citations_html = "<div class='citations'>"
                    citations_html += "<strong>Sources:</strong><br>"
                    for citation in citations:
                        # Parse citation to make link clickable
                        if " - http" in citation:
                            parts = citation.split(" - http")
                            text_part = parts[0]
                            url_part = "http" + parts[1]
                            citations_html += f"{text_part} - <a href='{url_part}' target='_blank'>Link</a><br>"
                        else:
                            citations_html += f"{citation}<br>"
                    citations_html += "</div>"

                html += f"""
            <div class="trend-item">
                <div class="trend-keyword">#{keyword.replace(' ', '').title()}</div>
                <div class="trend-details">{mentions} mentions • {respected_count} news sources • {community_count} community posts • Community sentiment: {sentiment_emoji}</div>
                <div class="story-content" style="margin-top: 10px;">{trend_summary}</div>
                {citations_html}
            </div>
"""
            html += "        </div>"

        # Footer
        html += f"""
        <div class="footer">
            <p>Generated on {current_date}</p>
            <p>This newsletter aggregates AI news from trusted sources and community discussions.<br>
            Data sources include MIT, Stanford, OpenAI, Google AI, Reddit communities, and more.<br>
            All summaries include citations and source links for verification.</p>
        </div>
    </div>
</body>
</html>"""

        return html
    
    def save_newsletter(self, html_content: str, filename: str = None) -> str:
        """Save newsletter HTML to file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d")
            filename = f"ai_weekly_{timestamp}.html"

        # Use output directory in project folder
        output_dir = Path(__file__).parent / "output"
        output_dir.mkdir(exist_ok=True)
        filepath = output_dir / filename

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)

        print(f"📧 Newsletter saved to {filepath}")
        return str(filepath)
    
    def generate_weekly_newsletter(self, days_back: int = 7, generate_social: bool = True) -> tuple[str, str, str]:
        """Generate complete weekly newsletter, Bluesky thread, and unified social content.

        Args:
            days_back: Number of days of content to analyze
            generate_social: Whether to generate social media content

        Returns:
            Tuple of (newsletter_path, bluesky_path, social_content_path)
        """
        print("🚀 Generating BioAI Weekly Newsletter...\n")

        # Collect all data
        articles, posts, trend_report = self.collect_all_data(days_back)

        # Generate newsletter
        html_content = self.generate_html_newsletter(
            articles,
            posts,
            trend_report
        )

        # Save newsletter
        newsletter_filepath = self.save_newsletter(html_content)

        # Generate social content if requested
        bluesky_filepath = None
        social_filepath = None
        if generate_social:
            # Generate legacy Bluesky thread
            bluesky_filepath = self.bluesky_generator.generate_bluesky_thread(
                articles,
                posts,
                trend_report['trending_topics']
            )

            # Generate unified social content (Bluesky, LinkedIn, Blog)
            trends = trend_report.get('trending_topics', [])
            weekly_content = self.social_content_generator.generate_weekly_content(
                articles=articles,
                community_posts=posts,
                trends=trends,
                max_posts=3
            )
            social_filepath = self.html_generator.generate_html(weekly_content)

        print(f"\n✅ Newsletter generation complete!")
        print(f"📊 Analyzed {len(articles)} articles and {len(posts)} community posts")
        print(f"📄 Newsletter saved to: {newsletter_filepath}")
        if bluesky_filepath:
            print(f"🐦 Bluesky thread saved to: {bluesky_filepath}")
        if social_filepath:
            print(f"📱 Social content saved to: {social_filepath}")

        return newsletter_filepath, bluesky_filepath, social_filepath

if __name__ == "__main__":
    # Initialize newsletter generator
    # Set your Anthropic API key in environment variable or pass directly
    generator = NewsletterGenerator()

    # Generate this week's newsletter
    newsletter_path, bluesky_path, social_path = generator.generate_weekly_newsletter(days_back=7)

    print(f"\n🎉 Open {newsletter_path} in your browser to view the newsletter!")
    if social_path:
        print(f"📱 Open {social_path} for social media content!")
