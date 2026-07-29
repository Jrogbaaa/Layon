import { getCaptureFreshness } from "@/app/lib/freshness";
import type {
  AttentionPriority,
  Highlight,
  Recommendation,
  RecommendationAction,
} from "@/app/lib/types";

type Bullet = { text?: string | { en?: string; es?: string } };

function text(value: Bullet["text"], language: "en" | "es"): string {
  if (typeof value === "string") return value;
  return value?.[language] ?? value?.en ?? value?.es ?? "";
}

function recommendationBullets(recommendation: Recommendation | null): Bullet[] {
  if (!recommendation) return [];
  try {
    const parsed = JSON.parse(recommendation.content) as { bullets?: unknown };
    return Array.isArray(parsed.bullets) ? (parsed.bullets as Bullet[]) : [];
  } catch {
    return [];
  }
}

export function deriveNextAction({
  latestCaptureAt,
  highlights,
  recommendation,
  actions,
  now = new Date(),
}: {
  latestCaptureAt: string | null;
  highlights: Highlight[];
  recommendation: Recommendation | null;
  actions: RecommendationAction[];
  now?: Date;
}): AttentionPriority {
  const freshness = getCaptureFreshness(latestCaptureAt, now);
  if (freshness === "missing") {
    return {
      kind: "missing_data",
      priority: 60,
      label: { en: "Restore Instagram evidence", es: "Restaurar datos de Instagram" },
      detail: { en: "No profile capture is available.", es: "No hay una captura de perfil disponible." },
    };
  }
  if (freshness === "stale") {
    return {
      kind: "stale_data",
      priority: 50,
      label: { en: "Refresh Instagram evidence", es: "Actualizar datos de Instagram" },
      detail: { en: "The latest capture is more than 36 hours old.", es: "La última captura tiene más de 36 horas." },
    };
  }

  const ready = actions.find(
    (action) => action.experiment_status === "evaluated" && Boolean(action.outcome) && !action.acknowledged_at,
  );
  if (ready) {
    return {
      kind: "review_experiment",
      priority: 45,
      label: { en: "Review experiment outcome", es: "Revisar resultado del experimento" },
      detail: null,
    };
  }

  const warning = highlights.find((highlight) => highlight.metric?.severity === "warning");
  if (warning) {
    return {
      kind: "warning",
      priority: 40,
      label: { en: "Discuss the warning signal", es: "Revisar la señal de alerta" },
      detail: { en: warning.content, es: warning.content },
    };
  }

  const active = actions.find(
    (action) => action.experiment_status === "planned" || action.experiment_status === "published",
  );
  if (active) {
    return {
      kind: "active_experiment",
      priority: 30,
      label: {
        en: active.experiment_status === "published" ? "Monitor active experiment" : "Plan the chosen experiment",
        es: active.experiment_status === "published" ? "Seguir el experimento activo" : "Planificar el experimento elegido",
      },
      detail: null,
    };
  }

  const answered = new Set(
    actions
      .filter((action) => action.recommendation_id === recommendation?.id)
      .map((action) => action.bullet_index),
  );
  const unanswered = recommendationBullets(recommendation).findIndex((_, index) => !answered.has(index));
  if (unanswered >= 0) {
    const bullet = recommendationBullets(recommendation)[unanswered];
    return {
      kind: "recommendation",
      priority: 20,
      label: { en: "Respond to the latest recommendation", es: "Responder a la última recomendación" },
      detail: { en: text(bullet.text, "en"), es: text(bullet.text, "es") },
    };
  }

  return {
    kind: "none",
    priority: 0,
    label: { en: "No immediate action", es: "Sin acción inmediata" },
    detail: null,
  };
}
