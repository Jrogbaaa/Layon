import Link from "next/link";
import { logout } from "@/app/actions/auth";

export function Nav() {
  return (
    <header className="border-b border-border bg-card">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
        <Link href="/" className="font-display text-lg font-extrabold tracking-tight text-ink">
          You First <span className="text-accent">Gersh</span>
        </Link>
        <nav className="flex items-center gap-6 text-sm font-medium text-muted">
          <Link href="/" className="hover:text-ink">
            Roster
          </Link>
          <Link href="/trends" className="hover:text-ink">
            Trends
          </Link>
          <form action={logout}>
            <button type="submit" className="text-muted hover:text-ink">
              Log out
            </button>
          </form>
        </nav>
      </div>
    </header>
  );
}
