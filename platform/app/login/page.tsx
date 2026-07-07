"use client";

import { useActionState } from "react";
import { login } from "@/app/actions/auth";

export default function LoginPage() {
  const [state, formAction, pending] = useActionState(login, undefined);

  return (
    <div className="flex flex-1 items-center justify-center bg-canvas px-4">
      <form action={formAction} className="card w-full max-w-sm p-8">
        <h1 className="font-display mb-1 text-xl font-bold tracking-tight text-ink">
          You First{" "}
          <span className="bg-gradient-to-r from-accent-2 to-accent bg-clip-text text-transparent">
            Gersh
          </span>
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
          className="mb-4 w-full rounded-lg border border-border bg-canvas px-3 py-2 text-ink outline-none focus:border-accent"
        />

        {state?.error && <p className="mb-4 text-sm text-negative">{state.error}</p>}

        <button
          type="submit"
          disabled={pending}
          className="w-full rounded-lg bg-gradient-to-r from-accent-2 to-accent px-3 py-2 font-semibold text-white transition hover:opacity-90 disabled:opacity-50"
        >
          {pending ? "Checking..." : "Enter"}
        </button>
      </form>
    </div>
  );
}
