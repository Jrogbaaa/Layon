"use client";

import { useLanguage } from "@/app/components/LanguageProvider";
import type { AttentionPriority } from "@/app/lib/types";

export function NextActionPanel({ action }: { action: AttentionPriority }) {
  const { lang } = useLanguage();
  return (
    <section data-testid="next-action" className="mb-8 border-l-2 border-accent bg-surface px-5 py-4">
      <p className="font-mono text-[10px] uppercase tracking-widest text-accent">
        {lang === "en" ? "Next action" : "Próxima acción"}
      </p>
      <p className="mt-1 text-sm font-medium text-ink">{action.label[lang]}</p>
      {action.detail ? <p className="mt-1 max-w-3xl text-xs leading-relaxed text-muted">{action.detail[lang]}</p> : null}
    </section>
  );
}
