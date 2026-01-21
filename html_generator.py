"""Generate tabbed HTML output for social content with dark theme."""
from __future__ import annotations

import html
import os
import re
from datetime import datetime
from pathlib import Path
from typing import List

from content_types import SocialPost, WeeklySocialContent

OUTPUT_DIR = Path(__file__).parent / "output"


class HTMLGenerator:
    """Generates unified tabbed HTML output for Bluesky, LinkedIn, and Blog content."""

    def generate_html(self, content: WeeklySocialContent, filename: str = None) -> str:
        """Generate complete HTML document with tabbed content.

        Args:
            content: WeeklySocialContent with all generated posts
            filename: Optional custom filename

        Returns:
            Path to saved HTML file
        """
        posts_html = self._render_posts(content.posts)
        generated_date = datetime.now().strftime("%B %d, %Y")

        html_doc = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>BioAI Weekly Social Content - {generated_date}</title>
    <meta name="description" content="Weekly social content for BioAI newsletter across Bluesky, LinkedIn, and Blog">
    <style>
    {self._get_css()}
    </style>
</head>
<body>
    <header class="hero">
        <div class="container">
            <div class="hero-content">
                <div class="hero-badge">
                    <span>Weekly Content</span>
                </div>
                <h1>BioAI Weekly</h1>
                <p class="subtitle">Social Content for Bluesky, LinkedIn & Blog</p>
                <div class="hero-meta">
                    <div class="hero-meta-item">
                        <p class="label">Week Of</p>
                        <p class="value">{content.week_end or generated_date}</p>
                    </div>
                    <div class="hero-meta-item">
                        <p class="label">Articles Analyzed</p>
                        <p class="value">{content.total_articles_analyzed}</p>
                    </div>
                    <div class="hero-meta-item">
                        <p class="label">Community Posts</p>
                        <p class="value">{content.total_community_posts}</p>
                    </div>
                    <div class="hero-meta-item">
                        <p class="label">Topics</p>
                        <p class="value">{len(content.posts)}</p>
                    </div>
                </div>
            </div>
        </div>
    </header>

    <main>
        <div class="container">
            <section class="content-section">
                <div class="section-header">
                    <h2>
                        <div class="section-icon">
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M12 20h9"/>
                                <path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"/>
                            </svg>
                        </div>
                        Social Content
                    </h2>
                </div>

                {posts_html}
            </section>
        </div>
    </main>

    <footer>
        <div class="container">
            <div class="footer-content">
                <div class="footer-logo">BioAI Weekly</div>
                <p class="footer-text">AI-generated social content for biology and AI research</p>
                <div class="footer-meta">
                    <span>Generated on {generated_date}</span>
                    <span>Model: Claude 3.7 Sonnet</span>
                </div>
            </div>
        </div>
    </footer>

    <script>
    {self._get_javascript()}
    </script>
</body>
</html>"""

        return self._save_html(html_doc, filename)

    def _render_posts(self, posts: List[SocialPost]) -> str:
        """Render all posts as HTML cards with tabs."""
        if not posts:
            return '<p class="no-content">No content generated this week.</p>'

        cards = []
        for post in posts:
            cards.append(self._render_post_card(post))

        return "\n".join(cards)

    def _render_post_card(self, post: SocialPost) -> str:
        """Render a single post as a tabbed card."""
        post_id = post.id

        # Bluesky content (thread)
        bluesky_html = self._render_bluesky_thread(post.bluesky_posts, post_id)

        # LinkedIn content
        linkedin_html = self._render_linkedin(post.linkedin_post, post_id)

        # Blog content
        blog_html = self._render_blog(
            post.blog_title,
            post.blog_content,
            post.blog_meta_description,
            post_id
        )

        return f"""
        <article class="post-card" data-post-id="{post_id}">
            <header class="post-header">
                <h3 class="post-title">{html.escape(post.topic_keyword.title())}</h3>
                <p class="post-source">
                    <span>Topic</span>
                    {self._render_source_link(post)}
                </p>
            </header>

            <div class="platform-tabs">
                <button class="platform-tab active" data-platform="bluesky" onclick="switchTab('{post_id}', 'bluesky')">
                    <svg viewBox="0 0 24 24" fill="currentColor">
                        <path d="M12 2C6.477 2 2 6.477 2 12c0 4.991 3.657 9.128 8.438 9.879V14.89h-2.54V12h2.54V9.797c0-2.506 1.492-3.89 3.777-3.89 1.094 0 2.238.195 2.238.195v2.46h-1.26c-1.243 0-1.63.771-1.63 1.562V12h2.773l-.443 2.89h-2.33v6.989C18.343 21.129 22 16.99 22 12c0-5.523-4.477-10-10-10z"/>
                    </svg>
                    Bluesky
                </button>
                <button class="platform-tab" data-platform="linkedin" onclick="switchTab('{post_id}', 'linkedin')">
                    <svg viewBox="0 0 24 24" fill="currentColor">
                        <path d="M19 0h-14c-2.761 0-5 2.239-5 5v14c0 2.761 2.239 5 5 5h14c2.762 0 5-2.239 5-5v-14c0-2.761-2.238-5-5-5zm-11 19h-3v-11h3v11zm-1.5-12.268c-.966 0-1.75-.79-1.75-1.764s.784-1.764 1.75-1.764 1.75.79 1.75 1.764-.783 1.764-1.75 1.764zm13.5 12.268h-3v-5.604c0-3.368-4-3.113-4 0v5.604h-3v-11h3v1.765c1.396-2.586 7-2.777 7 2.476v6.759z"/>
                    </svg>
                    LinkedIn
                </button>
                <button class="platform-tab" data-platform="blog" onclick="switchTab('{post_id}', 'blog')">
                    <svg viewBox="0 0 24 24" fill="currentColor">
                        <path d="M19 5v14H5V5h14m0-2H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-5 14H7v-2h7v2zm3-4H7v-2h10v2zm0-4H7V7h10v2z"/>
                    </svg>
                    Blog
                </button>
            </div>

            <!-- Bluesky Content -->
            {bluesky_html}

            <!-- LinkedIn Content -->
            {linkedin_html}

            <!-- Blog Content -->
            {blog_html}
        </article>
"""

    def _render_bluesky_thread(self, posts: List[str], post_id: str) -> str:
        """Render Bluesky thread posts."""
        if not posts:
            return '<div class="platform-content active" data-platform="bluesky"><p>No Bluesky content generated.</p></div>'

        thread_html = []
        for i, post_text in enumerate(posts, 1):
            escaped = html.escape(post_text)
            char_count = len(post_text)
            thread_html.append(f"""
                <div class="thread-post">
                    <div class="thread-number">Post {i}/{len(posts)}</div>
                    <div id="bs_{post_id}_{i}" class="content-text">{escaped}</div>
                    <div class="content-footer">
                        <span class="word-count">{char_count} chars</span>
                        <button class="copy-button" onclick="copyToClipboard('bs_{post_id}_{i}', this)">
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>
                            Copy
                        </button>
                    </div>
                </div>
            """)

        total_chars = sum(len(p) for p in posts)
        copy_all_text = "\\n\\n".join(posts)

        return f"""
            <div class="platform-content active" data-platform="bluesky">
                <div class="thread-container">
                    {"".join(thread_html)}
                </div>
                <div class="content-footer thread-footer">
                    <span class="word-count">Thread: {len(posts)} posts, {total_chars} total chars</span>
                    <button class="copy-button" onclick="copyThread('{post_id}', {len(posts)}, this)">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>
                        Copy All
                    </button>
                </div>
            </div>
        """

    def _render_linkedin(self, content: str, post_id: str) -> str:
        """Render LinkedIn post content."""
        if not content:
            return '<div class="platform-content" data-platform="linkedin"><p>No LinkedIn content generated.</p></div>'

        # Convert paragraphs
        paragraphs = content.split("\n\n")
        formatted = "".join(f"<p>{html.escape(p)}</p>" for p in paragraphs if p.strip())

        word_count = len(content.split())

        return f"""
            <div class="platform-content" data-platform="linkedin">
                <div id="li_{post_id}" class="content-text">
                    {formatted}
                </div>
                <div class="content-footer">
                    <span class="word-count">{word_count} words</span>
                    <button class="copy-button" onclick="copyToClipboard('li_{post_id}', this)">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>
                        Copy
                    </button>
                </div>
            </div>
        """

    def _render_blog(
        self, title: str, content: str, meta: str, post_id: str
    ) -> str:
        """Render blog post content with markdown-style formatting."""
        if not content:
            return '<div class="platform-content" data-platform="blog"><p>No blog content generated.</p></div>'

        # Convert markdown-style headers and formatting
        formatted = self._markdown_to_html(content)
        word_count = len(content.split())

        return f"""
            <div class="platform-content" data-platform="blog">
                <div class="blog-title-display">{html.escape(title)}</div>
                <div id="blog_{post_id}" class="blog-content">
                    {formatted}
                </div>
                <div class="blog-meta">
                    <div class="blog-meta-title">Post Metadata</div>
                    <dl>
                        <dt>Title</dt>
                        <dd>{html.escape(title)}</dd>
                        <dt>Meta Description</dt>
                        <dd>{html.escape(meta)}</dd>
                        <dt>Word Count</dt>
                        <dd>{word_count} words</dd>
                    </dl>
                </div>
                <div class="content-footer">
                    <span class="word-count">{word_count} words</span>
                    <button class="copy-button" onclick="copyToClipboard('blog_{post_id}', this)">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>
                        Copy
                    </button>
                </div>
            </div>
        """

    def _markdown_to_html(self, text: str) -> str:
        """Convert basic markdown to HTML."""
        lines = text.split("\n")
        result = []
        in_list = False
        list_type = None

        for line in lines:
            stripped = line.strip()

            # Headers
            if stripped.startswith("## "):
                if in_list:
                    result.append(f"</{list_type}>")
                    in_list = False
                result.append(f"<h2>{html.escape(stripped[3:])}</h2>")
            elif stripped.startswith("### "):
                if in_list:
                    result.append(f"</{list_type}>")
                    in_list = False
                result.append(f"<h3>{html.escape(stripped[4:])}</h3>")
            # Bullet lists
            elif stripped.startswith("- ") or stripped.startswith("* "):
                if not in_list or list_type != "ul":
                    if in_list:
                        result.append(f"</{list_type}>")
                    result.append("<ul>")
                    in_list = True
                    list_type = "ul"
                result.append(f"<li>{html.escape(stripped[2:])}</li>")
            # Numbered lists
            elif re.match(r"^\d+\.\s", stripped):
                if not in_list or list_type != "ol":
                    if in_list:
                        result.append(f"</{list_type}>")
                    result.append("<ol>")
                    in_list = True
                    list_type = "ol"
                content = re.sub(r"^\d+\.\s", "", stripped)
                result.append(f"<li>{html.escape(content)}</li>")
            # Paragraphs
            elif stripped:
                if in_list:
                    result.append(f"</{list_type}>")
                    in_list = False
                # Handle bold and inline code
                escaped = html.escape(stripped)
                escaped = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", escaped)
                escaped = re.sub(r"`(.+?)`", r"<code>\1</code>", escaped)
                result.append(f"<p>{escaped}</p>")

        if in_list:
            result.append(f"</{list_type}>")

        return "\n".join(result)

    def _render_source_link(self, post: SocialPost) -> str:
        """Render source link if available."""
        if post.source_articles:
            first_article = post.source_articles[0]
            link = first_article.get("link") or first_article.get("url")
            if link:
                return f' &bull; <a href="{html.escape(link)}" target="_blank" rel="noopener">View Source</a>'
        return ""

    def _get_css(self) -> str:
        """Return the CSS styles (dark theme matching benchmarking_deepdive)."""
        return """
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

    :root {
        --font-sans: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        --font-mono: 'JetBrains Mono', 'SF Mono', Monaco, monospace;
        --color-bg: #0f0f23;
        --color-card: #1a1a2e;
        --color-text: #e4e4e7;
        --color-text-secondary: #a1a1aa;
        --color-text-muted: #71717a;
        --color-border: #27272a;
        --color-border-light: #3f3f46;
        --color-accent: #6366f1;
        --color-accent-light: #818cf8;
        --shadow-sm: 0 1px 2px rgba(0,0,0,0.3);
        --shadow-md: 0 4px 12px rgba(0,0,0,0.4);
        --shadow-lg: 0 12px 40px rgba(0,0,0,0.5);
        --radius: 12px;
        --radius-lg: 16px;
        --transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
    }

    * {
        box-sizing: border-box;
        margin: 0;
        padding: 0;
    }

    html { scroll-behavior: smooth; }

    body {
        font-family: var(--font-sans);
        background: var(--color-bg);
        color: var(--color-text);
        line-height: 1.7;
        font-size: 16px;
        -webkit-font-smoothing: antialiased;
    }

    .container {
        max-width: 900px;
        margin: 0 auto;
        padding: 0 2rem;
    }

    /* Hero Header */
    .hero {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
        color: white;
        padding: 4rem 0 5rem;
        position: relative;
        border-bottom: 1px solid var(--color-border);
    }

    .hero-content {
        text-align: center;
    }

    .hero-badge {
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.5rem 1rem;
        background: rgba(99, 102, 241, 0.2);
        border: 1px solid rgba(99, 102, 241, 0.3);
        border-radius: 50px;
        margin-bottom: 1.5rem;
    }

    .hero-badge span {
        font-size: 0.75rem;
        font-weight: 600;
        letter-spacing: 0.1em;
        text-transform: uppercase;
        color: var(--color-accent-light);
    }

    .hero h1 {
        font-size: 2.5rem;
        font-weight: 700;
        margin-bottom: 0.75rem;
        letter-spacing: -0.02em;
        line-height: 1.2;
    }

    .hero .subtitle {
        font-size: 1.1rem;
        color: rgba(255,255,255,0.7);
        margin-bottom: 2rem;
    }

    .hero-meta {
        display: flex;
        justify-content: center;
        gap: 2rem;
        flex-wrap: wrap;
    }

    .hero-meta-item {
        text-align: center;
    }

    .hero-meta-item .label {
        font-size: 0.7rem;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        color: rgba(255,255,255,0.5);
        margin-bottom: 0.25rem;
    }

    .hero-meta-item .value {
        font-size: 0.95rem;
        font-weight: 600;
        color: white;
    }

    /* Main Content */
    main {
        padding: 3rem 0;
    }

    .content-section {
        margin-bottom: 4rem;
    }

    .section-header {
        margin-bottom: 2rem;
        padding-bottom: 1rem;
        border-bottom: 1px solid var(--color-border);
    }

    .section-header h2 {
        font-size: 1.5rem;
        font-weight: 600;
        color: var(--color-text);
        display: flex;
        align-items: center;
        gap: 0.75rem;
    }

    .section-header .section-icon {
        width: 32px;
        height: 32px;
        background: var(--color-accent);
        border-radius: 8px;
        display: flex;
        align-items: center;
        justify-content: center;
    }

    .section-header .section-icon svg {
        width: 18px;
        height: 18px;
        color: white;
    }

    /* Post Card */
    .post-card {
        background: var(--color-card);
        border-radius: var(--radius-lg);
        border: 1px solid var(--color-border);
        overflow: hidden;
        margin-bottom: 2rem;
    }

    .post-header {
        padding: 1.5rem 2rem;
        border-bottom: 1px solid var(--color-border);
    }

    .post-title {
        font-size: 1.25rem;
        font-weight: 600;
        margin-bottom: 0.5rem;
        color: var(--color-text);
    }

    .post-source {
        font-size: 0.85rem;
        color: var(--color-text-secondary);
    }

    .post-source a {
        color: var(--color-accent-light);
        text-decoration: none;
    }

    .post-source a:hover {
        text-decoration: underline;
    }

    /* Platform Tabs */
    .platform-tabs {
        display: flex;
        border-bottom: 1px solid var(--color-border);
        background: rgba(0,0,0,0.2);
    }

    .platform-tab {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        padding: 1rem 1.5rem;
        border: none;
        background: transparent;
        font-family: var(--font-sans);
        font-size: 0.875rem;
        font-weight: 500;
        color: var(--color-text-muted);
        cursor: pointer;
        transition: var(--transition);
        border-bottom: 2px solid transparent;
        margin-bottom: -1px;
    }

    .platform-tab:hover {
        color: var(--color-text);
    }

    .platform-tab.active {
        color: var(--color-accent-light);
        border-bottom-color: var(--color-accent);
        background: var(--color-card);
    }

    .platform-tab svg {
        width: 18px;
        height: 18px;
    }

    /* Platform Content */
    .platform-content {
        padding: 2rem;
        display: none;
    }

    .platform-content.active {
        display: block;
    }

    .content-text {
        font-size: 1rem;
        line-height: 1.9;
        color: var(--color-text);
    }

    .content-text p {
        margin-bottom: 1.25rem;
    }

    .content-text p:last-child {
        margin-bottom: 0;
    }

    .content-footer {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-top: 1.5rem;
        padding-top: 1rem;
        border-top: 1px solid var(--color-border);
    }

    .word-count {
        font-size: 0.8rem;
        color: var(--color-text-muted);
        font-family: var(--font-mono);
    }

    .copy-button {
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.625rem 1.25rem;
        background: var(--color-accent);
        border: none;
        border-radius: var(--radius);
        font-family: var(--font-sans);
        font-size: 0.8rem;
        font-weight: 600;
        color: white;
        cursor: pointer;
        transition: var(--transition);
    }

    .copy-button:hover {
        background: var(--color-accent-light);
        transform: translateY(-1px);
    }

    .copy-button.copied {
        background: #10b981;
    }

    .copy-button svg {
        width: 14px;
        height: 14px;
    }

    /* Thread styles */
    .thread-container {
        display: flex;
        flex-direction: column;
        gap: 1.5rem;
    }

    .thread-post {
        background: rgba(0,0,0,0.2);
        border-radius: var(--radius);
        padding: 1.25rem;
        border: 1px solid var(--color-border);
    }

    .thread-number {
        font-size: 0.75rem;
        font-weight: 600;
        color: var(--color-accent-light);
        margin-bottom: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    .thread-footer {
        margin-top: 1rem;
        padding-top: 1.5rem;
    }

    /* Blog Content */
    .blog-content {
        font-size: 1.05rem;
        line-height: 2;
    }

    .blog-content h2 {
        font-size: 1.4rem;
        font-weight: 600;
        margin-top: 2.5rem;
        margin-bottom: 1rem;
        color: var(--color-text);
    }

    .blog-content h3 {
        font-size: 1.2rem;
        font-weight: 600;
        margin-top: 2rem;
        margin-bottom: 0.75rem;
        color: var(--color-text);
    }

    .blog-content p {
        margin-bottom: 1.5rem;
    }

    .blog-content ul, .blog-content ol {
        margin-bottom: 1.5rem;
        padding-left: 1.75rem;
    }

    .blog-content li {
        margin-bottom: 0.625rem;
    }

    .blog-content strong {
        color: var(--color-accent-light);
    }

    .blog-content code {
        font-family: var(--font-mono);
        background: rgba(99, 102, 241, 0.15);
        padding: 0.2rem 0.4rem;
        border-radius: 4px;
        font-size: 0.9em;
    }

    .blog-title-display {
        font-size: 1.5rem;
        font-weight: 600;
        margin-bottom: 1.5rem;
        padding-bottom: 1rem;
        border-bottom: 2px solid var(--color-accent);
        color: var(--color-text);
    }

    .blog-meta {
        background: rgba(0,0,0,0.3);
        padding: 1.5rem;
        border-radius: var(--radius);
        margin-top: 2rem;
        border: 1px solid var(--color-border);
    }

    .blog-meta-title {
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        color: var(--color-text-muted);
        margin-bottom: 1rem;
    }

    .blog-meta dl {
        display: grid;
        grid-template-columns: auto 1fr;
        gap: 0.75rem 1.5rem;
    }

    .blog-meta dt {
        font-weight: 600;
        color: var(--color-text-secondary);
        font-size: 0.875rem;
    }

    .blog-meta dd {
        color: var(--color-text);
        font-size: 0.875rem;
    }

    /* Footer */
    footer {
        background: var(--color-card);
        color: var(--color-text);
        padding: 3rem 0;
        margin-top: 4rem;
        border-top: 1px solid var(--color-border);
    }

    .footer-content {
        text-align: center;
    }

    .footer-logo {
        font-size: 1.25rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
        color: var(--color-accent-light);
    }

    .footer-text {
        color: var(--color-text-secondary);
        font-size: 0.875rem;
        margin-bottom: 1.5rem;
    }

    .footer-meta {
        display: flex;
        justify-content: center;
        gap: 2rem;
        flex-wrap: wrap;
        font-size: 0.8rem;
        color: var(--color-text-muted);
    }

    .no-content {
        text-align: center;
        color: var(--color-text-muted);
        padding: 3rem;
    }

    /* Responsive - Mobile */
    @media (max-width: 768px) {
        .container { padding: 0 1rem; }
        .hero { padding: 2.5rem 0 3rem; }
        .hero h1 { font-size: 1.75rem; }
        main { padding: 2rem 0; }
        .post-header { padding: 1.25rem 1.5rem; }
        .platform-content { padding: 1.5rem; }

        /* Stack tabs on mobile */
        .platform-tabs {
            flex-direction: column;
        }

        .platform-tab {
            border-bottom: none;
            border-left: 2px solid transparent;
            margin-bottom: 0;
            margin-left: -1px;
        }

        .platform-tab.active {
            border-left-color: var(--color-accent);
            border-bottom-color: transparent;
        }

        .content-footer {
            flex-direction: column;
            gap: 1rem;
            align-items: stretch;
        }
        .copy-button { justify-content: center; }

        .hero-meta {
            gap: 1rem;
        }

        .blog-meta dl {
            grid-template-columns: 1fr;
            gap: 0.5rem;
        }
    }

    @media print {
        body { background: white; color: #1a1a2e; }
        .hero { background: white; color: #1a1a2e; padding: 2rem 0; }
        .post-card { border: 1px solid #e5e7eb; }
        .platform-tabs { display: none; }
        .platform-content { display: block !important; }
        .copy-button { display: none; }
    }
"""

    def _get_javascript(self) -> str:
        """Return the JavaScript for tab switching and copy functionality."""
        return """
    function switchTab(postId, platform) {
        const card = document.querySelector(`[data-post-id="${postId}"]`);
        if (!card) return;
        card.querySelectorAll('.platform-tab').forEach(tab => {
            tab.classList.toggle('active', tab.dataset.platform === platform);
        });
        card.querySelectorAll('.platform-content').forEach(content => {
            content.classList.toggle('active', content.dataset.platform === platform);
        });
    }

    function copyToClipboard(elementId, button) {
        const element = document.getElementById(elementId);
        if (!element) return;
        const text = element.innerText;
        navigator.clipboard.writeText(text).then(() => {
            const originalHtml = button.innerHTML;
            button.innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 6L9 17l-5-5"/></svg> Copied!';
            button.classList.add('copied');
            setTimeout(() => {
                button.innerHTML = originalHtml;
                button.classList.remove('copied');
            }, 2000);
        });
    }

    function copyThread(postId, numPosts, button) {
        const posts = [];
        for (let i = 1; i <= numPosts; i++) {
            const element = document.getElementById(`bs_${postId}_${i}`);
            if (element) {
                posts.push(element.innerText);
            }
        }
        const text = posts.join('\\n\\n---\\n\\n');
        navigator.clipboard.writeText(text).then(() => {
            const originalHtml = button.innerHTML;
            button.innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 6L9 17l-5-5"/></svg> Copied!';
            button.classList.add('copied');
            setTimeout(() => {
                button.innerHTML = originalHtml;
                button.classList.remove('copied');
            }, 2000);
        });
    }
"""

    def _save_html(self, html_doc: str, filename: str = None) -> str:
        """Save HTML to output directory."""
        OUTPUT_DIR.mkdir(exist_ok=True)

        if not filename:
            filename = f"social_content_{datetime.now().strftime('%Y%m%d')}.html"

        filepath = OUTPUT_DIR / filename
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(html_doc)

        print(f"📱 Social content HTML saved to {filepath}")
        return str(filepath)
