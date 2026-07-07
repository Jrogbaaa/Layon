import type { ReactNode } from "react";

export function HighlightContent({ content }: { content: string }) {
  const parts: ReactNode[] = [];
  let lastIndex = 0;
  const re = /post\s+([A-Za-z0-9_-]+)/g;
  let match: RegExpExecArray | null;

  while ((match = re.exec(content)) !== null) {
    const shortcode = match[1];
    const prefix = match[0].slice(0, match[0].length - shortcode.length);

    if (match.index > lastIndex) {
      parts.push(content.slice(lastIndex, match.index));
    }
    parts.push(prefix);
    parts.push(
      <a
        key={`${shortcode}-${match.index}`}
        href={`https://www.instagram.com/p/${shortcode}/`}
        target="_blank"
        rel="noopener noreferrer"
        className="text-accent hover:underline"
      >
        {shortcode}
      </a>,
    );
    lastIndex = match.index + match[0].length;
  }

  if (parts.length === 0) {
    return <>{content}</>;
  }

  if (lastIndex < content.length) {
    parts.push(content.slice(lastIndex));
  }

  return <>{parts}</>;
}
