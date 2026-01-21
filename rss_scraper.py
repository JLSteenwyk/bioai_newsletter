import feedparser
import requests
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import json
import time
from urllib.parse import urlparse
import re

from bio_ai_topic_filter import TopicMatch, analyze_text_for_bio_ai

class RSSNewsScraper:
    def __init__(self):
        self.respected_sources = {
            # Biology + AI Specialized Sources
            'Nature Biotechnology': 'https://www.nature.com/nbt.rss',
            'Nature Methods': 'https://www.nature.com/nmeth.rss',
            'Nature Computational Science': 'https://www.nature.com/natcomputsci.rss',
            'Science Magazine': 'https://www.science.org/rss/news_current.xml',
            'Cell Press': 'https://www.cell.com/action/showFeed?type=etoc&feed=rss&jc=cell',
            'Bioinformatics Journal': 'https://academic.oup.com/rss/site_5293/3017.xml',
            'PLOS Computational Biology': 'https://journals.plos.org/ploscompbiol/feed/atom',
            'bioRxiv Bioinformatics': 'https://connect.biorxiv.org/biorxiv_xml.php?subject=bioinformatics',
            'Genome Biology': 'https://genomebiology.biomedcentral.com/articles/most-recent/rss.xml',
            'Broad Institute News': 'https://www.broadinstitute.org/news/rss.xml',

            # Core AI Research & Labs
            'Anthropic Research': 'https://www.anthropic.com/blog/rss.xml',
            'Google DeepMind': 'https://deepmind.com/blog/feed/basic/',
            'OpenAI': 'https://openai.com/blog/rss/',
            'Meta AI': 'https://ai.facebook.com/blog/feed/',
            'Stability AI': 'https://stability.ai/blog.rss',
            'NVIDIA Technical Blog (Research)': 'https://blogs.nvidia.com/blog/category/research/feed/',
            'Stability AI Research': 'https://stability.ai/research.rss',
            'Thinking Machines': 'https://thinkingmachin.es/feed.xml',

            # Academic + Industry Crossovers
            'MIT AI News': 'https://news.mit.edu/rss/feed',
            'MIT Technology Review': 'https://www.technologyreview.com/feed/',
            'Allen Institute for AI': 'https://allenai.org/rss.xml',
            'Stanford HAI': 'https://hai.stanford.edu/news/feed',
            'Nature Machine Intelligence': 'https://www.nature.com/subjects/machine-learning.rss',

            # ArXiv & Preprint Feeds
            'ArXiv AI': 'https://rss.arxiv.org/rss/cs.AI',
            'ArXiv Machine Learning': 'https://rss.arxiv.org/rss/cs.LG',
            'ArXiv Quantitative Biology': 'https://rss.arxiv.org/rss/q-bio',
            'ArXiv Robotics': 'https://rss.arxiv.org/rss/cs.RO',

            # Computational Biology News
            'ScienceDaily Comp Bio': 'https://www.sciencedaily.com/rss/computers_math/computational_biology.xml',
            'GenomeWeb': 'https://www.genomeweb.com/rss.xml',
            'NIH News': 'https://www.nih.gov/news-events/news-releases/rss.xml',

            # Tech/AI with Biology Focus
            'MarkTechPost': 'https://www.marktechpost.com/feed/',
            'Towards Data Science': 'https://towardsdatascience.com/feed'
        }
        
    def clean_text(self, text: str) -> str:
        """Clean HTML tags and normalize text"""
        if not text:
            return ""
        # Remove HTML tags
        clean = re.sub('<.*?>', '', text)
        # Normalize whitespace
        clean = re.sub(r'\s+', ' ', clean)
        return clean.strip()
    
    def extract_keywords(self, text: str) -> TopicMatch:
        """Return Bio+AI keyword matches for downstream filtering."""
        return analyze_text_for_bio_ai(text)
    
    def fetch_feed(self, source_name: str, feed_url: str, days_back: int = 7) -> List[Dict]:
        """Fetch articles from a single RSS feed"""
        try:
            print(f"Fetching {source_name}...")
            
            # Set user agent to avoid blocks
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            }
            
            response = requests.get(feed_url, headers=headers, timeout=10)
            feed = feedparser.parse(response.content)
            
            articles = []
            cutoff_date = datetime.now() - timedelta(days=days_back)
            
            for entry in feed.entries[:20]:  # Limit to latest 20 entries per source
                # Parse publication date
                pub_date = None
                if hasattr(entry, 'published_parsed') and entry.published_parsed:
                    pub_date = datetime(*entry.published_parsed[:6])
                elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                    pub_date = datetime(*entry.updated_parsed[:6])
                
                # Skip old articles
                if pub_date and pub_date < cutoff_date:
                    continue
                
                title = self.clean_text(entry.get('title', ''))
                summary = self.clean_text(entry.get('summary', ''))
                
                # Extract keywords and ensure the story sits at the Bio+AI intersection
                keyword_match = self.extract_keywords(f"{title} {summary}")
                if not keyword_match.is_bio_ai:
                    continue

                article = {
                    'source': source_name,
                    'title': title,
                    'link': entry.get('link', ''),
                    'summary': summary[:500] + '...' if len(summary) > 500 else summary,
                    'published': pub_date.isoformat() if pub_date else None,
                    'keywords': keyword_match.keywords,
                    'type': 'respected'
                }
                
                if title:  # Only add articles with titles
                    articles.append(article)
            
            print(f"✓ {source_name}: {len(articles)} articles")
            return articles
            
        except Exception as e:
            print(f"✗ Error fetching {source_name}: {str(e)}")
            return []
    
    def scrape_all_sources(self, days_back: int = 7) -> List[Dict]:
        """Scrape all respected sources"""
        all_articles = []
        
        print(f"Scraping respected AI sources from last {days_back} days...\n")
        
        for source_name, feed_url in self.respected_sources.items():
            articles = self.fetch_feed(source_name, feed_url, days_back)
            all_articles.extend(articles)
            time.sleep(1)  # Be polite to servers
        
        # Sort by publication date (newest first)
        all_articles.sort(key=lambda x: x['published'] or '', reverse=True)
        
        print(f"\n📊 Total respected source articles: {len(all_articles)}")
        return all_articles
    
    def save_articles(self, articles: List[Dict], filename: str = None) -> str:
        """Save articles to JSON file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"rss_articles_{timestamp}.json"
        
        output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
        filepath = os.path.join(output_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(articles, f, indent=2, ensure_ascii=False)
        
        print(f"Articles saved to {filepath}")
        return filepath

if __name__ == "__main__":
    scraper = RSSNewsScraper()
    articles = scraper.scrape_all_sources(days_back=7)
    scraper.save_articles(articles)
