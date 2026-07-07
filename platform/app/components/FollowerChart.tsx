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
      <p className="text-sm text-neutral-500">
        Collecting daily data — chart unlocks after {MIN_DAYS} daily scrapes ({dayCount} of {MIN_DAYS}).
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
        <CartesianGrid strokeDasharray="3 3" stroke="#262626" />
        <XAxis dataKey="date" stroke="#737373" fontSize={12} />
        <YAxis stroke="#737373" fontSize={12} width={60} tickFormatter={(v) => formatCount(v)} />
        <Tooltip
          contentStyle={{ background: "#171717", border: "1px solid #404040", borderRadius: 8 }}
          labelStyle={{ color: "#e5e5e5" }}
          formatter={(value) => [typeof value === "number" ? value.toLocaleString() : value, "Followers"]}
        />
        <Line type="monotone" dataKey="followers" stroke="#f59e0b" strokeWidth={2} dot={false} />
      </LineChart>
    </ResponsiveContainer>
  );
}
