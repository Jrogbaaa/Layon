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
  unique (influencer_id, shortcode, captured_at)
);

create index if not exists post_snapshots_influencer_captured_idx
  on post_snapshots (influencer_id, captured_at desc);

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

create table if not exists post_content (
  id bigint generated always as identity primary key,
  influencer_id bigint not null references influencers(id) on delete cascade,
  shortcode text not null,
  summary text not null,
  analysis jsonb not null,
  analyzed_at timestamptz not null default now(),
  unique (influencer_id, shortcode)
);
