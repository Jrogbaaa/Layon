"use client";

import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from "recharts";
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

  return (
    <ResponsiveContainer width="100%" height={220}>
      <LineChart data={data}>
        <defs>
          <linearGradient id="followerLine" x1="0" y1="0" x2="1" y2="0">
            <stop offset="0%" stopColor="#18c8a8" />
            <stop offset="100%" stopColor="#2e8ff0" />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke="#e1e7ed" />
        <XAxis dataKey="date" stroke="#5b6675" fontSize={12} />
        <YAxis stroke="#5b6675" fontSize={12} width={60} tickFormatter={(v) => formatCount(v)} />
        <Tooltip
          contentStyle={{ background: "#ffffff", border: "1px solid #e1e7ed", borderRadius: 8 }}
          labelStyle={{ color: "#12181f" }}
          formatter={(value) => [typeof value === "number" ? value.toLocaleString() : value, "Followers"]}
        />
        <Line type="monotone" dataKey="followers" stroke="url(#followerLine)" strokeWidth={2.5} dot={false} />
      </LineChart>
    </ResponsiveContainer>
  );
}
