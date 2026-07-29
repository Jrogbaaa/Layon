-- Migration 003: Add index on post_snapshots (influencer_id, posted_at desc) for query performance

create index if not exists post_snapshots_influencer_posted_idx
  on post_snapshots (influencer_id, posted_at desc);
