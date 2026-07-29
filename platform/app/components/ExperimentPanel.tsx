"use client";

import { useActionState } from "react";
import {
  abandonExperiment,
  acknowledgeOutcome,
  linkExperiment,
  overridePostPillar,
} from "@/app/actions/experiment";
import { useLanguage } from "@/app/components/LanguageProvider";
import { formatCount } from "@/app/lib/metrics";
import type {
  Influencer,
  PillarPerformance,
  PostSnapshot,
  PostStrategyTag,
  RecommendationAction,
} from "@/app/lib/types";

function Message({ state }: { state: { error?: string; success?: boolean } | undefined }) {
  if (state?.error) return <p role="alert" className="mt-2 text-xs text-negative">{state.error}</p>;
  if (state?.success) return <p role="status" className="mt-2 text-xs text-positive">Saved.</p>;
  return null;
}

function LinkForm({ action, influencer, posts }: { action: RecommendationAction; influencer: Influencer; posts: PostSnapshot[] }) {
  const { lang } = useLanguage();
  const bound = linkExperiment.bind(null, action.id, influencer.id, influencer.handle);
  const [state, formAction, pending] = useActionState(bound, undefined);
  return (
    <form action={formAction} data-testid="link-experiment-form" className="mt-3 flex flex-wrap items-end gap-3">
      <label className="min-w-60 flex-1 text-[10px] uppercase tracking-wider text-faint">
        {lang === "en" ? "Published post" : "Publicación"}
        <select name="shortcode" required className="mt-1 block w-full border-b border-border-faint bg-transparent py-2 text-xs normal-case text-ink outline-none focus:border-accent">
          <option value="" className="bg-surface">{lang === "en" ? "Choose a scraped post" : "Elige una publicación capturada"}</option>
          {posts.map((post) => (
            <option key={post.shortcode} value={post.shortcode} className="bg-surface">
              {new Date(post.posted_at).toLocaleDateString(lang === "en" ? "en-US" : "es-ES")} · {post.post_type} · {post.shortcode}
            </option>
          ))}
        </select>
      </label>
      <button type="submit" disabled={pending} className="min-h-10 rounded-sm bg-accent px-4 font-mono text-[10px] font-semibold uppercase tracking-wider text-canvas-deep disabled:opacity-60">
        {pending ? "…" : lang === "en" ? "Link & start" : "Vincular e iniciar"}
      </button>
      <Message state={state} />
    </form>
  );
}

function LifecycleButton({ action, influencer, kind }: { action: RecommendationAction; influencer: Influencer; kind: "abandon" | "acknowledge" }) {
  const { lang } = useLanguage();
  const serverAction = kind === "abandon" ? abandonExperiment : acknowledgeOutcome;
  const bound = serverAction.bind(null, action.id, influencer.id, influencer.handle);
  const [state, formAction, pending] = useActionState(bound, undefined);
  return (
    <form action={formAction}>
      <button type="submit" disabled={pending} className="min-h-10 rounded-md border border-border px-3 text-xs text-ink hover:border-accent disabled:opacity-60">
        {pending ? "…" : kind === "abandon" ? (lang === "en" ? "Abandon" : "Abandonar") : (lang === "en" ? "Acknowledge outcome" : "Marcar como revisado")}
      </button>
      <Message state={state} />
    </form>
  );
}

function PillarOverride({ influencer, post, tag, pillars }: { influencer: Influencer; post: PostSnapshot; tag: PostStrategyTag | null; pillars: string[] }) {
  const { lang } = useLanguage();
  const bound = overridePostPillar.bind(null, influencer.id, influencer.handle, post.shortcode);
  const [state, formAction, pending] = useActionState(bound, undefined);
  return (
    <form action={formAction} className="flex min-w-0 items-center gap-2">
      <select name="pillar" defaultValue={tag?.pillar ?? ""} aria-label={`${lang === "en" ? "Pillar for" : "Pilar de"} ${post.shortcode}`} className="min-w-0 flex-1 border-b border-border-faint bg-transparent py-1 text-xs text-ink outline-none focus:border-accent">
        <option value="" className="bg-surface">{lang === "en" ? "Unassigned" : "Sin asignar"}</option>
        {tag?.removed_pillar && tag.pillar ? <option value={tag.pillar} className="bg-surface">⚠ {tag.pillar}</option> : null}
        {pillars.map((pillar) => <option key={pillar} value={pillar} className="bg-surface">{pillar}</option>)}
      </select>
      <button type="submit" disabled={pending} className="min-h-9 rounded-sm border border-border px-2 font-mono text-[9px] uppercase text-muted hover:border-accent disabled:opacity-60">
        {lang === "en" ? "Override" : "Cambiar"}
      </button>
      {state?.error ? <span role="alert" className="text-xs text-negative">{state.error}</span> : null}
    </form>
  );
}

export function ExperimentPanel({
  influencer,
  actions,
  posts,
  tags,
  pillars,
  performance,
}: {
  influencer: Influencer;
  actions: RecommendationAction[];
  posts: PostSnapshot[];
  tags: PostStrategyTag[];
  pillars: string[];
  performance: PillarPerformance[];
}) {
  const { lang } = useLanguage();
  const experiments = actions.filter((action) => action.decision === "try" && action.experiment_status);
  const tagByShortcode = new Map(tags.map((tag) => [tag.shortcode, tag] as const));
  return (
    <section className="panel mb-14 p-7 sm:p-9" data-testid="experiment-panel">
      <div className="mb-6">
        <h2 className="font-mono text-xs tracking-widest text-accent">{lang === "en" ? "EXPERIMENTS · STRATEGY PERFORMANCE" : "EXPERIMENTOS · RENDIMIENTO ESTRATÉGICO"}</h2>
        <p className="mt-2 max-w-3xl text-xs leading-relaxed text-muted">
          {lang === "en" ? "Shared directional evidence only. Comparisons do not establish causal lift." : "Evidencia direccional compartida. Las comparaciones no demuestran un efecto causal."}
        </p>
      </div>

      <div className="space-y-4">
        {experiments.length === 0 ? <p className="text-sm text-muted">{lang === "en" ? "No experiments yet. Choose Try on a recommendation to begin." : "Aún no hay experimentos. Elige Probar en una recomendación."}</p> : null}
        {experiments.map((action) => (
          <article key={action.id} className="rounded-md border border-border-faint bg-canvas-deep/30 p-4" data-action-id={action.id} data-experiment-status={action.experiment_status ?? ""}>
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <p className="font-mono text-[10px] uppercase tracking-wider text-faint">{action.experiment_status}</p>
                <p className="mt-1 text-sm text-ink">{action.shared_note || (lang === "en" ? "Recommendation experiment" : "Experimento de recomendación")}</p>
                {action.linked_shortcode ? <a href={`https://www.instagram.com/p/${action.linked_shortcode}/`} target="_blank" rel="noreferrer" className="mt-1 inline-block text-xs text-accent">{action.linked_shortcode} →</a> : null}
                {action.review_at && action.experiment_status === "published" ? <p className="mt-1 text-xs text-muted">{lang === "en" ? "Seven-day review" : "Revisión a siete días"}: {new Date(action.review_at).toLocaleDateString(lang === "en" ? "en-US" : "es-ES")}</p> : null}
              </div>
              {action.experiment_status === "planned" || action.experiment_status === "published" ? <LifecycleButton action={action} influencer={influencer} kind="abandon" /> : null}
            </div>
            {action.experiment_status === "planned" ? <LinkForm action={action} influencer={influencer} posts={posts} /> : null}
            {action.experiment_status === "evaluated" && action.outcome ? (
              <div className="mt-4 border-t border-border-faint pt-4">
                <div className="grid gap-3 sm:grid-cols-3">
                  <p className="text-xs text-muted"><span className="block font-mono text-[9px] uppercase text-faint">{lang === "en" ? "Interactions" : "Interacciones"}</span>{formatCount(action.outcome.target.interactions)} · {action.outcome.interaction_delta_pct == null ? "—" : `${action.outcome.interaction_delta_pct > 0 ? "+" : ""}${action.outcome.interaction_delta_pct}%`}</p>
                  <p className="text-xs text-muted"><span className="block font-mono text-[9px] uppercase text-faint">{lang === "en" ? "Baseline" : "Referencia"}</span>{action.outcome.baseline.interactions_median == null ? "—" : formatCount(action.outcome.baseline.interactions_median)} · n={action.outcome.baseline.sample_size}</p>
                  <p className="text-xs text-muted"><span className="block font-mono text-[9px] uppercase text-faint">{lang === "en" ? "Confidence" : "Confianza"}</span>{action.outcome.confidence}</p>
                </div>
                <p className="mt-3 text-[10px] text-faint">{action.outcome.disclaimer}</p>
                {!action.acknowledged_at ? <div className="mt-3"><LifecycleButton action={action} influencer={influencer} kind="acknowledge" /></div> : <p className="mt-3 text-xs text-positive">{lang === "en" ? "Outcome reviewed" : "Resultado revisado"}</p>}
              </div>
            ) : null}
          </article>
        ))}
      </div>

      <div className="mt-8 border-t border-border-faint pt-6">
        <h3 className="font-mono text-[10px] uppercase tracking-widest text-faint">{lang === "en" ? "Pillar performance · paid separated" : "Rendimiento por pilar · pago separado"}</h3>
        {performance.length ? (
          <div className="mt-3 overflow-x-auto"><table className="w-full min-w-[560px] text-left text-xs"><thead><tr className="border-b border-border-faint text-faint"><th className="py-2">{lang === "en" ? "PILLAR" : "PILAR"}</th><th>{lang === "en" ? "STATUS" : "ESTADO"}</th><th className="text-right">MEDIAN ENG.</th><th className="text-right">VIEWS</th><th className="text-right">SAMPLE</th><th className="text-right">CONFIDENCE</th></tr></thead><tbody>{performance.map((row) => <tr key={`${row.pillar}-${row.paidStatus}`} className="border-b border-border-faint"><td className="py-2 text-ink">{row.pillar}</td><td className="text-muted">{row.paidStatus}</td><td className="font-mono text-right text-ink">{formatCount(row.interactionsMedian)}</td><td className="font-mono text-right text-muted">{row.viewsMedian == null ? "—" : formatCount(row.viewsMedian)}</td><td className="font-mono text-right text-muted">n={row.sampleSize}</td><td className="text-right text-muted">{row.confidence}</td></tr>)}</tbody></table></div>
        ) : <p className="mt-3 text-sm text-muted">{lang === "en" ? "Pillar performance appears after posts are tagged." : "El rendimiento aparece cuando se etiquetan publicaciones."}</p>}
      </div>

      {posts.length ? (
        <div className="mt-8 border-t border-border-faint pt-6">
          <h3 className="font-mono text-[10px] uppercase tracking-widest text-faint">{lang === "en" ? "POST PILLAR OVERRIDES" : "AJUSTES DE PILAR"}</h3>
          <div className="mt-3 grid gap-3 sm:grid-cols-2">
            {posts.slice(0, 8).map((post) => {
              const tag = tagByShortcode.get(post.shortcode) ?? null;
              return <div key={post.shortcode} className="rounded-md border border-border-faint p-3"><div className="mb-2 flex items-center justify-between gap-2"><a href={`https://www.instagram.com/p/${post.shortcode}/`} target="_blank" rel="noreferrer" className="text-xs text-accent">{post.shortcode}</a><span className="text-[9px] uppercase text-faint">{tag?.source ?? "untagged"}{tag?.removed_pillar ? " · removed pillar" : ""}</span></div><PillarOverride influencer={influencer} post={post} tag={tag} pillars={pillars} /></div>;
            })}
          </div>
        </div>
      ) : null}
    </section>
  );
}
