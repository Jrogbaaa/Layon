"use client";

import { useActionState } from "react";
import { login } from "@/app/actions/auth";
import { SilkCanvas } from "@/app/components/SilkCanvas";

export default function LoginPage() {
  const [state, formAction, pending] = useActionState(login, undefined);

  return (
    <div className="grain relative flex min-h-dvh flex-1 bg-canvas-deep text-ink">
      {/* Living silk backdrop */}
      <SilkCanvas className="absolute inset-0 h-full w-full" />

      {/* Darkening veil so the form side stays readable */}
      <div
        aria-hidden
        className="absolute inset-0 bg-gradient-to-r from-canvas-deep via-canvas-deep/80 to-transparent sm:via-canvas-deep/60"
      />

      <div className="relative z-10 mx-auto flex w-full max-w-6xl flex-1 items-center justify-between gap-16 px-6 py-16 sm:px-10">
        <div className="w-full max-w-md">
          <p className="font-mono mb-6 text-xs tracking-widest text-accent">
            MADRID · {new Date().getFullYear()}
          </p>

          <h1 className="display-hero text-5xl text-ink sm:text-6xl">
            Look After
            <br />
            <em className="text-accent">You</em>
          </h1>

          <p className="font-display mt-5 max-w-sm text-lg italic leading-snug text-muted">
            Cuidamos a quienes brillan — the night watch for a roster of stars.
          </p>

          <form action={formAction} className="mt-10">
            <label htmlFor="password" className="mb-2 block text-sm font-medium text-ink">
              Team password
            </label>
            <div className="flex gap-2">
              <input
                id="password"
                name="password"
                type="password"
                required
                autoFocus
                autoComplete="current-password"
                aria-invalid={!!state?.error}
                aria-describedby="password-error"
                className="w-full rounded-md border border-border bg-canvas/70 px-3.5 py-2.5 text-ink backdrop-blur-sm transition-colors outline-none placeholder:text-faint focus:border-accent"
                placeholder="••••••"
              />
              <button
                type="submit"
                disabled={pending}
                className="shrink-0 rounded-md bg-accent px-5 py-2.5 font-semibold text-canvas-deep transition hover:bg-accent-bright disabled:opacity-50"
              >
                {pending ? "Entering…" : "Enter"}
              </button>
            </div>

            <p id="password-error" role="alert" className="min-h-5 mt-3 text-sm text-negative">
              {state?.error}
            </p>

            <p className="mt-8 text-xs text-muted">
              Team access password — ask your manager if you don&apos;t have it.
            </p>
          </form>
        </div>

        {/* Gallery plate: AI-generated key art, drifting slowly. */}
        <figure className="hidden shrink-0 lg:block">
          <div className="overflow-hidden rounded-[0.625rem] border border-border-faint">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src="/silk.jpg"
              alt="Silk fabric suspended in darkness, lit in garnet and gold"
              width={347}
              height={520}
              className="silk-drift block h-[520px] w-auto object-cover"
            />
          </div>
          <figcaption className="font-mono mt-3 flex items-baseline justify-between text-xs text-faint">
            <span className="italic">Seda en la medianoche</span>
            <span>№ 001</span>
          </figcaption>
        </figure>
      </div>
    </div>
  );
}
