# Spec - Post Engagement Performance Chart & Audience Log

## Goal of This Change

Replace the follower growth chart on the influencer dashboard with an interactive **Post Engagement Performance** chart showing Likes + Comments across the last 30 posts, and add a clean **Audience Log (Last 7 Days)** grid showing exact daily follower numbers and changes.

1. **Split Backend Post Queries:** Modify `getInfluencerDashboard` in `platform/app/lib/data.ts` to return:
   - `recentPosts`: sliced to the latest 12 posts (newest first) for the logs and greatest hits table.
   - `chartPosts`: sliced to the latest 30 posts and reversed (oldest of the 30 first, newest last) for correct left-to-right chronological rendering in the chart.
2. **Create EngagementChart Component:** Build `platform/app/components/EngagementChart.tsx` using Recharts to plot total engagement (Likes + Comments) with a horizontal median reference line and custom tooltips showing engagement rates, formatting, and caption snippets.
3. **Add Audience Log Grid:** In `platform/app/(app)/influencer/[handle]/page.tsx`, compute daily follower changes from `profileHistory` using `dailyHistory` and render a responsive grid showing the last 7 days of daily follower sizes and delta fluctuations.
4. **Delete Unused Component:** Remove `platform/app/components/FollowerChart.tsx`.

## Why This Matters

Since the project began scraping on July 6, the database only holds ~11 days of follower snapshots. A follower growth chart remains very short and has little visual detail. However, the database contains complete post snapshots extending back months and years, meaning a post-level engagement chart is immediately rich and deeply useful for both creators and agency managers scanning for content virality. Adding a numerical log maintains full visibility over exact follower growth/decline.

## Non-Goals

- No database backfills or synthetic follower generation.
- No changes to the scraper logic, database schemas, or scheduling.

## Success Criteria

1. `getInfluencerDashboard` returns `chartPosts` with up to 30 deduplicated posts sorted oldest-first.
2. `EngagementChart` renders correctly using Gilded Amber tokens, displays median engagement, and shows ER% in tooltips.
3. `AUDIENCE LOG` grid displays daily follower sizes and changes (+/-) correctly for the last 7 active days.
4. Next.js dashboard compiles, lints, and loads successfully.
5. Playwright test suite passes.
