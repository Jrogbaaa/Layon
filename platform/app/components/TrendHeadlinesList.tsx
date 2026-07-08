"use client";

import { useLanguage } from "@/app/components/LanguageProvider";
import type { TrendHeadlinesPayload } from "@/app/lib/types";

function parseHeadlines(content: string): TrendHeadlinesPayload["headlines"] | null {
  try {
    const parsed = JSON.parse(content);
    if (parsed && Array.isArray(parsed.headlines)) {
      return parsed.headlines as TrendHeadlinesPayload["headlines"];
    }
  } catch {
    // not valid JSON
  }
  return null;
}

function hostname(url: string): string | null {
  try {
    return new URL(url).hostname.replace(/^www\./, "");
  } catch {
    return null;
  }
}

export function TrendHeadlinesList({ content }: { content: string }) {
  const { lang } = useLanguage();
  const headlines = parseHeadlines(content);

  if (!headlines) return null;

  return (
    <ol className="space-y-8">
      {headlines.map((headline, i) => {
        const source = headline.source_url ? hostname(headline.source_url) : null;
        return (
          <li key={i}>
            <p className="font-display text-3xl font-bold leading-tight tracking-tight text-ink sm:text-4xl">
              {headline.text[lang]}
            </p>
            {source && headline.source_url ? (
              <a
                href={headline.source_url}
                target="_blank"
                rel="noopener noreferrer"
                className="mt-1 inline-block text-xs text-muted hover:text-ink"
              >
                {source} →
              </a>
            ) : null}
          </li>
        );
      })}
    </ol>
  );
}
