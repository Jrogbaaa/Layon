"use client";

import { useEffect, useRef } from "react";

/** Animates a numeral from 0 to its value when it enters the viewport.
 *  Server-renders the final value, so no-JS and reduced-motion see it instantly. */
export function CountUp({
  value,
  format = "plain",
  className = "",
}: {
  value: number;
  format?: "plain" | "compact";
  className?: string;
}) {
  const ref = useRef<HTMLSpanElement>(null);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    if (value === 0) return;

    const fmt = (n: number) =>
      format === "compact" ? formatCompact(n) : Math.round(n).toLocaleString("en-US");

    let raf = 0;
    const io = new IntersectionObserver(([entry]) => {
      if (!entry.isIntersecting) return;
      io.disconnect();
      const t0 = performance.now();
      const dur = 1100;
      const tick = (now: number) => {
        const t = Math.min((now - t0) / dur, 1);
        // ease-out-quint
        const e = 1 - Math.pow(1 - t, 5);
        el.textContent = fmt(value * e);
        if (t < 1) raf = requestAnimationFrame(tick);
      };
      raf = requestAnimationFrame(tick);
    });
    io.observe(el);
    return () => {
      io.disconnect();
      cancelAnimationFrame(raf);
    };
  }, [value, format]);

  return (
    <span ref={ref} className={`tnum ${className}`}>
      {format === "compact" ? formatCompact(value) : value.toLocaleString("en-US")}
    </span>
  );
}

function formatCompact(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}K`;
  return `${Math.round(n).toLocaleString("en-US")}`;
}
