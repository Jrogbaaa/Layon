"use client";

import { useLanguage } from "@/app/components/LanguageProvider";
import type { PortfolioKpis } from "@/app/lib/types";

export function PortfolioHealth({ kpis }: { kpis: PortfolioKpis }) {
  const { lang } = useLanguage();
  const coverage = kpis.rosterSize ? Math.round((kpis.strategyProfiles / kpis.rosterSize) * 100) : 0;
  const items = [
    { label: lang === "en" ? "Strategy coverage" : "Cobertura estratégica", value: kpis.rosterSize ? `${coverage}%` : "—", detail: `${kpis.strategyProfiles}/${kpis.rosterSize}` },
    { label: lang === "en" ? "Unresolved recommendations" : "Recomendaciones pendientes", value: String(kpis.unresolvedRecommendations), detail: lang === "en" ? "current bullets" : "puntos actuales" },
    { label: lang === "en" ? "Active experiments" : "Experimentos activos", value: String(kpis.activeExperiments), detail: lang === "en" ? "planned + published" : "planificados + publicados" },
    { label: lang === "en" ? "Experiment hit rate" : "Tasa de acierto", value: kpis.experimentHitRate == null ? "—" : `${kpis.experimentHitRate}%`, detail: kpis.evaluatedExperiments ? `${kpis.experimentHits}/${kpis.evaluatedExperiments}` : lang === "en" ? "no evaluated outcomes" : "sin resultados evaluados" },
  ];
  return (
    <section className="mb-12" data-testid="portfolio-health">
      <h2 className="font-mono mb-4 text-xs tracking-widest text-faint">{lang === "en" ? "COACHING OPERATIONS" : "OPERACIONES DE COACHING"}</h2>
      <dl className="grid grid-cols-2 border-y border-border-faint sm:grid-cols-4 sm:divide-x sm:divide-border-faint">
        {items.map((item) => <div key={item.label} className="px-3 py-4 first:pl-0 sm:px-5"><dt className="text-xs text-faint">{item.label}</dt><dd className="font-mono mt-1 text-2xl text-ink">{item.value}</dd><dd className="mt-1 text-[10px] text-muted">{item.detail}</dd></div>)}
      </dl>
    </section>
  );
}
