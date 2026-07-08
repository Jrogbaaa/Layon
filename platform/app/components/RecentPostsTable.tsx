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
    <div className="overflow-x-auto [mask-image:linear-gradient(to_right,black_calc(100%-1.5rem),transparent)] sm:[mask-image:none]">
      <table className="w-full min-w-[640px] text-left text-sm sm:min-w-0">
        <thead>
          <tr className="border-b border-border text-xs text-muted">
            <th className="pb-3 pr-4 font-medium">Date</th>
            <th className="pb-3 pr-4 font-medium">Format</th>
            <th className="pb-3 pr-4 font-medium">Likes</th>
            <th className="pb-3 pr-4 font-medium">Comments</th>
            <th className="pb-3 pr-4 font-medium">Views</th>
            <th className="pb-3 pr-4 font-medium">Eng. rate</th>
            <th className="pb-3 font-medium">Link</th>
          </tr>
        </thead>
        <tbody>
          {posts.map((post) => (
            <tr key={post.shortcode} className="border-b border-border/60">
              <td className="py-3 pr-4 text-muted">
                {new Date(post.posted_at).toLocaleDateString("en-US", {
                  month: "short",
                  day: "numeric",
                  year: "numeric",
                })}
              </td>
              <td className="py-3 pr-4 capitalize text-muted">{post.post_type}</td>
              <td className="py-3 pr-4 text-ink">{formatCount(post.likes)}</td>
              <td className="py-3 pr-4 text-ink">{formatCount(post.comments)}</td>
              <td className="py-3 pr-4 text-muted">
                {post.views != null ? formatCount(post.views) : "—"}
              </td>
              <td className="py-3 pr-4 text-ink">{postEngagementRate(post, followers)}%</td>
              <td className="py-3">
                <a
                  href={`https://www.instagram.com/p/${post.shortcode}/`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-accent-strong hover:underline"
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
