"use client";

import { useActionState, useEffect, useState } from "react";
import { saveTalentStrategy, type StrategyActionState } from "@/app/actions/strategy";
import { useLanguage } from "@/app/components/LanguageProvider";
import {
  getCaptureFreshness,
  isRecommendationOlderThanStrategy,
  isStrategyHorizonExpired,
  isStrategyReviewStale,
} from "@/app/lib/freshness";
import type { Influencer, TalentStrategy } from "@/app/lib/types";

const FORMAT_OPTIONS = ["photo", "video", "reel", "carousel"] as const;

const copy = {
  en: {
    heading: "CURRENT DIRECTION",
    edit: "Edit strategy",
    add: "Add current strategy",
    shared: "Shared context — everything here is visible and editable by everyone with dashboard access.",
    empty: "No current strategy has been set. Add only context that is suitable for both the agency and talent to read.",
    capture: "Instagram data",
    strategy: "Strategy review",
    recommendation: "Recommendation",
    current: "Current",
    stale: "Stale",
    missing: "Missing",
    notSet: "Not set",
    reviewDue: "Review due",
    expired: "Horizon passed",
    refreshNeeded: "Refresh needed",
    objective: "Current objective",
    horizon: "Horizon",
    audience: "Target audience",
    pillars: "Content pillars",
    formats: "Formats to develop",
    tone: "Tone and creative direction",
    guardrails: "Guardrails",
    commercial: "Commercial direction",
    constraints: "Posting constraints",
    save: "Save and mark reviewed",
    saving: "Saving…",
    cancel: "Cancel",
    saved: "Strategy saved.",
    directionGroup: "Direction",
    boundariesGroup: "Creative boundaries",
    pillarsHelp: "Comma-separated, up to 8.",
  },
  es: {
    heading: "DIRECCIÓN ACTUAL",
    edit: "Editar estrategia",
    add: "Añadir estrategia actual",
    shared: "Contexto compartido: todo es visible y editable para quienes acceden al panel.",
    empty: "Aún no hay una estrategia actual. Añade solo contexto apto para la agencia y el talento.",
    capture: "Datos de Instagram",
    strategy: "Revisión de estrategia",
    recommendation: "Recomendación",
    current: "Actual",
    stale: "Desactualizados",
    missing: "Sin datos",
    notSet: "Sin definir",
    reviewDue: "Revisión pendiente",
    expired: "Horizonte vencido",
    refreshNeeded: "Actualizar",
    objective: "Objetivo actual",
    horizon: "Horizonte",
    audience: "Audiencia objetivo",
    pillars: "Pilares de contenido",
    formats: "Formatos a desarrollar",
    tone: "Tono y dirección creativa",
    guardrails: "Límites creativos",
    commercial: "Dirección comercial",
    constraints: "Limitaciones de publicación",
    save: "Guardar y marcar revisada",
    saving: "Guardando…",
    cancel: "Cancelar",
    saved: "Estrategia guardada.",
    directionGroup: "Dirección",
    boundariesGroup: "Límites creativos",
    pillarsHelp: "Separados por comas, máximo 8.",
  },
} as const;

function StatusItem({ label, value, alert = false }: { label: string; value: string; alert?: boolean }) {
  return (
    <div className="flex items-center justify-between gap-4 border-b border-border-faint py-2.5 last:border-b-0 sm:block sm:border-b-0 sm:border-r sm:px-5 sm:first:pl-0 sm:last:border-r-0">
      <dt className="text-xs text-faint">{label}</dt>
      <dd className={`font-mono mt-1 text-xs ${alert ? "text-negative" : "text-muted"}`}>{value}</dd>
    </div>
  );
}

function StrategyForm({
  influencer,
  strategy,
  onCancel,
}: {
  influencer: Influencer;
  strategy: TalentStrategy | null;
  onCancel: () => void;
}) {
  const { lang } = useLanguage();
  const t = copy[lang];
  const action = saveTalentStrategy.bind(null, influencer.id, influencer.handle);
  const [state, formAction, pending] = useActionState<StrategyActionState, FormData>(action, undefined);

  useEffect(() => {
    if (state?.success) onCancel();
  }, [state?.success, onCancel]);

  const inputClass =
    "mt-1.5 w-full rounded-md border border-border-faint bg-canvas px-3 py-2.5 text-sm text-ink placeholder:text-faint focus:border-accent";

  return (
    <form action={formAction} className="mt-6 space-y-5">
      <fieldset className="grid gap-4 sm:grid-cols-2">
        <legend className="font-mono mb-3 text-xs text-faint">{t.directionGroup}</legend>
        <label className="text-sm text-muted sm:col-span-2">
          {t.objective}
          <textarea name="current_objective" maxLength={500} rows={3} defaultValue={strategy?.current_objective} className={inputClass} />
        </label>
        <label className="text-sm text-muted">
          {t.horizon}
          <input name="horizon" type="date" defaultValue={strategy?.horizon ?? ""} className={inputClass} />
        </label>
        <label className="text-sm text-muted">
          {t.audience}
          <input name="target_audience" maxLength={500} defaultValue={strategy?.target_audience} className={inputClass} />
        </label>
        <label className="text-sm text-muted sm:col-span-2">
          {t.pillars}
          <input
            name="content_pillars"
            defaultValue={strategy?.content_pillars.join(", ")}
            aria-describedby="content-pillars-help"
            className={inputClass}
          />
          <span id="content-pillars-help" className="mt-1 block text-xs text-faint">{t.pillarsHelp}</span>
        </label>
      </fieldset>

      <fieldset className="border-t border-border-faint pt-5">
        <legend className="font-mono mb-3 text-xs text-faint">{t.boundariesGroup}</legend>
        <div className="grid gap-4 sm:grid-cols-2">
          <div className="sm:col-span-2">
            <p className="text-sm text-muted">{t.formats}</p>
            <div className="mt-2 flex flex-wrap gap-x-5 gap-y-2">
              {FORMAT_OPTIONS.map((format) => (
                <label key={format} className="inline-flex items-center gap-2 text-sm capitalize text-ink">
                  <input
                    type="checkbox"
                    name="development_formats"
                    value={format}
                    defaultChecked={strategy?.development_formats.includes(format)}
                    className="h-4 w-4 accent-[var(--accent)]"
                  />
                  {format}
                </label>
              ))}
            </div>
          </div>
          <label className="text-sm text-muted">
            {t.tone}
            <textarea name="tone" maxLength={1000} rows={3} defaultValue={strategy?.tone} className={inputClass} />
          </label>
          <label className="text-sm text-muted">
            {t.guardrails}
            <textarea name="guardrails" maxLength={1000} rows={3} defaultValue={strategy?.guardrails} className={inputClass} />
          </label>
          <label className="text-sm text-muted">
            {t.commercial}
            <textarea name="commercial_direction" maxLength={500} rows={2} defaultValue={strategy?.commercial_direction} className={inputClass} />
          </label>
          <label className="text-sm text-muted">
            {t.constraints}
            <textarea name="posting_constraints" maxLength={1000} rows={2} defaultValue={strategy?.posting_constraints} className={inputClass} />
          </label>
        </div>
      </fieldset>

      {state?.error ? <p role="alert" className="text-sm text-negative">{state.error}</p> : null}
      {state?.success ? <p role="status" className="text-sm text-positive">{t.saved}</p> : null}
      <div className="flex flex-wrap items-center gap-3">
        <button type="submit" disabled={pending} className="rounded-md bg-accent px-4 py-2.5 text-sm font-semibold text-canvas-deep transition-colors hover:bg-accent-bright disabled:cursor-wait disabled:opacity-60">
          {pending ? t.saving : t.save}
        </button>
        <button type="button" onClick={onCancel} className="min-h-11 px-3 text-sm text-muted transition-colors hover:text-ink">
          {t.cancel}
        </button>
      </div>
    </form>
  );
}

export function StrategyPanel({
  influencer,
  strategy,
  latestCaptureAt,
  recommendationGeneratedAt,
}: {
  influencer: Influencer;
  strategy: TalentStrategy | null;
  latestCaptureAt: string | null;
  recommendationGeneratedAt: string | null;
}) {
  const { lang } = useLanguage();
  const t = copy[lang];
  const [editing, setEditing] = useState(false);
  const capture = getCaptureFreshness(latestCaptureAt);
  const reviewStale = isStrategyReviewStale(strategy?.reviewed_at);
  const horizonExpired = isStrategyHorizonExpired(strategy?.horizon);
  const recommendationStale = isRecommendationOlderThanStrategy(recommendationGeneratedAt, strategy?.updated_at);
  const hasStrategy = Boolean(
    strategy &&
      (strategy.current_objective || strategy.target_audience || strategy.content_pillars.length || strategy.tone || strategy.guardrails),
  );

  const rows = strategy
    ? [
        [t.objective, strategy.current_objective],
        [t.horizon, strategy.horizon],
        [t.audience, strategy.target_audience],
        [t.pillars, strategy.content_pillars.join(" · ")],
        [t.formats, strategy.development_formats.join(" · ")],
        [t.tone, strategy.tone],
        [t.guardrails, strategy.guardrails],
        [t.commercial, strategy.commercial_direction],
        [t.constraints, strategy.posting_constraints],
      ].filter((row): row is [string, string] => Boolean(row[1]))
    : [];

  return (
    <section className="panel mt-10 mb-14 p-6 sm:p-8" data-testid="strategy-panel">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h2 className="font-mono text-xs tracking-widest text-accent">{t.heading}</h2>
          <p className="mt-2 max-w-2xl text-xs leading-relaxed text-muted">{t.shared}</p>
        </div>
        {!editing ? (
          <button type="button" onClick={() => setEditing(true)} className="min-h-11 rounded-md border border-border px-3.5 text-sm text-ink transition-colors hover:border-accent hover:text-accent">
            {hasStrategy ? t.edit : t.add}
          </button>
        ) : null}
      </div>

      <dl className="mt-5 border-y border-border-faint sm:grid sm:grid-cols-3">
        <StatusItem label={t.capture} value={t[capture]} alert={capture !== "current"} />
        <StatusItem
          label={t.strategy}
          value={!strategy ? t.notSet : horizonExpired ? t.expired : reviewStale ? t.reviewDue : t.current}
          alert={!strategy || horizonExpired || reviewStale}
        />
        <StatusItem
          label={t.recommendation}
          value={!recommendationGeneratedAt ? t.missing : recommendationStale ? t.refreshNeeded : t.current}
          alert={!recommendationGeneratedAt || recommendationStale}
        />
      </dl>

      {editing ? (
        <StrategyForm influencer={influencer} strategy={strategy} onCancel={() => setEditing(false)} />
      ) : rows.length > 0 ? (
        <dl className="mt-6 grid gap-x-8 gap-y-5 sm:grid-cols-2">
          {rows.map(([label, value]) => (
            <div key={label}>
              <dt className="text-xs text-faint">{label}</dt>
              <dd className="mt-1 max-w-prose text-sm leading-relaxed text-ink">{value}</dd>
            </div>
          ))}
        </dl>
      ) : (
        <p className="mt-6 max-w-2xl text-sm leading-relaxed text-muted">{t.empty}</p>
      )}
    </section>
  );
}
