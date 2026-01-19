# BioAI Weekly Newsletter Generator

Automatically scrape top biology and AI intersection news stories and generate beautiful weekly newsletters covering computational biology, AI-driven research, and community discussions.

## Features

🔬 **Research Frontiers** - Latest discoveries from Nature, Science, PLOS, bioRxiv, and leading research institutions
🧬 **Community Insights** - Discussions from r/bioinformatics, r/MachineLearning, and biology research communities
📈 **Trending Topics** - Cross-platform analysis of what's hot in biology+AI intersection
🤖 **AI-Powered Summaries** - Blog-style paragraphs covering computational biology breakthroughs
🔗 **Citation Links** - All summaries include numbered citations with clickable source links
🐦 **Bluesky Thread Generator** - Automatic social media posts for newsletter promotion  

## Quick Start

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set Anthropic API key (optional but recommended):**
   ```bash
   export ANTHROPIC_API_KEY="your-api-key-here"
   ```

3. **Generate newsletter:**
   ```bash
   python run_newsletter.py
   ```

4. **Open the generated HTML file in your browser!**

## Output Example

The system generates a professional HTML newsletter with sections like:

- **Research Frontiers**: "AlphaFold3 achieves breakthrough accuracy in protein-ligand interactions [1]. New deep learning models predict drug-target binding with 95% accuracy [2]..."

- **Community Insights**: "The r/bioinformatics community is discussing the latest CRISPR-AI integration [3], with researchers sharing successful applications in gene therapy [4]..."

- **Trending This Week**: "#ProteinFolding - 52 mentions across platforms with very positive research sentiment 🧬"
  
  **Sources:**
  - [1] OpenAI Blog: GPT-5 Release - Link
  - [2] ArXiv AI: Performance Analysis - Link
  - [3] r/MachineLearning: Community Discussion - Link

## Configuration

### Command Line Options
```bash
python run_newsletter.py --help
```

- `--days 7` - Days back to scrape (default: 7)
- `--output filename.html` - Custom output filename  
- `--no-ai` - Disable AI summarization
- `--no-social` - Skip Bluesky thread generation

### Data Sources

**Research Sources (RSS):**
- Nature Computational Biology
- Nature Biotechnology & Methods
- Science Magazine
- PLOS Computational Biology
- Cell Press
- Bioinformatics Journal
- bioRxiv Bioinformatics
- ArXiv Quantitative Biology
- MIT AI News (biology applications)

**Community Sources (Reddit):**
- r/bioinformatics
- r/computational_biology
- r/biology
- r/MachineLearning
- r/genetics
- r/datascience
- r/labrats
- r/AskScience

## Architecture

The system consists of modular components:

1. **`rss_scraper.py`** - Scrapes RSS feeds from respected AI sources
2. **`reddit_scraper.py`** - Collects community posts and sentiment
3. **`trend_analyzer.py`** - Identifies trending topics across platforms
4. **`summarizer.py`** - Generates AI-powered blog-style summaries
5. **`newsletter_generator.py`** - Orchestrates everything and creates HTML output
6. **`run_newsletter.py`** - Main entry point

## Advanced Usage

### Running Individual Components

```bash
# Just scrape RSS feeds
python rss_scraper.py

# Just scrape Reddit  
python reddit_scraper.py

# Analyze trends from existing data
python trend_analyzer.py
```

### Custom Time Ranges

```bash
# Last 3 days only
python run_newsletter.py --days 3

# Last 2 weeks
python run_newsletter.py --days 14
```

### Without AI Summarization

If you don't have an Anthropic API key:

```bash
python run_newsletter.py --no-ai
```

This uses fallback summaries from original source descriptions.

## Output Files

Each run generates:

- `ai_weekly_YYYYMMDD.html` - Main newsletter
- `bluesky_thread_YYYYMMDD.html` - Social media thread posts (with copy buttons)
- `rss_articles_YYYYMMDD_HHMMSS.json` - Raw RSS data
- `reddit_posts_YYYYMMDD_HHMMSS.json` - Raw Reddit data  
- `trend_report_YYYYMMDD_HHMMSS.json` - Trend analysis

## Troubleshooting

**No articles found:**
- Check internet connection
- Some RSS feeds may be temporarily down
- Try increasing `--days` parameter

**AI summarization not working:**
- Verify ANTHROPIC_API_KEY is set correctly
- Check API key has sufficient credits
- Use `--no-ai` flag as fallback

**Rate limiting errors:**
- The system includes delays between requests
- Reddit scraping is limited to prevent blocks
- Try running at different times

## Customization

### Adding New Sources

Edit the source dictionaries in:
- `rss_scraper.py` - Add new biology/computational biology RSS feeds
- `reddit_scraper.py` - Add new biology and AI research subreddits

### Changing Newsletter Style

Modify the HTML template in:
- `newsletter_generator.py` - Update CSS and layout for biology focus

### Adjusting Trend Detection

Tune parameters in:
- `trend_analyzer.py` - Modify biology+AI keyword groups and weights

## License

Open source - feel free to modify and adapt for your needs!