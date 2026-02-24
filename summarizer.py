import json
import anthropic
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import os
import re
from pathlib import Path

# Path to stop_slop knowledge base
STOP_SLOP_DIR = Path(__file__).parent / "stop_slop"

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
        self.stop_slop_content = self._load_stop_slop()

    def _load_stop_slop(self) -> str:
        """Load the stop_slop knowledge base files."""
        if not STOP_SLOP_DIR.exists():
            print("  Warning: stop_slop directory not found, skipping anti-slop rules")
            return ""

        # Files to load in order
        files = ["skills.md", "phrases.md", "structures.md", "examples.md"]
        content_parts = []

        content_parts.append("""
## ANTI-AI-SLOP RULES

The following rules are CRITICAL for producing human-sounding prose.
Study these carefully and apply them rigorously to all generated content.
""")

        for filename in files:
            filepath = STOP_SLOP_DIR / filename
            if filepath.exists():
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        file_content = f.read()
                        content_parts.append(f"\n### {filename.upper()}\n\n{file_content}")
                except Exception as e:
                    print(f"  Warning: Could not load {filename}: {e}")

        if len(content_parts) > 1:
            print(f"  Loaded stop_slop knowledge base ({len(content_parts)-1} files)")
            return "\n".join(content_parts)

        return ""

    def _build_system_prompt(self, base_prompt: str) -> str:
        """Build the full system prompt including stop_slop rules."""
        if self.stop_slop_content:
            return f"{base_prompt}\n\n{self.stop_slop_content}"
        return base_prompt
    
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
            base_prompt = "You are a skilled tech journalist writing for an AI newsletter. Create engaging, informative summaries that capture both technical details and human interest."
            system_prompt = self._build_system_prompt(base_prompt)

            response = self.client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=400,
                temperature=0.7,
                system=system_prompt,
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
            base_prompt = "You are writing concise, engaging summaries for an AI newsletter audience."
            system_prompt = self._build_system_prompt(base_prompt)

            response = self.client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=250,
                temperature=0.6,
                system=system_prompt,
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
            base_prompt = "You are writing engaging newsletter section introductions. Keep them brief, punchy, and appropriate for the tone."
            system_prompt = self._build_system_prompt(base_prompt)

            response = self.client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=100,
                temperature=0.8,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            return response.content[0].text.strip()

        except Exception as e:
            print(f"❌ Error generating section intro: {str(e)}")
            return f"Here's what happened in {section_name.lower()} this week:"

    def generate_linkedin_post(
        self, topic: str, articles: List[Dict], trends: List[Dict]
    ) -> str:
        """Generate a LinkedIn thought-leadership post (400-600 words).

        Args:
            topic: Primary topic keyword for the post
            articles: Source articles to draw from
            trends: Trending topics for context

        Returns:
            LinkedIn post text (400-600 words)
        """
        if not self.api_enabled:
            return f"This week in {topic}: Key developments are reshaping the field. Read our full analysis in the newsletter."

        # Prepare article content for prompt
        content_parts: List[str] = []
        for i, article in enumerate(articles[:5], 1):
            content_parts.append(self.format_article_for_prompt(i, article))
        combined_content = "\n\n".join(content_parts)

        # Format trend context
        trend_context = ""
        if trends:
            trend_keywords = [t.get('keyword', '') for t in trends[:3] if t.get('keyword')]
            if trend_keywords:
                trend_context = f"\n\nRelated trending topics this week: {', '.join(trend_keywords)}"

        prompt = f"""Write a LinkedIn thought-leadership post about "{topic}" for a professional audience interested in AI and biology research.

REQUIREMENTS:
- Length: 400-600 words (this is critical - aim for ~500 words)
- Tone: Professional, insightful, authoritative but approachable
- Structure:
  1. Opening hook (1-2 sentences that grab attention)
  2. Context and key developments (2-3 paragraphs)
  3. Analysis and implications (1-2 paragraphs)
  4. Forward-looking takeaway or call to reflection (1 paragraph)
- NO hashtags, emojis, or "Like if you agree" type engagement bait
- Use concrete details, numbers, and specific examples from the sources
- Write in first person plural ("we're seeing", "our field") or third person
- Do NOT start with "I" or make it about yourself
- Avoid generic statements - be specific and substantive

SOURCE MATERIAL:
{combined_content}
{trend_context}

Write the LinkedIn post now:"""

        try:
            base_prompt = "You are a respected voice in AI and computational biology, writing thoughtful LinkedIn content that provides genuine insight rather than engagement bait."
            system_prompt = self._build_system_prompt(base_prompt)

            response = self.client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=1000,
                temperature=0.7,
                system=system_prompt,
                messages=[{"role": "user", "content": prompt}]
            )

            return response.content[0].text.strip()

        except Exception as e:
            print(f"❌ Error generating LinkedIn post: {str(e)}")
            return f"This week in {topic}: Key developments are reshaping the field. Read our full analysis in the newsletter."

    def generate_blog_post(
        self,
        topic: str,
        articles: List[Dict],
        community_posts: List[Dict],
        trends: List[Dict]
    ) -> tuple[str, str, str]:
        """Generate a comprehensive blog post (2000-3000 words).

        Args:
            topic: Primary topic keyword for the post
            articles: Source articles from respected sources
            community_posts: Community discussion posts
            trends: Trending topics for context

        Returns:
            Tuple of (title, content, meta_description)
        """
        if not self.api_enabled:
            title = f"Weekly Analysis: {topic.title()}"
            content = f"This week's developments in {topic} highlight ongoing progress in the field."
            meta = f"Weekly analysis of {topic} developments in AI and biology research."
            return title, content, meta

        # Prepare article content
        article_parts: List[str] = []
        citations: List[str] = []
        for i, article in enumerate(articles[:8], 1):
            article_parts.append(self.format_article_for_prompt(i, article))
            source = article.get('source', '') or article.get('subreddit', '')
            title = article.get('title', '')
            link = article.get('link', '') or article.get('url', '')
            citations.append(f"[{i}] {source}: {title} - {link}")

        # Prepare community context
        community_context = ""
        if community_posts:
            community_snippets = []
            for post in community_posts[:3]:
                title = post.get('title', '')
                score = post.get('score', 0)
                comments = post.get('num_comments', 0)
                community_snippets.append(f"- {title} ({score} upvotes, {comments} comments)")
            community_context = f"\n\nCOMMUNITY DISCUSSION:\n" + "\n".join(community_snippets)

        # Prepare trend context
        trend_context = ""
        if trends:
            trend_info = []
            for t in trends[:5]:
                keyword = t.get('keyword', '')
                mentions = t.get('mentions', 0)
                sentiment = t.get('community_sentiment', 'neutral')
                if keyword:
                    trend_info.append(f"- {keyword}: {mentions} mentions, {sentiment} sentiment")
            if trend_info:
                trend_context = f"\n\nTRENDING THIS WEEK:\n" + "\n".join(trend_info)

        citations_text = "\n".join(citations) if citations else "No specific citations available."

        prompt = f"""Write a comprehensive blog post about "{topic}" for the BioAI Weekly newsletter.

REQUIREMENTS:
- Length: 2000-3000 words (this is critical - aim for ~2500 words)
- Start with a TL;DR section (3-4 bullet points summarizing key takeaways)
- Include 4-6 clearly labeled sections with ## headers
- Cite sources using [1], [2], etc. format where relevant
- Include a "What This Means" or "Looking Ahead" conclusion section
- Tone: Authoritative but accessible, suitable for researchers and industry professionals
- Be specific with data, timelines, and technical details
- Cover multiple angles: technical developments, industry implications, community reactions

STRUCTURE TEMPLATE:
## TL;DR
[3-4 bullet points]

## [Section 1 - e.g., "The Core Development"]
[Content with citations]

## [Section 2 - e.g., "Technical Deep Dive"]
[Content with citations]

## [Section 3 - e.g., "Industry Implications"]
[Content]

## [Section 4 - e.g., "Community Perspective"]
[Content drawing from community discussions]

## [Section 5 - e.g., "What This Means"]
[Forward-looking analysis]

SOURCE ARTICLES:
{chr(10).join(article_parts)}
{community_context}
{trend_context}

AVAILABLE CITATIONS:
{citations_text}

FIRST: Write a compelling blog title (not generic - be specific to this week's content)
SECOND: Write a meta description (150-160 characters for SEO)
THIRD: Write the full blog post

Format your response as:
TITLE: [Your title here]
META: [Your meta description here]
CONTENT:
[Your full blog post here]"""

        try:
            base_prompt = "You are the lead writer for BioAI Weekly, producing in-depth analysis that bridges cutting-edge research and practical implications. Your writing is respected for its technical accuracy and clarity."
            system_prompt = self._build_system_prompt(base_prompt)

            response = self.client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=4000,
                temperature=0.7,
                system=system_prompt,
                messages=[{"role": "user", "content": prompt}]
            )

            response_text = response.content[0].text.strip()

            # Parse the response
            title = topic.title()
            meta = f"Weekly analysis of {topic} in AI and biology research."
            content = response_text

            # Extract title
            if "TITLE:" in response_text:
                title_start = response_text.find("TITLE:") + 6
                title_end = response_text.find("\n", title_start)
                if title_end > title_start:
                    title = response_text[title_start:title_end].strip()

            # Extract meta description
            if "META:" in response_text:
                meta_start = response_text.find("META:") + 5
                meta_end = response_text.find("\n", meta_start)
                if meta_end > meta_start:
                    meta = response_text[meta_start:meta_end].strip()

            # Extract content
            if "CONTENT:" in response_text:
                content_start = response_text.find("CONTENT:") + 8
                content = response_text[content_start:].strip()
            elif "## TL;DR" in response_text:
                # Content starts at TL;DR if no CONTENT marker
                content_start = response_text.find("## TL;DR")
                content = response_text[content_start:].strip()

            return title, content, meta

        except Exception as e:
            print(f"❌ Error generating blog post: {str(e)}")
            title = f"Weekly Analysis: {topic.title()}"
            content = f"This week's developments in {topic} highlight ongoing progress in the field."
            meta = f"Weekly analysis of {topic} developments in AI and biology research."
            return title, content, meta


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
