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
    return <p className="text-sm text-neutral-500">No post data yet.</p>;
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-left text-sm">
        <thead>
          <tr className="border-b border-neutral-800 text-xs text-neutral-500">
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
            <tr key={post.shortcode} className="border-b border-neutral-800/60">
              <td className="py-3 pr-4 text-neutral-300">
                {new Date(post.posted_at).toLocaleDateString("en-US", {
                  month: "short",
                  day: "numeric",
                  year: "numeric",
                })}
              </td>
              <td className="py-3 pr-4 capitalize text-neutral-300">{post.post_type}</td>
              <td className="py-3 pr-4 text-neutral-200">{formatCount(post.likes)}</td>
              <td className="py-3 pr-4 text-neutral-200">{formatCount(post.comments)}</td>
              <td className="py-3 pr-4 text-neutral-400">
                {post.views != null ? formatCount(post.views) : "—"}
              </td>
              <td className="py-3 pr-4 text-neutral-200">{postEngagementRate(post, followers)}%</td>
              <td className="py-3">
                <a
                  href={`https://www.instagram.com/p/${post.shortcode}/`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-amber-500 hover:underline"
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
