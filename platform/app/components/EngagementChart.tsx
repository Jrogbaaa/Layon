"use client";

import { useEffect, useState } from "react";
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, ReferenceLine } from "recharts";
import type { PostSnapshot } from "@/app/lib/types";
import { formatCount } from "@/app/lib/metrics";

type EngagementChartProps = {
  posts: PostSnapshot[];
  followers: number;
};

type EngagementPoint = {
  index: number;
  x: number;
  shortcode: string;
  date: string;
  publicationDate: string | null;
  relativeInterval: string | null;
  timingAvailable: boolean;
  format: string;
  engagement: number;
  likes: number;
  comments: number;
  er: number;
  caption: string;
};

interface TooltipPayloadItem {
  payload: EngagementPoint;
}

interface CustomTooltipProps {
  active?: boolean;
  payload?: TooltipPayloadItem[];
}

type EngagementDotProps = {
  cx?: number;
  cy?: number;
  index?: number;
  payload?: EngagementPoint;
  selectedIndex: number | null;
  onSelect: (index: number) => void;
  onHover: (index: number) => void;
};

const DISPLAY_TIME_ZONE = "Europe/Madrid";

function instagramPostUrl(shortcode: string): string {
  return `https://www.instagram.com/p/${shortcode}/`;
}

// Custom tooltips to show format, likes, comments, ER% and caption context
function CustomTooltip({ active, payload }: CustomTooltipProps) {
  if (active && payload && payload.length) {
    const d = payload[0].payload;
    return (
      <div className="w-[min(260px,calc(100vw-2rem))] max-w-[calc(100vw-2rem)] rounded-lg border border-border-faint bg-[#241819] p-3 text-xs font-mono">
        <p className="text-[#f4ede2] font-bold mb-2">
          {d.date} · <span className="capitalize">{d.format}</span>
        </p>
        <p className="text-accent font-semibold">Engagement: {d.engagement.toLocaleString()}</p>
        <p className="text-faint mt-1">
          Likes: {d.likes.toLocaleString()} · Comments: {d.comments.toLocaleString()}
        </p>
        <p className="text-accent mt-1">ER: {d.er}%</p>
        <p className="text-muted mt-2 border-t border-border-faint pt-2">
          {d.timingAvailable
            ? `Published ${d.publicationDate} · ${d.relativeInterval}`
            : "Publication timing unavailable"}
        </p>
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

function EngagementDot({ cx, cy, index, payload, selectedIndex, onSelect, onHover }: EngagementDotProps) {
  if (cx == null || cy == null || index == null || payload == null) return null;

  const isSelected = selectedIndex === index;
  const label = payload.timingAvailable
    ? `${payload.publicationDate}, ${payload.format}, ${formatCount(payload.engagement)} engagement`
    : `Publication timing unavailable, ${payload.format}, ${formatCount(payload.engagement)} engagement`;
  const retainFocus = () => {
    requestAnimationFrame(() => {
      document.querySelector<SVGAElement>(`[data-testid="engagement-point-${index}"]`)?.focus();
    });
  };

  return (
    <a
      href={instagramPostUrl(payload.shortcode)}
      target="_blank"
      rel="noopener noreferrer"
      className="group cursor-pointer outline-none"
      aria-label={`Open Instagram post: ${label}`}
      data-selected={isSelected ? "true" : "false"}
      data-testid={`engagement-point-${index}`}
      onClick={() => {
        onSelect(index);
        retainFocus();
      }}
      onFocus={() => {
        onSelect(index);
        retainFocus();
      }}
      onMouseEnter={() => onHover(index)}
    >
      <circle cx={cx} cy={cy} r={12} fill="transparent" stroke="none" />
      <circle
        cx={cx}
        cy={cy}
        r={isSelected ? 7 : 5.5}
        fill="none"
        stroke="#e3b04b"
        strokeWidth={1.5}
        className="opacity-0 transition-opacity group-focus-visible:opacity-100"
        aria-hidden
      />
      <circle
        cx={cx}
        cy={cy}
        r={isSelected ? 4.5 : 2.5}
        fill={isSelected ? "#f0c96a" : "#7e2230"}
        stroke="#120b0d"
        strokeWidth={isSelected ? 2 : 1.5}
        className="transition-[r,fill]"
      />
    </a>
  );
}

const ISO_TIMESTAMP_WITH_TIME_ZONE =
  /^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})(?:\.(\d{1,6}))?(Z|([+-])(\d{2}):(\d{2}))$/;

export function parsePublicationTimestamp(postedAt: unknown): number | null {
  if (typeof postedAt !== "string" || postedAt.length === 0 || postedAt !== postedAt.trim()) return null;

  const match = ISO_TIMESTAMP_WITH_TIME_ZONE.exec(postedAt);
  if (!match) return null;

  const [
    ,
    yearText,
    monthText,
    dayText,
    hourText,
    minuteText,
    secondText,
    ,
    ,
    ,
    offsetHourText,
    offsetMinuteText,
  ] = match;
  const year = Number(yearText);
  const month = Number(monthText);
  const day = Number(dayText);
  const hour = Number(hourText);
  const minute = Number(minuteText);
  const second = Number(secondText);
  const offsetHour = offsetHourText ? Number(offsetHourText) : 0;
  const offsetMinute = offsetMinuteText ? Number(offsetMinuteText) : 0;
  const leapYear = year % 4 === 0 && (year % 100 !== 0 || year % 400 === 0);
  const daysInMonth = [31, leapYear ? 29 : 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];

  if (
    year === 0 ||
    month < 1 ||
    month > 12 ||
    day < 1 ||
    day > daysInMonth[month - 1] ||
    hour > 23 ||
    minute > 59 ||
    second > 59 ||
    offsetHour > 14 ||
    offsetMinute > 59 ||
    (offsetHour === 14 && offsetMinute !== 0)
  ) {
    return null;
  }

  const timestamp = Date.parse(postedAt);
  return Number.isFinite(timestamp) ? timestamp : null;
}

function formatPublicationDate(timestamp: number): string {
  return new Date(timestamp).toLocaleDateString("en-US", {
    timeZone: DISPLAY_TIME_ZONE,
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

function formatChartDate(timestamp: number): string {
  return new Date(timestamp).toLocaleDateString("en-US", {
    timeZone: DISPLAY_TIME_ZONE,
    month: "short",
    day: "numeric",
  });
}

function formatRelativeInterval(current: number, previous: number | null): string {
  if (previous === null) return "first plotted post";

  const currentDate = new Date(current).toLocaleDateString("en-CA", { timeZone: DISPLAY_TIME_ZONE });
  const previousDate = new Date(previous).toLocaleDateString("en-CA", { timeZone: DISPLAY_TIME_ZONE });
  const days = Math.max(
    0,
    Math.round((Date.parse(`${currentDate}T00:00:00Z`) - Date.parse(`${previousDate}T00:00:00Z`)) / (24 * 60 * 60 * 1000)),
  );
  if (days === 0) return "same day as previous post";
  return `${days} day${days === 1 ? "" : "s"} after previous post`;
}

function PublicationDetails({ point, onClear }: { point: EngagementPoint; onClear?: () => void }) {
  return (
    <div
      className="relative rounded-md border border-border-faint bg-surface px-3 py-2 font-mono text-[11px]"
      data-testid="publication-details"
      aria-live="polite"
    >
      {onClear && (
        <button
          type="button"
          onClick={onClear}
          className="absolute right-2 top-2 h-5 w-5 flex items-center justify-center rounded-full border border-border text-muted hover:text-ink hover:bg-surface-2 transition-colors text-xs cursor-pointer"
          aria-label="Clear selection"
        >
          ×
        </button>
      )}
      <div className="flex flex-wrap items-baseline gap-x-3 gap-y-1 pr-6">
        <span className="text-ink">
          {point.timingAvailable ? `Published ${point.publicationDate}` : "Publication timing unavailable"}
        </span>
        <span className="capitalize text-faint">{point.format}</span>
        {point.relativeInterval ? <span className="text-accent">{point.relativeInterval}</span> : null}
      </div>
      <p className="mt-1 text-muted">
        {formatCount(point.engagement)} engagement · {point.er}% ER · {point.likes.toLocaleString()} likes ·{" "}
        {point.comments.toLocaleString()} comments
      </p>
      <a
        href={instagramPostUrl(point.shortcode)}
        target="_blank"
        rel="noopener noreferrer"
        className="mt-1 inline-block text-accent hover:text-accent-bright"
        data-testid="publication-details-link"
      >
        View on Instagram →
      </a>
    </div>
  );
}

function PublicationMarkerRail({
  data,
  selectedIndex,
  onSelect,
  onHover,
  onClear,
  isLocked,
}: {
  data: EngagementPoint[];
  selectedIndex: number | null;
  onSelect: (index: number) => void;
  onHover: (index: number) => void;
  onClear: () => void;
  isLocked: boolean;
}) {
  const selectedPoint = selectedIndex == null ? null : data[selectedIndex] ?? null;
  const selectPrevious = () => onSelect(selectedIndex == null ? 0 : Math.max(0, selectedIndex - 1));
  const selectNext = () => onSelect(selectedIndex == null ? 0 : Math.min(data.length - 1, selectedIndex + 1));

  const marker = (point: EngagementPoint, index: number, interactive: boolean) => {
    const label = point.timingAvailable
      ? `Published ${point.publicationDate}, ${point.format}, ${point.relativeInterval}. ${formatCount(point.engagement)} engagement.`
      : `Publication timing unavailable, ${point.format}. ${formatCount(point.engagement)} engagement.`;
    const dot = (
      <span
        className={`block h-2 w-2 rounded-full border transition-[background-color,box-shadow] ${
          point.timingAvailable
            ? selectedIndex === index
              ? "border-accent bg-accent shadow-[0_0_0_3px_rgba(227,176,75,0.18)]"
              : "border-accent-deep bg-accent-deep/70 group-hover:bg-accent/80 group-focus-visible:bg-accent/80"
            : selectedIndex === index
              ? "border-accent bg-surface-2 shadow-[0_0_0_3px_rgba(227,176,75,0.18)]"
              : "border-border bg-surface-2"
        }`}
        aria-hidden
      />
    );

    if (!interactive) {
      return (
        <span
          key={`${point.index}-${point.format}`}
          className="relative z-10 flex h-8 min-w-0 items-center justify-center"
          data-testid="publication-marker-visual"
          data-selected={selectedIndex === index ? "true" : "false"}
          aria-hidden
        >
          {dot}
        </span>
      );
    }

    return (
      <button
        key={`${point.index}-${point.format}`}
        type="button"
        className={`group relative z-10 flex h-11 min-w-0 items-center justify-center rounded-sm outline-offset-2 focus-visible:outline-2 focus-visible:outline-accent ${
          selectedIndex === index ? "bg-accent/10" : ""
        }`}
        aria-label={label}
        aria-pressed={selectedIndex === index}
        data-testid="publication-marker"
        data-publication-date={point.publicationDate ?? undefined}
        data-selected={selectedIndex === index ? "true" : "false"}
        onClick={() => onSelect(index)}
        onFocus={() => onSelect(index)}
        onMouseEnter={() => onHover(index)}
      >
        {dot}
      </button>
    );
  };

  return (
    <div className="mt-2" data-testid="publication-marker-rail">
      <div className="flex items-baseline justify-between gap-4">
        <span className="font-mono text-[10px] tracking-widest text-faint">
          POSTS · {data.length}
        </span>
        <span className="font-mono text-[10px] text-faint lg:hidden" data-testid="selected-post-position">
          {selectedIndex == null ? "NO POST SELECTED" : `POST ${selectedIndex + 1} / ${data.length}`}
        </span>
      </div>

      <div className="relative mt-1 h-8 lg:hidden" data-testid="publication-marker-overview">
        <div
          className="relative grid h-8 min-w-0"
          style={{
            gridTemplateColumns: `repeat(${data.length}, minmax(0, 1fr))`,
            marginLeft: 56,
            marginRight: 28,
          }}
        >
          <span className="pointer-events-none absolute inset-x-0 top-1/2 h-px bg-border-faint" aria-hidden />
          {data.map((point, index) => marker(point, index, false))}
        </div>
      </div>

      <div className="mt-1 hidden h-11 lg:block">
        <div
          className="relative grid h-11 min-w-0"
          style={{
            gridTemplateColumns: `repeat(${data.length}, minmax(0, 1fr))`,
            marginLeft: 56,
            marginRight: 28,
          }}
        >
          <span className="pointer-events-none absolute inset-x-0 top-1/2 h-px bg-border-faint" aria-hidden />
          {data.map((point, index) => marker(point, index, true))}
        </div>
      </div>

      <div className="mt-1 flex items-center justify-between gap-3 lg:hidden" data-testid="publication-mobile-controls">
        <button
          type="button"
          className="flex h-11 min-w-11 items-center justify-center rounded-md border border-border-faint bg-surface font-mono text-sm text-ink transition-colors hover:border-border hover:bg-surface-2 disabled:cursor-not-allowed disabled:text-faint disabled:opacity-50 cursor-pointer"
          aria-label="Previous post"
          disabled={selectedIndex == null || selectedIndex === 0}
          onClick={selectPrevious}
        >
          ←
        </button>
        <p className="min-w-0 flex-1 text-center font-mono text-[10px] text-muted">
          {selectedIndex == null ? "Use the arrows or select a chart point" : "Selected post"}
        </p>
        <button
          type="button"
          className="flex h-11 min-w-11 items-center justify-center rounded-md border border-border-faint bg-surface font-mono text-sm text-ink transition-colors hover:border-border hover:bg-surface-2 disabled:cursor-not-allowed disabled:text-faint disabled:opacity-50 cursor-pointer"
          aria-label={selectedIndex == null ? "Select first post" : "Next post"}
          disabled={selectedIndex === data.length - 1}
          onClick={selectNext}
        >
          →
        </button>
      </div>

      <div className="mt-1 min-h-11">
        {selectedPoint ? (
          <PublicationDetails point={selectedPoint} onClear={isLocked ? onClear : undefined} />
        ) : (
          <p className="pl-[4.75rem] font-mono text-[10px] text-faint">
            Select a point to identify the post and compare its timing with the spike.
          </p>
        )}
      </div>
    </div>
  );
}

export function EngagementChart({ posts, followers }: EngagementChartProps) {
  const [selectedIndex, setSelectedIndex] = useState<number | null>(null);
  const [isLocked, setIsLocked] = useState(false);

  useEffect(() => {
    const clearSelection = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        setSelectedIndex(null);
        setIsLocked(false);
      }
    };

    window.addEventListener("keydown", clearSelection);
    return () => window.removeEventListener("keydown", clearSelection);
  }, []);

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

  const parsedTimestamps = posts.map((post) => parsePublicationTimestamp(post.posted_at));
  const previousTimestamps = parsedTimestamps.map(
    (_, index) =>
      parsedTimestamps
        .slice(0, index)
        .reverse()
        .find((timestamp): timestamp is number => timestamp !== null) ?? null,
  );
  const data = posts.map((post, index) => {
    const engagement = post.likes + post.comments;
    const er = followers > 0 ? (engagement / followers) * 100 : 0;
    const timestamp = parsedTimestamps[index];
    const timingAvailable = timestamp !== null;
    const publicationDate = timestamp === null ? null : formatPublicationDate(timestamp);
    const relativeInterval = timestamp === null ? null : formatRelativeInterval(timestamp, previousTimestamps[index]);

    return {
      index,
      x: index,
      shortcode: post.shortcode,
      date: timestamp === null ? "Date unavailable" : formatChartDate(timestamp),
      publicationDate,
      relativeInterval,
      timingAvailable,
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
  const selectIndex = (index: number) => setSelectedIndex(Math.max(0, Math.min(index, data.length - 1)));
  const hoverSelect = (index: number) => {
    if (!isLocked) {
      selectIndex(index);
    }
  };
  const lockSelect = (index: number) => {
    selectIndex(index);
    setIsLocked(true);
  };
  const clearLock = () => {
    setSelectedIndex(null);
    setIsLocked(false);
  };

  const axisTicks = Array.from(
    new Set(
      Array.from({ length: Math.min(6, data.length) }, (_, tickIndex) =>
        data.length === 1 ? 0 : Math.round((tickIndex * (data.length - 1)) / (Math.min(6, data.length) - 1)),
      ),
    ),
  );

  return (
    <div className="w-full">
      <div className="h-[260px] w-full">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart
            data={data}
            margin={{ top: 12, right: 28, bottom: 0, left: 0 }}
            onMouseMove={(state) => {
              if (typeof state?.activeTooltipIndex === "number") hoverSelect(state.activeTooltipIndex);
            }}
            onClick={(state) => {
              if (typeof state?.activeTooltipIndex === "number") lockSelect(state.activeTooltipIndex);
            }}
          >
            <defs>
              <linearGradient id="engagementFill" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#e3b04b" stopOpacity={0.28} />
                <stop offset="60%" stopColor="#7e2230" stopOpacity={0.12} />
                <stop offset="100%" stopColor="#7e2230" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="2 6" stroke="#362527" vertical={false} />
            <XAxis
              dataKey="x"
              type="number"
              domain={[-0.5, Math.max(0.5, data.length - 0.5)]}
              ticks={axisTicks}
              tickFormatter={(value) => data[value]?.date ?? ""}
              minTickGap={24}
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
            <Tooltip
              content={<CustomTooltip />}
              cursor={{ stroke: "#362527", strokeWidth: 1 }}
              wrapperStyle={{ maxWidth: "calc(100vw - 2rem)" }}
            />
            {selectedIndex !== null ? (
              <ReferenceLine
                x={selectedIndex}
                stroke="#e3b04b"
                strokeOpacity={0.6}
                strokeDasharray="2 4"
                data-testid="selected-publication-guide"
              />
            ) : null}
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
              dot={(dotProps) => (
                <EngagementDot
                  {...dotProps}
                  selectedIndex={selectedIndex}
                  onSelect={lockSelect}
                  onHover={hoverSelect}
                />
              )}
              activeDot={false}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
      <PublicationMarkerRail
        data={data}
        selectedIndex={selectedIndex}
        onSelect={lockSelect}
        onHover={hoverSelect}
        onClear={clearLock}
        isLocked={isLocked}
      />
    </div>
  );
}
