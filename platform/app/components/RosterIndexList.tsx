"use client";

import { useState } from "react";
import Link from "next/link";
import { ViewTransition } from "react";
import { Avatar } from "@/app/components/Avatar";
import { Sparkline } from "@/app/components/Sparkline";
import { Reveal } from "@/app/components/Reveal";
import type { RosterEntry } from "@/app/lib/types";

type RosterIndexListProps = {
  initialRoster: RosterEntry[];
};

export function RosterIndexList({ initialRoster }: RosterIndexListProps) {
  const [sortBy, setSortBy] = useState<"audience" | "delta" | "name">("audience");

  // Sorting
  const sorted = [...initialRoster].sort((a, b) => {
    if (sortBy === "audience") {
      return (b.latestSnapshot?.followers ?? 0) - (a.latestSnapshot?.followers ?? 0);
    }
    if (sortBy === "delta") {
      return b.followerDelta - a.followerDelta;
    }
    const nameA = a.influencer.display_name ?? a.influencer.handle;
    const nameB = b.influencer.display_name ?? b.influencer.handle;
    return nameA.localeCompare(nameB);
  });

  return (
    <section className="space-y-6">
      {/* Controls Bar */}
      <div className="flex justify-end rounded-lg border border-border-faint bg-surface p-4">
        <div className="flex items-center gap-2 text-sm">
          <span className="text-faint font-mono text-xs">SORT:</span>
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value as "audience" | "delta" | "name")}
            className="bg-transparent text-ink border-b border-border-faint outline-none py-1 cursor-pointer hover:border-accent focus:border-accent transition-colors font-mono text-xs"
          >
            <option value="audience" className="bg-surface">AUDIENCE SIZE</option>
            <option value="delta" className="bg-surface">OVERNIGHT GROWTH</option>
            <option value="name" className="bg-surface">ALPHABETICAL</option>
          </select>
        </div>
      </div>

      {/* Index List */}
      <div>
        <h2 className="font-mono mb-4 text-xs tracking-widest text-faint">
          TONIGHT&apos;S INDEX · {sorted.length} RENDERED
        </h2>

        {sorted.length === 0 ? (
          <p className="text-sm text-muted p-4 border border-border-faint rounded-lg bg-surface">
            No talent matches the current filters.
          </p>
        ) : (
          <div className="panel overflow-hidden">
            {/* Table Header (Desktop Only) */}
            <div className="hidden sm:grid sm:grid-cols-[2.5rem_3rem_minmax(0,1fr)_8rem_9rem_8.5rem] items-center gap-x-4 border-b border-border-faint px-7 py-3 font-mono text-[10px] tracking-wider text-faint bg-canvas-deep/40">
              <span>RANK</span>
              <span className="col-span-2">TALENT</span>
              <span className="text-right">AUDIENCE</span>
              <span className="text-right">OVERNIGHT CHANGE</span>
              <span className="text-right">TRAJECTORY</span>
            </div>

            <ol className="divide-y divide-border-faint">
              {sorted.map(({ influencer, latestSnapshot, followerDelta, recentHighlights, history }, i) => {
                const hasWarning = recentHighlights.some((h) => h.metric?.severity === "warning");
                const hasGood = recentHighlights.some((h) => h.metric?.severity === "good");
                const followers = latestSnapshot?.followers ?? 0;
                const meaningful = Math.abs(followerDelta) >= Math.max(5, followers * 0.0001);
                const sparkValues = history.map((h) => h.followers);
                const sparkTone =
                  meaningful && followerDelta > 0
                    ? ("positive" as const)
                    : meaningful && followerDelta < 0
                      ? ("negative" as const)
                      : ("neutral" as const);

                return (
                  <Reveal as="li" key={influencer.id} delay={Math.min(i * 30, 210)}>
                    <Link
                      href={`/influencer/${influencer.handle}`}
                      className="group grid grid-cols-[2rem_auto_1fr] items-center gap-x-4 px-5 py-4 transition-colors hover:bg-surface-2 sm:grid-cols-[2.5rem_3rem_minmax(0,1fr)_8rem_9rem_8.5rem] sm:px-7"
                    >
                      <span className="font-mono text-sm text-faint" aria-hidden>
                        {String(i + 1).padStart(2, "0")}
                      </span>

                      <ViewTransition name={`avatar-${influencer.handle}`}>
                        <Avatar handle={influencer.handle} avatarUrl={influencer.avatar_url} size="sm" />
                      </ViewTransition>

                      <span className="min-w-0">
                        <span className="font-display block truncate text-xl text-ink transition-colors group-hover:text-accent">
                          {influencer.display_name ?? `@${influencer.handle}`}
                        </span>
                        <span className="mt-0.5 flex items-center gap-2 text-xs text-faint">
                          {influencer.display_name ? `@${influencer.handle}` : "Instagram"}
                          {hasWarning ? (
                            <span className="inline-flex items-center gap-1 text-negative">
                              <span aria-hidden className="h-1.5 w-1.5 rounded-full bg-negative" />
                              attention
                            </span>
                          ) : hasGood ? (
                            <span className="inline-flex items-center gap-1 text-positive">
                              <span aria-hidden className="h-1.5 w-1.5 rounded-full bg-positive" />
                              breakout
                            </span>
                          ) : null}
                        </span>
                      </span>

                      <span className="font-mono tnum col-start-3 row-start-1 text-right text-sm text-ink sm:col-start-4 sm:row-start-1 sm:text-base">
                        {followers > 0 ? followers.toLocaleString("en-US") : "—"}
                      </span>

                      <span
                        className={`font-mono tnum col-start-3 row-start-2 text-right text-xs sm:col-start-5 sm:row-start-1 sm:text-sm ${
                          meaningful && followerDelta > 0
                            ? "text-positive"
                            : meaningful && followerDelta < 0
                              ? "text-negative"
                              : "text-faint"
                        }`}
                      >
                        {latestSnapshot
                          ? followerDelta === 0
                            ? "±0"
                            : `${followerDelta > 0 ? "+" : ""}${followerDelta.toLocaleString("en-US")}`
                          : ""}
                      </span>

                      <span className="hidden justify-end sm:flex">
                        <Sparkline values={sparkValues} tone={sparkTone} />
                      </span>
                    </Link>
                  </Reveal>
                );
              })}
            </ol>
          </div>
        )}
      </div>
    </section>
  );
}
