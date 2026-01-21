#!/usr/bin/env python3
"""
AI Newsletter Generator - Main Script

This script generates a weekly AI newsletter by:
1. Scraping respected AI news sources (RSS feeds)
2. Collecting community sentiment from Reddit
3. Analyzing trending topics
4. Creating AI-powered summaries
5. Generating a beautiful HTML newsletter
6. Optionally sending via email

Usage:
    python run_newsletter.py
    python run_newsletter.py --send
    python run_newsletter.py --send --to recipient@example.com

Environment Variables:
    ANTHROPIC_API_KEY: Your Anthropic API key for Claude AI summarization (optional)
    SMTP_EMAIL: Your Gmail address (required for --send)
    SMTP_PASSWORD: Your Gmail app password (required for --send)
    EMAIL_TO: Recipient email address (required for --send, unless --to specified)

Output:
    - HTML newsletter file in output/ directory
    - JSON data files with raw scraped data
"""

import os
import sys
import argparse
from datetime import datetime
from newsletter_generator import NewsletterGenerator

def main():
    parser = argparse.ArgumentParser(description='Generate AI Weekly Newsletter')
    parser.add_argument('--days', type=int, default=7,
                       help='Number of days back to scrape (default: 7)')
    parser.add_argument('--output', type=str,
                       help='Custom output filename for newsletter')
    parser.add_argument('--no-ai', action='store_true',
                       help='Disable AI summarization (use fallback summaries)')
    parser.add_argument('--no-social', action='store_true',
                       help='Skip social content generation (Bluesky, LinkedIn, Blog)')
    parser.add_argument('--social-only', action='store_true',
                       help='Generate only social content, skip main newsletter')
    parser.add_argument('--send', action='store_true',
                       help='Send newsletter via email after generation')
    parser.add_argument('--to', type=str,
                       help='Override email recipient (default: EMAIL_TO env var)')

    args = parser.parse_args()
    
    print("🤖 AI Weekly Newsletter Generator")
    print("=" * 50)
    
    # Check for Anthropic API key
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if args.no_ai:
        api_key = None
        print("ℹ️  AI summarization disabled by user")
    elif not api_key:
        print("⚠️  No Anthropic API key found. Set ANTHROPIC_API_KEY environment variable for Claude AI summaries.")
        print("   Falling back to basic summaries...")
    else:
        print("✅ Anthropic API key found - Claude AI summarization enabled")
    
    print(f"📅 Collecting news from last {args.days} days")
    print()
    
    try:
        # Initialize generator
        generator = NewsletterGenerator(anthropic_api_key=api_key)

        # Handle --social-only mode
        if args.social_only:
            print("📱 Social-only mode: generating social content without newsletter")
            # Still need to collect data
            articles, posts, trend_report = generator.collect_all_data(args.days)

            # Generate unified social content
            from social_content_generator import SocialContentGenerator
            from html_generator import HTMLGenerator

            social_gen = SocialContentGenerator(generator.summarizer)
            html_gen = HTMLGenerator()

            weekly_content = social_gen.generate_weekly_content(
                articles=articles,
                community_posts=posts,
                trends=trend_report.get('trending_topics', []),
                max_posts=3
            )
            social_path = html_gen.generate_html(weekly_content)

            print()
            print("🎉 Social content generation successful!")
            print(f"📱 Social content: Open this file in your browser: {social_path}")
            return 0

        # Generate newsletter and optionally social content
        newsletter_path, bluesky_path, social_path = generator.generate_weekly_newsletter(
            days_back=args.days,
            generate_social=not args.no_social
        )

        # Optional: rename output file
        if args.output:
            import shutil
            from pathlib import Path
            output_dir = Path(__file__).parent / "output"
            new_path = output_dir / args.output
            shutil.move(newsletter_path, new_path)
            newsletter_path = str(new_path)
            print(f"📧 Newsletter renamed to: {newsletter_path}")

        print()
        print("🎉 Newsletter generation successful!")
        print(f"📄 Newsletter: Open this file in your browser: {newsletter_path}")
        if bluesky_path:
            print(f"🐦 Bluesky thread: Open this file to copy social posts: {bluesky_path}")
        if social_path:
            print(f"📱 Social content: Open this file for LinkedIn/Blog content: {social_path}")

        # Send email if requested
        if args.send:
            print()
            print("📬 Sending newsletter via email...")
            from send_email import send_email, get_env_var

            try:
                smtp_email = get_env_var("SMTP_EMAIL")
                smtp_password = get_env_var("SMTP_PASSWORD")
                to_address = args.to or get_env_var("EMAIL_TO")

                success = send_email(
                    smtp_email=smtp_email,
                    smtp_password=smtp_password,
                    to_address=to_address,
                    attachment_path=newsletter_path
                )

                if not success:
                    print("⚠️  Email sending failed, but newsletter was generated successfully")
                    return 1

            except ValueError as e:
                print(f"❌ Email error: {e}")
                print("💡 Make sure SMTP_EMAIL, SMTP_PASSWORD, and EMAIL_TO are set in .env")
                return 1

        print()
        print("💡 Tips:")
        print("   - Set ANTHROPIC_API_KEY environment variable for Claude AI summaries")
        print("   - Use --send to email the newsletter after generation")
        print("   - Use --no-social to skip social content generation")
        print("   - Use --social-only to generate only social content (LinkedIn/Blog)")
        print("   - Run weekly for best results")

        return 0

    except KeyboardInterrupt:
        print("\n❌ Generation cancelled by user")
        return 1
    except Exception as e:
        print(f"\n❌ Error generating newsletter: {str(e)}")
        print("💡 Try running with --no-ai flag if Claude API issues persist")
        return 1

if __name__ == "__main__":
    sys.exit(main())