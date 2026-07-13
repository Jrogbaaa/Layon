# Spec - Rolling 30-Day Growth Chart Correction

## Goal of This Change

Fix the query sorting bug for follower history on the influencer dashboard to correctly display the rolling past month (latest 30 days of data) in chronological order.

1. **Correct Database Query Sorting:** Modify `getInfluencerDashboard` in `platform/app/lib/data.ts` to order by `captured_at` descending and limit to 30, retrieving the latest 30 snapshots instead of the oldest 30 snapshots.
2. **Reverse for Chronological Display:** Reverse the retrieved snapshots list in-memory so they are ordered chronologically ascending for rendering in the line/area chart.
3. **No Synthetic Backfilling:** Do not insert estimated or synthetic follower counts into the database (per user decision). Allow data to accumulate naturally through daily scrapes.

## Why This Matters

Currently, `getInfluencerDashboard` selects the first 30 snapshots ever captured (ordered by `captured_at` ascending and limited to 30). This is a query bug; once there are more than 30 days of scraped data, the dashboard will display the initial 30 days of the project forever and never show new daily growth. Reversing the sorting and limits ensures a rolling window of the past month of exact data is shown.

## Non-Goals

- No synthetic data generation or database backfills.
- No changes to the scraper logic or database schema.

## Success Criteria

1. `getInfluencerDashboard` queries `profile_snapshots` table ordered by `captured_at` descending with limit 30.
2. The query output `profileHistory` is reversed in-memory before returning.
3. Next.js dashboard compiles, lints, and loads successfully.
4. Playwright test suite passes.
