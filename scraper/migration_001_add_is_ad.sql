-- Migration: Add is_ad column to post_snapshots and top_posts view
alter table post_snapshots add column if not exists is_ad boolean not null default false;

drop view if exists top_posts;

create view top_posts as
select distinct on (influencer_id, shortcode)
  influencer_id, shortcode, post_type, likes, comments, views, caption, posted_at, is_ad,
  likes + comments as engagement
from post_snapshots
order by influencer_id, shortcode, (likes + comments) desc, captured_at desc;
