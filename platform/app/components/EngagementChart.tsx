"use client";

import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, ReferenceLine } from "recharts";
import type { PostSnapshot } from "@/app/lib/types";
import { formatCount } from "@/app/lib/metrics";

type EngagementChartProps = {
  posts: PostSnapshot[];
  followers: number;
};

interface TooltipPayloadItem {
  payload: {
    date: string;
    format: string;
    engagement: number;
    likes: number;
    comments: number;
    er: number;
    caption: string;
  };
}

interface CustomTooltipProps {
  active?: boolean;
  payload?: TooltipPayloadItem[];
}

// Custom tooltips to show format, likes, comments, ER% and caption context
function CustomTooltip({ active, payload }: CustomTooltipProps) {
  if (active && payload && payload.length) {
    const d = payload[0].payload;
    return (
      <div className="border border-border-faint bg-[#241819] p-3 rounded-lg text-xs font-mono">
        <p className="text-[#f4ede2] font-bold mb-2">
          {d.date} · <span className="capitalize">{d.format}</span>
        </p>
        <p className="text-accent font-semibold">Engagement: {d.engagement.toLocaleString()}</p>
        <p className="text-faint mt-1">
          Likes: {d.likes.toLocaleString()} · Comments: {d.comments.toLocaleString()}
        </p>
        <p className="text-accent mt-1">ER: {d.er}%</p>
        {d.caption && (
          <p className="text-muted mt-2 border-t border-border-faint pt-2 text-[10px] line-clamp-2 max-w-[220px]">
            &ldquo;{d.caption}&rdquo;
          </p>
        )}
      </div>
    );
  }
  return null;
}

export function EngagementChart({ posts, followers }: EngagementChartProps) {
  if (posts.length === 0) {
    return <p className="text-sm text-muted">No post engagement data yet.</p>;
  }

  // Calculate engagement (likes + comments) and median engagement
  const sortedEngagement = posts
    .map((p) => p.likes + p.comments)
    .sort((a, b) => a - b);

  let median = 0;
  if (sortedEngagement.length > 0) {
    const mid = Math.floor(sortedEngagement.length / 2);
    median =
      sortedEngagement.length % 2 !== 0
        ? sortedEngagement[mid]
        : (sortedEngagement[mid - 1] + sortedEngagement[mid]) / 2;
  }

  const data = posts.map((post) => {
    const engagement = post.likes + post.comments;
    const er = followers > 0 ? (engagement / followers) * 100 : 0;
    return {
      date: new Date(post.posted_at).toLocaleDateString("en-US", { month: "short", day: "numeric" }),
      engagement,
      likes: post.likes,
      comments: post.comments,
      er: Math.round(er * 100) / 100,
      format: post.post_type,
      caption: post.caption || "",
    };
  });

  const values = data.map((d) => d.engagement);
  const maxVal = Math.max(...values, 0);

  return (
    <ResponsiveContainer width="100%" height={260}>
      <AreaChart data={data} margin={{ top: 12, right: 28, bottom: 0, left: 0 }}>
        <defs>
          <linearGradient id="engagementFill" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#e3b04b" stopOpacity={0.28} />
            <stop offset="60%" stopColor="#7e2230" stopOpacity={0.12} />
            <stop offset="100%" stopColor="#7e2230" stopOpacity={0} />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="2 6" stroke="#362527" vertical={false} />
        <XAxis
          dataKey="date"
          stroke="#97897f"
          fontSize={11}
          fontFamily="var(--font-mono)"
          tickLine={false}
          axisLine={{ stroke: "#362527" }}
        />
        <YAxis
          stroke="#97897f"
          fontSize={11}
          fontFamily="var(--font-mono)"
          width={56}
          tickLine={false}
          axisLine={false}
          domain={[0, maxVal * 1.1]}
          tickFormatter={formatCount}
        />
        <Tooltip content={<CustomTooltip />} cursor={{ stroke: "#362527", strokeWidth: 1 }} />
        <ReferenceLine
          y={median}
          stroke="#7e2230"
          strokeDasharray="4 4"
          label={{
            value: `Median: ${formatCount(median)}`,
            fill: "#97897f",
            position: "top",
            fontSize: 10,
            fontFamily: "var(--font-mono)",
          }}
        />
        <Area
          type="monotone"
          dataKey="engagement"
          stroke="#e3b04b"
          strokeWidth={2}
          fill="url(#engagementFill)"
          dot={false}
          activeDot={{ r: 3.5, fill: "#f0c96a", stroke: "#120b0d", strokeWidth: 2 }}
        />
      </AreaChart>
    </ResponsiveContainer>
  );
}
