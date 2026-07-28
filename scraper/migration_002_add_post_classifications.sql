-- Migration: Add post_classifications for evidence-backed paid media decisions
create table if not exists post_classifications (
  id bigint generated always as identity primary key,
  influencer_id bigint not null references influencers(id) on delete cascade,
  shortcode text not null,
  status text not null check (status in ('paid', 'organic', 'needs_review')),
  decision_code text not null,
  evidence jsonb not null,
  classifier_version text not null,
  input_hash text not null,
  classified_at timestamptz not null default now(),
  unique (influencer_id, shortcode)
);

create index if not exists post_classifications_influencer_classified_idx
  on post_classifications (influencer_id, classified_at desc);
