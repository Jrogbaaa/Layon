"use client";

import { useLanguage } from "@/app/components/LanguageProvider";

export function LanguageToggle() {
  const { lang, toggle } = useLanguage();

  return (
    <button
      type="button"
      onClick={toggle}
      className="rounded-full border border-border px-3 py-1 text-xs font-medium text-muted hover:text-ink"
    >
      {lang === "en" ? "EN" : "ES"}
    </button>
  );
}
