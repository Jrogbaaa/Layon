import Link from "next/link";
import { logout } from "@/app/actions/auth";
import { NavLinks } from "@/app/components/NavLinks";
import { LanguageToggle } from "@/app/components/LanguageToggle";

export function Nav() {
  const tonight = new Date().toLocaleDateString("en-US", {
    weekday: "short",
    month: "short",
    day: "numeric",
  });

  return (
    <header className="sticky top-0 z-40 border-b border-border-faint bg-canvas/85 backdrop-blur-md">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-3.5">
        <Link href="/" className="font-display text-xl tracking-tight text-ink">
          Look After <em className="not-italic text-accent">You</em>
        </Link>
        <nav className="flex items-center gap-6 text-sm font-medium text-muted">
          <span className="font-mono hidden text-xs text-faint sm:inline" aria-hidden>
            {tonight}
          </span>
          <NavLinks />
          <LanguageToggle />
          <form action={logout}>
            <button type="submit" className="text-muted transition-colors hover:text-ink">
              Log out
            </button>
          </form>
        </nav>
      </div>
    </header>
  );
}
