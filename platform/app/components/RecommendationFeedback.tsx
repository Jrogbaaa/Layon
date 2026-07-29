"use client";

import { useActionState, useState } from "react";
import { respondToRecommendation } from "@/app/actions/recommendation";
import { useLanguage } from "@/app/components/LanguageProvider";
import type { RecommendationAction, RecommendationDecision } from "@/app/lib/types";

const LABELS: Record<RecommendationDecision, { en: string; es: string }> = {
  try: { en: "Try", es: "Probar" },
  not_relevant: { en: "Not relevant", es: "No relevante" },
  already_planned: { en: "Already planned", es: "Ya planificado" },
  talent_declined: { en: "Talent declined", es: "Talento no interesado" },
  revisit: { en: "Revisit", es: "Revisar más adelante" },
};

export function RecommendationFeedback({
  recommendationId,
  influencerId,
  handle,
  bulletIndex,
  current,
}: {
  recommendationId: number;
  influencerId: number;
  handle: string;
  bulletIndex: number;
  current: RecommendationAction | null;
}) {
  const { lang } = useLanguage();
  const [decision, setDecision] = useState<RecommendationDecision>(current?.decision ?? "try");
  const boundAction = respondToRecommendation.bind(null, recommendationId, influencerId, handle, bulletIndex);
  const [state, formAction, pending] = useActionState(boundAction, undefined);

  if (current && (current.experiment_status === "published" || current.experiment_status === "evaluated")) {
    return (
      <p className="mt-3 rounded-md border border-border-faint bg-canvas-deep/40 p-3 text-xs text-muted">
        {lang === "en" ? "This response is managed in Experiments below." : "Esta respuesta se gestiona en Experimentos más abajo."}
      </p>
    );
  }

  return (
    <form
      action={formAction}
      data-recommendation-id={recommendationId}
      data-influencer-id={influencerId}
      data-bullet-index={bulletIndex}
      className="mt-3 rounded-md border border-border-faint bg-canvas-deep/40 p-3"
    >
      <div className="flex flex-wrap items-end gap-3">
        <label className="min-w-44 flex-1 text-[10px] uppercase tracking-wider text-faint">
          {lang === "en" ? "Shared response" : "Respuesta compartida"}
          <select
            name="decision"
            value={decision}
            onChange={(event) => setDecision(event.target.value as RecommendationDecision)}
            className="mt-1 block w-full border-b border-border-faint bg-transparent py-1.5 text-xs normal-case text-ink outline-none focus:border-accent"
          >
            {(Object.keys(LABELS) as RecommendationDecision[]).map((value) => (
              <option key={value} value={value} className="bg-surface">
                {LABELS[value][lang]}
              </option>
            ))}
          </select>
        </label>
        {decision === "revisit" ? (
          <label className="text-[10px] uppercase tracking-wider text-faint">
            {lang === "en" ? "Revisit date" : "Fecha de revisión"}
            <input
              type="date"
              name="revisit_on"
              defaultValue={current?.revisit_on ?? ""}
              className="mt-1 block border-b border-border-faint bg-transparent py-1 text-xs normal-case text-ink outline-none focus:border-accent"
            />
          </label>
        ) : null}
        <button
          type="submit"
          disabled={pending}
          className="min-h-9 rounded-sm bg-accent px-4 font-mono text-[10px] font-semibold uppercase tracking-wider text-canvas-deep disabled:opacity-60"
        >
          {pending ? (lang === "en" ? "Saving…" : "Guardando…") : lang === "en" ? "Save" : "Guardar"}
        </button>
      </div>
      <label className="mt-3 block text-[10px] uppercase tracking-wider text-faint">
        {lang === "en" ? "Optional shared note" : "Nota compartida opcional"}
        <input
          name="shared_note"
          maxLength={500}
          defaultValue={current?.shared_note ?? ""}
          placeholder={lang === "en" ? "Visible to everyone with dashboard access" : "Visible para todos con acceso al dashboard"}
          className="mt-1 block w-full border-b border-border-faint bg-transparent py-1.5 text-xs normal-case text-ink outline-none placeholder:text-faint focus:border-accent"
        />
      </label>
      <p className="mt-2 text-[10px] text-faint">
        {lang === "en"
          ? "Shared with every dashboard visitor. Do not enter private talent information."
          : "Compartido con todos los visitantes del dashboard. No incluyas información privada del talento."}
      </p>
      {state?.success ? (
        <p className="mt-2 text-xs text-positive" role="status">
          {decision === "try"
            ? lang === "en" ? "Saved as a planned experiment." : "Guardado como experimento planificado."
            : lang === "en" ? "Response saved." : "Respuesta guardada."}
        </p>
      ) : null}
      {state?.error ? <p className="mt-2 text-xs text-negative" role="alert">{state.error}</p> : null}
    </form>
  );
}
