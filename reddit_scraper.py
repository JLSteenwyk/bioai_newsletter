import requests
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import time
import re

from bio_ai_topic_filter import TopicMatch, analyze_text_for_bio_ai

class RedditScraper:
    def __init__(self):
        self.base_url = "https://www.reddit.com"
        self.headers = {
            'User-Agent': 'AI Newsletter Bot 1.0'
        }
        
        self.subreddits = {
            # Biology + AI focused subreddits
            'bioinformatics': {
                'name': 'r/bioinformatics',
                'focus': 'Computational biology and bioinformatics'
            },
            'MachineLearning': {
                'name': 'r/MachineLearning',
                'focus': 'ML research including biology applications'
            },
            'compsci': {
                'name': 'r/compsci',
                'focus': 'Computer science research and applications'
            },
            'biology': {
                'name': 'r/biology',
                'focus': 'General biology discussions and research'
            },
            'computational_biology': {
                'name': 'r/computational_biology',
                'focus': 'Computational approaches to biological problems'
            },
            'genetics': {
                'name': 'r/genetics',
                'focus': 'Genetics research and AI applications'
            },
            'datascience': {
                'name': 'r/datascience',
                'focus': 'Data science methods in biology'
            },
            'labrats': {
                'name': 'r/labrats',
                'focus': 'Laboratory research and methods'
            },
            'AskScience': {
                'name': 'r/AskScience',
                'focus': 'Scientific questions and explanations'
            },
            'artificial': {
                'name': 'r/artificial',
                'focus': 'AI applications including biology'
            }
        }
    
    def clean_text(self, text: str) -> str:
        """Clean and normalize Reddit text"""
        if not text:
            return ""
        
        # Remove Reddit markdown
        text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)  # Bold
        text = re.sub(r'\*(.*?)\*', r'\1', text)      # Italic
        text = re.sub(r'~~(.*?)~~', r'\1', text)      # Strikethrough
        text = re.sub(r'\^(\w+)', r'\1', text)        # Superscript
        
        # Remove URLs but keep the text
        text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
        
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
    
    def extract_keywords(self, text: str) -> TopicMatch:
        """Return Bio+AI keyword matches from Reddit content."""
        return analyze_text_for_bio_ai(text)
    
    def get_sentiment_indicators(self, text: str, score: int) -> str:
        """Determine sentiment from text and score"""
        text_lower = text.lower()
        
        positive_words = ['amazing', 'incredible', 'breakthrough', 'exciting', 'love', 'awesome', 'great']
        negative_words = ['terrible', 'awful', 'concerning', 'worried', 'scary', 'dangerous', 'hate']
        
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        if score > 100 and positive_count > negative_count:
            return 'very_positive'
        elif score > 50 and positive_count >= negative_count:
            return 'positive'
        elif score < -10 or negative_count > positive_count:
            return 'negative'
        else:
            return 'neutral'
    
    def fetch_subreddit_posts(self, subreddit: str, time_filter: str = 'week', limit: int = 25) -> List[Dict]:
        """Fetch top posts from a subreddit"""
        try:
            url = f"{self.base_url}/r/{subreddit}/top.json"
            params = {
                't': time_filter,
                'limit': limit
            }
            
            print(f"Fetching r/{subreddit}...")
            
            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            posts = []
            
            for post_data in data['data']['children']:
                post = post_data['data']
                
                # Skip stickied posts and removed content
                if post.get('stickied') or post.get('removed_by_category'):
                    continue
                
                title = self.clean_text(post.get('title', ''))
                selftext = self.clean_text(post.get('selftext', ''))
                
                # Combine title and text for keyword extraction
                full_text = f"{title} {selftext}"
                keyword_match = self.extract_keywords(full_text)

                # Only include posts that explicitly bridge AI and biology
                if not keyword_match.is_bio_ai:
                    continue

                sentiment = self.get_sentiment_indicators(full_text, post.get('score', 0))

                post_obj = {
                    'subreddit': f"r/{subreddit}",
                    'title': title,
                    'selftext': selftext[:300] + '...' if len(selftext) > 300 else selftext,
                    'url': f"https://reddit.com{post.get('permalink', '')}",
                    'score': post.get('score', 0),
                    'num_comments': post.get('num_comments', 0),
                    'created_utc': datetime.fromtimestamp(post.get('created_utc', 0)).isoformat(),
                    'author': post.get('author', '[deleted]'),
                    'keywords': keyword_match.keywords,
                    'sentiment': sentiment,
                    'type': 'community',
                    'engagement_ratio': post.get('upvote_ratio', 0.5)
                }
                
                posts.append(post_obj)
            
            print(f"✓ r/{subreddit}: {len(posts)} relevant posts")
            return posts
            
        except Exception as e:
            print(f"✗ Error fetching r/{subreddit}: {str(e)}")
            return []
    
    def scrape_all_subreddits(self, time_filter: str = 'week') -> List[Dict]:
        """Scrape all configured subreddits"""
        all_posts = []
        
        print(f"Scraping Reddit communities for {time_filter} timeframe...\n")
        
        for subreddit, info in self.subreddits.items():
            posts = self.fetch_subreddit_posts(subreddit, time_filter)
            all_posts.extend(posts)
            time.sleep(2)  # Be extra polite to Reddit
        
        # Sort by engagement (score + comments)
        all_posts.sort(key=lambda x: x['score'] + x['num_comments'], reverse=True)
        
        print(f"\n🗣️ Total community posts: {len(all_posts)}")
        return all_posts
    
    def save_posts(self, posts: List[Dict], filename: str = None) -> str:
        """Save posts to JSON file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"reddit_posts_{timestamp}.json"
        
        filepath = f"/Users/jacoblsteenwyk/Desktop/BUSINESS/AI_NEWS/{filename}"
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(posts, f, indent=2, ensure_ascii=False)
        
        print(f"Posts saved to {filepath}")
        return filepath

if __name__ == "__main__":
    scraper = RedditScraper()
    posts = scraper.scrape_all_subreddits(time_filter='week')
    scraper.save_posts(posts)
