import json
import os
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from typing import List, Dict, Tuple
import re

class TrendAnalyzer:
    def __init__(self):
        self.min_mentions = 2.5  # Minimum weighted mentions to trend
        self.keyword_weights = {
            'respected': 2.1,    # Slightly prioritize vetted sources
            'community': 1.1     # Community posts still meaningful, especially with engagement boosts
        }
        self.source_weight_overrides = {
            'Hacker News': 1.15,
            'Techmeme': 0.9,
            'Anthropic Research': 1.25,
            'Google DeepMind': 1.2,
            'OpenAI': 1.2,
            'Meta AI': 1.15,
            'Thinking Machines': 1.1,
            'Stability AI': 1.1,
            'Allen Institute for AI': 1.1,
            'Stanford HAI': 1.1,
            'MIT Technology Review': 1.05,
            'MIT AI News': 1.05
        }

    def _format_keyword_list(self, keywords: List[str]) -> str:
        if not keywords:
            return ""
        if len(keywords) == 1:
            return keywords[0]
        if len(keywords) == 2:
            return f"{keywords[0]} and {keywords[1]}"
        return ", ".join(keywords[:-1]) + f", and {keywords[-1]}"

    def _compose_overview_summary(
        self,
        trending_topics: List[Dict],
        total_articles: int,
        total_respected: int,
        total_community: int
    ) -> str:
        if total_articles == 0:
            return "No BioAI articles were captured this period."

        if not trending_topics:
            return (
                f"We reviewed {total_articles} BioAI stories this week "
                f"({total_respected} research sources, {total_community} community posts), "
                "but no themes crossed the trending threshold."
            )

        top_topics = trending_topics[:3]
        keywords = [topic.get('keyword', 'BioAI') for topic in top_topics if topic.get('keyword')]
        primary_themes = self._format_keyword_list(keywords)

        total_mentions = sum(topic.get('mentions', 0) for topic in trending_topics)
        cross_platform = sum(1 for topic in trending_topics if topic.get('cross_platform'))

        sentiment_counts = Counter(
            topic.get('community_sentiment', 'neutral')
            for topic in trending_topics
            if topic.get('community_sentiment')
        )
        sentiment_phrase = ''
        if sentiment_counts:
            dominant, _ = sentiment_counts.most_common(1)[0]
            sentiment_map = {
                'very_positive': 'very positive',
                'positive': 'positive',
                'neutral': 'mixed',
                'negative': 'cautious'
            }
            sentiment_phrase = f" Community discussion skewed {sentiment_map.get(dominant, dominant)}."

        overview = (
            f"This week we reviewed {total_articles} BioAI stories "
            f"({total_respected} from research outlets and {total_community} community updates), "
        )

        if primary_themes:
            overview += f"with momentum centered on {primary_themes}. "
        else:
            overview += "highlighting a diverse mix of topics. "

        overview += (
            f"Trending threads accounted for {total_mentions} mentions overall, "
            f"and {cross_platform} of them spanned both trusted sources and community chatter."
        )

        if sentiment_phrase:
            overview += sentiment_phrase

        return overview

    def normalize_keywords(self, keywords: List[str]) -> List[str]:
        """Normalize and group similar keywords"""
        if not keywords:
            return []
        
        # Biology+AI keyword normalization mappings
        keyword_groups = {
            # Core AI/ML
            'machine learning': ['machine learning', 'ml', 'deep learning'],
            'neural networks': ['neural network', 'neural networks', 'deep neural networks'],
            'transformer': ['transformer', 'attention mechanism', 'attention'],
            'llm': ['llm', 'large language model', 'language model', 'foundation models'],

            # Protein and structural biology
            'protein folding': ['protein folding', 'alphafold', 'protein structure'],
            'structural biology': ['structural biology', 'cryo-em', 'x-ray crystallography'],
            'molecular dynamics': ['molecular dynamics', 'md simulation', 'molecular simulation'],
            'protein design': ['protein design', 'antibody design', 'enzyme design'],

            # Genomics and sequencing
            'genomics': ['genomics', 'genome', 'sequencing', 'dna sequencing'],
            'single-cell': ['single-cell', 'scRNA-seq', 'single cell analysis'],
            'omics': ['omics', 'proteomics', 'transcriptomics', 'metabolomics'],
            'crispr': ['crispr', 'gene editing', 'genome editing'],

            # Drug discovery and medicine
            'drug discovery': ['drug discovery', 'drug development', 'pharmaceutical ai'],
            'precision medicine': ['precision medicine', 'personalized medicine'],
            'clinical ai': ['clinical ai', 'medical ai', 'healthcare ai'],
            'medical imaging': ['medical imaging', 'radiology ai', 'pathology ai'],
            'biomarker discovery': ['biomarker', 'biomarker discovery'],

            # Systems and computational biology
            'bioinformatics': ['bioinformatics', 'computational biology'],
            'systems biology': ['systems biology', 'network biology'],
            'synthetic biology': ['synthetic biology', 'bioengineering'],
            'evolutionary biology': ['evolutionary biology', 'phylogenetics'],

            # Specific applications
            'cancer research': ['cancer research', 'oncology ai', 'tumor analysis'],
            'immunotherapy': ['immunotherapy', 'immune system', 'immunology ai'],
            'vaccine design': ['vaccine design', 'vaccine development'],
            'microbiome': ['microbiome', 'metagenomics', 'gut microbiome'],
            'epidemiology': ['epidemiology', 'public health ai', 'disease modeling'],

            # Emerging AI themes
            'ai safety': ['ai safety', 'alignment', 'responsible ai', 'safe ai'],
            'governance': ['ai governance', 'policy', 'regulation', 'compliance'],
            'generative ai': ['generative ai', 'diffusion model', 'text-to-image', 'video generation', 'image generation'],
            'multimodal': ['multimodal', 'vision-language', 'audio-visual', 'speech-to-text'],
            'robotics': ['robotics', 'autonomous robotics', 'manipulation', 'robot learning'],
            'autonomous agents': ['autonomous agent', 'ai agent', 'agentic', 'workflow automation'],
            'synthetic data': ['synthetic data', 'data generation'],
            'open source ai': ['open source ai', 'open weights', 'model release'],
            'compute': ['compute', 'gpu', 'semiconductor', 'chip design', 'hardware accelerator'],
            'benchmarking': ['benchmark', 'evaluation suite', 'leaderboard'],
            'hallucination': ['hallucination', 'factuality', 'truthful ai'],
            'reasoning': ['reasoning', 'chain-of-thought', 'tool use']
        }
        
        normalized = []
        keywords_lower = [k.lower() for k in keywords]
        
        # Group similar keywords
        used_keywords = set()
        for group_name, variants in keyword_groups.items():
            if any(variant in keywords_lower for variant in variants):
                if group_name not in used_keywords:
                    normalized.append(group_name)
                    used_keywords.add(group_name)
        
        # Add remaining keywords that don't fit groups
        for keyword in keywords_lower:
            if keyword not in used_keywords and not any(keyword in variants for variants in keyword_groups.values()):
                normalized.append(keyword)

        return normalized

    def get_recency_boost(self, article: Dict) -> float:
        """Boost newer items; penalize stale ones."""
        timestamp = article.get('published') or article.get('created_utc')
        if not timestamp:
            return 1.0

        try:
            article_dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        except Exception:
            return 1.0

        age_days = (datetime.now() - article_dt).total_seconds() / 86400

        if age_days < 1:
            return 1.3
        if age_days < 3:
            return 1.15
        if age_days < 7:
            return 1.0
        if age_days < 14:
            return 0.85
        return 0.7

    def get_source_weight(self, article: Dict) -> float:
        """Apply source-specific adjustments for known high-signal feeds."""
        source_name = article.get('source') or article.get('subreddit')
        if not source_name:
            return 1.0
        return self.source_weight_overrides.get(source_name, 1.0)
    
    def calculate_keyword_scores(self, articles: List[Dict]) -> Dict[str, float]:
        """Calculate weighted scores for keywords across all content"""
        keyword_scores = defaultdict(float)
        
        for article in articles:
            keywords = self.normalize_keywords(article.get('keywords', []))
            source_type = article.get('type', 'community')
            weight = self.keyword_weights.get(source_type, 1.0)
            weight *= self.get_source_weight(article)
            weight *= self.get_recency_boost(article)

            # Add engagement boost for community posts
            if source_type == 'community':
                score = article.get('score', 0)
                comments = article.get('num_comments', 0)
                engagement_boost = min((score + comments) / 100, 2.0)  # Cap at 2x boost
                weight *= (1 + engagement_boost)
            
            for keyword in keywords:
                keyword_scores[keyword] += weight
        
        return dict(keyword_scores)
    
    def find_trending_topics(self, articles: List[Dict]) -> List[Dict]:
        """Identify trending topics based on keyword frequency and engagement"""
        keyword_scores = self.calculate_keyword_scores(articles)
        
        # Filter keywords that meet minimum threshold
        trending_keywords = {
            keyword: score 
            for keyword, score in keyword_scores.items() 
            if score >= self.min_mentions
        }
        
        # Sort by score
        sorted_trends = sorted(trending_keywords.items(), key=lambda x: x[1], reverse=True)
        
        trends = []
        for keyword, score in sorted_trends[:10]:  # Top 10 trends
            # Find articles mentioning this keyword
            related_articles = []
            community_sentiment = {'very_positive': 0, 'positive': 0, 'negative': 0, 'neutral': 0}
            
            for article in articles:
                normalized_keywords = self.normalize_keywords(article.get('keywords', []))
                if keyword in normalized_keywords:
                    related_articles.append({
                        'title': article.get('title', ''),
                        'source': article.get('source', article.get('subreddit', '')),
                        'type': article.get('type', 'unknown'),
                        'url': article.get('link', article.get('url', '')),
                        'sentiment': article.get('sentiment', 'neutral')
                    })
                    
                    # Count sentiment for community posts
                    if article.get('type') == 'community':
                        sentiment = article.get('sentiment', 'neutral')
                        if sentiment in community_sentiment:
                            community_sentiment[sentiment] += 1
                        else:
                            community_sentiment['neutral'] += 1
            
            # Determine overall community sentiment
            dominant_sentiment = max(community_sentiment, key=community_sentiment.get)
            
            trend = {
                'keyword': keyword,
                'score': round(score, 2),
                'mentions': len(related_articles),
                'community_sentiment': dominant_sentiment,
                'sentiment_breakdown': community_sentiment,
                'respected_sources': [a for a in related_articles if a['type'] == 'respected'],
                'community_posts': [a for a in related_articles if a['type'] == 'community'],
                'cross_platform': len(set(a['source'] for a in related_articles)) > 1
            }
            
            trends.append(trend)
        
        return trends
    
    def analyze_sentiment_shifts(self, articles: List[Dict]) -> Dict[str, Dict]:
        """Analyze how sentiment around topics has shifted"""
        # Group articles by day
        daily_sentiment = defaultdict(lambda: defaultdict(list))
        
        for article in articles:
            if article.get('type') != 'community':
                continue
                
            # Parse date
            published = article.get('created_utc', article.get('published'))
            if not published:
                continue
                
            try:
                date = datetime.fromisoformat(published.replace('Z', '+00:00')).date()
            except:
                continue
            
            keywords = self.normalize_keywords(article.get('keywords', []))
            sentiment = article.get('sentiment', 'neutral')
            
            for keyword in keywords:
                daily_sentiment[keyword][date].append(sentiment)
        
        # Calculate sentiment trends
        sentiment_analysis = {}
        for keyword, dates in daily_sentiment.items():
            if len(dates) < 2:  # Need at least 2 days of data
                continue
                
            # Calculate average sentiment per day
            daily_scores = {}
            for date, sentiments in dates.items():
                score = sum(1 if s == 'positive' else -1 if s == 'negative' else 0 for s in sentiments)
                daily_scores[date] = score / len(sentiments) if sentiments else 0
            
            # Determine trend
            dates_sorted = sorted(daily_scores.keys())
            if len(dates_sorted) >= 2:
                recent_avg = sum(daily_scores[d] for d in dates_sorted[-2:]) / 2
                early_avg = sum(daily_scores[d] for d in dates_sorted[:2]) / 2
                
                if recent_avg > early_avg + 0.2:
                    trend = 'improving'
                elif recent_avg < early_avg - 0.2:
                    trend = 'declining'
                else:
                    trend = 'stable'
                
                sentiment_analysis[keyword] = {
                    'trend': trend,
                    'recent_sentiment': recent_avg,
                    'change': recent_avg - early_avg,
                    'daily_data': daily_scores
                }
        
        return sentiment_analysis
    
    def generate_trend_report(self, articles: List[Dict]) -> Dict:
        """Generate comprehensive trend analysis report"""
        trending_topics = self.find_trending_topics(articles)
        sentiment_shifts = self.analyze_sentiment_shifts(articles)
        
        # Calculate overall statistics
        total_respected = len([a for a in articles if a.get('type') == 'respected'])
        total_community = len([a for a in articles if a.get('type') == 'community'])
        
        # Find cross-platform stories (appearing in both respected and community)
        cross_platform_topics = [t for t in trending_topics if t['cross_platform']]
        
        report = {
            'generated_at': datetime.now().isoformat(),
            'data_summary': {
                'total_articles': len(articles),
                'respected_sources': total_respected,
                'community_posts': total_community,
                'trending_topics_found': len(trending_topics)
            },
            'trending_topics': trending_topics,
            'sentiment_analysis': sentiment_shifts,
            'cross_platform_stories': cross_platform_topics,
            'top_keywords': [t['keyword'] for t in trending_topics[:5]]
        }

        report['overview_summary'] = self._compose_overview_summary(
            trending_topics,
            report['data_summary']['total_articles'],
            total_respected,
            total_community
        )

        return report
    
    def save_report(self, report: Dict, filename: str = None) -> str:
        """Save trend analysis report"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"trend_report_{timestamp}.json"
        
        output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
        filepath = os.path.join(output_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"Trend report saved to {filepath}")
        return filepath

def load_articles(rss_file: str, reddit_file: str) -> List[Dict]:
    """Load and combine articles from both sources"""
    articles = []
    
    try:
        with open(rss_file, 'r', encoding='utf-8') as f:
            rss_articles = json.load(f)
            articles.extend(rss_articles)
    except FileNotFoundError:
        print(f"RSS file not found: {rss_file}")
    
    try:
        with open(reddit_file, 'r', encoding='utf-8') as f:
            reddit_posts = json.load(f)
            articles.extend(reddit_posts)
    except FileNotFoundError:
        print(f"Reddit file not found: {reddit_file}")
    
    return articles

if __name__ == "__main__":
    # Example usage - you'll need to run the scrapers first
    analyzer = TrendAnalyzer()
    
    # Load data (replace with actual file paths)
    # articles = load_articles('rss_articles_latest.json', 'reddit_posts_latest.json')
    # report = analyzer.generate_trend_report(articles)
    # analyzer.save_report(report)
    
    print("Trend analyzer ready. Run RSS and Reddit scrapers first, then use load_articles() and generate_trend_report()")
