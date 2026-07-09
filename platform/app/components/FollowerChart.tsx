"use client";

import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from "recharts";
import type { ProfileSnapshot } from "@/app/lib/types";
import { dailyHistory, formatCount } from "@/app/lib/metrics";

const MIN_DAYS = 3;

export function FollowerChart({ history }: { history: ProfileSnapshot[] }) {
  const daily = dailyHistory(history);
  const dayCount = daily.length;

  if (dayCount < MIN_DAYS) {
    return (
      <p className="text-sm text-muted">
        Collecting daily data — the trend chart appears after {MIN_DAYS} days of tracking ({dayCount} of{" "}
        {MIN_DAYS} so far).
      </p>
    );
  }

  const data = daily.map((snapshot) => ({
    date: new Date(snapshot.captured_at).toLocaleDateString("en-US", { month: "short", day: "numeric" }),
    followers: snapshot.followers,
  }));

  // Tight ranges (a few hundred followers on a millions-scale account) collapse
  // to identical compact ticks — fall back to exact numerals there.
  const values = data.map((d) => d.followers);
  const span = Math.max(...values) - Math.min(...values);
  const tight = span < Math.max(...values) * 0.01;
  const tick = (v: number): string => (tight ? v.toLocaleString("en-US") : formatCount(v));

  return (
    <ResponsiveContainer width="100%" height={260}>
      <AreaChart data={data} margin={{ top: 8, right: 28, bottom: 0, left: 0 }}>
        <defs>
          <linearGradient id="followerFill" x1="0" y1="0" x2="0" y2="1">
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
          width={tight ? 84 : 56}
          tickLine={false}
          axisLine={false}
          domain={["dataMin", "dataMax"]}
          tickFormatter={tick}
        />
        <Tooltip
          contentStyle={{
            background: "#241819",
            border: "1px solid #362527",
            borderRadius: 8,
            fontFamily: "var(--font-mono)",
            fontSize: 12,
          }}
          labelStyle={{ color: "#f4ede2" }}
          itemStyle={{ color: "#e3b04b" }}
          formatter={(value) => [typeof value === "number" ? value.toLocaleString("en-US") : value, "Followers"]}
        />
        <Area
          type="monotone"
          dataKey="followers"
          stroke="#e3b04b"
          strokeWidth={2}
          fill="url(#followerFill)"
          dot={false}
          activeDot={{ r: 3.5, fill: "#f0c96a", stroke: "#120b0d", strokeWidth: 2 }}
        />
      </AreaChart>
    </ResponsiveContainer>
  );
}
