import type { PostClassificationStatus, PostSnapshot } from "@/app/lib/types";

export function getPostStatus(post: Pick<PostSnapshot, "classification" | "is_ad">): PostClassificationStatus {
  if (post.classification?.status) {
    return post.classification.status;
  }
  return post.is_ad ? "paid" : "organic";
}

export function getPostStatusLabel(status: PostClassificationStatus): string {
  if (status === "paid") return "Paid Media";
  if (status === "needs_review") return "Needs Review";
  return "Organic";
}

export function getListPostStatusLabel(status: PostClassificationStatus): string | null {
  return status === "paid" ? "Paid Media" : null;
}

export function getPostStatusBadgeClass(status: PostClassificationStatus): string {
  if (status === "paid") {
    return "rounded bg-accent/10 px-1 py-0.5 text-[9px] font-semibold text-accent uppercase tracking-wider";
  }
  if (status === "needs_review") {
    return "rounded border border-border-faint px-1 py-0.5 text-[9px] font-semibold text-faint uppercase tracking-wider";
  }
  return "rounded border border-border-faint px-1 py-0.5 text-[9px] font-semibold text-muted uppercase tracking-wider";
}
