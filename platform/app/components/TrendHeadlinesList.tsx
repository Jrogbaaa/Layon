"use client";

import { useLanguage } from "@/app/components/LanguageProvider";
import { Reveal } from "@/app/components/Reveal";
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
    <ol className="max-w-4xl">
      {headlines.map((headline, i) => {
        const source = headline.source_url ? hostname(headline.source_url) : null;
        return (
          <Reveal as="li" key={i} delay={Math.min(i * 60, 360)}>
            <div className="group flex gap-6 border-b border-border-faint py-9 first:pt-0 last:border-b-0 sm:gap-10">
              <span className="font-mono pt-2 text-xs text-accent" aria-hidden>
                {String(i + 1).padStart(2, "0")}
              </span>
              <div>
                <p className="display-hero text-3xl text-ink sm:text-[2.6rem]">
                  {headline.text[lang]}
                </p>
                {source && headline.source_url ? (
                  <a
                    href={headline.source_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="font-mono mt-3 inline-block text-xs text-faint transition-colors hover:text-accent"
                  >
                    {source} →
                  </a>
                ) : null}
              </div>
            </div>
          </Reveal>
        );
      })}
    </ol>
  );
}
