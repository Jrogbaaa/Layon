"use client";

import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from "recharts";
import type { ProfileSnapshot } from "@/app/lib/types";

export function FollowerChart({ history }: { history: ProfileSnapshot[] }) {
  const data = history.map((snapshot) => ({
    date: new Date(snapshot.captured_at).toLocaleDateString("en-US", { month: "short", day: "numeric" }),
    followers: snapshot.followers,
  }));

  if (data.length < 2) {
    return <p className="text-sm text-neutral-500">Not enough history yet to chart follower growth.</p>;
  }

  return (
    <ResponsiveContainer width="100%" height={220}>
      <LineChart data={data}>
        <CartesianGrid strokeDasharray="3 3" stroke="#262626" />
        <XAxis dataKey="date" stroke="#737373" fontSize={12} />
        <YAxis stroke="#737373" fontSize={12} width={60} />
        <Tooltip
          contentStyle={{ background: "#171717", border: "1px solid #404040", borderRadius: 8 }}
          labelStyle={{ color: "#e5e5e5" }}
        />
        <Line type="monotone" dataKey="followers" stroke="#f59e0b" strokeWidth={2} dot={false} />
      </LineChart>
    </ResponsiveContainer>
  );
}
