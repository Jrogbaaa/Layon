export type Influencer = {
  id: number;
  handle: string;
  display_name: string | null;
  avatar_url: string | null;
};

export type TalentStrategy = {
  influencer_id: number;
  current_objective: string;
  horizon: string | null;
  target_audience: string;
  content_pillars: string[];
  development_formats: PostSnapshot["post_type"][];
  tone: string;
  guardrails: string;
  commercial_direction: string;
  posting_constraints: string;
  updated_at: string;
  reviewed_at: string;
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
  id: number;
  generated_at: string;
  model: string;
  content: string;
};

export type RecommendationDecision =
  | "try"
  | "not_relevant"
  | "already_planned"
  | "talent_declined"
  | "revisit";

export type RecommendationAction = {
  id: number;
  recommendation_id: number;
  influencer_id: number;
  bullet_index: number;
  decision: RecommendationDecision;
  shared_note: string;
  revisit_on: string | null;
  experiment_status: "planned" | "published" | "evaluated" | "abandoned" | null;
  linked_shortcode: string | null;
  published_at: string | null;
  review_at: string | null;
  baseline: ContentExperimentOutcome["baseline"] | null;
  outcome: ContentExperimentOutcome | null;
  evaluated_at: string | null;
  acknowledged_at: string | null;
  created_at: string;
  updated_at: string;
};

export type ExperimentConfidence = "insufficient" | "directional" | "strong";

export type ContentExperimentOutcome = {
  target: { interactions: number; views: number | null; captured_at: string };
  baseline: {
    interactions_median: number | null;
    views_median: number | null;
    sample_size: number;
    cohort: "format_paid_pillar" | "format_paid";
    post_type: PostSnapshot["post_type"];
    paid_status: PostClassificationStatus;
    pillar: string | null;
  };
  interaction_delta_pct: number | null;
  views_delta_pct: number | null;
  confidence: ExperimentConfidence;
  disclaimer: string;
};

export type PostStrategyTag = {
  id: number;
  influencer_id: number;
  shortcode: string;
  pillar: string | null;
  source: "automatic" | "manual";
  strategy_updated_at: string | null;
  removed_pillar: boolean;
  tagged_at: string;
  updated_at: string;
};

export type PillarPerformance = {
  pillar: string;
  paidStatus: PostClassificationStatus;
  interactionsMedian: number;
  viewsMedian: number | null;
  sampleSize: number;
  confidence: ExperimentConfidence;
};

export type AttentionPriority = {
  kind: "missing_data" | "stale_data" | "review_experiment" | "warning" | "active_experiment" | "recommendation" | "none";
  priority: number;
  label: Bilingual;
  detail: Bilingual | null;
};

export type TopPost = PostSnapshot & { engagement: number };

export type Bilingual = { en: string; es: string };

export type RosterBriefing = {
  generated_at: string;
  model: string;
  content: string | Record<string, unknown>;
  period_start: string | null;
  period_end: string | null;
};

export type BriefingPayload = {
  summary: Bilingual;
  patterns: { finding: Bilingual; evidence: string; handles: string[] }[];
  actions: { handle: string; action: Bilingual; reason: Bilingual; shortcode: string | null }[];
};

export type WeeklyReviewItem = {
  title: Bilingual;
  handles: string[];
  metric: string | null;
  shortcode: string | null;
};

export type WeeklyReviewPayload = {
  top_priorities: WeeklyReviewItem[];
  strongest_creative_win: WeeklyReviewItem | null;
  primary_risk: WeeklyReviewItem | null;
  experiments: { due: WeeklyReviewItem[]; recently_evaluated: WeeklyReviewItem[] };
  stale_strategies: { handle: string; status: Bilingual }[];
  suggested_conversations: {
    handle: string;
    topic: Bilingual;
    reason: Bilingual;
    metric: string | null;
    shortcode: string | null;
  }[];
};

export type PortfolioKpis = {
  rosterSize: number;
  strategyProfiles: number;
  unresolvedRecommendations: number;
  activeExperiments: number;
  evaluatedExperiments: number;
  experimentHits: number;
  experimentHitRate: number | null;
};

export type RosterEntry = {
  influencer: Influencer;
  latestSnapshot: ProfileSnapshot | null;
  followerDelta: number;
  recentHighlights: Highlight[];
  /** Recent snapshots, oldest→newest, for the roster sparkline. */
  history: ProfileSnapshot[];
  nextAction: AttentionPriority;
};

export type InfluencerDashboard = {
  influencer: Influencer;
  profileHistory: ProfileSnapshot[];
  recentPosts: PostSnapshot[];
  chartPosts: PostSnapshot[];
  latestRecommendation: Recommendation | null;
  recommendationActions: RecommendationAction[];
  nextAction: AttentionPriority;
  postStrategyTags: PostStrategyTag[];
  pillarPerformance: PillarPerformance[];
  strategy: TalentStrategy | null;
  highlights: Highlight[];
  topPosts: TopPost[];
};
