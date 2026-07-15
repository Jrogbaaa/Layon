import type { PostSnapshot } from "@/app/lib/types";
import { formatCount, postEngagementRate } from "@/app/lib/metrics";

export function RecentPostsTable({
  posts,
  followers,
}: {
  posts: PostSnapshot[];
  followers: number;
}) {
  if (posts.length === 0) {
    return <p className="text-sm text-muted">No post data yet.</p>;
  }

  return (
    <div className="overflow-x-auto [mask-image:linear-gradient(to_right,black_calc(100%_-_1.5rem),transparent)] sm:[mask-image:none]">
      <table className="w-full min-w-[640px] text-left text-sm sm:min-w-0">
        <thead>
          <tr className="font-mono border-b border-border text-xs text-faint">
            <th className="pb-3 pr-4 font-normal">DATE</th>
            <th className="pb-3 pr-4 font-normal">FORMAT</th>
            <th className="pb-3 pr-4 text-right font-normal">LIKES</th>
            <th className="pb-3 pr-4 text-right font-normal">COMMENTS</th>
            <th className="pb-3 pr-4 text-right font-normal">VIEWS</th>
            <th className="pb-3 pr-4 text-right font-normal">ENG.</th>
            <th className="pb-3 font-normal">LINK</th>
          </tr>
        </thead>
        <tbody>
          {posts.map((post) => (
            <tr
              key={post.shortcode}
              className="border-b border-border-faint transition-colors last:border-b-0 hover:bg-surface"
            >
              <td className="py-3 pr-4 text-muted">
                {new Date(post.posted_at).toLocaleDateString("en-US", {
                  month: "short",
                  day: "numeric",
                  year: "numeric",
                })}
              </td>
              <td className="py-3 pr-4 capitalize text-muted">
                {post.post_type}
                {post.is_ad && (
                  <span className="ml-1.5 rounded bg-accent/10 px-1 py-0.5 text-[9px] font-semibold text-accent uppercase tracking-wider">
                    Paid Media
                  </span>
                )}
              </td>
              <td className="font-mono tnum py-3 pr-4 text-right text-ink">{formatCount(post.likes)}</td>
              <td className="font-mono tnum py-3 pr-4 text-right text-ink">
                {formatCount(post.comments)}
              </td>
              <td className="font-mono tnum py-3 pr-4 text-right text-muted">
                {post.views != null ? formatCount(post.views) : "—"}
              </td>
              <td className="font-mono tnum py-3 pr-4 text-right text-ink">
                {postEngagementRate(post, followers)}%
              </td>
              <td className="py-3">
                <a
                  href={`https://www.instagram.com/p/${post.shortcode}/`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-accent hover:text-accent-bright"
                >
                  View
                </a>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
