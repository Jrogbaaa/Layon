"use client";

import { useActionState } from "react";
import { login } from "@/app/actions/auth";

export default function LoginPage() {
  const [state, formAction, pending] = useActionState(login, undefined);

  return (
    <div className="flex flex-1 items-center justify-center bg-canvas px-4">
      <form action={formAction} className="card w-full max-w-sm p-8">
        <h1 className="font-display mb-1 text-xl font-bold tracking-tight text-ink">
          Look After <span className="text-accent">You</span>
        </h1>
        <p className="mb-6 text-sm text-muted">Influencer Insights Platform</p>

        <label htmlFor="password" className="mb-2 block text-sm font-medium text-ink">
          Password
        </label>
        <input
          id="password"
          name="password"
          type="password"
          required
          autoFocus
          autoComplete="current-password"
          aria-invalid={!!state?.error}
          aria-describedby="password-error"
          className="w-full rounded-lg border border-border bg-canvas px-3 py-2 text-ink outline-none focus:border-accent"
        />

        <p id="password-error" role="alert" className="min-h-5 my-2 text-sm text-negative">
          {state?.error}
        </p>

        <button
          type="submit"
          disabled={pending}
          className="w-full rounded-lg bg-accent-strong px-3 py-2 font-semibold text-white transition hover:opacity-90 disabled:opacity-50"
        >
          {pending ? "Signing in…" : "Sign in"}
        </button>

        <p className="mt-4 text-xs text-muted">
          Team access password — ask your manager if you don&apos;t have it.
        </p>
      </form>
    </div>
  );
}
