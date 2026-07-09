"use client";

import ReactMarkdown from "react-markdown";
import { useLanguage } from "@/app/components/LanguageProvider";

type BilingualText = { en: string; es: string };
type Bullet = {
  text: string | BilingualText;
  reason?: string | BilingualText | null;
  shortcode?: string | null;
};

function parseBullets(content: string): Bullet[] | null {
  try {
    const parsed = JSON.parse(content);
    if (parsed && Array.isArray(parsed.bullets)) {
      return parsed.bullets as Bullet[];
    }
  } catch {
    // not JSON — fall through to markdown rendering
  }
  return null;
}

function pick(value: string | BilingualText | null | undefined, lang: "en" | "es"): string | null {
  if (value == null) return null;
  return typeof value === "string" ? value : value[lang];
}

export function RecommendationContent({ content }: { content: string }) {
  const { lang } = useLanguage();
  const bullets = parseBullets(content);

  if (bullets) {
    return (
      <ol className="space-y-5">
        {bullets.map((bullet, i) => (
          <li key={i} className="flex gap-4">
            <span className="font-mono mt-0.5 text-xs text-accent" aria-hidden>
              {String(i + 1).padStart(2, "0")}
            </span>
            <div>
              <p className="max-w-prose text-sm font-medium leading-relaxed text-ink">
                {pick(bullet.text, lang)}
              </p>
              {bullet.reason ? (
                <p className="mt-1 max-w-prose text-xs leading-relaxed text-muted">
                  {pick(bullet.reason, lang)}
                </p>
              ) : null}
              {bullet.shortcode ? (
                <a
                  href={`https://www.instagram.com/p/${bullet.shortcode}/`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="mt-1 inline-block text-xs text-accent hover:text-accent-bright"
                >
                  Ver post →
                </a>
              ) : null}
            </div>
          </li>
        ))}
      </ol>
    );
  }

  return (
    <div className="prose prose-sm max-w-none prose-headings:font-medium prose-headings:text-ink prose-p:text-ink prose-li:text-ink prose-strong:text-ink">
      <ReactMarkdown>{content}</ReactMarkdown>
    </div>
  );
}
