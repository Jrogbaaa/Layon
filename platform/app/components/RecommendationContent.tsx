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
      <ul className="space-y-3">
        {bullets.map((bullet, i) => (
          <li key={i} className="rounded-xl border border-border bg-canvas px-4 py-3">
            <p className="text-sm font-medium text-ink">{pick(bullet.text, lang)}</p>
            {bullet.reason ? <p className="mt-1 text-xs text-muted">{pick(bullet.reason, lang)}</p> : null}
            {bullet.shortcode ? (
              <a
                href={`https://www.instagram.com/p/${bullet.shortcode}/`}
                target="_blank"
                rel="noopener noreferrer"
                className="mt-1 inline-block text-xs text-accent hover:underline"
              >
                Ver post →
              </a>
            ) : null}
          </li>
        ))}
      </ul>
    );
  }

  return (
    <div className="prose prose-sm max-w-none prose-headings:font-medium prose-headings:text-ink prose-p:text-ink prose-li:text-ink prose-strong:text-ink">
      <ReactMarkdown>{content}</ReactMarkdown>
    </div>
  );
}
