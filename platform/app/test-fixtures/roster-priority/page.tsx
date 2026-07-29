import { RosterIndexList } from "@/app/components/RosterIndexList";
import type { AttentionPriority, RosterEntry } from "@/app/lib/types";
import { notFound } from "next/navigation";

const current = "2099-01-01T00:00:00.000Z";

function entry(id: number, handle: string, followers: number, nextAction: AttentionPriority): RosterEntry {
  return {
    influencer: { id, handle, display_name: handle, avatar_url: null },
    latestSnapshot: { followers, following: 1, media_count: 1, bio: null, captured_at: current },
    followerDelta: id,
    recentHighlights: [],
    history: [{ followers, following: 1, media_count: 1, bio: null, captured_at: current }],
    nextAction,
  };
}

const roster = [
  entry(1, "large_no_action", 1000, { kind: "none", priority: 0, label: { en: "No immediate action", es: "Sin acción inmediata" }, detail: null }),
  entry(2, "recommendation_due", 100, { kind: "recommendation", priority: 20, label: { en: "Respond to recommendation", es: "Responder a la recomendación" }, detail: null }),
  entry(3, "data_missing", 10, { kind: "missing_data", priority: 60, label: { en: "Restore evidence", es: "Restaurar datos" }, detail: null }),
];

export default function RosterPriorityFixture() {
  if (process.env.NODE_ENV === "production") notFound();
  return <main className="mx-auto max-w-5xl p-8"><RosterIndexList initialRoster={roster} /></main>;
}
