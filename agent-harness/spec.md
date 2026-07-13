# Spec - Social Media Platform Trend Sources (feature_011)

## Goal of This Change

Replace the general news RSS feeds in `config.TREND_SOURCES` with official, actionable social media platform trend reports and format statistics (TikTok Next and Metricool) to guide influencer content recommendations.

## Why This Matters

The previous news RSS feeds captured general daily news events (which were "things that happened" rather than social media formats/strategies, e.g., "Anthony Hopkins is becoming a composer"). Managers need real social media trends (like carousel performance stats, hooks, and TikTok's Dose of Reality) to advise creators.

## Success Criteria

1. `config.TREND_SOURCES` contains:
   - `https://ads.tiktok.com/business/es-LA/next` (TikTok Next official trend report in Spanish)
   - `https://metricool.com/es/tendencias-instagram/` (Metricool Instagram trends report in Spanish)
   - `https://metricool.com/es/tendencias-estrategias-tiktok/` (Metricool TikTok trends report in Spanish)
2. `trend_headlines.build_prompt` instructions are updated to expect platform creative trend reports, format statistics, and strategic forecasts for TikTok and Instagram, rather than general news.
3. Example headlines in the prompt are adjusted to focus on social media tactics/data (e.g., "Carousels outperform Reels").
4. pytest is green including updated config and prompt assertions (145/145 passing).
5. A live database run successfully pulls real-time social platform metrics from these new HTML sources and writes distilled headlines to Supabase.
