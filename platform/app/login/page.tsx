"use client";

import { useActionState } from "react";
import { login } from "@/app/actions/auth";

export default function LoginPage() {
  const [state, formAction, pending] = useActionState(login, undefined);

  return (
    <div className="flex flex-1 items-center justify-center bg-neutral-950 px-4">
      <form
        action={formAction}
        className="w-full max-w-sm rounded-2xl border border-neutral-800 bg-neutral-900 p-8 shadow-xl"
      >
        <h1 className="mb-1 text-xl font-semibold text-neutral-50">You First Gersh</h1>
        <p className="mb-6 text-sm text-neutral-400">Influencer Insights Platform</p>

        <label htmlFor="password" className="mb-2 block text-sm text-neutral-300">
          Password
        </label>
        <input
          id="password"
          name="password"
          type="password"
          required
          autoFocus
          className="mb-4 w-full rounded-lg border border-neutral-700 bg-neutral-950 px-3 py-2 text-neutral-50 outline-none focus:border-amber-500"
        />

        {state?.error && <p className="mb-4 text-sm text-red-400">{state.error}</p>}

        <button
          type="submit"
          disabled={pending}
          className="w-full rounded-lg bg-amber-500 px-3 py-2 font-medium text-neutral-950 transition hover:bg-amber-400 disabled:opacity-50"
        >
          {pending ? "Checking..." : "Enter"}
        </button>
      </form>
    </div>
  );
}
