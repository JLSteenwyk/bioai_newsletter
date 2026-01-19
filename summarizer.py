import json
import anthropic
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import os
import re

class AISummarizer:
    def __init__(self, api_key: str = None):
        """Initialize with Anthropic API key. Set ANTHROPIC_API_KEY environment variable or pass directly."""
        self.api_key = api_key or os.getenv('ANTHROPIC_API_KEY')
        if not self.api_key:
            print("⚠️  No Anthropic API key found. Set ANTHROPIC_API_KEY environment variable.")
            print("   AI summarization will be disabled. Using fallback summaries.")
            self.api_enabled = False
            self.client = None
        else:
            self.client = anthropic.Anthropic(api_key=self.api_key)
            self.api_enabled = True
            print("✅ Claude AI summarization enabled")
    
    def clean_text_for_summary(self, text: str) -> str:
        """Clean text for better summarization"""
        if not text:
            return ""
        
        # Remove excessive newlines and spaces
        text = re.sub(r'\n+', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        
        # Remove common web artifacts
        text = re.sub(r'(Continue reading|Read more|Click here)', '', text, flags=re.IGNORECASE)
        
        return text.strip()

    def format_article_for_prompt(self, index: int, article: Dict) -> str:
        """Assemble a structured snippet with metadata for prompting."""
        title = article.get('title', 'Untitled')
        source = article.get('source') or article.get('subreddit', 'Unknown')
        published = article.get('published') or article.get('created_utc') or 'Unknown date'
        summary = article.get('summary') or article.get('selftext') or ''
        summary = self.clean_text_for_summary(summary)[:600]

        metrics = []
        score = article.get('score')
        comments = article.get('num_comments')
        sentiment = article.get('sentiment')
        if score is not None:
            metrics.append(f"Score: {score}")
        if comments is not None and comments > 0:
            metrics.append(f"Comments: {comments}")
        if sentiment:
            metrics.append(f"Sentiment: {sentiment}")

        metric_line = ", ".join(metrics) if metrics else "None reported"

        return (
            f"[{index}] Title: {title}\n"
            f"Source: {source}\n"
            f"Published: {published}\n"
            f"Metrics: {metric_line}\n"
            f"Summary: {summary}"
        )

    def qa_check_summary(self, summary: str, citations: List[str]) -> Tuple[str, List[str]]:
        """Flag mismatches between inline citations and provided sources."""
        issues: List[str] = []

        citation_refs = set(re.findall(r'\[(\d+)\]', summary))
        valid_refs = {str(i + 1) for i in range(len(citations))}

        if citations and not citation_refs:
            issues.append("no citations referenced despite available sources")

        if not citations and citation_refs:
            issues.append("references citation markers but no citations were supplied")

        invalid_refs = citation_refs - valid_refs
        if invalid_refs:
            issues.append(f"invalid citation ids: {', '.join(sorted(invalid_refs))}")

        unused_citations = valid_refs - citation_refs
        if len(citations) > 1 and unused_citations:
            issues.append(f"unused citations: {', '.join(sorted(unused_citations))}")

        return summary, issues
    
    def create_fallback_summary(self, articles: List[Dict]) -> str:
        """Create a basic summary without AI when API is unavailable"""
        if not articles:
            return "No articles found for this topic."
        
        # Use the first article's existing summary or title
        primary = articles[0]
        summary = primary.get('summary', '') or primary.get('selftext', '')
        
        if len(summary) > 300:
            summary = summary[:300] + "..."
        
        if len(articles) > 1:
            summary += f" This story has generated discussion across {len(articles)} sources."
        
        return summary or primary.get('title', 'No summary available.')
    
    def summarize_topic_cluster(self, topic: str, articles: List[Dict], style: str = 'professional') -> tuple[str, List[str], List[str]]:
        """Create a blog-style summary for a trending topic with citations and QA flags."""
        if not articles:
            return self.create_fallback_summary(articles), [], []

        if not self.api_enabled:
            return self.create_fallback_summary(articles), [], []

        # Prepare content for summarization and collect citations
        content_parts: List[str] = []
        citations: List[str] = []

        for i, article in enumerate(articles[:5], 1):  # Limit to top 5 articles to avoid token limits
            source = article.get('source', '') or article.get('subreddit', '')
            title = article.get('title', '')
            link = article.get('link', '') or article.get('url', '')

            content_parts.append(self.format_article_for_prompt(i, article))
            citations.append(f"[{i}] {source}: {title} - {link}")

        combined_content = "\n\n".join(content_parts)
        combined_content = self.clean_text_for_summary(combined_content)

        # Craft prompt based on style
        if style == 'professional':
            prompt = f"""Write a concise two-paragraph newsletter summary about the AI topic "{topic}" using the following sources.

Style guidelines:
- Paragraph 1 (2-3 sentences): capture core developments and cite the most relevant sources.
- Paragraph 2 (2-3 sentences): explain impact, highlight metrics or sentiment, and compare viewpoints when possible.
- Keep an authoritative yet approachable tone; avoid hype.
- Weave in concrete numbers, timelines, or engagement data when provided.
- Reference sources as [1], [2], etc., and ensure every listed citation is used.
- No bullet points.
- Do NOT include any headers, titles, or markdown formatting - just the two paragraphs.

Content to summarize:
{combined_content}

Summary:"""

        elif style == 'community':
            prompt = f"""Write two compact paragraphs about the AI topic "{topic}" emphasizing community reactions.

Style guidelines:
- Paragraph 1 (2 sentences): recap the triggering news and key facts with citations.
- Paragraph 2 (2-3 sentences): describe sentiment, debates, or humor using the engagement metrics provided.
- Tone should be conversational but still professional.
- Cite sources as [1], [2], etc., using each citation exactly once.
- Avoid bullet points and filler phrases.
- Do NOT include any headers, titles, or markdown formatting - just the two paragraphs.

Content to summarize:
{combined_content}

Summary:"""

        else:
            prompt = f"""Write two short paragraphs about the AI topic "{topic}". Reference sources as [1], [2], etc.

Content to summarize:
{combined_content}

Summary:"""

        try:
            response = self.client.messages.create(
                model="claude-3-7-sonnet-20250219",
                max_tokens=400,
                temperature=0.7,
                system="You are a skilled tech journalist writing for an AI newsletter. Create engaging, informative summaries that capture both technical details and human interest.",
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            summary_text = response.content[0].text.strip()
            summary_text, issues = self.qa_check_summary(summary_text, citations)
            if issues:
                print(f"⚠️  QA flags for topic '{topic}': {', '.join(issues)}")

            return summary_text, citations, issues

        except Exception as e:
            print(f"❌ Error with AI summarization: {str(e)}")
            return self.create_fallback_summary(articles), [], []
    
    def summarize_individual_story(self, article: Dict, context: str = "respected") -> tuple[str, str]:
        """Create a summary for an individual news story with source link"""
        source_link = article.get('link', '') or article.get('url', '')
        
        if not self.api_enabled:
            summary = article.get('summary', '') or article.get('selftext', '')
            fallback = summary[:300] + "..." if len(summary) > 300 else summary
            return fallback, source_link
        
        title = article.get('title', '')
        content = article.get('summary', '') or article.get('selftext', '')
        source = article.get('source', '') or article.get('subreddit', '')
        published = article.get('published') or article.get('created_utc') or 'Unknown date'

        metrics = []
        score = article.get('score')
        comments = article.get('num_comments')
        sentiment = article.get('sentiment')
        if score is not None:
            metrics.append(f"Score: {score}")
        if comments:
            metrics.append(f"Comments: {comments}")
        if sentiment:
            metrics.append(f"Sentiment: {sentiment}")
        metric_line = ", ".join(metrics) if metrics else "None reported"

        body = self.clean_text_for_summary(content)
        full_content = (
            f"Title: {title}\n"
            f"Source: {source}\n"
            f"Published: {published}\n"
            f"Metrics: {metric_line}\n"
            f"Details: {body}"
        )

        if context == "respected":
            prompt = f"""Summarize this AI news story for a professional newsletter.

Requirements:
- Produce exactly two paragraphs with two sentences each.
- Paragraph 1: describe the development, include any timelines or metrics.
- Paragraph 2: explain significance, technical implications, and likely next steps.
- Use concrete language, avoid hype, and do not invent details.
- Do NOT include any headers, titles, or markdown formatting - just the two paragraphs.

Source material:
{full_content}

Summary:"""
        else:  # community context
            prompt = f"""Summarize this AI community discussion for a newsletter audience.

Requirements:
- Produce two paragraphs (2 sentences each) in a conversational tone.
- Paragraph 1: state the topic and why it surfaced now, referencing the key facts.
- Paragraph 2: cover viewpoints, sentiment, or notable quotes using the engagement data.
- Stay grounded in the provided details; avoid speculation.
- Do NOT include any headers, titles, or markdown formatting - just the two paragraphs.

Source material:
{full_content}

Summary:"""
        
        try:
            response = self.client.messages.create(
                model="claude-3-7-sonnet-20250219",
                max_tokens=250,
                temperature=0.6,
                system="You are writing concise, engaging summaries for an AI newsletter audience.",
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            summary_text = response.content[0].text.strip()
            summary_text, issues = self.qa_check_summary(summary_text, [])
            if issues:
                print(f"⚠️  QA flags for story '{title}': {', '.join(issues)}")

            return summary_text, source_link
            
        except Exception as e:
            print(f"❌ Error summarizing individual story: {str(e)}")
            return self.create_fallback_summary([article]), source_link
    
    def generate_section_intro(self, section_name: str, article_count: int) -> str:
        """Generate engaging introductions for newsletter sections"""
        if not self.api_enabled:
            return f"Here are the top {article_count} developments in {section_name.lower()}:"
        
        prompts = {
            "The Signal": f"Write a 1-2 sentence engaging introduction for the 'Signal' section of an AI newsletter, which covers {article_count} serious AI developments this week.",
            "The Noise": f"Write a 1-2 sentence fun, casual introduction for the 'Noise' section of an AI newsletter, which covers {article_count} community reactions and viral AI moments this week.",
            "Trending This Week": f"Write a 1-2 sentence introduction for the trending topics section, highlighting {article_count} themes that dominated AI discussions this week."
        }
        
        prompt = prompts.get(section_name, f"Write a brief introduction for {section_name} with {article_count} items.")
        
        try:
            response = self.client.messages.create(
                model="claude-3-7-sonnet-20250219",
                max_tokens=100,
                temperature=0.8,
                system="You are writing engaging newsletter section introductions. Keep them brief, punchy, and appropriate for the tone.",
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            return response.content[0].text.strip()
            
        except Exception as e:
            print(f"❌ Error generating section intro: {str(e)}")
            return f"Here's what happened in {section_name.lower()} this week:"

if __name__ == "__main__":
    # Test the summarizer
    summarizer = AISummarizer()
    
    if summarizer.api_enabled:
        print("✅ AI Summarizer ready with OpenAI API")
    else:
        print("⚠️  AI Summarizer running in fallback mode (no API key)")
    
    # Example test
    test_article = {
        'title': 'OpenAI Releases GPT-5',
        'summary': 'OpenAI has announced the release of GPT-5, featuring improved reasoning capabilities and multimodal understanding.',
        'source': 'OpenAI Blog'
    }
    
    # Test individual story summarization
    summary = summarizer.summarize_individual_story(test_article)
    print(f"\nTest summary: {summary}")
