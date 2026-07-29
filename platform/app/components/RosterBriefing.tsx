"use client";

import Link from "next/link";
import { useLanguage } from "@/app/components/LanguageProvider";
import type { BriefingPayload, WeeklyReviewItem, WeeklyReviewPayload } from "@/app/lib/types";

function parsedContent(content: string | Record<string, unknown>): Record<string, unknown> | null {
  try {
    return (typeof content === "string" ? JSON.parse(content) : content) as Record<string, unknown>;
  } catch {
    return null;
  }
}

function parseBriefing(content: string | Record<string, unknown>): BriefingPayload | null {
  const parsed = parsedContent(content);
  if (parsed && parsed.summary && Array.isArray(parsed.patterns) && Array.isArray(parsed.actions)) return parsed as BriefingPayload;
  return null;
}

function parseWeeklyReview(content: string | Record<string, unknown>): WeeklyReviewPayload | null {
  const parsed = parsedContent(content);
  if (!parsed || !Array.isArray(parsed.top_priorities) || !isReviewItems(parsed.top_priorities)) return null;
  const experiments = parsed.experiments;
  if (!experiments || typeof experiments !== "object") return null;
  const due = (experiments as Record<string, unknown>).due;
  const recentlyEvaluated = (experiments as Record<string, unknown>).recently_evaluated;
  if (!Array.isArray(due) || !isReviewItems(due) || !Array.isArray(recentlyEvaluated) || !isReviewItems(recentlyEvaluated)) return null;
  if (!Array.isArray(parsed.stale_strategies) || !Array.isArray(parsed.suggested_conversations)) return null;
  if (parsed.strongest_creative_win != null && !isReviewItem(parsed.strongest_creative_win)) return null;
  if (parsed.primary_risk != null && !isReviewItem(parsed.primary_risk)) return null;
  if (!parsed.stale_strategies.every((item) => isRecord(item) && typeof item.handle === "string" && isBilingual(item.status))) return null;
  if (!parsed.suggested_conversations.every((item) => isRecord(item) && typeof item.handle === "string" && isBilingual(item.topic) && isBilingual(item.reason))) return null;
  return parsed as unknown as WeeklyReviewPayload;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return Boolean(value) && typeof value === "object";
}

function isBilingual(value: unknown): boolean {
  return isRecord(value) && typeof value.en === "string" && typeof value.es === "string";
}

function isReviewItem(value: unknown): boolean {
  return isRecord(value) && isBilingual(value.title) && Array.isArray(value.handles) && value.handles.every((handle) => typeof handle === "string");
}

function isReviewItems(value: unknown[]): boolean {
  return value.every(isReviewItem);
}

function ReviewItem({ item, lang }: { item: WeeklyReviewItem; lang: "en" | "es" }) {
  return <li className="border-l border-border-faint pl-3"><p className="text-sm text-ink">{item.title[lang]}</p><p className="font-mono mt-1 text-[10px] text-faint">{item.metric ?? (lang === "en" ? "Qualitative evidence" : "Evidencia cualitativa")}</p><p className="mt-1 flex flex-wrap gap-2 text-xs">{item.handles.map((handle) => <Link key={handle} href={`/influencer/${handle}`} className="text-accent">@{handle}</Link>)}{item.shortcode ? <a href={`https://www.instagram.com/p/${item.shortcode}/`} target="_blank" rel="noreferrer" className="text-accent">post →</a> : null}</p></li>;
}

export function RosterBriefing({
  content,
  generatedAt,
  periodStart = null,
  periodEnd = null,
}: {
  content: string | Record<string, unknown>;
  generatedAt: string;
  periodStart?: string | null;
  periodEnd?: string | null;
}) {
  const { lang } = useLanguage();
  const weekly = parseWeeklyReview(content);
  const briefing = parseBriefing(content);

  if (weekly) {
    const experimentItems = [...weekly.experiments.due, ...weekly.experiments.recently_evaluated];
    return (
      <section className="mb-12" data-testid="weekly-review">
        <div className="mb-5 flex flex-wrap items-center justify-between gap-2"><h2 className="font-mono text-xs tracking-widest text-accent">{lang === "en" ? "WEEKLY PORTFOLIO REVIEW" : "REVISIÓN SEMANAL DE CARTERA"}</h2><p className="font-mono text-[10px] text-faint">{periodStart && periodEnd ? `${periodStart} → ${periodEnd}` : new Date(generatedAt).toLocaleDateString()}</p></div>
        <div className="grid gap-8 lg:grid-cols-2">
          <div><h3 className="font-mono mb-3 text-[10px] uppercase tracking-widest text-faint">{lang === "en" ? "Top priorities" : "Prioridades"}</h3><ol className="space-y-4">{weekly.top_priorities.map((item, index) => <ReviewItem key={index} item={item} lang={lang} />)}</ol></div>
          <div className="space-y-6">
            {weekly.strongest_creative_win ? <div><h3 className="font-mono text-[10px] uppercase text-positive">{lang === "en" ? "Strongest creative win" : "Mejor logro creativo"}</h3><ul className="mt-2"><ReviewItem item={weekly.strongest_creative_win} lang={lang} /></ul></div> : null}
            {weekly.primary_risk ? <div><h3 className="font-mono text-[10px] uppercase text-negative">{lang === "en" ? "Primary risk" : "Riesgo principal"}</h3><ul className="mt-2"><ReviewItem item={weekly.primary_risk} lang={lang} /></ul></div> : null}
          </div>
        </div>
        <details className="group mt-6"><summary className="cursor-pointer text-sm text-accent">{lang === "en" ? "Experiments, strategy health & conversations" : "Experimentos, estrategia y conversaciones"}</summary><div className="mt-5 grid gap-8 lg:grid-cols-3"><div><h3 className="font-mono mb-3 text-[10px] uppercase text-faint">{lang === "en" ? "Experiments" : "Experimentos"}</h3>{experimentItems.length ? <ul className="space-y-3">{experimentItems.map((item, index) => <ReviewItem key={index} item={item} lang={lang} />)}</ul> : <p className="text-xs text-muted">{lang === "en" ? "None due or recently evaluated." : "Ninguno pendiente o recién evaluado."}</p>}</div><div><h3 className="font-mono mb-3 text-[10px] uppercase text-faint">{lang === "en" ? "Stale strategies" : "Estrategias desactualizadas"}</h3><ul className="space-y-2">{weekly.stale_strategies.map((item) => <li key={item.handle} className="text-xs"><Link href={`/influencer/${item.handle}`} className="text-accent">@{item.handle}</Link><span className="ml-2 text-muted">{item.status[lang]}</span></li>)}</ul></div><div><h3 className="font-mono mb-3 text-[10px] uppercase text-faint">{lang === "en" ? "Suggested conversations" : "Conversaciones sugeridas"}</h3><ul className="space-y-3">{weekly.suggested_conversations.map((item) => <li key={`${item.handle}-${item.topic.en}`} className="text-xs"><Link href={`/influencer/${item.handle}`} className="font-semibold text-accent">@{item.handle}</Link><p className="mt-1 text-ink">{item.topic[lang]}</p><p className="mt-1 text-muted">{item.reason[lang]}</p></li>)}</ul></div></div></details>
      </section>
    );
  }

  if (!briefing) return null;

  const hasDetails = briefing.patterns.length > 0 || briefing.actions.length > 0;

  return (
    <section className="mb-12">
      <div className="mb-5 flex items-center justify-between">
        <h2 className="font-mono text-xs tracking-widest text-accent">
          THE DISPATCH ·{" "}
          {new Date(generatedAt)
            .toLocaleDateString("en-US", { month: "short", day: "numeric" })
            .toUpperCase()}
        </h2>
      </div>

      {/* The week's story, told as a pull-quote. */}
      <blockquote className="font-display max-w-[32ch] text-2xl italic leading-snug text-ink sm:text-[1.75rem]">
        {briefing.summary[lang]}
      </blockquote>

      {hasDetails ? (
        <details className="group mt-6">
          <summary className="inline-flex cursor-pointer list-none items-center gap-2 text-sm font-medium text-accent transition-colors hover:text-accent-bright [&::-webkit-details-marker]:hidden">
            <span
              aria-hidden
              className="inline-block transition-transform duration-300 group-open:rotate-90"
            >
              ▸
            </span>
            <span className="group-open:hidden">Patterns &amp; priority actions</span>
            <span className="hidden group-open:inline">Hide patterns &amp; actions</span>
          </summary>

          <div
            className={`mt-6 grid gap-10 ${
              briefing.patterns.length > 0 && briefing.actions.length > 0 ? "lg:grid-cols-2" : ""
            }`}
          >
            {briefing.patterns.length > 0 ? (
              <div>
                <h3 className="font-mono mb-4 text-xs tracking-widest text-faint">PATTERNS</h3>
                <ul className="space-y-5">
                  {briefing.patterns.map((pattern, i) => (
                    <li key={i} className="text-sm leading-relaxed">
                      <p className="max-w-prose text-ink">{pattern.finding[lang]}</p>
                      <p className="font-mono mt-1 max-w-prose text-xs text-faint">
                        {pattern.evidence}
                      </p>
                      <p className="mt-1.5 flex flex-wrap gap-x-3 gap-y-1 text-xs">
                        {pattern.handles.map((handle) => (
                          <Link
                            key={handle}
                            href={`/influencer/${handle}`}
                            className="text-accent hover:text-accent-bright"
                          >
                            @{handle}
                          </Link>
                        ))}
                      </p>
                    </li>
                  ))}
                </ul>
              </div>
            ) : null}

            {briefing.actions.length > 0 ? (
              <div>
                <h3 className="font-mono mb-4 text-xs tracking-widest text-faint">
                  PRIORITY ACTIONS
                </h3>
                <ol className="space-y-5">
                  {briefing.actions.map((action, i) => (
                    <li key={i} className="flex gap-4 text-sm leading-relaxed">
                      <span className="font-mono mt-0.5 text-xs text-accent" aria-hidden>
                        {String(i + 1).padStart(2, "0")}
                      </span>
                      <div>
                        <Link
                          href={`/influencer/${action.handle}`}
                          className="font-semibold text-ink hover:text-accent"
                        >
                          @{action.handle}
                        </Link>
                        <p className="mt-1 max-w-prose text-ink">{action.action[lang]}</p>
                        <p className="mt-1 max-w-prose text-xs text-muted">{action.reason[lang]}</p>
                        {action.shortcode ? (
                          <a
                            href={`https://www.instagram.com/p/${action.shortcode}/`}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="mt-1 inline-block text-xs text-accent hover:text-accent-bright"
                          >
                            View post →
                          </a>
                        ) : null}
                      </div>
                    </li>
                  ))}
                </ol>
              </div>
            ) : null}
          </div>
        </details>
      ) : null}
    </section>
  );
}
