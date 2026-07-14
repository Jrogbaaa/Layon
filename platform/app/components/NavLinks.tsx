"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const LINKS = [
  { href: "/", label: "Roster" },
  { href: "/trends", label: "Tips" },
] as const;

export function NavLinks() {
  const pathname = usePathname();

  return (
    <>
      {LINKS.map(({ href, label }) => {
        const active = href === "/" ? pathname === "/" || pathname.startsWith("/influencer") : pathname.startsWith(href);
        return (
          <Link
            key={href}
            href={href}
            aria-current={active ? "page" : undefined}
            className={`relative pb-0.5 transition-colors hover:text-ink ${
              active
                ? "text-ink after:absolute after:inset-x-0 after:-bottom-[1.05rem] after:h-px after:bg-accent"
                : ""
            }`}
          >
            {label}
          </Link>
        );
      })}
    </>
  );
}
