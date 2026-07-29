-- You First Gersh Influencer Insights Platform — Supabase schema
-- Run this once against a new Supabase project (SQL Editor, or `supabase db push`).

create table if not exists influencers (
  id bigint generated always as identity primary key,
  handle text not null unique,
  display_name text,
  persona text,
  avatar_url text,
  active boolean not null default true,
  created_at timestamptz not null default now()
);

alter table influencers add column if not exists avatar_url text;

create table if not exists talent_strategies (
  influencer_id bigint primary key references influencers(id) on delete cascade,
  current_objective text not null default '',
  horizon date,
  target_audience text not null default '',
  content_pillars jsonb not null default '[]'::jsonb,
  development_formats jsonb not null default '[]'::jsonb,
  tone text not null default '',
  guardrails text not null default '',
  commercial_direction text not null default '',
  posting_constraints text not null default '',
  updated_at timestamptz not null default now(),
  reviewed_at timestamptz not null default now()
);

create table if not exists profile_snapshots (
  id bigint generated always as identity primary key,
  influencer_id bigint not null references influencers(id) on delete cascade,
  followers integer not null,
  following integer not null,
  media_count integer not null,
  bio text,
  captured_at timestamptz not null default now()
);

create index if not exists profile_snapshots_influencer_captured_idx
  on profile_snapshots (influencer_id, captured_at desc);

create table if not exists post_snapshots (
  id bigint generated always as identity primary key,
  influencer_id bigint not null references influencers(id) on delete cascade,
  shortcode text not null,
  post_type text not null check (post_type in ('photo', 'video', 'reel', 'carousel')),
  likes integer not null,
  comments integer not null,
  views integer,
  caption text,
  posted_at timestamptz not null,
  captured_at timestamptz not null default now(),
  is_ad boolean not null default false,
  unique (influencer_id, shortcode, captured_at)
);

create index if not exists post_snapshots_influencer_captured_idx
  on post_snapshots (influencer_id, captured_at desc);

create index if not exists post_snapshots_influencer_posted_idx
  on post_snapshots (influencer_id, posted_at desc);

create table if not exists trend_snapshots (
  id bigint generated always as identity primary key,
  source_url text not null,
  title text,
  content_text text not null,
  captured_at timestamptz not null default now()
);

create index if not exists trend_snapshots_source_captured_idx
  on trend_snapshots (source_url, captured_at desc);

create table if not exists recommendations (
  id bigint generated always as identity primary key,
  influencer_id bigint not null references influencers(id) on delete cascade,
  generated_at timestamptz not null default now(),
  model text not null,
  content text not null
);

create index if not exists recommendations_influencer_generated_idx
  on recommendations (influencer_id, generated_at desc);

create table if not exists recommendation_actions (
  id bigint generated always as identity primary key,
  recommendation_id bigint not null references recommendations(id) on delete cascade,
  influencer_id bigint not null references influencers(id) on delete cascade,
  bullet_index smallint not null check (bullet_index between 0 and 20),
  decision text not null check (
    decision in ('try', 'not_relevant', 'already_planned', 'talent_declined', 'revisit')
  ),
  shared_note text not null default '',
  revisit_on date,
  experiment_status text check (
    experiment_status is null or experiment_status in ('planned', 'published', 'evaluated', 'abandoned')
  ),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (recommendation_id, bullet_index)
);

create index if not exists recommendation_actions_influencer_updated_idx
  on recommendation_actions (influencer_id, updated_at desc);

alter table recommendation_actions add column if not exists linked_shortcode text;
alter table recommendation_actions add column if not exists published_at timestamptz;
alter table recommendation_actions add column if not exists review_at timestamptz;
alter table recommendation_actions add column if not exists baseline jsonb;
alter table recommendation_actions add column if not exists outcome jsonb;
alter table recommendation_actions add column if not exists evaluated_at timestamptz;
alter table recommendation_actions add column if not exists acknowledged_at timestamptz;

create index if not exists recommendation_actions_due_idx
  on recommendation_actions (experiment_status, review_at)
  where experiment_status = 'published';

create table if not exists post_strategy_tags (
  id bigint generated always as identity primary key,
  influencer_id bigint not null references influencers(id) on delete cascade,
  shortcode text not null,
  pillar text,
  source text not null check (source in ('automatic', 'manual')),
  strategy_updated_at timestamptz,
  removed_pillar boolean not null default false,
  tagged_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (influencer_id, shortcode)
);

create index if not exists post_strategy_tags_influencer_updated_idx
  on post_strategy_tags (influencer_id, updated_at desc);

create table if not exists highlights (
  id bigint generated always as identity primary key,
  influencer_id bigint not null references influencers(id) on delete cascade,
  content text not null,
  metric jsonb not null,
  captured_at timestamptz not null default now()
);

create index if not exists highlights_influencer_captured_idx
  on highlights (influencer_id, captured_at desc);

create table if not exists roster_briefings (
  id bigint generated always as identity primary key,
  generated_at timestamptz not null default now(),
  model text not null,
  content jsonb not null
);

create index if not exists roster_briefings_generated_idx
  on roster_briefings (generated_at desc);

alter table roster_briefings add column if not exists period_start date;
alter table roster_briefings add column if not exists period_end date;

create unique index if not exists roster_briefings_period_start_unique_idx
  on roster_briefings (period_start)
  where period_start is not null;

create table if not exists post_content (
  id bigint generated always as identity primary key,
  influencer_id bigint not null references influencers(id) on delete cascade,
  shortcode text not null,
  summary text not null,
  analysis jsonb not null,
  analyzed_at timestamptz not null default now(),
  unique (influencer_id, shortcode)
);

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

-- All-time best snapshot per (influencer, post): dedupes daily captures by
-- shortcode, keeping the capture with the highest engagement.
create index if not exists post_snapshots_influencer_shortcode_idx
  on post_snapshots (influencer_id, shortcode);

create or replace view top_posts as
select distinct on (influencer_id, shortcode)
  influencer_id, shortcode, post_type, likes, comments, views, caption, posted_at, is_ad,
  likes + comments as engagement
from post_snapshots
order by influencer_id, shortcode, (likes + comments) desc, captured_at desc;

create table if not exists trend_headlines (
  id bigint generated always as identity primary key,
  generated_at timestamptz not null default now(),
  model text not null,
  content jsonb not null
);

create index if not exists trend_headlines_generated_idx
  on trend_headlines (generated_at desc);
