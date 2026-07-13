import type { TrendHeadlinesPayload } from "@/app/lib/types";

export function parseTrendHeadlines(content: string): TrendHeadlinesPayload["headlines"] | null {
  try {
    const parsed = JSON.parse(content);
    if (parsed && Array.isArray(parsed.headlines) && parsed.headlines.length > 0) {
      return parsed.headlines as TrendHeadlinesPayload["headlines"];
    }
  } catch {
    // not valid JSON
  }
  return null;
}
