export type Influencer = {
  id: number;
  handle: string;
  display_name: string | null;
};

export type ProfileSnapshot = {
  followers: number;
  following: number;
  media_count: number;
  bio: string | null;
  captured_at: string;
};

export type PostSnapshot = {
  shortcode: string;
  post_type: "photo" | "video" | "reel" | "carousel";
  likes: number;
  comments: number;
  views: number | null;
  caption: string | null;
  posted_at: string;
};

export type Highlight = {
  content: string;
  metric: Record<string, unknown>;
  captured_at: string;
};

export type TrendSnapshot = {
  source_url: string;
  title: string | null;
  content_text: string;
  captured_at: string;
};

export type Recommendation = {
  generated_at: string;
  model: string;
  content: string;
};

export type RosterEntry = {
  influencer: Influencer;
  latestSnapshot: ProfileSnapshot | null;
  followerDelta: number;
  recentHighlights: Highlight[];
};

export type InfluencerDashboard = {
  influencer: Influencer;
  profileHistory: ProfileSnapshot[];
  recentPosts: PostSnapshot[];
  latestRecommendation: Recommendation | null;
  highlights: Highlight[];
};
