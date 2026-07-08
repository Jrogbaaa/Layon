"use client";

import Link from "next/link";
import { useLanguage } from "@/app/components/LanguageProvider";
import { LanguageToggle } from "@/app/components/LanguageToggle";
import type { BriefingPayload } from "@/app/lib/types";

function parseBriefing(content: string): BriefingPayload | null {
  try {
    const parsed = JSON.parse(content);
    if (parsed && parsed.summary && Array.isArray(parsed.patterns) && Array.isArray(parsed.actions)) {
      return parsed as BriefingPayload;
    }
  } catch {
    // malformed — treated as no briefing
  }
  return null;
}

export function RosterBriefing({
  content,
  generatedAt,
}: {
  content: string;
  generatedAt: string;
}) {
  const { lang } = useLanguage();
  const briefing = parseBriefing(content);

  if (!briefing) return null;

  const hasDetails = briefing.patterns.length > 0 || briefing.actions.length > 0;

  return (
    <section className="card mb-8 p-6">
      <div className="mb-1 flex items-center justify-between">
        <h2 className="text-lg font-semibold">This week across the roster</h2>
        <LanguageToggle />
      </div>
      <p className="mb-4 text-xs text-muted">
        Updated {new Date(generatedAt).toLocaleDateString(undefined, { month: "short", day: "numeric" })}
      </p>

      <p className="max-w-prose text-sm leading-relaxed text-ink">{briefing.summary[lang]}</p>

      {hasDetails ? (
        <details className="group mt-4">
          <summary className="cursor-pointer list-none text-sm font-medium text-accent-strong hover:underline">
            <span className="group-open:hidden">Show patterns &amp; actions ▸</span>
            <span className="hidden group-open:inline">Hide patterns &amp; actions ▾</span>
          </summary>

          {briefing.patterns.length > 0 ? (
            <div className="mt-4 mb-5">
              <h3 className="mb-2 text-sm font-semibold text-muted">Patterns found</h3>
              <ul className="space-y-2">
                {briefing.patterns.map((pattern, i) => (
                  <li key={i} className="rounded-xl border border-border bg-canvas px-4 py-3 text-sm text-ink">
                    <p className="max-w-prose">{pattern.finding[lang]}</p>
                    <p className="mt-1 max-w-prose text-xs text-muted">{pattern.evidence}</p>
                    <p className="mt-1 flex flex-wrap gap-2 text-xs">
                      {pattern.handles.map((handle) => (
                        <Link
                          key={handle}
                          href={`/influencer/${handle}`}
                          className="text-accent-strong hover:underline"
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
            <div className="mt-4">
              <h3 className="mb-2 text-sm font-semibold text-muted">Priority actions</h3>
              <ul className="space-y-2">
                {briefing.actions.map((action, i) => (
                  <li key={i} className="rounded-xl border border-border bg-canvas px-4 py-3 text-sm text-ink">
                    <Link href={`/influencer/${action.handle}`} className="font-semibold hover:underline">
                      @{action.handle}
                    </Link>
                    <p className="mt-1 max-w-prose">{action.action[lang]}</p>
                    <p className="mt-1 max-w-prose text-xs text-muted">{action.reason[lang]}</p>
                    {action.shortcode ? (
                      <a
                        href={`https://www.instagram.com/p/${action.shortcode}/`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="mt-1 inline-block text-xs text-accent-strong hover:underline"
                      >
                        View post →
                      </a>
                    ) : null}
                  </li>
                ))}
              </ul>
            </div>
          ) : null}
        </details>
      ) : null}
    </section>
  );
}
