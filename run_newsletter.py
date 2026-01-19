#!/usr/bin/env python3
"""
AI Newsletter Generator - Main Script

This script generates a weekly AI newsletter by:
1. Scraping respected AI news sources (RSS feeds)
2. Collecting community sentiment from Reddit
3. Analyzing trending topics
4. Creating AI-powered summaries
5. Generating a beautiful HTML newsletter

Usage:
    python run_newsletter.py

Environment Variables:
    ANTHROPIC_API_KEY: Your Anthropic API key for Claude AI summarization (optional)

Output:
    - HTML newsletter file
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
                       help='Skip Bluesky thread generation')
    
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
        
        # Generate newsletter and optionally Bluesky thread
        newsletter_path, bluesky_path = generator.generate_weekly_newsletter(
            days_back=args.days, 
            generate_social=not args.no_social
        )
        
        # Optional: rename output file
        if args.output:
            import shutil
            new_path = f"/Users/jacoblsteenwyk/Desktop/BUSINESS/AI_NEWS/{args.output}"
            shutil.move(newsletter_path, new_path)
            newsletter_path = new_path
            print(f"📧 Newsletter renamed to: {newsletter_path}")
        
        print()
        print("🎉 Newsletter generation successful!")
        print(f"📄 Newsletter: Open this file in your browser: {newsletter_path}")
        if bluesky_path:
            print(f"🐦 Bluesky thread: Open this file to copy social posts: {bluesky_path}")
        print()
        print("💡 Tips:")
        print("   - Set ANTHROPIC_API_KEY environment variable for Claude AI summaries")
        print("   - Use --no-social to skip Bluesky thread generation")
        print("   - Run weekly for best results")
        print("   - Check the generated JSON files for raw data")
        
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