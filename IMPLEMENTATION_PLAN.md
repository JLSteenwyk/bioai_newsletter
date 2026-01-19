# Expansion Roadmap

## Goals
- Broaden RSS coverage with reputable AI research and industry sources, including Thinking Machines.
- Layer additional community channels beyond Reddit to catch fast-moving conversations.
- Enrich trend heuristics so emerging AI themes surface reliably.

## Approach
1. **RSS Enhancements**: Audit `RSSNewsScraper.respected_sources`, add high-signal AI feeds (e.g., Anthropic blog RSS endpoint, DeepMind research, Thinking Machines, Stability AI, Meta AI, NVIDIA Research), and normalize metadata for faster additions later.
2. **Community Layer**: Introduce a lightweight aggregator for Hacker News and Bluesky/Tech/AI digests, exposing a new scraper module consumed by `NewsletterGenerator` alongside Reddit results.
3. **Trend Heuristics**: Update `trend_analyzer.py` to broaden keyword groups (alignment, generative media, robotics, governance) and tune weights/decay so newer stories and niche-but-growing topics rank higher.
4. **Validation**: Smoke-test individual scrapers (`python rss_scraper.py`, new community module) and ensure `NewsletterGenerator` integrates the combined dataset without regressions.

## Risks & Mitigations
- **API throttling**: Use polite timeouts and request caps; reuse existing delay helpers.
- **JSON inflation**: Keep per-source fetch limits reasonable and deduplicate overlapping stories.
- **Keyword noise**: Log scoring outputs when adjusting weights to avoid overfitting to buzzwords.
