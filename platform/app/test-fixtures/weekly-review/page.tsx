import { notFound } from "next/navigation";
import { LanguageProvider } from "@/app/components/LanguageProvider";
import { LanguageToggle } from "@/app/components/LanguageToggle";
import { PortfolioHealth } from "@/app/components/PortfolioHealth";
import { RosterBriefing } from "@/app/components/RosterBriefing";

const item = { title: { en: "Discuss the active experiment", es: "Revisar el experimento activo" }, handles: ["fixture_talent"], metric: "+25.0% interactions vs baseline", shortcode: "fixture-post" };
const weekly = {
  top_priorities: [item],
  strongest_creative_win: { ...item, title: { en: "Craft reel beat its baseline", es: "El reel de oficio superó su referencia" } },
  primary_risk: { ...item, title: { en: "Strategy review is overdue", es: "La revisión estratégica está pendiente" }, metric: null, shortcode: null },
  experiments: { due: [item], recently_evaluated: [] },
  stale_strategies: [{ handle: "fixture_talent", status: { en: "Review due", es: "Revisión pendiente" } }],
  suggested_conversations: [{ handle: "fixture_talent", topic: { en: "Agree the next craft test", es: "Acordar la próxima prueba de oficio" }, reason: { en: "The current result is directional.", es: "El resultado actual es direccional." }, metric: "+25.0% interactions vs baseline", shortcode: "fixture-post" }],
};
const legacy = { summary: { en: "Legacy summary", es: "Resumen anterior" }, patterns: [], actions: [] };
const malformed = { top_priorities: [], experiments: { due: "not-a-list" }, stale_strategies: [], suggested_conversations: [] };

export default async function WeeklyReviewFixture({ searchParams }: { searchParams: Promise<{ scenario?: string }> }) {
  if (process.env.NODE_ENV === "production") notFound();
  const { scenario } = await searchParams;
  const empty = scenario === "empty";
  const content = scenario === "legacy" ? JSON.stringify(legacy) : scenario === "malformed" ? malformed : weekly;
  return (
    <LanguageProvider><main className="mx-auto max-w-5xl p-8"><div className="mb-4 flex justify-end"><LanguageToggle /></div><RosterBriefing content={content} generatedAt="2026-07-29T12:00:00.000Z" periodStart={scenario === "legacy" ? null : "2026-07-27"} periodEnd={scenario === "legacy" ? null : "2026-08-02"} /><PortfolioHealth kpis={empty ? { rosterSize: 0, strategyProfiles: 0, unresolvedRecommendations: 0, activeExperiments: 0, evaluatedExperiments: 0, experimentHits: 0, experimentHitRate: null } : { rosterSize: 5, strategyProfiles: 3, unresolvedRecommendations: 7, activeExperiments: 2, evaluatedExperiments: 4, experimentHits: 3, experimentHitRate: 75 }} /></main></LanguageProvider>
  );
}
