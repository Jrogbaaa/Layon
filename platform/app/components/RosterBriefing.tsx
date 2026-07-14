"use client";

import Link from "next/link";
import { useLanguage } from "@/app/components/LanguageProvider";
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
