import Link from "next/link";
import { logout } from "@/app/actions/auth";

export function Nav() {
  return (
    <header className="border-b border-neutral-800 bg-neutral-950">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
        <Link href="/" className="text-lg font-semibold tracking-tight text-neutral-50">
          You First <span className="text-amber-500">Gersh</span>
        </Link>
        <nav className="flex items-center gap-6 text-sm text-neutral-300">
          <Link href="/" className="hover:text-neutral-50">
            Roster
          </Link>
          <Link href="/trends" className="hover:text-neutral-50">
            Trends
          </Link>
          <form action={logout}>
            <button type="submit" className="text-neutral-500 hover:text-neutral-300">
              Log out
            </button>
          </form>
        </nav>
      </div>
    </header>
  );
}
