export type Influencer = {
  id: number;
  handle: string;
  display_name: string | null;
  avatar_url: string | null;
};

export type PostClassificationStatus = "paid" | "organic" | "needs_review";

export type PostClassification = {
  status: PostClassificationStatus;
  decision_code: string;
  evidence: {
    caption_mentions: string[];
    tagged_users: string[];
    sponsor_users: string[];
    caption_brand_mentions: { text: string; reason: string }[];
    tagged_accounts: {
      username: string;
      account_type: "person" | "commercial_brand" | "noncommercial_org" | "unknown";
      reason: string;
    }[];
    visual_brand_mentions: {
      name: string;
      prominence: "central" | "incidental" | "unknown";
      reason: string;
    }[];
    disclosure_terms: string[];
    incidental_visual_brand: boolean;
    summary: string | null;
  };
  classifier_version: string;
  input_hash: string;
  classified_at: string;
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
  is_ad?: boolean;
  classification?: PostClassification | null;
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

export type TrendHeadlines = {
  generated_at: string;
  model: string;
  content: string;
};

export type TrendHeadlinesPayload = {
  headlines: { text: Bilingual; source_url: string | null }[];
};

export type Recommendation = {
  generated_at: string;
  model: string;
  content: string;
};

export type TopPost = PostSnapshot & { engagement: number };

export type Bilingual = { en: string; es: string };

export type RosterBriefing = {
  generated_at: string;
  model: string;
  content: string;
};

export type BriefingPayload = {
  summary: Bilingual;
  patterns: { finding: Bilingual; evidence: string; handles: string[] }[];
  actions: { handle: string; action: Bilingual; reason: Bilingual; shortcode: string | null }[];
};

export type RosterEntry = {
  influencer: Influencer;
  latestSnapshot: ProfileSnapshot | null;
  followerDelta: number;
  recentHighlights: Highlight[];
  /** Recent snapshots, oldest→newest, for the roster sparkline. */
  history: ProfileSnapshot[];
};

export type InfluencerDashboard = {
  influencer: Influencer;
  profileHistory: ProfileSnapshot[];
  recentPosts: PostSnapshot[];
  chartPosts: PostSnapshot[];
  latestRecommendation: Recommendation | null;
  highlights: Highlight[];
  topPosts: TopPost[];
};
