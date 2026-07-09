import Link from "next/link";
import { getRoster } from "@/app/lib/data";
import { formatCount } from "@/app/lib/metrics";

/** The tape: a slow trading-floor ticker of every talent's overnight move.
 *  Decorative duplicate is aria-hidden; reduced-motion stops the scroll. */
export async function Tape() {
  const roster = await getRoster();
  if (roster.length === 0) return null;

  const items = roster.map(({ influencer, latestSnapshot, followerDelta }) => ({
    handle: influencer.handle,
    followers: latestSnapshot?.followers ?? 0,
    delta: followerDelta,
  }));

  const strip = (hidden: boolean) => (
    <ul
      aria-hidden={hidden || undefined}
      className="tape-strip flex shrink-0 items-center gap-10 pr-10"
    >
      {items.map((item) => (
        <li key={item.handle} className="font-mono flex items-baseline gap-2 text-xs whitespace-nowrap">
          <Link
            href={`/influencer/${item.handle}`}
            tabIndex={hidden ? -1 : undefined}
            className="text-muted transition-colors hover:text-ink"
          >
            @{item.handle}
          </Link>
          <span className="tnum text-faint">{formatCount(item.followers)}</span>
          <span
            className={`tnum ${
              item.delta > 0 ? "text-positive" : item.delta < 0 ? "text-negative" : "text-faint"
            }`}
          >
            {item.delta > 0 ? "▲" : item.delta < 0 ? "▼" : "·"}
            {item.delta !== 0 ? Math.abs(item.delta).toLocaleString("en-US") : ""}
          </span>
        </li>
      ))}
    </ul>
  );

  return (
    <div className="tape group/tape overflow-hidden border-b border-border-faint bg-canvas-deep/60">
      <div className="tape-track flex w-max py-2">
        {strip(false)}
        {strip(true)}
      </div>
    </div>
  );
}
